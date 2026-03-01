import os
import json
import requests
import datetime
import time
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
METRICS_GITHUB_TOKEN = os.environ.get("METRICS_GITHUB_TOKEN")
USERNAME = "madhavkapila"

if not GEMINI_API_KEY or not METRICS_GITHUB_TOKEN:
    print("Error: Missing API Keys")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
headers = {'Authorization': f'token {METRICS_GITHUB_TOKEN}'}
raw_headers = {'Authorization': f'token {METRICS_GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}

print("Starting Exhaustive GitHub Scrape...")

# --- 1. Load the Brain (Resume Data) ---
with open(".github/data/madhavgit_brain.md", "r", encoding="utf-8") as f:
    chunks = f.read().split("\n\n")

# --- 2. Exhaustive Repo Scrape ---
repos_url = f"https://api.github.com/users/{USERNAME}/repos?sort=updated&per_page=15"
repos = requests.get(repos_url, headers=headers).json()

one_week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat() + "Z"

for r in repos:
    if r.get('private') is True:
        continue
        
    name = r.get('name', 'Unknown')
    desc = r.get('description') or 'No description.'
    lang = r.get('language') or 'Multiple/None'
    branch = r.get('default_branch', 'main')

    # A. Base Context
    chunks.append(f"Repository: {name}\nDescription: {desc}\nPrimary Language: {lang}")

    # B. Last 7 Days of Commits
    commits_res = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}/commits?since={one_week_ago}", headers=headers)
    if commits_res.status_code == 200:
        commits = commits_res.json()
        if commits:
            commit_msgs = [c['commit']['message'] for c in commits[:10]]
            chunks.append(f"Recent activity by Madhav on project '{name}' (Last 7 days):\n" + "\n".join(commit_msgs))

    # C. Directory Structure
    tree_res = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}/git/trees/{branch}?recursive=1", headers=headers)
    if tree_res.status_code == 200:
        tree = tree_res.json().get('tree', [])
        paths = [item['path'] for item in tree if item['type'] == 'blob']
        if paths:
            struct = "\n".join(paths[:40])
            chunks.append(f"Directory and File Structure for project '{name}':\n{struct}")

    # D. README Scrape
    readme_res = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}/readme", headers=raw_headers)
    if readme_res.status_code == 200:
        readme_text = readme_res.text
        for i in range(0, len(readme_text), 1500):
            chunks.append(f"Technical README for '{name}' (Part {i//1500 + 1}):\n{readme_text[i:i+1500]}")

chunks = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 10]

# --- 3. THE SMART UPSERT LOGIC ---
existing_db = {}
try:
    with open(".github/data/vector_db.json", "r", encoding="utf-8") as f:
        old_db = json.load(f)
        for item in old_db:
            # Map existing text directly to its embedding
            existing_db[item['text']] = item['embedding']
    print(f"Loaded {len(existing_db)} existing embeddings from cache.")
except FileNotFoundError:
    print("No existing DB found. Performing full initial build.")

final_db = []
chunks_to_embed = []

# Filter chunks: if it hasn't changed, reuse the old embedding. If it's new, queue it for the API.
for chunk in chunks:
    if chunk in existing_db:
        final_db.append({"text": chunk, "embedding": existing_db[chunk]})
    else:
        chunks_to_embed.append(chunk)

print(f"Total chunks: {len(chunks)}. New/Modified chunks needing API calls: {len(chunks_to_embed)}")

# --- 4. Batch Embed ONLY New Chunks ---
if chunks_to_embed:
    BATCH_SIZE = 100
    for i in range(0, len(chunks_to_embed), BATCH_SIZE):
        batch = chunks_to_embed[i:i+BATCH_SIZE]
        print(f"Embedding new batch {i//BATCH_SIZE + 1}...")
        
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
            )
            
            for text, emb in zip(batch, result.embeddings):
                final_db.append({"text": text, "embedding": emb.values})
                
        except Exception as e:
            print(f"Embedding Error on batch {i//BATCH_SIZE + 1}: {e}")
        
        time.sleep(2) # Safe buffer

# --- 5. Save the Pruned & Updated Database ---
os.makedirs(".github/data", exist_ok=True)
with open(".github/data/vector_db.json", "w", encoding="utf-8") as f:
    json.dump(final_db, f)

print(f"✅ Upsert Complete! Saved {len(final_db)} total chunks to vector_db.json securely.")
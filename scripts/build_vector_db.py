import os
import json
import requests
import datetime
import time
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # 🔒 Firewall: Using the default, unprivileged token!
USERNAME = "madhavkapila"
ALLOW_PRIVATE_REPOS = os.environ.get("ALLOW_PRIVATE_REPOS", "false").lower() == "true"

if not GEMINI_API_KEY or not GITHUB_TOKEN:
    print("Error: Missing API Keys")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
headers = {'Authorization': f'token {GITHUB_TOKEN}'}
raw_headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3.raw'}

if ALLOW_PRIVATE_REPOS:
    print("Warning: ALLOW_PRIVATE_REPOS=true was requested, but private repos are forcibly disabled by policy.")

print("Starting Exhaustive GitHub Scrape...")

def get_json(url, req_headers):
    try:
        res = requests.get(url, headers=req_headers, timeout=20)
    except requests.RequestException as e:
        print(f"Warning: request failed for {url}: {e}")
        return None

    if res.status_code != 200:
        print(f"Warning: {url} returned status {res.status_code}")
        return None

    try:
        return res.json()
    except ValueError:
        print(f"Warning: non-JSON response from {url}")
        return None

# --- 1. Load the Brain (Resume Data) ---
try:
    with open(".github/data/madhavgit_brain.md", "r", encoding="utf-8") as f:
        chunks = f.read().split("\n\n")
except FileNotFoundError:
    print("Error: madhavgit_brain.md not found.")
    chunks = []

# --- 2. Exhaustive Repo Scrape ---
# Public-only listing from authenticated account. This prevents private repo ingestion.
repos_url = "https://api.github.com/user/repos?affiliation=owner&visibility=public&sort=updated&per_page=15"
repos = get_json(repos_url, headers)
if not isinstance(repos, list):
    print("Warning: could not fetch repository list safely. Continuing with resume data only.")
    repos = []

one_week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat() + "Z"

for r in repos:
    if not isinstance(r, dict):
        continue

    # 🚨 SECURITY PROTOCOL: Never ingest private repos.
    if r.get('private') is True:
        print(f"Skipping private repo: {r.get('full_name', r.get('name', 'unknown'))}")
        continue

    owner_login = (r.get('owner') or {}).get('login', '').lower()
    if owner_login != USERNAME.lower():
        continue
        
    name = r.get('name', 'Unknown')
    desc = r.get('description') or 'No description.'
    lang = r.get('language') or 'Multiple/None'
    branch = r.get('default_branch', 'main')

    chunks.append(f"Repository: {name}\nDescription: {desc}\nPrimary Language: {lang}")

    commits = get_json(f"https://api.github.com/repos/{USERNAME}/{name}/commits?since={one_week_ago}", headers)
    if isinstance(commits, list):
        if commits and isinstance(commits, list):
            commit_msgs = [c['commit']['message'] for c in commits[:10]]
            chunks.append(f"Recent activity by Madhav on project '{name}' (Last 7 days):\n" + "\n".join(commit_msgs))

    tree_data = get_json(f"https://api.github.com/repos/{USERNAME}/{name}/git/trees/{branch}?recursive=1", headers)
    if isinstance(tree_data, dict):
        tree = tree_data.get('tree', [])
        paths = [item['path'] for item in tree if item['type'] == 'blob']
        if paths:
            struct = "\n".join(paths[:40])
            chunks.append(f"Directory and File Structure for project '{name}':\n{struct}")

    try:
        readme_res = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}/readme", headers=raw_headers, timeout=20)
    except requests.RequestException as e:
        print(f"Warning: failed to fetch README for '{name}': {e}")
        readme_res = None

    if readme_res is not None and readme_res.status_code == 200:
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
            existing_db[item['text']] = item['embedding']
    print(f"Loaded {len(existing_db)} existing embeddings from cache.")
except FileNotFoundError:
    print("No existing DB found. Performing full initial build.")

final_db = []
chunks_to_embed = []

for chunk in chunks:
    if chunk in existing_db:
        final_db.append({"text": chunk, "embedding": existing_db[chunk]})
    else:
        chunks_to_embed.append(chunk)

print(f"Total chunks: {len(chunks)}. New/Modified chunks needing API calls: {len(chunks_to_embed)}")

# --- 4. Batch Embed ONLY New Chunks (With Fault Tolerance) ---
if chunks_to_embed:
    BATCH_SIZE = 100
    MAX_RETRIES = 3
    
    for i in range(0, len(chunks_to_embed), BATCH_SIZE):
        batch = chunks_to_embed[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(chunks_to_embed) - 1) // BATCH_SIZE + 1
        print(f"Embedding new batch {batch_num}/{total_batches}...")
        
        for attempt in range(MAX_RETRIES):
            try:
                result = client.models.embed_content(
                    model="gemini-embedding-002",
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                
                for text, emb in zip(batch, result.embeddings):
                    final_db.append({"text": text, "embedding": emb.values})
                
                print(f"✅ Batch {batch_num} successful.")
                break 
                
            except Exception as e:
                print(f"⚠️ API Error on batch {batch_num} (Attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 65 
                    print(f"⏸️ Rate limit suspected. Sleeping for {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to embed batch {batch_num} after {MAX_RETRIES} attempts. Skipping.")
        
        time.sleep(2) 

# --- 5. Save the Pruned & Updated Database ---
os.makedirs(".github/data", exist_ok=True)
with open(".github/data/vector_db.json", "w", encoding="utf-8") as f:
    json.dump(final_db, f)

print(f"✅ Upsert Complete! Saved {len(final_db)} total chunks to vector_db.json securely.")

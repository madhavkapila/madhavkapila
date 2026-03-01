import os
import json
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "madhavkapila/madhavkapila")

def get_embedding(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    res = requests.post(url, json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}})
    return res.json()['embedding']['values']

print("Scraping GitHub Data & Resume...")
# --- 1. Load Static Resume Brain ---
with open(".github/data/madhavgit_brain.md", "r", encoding="utf-8") as f:
    chunks = f.read().split("\n\n")

# --- 2. Scrape Repos with STRICT PUBLIC FILTER ---
headers = {'Authorization': f'token {GITHUB_TOKEN}'}
repos = requests.get("https://api.github.com/users/madhavkapila/repos?sort=updated&per_page=10", headers=headers).json()

for r in repos:
    # 🚨 SECURITY PROTOCOL: Explicitly block ANY private repositories from entering the DB
    if r.get('private') is True:
        print(f"🔒 Security lock: Skipped private repository '{r.get('name')}'")
        continue
        
    name = r.get('name', 'Unknown')
    desc = r.get('description') or 'No description.'
    lang = r.get('language') or 'Multiple/None'
    
    # Tag it explicitly as public context so the LLM knows it's safe to discuss
    chunks.append(f"Public Open-Source Project: {name}. Description: {desc}. Primary Language: {lang}.")

# --- 3. Build Vector Database ---
vector_db = []
for chunk in chunks:
    if len(chunk.strip()) > 10:
        vector_db.append({"text": chunk, "embedding": get_embedding(chunk)})

# --- 4. Save to Repository ---
os.makedirs(".github/data", exist_ok=True)
with open(".github/data/vector_db.json", "w", encoding="utf-8") as f:
    json.dump(vector_db, f)

print("✅ Persistent Public Vector DB compiled and saved securely!")
import os
import json
import requests
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GEMINI_API_KEY:
    print("Error: Missing Gemini API Key")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

print("Scraping GitHub Data & Resume...")
with open(".github/data/madhavgit_brain.md", "r", encoding="utf-8") as f:
    chunks = f.read().split("\n\n")

# Scrape Repos
headers = {'Authorization': f'token {GITHUB_TOKEN}'}
repos = requests.get("https://api.github.com/users/madhavkapila/repos?sort=updated&per_page=10", headers=headers).json()

for r in repos:
    if r.get('private') is True:
        continue
    name = r.get('name', 'Unknown')
    desc = r.get('description') or 'No description.'
    lang = r.get('language') or 'Multiple/None'
    chunks.append(f"Public Open-Source Project: {name}. Description: {desc}. Primary Language: {lang}.")

# Filter out empty chunks
chunks = [chunk for chunk in chunks if len(chunk.strip()) > 10]

print(f"Embedding {len(chunks)} chunks in a single API call...")
try:
    # 🚀 Batch Embedding via official SDK (Uses only 1 RPM!)
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=chunks,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    
    vector_db = [
        {"text": chunk, "embedding": emb.values} 
        for chunk, emb in zip(chunks, result.embeddings)
    ]

    os.makedirs(".github/data", exist_ok=True)
    with open(".github/data/vector_db.json", "w", encoding="utf-8") as f:
        json.dump(vector_db, f)
        
    print("✅ Persistent Public Vector DB compiled and saved securely!")
    
except Exception as e:
    print(f"Embedding Error: {e}")
    exit(1)
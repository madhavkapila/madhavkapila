import os
import requests
import datetime
from google import genai

# Configure API Keys
GENAI_KEY = os.environ.get("GEMINI_API_KEY")
METRICS_GITHUB_TOKEN = os.environ.get("METRICS_GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "madhavkapila/madhavkapila")

if not GENAI_KEY:
    print("❌ ERROR: No Gemini API key found. Exiting.")
    exit(1)

# Fetch today's commits safely
headers = {'Authorization': f'token {METRICS_GITHUB_TOKEN}'}
since = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"
commits_url = f"https://api.github.com/repos/{REPO}/commits?since={since}"

try:
    commits_res = requests.get(commits_url, headers=headers)
    commits = commits_res.json() if commits_res.status_code == 200 else []
except Exception as e:
    print(f"⚠️ Warning: Failed to fetch commits ({e}).")
    commits = []

commit_msgs = [c['commit']['message'] for c in commits] if isinstance(commits, list) else []
code_context = "No commits today. Reading docs, grinding DSA, or plotting the next billion-dollar startup."
if commit_msgs:
    code_context = f"Today's commits: {', '.join(commit_msgs)}"

prompt = f"""
You are Madhav Kapila's GitHub PA, who is an applied GenAI developer, a backend engineer, and a consistent DSA/CP solver. 
Context of your day: {code_context}

Write a SINGLE LINE Instagram-style caption summarizing your day. 
Rules:
1. It MUST blend a "Punjabi gabru attitude" (confident, unstoppable, slight swagger) with a "soft at heart / loving" vibe.
2. Keep it under 15 words. No hashtags. Pure aesthetic.
"""

# 🚀 Generate the Quote
try:
    client = genai.Client(api_key=GENAI_KEY)
    response = client.models.generate_content(
        model="gemini-3-flash", 
        contents=prompt,
    )
    quote = response.text.strip().replace('"', '')
except Exception as e:
    print(f"⚠️ API Error: {e}")
    quote = "Compiling backends and heavy thoughts. O(1) focus."


# 🔒 ZERO-BLUNDER INJECTION LOGIC (No Regex)
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    # The exact anchor line directly above your quote
    marker = "> [INFO] Booting Active Agent on Gemma 3 cluster..."

    if marker not in readme:
        print("❌ ERROR: Terminal marker not found in README.md.")
        print("Script aborted to prevent file corruption.")
        exit(1)

    # Split the file strictly at the marker
    parts = readme.split(marker)
    before_marker = parts[0]
    after_marker = parts[1]

    # Split the trailing part by lines so we only edit the very next line
    lines = after_marker.split('\n')

    # lines[0] is the newline, lines[1] is the target quote line
    if len(lines) > 1 and lines[1].startswith('>'):
        lines[1] = f'> "{quote}"'
    else:
        print("❌ ERROR: Format below marker changed. Aborting to prevent corruption.")
        exit(1)

    # Reassemble the README perfectly
    new_readme = before_marker + marker + '\n'.join(lines)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)
        
    print("✅ Passive Pulse updated successfully without regex!")

except Exception as e:
    print(f"❌ CRITICAL ERROR during file write: {e}")
    exit(1)
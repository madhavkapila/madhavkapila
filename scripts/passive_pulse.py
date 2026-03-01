import os
import requests
import google.generativeai as genai
import datetime

# Configure Gemini
GENAI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "madhavkapila/madhavkapila")

if not GENAI_KEY:
    print("No Gemini API key found. Exiting.")
    exit()

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Fetch today's commits
headers = {'Authorization': f'token {GITHUB_TOKEN}'}
since = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"
commits_url = f"https://api.github.com/repos/{REPO}/commits?since={since}"
commits = requests.get(commits_url, headers=headers).json()

commit_msgs = [c['commit']['message'] for c in commits] if isinstance(commits, list) else []
code_context = "No commits today. Reading docs, grinding DSA, or plotting the next billion-dollar startup."
if commit_msgs:
    code_context = f"Today's commits: {', '.join(commit_msgs)}"

# The Prompt Engineering
prompt = f"""
You are Madhav Kapila's GitHub PA, who is an applied GenAI, a backend engineer and a problem solver solving consistently DSA and CP. 
Context of your day: {code_context}

Write a SINGLE LINE Instagram-style caption summarizing your day. 
Rules:
1. It MUST blend a "Punjabi gabru attitude" (confident, unstoppable, slight swagger) with a "soft at heart / loving" vibe.
2. It should have an abstract or hidden meaning related to coding, deep learning, or life.
3. Keep it under 15 words. No hashtags. Pure aesthetic.
"""

response = model.generate_content(prompt)
quote = response.text.strip().replace('"', '')

# Inject into README
with open('README.md', 'r', encoding='utf-8') as f:
    readme = f.read()

import re
# Finds the AI Agent terminal block and updates the quote
new_readme = re.sub(
    r'(\n).*?(\n)',
    f'\\1> {quote}\\2',
    readme,
    flags=re.DOTALL
)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(new_readme)
print("Passive Pulse updated successfully.")
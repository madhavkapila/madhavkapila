import os
import requests
import re

# --- EXACT USERNAMES ---
LC_HANDLE = "SmartKapila"
CC_HANDLE = "SmartK"
CF_HANDLE = "smartk"

# --- FALLBACK STATS ---
lc_total, lc_easy, lc_medium, lc_hard, lc_rating = "411", "150", "200", "61", "1473"
cc_rating, cc_rank, cc_stars = "1485", "457", "2★"
cf_rating, cf_max = "1112", "1112"

# Spoof browser to avoid being blocked
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# --- FETCH LEETCODE ---
try:
    query = """
    {
      matchedUser(username: "%s") {
        submitStatsGlobal { acSubmissionNum { difficulty count } }
      }
      userContestRanking(username: "%s") { rating }
    }
    """ % (LC_HANDLE, LC_HANDLE)
    
    lc_res = requests.post("https://leetcode.com/graphql", json={"query": query}, headers=headers, timeout=10).json()
    stats = lc_res['data']['matchedUser']['submitStatsGlobal']['acSubmissionNum']
    lc_total = str(next(item['count'] for item in stats if item['difficulty'] == 'All'))
    lc_easy = str(next(item['count'] for item in stats if item['difficulty'] == 'Easy'))
    lc_medium = str(next(item['count'] for item in stats if item['difficulty'] == 'Medium'))
    lc_hard = str(next(item['count'] for item in stats if item['difficulty'] == 'Hard'))
    
    ranking = lc_res['data'].get('userContestRanking')
    if ranking:
        lc_rating = str(int(ranking['rating']))
except Exception as e:
    print(f"LeetCode Fetch Failed (Using Fallbacks): {e}")

# --- FETCH CODEFORCES ---
try:
    cf_res = requests.get(f"https://codeforces.com/api/user.info?handles={CF_HANDLE}", headers=headers, timeout=10).json()
    if cf_res.get('status') == 'OK':
        cf_rating = str(cf_res['result'][0].get('rating', 'Unrated'))
        cf_max = str(cf_res['result'][0].get('maxRating', 'Unrated'))
except Exception as e:
    print(f"Codeforces Fetch Failed (Using Fallbacks): {e}")

# --- FETCH CODECHEF (Direct Scrape - No 3rd Party APIs) ---
try:
    cc_url = f"https://www.codechef.com/users/{CC_HANDLE}"
    cc_res = requests.get(cc_url, headers=headers, timeout=10).text
    
    # Regex to pull exact stats from the HTML
    rating_match = re.search(r'<div class="rating-number">(\d+?)</div>', cc_res)
    if rating_match: cc_rating = rating_match.group(1)
        
    stars_match = re.search(r'<span class="rating">([^<]+?)</span>', cc_res)
    if stars_match: cc_stars = stars_match.group(1)
        
    rank_match = re.search(r'Global Rank.*?<a[^>]*>([0-9]+)</a>', cc_res, re.IGNORECASE | re.DOTALL)
    if rank_match: cc_rank = rank_match.group(1)
except Exception as e:
    print(f"CodeChef Scrape Failed (Using Fallbacks): {e}")

# --- SVG DESIGN 1: LEETCODE ---
dsa_svg = f"""<svg width="420" height="180" viewBox="0 0 420 180" xmlns="http://www.w3.org/2000/svg">
    <rect width="420" height="180" rx="10" fill="#0D1117" stroke="#FFA116" stroke-width="2"/>
    <text x="20" y="35" font-family="monospace" font-size="16" fill="#FFA116" font-weight="bold">> LEETCODE_ANALYTICS_</text>
    <g transform="translate(20, 65)">
        <text x="0" y="15" font-family="sans-serif" font-size="12" fill="#8B949E">Total Solved</text>
        <text x="0" y="45" font-family="monospace" font-size="30" fill="#FFFFFF" font-weight="bold">{lc_total}</text>
        
        <text x="130" y="15" font-family="sans-serif" font-size="12" fill="#00b8a3">Easy</text>
        <text x="130" y="40" font-family="monospace" font-size="20" fill="#FFFFFF">{lc_easy}</text>
        
        <text x="210" y="15" font-family="sans-serif" font-size="12" fill="#ffc01e">Medium</text>
        <text x="210" y="40" font-family="monospace" font-size="20" fill="#FFFFFF">{lc_medium}</text>
        
        <text x="300" y="15" font-family="sans-serif" font-size="12" fill="#ff375f">Hard</text>
        <text x="300" y="40" font-family="monospace" font-size="20" fill="#FFFFFF">{lc_hard}</text>
    </g>
    <line x1="20" y1="130" x2="400" y2="130" stroke="#30363D" stroke-width="1"/>
    <text x="20" y="158" font-family="sans-serif" font-size="13" fill="#8B949E">Peak Contest Rating: <tspan fill="#FFFFFF" font-weight="bold">{lc_rating}</tspan></text>
</svg>"""

# --- SVG DESIGN 2: CP ---
cp_svg = f"""<svg width="420" height="140" viewBox="0 0 420 140" xmlns="http://www.w3.org/2000/svg">
    <rect width="420" height="140" rx="10" fill="#0D1117" stroke="#8B44FC" stroke-width="2"/>
    <text x="20" y="35" font-family="monospace" font-size="16" fill="#8B44FC" font-weight="bold">> COMPETITIVE_PROG_</text>
    <g transform="translate(20, 65)">
        <text x="0" y="15" font-family="sans-serif" font-size="12" fill="#8B949E">CodeChef ({cc_stars})</text>
        <text x="0" y="45" font-family="monospace" font-size="28" fill="#FFFFFF" font-weight="bold">{cc_rating}</text>
        <text x="100" y="42" font-family="sans-serif" font-size="10" fill="#8B949E">Rank: {cc_rank}</text>
        
        <text x="210" y="15" font-family="sans-serif" font-size="12" fill="#8B949E">Codeforces</text>
        <text x="210" y="45" font-family="monospace" font-size="28" fill="#FFFFFF" font-weight="bold">{cf_rating}</text>
        <text x="310" y="42" font-family="sans-serif" font-size="10" fill="#8B949E">Max: {cf_max}</text>
    </g>
</svg>"""

# --- SAVE ---
os.makedirs('dist', exist_ok=True)
with open('dist/dsa_card.svg', 'w', encoding='utf-8') as f: f.write(dsa_svg)
with open('dist/cp_card.svg', 'w', encoding='utf-8') as f: f.write(cp_svg)
print("GenZ SVGs successfully generated!")
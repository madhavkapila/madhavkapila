import os
import requests

# --- 1. CONFIGURATION (Change handles here if needed) ---
LC_HANDLE = "SmartKapila"
CC_HANDLE = "madhavkapila"
CF_HANDLE = "madhavkapila"

# --- 2. FALLBACK STATS (If APIs ever go down, your profile won't break) ---
lc_solved, lc_rating = "400+", "1473"
cc_rating, cc_global_rank = "1485", "457"
cf_rating = "1112"

# --- 3. LIVE API FETCHING ---
# LeetCode (Direct GraphQL)
try:
    lc_query = {"query": f'{{ matchedUser(username: "{LC_HANDLE}") {{ submitStatsGlobal {{ acSubmissionNum {{ difficulty count }} }} }} userContestRanking(username: "{LC_HANDLE}") {{ rating }} }}'}
    lc_res = requests.post("https://leetcode.com/graphql", json=lc_query, timeout=10).json()
    lc_solved = str(lc_res['data']['matchedUser']['submitStatsGlobal']['acSubmissionNum'][0]['count'])
    lc_rating = str(int(lc_res['data']['userContestRanking']['rating']))
except Exception as e:
    print(f"LeetCode Fetch Failed: {e}")

# Codeforces (Official API)
try:
    cf_res = requests.get(f"https://codeforces.com/api/user.info?handles={CF_HANDLE}", timeout=10).json()
    cf_rating = str(cf_res['result'][0]['rating'])
except Exception as e:
    print(f"Codeforces Fetch Failed: {e}")

# CodeChef (Public API Wrapper)
try:
    cc_res = requests.get(f"https://codechef-api.vercel.app/handle/{CC_HANDLE}", timeout=10).json()
    if cc_res.get('success', False):
        cc_rating = str(cc_res['currentRating'])
        cc_global_rank = str(cc_res['globalRank'])
except Exception as e:
    print(f"CodeChef Fetch Failed: {e}")

# --- 4. SVG GENERATION ENGINE ---
def generate_cyber_card(title, subtitle, stat1_k, stat1_v, stat2_k, stat2_v, stat3_k, stat3_v, color):
    return f"""<svg width="400" height="150" viewBox="0 0 400 150" xmlns="http://www.w3.org/2000/svg">
    <rect width="400" height="150" rx="10" fill="#0D1117" stroke="{color}" stroke-width="2"/>
    <line x1="20" y1="45" x2="380" y2="45" stroke="{color}" stroke-width="1" opacity="0.5"/>
    <text x="20" y="30" font-family="monospace" font-size="16" fill="{color}" font-weight="bold">> {title}_</text>
    <text x="380" y="30" font-family="monospace" font-size="12" fill="#8B949E" text-anchor="end">{subtitle}</text>

    <g transform="translate(20, 70)">
        <rect width="110" height="60" rx="5" fill="#161B22"/>
        <text x="55" y="25" font-family="sans-serif" font-size="11" fill="#8B949E" text-anchor="middle">{stat1_k}</text>
        <text x="55" y="48" font-family="monospace" font-size="20" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{stat1_v}</text>
    </g>
    <g transform="translate(145, 70)">
        <rect width="110" height="60" rx="5" fill="#161B22"/>
        <text x="55" y="25" font-family="sans-serif" font-size="11" fill="#8B949E" text-anchor="middle">{stat2_k}</text>
        <text x="55" y="48" font-family="monospace" font-size="20" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{stat2_v}</text>
    </g>
    <g transform="translate(270, 70)">
        <rect width="110" height="60" rx="5" fill="#161B22"/>
        <text x="55" y="25" font-family="sans-serif" font-size="11" fill="#8B949E" text-anchor="middle">{stat3_k}</text>
        <text x="55" y="48" font-family="monospace" font-size="20" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{stat3_v}</text>
    </g>
</svg>"""

# Inject Live Data into SVGs
dsa_svg = generate_cyber_card("DSA_GRIND", "Live LeetCode Stats", "Total Solved", lc_solved, "Max Rating", lc_rating, "Platform", "LeetCode", "#00D2FF")
cp_svg = generate_cyber_card("COMP_PROG", "Live CC / CF Stats", "Highest Rank", cc_global_rank, "CC Rating", cc_rating, "CF Rating", cf_rating, "#8B44FC")

os.makedirs('dist', exist_ok=True)
with open('dist/dsa_card.svg', 'w') as f: f.write(dsa_svg)
with open('dist/cp_card.svg', 'w') as f: f.write(cp_svg)
print("Live GenZ SVGs generated successfully.")
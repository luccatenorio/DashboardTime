
import os
import sys
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

load_dotenv()
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
META_API_VERSION = "v21.0"
META_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"
AD_ACCOUNT_ID = "act_551050788075535" 

def deep_inspect(campaign_id):
    print(f"Deep inspecting campaign {campaign_id}")
    url = f"{META_BASE_URL}/{campaign_id}/insights"
    # Try requesting specific breakdown or fields that might reveal profile visits
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "actions,action_values,cost_per_action_type,results,result_values",
        "date_preset": "last_30d"
    }
    
    resp = requests.get(url, params=params)
    data = resp.json().get('data', [])
    
    if not data:
        print("No data")
        return

    all_action_types = set()
    for d in data:
        actions = d.get('actions', [])
        for a in actions:
            typ = a.get('action_type')
            val = a.get('value')
            all_action_types.add(f"{typ}: {val}")
            if 'profile' in typ:
                print(f"POSSIBLE MATCH: {typ} = {val}")

    print("All Action Types Found:")
    for t in sorted(list(all_action_types)):
        print(t)

if __name__ == "__main__":
    deep_inspect("120234887557820645")


import os
import sys
import requests
from dotenv import load_dotenv

# ... (setup code same as before) ...
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

def get_campaign_by_name(name_part):
    print(f"Searching for campaign: {name_part}")
    url = f"{META_BASE_URL}/{AD_ACCOUNT_ID}/campaigns"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "id,name,objective",
        "limit": 500
    }
    resp = requests.get(url, params=params)
    data = resp.json().get('data', [])
    for c in data:
        if name_part.lower() in c['name'].lower():
            print(f"FOUND: {c['name']} (ID: {c['id']}) Obj: {c['objective']}")
            print("--- Actions ---")
            inspect_actions(c['id'])

def inspect_actions(campaign_id):
    url = f"{META_BASE_URL}/{campaign_id}/insights"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "actions,action_values",
        "date_preset": "last_30d"
    }
    resp = requests.get(url, params=params)
    data = resp.json().get('data', [])
    for d in data:
        for a in d.get('actions', []):
            print(f"{a['action_type']}: {a['value']}")

if __name__ == "__main__":
    get_campaign_by_name("VENDA DIRETA")

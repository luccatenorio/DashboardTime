
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Configurar encoding para Windows
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

# RGA Ad Account ID (from log)
AD_ACCOUNT_ID = "act_551050788075535" 

def get_raw_campaign_data(campaign_name_part):
    # 1. Get Campaign ID
    print(f"\nSearching for campaign containing: {campaign_name_part}")
    url = f"{META_BASE_URL}/{AD_ACCOUNT_ID}/campaigns"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "id,name,objective",
        "limit": 100
    }
    
    found_campaign = None
    response = requests.get(url, params=params)
    data = response.json().get('data', [])
    
    for c in data:
        if campaign_name_part in c['name']:
            found_campaign = c
            break
            
    if not found_campaign:
        print("Campaign not found.")
        return

    print(f"Found Campaign: {found_campaign['name']} (ID: {found_campaign['id']}) Obj: {found_campaign['objective']}")
    
    # 2. Get Insights/Actions
    insights_url = f"{META_BASE_URL}/{found_campaign['id']}/insights"
    ins_params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "actions,action_values",
        "date_preset": "last_30d"
    }
    
    ins_resp = requests.get(insights_url, params=ins_params)
    ins_data = ins_resp.json().get('data', [])
    
    if not ins_data:
        print("No insights data.")
        return
        
    # Aggregate actions
    total_actions = {}
    for d in ins_data:
        actions = d.get('actions', [])
        for a in actions:
            atype = a['action_type']
            val = float(a['value'])
            total_actions[atype] = total_actions.get(atype, 0) + val
            
    print("Total Actions (Last 30d):")
    for k, v in total_actions.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    get_raw_campaign_data("Post do Instagram")
    get_raw_campaign_data("[ENGAJAMENTO]")

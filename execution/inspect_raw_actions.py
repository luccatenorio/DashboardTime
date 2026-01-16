import os
import json
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
# Gabriel's Account ID from previous logs: act_1395732718226239
AD_ACCOUNT_ID = 'act_1395732718226239' 
API_VER = 'v21.0'

def inspect_actions():
    # Fetch campaigns first
    url = f"https://graph.facebook.com/{API_VER}/{AD_ACCOUNT_ID}/campaigns"
    params = {'access_token': ACCESS_TOKEN, 'fields': 'id,name', 'limit': 100}
    
    resp = requests.get(url, params=params).json()
    campaigns = resp.get('data', [])
    
    print(f"Encontradas {len(campaigns)} campanhas. Verificando ações dos últimos 30 dias...")
    
    all_action_counts = {}
    
    for camp in campaigns:
        # if 'betania' not in camp['name'].lower(): continue # Optional filter
        
        c_id = camp['id']
        c_name = camp['name']
        
        url_insights = f"https://graph.facebook.com/{API_VER}/{c_id}/insights"
        i_params = {
            'access_token': ACCESS_TOKEN,
            'fields': 'actions',
            'date_preset': 'last_30d'
        }
        
        i_resp = requests.get(url_insights, params=i_params).json()
        data = i_resp.get('data', [])
        
        if not data: continue
        
        # Meta returns aggregate for date_preset if no time_increment is set
        # Let's see the aggregate actions
        for row in data:
            actions = row.get('actions', [])
            for action in actions:
                atype = action['action_type']
                val = float(action['value'])
                
                if atype not in all_action_counts: all_action_counts[atype] = 0
                all_action_counts[atype] += val

    print("\n=== TOTAL DE AÇÕES (RAW) DO CLIENTE (Últimos 30 dias) ===")
    for k, v in sorted(all_action_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{k}: {v}")

if __name__ == "__main__":
    inspect_actions()

import os
import requests
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Setup Supabase (Service Role to read DB)
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Meta Setup
ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
API_VER = 'v21.0'

def debug_pedro():
    print("Investigating Pedro Fiuza...")
    
    # 1. Get Pedro's Ad Account ID from DB
    client = supabase.table('clients').select('*').ilike('cliente', '%Pedro Fiuza%').single().execute()
    if not client.data:
        print("Pedro Fiuza not found in DB!")
        return
        
    c_data = client.data
    ad_account = c_data['conta_anuncio']
    # Fix format
    if not ad_account.startswith('act_'): ad_account = f"act_{ad_account}"
    
    print(f"Client: {c_data['cliente']}")
    print(f"Ad Account: {ad_account}")
    
    # 2. Check Meta Campaigns
    url_camp = f"https://graph.facebook.com/{API_VER}/{ad_account}/campaigns"
    params_camp = {
        'access_token': ACCESS_TOKEN,
        'fields': 'id,name,status,effective_status',
        'limit': 50
    }
    
    print("\nFetching Campaigns from Meta...")
    resp = requests.get(url_camp, params=params_camp).json()
    
    campaigns = resp.get('data', [])
    print(f"Found {len(campaigns)} campaigns.")
    
    if not campaigns:
        print(f"Raw Response: {json.dumps(resp, indent=2)}")
    
    for camp in campaigns:
        print(f"\n[Campanha] {camp['name']} ({camp['status']})")
        
        # 3. Check Insights for this campaign (Last 30 Days)
        url_ins = f"https://graph.facebook.com/{API_VER}/{camp['id']}/insights"
        params_ins = {
            'access_token': ACCESS_TOKEN,
            'date_preset': 'last_30d',
            'fields': 'spend,impressions,actions'
        }
        res_ins = requests.get(url_ins, params=params_ins).json()
        data_ins = res_ins.get('data', [])
        
        if data_ins:
            print(f"   => Has Data! Spend: {data_ins[0].get('spend')} | Impr: {data_ins[0].get('impressions')}")
        else:
            print(f"   => NO DATA (Insights empty for last_30d)")
            # Try debugging why (maybe created recently?)

if __name__ == "__main__":
    debug_pedro()

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=r'c:\Users\Christian\Desktop\DASHBOARD CURSOR\.env')
meta_token = os.environ.get('META_ACCESS_TOKEN')
url = f"https://graph.facebook.com/v18.0/120205837330750567/insights" # Campaign ID for VIC SERRANO
# Wait, do I know the campaign ID? Yes, it's in the DB but I don't have it right now.
# Let's just query the DB correctly using requests to Supabase REST API instead of the client?
# No, let's fix check_campaign.py with correct keys first.

supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')

headers = {
    "apikey": supabase_key,
    "Authorization": f"Bearer {supabase_key}"
}

endpoint = f"{supabase_url}/rest/v1/dashboard_campaign_metrics?campaign_name=eq.CA%5BMENSAGEM%5D%5BVIC%20SERRANO%5D%5BVictor%5D%2012.02&select=data_referencia,investimento,resultado_valor,resultado_nome"

resp = requests.get(endpoint, headers=headers)
data = resp.json()

if not isinstance(data, list):
    print("Error:", data)
    sys.exit(1)

tot_i = 0
tot_l = 0

print("Data       | Gasto  | Leads")
for r in sorted(data, key=lambda x: x['data_referencia']):
    i = float(r['investimento'])
    l = float(r['resultado_valor'])
    print(f"{r['data_referencia']} | {i:>6.2f} | {l:>5.0f} ({r['resultado_nome']})")
    tot_i += i
    tot_l += l

print("-" * 30)
print(f"TOTAL DB   | {tot_i:>6.2f} | {tot_leads:>5.0f}")

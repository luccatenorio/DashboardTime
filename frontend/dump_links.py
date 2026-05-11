import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=r'c:\Users\Christian\Desktop\DASHBOARD CURSOR\.env')
s_url = os.environ.get('SUPABASE_URL')
s_key = os.environ.get('SUPABASE_KEY')

headers = {
    "apikey": s_key,
    "Authorization": f"Bearer {s_key}"
}

endpoint = f"{s_url}/rest/v1/clients?select=cliente,observacoes&ativo=eq.true"
try:
    data = requests.get(endpoint, headers=headers).json()
    print("--- LINKS GERADOS ---")
    for row in data:
        print(f"{row['cliente']} | https://dashboardtimecontroll.vercel.app/#/c/{row['observacoes']}")
except Exception as e:
    print("ERR:", e)

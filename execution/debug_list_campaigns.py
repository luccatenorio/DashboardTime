
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def list_campaigns():
    response = supabase.table("dashboard_campaign_metrics").select("campaign_name").execute()
    names = sorted(list(set(r['campaign_name'] for r in response.data)))
    print("Campaign Names found:")
    for n in names:
        print(n)

if __name__ == "__main__":
    list_campaigns()

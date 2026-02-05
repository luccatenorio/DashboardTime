
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
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def check_awareness():
    print("Checking Awareness Campaign in DB...")
    # Search by partial name
    response = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .ilike("campaign_name", "%RECONHECIMENTO%")\
        .order("data_referencia", desc=True)\
        .execute()
    
    rows = response.data
    print(f"Found {len(rows)} rows.")
    for r in rows[:5]: # Show top 5 recent
        print(f"Date: {r.get('data_referencia')} | Val: {r.get('resultado_valor')} | Name: {r.get('resultado_nome')} | Reach: {r.get('alcance')}")

if __name__ == "__main__":
    check_awareness()

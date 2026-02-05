
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

def check_db():
    print("Checking Venda Direta in DB...")
    # Search by partial name
    response = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .ilike("campaign_name", "%VENDA DIRETA%")\
        .execute()
    
    rows = response.data
    total_val = 0
    print(f"Found {len(rows)} rows.")
    for r in rows:
        print(f"Date: {r.get('data_referencia')} | Val: {r.get('resultado_valor')} | Name: {r.get('resultado_nome')} | CID: {r.get('campaign_id')}")
        total_val += r.get('resultado_valor', 0)
        
    print(f"Total calculated from DB: {total_val}")

if __name__ == "__main__":
    check_db()

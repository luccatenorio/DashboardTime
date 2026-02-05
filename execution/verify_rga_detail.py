
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def check_rga_detail():
    print("Checking RGA Engagement Campaign (Post do Instagram) Dates...")
    res = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .ilike("campaign_name", "%Post do Instagram%")\
        .order("data_referencia", desc=True)\
        .limit(10)\
        .execute()
    
    rows = res.data
    for r in rows:
        print(f"Date: {r['data_referencia']} | Val: {r['resultado_valor']} | Name: {r['resultado_nome']}")

if __name__ == "__main__":
    check_rga_detail()

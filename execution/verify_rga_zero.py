
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def check_rga_engagement():
    print("Checking RGA Engagement Campaign (Post do Instagram)...")
    # Finding campaign by name (approximate)
    res = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .ilike("campaign_name", "%Post do Instagram%")\
        .execute()
    
    rows = res.data
    if rows:
        print(f"Found {len(rows)} rows.")
        total_leads = sum(r['resultado_valor'] for r in rows)
        print(f"Total Leads (should be 0): {total_leads}")
        print(f"Sample row: Val={rows[0]['resultado_valor']} | Name={rows[0]['resultado_nome']}")
    else:
        print("No rows found for 'Post do Instagram'. Checking 'ENGAJAMENTO' generic...")
        res = supabase.table("dashboard_campaign_metrics")\
            .select("*")\
            .ilike("campaign_name", "%ENGAJAMENTO%")\
            .limit(5)\
            .execute()
        for r in res.data:
             print(f"Camp: {r['campaign_name']} | Val: {r['resultado_valor']}")

if __name__ == "__main__":
    check_rga_engagement()

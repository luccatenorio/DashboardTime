
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def check_vicente_leads():
    print("Checking Vicente Message Campaigns...")
    # Get Client ID for Vicente if needed, or just filter by client_name?
    # The sync script uses client_id in the DB.
    # I'll search by campaign name containing "Mensagem" for Vicente's client ID?
    # First get Vicente's ID
    c = supabase.table("clients").select("id").eq("cliente", "Vicente").execute()
    if not c.data:
        print("Client Vicente not found")
        return
    client_id = c.data[0]['id']

    res = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .eq("client_id", client_id)\
        .execute()
    
    rows = res.data
    print(f"Found {len(rows)} metrics for Vicente.")
    
    total = 0
    for r in rows:
        val = r['resultado_valor']
        if val > 0:
            total += val
            print(f"Date: {r['data_referencia']} | Val: {val} | Name: {r['resultado_nome']} | Camp: {r['campaign_name']}")

    print(f"Total Leads Vicente: {total}")

if __name__ == "__main__":
    check_vicente_leads()

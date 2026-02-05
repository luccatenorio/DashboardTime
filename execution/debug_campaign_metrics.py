
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Configurar encoding para Windows
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

def check_campaign():
    # 1. Find the campaign
    print("Searching for campaign 'ca - [mensagem] 27.11'...")
    # Just search in metrics table directly or join? 
    # The metrics table has campaign_name.
    
    response = supabase.table("dashboard_campaign_metrics")\
        .select("*")\
        .eq("campaign_name", "ca - [ mensagem ]  27.11")\
        .execute()
    
    rows = response.data
    if not rows:
        print("No metrics found for this campaign.")
        return

    print(f"Found {len(rows)} daily records.")
    
    total_invest = 0.0
    total_results = 0.0
    
    print(f"{'Date':<12} | {'Invest':<10} | {'Result':<8} | {'Metric Name':<30}")
    print("-" * 70)
    
    rows.sort(key=lambda x: x['data_referencia'])
    
    for row in rows:
        invest = row.get('investimento', 0)
        res_val = row.get('resultado_valor', 0)
        res_name = row.get('resultado_nome', 'N/A')
        date = row.get('data_referencia')
        
        total_invest += invest
        total_results += res_val
        
        if res_name is None:
            res_name = 'None'
        print(f"{date:<12} | {invest:<10.2f} | {res_val:<8.1f} | {res_name:<30}")

    print("-" * 70)
    print(f"TOTAL INVEST: {total_invest:.2f}")
    print(f"TOTAL RESULTS: {total_results:.1f}")

if __name__ == "__main__":
    check_campaign()

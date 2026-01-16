import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def debug_casa_retiro():
    print("Investigating Casa Retiro data...")
    
    # Get ID
    client = supabase.table('clients').select('id').ilike('cliente', '%retiro%').single().execute()
    c_id = client.data['id']
    print(f"Client ID: {c_id}")
    
    # Get metrics sum
    metrics = supabase.table('dashboard_campaign_metrics').select('investimento, campaign_name, data_referencia').eq('client_id', c_id).gte('data_referencia', '2024-12-16').execute()
    
    total = 0
    by_campaign = {}
    
    for m in metrics.data:
        inv = m['investimento']
        total += inv
        cname = m['campaign_name']
        if cname not in by_campaign: by_campaign[cname] = 0
        by_campaign[cname] += inv
        
    print(f"Total Invested (DB - Last 30d): R$ {total:.2f}")
    print("\nBy Campaign:")
    for c, v in by_campaign.items():
        print(f" - {c}: R$ {v:.2f}")

if __name__ == "__main__":
    debug_casa_retiro()

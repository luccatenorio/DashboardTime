import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check():
    print("Verificando status de sincronizacao de hoje...")
    from datetime import datetime, date
    today = date.today().isoformat()
    
    res = supabase.table('clients').select('cliente, last_sync_at, conta_anuncio').execute()
    synced = 0
    not_synced = 0
    
    for row in res.data:
        ls = row.get('last_sync_at')
        if ls and ls.startswith(today):
            synced += 1
        else:
            not_synced += 1
            print(f"PENDENTE: {row['cliente']} (Ultima: {ls})")
            
    print(f"\nResumo: {synced} sincronizados hoje, {not_synced} ainda nao sincronizados.")

if __name__ == "__main__":
    check()

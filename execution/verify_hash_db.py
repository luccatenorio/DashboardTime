import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
# Using Service Key to guarantee read
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def check_gabriel():
    target_hash = 'exfdc8zud7d8jisg7iflyaz4uaiogw'
    print(f"Checking DB for hash: '{target_hash}'")
    
    # 1. Check if hash exists exactly
    res = supabase.table('clients').select('id, cliente, observacoes').eq('observacoes', target_hash).execute()
    if res.data:
        print(f"✅ SUCCESS: Found exact match for {res.data[0]['cliente']}")
        return

    # 2. If not, check what IS in Gabriel's row
    print("❌ Match not found. Checking Gabriel's row manually...")
    gabriel = supabase.table('clients').select('id, cliente, observacoes').ilike('cliente', '%Gabriel%').execute()
    
    for g in gabriel.data:
        curr = g.get('observacoes')
        print(f"Client: {g['cliente']}")
        print(f"Current DB Hash: '{curr}'")
        print(f"Target Hash:     '{target_hash}'")
        print(f"Match? {curr == target_hash}")
        print(f"Lengths: DB={len(curr) if curr else 0}, Target={len(target_hash)}")

if __name__ == "__main__":
    check_gabriel()

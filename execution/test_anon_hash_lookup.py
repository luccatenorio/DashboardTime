import os
from supabase import create_client

# Frontend Anon Key (from user request/supabase.js)
SUPABASE_URL = 'https://lsxrqbzitmbyycfxtpyu.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzeHJxYnppdG1ieXljZnh0cHl1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc2NjQyMDcsImV4cCI6MjA4MzI0MDIwN30.woOsJBXNAu9ssvXRN4eabgX2sC8sTq9wphiSeDOtDxs'

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Hash generated for Gabriel
TEST_HASH = 'exfdc8zud7d8jisg7iflyaz4uaiogw'

try:
    print(f"Testing access with Anon Key for hash: {TEST_HASH}")
    # supabase-py v2 syntax
    response = supabase.table('clients').select('id, cliente').eq('observacoes', TEST_HASH).execute()
    
    if response.data and len(response.data) > 0:
        print(f"SUCCESS: Found client: {response.data}")
    else:
        print("FAILURE: No data found. This confirms RLS blockage (or empty DB).")
        # Try finding *any* client to see if we can read anything
        all_clients = supabase.table('clients').select('id').limit(1).execute()
        if not all_clients.data:
            print("CONFIRMED: Cannot read 'clients' table at all (RLS Deny All).")
        
except Exception as e:
    print(f"ERROR: {str(e)}")

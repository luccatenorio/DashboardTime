import os
import secrets
from supabase import create_client

# HARDCODED Service Role Key (from force_update_hashes.py)
SUPABASE_URL = 'https://lsxrqbzitmbyycfxtpyu.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzeHJxYnppdG1ieXljZnh0cHl1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY2NDIwNywiZXhwIjoyMDgzMjQwMjA3fQ.o7Tcs0jJ-cj6Qwyo1fA4BQ0tJpEfiOnzcAt77YKsVTE'

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def generate_hash():
    return secrets.token_urlsafe(24).replace('-', '').replace('_', '').lower()

def main():
    print("Starting Client Update/Insertion...")

    # 1. Handle RGA Imoveis (Old Pedro Ferreira)
    print("\n--- Processing 'RGA Imoveis' ---")
    
    # Check if RGA already exists
    rga_check = supabase.table('clients').select('*').eq('cliente', 'RGA Imoveis').execute()
    
    if rga_check.data:
        print("✅ 'RGA Imoveis' already exists using that name.")
        client_id = rga_check.data[0]['id']
        current_hash = rga_check.data[0].get('observacoes')
        
        # Ensure it has a hash
        if not current_hash or len(current_hash) < 10:
             print("Hash appears invalid/missing. Generating new one...")
             new_hash = generate_hash()
             supabase.table('clients').update({'observacoes': new_hash}).eq('id', client_id).execute()
             print(f"Updated hash for RGA Imoveis.")
    else:
        # Check for 'pedro ferreira' (case insensitive search might be tricky depending on DB, assume exact or partial)
        # Using a broader search or just exact for now as per user instruction "alterado foi o antigo pedro ferreira"
        pedro_check = supabase.table('clients').select('*').ilike('cliente', 'pedro ferreira').execute()
        
        if pedro_check.data:
            print("Found 'pedro ferreira'. Renaming to 'RGA Imoveis'...")
            client_id = pedro_check.data[0]['id']
            # User said "RGA deixei o mesmo hash", so we generally preserve if exists, but ensure it works.
            # Assuming user manually renamed it? Or wants me to? "o alterado foi o antigo pedro ferreira que agora é RGA Imoveis"
            # It sounds like the user might have already renamed it in their mind or UI, but let's ensure DB reflects it.
            # "o do RGA deixei o mesmo hash, alterei o nome e a conta de anuncio" -> implies user might have done it?
            # BUT "adicionei a tabela clients mais 3 usuários e editei 1... o alterado foi o antigo pedro ferreira que agora é RGA Imoveis"
            # It's safer to ensure the name is 'RGA Imoveis'.
            
            supabase.table('clients').update({'cliente': 'RGA Imoveis'}).eq('id', client_id).execute()
            print("✅ Renamed 'pedro ferreira' to 'RGA Imoveis'")
        else:
             print("Could not find 'RGA Imoveis' or 'pedro ferreira'. Creating 'RGA Imoveis' fresh...")
             new_hash = generate_hash()
             supabase.table('clients').insert({
                 'cliente': 'RGA Imoveis',
                 'ativo': True,
                 'observacoes': new_hash
             }).execute()
             print("✅ Created new 'RGA Imoveis' client")

    # 2. Add/Update New Clients
    new_clients = ['marcos Souza', 'marcos Sena', 'daniel rocha']
    
    print("\n--- Processing New Clients ---")
    for name in new_clients:
        # Check if exists (case insensitive ideally, but simple check first)
        res = supabase.table('clients').select('*').ilike('cliente', name).execute()
        
        if res.data:
            print(f"Client '{name}' found. Checking hash...")
            client_data = res.data[0]
            if not client_data.get('observacoes') or len(client_data.get('observacoes')) < 10:
                new_hash = generate_hash()
                supabase.table('clients').update({'observacoes': new_hash}).eq('id', client_data['id']).execute()
                print(f"✅ Generated hash for existing '{name}'")
            else:
                 print(f"ℹ️ '{name}' already has a hash.")
        else:
            print(f"Client '{name}' NOT found. Inserting...")
            new_hash = generate_hash()
            # Assuming minimal required fields. 'ativo': True seems important.
            supabase.table('clients').insert({
                 'cliente': name,
                 'ativo': True,
                 'observacoes': new_hash
            }).execute()
            print(f"✅ Inserted '{name}' with new hash.")

    # 3. Final Report
    with open("execution/hashes.txt", "w", encoding="utf-8") as f:
        print("\n" + "="*50)
        print("FINAL CLIENT ACCESS LINKS")
        print("="*50)
        
        # Fetch all relevant clients to print
        all_names = ['RGA Imoveis'] + new_clients
        # Using 'in' query if possible, or just looping
        
        for name in all_names:
            res = supabase.table('clients').select('cliente, observacoes').ilike('cliente', name).execute()
            if res.data:
                c = res.data[0]
                line = f"{c['cliente']}: http://localhost:5174/#/c/{c.get('observacoes')}"
                print(line)
                f.write(line + "\n")
            else:
                print(f"⚠️ Could not retrieve data for {name}")

if __name__ == "__main__":
    main()

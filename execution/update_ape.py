from supabase import create_client

SUPABASE_URL = 'https://werkiwmegzqdsgfhcglb.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indlcmtpd21lZ3pxZHNnZmhjZ2xiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1OTQxMDksImV4cCI6MjA4OTE3MDEwOX0.xHztZ38cpcaMop97PFwSqDQXg92AXWCEDgjBmC3xV7E'

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

result = supabase.table('clients').select('id,cliente').ilike('cliente', '%ape%').execute()

if not result.data:
    print("Nenhum cliente com 'ape' foi encontrado.")
else:
    for client in result.data:
        old_name = client['cliente']
        new_name = old_name.replace('APE', 'APÊ').replace('Ape', 'Apê').replace('ape', 'apê')
        print(f"Atualizando: '{old_name}' -> '{new_name}'")
        
        if new_name != old_name:
            update_res = supabase.table('clients').update({'cliente': new_name}).eq('id', client['id']).execute()
            print(f"Update realizado.")
        else:
            print("Nenhuma mudanca no nome.")

# Verifica como ficou
result = supabase.table('clients').select('id,cliente').ilike('cliente', '%apê%').execute()
print("Clientes com 'apê' no banco agora:")
for client in result.data:
    print("-", client['cliente'])

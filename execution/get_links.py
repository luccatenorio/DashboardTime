import os
from supabase import create_client

SUPABASE_URL = 'https://lsxrqbzitmbyycfxtpyu.supabase.co'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxzeHJxYnppdG1ieXljZnh0cHl1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY2NDIwNywiZXhwIjoyMDgzMjQwMjA3fQ.o7Tcs0jJ-cj6Qwyo1fA4BQ0tJpEfiOnzcAt77YKsVTE'

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_links():
    print("Recuperando clientes ATIVOS e seus Links/Hashes...")
    clients = supabase.table('clients').select('id, cliente, observacoes').eq('ativo', True).execute()
    
    # Produz uma lista
    print("\nLista de Clientes e Links Dashboard:")
    print("="*60)
    for c in sorted(clients.data, key=lambda x: x['cliente']):
        nome = c['cliente']
        hash_str = c.get('observacoes')
        if hash_str and len(hash_str) > 10:
            link = f"https://dash.v4company.com.br/#/c/{hash_str}"
            print(f"- {nome}: {link} \n  (Hash: {hash_str})\n")
        else:
            print(f"- {nome}: SEM HASH definido! ({hash_str})\n")

if __name__ == '__main__':
    get_links()

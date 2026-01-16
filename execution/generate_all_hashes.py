import os
import secrets
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def generate_hashes():
    print("Gerando hashes para clientes...")
    
    # Buscar clientes ativos
    clients = supabase.table('clients').select('*').eq('ativo', True).execute()
    
    for client in clients.data:
        current_hash = client.get('observacoes')
        final_hash = None
        
        # Se já tem um hash longo (assumindo que seja nosso hash de acesso), mantém
        if current_hash and len(current_hash) > 20: 
            print(f"[{client['cliente']}] Já possui hash: {current_hash}")
            final_hash = current_hash
        else:
            # Gerar novo hash
            new_hash = secrets.token_urlsafe(24).replace('-', '').replace('_', '').lower()
            
            # Atualizar
            supabase.table('clients').update({'observacoes': new_hash}).eq('id', client['id']).execute()
            print(f"[{client['cliente']}] Novo hash gerado: {new_hash}")
            final_hash = new_hash
            
        print(f"LINK: http://localhost:5174/#/c/{final_hash}\n")

if __name__ == "__main__":
    generate_hashes()

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def get_links():
    res = supabase.table('clients').select('cliente, observacoes').eq('ativo', True).order('cliente').execute()
    print("| Cliente | Link do Dashboard |")
    print("| :--- | :--- |")
    for row in res.data:
        name = row['cliente']
        hash_code = row.get('observacoes')
        if hash_code and len(hash_code) > 10:
            print(f"| **{name}** | http://localhost:5173/#/c/{hash_code} |")

if __name__ == "__main__":
    get_links()

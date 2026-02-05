import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Pegar os últimos 5 logs para ver o que está acontecendo
logs = supabase.table("logs").select("*").order("created_at", desc=True).limit(5).execute()
for log in logs.data:
    print(f"[{log.get('created_at')}] {log.get('status')} - {log.get('mensagem')}")

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

since = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
logs = supabase.table("logs").select("mensagem,created_at").eq("status", "success").gte("created_at", since).execute()
processed = set()
for log in logs.data:
    if "Sincronização concluída para" in log['mensagem']:
        name = log['mensagem'].replace("Sincronização concluída para ", "")
        processed.add(name)

clients = supabase.table("clients").select("cliente").eq("ativo", True).execute()
total_clients = [c['cliente'] for c in clients.data]

print(f"Total de clientes ativos: {len(total_clients)}")
print(f"Clientes processados nos últimos 20 min: {len(processed)}")
print(f"Faltam: {set(total_clients) - processed}")

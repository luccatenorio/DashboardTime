from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
res = sb.table('clients').select('cliente, observacoes').execute()
for c in res.data:
    print(f"{c['cliente']}: http://localhost:5174/#/c/{c['observacoes']}")

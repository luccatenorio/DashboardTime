from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Testar query sem filtro
result = supabase.table('clients').select('id,cliente,conta_anuncio,ativo').execute()
print(f'Total de clientes: {len(result.data)}')
print(f'Ativos (Python filter): {sum(1 for c in result.data if c.get("ativo"))}')

# Testar com filtro
result2 = supabase.table('clients').select('id,cliente,conta_anuncio').eq('ativo', True).execute()
print(f'Com filtro ativo=True: {len(result2.data)}')

# Testar com string
result3 = supabase.table('clients').select('id,cliente,conta_anuncio').eq('ativo', 'true').execute()
print(f'Com filtro ativo="true": {len(result3.data)}')

if result.data:
    print('\nPrimeiros 3 clientes:')
    for c in result.data[:3]:
        print(f"  {c['cliente']} - Ativo: {c.get('ativo')} (tipo: {type(c.get('ativo'))})")

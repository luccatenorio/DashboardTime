import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Hash e ID do Gabriel fornecidos pelo usuario
# Hash: opj7db435vzq0yf2sxlt8ceuar61kn9hwmgii
# ID Gabriel (recuperado no inspect anterior): e0d0814a-1ce6-4e91-98ca-d8212020a29b

CLIENT_ID = 'e0d0814a-1ce6-4e91-98ca-d8212020a29b'
HASH = 'opj7db435vzq0yf2sxlt8ceuar61kn9hwmgii'

print(f"Atualizando cliente {CLIENT_ID} com hash no campo observacoes...")

try:
    data = supabase.table('clients').update({'observacoes': HASH}).eq('id', CLIENT_ID).execute()
    print("Sucesso! Registro atualizado:", data.data)
except Exception as e:
    print(f"Erro ao atualizar: {e}")

"""
Script de teste para validar a sincronização com um cliente específico
Execute este script primeiro para testar antes de rodar a sincronização completa
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Carrega variáveis de ambiente
load_dotenv()

# Validação básica
print("Validando configuracoes...")

META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not META_ACCESS_TOKEN:
    print("ERRO: META_ACCESS_TOKEN nao encontrado no .env")
    sys.exit(1)

if not SUPABASE_URL:
    print("ERRO: SUPABASE_URL nao encontrado no .env")
    sys.exit(1)

if not SUPABASE_KEY:
    print("ERRO: SUPABASE_KEY nao encontrado no .env")
    sys.exit(1)

print("OK: Variaveis de ambiente carregadas")

# Testar conexão Supabase
print("\nTestando conexao com Supabase...")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Buscar um cliente para teste
    clients = supabase.table("clients").select("id,cliente,conta_anuncio").eq("ativo", True).limit(1).execute()
    
    if clients.data:
        client = clients.data[0]
        print(f"OK: Conexao OK - Cliente de teste: {client['cliente']}")
        print(f"   Conta: {client['conta_anuncio']}")
    else:
        print("AVISO: Conexao OK, mas nenhum cliente ativo encontrado")
except Exception as e:
    print(f"ERRO: Erro ao conectar no Supabase: {str(e)}")
    sys.exit(1)

# Testar token Meta
print("\nTestando token do Meta...")
import requests
try:
    response = requests.get(
        f"https://graph.facebook.com/v21.0/me",
        params={"access_token": META_ACCESS_TOKEN},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK: Token valido - Usuario: {data.get('name', 'N/A')}")
    else:
        print(f"ERRO: Token invalido: {response.status_code}")
        print(f"   Resposta: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"ERRO: Erro ao validar token: {str(e)}")
    sys.exit(1)

print("\nOK: Todas as validacoes passaram!")
print("Voce pode executar sync_meta_metrics.py agora")

"""
Script para testar o token do Meta e listar recursos disponíveis
"""
import os
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Obtém o token do Meta
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')

if not META_ACCESS_TOKEN:
    print("❌ ERRO: Token META_ACCESS_TOKEN não encontrado no arquivo .env")
    exit(1)

print(f"✅ Token encontrado: {META_ACCESS_TOKEN[:20]}...")
print("\n" + "="*60)
print("Testando conexão com Meta Graph API...")
print("="*60 + "\n")

# URL base da Meta Graph API
BASE_URL = "https://graph.facebook.com/v21.0"

# Teste 1: Verificar informações do token
print("1️⃣ Testando token - Verificando informações básicas...")
try:
    response = requests.get(
        f"{BASE_URL}/me",
        params={"access_token": META_ACCESS_TOKEN}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token válido!")
        print(f"   ID: {data.get('id', 'N/A')}")
        print(f"   Nome: {data.get('name', 'N/A')}")
    else:
        print(f"❌ Erro ao validar token: {response.status_code}")
        print(f"   Resposta: {response.text}")
        exit(1)
except Exception as e:
    print(f"❌ Erro na requisição: {str(e)}")
    exit(1)

print("\n" + "-"*60 + "\n")

# Teste 2: Listar Business Managers
print("2️⃣ Buscando Business Managers...")
try:
    response = requests.get(
        f"{BASE_URL}/me/businesses",
        params={
            "access_token": META_ACCESS_TOKEN,
            "fields": "id,name,primary_page"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        businesses = data.get('data', [])
        
        if businesses:
            print(f"✅ Encontrados {len(businesses)} Business Manager(s):\n")
            for i, business in enumerate(businesses, 1):
                print(f"   {i}. {business.get('name', 'Sem nome')}")
                print(f"      ID: {business.get('id')}")
                if business.get('primary_page'):
                    print(f"      Página Principal: {business['primary_page'].get('name', 'N/A')}")
                print()
        else:
            print("⚠️  Nenhum Business Manager encontrado")
    else:
        print(f"❌ Erro ao buscar Business Managers: {response.status_code}")
        print(f"   Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro na requisição: {str(e)}")

print("\n" + "-"*60 + "\n")

# Teste 3: Listar Contas de Anúncios
print("3️⃣ Buscando Contas de Anúncios (Ad Accounts)...")
try:
    response = requests.get(
        f"{BASE_URL}/me/adaccounts",
        params={
            "access_token": META_ACCESS_TOKEN,
            "fields": "id,name,account_id,account_status,currency,timezone_name"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        ad_accounts = data.get('data', [])
        
        if ad_accounts:
            print(f"✅ Encontradas {len(ad_accounts)} Conta(s) de Anúncios:\n")
            for i, account in enumerate(ad_accounts, 1):
                print(f"   {i}. {account.get('name', 'Sem nome')}")
                print(f"      Account ID: {account.get('account_id')}")
                print(f"      ID: {account.get('id')}")
                print(f"      Status: {account.get('account_status', 'N/A')}")
                print(f"      Moeda: {account.get('currency', 'N/A')}")
                print(f"      Timezone: {account.get('timezone_name', 'N/A')}")
                print()
        else:
            print("⚠️  Nenhuma Conta de Anúncios encontrada")
    else:
        print(f"❌ Erro ao buscar Contas de Anúncios: {response.status_code}")
        print(f"   Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro na requisição: {str(e)}")

print("\n" + "="*60)
print("✅ Teste concluído!")
print("="*60)

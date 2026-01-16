"""
Script para sincronizar métricas de campanhas do Meta para o Supabase
Sincroniza dados históricos e mantém atualizado a cada execução
"""
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

# Configurar encoding para Windows
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
META_ACCESS_TOKEN = os.getenv('META_ACCESS_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validação de variáveis
if not all([META_ACCESS_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Variáveis de ambiente faltando. Verifique META_ACCESS_TOKEN, SUPABASE_URL e SUPABASE_KEY no .env")

# Inicializa cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações da API Meta
META_API_VERSION = "v21.0"
META_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"

# Delay entre requisições para evitar rate limits (em segundos)
REQUEST_DELAY = 0.1

# Máximo de tentativas para retry
MAX_RETRIES = 3


def log_error(client_id: Optional[str], tipo: str, status: str, mensagem: str, meta: Optional[Dict] = None):
    """Registra erro ou sucesso na tabela logs do Supabase"""
    try:
        log_data = {
            "client_id": client_id,
            "tipo": tipo,
            "status": status,
            "mensagem": mensagem,
            "meta": meta or {}
        }
        supabase.table("logs").insert(log_data).execute()
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")


def make_meta_request(url: str, params: Dict) -> Optional[Dict]:
    """
    Faz requisição à API do Meta com retry e tratamento de rate limits
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=30)
            
            # Rate limit - aguardar e tentar novamente
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limit atingido. Aguardando {retry_after} segundos...")
                time.sleep(retry_after)
                continue
            
            # Erro de autenticação
            if response.status_code == 401:
                error_data = response.json()
                raise Exception(f"Token inválido: {error_data.get('error', {}).get('message', 'Erro desconhecido')}")
            
            # Outros erros HTTP
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                raise Exception(f"Erro HTTP {response.status_code}: {error_data.get('error', {}).get('message', 'Erro desconhecido')}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise Exception(f"Erro na requisição após {MAX_RETRIES} tentativas: {str(e)}")
            time.sleep(2 ** attempt)  # Backoff exponencial
    
    return None


def get_campaigns(ad_account_id: str) -> List[Dict]:
    """
    Busca todas as campanhas de uma conta de anúncios
    """
    url = f"{META_BASE_URL}/{ad_account_id}/campaigns"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "id,name,status,created_time",
        "limit": 100
    }
    
    campaigns = []
    next_url = url
    
    while next_url:
        time.sleep(REQUEST_DELAY)
        data = make_meta_request(next_url, params if next_url == url else {})
        
        if not data:
            break
        
        campaigns.extend(data.get('data', []))
        
        # Paginação
        paging = data.get('paging', {})
        next_url = paging.get('next')
        if next_url:
            # Remove access_token dos params pois já está na URL
            params = {}
    
    return campaigns


def get_campaign_insights(campaign_id: str, since_date: Optional[str] = None, until_date: Optional[str] = None) -> List[Dict]:
    """
    Busca insights históricos de uma campanha
    """
    if not until_date:
        until_date = datetime.now().strftime("%Y-%m-%d")
    
        # Meta tem limite de 37 meses para insights
        # Usamos 30 dias para garantir dados recentes e performance rápida (solicitação do usuário)
        since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    url = f"{META_BASE_URL}/{campaign_id}/insights"
    params = {
        "access_token": META_ACCESS_TOKEN,
        "fields": "date_start,date_stop,spend,impressions,reach,clicks,actions",
        "time_range": json.dumps({"since": since_date, "until": until_date}),
        "time_increment": 1,  # Dados diários
        "limit": 100
    }
    
    insights = []
    next_url = url
    
    while next_url:
        time.sleep(REQUEST_DELAY)
        data = make_meta_request(next_url, params if next_url == url else {})
        
        if not data:
            break
        
        insights.extend(data.get('data', []))
        
        # Paginação
        paging = data.get('paging', {})
        next_url = paging.get('next')
        if next_url:
            params = {}
    
    return insights


def process_actions(actions: List[Dict]) -> tuple:
    """
    Processa array de ações e retorna (resultado_valor, resultado_nome)
    Prioriza ações de conversão/resultados principais.
    """
    if not actions:
        return (0, None)
    
    # Mapa de prioridade para definir o que conta como "Resultado"
    # Ordem de prioridade para buscar o resultado principal
    PRIORITY_ACTIONS = [
        'onsite_conversion.messaging_conversation_started_7d',
        'onsite_conversion.messaging_conversation_started_1d',
        'leads',
        'purchase',
        'initiate_checkout',
        'add_to_cart',
        'contact',
        'schedule',
        'submit_application',
        'link_click', # Fallback para campanhas de tráfego
        'post_engagement', # Fallback último caso
        'page_engagement'
    ]

    action_map = {a.get('action_type'): float(a.get('value', 0)) for a in actions}
    
    resultado_valor = 0.0
    resultado_nome = None

    # Tenta encontrar a ação prioritária
    for action_type in PRIORITY_ACTIONS:
        if action_type in action_map:
            resultado_valor = action_map[action_type]
            resultado_nome = action_type
            break
            
    # Se não encontrou nenhuma das prioritárias, pega a com maior valor
    # MAS exclui métricas agregadas que podem inflar o número (ex: total_messaging_connection)
    if resultado_nome is None and action_map:
        # Filtrar chaves indesejadas
        filtered_map = {k: v for k, v in action_map.items() if 'total_messaging_connection' not in k}
        
        if filtered_map:
            resultado_nome = max(filtered_map, key=filtered_map.get)
            resultado_valor = filtered_map[resultado_nome]
        else:
            # Se só sobrou lixo, retorna 0
            resultado_nome = None
            resultado_valor = 0.0

    return (float(resultado_valor), resultado_nome)


def sync_client_metrics(client_id: str, client_name: str, ad_account_id: str):
    """
    Sincroniza métricas de todas as campanhas de um cliente
    """
    print(f"\nProcessando cliente: {client_name} ({ad_account_id})")
    
    try:
        # Buscar campanhas
        campaigns = get_campaigns(ad_account_id)
        print(f"   Encontradas {len(campaigns)} campanha(s)")
        
        if not campaigns:
            log_error(client_id, "sync_meta_metrics", "warning", 
                     f"Nenhuma campanha encontrada para {client_name}",
                     {"ad_account_id": ad_account_id})
            return
        
        total_insights = 0
        
        # Processar cada campanha
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            campaign_name = campaign.get('name', 'Sem nome')
            campaign_status = campaign.get('status', 'UNKNOWN')
            
            # Pular campanhas arquivadas se desejar otimizar mais
            # if campaign_status == 'ARCHIVED': continue
            
            print(f"   Campanha: {campaign_name} ({campaign_status})")
            
            try:
                # Buscar insights históricos (últimos 30 dias por padrão)
                insights = get_campaign_insights(campaign_id)
                
                if not insights:
                    print(f"      AVISO: Nenhum insight encontrado")
                    continue
                
                print(f"      OK: {len(insights)} dia(s) de dados encontrados")
                
                # Processar cada dia de insights
                metrics_to_insert = []
                
                for insight in insights:
                    # Usar date_start como data de referência
                    date_str = insight.get('date_start')
                    if not date_str:
                        continue
                    
                    # Processar ações
                    actions = insight.get('actions', [])
                    resultado_valor, resultado_nome = process_actions(actions)
                    
                    # Preparar dados para inserção
                    metric_data = {
                        "client_id": client_id,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "data_referencia": date_str,
                        "investimento": float(insight.get('spend', 0)) if insight.get('spend') else 0.0,
                        "impressoes": int(insight.get('impressions', 0)) if insight.get('impressions') else 0,
                        "cliques_link": int(insight.get('clicks', 0)) if insight.get('clicks') else 0,
                        "alcance": int(insight.get('reach', 0)) if insight.get('reach') else 0,
                        "resultado_valor": resultado_valor, # Já garantido ser float (0.0 se vazio)
                        "resultado_nome": resultado_nome
                    }
                    
                    metrics_to_insert.append(metric_data)
                
                # Inserir/atualizar no Supabase em batch
                if metrics_to_insert:
                    # Usar upsert - Supabase faz upsert automaticamente se houver constraint única
                    # Caso contrário, vamos inserir em batch e tratar conflitos
                    batch_size = 50
                    inserted_count = 0
                    
                    for i in range(0, len(metrics_to_insert), batch_size):
                        batch = metrics_to_insert[i:i + batch_size]
                        try:
                            # Tentar inserir/atualizar em batch
                            result = supabase.table("dashboard_campaign_metrics").upsert(
                                batch
                            ).execute()
                            inserted_count += len(batch)
                        except Exception as e:
                            # Se batch falhar, tentar individualmente
                            print(f"      ⚠️  Erro no batch, tentando individualmente...")
                            for metric in batch:
                                try:
                                    # Verificar se já existe
                                    existing = supabase.table("dashboard_campaign_metrics").select("id").eq(
                                        "client_id", metric["client_id"]
                                    ).eq("campaign_id", metric["campaign_id"]).eq(
                                        "data_referencia", metric["data_referencia"]
                                    ).execute()
                                    
                                    if existing.data:
                                        # Atualizar
                                        supabase.table("dashboard_campaign_metrics").update(metric).eq(
                                            "id", existing.data[0]["id"]
                                        ).execute()
                                    else:
                                        # Inserir
                                        supabase.table("dashboard_campaign_metrics").insert(metric).execute()
                                    
                                    inserted_count += 1
                                except Exception as e2:
                                    print(f"      ERRO: Erro ao inserir metrica para {metric['data_referencia']}: {str(e2)}")
                    
                    total_insights += inserted_count
                    print(f"      OK: {inserted_count} metrica(s) inserida(s)/atualizada(s)")
                
            except Exception as e:
                error_msg = f"Erro ao processar campanha {campaign_name}: {str(e)}"
                print(f"      ERRO: {error_msg}")
                log_error(client_id, "sync_meta_metrics", "error", error_msg,
                         {"campaign_id": campaign_id, "campaign_name": campaign_name})
        
        # Log de sucesso
        log_error(client_id, "sync_meta_metrics", "success",
                 f"Sincronização concluída para {client_name}",
                 {"campaigns_processed": len(campaigns), "insights_processed": total_insights})
        
        print(f"   OK: Cliente {client_name} processado: {total_insights} metricas")
        
    except Exception as e:
        error_msg = f"Erro ao sincronizar cliente {client_name}: {str(e)}"
        print(f"   ERRO: {error_msg}")
        log_error(client_id, "sync_meta_metrics", "error", error_msg,
                 {"ad_account_id": ad_account_id})


def main():
    """
    Função principal: busca clientes ativos e sincroniza métricas
    """
    print("=" * 60)
    print("Iniciando sincronizacao Meta -> Supabase")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        # Buscar clientes ativos
        print("\nBuscando clientes ativos...")
        clients_response = supabase.table("clients").select("id,cliente,conta_anuncio").eq("ativo", True).execute()
        clients = clients_response.data
        
        if not clients:
            print("AVISO: Nenhum cliente ativo encontrado")
            return
        
        print(f"OK: {len(clients)} cliente(s) ativo(s) encontrado(s)\n")
        
        # Processar cada cliente
        for client in clients:
            client_id = client.get('id')
            client_name = client.get('cliente', 'Sem nome')
            conta_anuncio = client.get('conta_anuncio')
            
            if not conta_anuncio:
                print(f"AVISO: Cliente {client_name} sem conta_anuncio. Pulando...")
                continue
            
            # Garantir formato correto (act_XXXXXXXXX)
            if not conta_anuncio.startswith('act_'):
                conta_anuncio = f"act_{conta_anuncio.replace('act_', '')}"
            
            try:
                sync_client_metrics(client_id, client_name, conta_anuncio)
            except Exception as e:
                print(f"ERRO CRÍTICO ao processar cliente {client_name}: {str(e)}")
                # Continue processando outros clientes
                continue
        
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"OK: Sincronizacao concluida em {elapsed_time:.2f} segundos")
        print("=" * 60)
        
    except Exception as e:
        error_msg = f"Erro fatal na sincronizacao: {str(e)}"
        print(f"\nERRO: {error_msg}")
        log_error(None, "sync_meta_metrics", "error", error_msg)
        raise


if __name__ == "__main__":
    main()

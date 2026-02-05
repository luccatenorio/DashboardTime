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
        "fields": "id,name,status,created_time,objective",
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


def process_actions(actions: List[Dict], objective: str = None, campaign_name: str = "") -> tuple:
    """
    Processa array de ações e retorna (resultado_valor, resultado_nome)
    Prioriza ações de conversão/resultados principais.
    """
    if not actions:
        return (0.0, None)
    
    # Tratamento especial para Engajamento:
    # Se for campanha de MENSAGEM (wpp, direct, etc), é estrito.
    # Se for campanha de ENGAJAMENTO (post, video view, etc), aceita apenas post_engagement.
    is_message_campaign = False
    if campaign_name:
        normalized_name = campaign_name.lower()
        msg_keywords = ['mensagem', 'message', 'direct', 'whatsapp', 'wpp', 'chat', 'msg']
        if any(k in normalized_name for k in msg_keywords):
            is_message_campaign = True

    action_map = {a.get('action_type'): float(a.get('value', 0)) for a in actions}

    # ---- LÓGICA DE SELEÇÃO DE MÉTRICA ----
    
    # 1. OUTCOME_ENGAGEMENT
    if objective == 'OUTCOME_ENGAGEMENT':
        if is_message_campaign:
             # Campanha de mensagem: busca conversas iniciadas
             pass # Segue prioridade padrão (messaging_conversation_started está no topo)
        else:
             # Campanha de engajamento genérico: busca estritamente 'post_engagement'
             val = action_map.get('post_engagement', 0)
             if val > 0:
                 return (float(val), 'post_engagement')
             return (0.0, None) # Não aceita clicks aqui
             
    # 2. OUTCOME_TRAFFIC ou OUTCOME_AWARENESS
    if objective in ['OUTCOME_TRAFFIC', 'OUTCOME_AWARENESS']:
        # Busca estritamente 'instagram_profile_visits'
        val = action_map.get('instagram_profile_visits', 0)
        # Fallback para profile visits se vier com outro nome (ex: checkin, ou variations)
        # mas solicitado explícito instagram_profile_visits.
        if val > 0:
            return (float(val), 'instagram_profile_visits')
        
        # Se zerado, tenta outras actions de "Visita" se existirem, ou retorna zero?
        # User requested: "PEGUE o valor da action instagram_profile_visits".
        # Se não tiver, retorna 0 (ou tenta link_click se for Traffic? O user disse "Post do Instagram deve mostrar 300").
        # O user disse "PEGUE o valor da action instagram_profile_visits".
        # Vamos tentar link_click como fallback APENAS se for Traffic e profile_visit zerado?
        # User: "Se campaign_objective == ... PEGUE o valor da action instagram_profile_visits"
        # Vou arriscar um fallback para link_click se profile_visits for 0, mas priorizando profile_visits.
        val_clicks = action_map.get('link_click', 0)
        # Entretanto, o pedido foi "NÃO pegue clicks... PEGUE o valor de post_engagement" para Engagement.
        # Para Traffic ele disse "PEGUE o valor da action instagram_profile_visits".
        # Se eu não tiver esse valor, vai zerar. Vou adicionar fallback SEGURO para clicks se objetivo for TRAFEGO apenas.
        if objective == 'OUTCOME_TRAFFIC' and val_clicks > 0:
             # Se não achou profile_visits, mas tem click, usa click? O user reclamou de clicks em engagement.
             # Vou manter estrito por enquanto. Se zerar, ajustamos.
             return (0.0, None)
        return (0.0, None)

    # 3. OUTCOME_LEADS, OUTCOME_SALES, MESSAGES, etc (Padrão)
    
    # Mapa de prioridade para definir o que conta como "Resultado"
    PRIORITY_ACTIONS = [
        'onsite_conversion.messaging_conversation_started_7d',
        'onsite_conversion.messaging_conversation_started_1d',
        'lead',
        'leads',
        'offsite_conversion.fb_pixel_lead',
        'purchase',
        'initiate_checkout',
        'add_to_cart',
        'contact',
        'schedule',
        'submit_application',
        'link_click', # Fallback para campanhas de LEADS/TRAFEGO se não for restrito
        'post_engagement', 
        'page_engagement',
        'video_view' 
    ]
    
    # Restaura lista STRICT original (sem engagement, pois já tratamos acima)
    STRICT_OBJECTIVES = [
        'OUTCOME_LEADS', 
        'OUTCOME_SALES',
        'LEAD_GENERATION',
        'CONVERSIONS',
        'MESSAGES'
    ]

    # Tenta encontrar a ação prioritária
    for action_type in PRIORITY_ACTIONS:
        if action_type in action_map:
            if action_type in ['link_click', 'post_engagement', 'page_engagement', 'video_view']:
                if objective and objective in STRICT_OBJECTIVES:
                    continue # Pula este fallback para objetivos estritos
            
            resultado_valor = action_map[action_type]
            resultado_nome = action_type
            return (float(resultado_valor), resultado_nome)
            
    # Se chegou aqui, não achou prioritária válida
    return (0.0, None)


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
            
            print(f"   Campanha: {campaign_name} ({campaign_status}) - Obj: {campaign.get('objective')}")
            
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
                    resultado_valor, resultado_nome = process_actions(actions, campaign.get('objective'), campaign_name)
                    
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
                
                # Buscar IDs existentes para garantir UPDATE correto (evitar duplicatas)
                # Formar lista de chaves para busca
                dates = [m['data_referencia'] for m in metrics_to_insert]
                existing_map = {}
                
                if dates:
                    try:
                        # Buscar registros existentes para este cliente/campanha nessas datas
                        existing_response = supabase.table("dashboard_campaign_metrics").select("id, data_referencia")\
                            .eq("client_id", client_id)\
                            .eq("campaign_id", campaign_id)\
                            .in_("data_referencia", dates)\
                            .execute()
                        
                        if existing_response.data:
                            for row in existing_response.data:
                                existing_map[row['data_referencia']] = row['id']
                    except Exception as e:
                        print(f"      ⚠️  Erro ao buscar existentes: {str(e)}")

                # Atualizar metric_data com IDs existentes
                for metric in metrics_to_insert:
                    if metric['data_referencia'] in existing_map:
                        metric['id'] = existing_map[metric['data_referencia']]

                # Inserir/atualizar no Supabase em batch
                if metrics_to_insert:
                    batch_size = 50
                    inserted_count = 0
                    
                    for i in range(0, len(metrics_to_insert), batch_size):
                        batch = metrics_to_insert[i:i + batch_size]
                        try:
                            # Upsert deve funcionar agora que temos IDs para os existentes
                            result = supabase.table("dashboard_campaign_metrics").upsert(
                                batch
                            ).execute()
                            inserted_count += len(batch)
                        except Exception as e:
                            # Se batch falhar, tentar individualmente
                            print(f"      ⚠️  Erro no batch, tentando individualmente: {str(e)}")
                            for metric in batch:
                                try:
                                    supabase.table("dashboard_campaign_metrics").upsert(metric).execute()
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


import argparse

def main():
    """
    Função principal: busca clientes ativos e sincroniza métricas
    """
    parser = argparse.ArgumentParser(description='Sincronizar métricas do Meta Ads.')
    parser.add_argument('--client', type=str, help='Nome (ou parte do nome) do cliente para sincronizar apenas ele.')
    args = parser.parse_args()

    print("=" * 60)
    print("Iniciando sincronizacao Meta -> Supabase")
    if args.client:
        print(f"MODO FILTRADO: Apenas clientes contendo '{args.client}'")
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
            
        # Filtrar se argumento foi passado
        if args.client:
            filtered_clients = [
                c for c in clients 
                if args.client.lower() in c.get('cliente', '').lower()
            ]
            if not filtered_clients:
                 print(f"AVISO: Nenhum cliente encontrado com o termo '{args.client}'")
                 return
            clients = filtered_clients
        
        print(f"OK: {len(clients)} cliente(s) para processar\n")
        
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

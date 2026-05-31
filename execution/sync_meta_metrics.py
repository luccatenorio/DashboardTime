"""
Script para sincronizar métricas de campanhas do Meta para o Supabase
Sincroniza dados históricos e mantém atualizado a cada execução
"""
import os
import sys
import re
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

# Force UTF-8 stdout/stderr on Windows so emojis in campaign names don't crash print()
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
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
    if not since_date:
        # Janela rolante de 30 dias (Meta retém até 37 meses; mantemos curto para velocidade)
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


def process_actions(actions: List[Dict], objective: str = None, campaign_name: str = "", insight_data: Dict = None) -> tuple:
    """
    Processa array de ações e retorna (resultado_valor, resultado_nome).

    Regra de negócio Trime: 1 cadastro = 1 lead, 1 conversa iniciada = 1 lead.
    Quando a mesma campanha tem cadastro + mensagem no mesmo dia, SOMAR os dois.
    Não somar tipos duplicados (ex: messaging_started_7d e _1d são overlapping —
    pega um único representante por categoria).
    """
    if not actions:
        return (0.0, None)

    action_map = {a.get('action_type'): float(a.get('value', 0)) for a in actions}

    # Cada tupla = uma categoria comercial. Pega o PRIMEIRO key com valor > 0
    # de cada categoria (evita duplicar attribution windows do mesmo evento).
    categories = [
        ('cadastro', ['lead', 'leads', 'onsite_conversion.lead_grouped',
                      'offsite_conversion.fb_pixel_lead', 'submit_application']),
        ('mensagem', ['onsite_conversion.messaging_conversation_started_7d',
                      'onsite_conversion.messaging_conversation_started_1d',
                      'omnichannel_messaging_conversation_started_7d',
                      'omnichannel_messaging_conversation_started',
                      'onsite_conversion.messaging_first_reply']),
        ('contato', ['contact', 'schedule']),
        ('compra', ['purchase']),
    ]

    total = 0.0
    nomes = []
    for _, keys in categories:
        for k in keys:
            v = action_map.get(k, 0)
            if v > 0:
                total += v
                nomes.append(k)
                break  # próxima categoria — não soma janelas do mesmo evento

    if total <= 0:
        return (0.0, None)
    return (total, ','.join(nomes))


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
                    resultado_valor, resultado_nome = process_actions(actions, campaign.get('objective'), campaign_name, insight)
                    
                    # Preparar dados para inserção
                    metric_data = {
                        "client_id": client_id,
                        "campaign_id": campaign_id,
                        "campaign_name": campaign_name,
                        "campaign_status": campaign_status,
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

                # Separa atualizações e inserções para garantir consistência de chaves no batch
                updates = []
                inserts = []
                
                for metric in metrics_to_insert:
                    if metric['data_referencia'] in existing_map:
                        metric['id'] = existing_map[metric['data_referencia']]
                        updates.append(metric)
                    else:
                        inserts.append(metric)

                # Função auxiliar para batch upsert
                def batch_upsert(items, label="items"):
                    if not items: return 0
                    count = 0
                    batch_size = 50
                    for i in range(0, len(items), batch_size):
                        batch = items[i:i + batch_size]
                        try:
                            # Upsert deve funcionar agora que temos IDs para os existentes
                            result = supabase.table("dashboard_campaign_metrics").upsert(
                                batch
                            ).execute()
                            count += len(batch)
                        except Exception as e:
                            # Se batch falhar, tentar individualmente
                            print(f"      ⚠️  Erro no batch ({label}), tentando individualmente: {str(e)}")
                            for metric in batch:
                                try:
                                    supabase.table("dashboard_campaign_metrics").upsert(metric).execute()
                                    count += 1
                                except Exception as e2:
                                    print(f"      ERRO: Erro ao inserir metrica para {metric['data_referencia']}: {str(e2)}")
                    return count

                # Executar batches
                updated_count = batch_upsert(updates, "updates")
                inserted_count = batch_upsert(inserts, "inserts")
                
                total_ops = updated_count + inserted_count
                total_insights += total_ops
                print(f"      OK: {total_ops} metrica(s) processada(s) ({updated_count} updates, {inserted_count} inserts)")
                
            except Exception as e:
                error_msg = f"Erro ao processar campanha {campaign_name}: {str(e)}"
                print(f"      ERRO: {error_msg}")
                log_error(client_id, "sync_meta_metrics", "error", error_msg,
                         {"campaign_id": campaign_id, "campaign_name": campaign_name})
        
        # Log de sucesso (campaign-level)
        log_error(client_id, "sync_meta_metrics", "success",
                 f"Sincronização concluída para {client_name}",
                 {"campaigns_processed": len(campaigns), "insights_processed": total_insights})

        print(f"   OK: Cliente {client_name} processado: {total_insights} metricas")

    except Exception as e:
        error_msg = f"Erro ao sincronizar cliente {client_name}: {str(e)}"
        print(f"   ERRO: {error_msg}")
        log_error(client_id, "sync_meta_metrics", "error", error_msg,
                 {"ad_account_id": ad_account_id})

    # ----------------------------------------------------------------
    # ACCOUNT-LEVEL TOTALS + FUNDING (deduplicated reach 7d/30d, saldo prepago, status)
    # Roda mesmo se o loop de campanhas acima levantou — last_sync_at sempre reflete a tentativa.
    # ----------------------------------------------------------------
    update_data = {'last_sync_at': datetime.now().isoformat()}

    for preset, suffix in (('last_30d', '30d'), ('last_7d', '7d')):
        try:
            resp = requests.get(
                f"{META_BASE_URL}/{ad_account_id}/insights",
                params={
                    'access_token': META_ACCESS_TOKEN,
                    'level': 'account',
                    'date_preset': preset,
                    'fields': 'reach,impressions,spend',
                },
                timeout=30,
            )
            if resp.status_code == 200:
                rows = resp.json().get('data', [])
                if rows:
                    row = rows[0]
                    update_data[f'account_reach_{suffix}'] = int(row.get('reach', 0))
                    update_data[f'account_impressions_{suffix}'] = int(row.get('impressions', 0))
                    update_data[f'account_spend_{suffix}'] = float(row.get('spend', 0))
                    print(f"      [CONTA {suffix}] Reach: {row.get('reach')} | Impr: {row.get('impressions')} | Spend: {row.get('spend')}")
        except Exception as e_acc:
            print(f"      ERRO Account Insights ({preset}): {e_acc}")

    # Funding info (saldo prepago, status, total gasto vida) — campos da conta, não dos insights
    try:
        resp = requests.get(
            f"{META_BASE_URL}/{ad_account_id}",
            params={
                'access_token': META_ACCESS_TOKEN,
                'fields': 'name,balance,currency,account_status,amount_spent,spend_cap,funding_source_details',
            },
            timeout=30,
        )
        if resp.status_code == 200:
            acc = resp.json()
            update_data['account_currency'] = acc.get('currency') or 'BRL'
            update_data['account_status'] = int(acc.get('account_status') or 0)
            # Meta retorna amount_spent e spend_cap em centavos
            update_data['account_amount_spent'] = float(acc.get('amount_spent') or 0) / 100
            update_data['account_spend_cap'] = float(acc.get('spend_cap') or 0) / 100

            # Saldo: preferir display_string (já em R$), fallback para balance/100
            balance = 0.0
            funding = acc.get('funding_source_details') or {}
            display = funding.get('display_string') or ''
            if display:
                update_data['account_funding_display'] = display
                m = re.search(r'R\$\s*([\d.,]+)', display)
                if m:
                    raw = m.group(1).replace('.', '').replace(',', '.')
                    try:
                        balance = float(raw)
                    except ValueError:
                        pass
            if not balance and acc.get('balance'):
                balance = float(acc['balance']) / 100
            update_data['account_balance'] = balance

            # Tipo de funding: type=1 normalmente é prepago
            f_type = funding.get('type')
            if f_type == 1:
                update_data['account_funding_type'] = 'prepaid'
            elif f_type:
                update_data['account_funding_type'] = 'postpaid'

            print(f"      [SALDO] {display or f'R$ {balance:.2f}'} | status={update_data['account_status']} | type={update_data.get('account_funding_type','?')}")
    except Exception as e_fund:
        print(f"      ERRO Funding: {e_fund}")

    try:
        supabase.table('clients').update(update_data).eq('id', client_id).execute()
    except Exception as ex_db:
        # Fallback: tenta gravar só o que existe garantido (last_sync_at + 30d)
        print(f"      AVISO DB: Falha ao gravar tudo ({ex_db}). Tentando fallback mínimo...")
        safe = {k: v for k, v in update_data.items() if k in ('last_sync_at', 'account_reach_30d', 'account_impressions_30d', 'account_spend_30d')}
        try:
            supabase.table('clients').update(safe).eq('id', client_id).execute()
        except Exception as ex_db2:
            print(f"      AVISO DB: Fallback também falhou: {ex_db2}")


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

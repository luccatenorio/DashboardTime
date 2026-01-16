# Diretiva: Sincronização de Métricas Meta → Supabase

## Objetivo
Sincronizar métricas de campanhas do Meta (Facebook Ads) para a tabela `dashboard_campaign_metrics` no Supabase, mantendo os dados atualizados e históricos.

## Entradas
- Token de acesso do Meta (`META_ACCESS_TOKEN` no `.env`)
- URL e chave do Supabase (`SUPABASE_URL` e `SUPABASE_KEY` no `.env`)
- Lista de clientes ativos da tabela `clients` no Supabase

## Processo

### 1. Inicialização
- Carregar variáveis de ambiente do `.env`
- Conectar ao Supabase usando `supabase-py`
- Validar token do Meta fazendo uma chamada de teste

### 2. Buscar Clientes Ativos
- Query no Supabase: `SELECT id, cliente, conta_anuncio FROM clients WHERE ativo = true`
- Para cada cliente, extrair `conta_anuncio` (formato: `act_XXXXXXXXX`)

### 3. Para Cada Cliente

#### 3.1 Buscar Campanhas
- Endpoint: `GET https://graph.facebook.com/v21.0/{conta_anuncio}/campaigns`
- Parâmetros:
  - `fields=id,name,status,created_time`
  - `access_token={META_ACCESS_TOKEN}`
- Filtrar campanhas ativas ou todas (incluir todas para histórico)

#### 3.2 Para Cada Campanha

##### Buscar Insights Históricos
- Endpoint: `GET https://graph.facebook.com/v21.0/{campaign_id}/insights`
- Parâmetros:
  - `fields=date,spend,impressions,reach,link_clicks,actions`
  - `time_range={"since":"{DATA_3_ANOS_ATRAS}","until":"{DATA_ATUAL}"}` (Respeitando limite de 37 meses da API)
  - `time_increment=1` (dados diários)
  - `access_token={META_ACCESS_TOKEN}`

##### Processar Métricas
Para cada dia retornado:
- `date` → `data_referencia`
- `spend` → `investimento` (converter para numeric)
- `impressions` → `impressoes` (integer)
- `reach` → `alcance` (integer)
- `link_clicks` → `cliques_link` (integer)
- `actions` → processar array de ações:
  - Somar todos os `value` → `resultado_valor`
  - Concatenar tipos únicos de `action_type` → `resultado_nome` (ex: "lead,onsite_conversion")

##### Inserir/Atualizar no Supabase
- Usar UPSERT baseado em: `client_id + campaign_id + data_referencia`
- Query: `INSERT INTO dashboard_campaign_metrics (...) VALUES (...) ON CONFLICT (...) DO UPDATE SET ...`

### 4. Tratamento de Erros

#### Rate Limits da Meta API
- Se receber erro 429 (Too Many Requests):
  - Implementar retry com backoff exponencial
  - Aguardar tempo indicado no header `Retry-After`
  - Máximo de 3 tentativas

#### Conta Inválida ou Sem Acesso
- Logar erro na tabela `logs` do Supabase
- Continuar com próximo cliente
- Não interromper processo

#### Dados Faltantes
- Campos nulos são aceitos na tabela
- Converter valores vazios para NULL
- Validar tipos antes de inserir

### 5. Logging
- Registrar início e fim da sincronização
- Contar campanhas processadas por cliente
- Registrar erros na tabela `logs`:
  - `client_id`: ID do cliente (ou NULL se erro geral)
  - `tipo`: "sync_meta_metrics"
  - `status`: "success" ou "error"
  - `mensagem`: Descrição do erro ou sucesso
  - `meta`: JSON com detalhes (ex: número de campanhas, erros específicos)

## Saídas
- Tabela `dashboard_campaign_metrics` atualizada com métricas históricas e atuais
- Logs na tabela `logs` para auditoria

## Edge Cases

1. **Campanha sem insights**: Pular campanha e logar
2. **Limite de Retenção (37 meses)**: A API do Meta retorna erro 400 se solicitar dados > 37 meses. O script deve calcular `since` dinamicamente (hoje - 3 anos).
2. **Múltiplas ações no mesmo dia**: Agregar valores e concatenar tipos
3. **Data futura**: Filtrar datas futuras (não devem existir, mas validar)
4. **Primeira execução**: Processar todos os dados históricos (pode demorar)
5. **Execuções subsequentes**: Processar apenas últimos 7 dias para eficiência (ou verificar última data sincronizada)

## Performance
- Processar em batches de 10 campanhas por vez
- Implementar delay entre requisições (100ms) para evitar rate limits
- Primeira execução pode levar várias horas dependendo do volume histórico

## Manutenção
- Verificar logs regularmente
- Monitorar rate limits da API
- Atualizar esta diretiva se descobrir novos edge cases ou melhorias

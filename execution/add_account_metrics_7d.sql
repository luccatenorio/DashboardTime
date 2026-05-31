-- Adiciona colunas 7d para alcance/impressões/gasto deduplicado pela Meta API.
-- Sem isso, o dashboard mostra reach inflado quando o usuário seleciona "Últimos 7 dias".

ALTER TABLE public.clients
ADD COLUMN IF NOT EXISTS account_reach_7d BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS account_impressions_7d BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS account_spend_7d NUMERIC DEFAULT 0;

-- Garantir unique constraint para upsert correto de métricas diárias
-- (sem isso, o sync pode inserir duplicatas se o lookup de IDs existentes falhar)
CREATE UNIQUE INDEX IF NOT EXISTS uq_dashboard_metric_client_campaign_date
  ON public.dashboard_campaign_metrics (client_id, campaign_id, data_referencia);

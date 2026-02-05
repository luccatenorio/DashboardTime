
-- Run this in your Supabase SQL Editor to enable Account Level Totals

ALTER TABLE public.clients
ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMPTZ DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS account_reach_30d BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS account_impressions_30d BIGINT DEFAULT 0,
ADD COLUMN IF NOT EXISTS account_spend_30d NUMERIC DEFAULT 0;

-- Optional: Create index if needed (not strictly necessary for small tables)
-- CREATE INDEX IF NOT EXISTS idx_clients_last_sync ON public.clients(last_sync_at);

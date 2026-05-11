import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://werkiwmegzqdsgfhcglb.supabase.co'
// Usando a chave anon do .env para acesso seguro
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indlcmtpd21lZ3pxZHNnZmhjZ2xiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1OTQxMDksImV4cCI6MjA4OTE3MDEwOX0.xHztZ38cpcaMop97PFwSqDQXg92AXWCEDgjBmC3xV7E'

export const supabase = createClient(supabaseUrl, supabaseKey)

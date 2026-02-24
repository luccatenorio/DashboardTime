import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY
const supabase = createClient(supabaseUrl, supabaseKey)

async function test() {
    const { data } = await supabase.from('dashboard_campaign_metrics').select('data_referencia, investimento, resultado_valor').eq('campaign_name', 'CA[MENSAGEM][VIC SERRANO][Victor] 12.02').order('data_referencia')
    console.table(data)
}
test()

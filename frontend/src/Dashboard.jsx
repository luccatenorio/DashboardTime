import React, { useState, useEffect, useMemo } from 'react'
import { supabase } from './lib/supabase'
import {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart
} from 'recharts'
import {
    LayoutDashboard, Users, DollarSign, MousePointer2, Eye, TrendingUp, Activity, Filter
} from 'lucide-react'

const Dashboard = () => {
    const [isAdmin, setIsAdmin] = useState(false)
    const [selectedClient, setSelectedClient] = useState(null)
    const [clientName, setClientName] = useState('') // Name of the displayed client
    const [clients, setClients] = useState([])
    const [metrics, setMetrics] = useState([])
    const [loading, setLoading] = useState(true)
    const [dateRange, setDateRange] = useState('30')
    const [errorObj, setErrorObj] = useState(null)
    const [accessGranted, setAccessGranted] = useState(false)
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768)
    const [clientDetails, setClientDetails] = useState(null) // metadata like sync time, totals
    const [showCreateForm, setShowCreateForm] = useState(false)
    const [newClientName, setNewClientName] = useState('')
    const [newClientAccount, setNewClientAccount] = useState('')
    const [creating, setCreating] = useState(false)
    const [createdLink, setCreatedLink] = useState(null)
    const [copiedId, setCopiedId] = useState(null)
    const [showOnlyActive, setShowOnlyActive] = useState(false)
    const [waGroups, setWaGroups] = useState(null) // null = nao carregado, [] = vazio
    const [loadingGroups, setLoadingGroups] = useState(false)
    const [sendingFeedback, setSendingFeedback] = useState(null) // 'all' | client_id | null
    const [feedbackResult, setFeedbackResult] = useState(null)
    const [editingGroup, setEditingGroup] = useState(false)

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 768)
        window.addEventListener('resize', handleResize)
        return () => window.removeEventListener('resize', handleResize)
    }, [])

    useEffect(() => {
        fetchData()

        // Listen for hash changes
        window.addEventListener('hashchange', fetchData)
        return () => window.removeEventListener('hashchange', fetchData)
    }, []) // Re-fetch when date range changes

    async function fetchData() {
        try {
            setLoading(true)
            setErrorObj(null)
            setAccessGranted(false) // Reset access
            setIsAdmin(false)
            setClientDetails(null)
            // setSelectedClient(null) // REMOVED: Don't force reset selected client on re-fetch

            // Hash Routing Logic
            const hash = window.location.hash
            let hashClient = null // Initialize variable

            if (!hash || !hash.startsWith('#/c/')) {
                setLoading(false)
                console.log('No access hash found')
                return // Access Denied (Implicitly)
            }

            const code = hash.split('#/c/')[1].replace(/\/$/, '').trim()
            console.log('Detected Client Hash (Trimmed):', code)

            // ADMIN HASH CHECK
            const ADMIN_HASH = 'master_key_admin_access_2025' // Hardcoded Admin Key

            if (code === ADMIN_HASH) {
                console.log('Admin Access Granted')
                setAccessGranted(true)
                setIsAdmin(true)
                setSelectedClient(null) // Start with NO client selected (Show Grid)
                setClientName('')

                // Fetch ALL clients for the grid
                console.log('Fetching Clients for Admin...')
                const { data: clientsData, error: clientsError } = await supabase
                    .from('clients')
                    .select('*')
                    .eq('ativo', true)
                    .order('cliente')

                if (clientsError) throw clientsError
                setClients(clientsData || [])
                loadWhatsAppGroups() // pre-carrega grupos pra dropdown ja vir populado
                setLoading(false)
                return // Stop here, wait for user to pick a client
            }

            // NORMAL CLIENT FLOW
            // Find client by hash (stored in observacoes)
            const { data: clientData, error: clientError } = await supabase
                .from('clients')
                .select('*')
                .eq('observacoes', code)
                .maybeSingle()

            if (clientError) {
                console.error('Client hash lookup error:', clientError)
                throw clientError
            }

            if (clientData) {
                console.log('Authorized Client:', clientData)
                hashClient = clientData
                setSelectedClient(clientData.id)
                setClientName(clientData.cliente) // Set Name Here
                setClientDetails(clientData) // Store metadata
                setAccessGranted(true)
            } else {
                console.error('Hash not found in DB')
                throw new Error('Código de acesso inválido.')
            }

            // Fetch metrics for the SPECIFIC client
            console.log('Fetching Metrics...')
            let query = supabase
                .from('dashboard_campaign_metrics')
                .select('*')

            if (hashClient) {
                query = query.eq('client_id', hashClient.id)
            }

            // Bump limit to avoid truncation
            const { data: metricsData, error: metricsError } = await query.limit(10000)

            if (metricsError) throw metricsError

            setMetrics(metricsData || [])
            setLoading(false)

        } catch (error) {
            console.error('Error fetching data:', error)
            setErrorObj(error)
            setLoading(false)
        }
    }

    // Helper to filter metrics for the view
    // If Admin picked a client, filter just that client.
    // If Normal user, it's already filtered by DB query, but good to be safe.
    const displayedMetrics = isAdmin
        ? (selectedClient ? metrics.filter(m => m.client_id === selectedClient) : []) // Admin + Selection
        : metrics // Normal user (already filtered)

    const generateAccessHash = () => {
        const bytes = new Uint8Array(18)
        crypto.getRandomValues(bytes)
        return Array.from(bytes, b => b.toString(36)).join('').replace(/[^a-z0-9]/g, '').slice(0, 30)
    }

    const handleCreateClient = async () => {
        const name = newClientName.trim()
        let account = newClientAccount.trim().replace(/^act_/, '')
        if (!name || !account) {
            alert('Preencha nome e ID da conta de anúncio')
            return
        }
        if (!/^\d+$/.test(account)) {
            alert('O ID da conta deve conter apenas números (sem o prefixo act_)')
            return
        }
        setCreating(true)
        try {
            const { data: existing } = await supabase
                .from('clients')
                .select('id, cliente, observacoes')
                .ilike('cliente', name)
                .maybeSingle()

            const hash = existing?.observacoes && existing.observacoes.length >= 20
                ? existing.observacoes
                : generateAccessHash()

            if (existing) {
                await supabase.from('clients').update({
                    conta_anuncio: `act_${account}`,
                    ativo: true,
                    observacoes: hash
                }).eq('id', existing.id)
            } else {
                await supabase.from('clients').insert({
                    cliente: name,
                    conta_anuncio: `act_${account}`,
                    ativo: true,
                    observacoes: hash
                })
            }

            const link = `${window.location.origin}/#/c/${hash}`
            setCreatedLink(link)

            const webhookUrl = import.meta.env.VITE_N8N_SYNC_WEBHOOK
            if (webhookUrl) {
                fetch(webhookUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cliente: name, conta_anuncio: `act_${account}` })
                }).catch(() => {})
            }

            const { data: refreshed } = await supabase
                .from('clients')
                .select('*')
                .eq('ativo', true)
                .order('cliente')
            setClients(refreshed || [])

            setNewClientName('')
            setNewClientAccount('')
        } catch (e) {
            console.error(e)
            alert('Erro ao criar cliente: ' + (e.message || e))
        } finally {
            setCreating(false)
        }
    }

    const loadWhatsAppGroups = async () => {
        if (waGroups || loadingGroups) return
        const url = import.meta.env.VITE_N8N_LIST_GROUPS
        if (!url) { setWaGroups([]); return }
        setLoadingGroups(true)
        try {
            const r = await fetch(url)
            const data = await r.json()
            setWaGroups(Array.isArray(data?.groups) ? data.groups : [])
        } catch (e) {
            console.error('list groups failed', e)
            setWaGroups([])
        } finally {
            setLoadingGroups(false)
        }
    }

    const saveClientGroup = async (clientId, jid, name) => {
        try {
            await supabase.from('clients').update({
                whatsapp_group_jid: jid || null,
                whatsapp_group_name: name || null
            }).eq('id', clientId)
            setClients(prev => prev.map(c => c.id === clientId ? { ...c, whatsapp_group_jid: jid, whatsapp_group_name: name } : c))
            if (clientDetails && clientDetails.id === clientId) {
                setClientDetails(prev => ({ ...prev, whatsapp_group_jid: jid, whatsapp_group_name: name }))
            }
        } catch (e) {
            alert('Erro ao salvar grupo: ' + (e.message || e))
        }
    }

    const triggerFeedback = async (payload, label) => {
        const url = import.meta.env.VITE_N8N_SEND_FEEDBACK
        if (!url) { alert('Webhook de feedback não configurado'); return }
        if (!confirm(`Disparar mensagem de feedback ${label}? Isso vai enviar mensagens WhatsApp reais.`)) return
        setSendingFeedback(payload.all ? 'all' : payload.client_id)
        setFeedbackResult(null)
        try {
            const r = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            const txt = await r.text()
            setFeedbackResult({ ok: r.ok, status: r.status, body: txt.slice(0, 300) })
        } catch (e) {
            setFeedbackResult({ ok: false, status: 0, body: String(e) })
        } finally {
            setSendingFeedback(null)
            setTimeout(() => setFeedbackResult(null), 6000)
        }
    }

    // Admin: Function to load metrics when a client is clicked
    const handleAdminSelectClient = async (clientId) => {
        setLoading(true)
        setSelectedClient(clientId)

        // Find name from clients list
        const c = clients.find(cl => cl.id === clientId)
        if (c) {
            setClientName(c.cliente)
            setClientDetails(c) // Set metadata from admin list
        }

        try {
            const { data: metricsData, error: metricsError } = await supabase
                .from('dashboard_campaign_metrics')
                .select('*')
                .eq('client_id', clientId)
                .limit(10000)

            if (metricsError) throw metricsError
            setMetrics(metricsData || [])
        } catch (e) {
            console.error(e)
            alert('Erro ao carregar dados do cliente')
        } finally {
            setLoading(false)
        }
    }

    // --- DATA PROCESSING (Restored) ---

    // Metric Classification
    const COMMERCIAL_METRICS = [
        'lead', 'leads',
        'messaging_conversation_started_7d',
        'messaging_conversation_started_1d',
        'omnichannel_messaging_conversation_started',
        'messaging_first_reply',
        'messaging_conversation_started',
        'fb_pixel_lead',
        'purchase',
        'initiate_checkout',
        'add_to_cart',
        'contact',
        'schedule',
        'submit_application'
    ]

    const VANITY_METRICS = [
        'link_click',
        'post_engagement',
        'page_engagement',
        'video_view',
        'instagram_profile_visits',
        'thumbs_up'
    ]

    const isCommercial = (metricName) => {
        if (!metricName) return false
        return COMMERCIAL_METRICS.includes(metricName) || COMMERCIAL_METRICS.some(m => metricName.includes(m))
    }

    // Filter and Aggregate Data
    const filteredData = useMemo(() => {
        if (!Array.isArray(metrics)) return []

        let data = metrics

        // Client Filter (Redundant if filtered by DB, but safe)
        if (selectedClient && selectedClient !== 'all') {
            data = data.filter(m => m.client_id === selectedClient)
        }

        // Date Range Filter
        const today = new Date()

        // Determina a data final
        let includeToday = dateRange.includes('_today')
        let daysToSubtract = parseInt(dateRange.replace('_today', ''))

        // Data de corte inicial (ex: há 30 dias)
        const cutoffDate = new Date()
        cutoffDate.setDate(today.getDate() - daysToSubtract)
        const cutoffStr = cutoffDate.getFullYear() + '-' +
            String(cutoffDate.getMonth() + 1).padStart(2, '0') + '-' +
            String(cutoffDate.getDate()).padStart(2, '0')

        // Data de corte final (ontem ou hoje)
        const endDate = new Date()
        if (!includeToday) {
            endDate.setDate(today.getDate() - 1) // Meta Ads Default: Últimos X dias ENCERRA ontem
        }
        const endStr = endDate.getFullYear() + '-' +
            String(endDate.getMonth() + 1).padStart(2, '0') + '-' +
            String(endDate.getDate()).padStart(2, '0')

        return data.filter(m => m.data_referencia && m.data_referencia >= cutoffStr && m.data_referencia <= endStr)
    }, [metrics, selectedClient, dateRange])

    // Aggregate for Scorecards
    const totals = useMemo(() => {
        return filteredData.reduce((acc, curr) => {
            const val = Number(curr.resultado_valor) || 0
            const name = curr.resultado_nome

            const isComm = isCommercial(name)

            return {
                investimento: acc.investimento + (Number(curr.investimento) || 0),
                impressions: acc.impressions + (Number(curr.impressoes) || 0),
                clicks: acc.clicks + (Number(curr.cliques_link) || 0),
                reach: acc.reach + (Number(curr.alcance) || 0),
                leads: acc.leads + (isComm ? val : 0),
                engagement: acc.engagement + (!isComm ? val : 0)
            }
        }, { investimento: 0, impressions: 0, clicks: 0, reach: 0, leads: 0, engagement: 0 })
    }, [filteredData])

    // --- ACCURATE TOTALS OVERRIDE ---
    // Meta API returns deduplicated reach/impressions at the account level for last_7d and last_30d.
    // Summing per-campaign inflates these numbers (same user counted across multiple campaigns),
    // so prefer the official account totals when the date range matches.
    // For "+today" variants we still use the official N-day number (it omits today's reach but is
    // the deduplicated truth for the window; alternative is the inflated sum, which is worse).
    const baseRange = dateRange.replace('_today', '')
    const officialReach = baseRange === '7' ? clientDetails?.account_reach_7d : clientDetails?.account_reach_30d
    const officialImpressions = baseRange === '7' ? clientDetails?.account_impressions_7d : clientDetails?.account_impressions_30d

    const displayReach = officialReach > 0 ? officialReach : totals.reach
    const displayImpressions = officialImpressions > 0 ? officialImpressions : totals.impressions
    const reachIsOfficial = officialReach > 0
    const impressionsIsOfficial = officialImpressions > 0

    // Computed Metrics
    const cpl = totals.leads > 0 ? totals.investimento / totals.leads : 0
    // CPM/CTR should use the Display values to match the cards
    // Use totals.impressions if displayImpressions is 0 to avoid Infinity/NaN on empty states
    const impForCalc = displayImpressions > 0 ? displayImpressions : (totals.impressions > 0 ? totals.impressions : 0)

    const cpm = impForCalc > 0 ? (totals.investimento / impForCalc) * 1000 : 0
    const ctr = impForCalc > 0 ? (totals.clicks / impForCalc) * 100 : 0

    // Chart Data (Group by Date)
    const chartData = useMemo(() => {
        const grouped = filteredData.reduce((acc, curr) => {
            const date = curr.data_referencia
            if (!date) return acc // Skip invalid dates

            if (!acc[date]) {
                acc[date] = { date, investimento: 0, leads: 0, engagement: 0, clicks: 0, impressions: 0 }
            }

            const val = Number(curr.resultado_valor) || 0
            const name = curr.resultado_nome
            const isComm = isCommercial(name)

            acc[date].investimento += (Number(curr.investimento) || 0)
            acc[date].leads += (isComm ? val : 0)
            acc[date].engagement += (!isComm ? val : 0)
            acc[date].clicks += (Number(curr.cliques_link) || 0)
            acc[date].impressions += (Number(curr.impressoes) || 0)
            return acc
        }, {})

        // Sort by date
        return Object.values(grouped).sort((a, b) => (a.date || '').localeCompare(b.date || '')).map(item => ({
            ...item,
            dateFormatted: new Date(item.date + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
            ctr: item.impressions > 0 ? (item.clicks / item.impressions) * 100 : 0,
            cpm: item.impressions > 0 ? (item.investimento / item.impressions) * 1000 : 0,
            cpl: item.leads > 0 ? (item.investimento / item.leads) : 0
        }))
    }, [filteredData])

    // Campaign Breakdown Data
    const campaignData = useMemo(() => {
        const grouped = filteredData.reduce((acc, curr) => {
            const id = curr.campaign_id || curr.campaign_name
            const name = curr.campaign_name || 'Desconhecida'
            if (!acc[id]) {
                acc[id] = { id, name, status: curr.campaign_status || null, statusDate: curr.data_referencia, investimento: 0, leads: 0, engagement: 0, clicks: 0, impressions: 0 }
            } else if (curr.campaign_status && curr.data_referencia >= acc[id].statusDate) {
                // Pega o status do registro mais recente (status mais atual da campanha)
                acc[id].status = curr.campaign_status
                acc[id].statusDate = curr.data_referencia
            }

            const val = Number(curr.resultado_valor) || 0
            const resName = curr.resultado_nome
            const isComm = isCommercial(resName)

            acc[id].investimento += (Number(curr.investimento) || 0)
            acc[id].leads += (isComm ? val : 0)
            acc[id].engagement += (!isComm ? val : 0)
            acc[id].clicks += (Number(curr.cliques_link) || 0)
            acc[id].impressions += (Number(curr.impressoes) || 0)
            return acc
        }, {})

        return Object.values(grouped).sort((a, b) => b.investimento - a.investimento).map(c => ({
            ...c,
            ctr: c.impressions > 0 ? (c.clicks / c.impressions) * 100 : 0,
            cpl: c.leads > 0 ? (c.investimento / c.leads) : 0,
            cpm: c.impressions > 0 ? (c.investimento / c.impressions) * 1000 : 0,
            type: c.leads > 0 ? 'Lead' : 'Engajamento' // Helper for UI
        }))
    }, [filteredData])

    // Daily Detail Data (for table) - desc date
    const tableData = useMemo(() => {
        return [...chartData].reverse()
    }, [chartData])

    // Today's Data — reads raw metrics directly (not filtered chartData which may exclude today)
    const todayStats = useMemo(() => {
        const today = new Date()
        const todayStr = today.getFullYear() + '-' +
            String(today.getMonth() + 1).padStart(2, '0') + '-' +
            String(today.getDate()).padStart(2, '0')

        const todayMetrics = displayedMetrics.filter(m => m.data_referencia === todayStr)
        if (!todayMetrics.length) return { investimento: 0, leads: 0, cpl: 0 }

        const agg = todayMetrics.reduce((acc, m) => {
            const val = Number(m.resultado_valor) || 0
            const isComm = isCommercial(m.resultado_nome)
            return {
                investimento: acc.investimento + (Number(m.investimento) || 0),
                leads: acc.leads + (isComm ? val : 0)
            }
        }, { investimento: 0, leads: 0 })

        return { ...agg, cpl: agg.leads > 0 ? agg.investimento / agg.leads : 0 }
    }, [displayedMetrics])

    // Utils
    const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
    const formatNumber = (val) => new Intl.NumberFormat('pt-BR').format(val)
    const formatPercent = (val) => new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2 }).format(val / 100)


    // Header Component
    const Header = () => (
        <header className="header glass-panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <img src="/tc-logo.png" alt="Time Controll" style={{ height: '48px', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }} />
                <div>
                    <h1 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>
                        Dashboard de Resultados
                    </h1>
                    <span className="text-gradient" style={{ fontSize: '14px', fontWeight: '600' }}>Time Controll Agency</span>
                </div>
            </div>

            {/* Client Name Display */}
            {selectedClient && (
                <div style={{ textAlign: 'right' }}>
                    <span style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '2px' }}>Cliente Select</span>
                    <span style={{ fontSize: '18px', fontWeight: '700', letterSpacing: '-0.02em' }}>
                        {clientName || 'Carregando...'}
                    </span>
                </div>
            )}

            {isAdmin && selectedClient && (
                <button
                    onClick={() => { setSelectedClient(null); setMetrics([]); setClientName('') }}
                    className="btn-ghost"
                    style={{ marginLeft: '20px' }}
                >
                    &larr; Voltar para Clientes
                </button>
            )}
        </header>
    )

    if (loading) return (
        <div style={{ background: '#0a0a0a', minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#888' }}>Carregando...</span>
        </div>
    )

    if (!accessGranted) {
        return (
            <div style={{ background: '#0a0a0a', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
                <img src="/tc-logo.png" alt="TC" style={{ height: '80px', marginBottom: '24px', opacity: 0.8 }} />
                <h1 style={{ fontSize: '24px', fontWeight: '600' }}>Acesso Restrito</h1>
                <p style={{ color: '#666', marginTop: '8px' }}>Utilize um link exclusivo para acessar o relatório.</p>
                <div style={{ marginTop: '20px', padding: '15px', background: '#1a1a1a', borderRadius: '8px', border: '1px solid #333', maxWidth: '400px', width: '100%', wordBreak: 'break-all' }}>
                    <p style={{ color: '#888', fontSize: '12px', margin: '0 0 5px 0' }}>URL Hash detectado:</p>
                    <code style={{ color: '#FFA500', fontSize: '14px' }}>{window.location.hash || '<Vazio>'}</code>

                    {errorObj && (
                        <div style={{ marginTop: '15px', borderTop: '1px solid #333', paddingTop: '10px' }}>
                            <p style={{ color: '#ff4444', fontSize: '13px', margin: 0 }}>Erro: {errorObj?.message || 'Desconhecido'}</p>
                        </div>
                    )}
                </div>
            </div>
        )
    }

    if (errorObj) return (
        <div style={{ padding: 40, background: '#0a0a0a', minHeight: '100vh', color: '#fff' }}>
            <h2 style={{ color: '#ff4444' }}>Erro ao carregar dados</h2>
            <pre style={{ background: '#1a1a1a', padding: 20, borderRadius: 8, overflow: 'auto' }}>
                {errorObj.message}
            </pre>
        </div>
    )

    // --- ADMIN: CLIENT SELECTION GRID ---
    if (isAdmin && !selectedClient) {
        return (
            <div className="dashboard-container animate-fade-in">
                <Header />
                <div style={{ maxWidth: '1200px', margin: '0 auto', paddingTop: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '12px' }}>
                        <h2 style={{ color: 'var(--text-primary)', margin: 0, fontSize: '1.5rem', fontWeight: '600' }}>
                            Clientes ({clients.length})
                        </h2>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            {(() => {
                                const withGroup = clients.filter(c => c.whatsapp_group_jid).length
                                return (
                                    <button
                                        onClick={() => triggerFeedback({ all: true }, `para TODOS os ${withGroup} clientes com grupo cadastrado`)}
                                        disabled={sendingFeedback === 'all' || withGroup === 0}
                                        title={withGroup === 0 ? 'Nenhum cliente tem grupo cadastrado ainda' : `Enviar feedback para ${withGroup} grupos`}
                                        style={{
                                            background: '#25D366', color: '#fff', border: 'none',
                                            padding: '10px 18px', borderRadius: '8px', fontWeight: '600',
                                            cursor: (sendingFeedback === 'all' || withGroup === 0) ? 'not-allowed' : 'pointer',
                                            opacity: (sendingFeedback === 'all' || withGroup === 0) ? 0.5 : 1,
                                            fontSize: '0.9rem'
                                        }}
                                    >
                                        {sendingFeedback === 'all' ? 'Enviando…' : `Enviar feedback p/ todos (${withGroup})`}
                                    </button>
                                )
                            })()}
                            <button
                                onClick={() => { setShowCreateForm(true); setCreatedLink(null); }}
                                style={{
                                    background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                                    color: '#fff', border: 'none', padding: '10px 20px',
                                    borderRadius: '8px', fontWeight: '600', cursor: 'pointer',
                                    fontSize: '0.9rem', boxShadow: '0 4px 12px rgba(59,130,246,0.3)'
                                }}
                            >
                                + Novo cliente
                            </button>
                        </div>
                    </div>

                    {feedbackResult && (
                        <div style={{ padding: '12px 16px', marginBottom: '20px', borderRadius: '6px',
                            background: feedbackResult.ok ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                            border: `1px solid ${feedbackResult.ok ? '#10b981' : '#ef4444'}`,
                            color: feedbackResult.ok ? '#10b981' : '#ef4444', fontSize: '0.85rem' }}>
                            {feedbackResult.ok ? '✓ Disparado. Webhook recebeu o trigger; envios estão acontecendo no n8n com intervalo entre cada um.' : `✗ Erro ${feedbackResult.status}: ${feedbackResult.body}`}
                        </div>
                    )}

                    {showCreateForm && (
                        <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
                            <h3 style={{ marginTop: 0, color: 'var(--text-primary)' }}>Adicionar cliente</h3>
                            {createdLink ? (
                                <div>
                                    <p style={{ color: '#10b981', marginTop: 0 }}>✓ Cliente criado. Link de acesso:</p>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', background: '#0f0f12', padding: '12px', borderRadius: '6px', border: '1px solid #2a2a30' }}>
                                        <code style={{ color: '#f97316', fontSize: '0.85rem', flex: 1, wordBreak: 'break-all' }}>{createdLink}</code>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(createdLink)}
                                            style={{ background: '#1f1f25', color: '#fff', border: '1px solid #2a2a30', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' }}
                                        >Copiar</button>
                                    </div>
                                    <button
                                        onClick={() => { setShowCreateForm(false); setCreatedLink(null); }}
                                        style={{ marginTop: '16px', background: 'transparent', color: 'var(--text-secondary)', border: '1px solid #2a2a30', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
                                    >Fechar</button>
                                </div>
                            ) : (
                                <>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                                        <div>
                                            <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '1px' }}>Nome do cliente</label>
                                            <input
                                                type="text" value={newClientName}
                                                onChange={(e) => setNewClientName(e.target.value)}
                                                placeholder="Ex: João Silva Imóveis"
                                                style={{ width: '100%', background: '#0f0f12', color: '#fff', border: '1px solid #2a2a30', padding: '10px 12px', borderRadius: '6px', fontSize: '0.95rem' }}
                                            />
                                        </div>
                                        <div>
                                            <label style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '1px' }}>ID conta Meta (sem act_)</label>
                                            <input
                                                type="text" value={newClientAccount}
                                                onChange={(e) => setNewClientAccount(e.target.value)}
                                                placeholder="Ex: 199691101179385"
                                                style={{ width: '100%', background: '#0f0f12', color: '#fff', border: '1px solid #2a2a30', padding: '10px 12px', borderRadius: '6px', fontSize: '0.95rem' }}
                                            />
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button
                                            onClick={handleCreateClient}
                                            disabled={creating}
                                            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '6px', fontWeight: '600', cursor: creating ? 'wait' : 'pointer', opacity: creating ? 0.7 : 1 }}
                                        >{creating ? 'Criando...' : 'Criar e gerar link'}</button>
                                        <button
                                            onClick={() => { setShowCreateForm(false); setNewClientName(''); setNewClientAccount(''); }}
                                            style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid #2a2a30', padding: '10px 16px', borderRadius: '6px', cursor: 'pointer' }}
                                        >Cancelar</button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '20px'
                    }}>
                        {clients.map(client => {
                            const clientLink = `${window.location.origin}/#/c/${client.observacoes}`
                            const justCopied = copiedId === client.id
                            return (
                                <div
                                    key={client.id}
                                    onClick={() => handleAdminSelectClient(client.id)}
                                    className="admin-client-card"
                                    style={{ position: 'relative' }}
                                >
                                    <div className="admin-client-avatar">
                                        {client.cliente.substr(0, 2).toUpperCase()}
                                    </div>
                                    <span style={{ color: 'var(--text-primary)', fontWeight: '500', fontSize: '1.05rem', flex: 1 }}>{client.cliente}</span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            navigator.clipboard.writeText(clientLink)
                                            setCopiedId(client.id)
                                            setTimeout(() => setCopiedId(prev => prev === client.id ? null : prev), 1500)
                                        }}
                                        title={justCopied ? 'Link copiado' : 'Copiar link do cliente'}
                                        aria-label="Copiar link"
                                        style={{
                                            background: 'transparent',
                                            border: 'none',
                                            cursor: 'pointer',
                                            padding: '6px',
                                            borderRadius: '6px',
                                            color: justCopied ? '#10b981' : 'var(--text-secondary)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            transition: 'background 0.15s, color 0.15s'
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; if (!justCopied) e.currentTarget.style.color = 'var(--text-primary)' }}
                                        onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; if (!justCopied) e.currentTarget.style.color = 'var(--text-secondary)' }}
                                    >
                                        {justCopied ? (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                                        ) : (
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                                        )}
                                    </button>
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>
        )
    }

    // --- MAIN DASHBOARD (For Single Client or Admin viewing Single Client) ---

    return (
        <div className="dashboard-container animate-fade-in">
            <Header />

            {isAdmin && clientDetails && (
                <div className="glass-panel" style={{ padding: '14px 18px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', borderLeft: '3px solid #25D366' }}>
                    <div style={{ flex: '1 1 220px' }}>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '6px' }}>Grupo WhatsApp</div>
                        {editingGroup ? (
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <select
                                    autoFocus
                                    value={clientDetails.whatsapp_group_jid || ''}
                                    onFocus={loadWhatsAppGroups}
                                    onChange={(e) => {
                                        const jid = e.target.value
                                        const g = (waGroups || []).find(x => x.jid === jid)
                                        saveClientGroup(clientDetails.id, jid || null, g?.name || (jid ? clientDetails.whatsapp_group_name : null))
                                        setEditingGroup(false)
                                    }}
                                    onBlur={() => setEditingGroup(false)}
                                    disabled={loadingGroups}
                                    style={{ flex: 1, minWidth: 0, background: '#0f0f12', color: '#fff', border: '1px solid #2a2a30', padding: '8px 10px', borderRadius: '6px', fontSize: '0.9rem' }}
                                >
                                    <option value="">Sem grupo vinculado</option>
                                    {clientDetails.whatsapp_group_jid && !(waGroups || []).some(g => g.jid === clientDetails.whatsapp_group_jid) && (
                                        <option value={clientDetails.whatsapp_group_jid}>
                                            {clientDetails.whatsapp_group_name || clientDetails.whatsapp_group_jid}
                                            {loadingGroups ? ' (carregando lista…)' : ''}
                                        </option>
                                    )}
                                    {(waGroups || []).map(g => (
                                        <option key={g.jid} value={g.jid}>{g.name}</option>
                                    ))}
                                </select>
                                <button
                                    onClick={() => setEditingGroup(false)}
                                    title="Cancelar"
                                    style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid #2a2a30', padding: '8px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}
                                >✕</button>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <div style={{
                                    flex: 1, minWidth: 0, padding: '8px 12px',
                                    background: '#0f0f12', border: '1px solid #2a2a30',
                                    borderRadius: '6px', color: clientDetails.whatsapp_group_name ? '#fff' : 'var(--text-secondary)',
                                    fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                                }} title={clientDetails.whatsapp_group_name || ''}>
                                    {clientDetails.whatsapp_group_name || '— Sem grupo vinculado —'}
                                </div>
                                <button
                                    onClick={() => { loadWhatsAppGroups(); setEditingGroup(true) }}
                                    title="Trocar grupo"
                                    style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid #2a2a30', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}
                                >
                                    Trocar
                                </button>
                            </div>
                        )}
                    </div>
                    <button
                        onClick={() => triggerFeedback({ client_id: clientDetails.id }, `apenas para ${clientDetails.cliente}`)}
                        disabled={!clientDetails.whatsapp_group_jid || sendingFeedback === clientDetails.id}
                        title={!clientDetails.whatsapp_group_jid ? 'Selecione um grupo antes' : 'Disparar mensagem de feedback'}
                        style={{
                            background: '#25D366', color: '#fff', border: 'none',
                            padding: '10px 18px', borderRadius: '6px', fontWeight: '600',
                            cursor: (!clientDetails.whatsapp_group_jid || sendingFeedback === clientDetails.id) ? 'not-allowed' : 'pointer',
                            opacity: (!clientDetails.whatsapp_group_jid || sendingFeedback === clientDetails.id) ? 0.5 : 1,
                            fontSize: '0.9rem', alignSelf: 'flex-end'
                        }}
                    >
                        {sendingFeedback === clientDetails.id ? 'Enviando…' : 'Enviar feedback'}
                    </button>
                </div>
            )}

            {clientDetails && (clientDetails.account_balance > 0 || clientDetails.account_funding_display) && (() => {
                const balance = Number(clientDetails.account_balance) || 0
                const dailyAvg = (Number(clientDetails.account_spend_30d) || 0) / 30
                const daysLeft = dailyAvg > 0 && balance > 0 ? Math.floor(balance / dailyAvg) : null
                const color = balance <= 0 ? '#ef4444' : (daysLeft !== null && daysLeft <= 3 ? '#ef4444' : (daysLeft !== null && daysLeft <= 7 ? '#f59e0b' : '#10b981'))
                const isPrepaid = clientDetails.account_funding_type === 'prepaid' || balance > 0
                return (
                    <div className="glass-panel" style={{ padding: '16px 20px', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '20px', flexWrap: 'wrap', borderLeft: `3px solid ${color}` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
                            <div>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '4px' }}>
                                    {isPrepaid ? 'Saldo da conta (pré-pago)' : 'Conta'}
                                </div>
                                <div style={{ color, fontSize: '1.5rem', fontWeight: '700' }}>
                                    {clientDetails.account_funding_display || formatCurrency(balance)}
                                </div>
                            </div>
                            {daysLeft !== null && (
                                <div>
                                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: '4px' }}>Dura aprox.</div>
                                    <div style={{ color: 'var(--text-primary)', fontSize: '1.1rem', fontWeight: '600' }}>
                                        {daysLeft === 0 ? 'Acaba hoje' : `${daysLeft} dia${daysLeft === 1 ? '' : 's'}`}
                                    </div>
                                </div>
                            )}
                        </div>
                        {balance <= 0 && isPrepaid && (
                            <div style={{ color: '#ef4444', fontWeight: '600', fontSize: '0.9rem' }}>⚠ Recarregue para reativar campanhas</div>
                        )}
                    </div>
                )
            })()}

            <div className="filters-bar" style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
                <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="date-select"
                >
                    <option value="7">Últimos 7 dias (Padrão Meta)</option>
                    <option value="30">Últimos 30 dias (Padrão Meta)</option>
                    <option value="7_today">Últimos 7 dias (+Hoje)</option>
                    <option value="30_today">Últimos 30 dias (+Hoje)</option>
                </select>
            </div>
            {/* Metrics Grid */}
            <div className="metrics-grid">
                <MetricCard title="Investimento" value={formatCurrency(totals.investimento)} sub="Valor Gasto" icon={<DollarSign size={16} />} />
                <MetricCard title="Leads" value={formatNumber(totals.leads)} sub="Contatos gerados" icon={<Users size={16} />} highlight />
                <MetricCard title="CPL" value={formatCurrency(cpl)} sub="Custo/Lead" icon={<DollarSign size={16} />} />
                <MetricCard title="Alcance"
                    value={formatNumber(displayReach)}
                    sub={reachIsOfficial ? `Contas (Oficial ${baseRange}d)` : "Contas Alcançadas"}
                    icon={<Eye size={16} />} />
                <MetricCard title="Impressões"
                    value={formatNumber(displayImpressions)}
                    sub={impressionsIsOfficial ? `Exibições (Oficial ${baseRange}d)` : "Exibições num total"}
                    icon={<Eye size={16} />} />
                <MetricCard title="CPM" value={formatCurrency(cpm)} sub="Custo/1.000 Imp" icon={<TrendingUp size={16} />} />
                <MetricCard title="Cliques Link" value={formatNumber(totals.clicks)} sub="Total de cliques" icon={<MousePointer2 size={16} />} />
                <MetricCard title="CTR" value={formatPercent(ctr)} sub="Taxa Clique/Visita" icon={<Activity size={16} />} />
            </div>

            {/* Main Chart */}
            <div className="chart-section glass-panel">
                <div className="section-title">
                    Tendência de Performance
                    <span className="indicator">
                        <span className="investimento" style={{ color: '#3b82f6' }}>Investimento</span>
                        <span className="leads" style={{ color: '#f97316' }}>Leads</span>
                    </span>
                </div>
                <div style={{ width: '100%', height: 350 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis
                                dataKey="dateFormatted"
                                stroke="#71717a"
                                tick={{ fontSize: isMobile ? 10 : 12, fill: '#71717a' }}
                                tickLine={false}
                                axisLine={false}
                                interval={isMobile ? (dateRange === '30' ? 4 : 1) : 0}
                                dy={10}
                            />
                            <YAxis yAxisId="left" stroke="#71717a" tick={{ fontSize: 10, fill: '#71717a' }} tickFormatter={(val) => `R$${val}`} tickLine={false} axisLine={false} />
                            <YAxis yAxisId="right" orientation="right" stroke="#71717a" tick={{ fontSize: 10, fill: '#71717a' }} tickLine={false} axisLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'rgba(20,20,25,0.9)', backdropFilter: 'blur(10px)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }}
                                itemStyle={{ color: '#fff' }}
                                cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                            />
                            <Bar
                                yAxisId="left"
                                dataKey="investimento"
                                fill="url(#colorInvestimento)"
                                name="Investimento"
                                barSize={isMobile ? (dateRange === '30' ? 8 : 15) : 20}
                                radius={[4, 4, 0, 0]}
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="leads"
                                stroke="#f97316"
                                strokeWidth={isMobile ? 2 : 3}
                                dot={isMobile ? { r: 1, fill: '#f97316', strokeWidth: 0 } : { r: 4, fill: '#f97316', strokeWidth: 0 }}
                                activeDot={{ r: 6, fill: '#f97316', strokeWidth: 0 }}
                                name="Leads"
                            />
                            <defs>
                                <linearGradient id="colorInvestimento" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8} />
                                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.2} />
                                </linearGradient>
                            </defs>
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Campaign Breakdown */}
            {campaignData && campaignData.length > 0 && (() => {
                const displayedCampaigns = showOnlyActive ? campaignData.filter(c => c.status === 'ACTIVE') : campaignData
                const activeCount = campaignData.filter(c => c.status === 'ACTIVE').length
                const statusStyle = (status) => {
                    if (status === 'ACTIVE') return { bg: 'rgba(16, 185, 129, 0.15)', color: '#10b981', label: 'Ativa' }
                    if (status === 'PAUSED') return { bg: 'rgba(245, 158, 11, 0.12)', color: '#f59e0b', label: 'Pausada' }
                    if (status === 'ARCHIVED' || status === 'DELETED') return { bg: 'rgba(113, 113, 122, 0.15)', color: '#71717a', label: status === 'DELETED' ? 'Excluída' : 'Arquivada' }
                    return { bg: 'transparent', color: 'var(--text-secondary)', label: '—' }
                }
                return (
                    <div className="glass-panel" style={{ marginBottom: 32, padding: 28 }}>
                        <div className="section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                Resultados por Campanha <Activity size={18} color="var(--text-secondary)" />
                            </span>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: '400', textTransform: 'none', letterSpacing: 0 }}>
                                <input
                                    type="checkbox"
                                    checked={showOnlyActive}
                                    onChange={(e) => setShowOnlyActive(e.target.checked)}
                                    style={{ accentColor: '#10b981', cursor: 'pointer' }}
                                />
                                Só ativas ({activeCount}/{campaignData.length})
                            </label>
                        </div>
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Campanha</th>
                                        <th>Status</th>
                                        <th>Investimento</th>
                                        <th>Resultados</th>
                                        <th>Custo por Result.</th>
                                        <th>CTR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {displayedCampaigns.map((c, i) => {
                                        const s = statusStyle(c.status)
                                        return (
                                            <tr key={i} style={{ opacity: c.status && c.status !== 'ACTIVE' ? 0.7 : 1 }}>
                                                <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={c.name}>{c.name}</td>
                                                <td>
                                                    <span style={{
                                                        background: s.bg, color: s.color,
                                                        padding: '3px 10px', borderRadius: '12px',
                                                        fontSize: '0.75rem', fontWeight: '600',
                                                        display: 'inline-block', whiteSpace: 'nowrap'
                                                    }}>{s.label}</span>
                                                </td>
                                                <td>{formatCurrency(c.investimento)}</td>
                                                <td>
                                                    <span style={{
                                                        background: c.leads > 0 ? 'rgba(249, 115, 22, 0.1)' : 'transparent',
                                                        color: c.leads > 0 ? '#f97316' : 'var(--text-primary)',
                                                        padding: '4px 8px',
                                                        borderRadius: '4px',
                                                        fontWeight: c.leads > 0 ? '600' : '500'
                                                    }}>{c.leads}</span>
                                                </td>
                                                <td>{formatCurrency(c.cpl)}</td>
                                                <td>{formatPercent(c.ctr)}</td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )
            })()}

            {/* Bottom Section */}
            <div className="bottom-grid">
                <div className="bottom-card glass-panel">
                    <div className="section-title">Performance Hoje</div>
                    <div>
                        <div className="today-stat-box text-center" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h3 style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>DATA REFERÊNCIA</h3>
                                <p style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontWeight: '600', margin: 0 }}>Hoje</p>
                            </div>
                            <Activity size={24} color="var(--accent-color)" opacity={0.8} />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                            <div className="today-stat-box" style={{ margin: 0 }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Investido</div>
                                <div style={{ fontSize: '1.4rem', color: '#3b82f6', fontWeight: '700' }}>
                                    {formatCurrency(todayStats.investimento)}
                                </div>
                            </div>
                            <div className="today-stat-box" style={{ margin: 0 }}>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>Leads</div>
                                <div style={{ fontSize: '1.4rem', color: '#f97316', fontWeight: '700' }}>
                                    {todayStats.leads}
                                </div>
                            </div>
                        </div>

                        <div className="today-stat-box">
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                                <span>CPL Hoje</span>
                                <TrendingUp size={14} color="var(--text-secondary)" />
                            </div>
                            <div style={{ fontSize: '1.25rem', color: 'var(--text-primary)', fontWeight: '700' }}>
                                {formatCurrency(todayStats.cpl)}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bottom-card glass-panel">
                    <div className="section-title">Detalhamento Diário <Filter size={18} color="var(--text-secondary)" /></div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Data</th>
                                    <th>Investimento</th>
                                    <th>Leads</th>
                                    <th>CPL</th>
                                    <th>Cliques</th>
                                    <th>CTR</th>
                                    <th>CPM</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tableData.map((row, i) => (
                                    <tr key={i}>
                                        <td style={{ color: 'var(--text-secondary)' }}>{row.dateFormatted}</td>
                                        <td>{formatCurrency(row.investimento)}</td>
                                        <td style={{ color: row.leads > 0 ? '#f97316' : 'inherit', fontWeight: row.leads > 0 ? '600' : '500' }}>{row.leads}</td>
                                        <td>{formatCurrency(row.cpl)}</td>
                                        <td>{row.clicks}</td>
                                        <td>{formatPercent(row.ctr)}</td>
                                        <td>{formatCurrency(row.cpm)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div style={{
                marginTop: '40px',
                textAlign: 'center',
                color: 'var(--text-secondary)',
                fontSize: '0.75rem',
                padding: '24px',
                letterSpacing: '0.5px'
            }}>
                ÚLTIMA SINCRONIZAÇÃO: {clientDetails?.last_sync_at ? new Date(clientDetails.last_sync_at).toLocaleString('pt-BR') : 'Aguardando sincronização...'}
            </div>
        </div>
    )
}

const MetricCard = ({ title, value, sub, icon, highlight }) => (
    <div className={`metric-card glass-panel ${highlight ? 'highlight' : ''}`}>
        <div className="metric-header">
            {title}
            {icon}
        </div>
        <div className="metric-value">{value}</div>
        <div className="metric-sub">{sub}</div>
    </div>
)

export default Dashboard

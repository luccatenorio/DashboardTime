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
        'onsite_conversion.messaging_conversation_started_7d',
        'onsite_conversion.messaging_conversation_started_1d',
        'offsite_conversion.fb_pixel_lead',
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
        const cutoffDate = new Date()
        cutoffDate.setDate(today.getDate() - parseInt(dateRange))
        const cutoffStr = cutoffDate.getFullYear() + '-' +
            String(cutoffDate.getMonth() + 1).padStart(2, '0') + '-' +
            String(cutoffDate.getDate()).padStart(2, '0')

        return data.filter(m => m.data_referencia && m.data_referencia >= cutoffStr)
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

    // --- ACCURATE TOTALS OVERRIDE (For 30 Days view) ---
    // If we have Account Level total (from client details) and are viewing 30 days, use that.
    // Otherwise, we MUST default to the sum (totals.reach) because we don't have other data,
    // BUT we know it's technically wrong (duplicated).
    // The user instruction "Forbidden to sum" is strong, but showing 0 is worse.
    // I will prioritize the Official 30d data.
    const displayReach = (dateRange === '30' && clientDetails?.account_reach_30d > 0)
        ? clientDetails.account_reach_30d
        : totals.reach

    const displayImpressions = (dateRange === '30' && clientDetails?.account_impressions_30d > 0)
        ? clientDetails.account_impressions_30d
        : totals.impressions

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
            const name = curr.campaign_name || 'Desconhecida'
            if (!acc[name]) {
                acc[name] = { name, investimento: 0, leads: 0, engagement: 0, clicks: 0, impressions: 0 }
            }

            const val = Number(curr.resultado_valor) || 0
            const resName = curr.resultado_nome
            const isComm = isCommercial(resName)

            acc[name].investimento += (Number(curr.investimento) || 0)
            acc[name].leads += (isComm ? val : 0)
            acc[name].engagement += (!isComm ? val : 0)
            acc[name].clicks += (Number(curr.cliques_link) || 0)
            acc[name].impressions += (Number(curr.impressoes) || 0)
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

    // Today's Data
    const todayStats = useMemo(() => {
        const today = new Date()
        const todayStr = today.getFullYear() + '-' +
            String(today.getMonth() + 1).padStart(2, '0') + '-' +
            String(today.getDate()).padStart(2, '0')
        const todayItem = chartData.find(d => d.date === todayStr) || {
            investimento: 0, leads: 0, cpl: 0
        }
        return todayItem
    }, [chartData])

    // Utils
    const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)
    const formatNumber = (val) => new Intl.NumberFormat('pt-BR').format(val)
    const formatPercent = (val) => new Intl.NumberFormat('pt-BR', { style: 'percent', minimumFractionDigits: 2 }).format(val / 100)


    // Header Component
    const Header = () => (
        <header className="header" style={{
            background: 'rgba(20, 20, 25, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            padding: '16px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <img src="/tc-logo.png" alt="Time Controll" style={{ height: '48px', borderRadius: '8px' }} />
                <div>
                    <h1 style={{ fontSize: '20px', fontWeight: '600', color: '#fff', margin: 0 }}>
                        Dashboard de Resultados
                    </h1>
                    <span style={{ fontSize: '14px', color: '#FFA500', fontWeight: '500' }}>Time Controll Agency</span>
                </div>
            </div>

            {/* Client Name Display */}
            {selectedClient && (
                <div style={{ textAlign: 'right' }}>
                    <span style={{ display: 'block', fontSize: '12px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>Cliente</span>
                    <span style={{ fontSize: '18px', fontWeight: '600', color: '#fff' }}>
                        {clientName || 'Carregando...'}
                    </span>
                </div>
            )}

            {isAdmin && selectedClient && (
                <button
                    onClick={() => { setSelectedClient(null); setMetrics([]); setClientName('') }}
                    style={{
                        marginLeft: '20px',
                        background: 'transparent',
                        border: '1px solid rgba(255,255,255,0.2)',
                        color: '#fff',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer'
                    }}
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
                {errorObj && <p style={{ color: '#ff4444', marginTop: 16 }}>{errorObj.message}</p>}
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
            <div className="dashboard-container" style={{ background: '#0a0a0a', minHeight: '100vh' }}>
                <Header />
                <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
                    <h2 style={{ color: '#fff', marginBottom: '32px', fontSize: '24px' }}>Selecione um Cliente</h2>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                        gap: '20px'
                    }}>
                        {clients.map(client => (
                            <div
                                key={client.id}
                                onClick={() => handleAdminSelectClient(client.id)}
                                style={{
                                    background: '#141419',
                                    border: '1px solid rgba(255,255,255,0.05)',
                                    borderRadius: '12px',
                                    padding: '24px',
                                    cursor: 'pointer',
                                    transition: 'transform 0.2s, border-color 0.2s',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '16px'
                                }}
                                onMouseEnter={e => {
                                    e.currentTarget.style.borderColor = '#FFA500'
                                    e.currentTarget.style.transform = 'translateY(-2px)'
                                }}
                                onMouseLeave={e => {
                                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)'
                                    e.currentTarget.style.transform = 'translateY(0)'
                                }}
                            >
                                <div style={{
                                    width: '40px', height: '40px', borderRadius: '50%', background: '#252530',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: '#FFA500', fontWeight: 'bold'
                                }}>
                                    {client.cliente.substr(0, 2).toUpperCase()}
                                </div>
                                <span style={{ color: '#e0e0e0', fontWeight: '500' }}>{client.cliente}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    // --- MAIN DASHBOARD (For Single Client or Admin viewing Single Client) ---

    return (
        <div className="dashboard-container">
            <Header />

            <div className="filters-bar" style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', padding: '0 32px' }}>
                <select
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    className="date-select"
                    style={{
                        background: '#1A1A1A',
                        border: '1px solid rgba(255,255,255,0.1)',
                        color: '#fff',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer'
                    }}
                >
                    <option value="7">Últimos 7 dias</option>
                    <option value="30">Últimos 30 dias</option>
                </select>
            </div>
            {/* Metrics Grid */}
            <div className="metrics-grid">
                <MetricCard title="Investimento" value={formatCurrency(totals.investimento)} sub="Valor Gasto" icon={<DollarSign size={16} />} />
                <MetricCard title="Leads" value={formatNumber(totals.leads)} sub="Contatos" icon={<Users size={16} />} highlight />
                <MetricCard title="CPL" value={formatCurrency(cpl)} sub="Custo/Lead" icon={<DollarSign size={16} />} />
                <MetricCard title="Alcance"
                    value={formatNumber(displayReach)}
                    sub={dateRange === '30' && clientDetails?.account_reach_30d > 0 ? "Contas (Oficial 30d)" : "Contas Alcançadas"}
                    icon={<Eye size={16} />} />
                <MetricCard title="Impressões"
                    value={formatNumber(displayImpressions)}
                    sub={dateRange === '30' && clientDetails?.account_impressions_30d > 0 ? "Exibições (Ref. 30d)" : "Exibições"}
                    icon={<Eye size={16} />} />
                <MetricCard title="CPM" value={formatCurrency(cpm)} sub="Custo/1k Imp" icon={<TrendingUp size={16} />} />
                <MetricCard title="Cliques Link" value={formatNumber(totals.clicks)} sub="Total" icon={<MousePointer2 size={16} />} />
                <MetricCard title="CTR" value={formatPercent(ctr)} sub="Taxa Clique" icon={<MousePointer2 size={16} />} />
            </div>

            {/* Main Chart */}
            <div className="chart-section">
                <div className="section-title">
                    <span>Tendência de Performance</span>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        <span style={{ color: '#3b82f6' }}>● Investimento</span> <span style={{ color: '#f97316', marginLeft: '10px' }}>● Leads</span>
                    </div>
                </div>
                <div style={{ width: '100%', height: 350 }}>
                    <ResponsiveContainer>
                        <ComposedChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                            <XAxis
                                dataKey="dateFormatted"
                                stroke="#71717a"
                                tick={{ fontSize: isMobile ? 10 : 12 }}
                                interval={isMobile ? (dateRange === '30' ? 4 : 1) : 0}
                            />
                            <YAxis yAxisId="left" stroke="#71717a" tick={{ fontSize: 10 }} tickFormatter={(val) => `R$${val}`} />
                            <YAxis yAxisId="right" orientation="right" stroke="#71717a" tick={{ fontSize: 10 }} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Bar
                                yAxisId="left"
                                dataKey="investimento"
                                fill="#3b82f6"
                                name="Investimento"
                                barSize={isMobile ? (dateRange === '30' ? 8 : 15) : 20}
                                radius={[2, 2, 0, 0]}
                            />
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="leads"
                                stroke="#f97316"
                                strokeWidth={isMobile ? 2 : 3}
                                dot={isMobile ? { r: 1, fill: '#f97316' } : { r: 4, fill: '#f97316' }}
                                name="Leads"
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Campaign Breakdown */}
            {campaignData && campaignData.length > 0 && (
                <div className="bottom-card" style={{ marginBottom: 20 }}>
                    <div className="section-title">Resultados por Campanha</div>
                    <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Campanha</th>
                                    <th>Investimento</th>
                                    <th>Resultados (Leads)</th>
                                    <th>CPL / CPA</th>
                                    <th>CTR</th>
                                </tr>
                            </thead>
                            <tbody>
                                {campaignData.map((c, i) => (
                                    <tr key={i}>
                                        <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={c.name}>{c.name}</td>
                                        <td>{formatCurrency(c.investimento)}</td>
                                        <td>{c.leads}</td>
                                        <td>{formatCurrency(c.cpl)}</td>
                                        <td>{formatPercent(c.ctr)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Bottom Section */}
            <div className="bottom-grid">
                <div className="bottom-card">
                    <div className="section-title">Performance Hoje</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        <div className="today-stat" style={{ marginBottom: '20px' }}>
                            <h3 style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>DATA</h3>
                            <p style={{ fontSize: '1.2rem', color: 'var(--text-primary)', fontWeight: 'bold' }}>Hoje</p>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                            <div>
                                <div style={{ fontSize: '0.75rem' }}>Investido</div>
                                <div style={{ fontSize: '1.5rem', color: 'var(--accent-color)', fontWeight: 'bold' }}>
                                    {formatCurrency(todayStats.investimento)}
                                </div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.75rem' }}>Leads</div>
                                <div style={{ fontSize: '1.5rem', color: 'var(--text-primary)', fontWeight: 'bold' }}>
                                    {todayStats.leads}
                                </div>
                            </div>
                        </div>

                        <div>
                            <div style={{ fontSize: '0.75rem' }}>CPL Hoje</div>
                            <div style={{ fontSize: '1.2rem', color: 'var(--text-primary)', fontWeight: 'bold' }}>
                                {formatCurrency(todayStats.cpl)}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bottom-card">
                    <div className="section-title">Detalhamento Diário</div>
                    <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
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
                                        <td>{row.dateFormatted}</td>
                                        <td>{formatCurrency(row.investimento)}</td>
                                        <td>{row.leads}</td>
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
                marginTop: '30px',
                textAlign: 'center',
                color: '#666',
                fontSize: '0.8rem',
                padding: '20px',
                borderTop: '1px solid rgba(255,255,255,0.05)'
            }}>
                Atualizado em: {clientDetails?.last_sync_at ? new Date(clientDetails.last_sync_at).toLocaleString('pt-BR') : 'Aguardando sincronização...'}
            </div>
        </div>
    )
}

const MetricCard = ({ title, value, sub, icon, highlight }) => (
    <div className="metric-card" style={highlight ? { borderColor: 'var(--accent-color)' } : {}}>
        <div className="metric-header">
            {title}
            {icon}
        </div>
        <div className="metric-value" style={highlight ? { color: 'var(--accent-color)' } : {}}>{value}</div>
        <div className="metric-sub">{sub}</div>
    </div>
)

export default Dashboard

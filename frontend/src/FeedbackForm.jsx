import React, { useState, useEffect } from 'react'
import { supabase } from './lib/supabase'

const PERFIL_OPTIONS = ['Todos', 'Maioria', 'Metade', 'Poucos', 'Nenhum']
const FAIXA_RENDA_OPTIONS = ['Abaixo do esperado', 'Dentro do esperado', 'Acima do esperado']
const OBJECAO_OPTIONS = ['Entrada alta', 'Parcela', 'Localização', 'Documentação', 'Só pesquisando', 'Outro']

// Segunda da semana atual (segunda 00:00 BRT)
function getCurrentWeekStart() {
    const d = new Date()
    const day = d.getDay() // 0=domingo, 1=segunda
    const diff = (day === 0 ? -6 : 1 - day) // se domingo, volta 6 dias; senão, volta até segunda
    const monday = new Date(d)
    monday.setDate(d.getDate() + diff)
    monday.setHours(0, 0, 0, 0)
    return monday
}

function fmtDate(d) {
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' })
}

function isoDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}

const FeedbackForm = ({ hash }) => {
    const [client, setClient] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [submitted, setSubmitted] = useState(false)
    const [saving, setSaving] = useState(false)
    const [existingId, setExistingId] = useState(null)
    const weekStart = getCurrentWeekStart()
    const weekEnd = new Date(weekStart); weekEnd.setDate(weekStart.getDate() + 6)
    const weekStartIso = isoDate(weekStart)

    const [form, setForm] = useState({
        leads_recebidos: '',
        leads_contatados: '',
        leads_nao_responderam: '',
        perfil_leads: '',
        faixa_renda: '',
        principal_objecao: '',
        principal_objecao_outro: '',
        empreendimento_interesse: '',
        visitas_agendadas: '',
        visitas_realizadas: '',
        agendamentos_proxima_semana: '',
        lead_em_negociacao: '',
        ajustes_campanha: ''
    })

    useEffect(() => {
        (async () => {
            try {
                const { data: c, error: cErr } = await supabase
                    .from('clients')
                    .select('id, cliente, greeting_name, account_spend_7d')
                    .eq('observacoes', hash)
                    .maybeSingle()
                if (cErr) throw cErr
                if (!c) { setError('Link inválido'); setLoading(false); return }
                setClient(c)

                // Verifica se já tem feedback dessa semana
                const { data: existing } = await supabase
                    .from('client_feedbacks')
                    .select('*')
                    .eq('client_id', c.id)
                    .eq('week_start', weekStartIso)
                    .maybeSingle()
                if (existing) {
                    setExistingId(existing.id)
                    setForm({
                        leads_recebidos: existing.leads_recebidos ?? '',
                        leads_contatados: existing.leads_contatados ?? '',
                        leads_nao_responderam: existing.leads_nao_responderam ?? '',
                        perfil_leads: existing.perfil_leads ?? '',
                        faixa_renda: existing.faixa_renda ?? '',
                        principal_objecao: existing.principal_objecao ?? '',
                        principal_objecao_outro: existing.principal_objecao_outro ?? '',
                        empreendimento_interesse: existing.empreendimento_interesse ?? '',
                        visitas_agendadas: existing.visitas_agendadas ?? '',
                        visitas_realizadas: existing.visitas_realizadas ?? '',
                        agendamentos_proxima_semana: existing.agendamentos_proxima_semana ?? '',
                        lead_em_negociacao: existing.lead_em_negociacao == null ? '' : (existing.lead_em_negociacao ? 'sim' : 'nao'),
                        ajustes_campanha: existing.ajustes_campanha ?? ''
                    })
                }
            } catch (e) {
                console.error(e)
                setError(e.message || 'Erro ao carregar')
            } finally {
                setLoading(false)
            }
        })()
    }, [hash])

    const update = (k) => (e) => setForm(prev => ({ ...prev, [k]: e.target.value }))
    const updateChoice = (k, v) => () => setForm(prev => ({ ...prev, [k]: v }))

    const validate = () => {
        const required = ['leads_recebidos', 'leads_contatados', 'perfil_leads', 'visitas_agendadas', 'visitas_realizadas']
        for (const f of required) {
            if (form[f] === '' || form[f] === null || form[f] === undefined) {
                return 'Preencha o campo: ' + f.replace(/_/g, ' ')
            }
        }
        return null
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        const err = validate()
        if (err) { alert(err); return }
        setSaving(true)
        try {
            const toInt = (v) => (v === '' || v == null) ? null : parseInt(v, 10)
            const payload = {
                client_id: client.id,
                week_start: weekStartIso,
                leads_recebidos: toInt(form.leads_recebidos),
                leads_contatados: toInt(form.leads_contatados),
                leads_nao_responderam: toInt(form.leads_nao_responderam),
                perfil_leads: form.perfil_leads || null,
                faixa_renda: form.faixa_renda || null,
                principal_objecao: form.principal_objecao || null,
                principal_objecao_outro: form.principal_objecao === 'Outro' ? (form.principal_objecao_outro || null) : null,
                empreendimento_interesse: form.empreendimento_interesse || null,
                visitas_agendadas: toInt(form.visitas_agendadas),
                visitas_realizadas: toInt(form.visitas_realizadas),
                agendamentos_proxima_semana: toInt(form.agendamentos_proxima_semana),
                lead_em_negociacao: form.lead_em_negociacao === '' ? null : form.lead_em_negociacao === 'sim',
                ajustes_campanha: form.ajustes_campanha || null
            }
            const { error: upErr } = existingId
                ? await supabase.from('client_feedbacks').update(payload).eq('id', existingId)
                : await supabase.from('client_feedbacks').insert(payload)
            if (upErr) throw upErr
            setSubmitted(true)
            window.scrollTo({ top: 0, behavior: 'smooth' })
        } catch (e) {
            console.error(e)
            alert('Erro ao salvar: ' + (e.message || e))
        } finally {
            setSaving(false)
        }
    }

    if (loading) return (
        <div style={pageBg}><div style={{ color: '#888' }}>Carregando…</div></div>
    )
    if (error) return (
        <div style={pageBg}>
            <div style={cardBg}>
                <h1 style={{ color: '#ef4444' }}>Ops</h1>
                <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
            </div>
        </div>
    )

    if (submitted) return (
        <div style={pageBg}>
            <div style={cardBg}>
                <img src="/tc-logo.png" alt="TC" style={{ height: '60px', marginBottom: '20px' }} />
                <h1 style={{ color: '#10b981', fontSize: '1.6rem', marginBottom: '8px' }}>Obrigado, {client.greeting_name || client.cliente}!</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '24px' }}>
                    Recebemos seu feedback da semana de <b>{fmtDate(weekStart)} a {fmtDate(weekEnd)}</b>.<br/>
                    Você pode reabrir esse link e atualizar a qualquer momento até o fim da semana.
                </p>
                <button onClick={() => setSubmitted(false)} style={btnGhost}>Editar minhas respostas</button>
            </div>
        </div>
    )

    return (
        <div style={pageBg}>
            <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '720px' }}>
                <div style={{ ...cardBg, marginBottom: '20px', textAlign: 'left' }}>
                    <img src="/tc-logo.png" alt="TC" style={{ height: '44px', marginBottom: '14px' }} />
                    <h1 style={{ fontSize: '1.4rem', margin: '0 0 6px 0' }}>Feedback semanal — {client.cliente}</h1>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                        Semana de <b>{fmtDate(weekStart)} a {fmtDate(weekEnd)}</b>
                        {existingId ? ' · Você já enviou. Pode alterar à vontade.' : ''}
                    </p>
                </div>

                <Section title="Quantos leads você recebeu esta semana?" required>
                    <NumberInput value={form.leads_recebidos} onChange={update('leads_recebidos')} placeholder="Ex: 30" />
                </Section>

                <Section title="Quantos você conseguiu contatar?" required>
                    <NumberInput value={form.leads_contatados} onChange={update('leads_contatados')} placeholder="Ex: 18" />
                </Section>

                <Section title="Quantos não responderam?">
                    <NumberInput value={form.leads_nao_responderam} onChange={update('leads_nao_responderam')} placeholder="Ex: 12" />
                </Section>

                <Section title="Os leads estavam dentro do perfil esperado?" required>
                    <Radios options={PERFIL_OPTIONS} value={form.perfil_leads} onSelect={(v) => updateChoice('perfil_leads', v)()} />
                </Section>

                <Section title="Faixa de renda percebida">
                    <Radios options={FAIXA_RENDA_OPTIONS} value={form.faixa_renda} onSelect={(v) => updateChoice('faixa_renda', v)()} />
                </Section>

                <Section title="Principal objeção que apareceu">
                    <Radios options={OBJECAO_OPTIONS} value={form.principal_objecao} onSelect={(v) => updateChoice('principal_objecao', v)()} />
                    {form.principal_objecao === 'Outro' && (
                        <input
                            type="text" value={form.principal_objecao_outro} onChange={update('principal_objecao_outro')}
                            placeholder="Especifique…"
                            style={{ ...inputStyle, marginTop: '8px' }}
                        />
                    )}
                </Section>

                <Section title="Empreendimento de maior interesse">
                    <input type="text" value={form.empreendimento_interesse} onChange={update('empreendimento_interesse')} placeholder="Ex: Riva Botanic, Edifício X…" style={inputStyle} />
                </Section>

                <Section title="Visitas agendadas" required>
                    <NumberInput value={form.visitas_agendadas} onChange={update('visitas_agendadas')} placeholder="Ex: 6" />
                </Section>

                <Section title="Visitas que efetivamente aconteceram" required>
                    <NumberInput value={form.visitas_realizadas} onChange={update('visitas_realizadas')} placeholder="Ex: 4" />
                </Section>

                <Section title="Agendamentos para a próxima semana">
                    <NumberInput value={form.agendamentos_proxima_semana} onChange={update('agendamentos_proxima_semana')} placeholder="Ex: 3" />
                </Section>

                <Section title="Algum lead em negociação/proposta?">
                    <Radios options={['Sim', 'Não']} value={form.lead_em_negociacao === 'sim' ? 'Sim' : form.lead_em_negociacao === 'nao' ? 'Não' : ''}
                        onSelect={(v) => updateChoice('lead_em_negociacao', v === 'Sim' ? 'sim' : 'nao')()} />
                </Section>

                <Section title="Algo que devemos ajustar na campanha?">
                    <textarea value={form.ajustes_campanha} onChange={update('ajustes_campanha')} rows={3} placeholder="Sugestões, observações, ideias…" style={{ ...inputStyle, resize: 'vertical', minHeight: '72px' }} />
                </Section>

                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
                    <button type="submit" disabled={saving} style={btnPrimary}>
                        {saving ? 'Enviando…' : (existingId ? 'Atualizar respostas' : 'Enviar feedback')}
                    </button>
                </div>
            </form>
        </div>
    )
}

const Section = ({ title, required, children }) => (
    <div style={{ ...cardBg, textAlign: 'left', marginBottom: '14px', padding: '20px 24px' }}>
        <label style={{ display: 'block', color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.95rem', marginBottom: '10px' }}>
            {title} {required && <span style={{ color: '#ef4444' }}>*</span>}
        </label>
        {children}
    </div>
)

const NumberInput = ({ value, onChange, placeholder }) => (
    <input type="number" min="0" inputMode="numeric" value={value} onChange={onChange} placeholder={placeholder} style={inputStyle} />
)

const Radios = ({ options, value, onSelect }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {options.map(opt => {
            const active = value === opt
            return (
                <button key={opt} type="button" onClick={() => onSelect(opt)} style={{
                    background: active ? 'rgba(249,115,22,0.12)' : '#0f0f12',
                    color: active ? '#f97316' : 'var(--text-primary)',
                    border: `1px solid ${active ? '#f97316' : '#2a2a30'}`,
                    padding: '10px 14px', borderRadius: '8px', cursor: 'pointer',
                    textAlign: 'left', fontSize: '0.95rem', fontWeight: active ? 600 : 400,
                    transition: 'all 0.12s'
                }}>
                    {active ? '◉ ' : '○ '} {opt}
                </button>
            )
        })}
    </div>
)

const pageBg = {
    background: '#0a0a0a', minHeight: '100vh', padding: '24px 16px',
    display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#fff'
}
const cardBg = {
    background: 'linear-gradient(180deg, #18181c, #0f0f12)',
    border: '1px solid #2a2a30', borderRadius: '12px',
    padding: '28px', maxWidth: '720px', width: '100%',
    textAlign: 'center'
}
const inputStyle = {
    width: '100%', background: '#0f0f12', color: '#fff',
    border: '1px solid #2a2a30', padding: '10px 12px',
    borderRadius: '6px', fontSize: '0.95rem', boxSizing: 'border-box'
}
const btnPrimary = {
    background: 'linear-gradient(135deg, #f97316, #ea580c)', color: '#fff',
    border: 'none', padding: '12px 28px', borderRadius: '8px',
    fontWeight: 700, cursor: 'pointer', fontSize: '0.95rem'
}
const btnGhost = {
    background: 'transparent', color: 'var(--text-secondary)',
    border: '1px solid #2a2a30', padding: '10px 20px',
    borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem'
}

export default FeedbackForm

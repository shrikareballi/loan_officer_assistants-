import { useCallback, useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from './api'
import InvoiceTable from './components/InvoiceTable'
import InvoiceModal from './components/InvoiceModal'
import ReviewModal from './components/ReviewModal'

const currency = (value) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0,
}).format(value || 0)

export default function App() {
  const [page, setPage] = useState('Dashboard')
  const [dashboard, setDashboard] = useState(null)
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewInvoice, setShowNewInvoice] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [query, setQuery] = useState('')

  const refresh = useCallback(async () => {
    try {
      const [nextDashboard, nextInvoices] = await Promise.all([api.dashboard(), api.invoices()])
      setDashboard(nextDashboard)
      setInvoices(nextInvoices)
      setError('')
    } catch (exception) {
      setError(exception.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const filteredInvoices = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return invoices
    return invoices.filter((item) => [item.vendor, item.invoice_number, item.purchase_order, item.risk_level]
      .some((value) => String(value).toLowerCase().includes(needle)))
  }, [invoices, query])

  const summary = dashboard?.summary || {}
  const vendors = dashboard?.vendors || []
  const openInvoices = invoices.filter((invoice) => !invoice.decision)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">L</div><div><strong>Ledgerwise</strong><span>AP INTELLIGENCE</span></div></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {[['Dashboard', '◫'], ['Invoice Queue', '▤'], ['Vendor Memory', '◉']].map(([label, icon]) => (
            <button key={label} className={`nav-link ${page === label ? 'active' : ''}`} onClick={() => setPage(label)}><span className="nav-icon">{icon}</span>{label}{label === 'Invoice Queue' && openInvoices.length > 0 && <em>{openInvoices.length}</em>}</button>
          ))}
        </nav>
        <div className="sidebar-spacer" />
        <div className="memory-status"><span className="status-dot" /><div><strong>Hindsight memory</strong><small>Vendor-scoped retrieval</small></div></div>
        <div className="sidebar-footer"><span className="avatar avatar-user">AP</span><div><strong>AP Operations</strong><small>Demo workspace</small></div><span className="more">···</span></div>
      </aside>

      <main className="main-area">
        <header className="topbar"><div className="breadcrumb">Finance <span>/</span> <strong>{page}</strong></div><div className="topbar-actions"><span className="demo-badge">DEMO ENVIRONMENT</span><button className="button button-primary" onClick={() => setShowNewInvoice(true)}><span className="plus">＋</span> Review invoice</button></div></header>
        <div className="content-area">
          {error && <div className="alert alert-error">Could not load the AP service: {error}. Start the FastAPI server and refresh.</div>}
          {loading ? <div className="loading-state"><span className="spinner" /> Loading invoice workspace…</div> : <>
            {page === 'Dashboard' && <Dashboard dashboard={dashboard} invoices={invoices} vendors={vendors} onSelect={setSelectedInvoice} onGoInvoices={() => setPage('Invoice Queue')} onGoVendors={() => setPage('Vendor Memory')} />}
            {page === 'Invoice Queue' && <InvoiceQueue invoices={filteredInvoices} query={query} setQuery={setQuery} onSelect={setSelectedInvoice} />}
            {page === 'Vendor Memory' && <VendorMemoryPage vendors={vendors} />}
          </>}
        </div>
      </main>

      {showNewInvoice && <InvoiceModal onClose={() => setShowNewInvoice(false)} onReviewed={(invoice) => { setShowNewInvoice(false); setSelectedInvoice(invoice); refresh() }} />}
      {selectedInvoice && <ReviewModal invoice={selectedInvoice} onClose={() => setSelectedInvoice(null)} onChanged={refresh} />}
    </div>
  )
}

function Dashboard({ dashboard, invoices, vendors, onSelect, onGoInvoices, onGoVendors }) {
  const summary = dashboard?.summary || {}
  const attention = invoices.filter((item) => !item.decision && item.risk_score >= 25)
  const northstar = vendors.find((item) => item.vendor === 'Northstar Office Supply')
  return <>
    <div className="page-heading"><div><span className="eyebrow">{new Intl.DateTimeFormat('en', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date()).toUpperCase()}</span><h1>Accounts payable overview</h1><p>Review invoice exceptions with a vendor history that learns from every confirmed case.</p></div><button className="text-button" onClick={onGoInvoices}>View invoice queue <span>→</span></button></div>
    <section className="stats-grid" aria-label="Portfolio summary">
      <StatCard label="Invoices reviewed" value={summary.invoice_count || 0} note="Across this workspace" icon="▤" tone="violet" />
      <StatCard label="Awaiting review" value={summary.open_count || 0} note={`${attention.length} with an exception`} icon="◷" tone="amber" />
      <StatCard label="Open invoice value" value={currency(summary.total_open_amount)} note="Human decision pending" icon="$" tone="green" />
      <StatCard label="Vendor histories" value={vendors.length} note="Built from resolved cases" icon="◉" tone="blue" />
    </section>
    <div className="dashboard-grid">
      <section className="panel chart-panel"><div className="section-heading"><div><span className="eyebrow">PORTFOLIO</span><h2>Invoice volume</h2></div><span className="select-chip">Recent activity⌄</span></div>
        <div className="chart-wrap">{dashboard?.monthly_volume?.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={dashboard.monthly_volume} margin={{ top: 12, right: 10, left: 4, bottom: 2 }}><CartesianGrid stroke="#eeeef0" vertical={false} /><XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#85838e', fontSize: 11 }} /><YAxis axisLine={false} tickLine={false} tickFormatter={(value) => `$${Math.round(value / 1000)}k`} tick={{ fill: '#85838e', fontSize: 11 }} width={42} /><Tooltip formatter={(value) => currency(value)} cursor={{ fill: '#f4f1fb' }} /><Bar dataKey="amount" fill="#6e56cf" radius={[5, 5, 0, 0]} maxBarSize={42} /></BarChart></ResponsiveContainer> : <div className="empty-chart">Invoice activity will appear here.</div>}</div>
      </section>
      <section className="memory-hero"><div className="memory-orbit"><span>✦</span></div><span className="eyebrow">MEMORY IN ACTION</span><h2>Vendor exceptions<br />become learned context.</h2><p>Hindsight recalls prior resolutions by vendor, then grounds the next review in those cases.</p><div className="memory-example"><div className="example-top"><span className="avatar avatar-vendor">N</span><div><strong>Northstar Office Supply</strong><small>Vendor pattern · {northstar?.prior_variance_cases || 2} prior variances</small></div></div><div className="example-quote">“Both prior overages were held until supporting documentation arrived.”</div></div><button className="memory-link" onClick={onGoVendors}>Explore vendor memory <span>↗</span></button></section>
    </div>
    <div className="lower-grid">
      <section className="panel table-panel"><div className="section-heading"><div><span className="eyebrow">WORK QUEUE</span><h2>Recent invoices</h2></div><button className="subtle-button" onClick={onGoInvoices}>All invoices →</button></div><InvoiceTable invoices={dashboard?.recent_invoices || []} onSelect={onSelect} compact /></section>
      <section className="panel attention-panel"><div className="section-heading"><div><span className="eyebrow">PRIORITIZED BY RISK</span><h2>Needs attention</h2></div><span className="count-badge">{attention.length}</span></div>
        {attention.slice(0, 4).map((item) => <button className="attention-item" key={item.id} onClick={() => onSelect(item)}><span className={`attention-mark risk-${item.risk_level.toLowerCase()}`}>!</span><span className="attention-text"><strong>{item.vendor}</strong><small>{item.invoice_number} · {item.risk_level} attention</small></span><b>{currency(item.invoice_amount)}</b></button>)}
        {!attention.length && <p className="muted pad-small">No open exceptions in the current queue.</p>}
      </section>
    </div>
  </>
}

function StatCard({ label, value, note, icon, tone }) {
  return <div className="stat-card"><div className="stat-card-top"><span>{label}</span><span className={`stat-icon ${tone}`}>{icon}</span></div><strong className="stat-value">{value}</strong><small>{note}</small></div>
}

function InvoiceQueue({ invoices, query, setQuery, onSelect }) {
  const [filter, setFilter] = useState('All invoices')
  const shown = filter === 'Open only' ? invoices.filter((invoice) => !invoice.decision) : invoices
  return <><div className="page-heading"><div><span className="eyebrow">AP OPERATIONS</span><h1>Invoice queue</h1><p>Review flagged invoices, compare their purchase orders, and record outcomes.</p></div></div>
    <section className="panel queue-panel"><div className="queue-toolbar"><div className="filter-tabs">{['All invoices', 'Open only'].map((item) => <button key={item} className={filter === item ? 'selected' : ''} onClick={() => setFilter(item)}>{item}</button>)}</div><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search vendor or invoice" /></label></div><InvoiceTable invoices={shown} onSelect={onSelect} /></section>
  </>
}

function VendorMemoryPage({ vendors }) {
  const [selected, setSelected] = useState(vendors[0]?.vendor || '')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    if (!selected && vendors.length) setSelected(vendors[0].vendor)
  }, [selected, vendors])
  useEffect(() => {
    if (!selected) return
    setLoading(true)
    api.vendorMemory(selected).then(setData).catch((error) => setData({ error: error.message })).finally(() => setLoading(false))
  }, [selected])
  const profile = data?.profile
  const memory = data?.memory
  return <><div className="page-heading"><div><span className="eyebrow">LONG-TERM CONTEXT</span><h1>Vendor memory</h1><p>See how confirmed invoice resolutions shape the next review.</p></div></div>
    <div className="vendor-layout"><section className="panel vendor-list-panel" data-vendor-list><div className="section-heading"><div><span className="eyebrow">SUPPLIER PROFILES</span><h2>Known vendors</h2></div><span className="count-badge">{vendors.length}</span></div>{vendors.map((vendor) => <button key={vendor.vendor} className={`vendor-select ${selected === vendor.vendor ? 'selected' : ''}`} onClick={() => setSelected(vendor.vendor)}><span className="vendor-avatar">{vendor.vendor.slice(0, 1)}</span><span><strong>{vendor.vendor}</strong><small>{vendor.resolved_cases} resolved cases</small></span><span className="arrow">›</span></button>)}</section>
      <section className="panel vendor-profile-panel">{loading ? <div className="loading-state"><span className="spinner" /> Recalling vendor history…</div> : profile ? <><div className="profile-title"><div className="vendor-avatar large">{selected.slice(0, 1)}</div><div><span className="eyebrow">VENDOR PROFILE</span><h2>{selected}</h2><p>Learned only from recorded, human-confirmed invoice outcomes.</p></div></div><div className="profile-metrics"><div><span>Confirmed cases</span><strong>{profile.resolved_cases}</strong></div><div><span>Prior PO variances</span><strong>{profile.prior_variance_cases}</strong></div><div><span>Common payment terms</span><strong>{profile.usual_payment_terms || 'Not known'}</strong></div></div><div className="reflection-box"><div className="card-title-row"><h3>Hindsight reflection</h3><span className={memory?.available ? 'live-dot' : 'offline-dot'}>{memory?.available ? 'GROUNDED' : 'UNAVAILABLE'}</span></div>{memory?.summary ? <p>{memory.summary}</p> : <p className="muted">{memory?.error || 'No Hindsight summary is available for this vendor yet.'}</p>}{memory?.sources?.length > 0 && <div className="memory-sources">{memory.sources.map((source, index) => <blockquote key={index}>{source}</blockquote>)}</div>}</div><h3 className="history-heading">Confirmed review outcomes</h3><div className="case-list">{profile.cases?.map((item) => <div className="case-row" key={item.invoice_number}><span className="case-date">{item.created_at?.slice(0, 10)}</span><span><strong>{item.invoice_number}</strong><small>{item.resolution}</small></span><span className="variance-bad">{item.variance_pct > 0 ? '+' : ''}{item.variance_pct}%</span><span className="decision-label">{item.decision}</span></div>)}</div></> : <div className="empty-state">No vendor history yet.</div>}</section></div>
  </>
}

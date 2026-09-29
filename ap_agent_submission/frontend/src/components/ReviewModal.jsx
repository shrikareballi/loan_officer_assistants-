import { useState } from 'react'
import { api } from '../api'

const money = (value) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0)

export default function ReviewModal({ invoice: initialInvoice, onClose, onChanged }) {
  const [invoice, setInvoice] = useState(initialInvoice)
  const [decision, setDecision] = useState('hold')
  const [resolution, setResolution] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function saveDecision(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const updated = await api.resolveInvoice(invoice.id, { decision, resolution })
      setInvoice(updated)
      setNotice(updated.memory_save?.message || 'Decision recorded.')
      onChanged()
    } catch (exception) {
      setError(exception.message)
    } finally {
      setSaving(false)
    }
  }

  const memory = invoice.memory || {}
  return (
    <div className="overlay" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal review-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
        <div className="modal-head"><div><span className="eyebrow">INVOICE {invoice.invoice_number}</span><h2 id="review-title">{invoice.vendor}</h2><p>{invoice.purchase_order} · Due {invoice.due_date} · {invoice.payment_terms}</p></div><button className="icon-button" onClick={onClose} aria-label="Close">×</button></div>
        <div className="review-score-row"><div className={`score score-${invoice.risk_level.toLowerCase()}`}><strong>{invoice.risk_score}</strong><span>attention score</span></div><div><span className={`risk-pill risk-${invoice.risk_level.toLowerCase()}`}>{invoice.risk_level} attention</span><h3>{invoice.recommendation}</h3><p className="muted">This is a review aid. A person makes the payment decision.</p></div></div>
        <div className="review-grid">
          <div className="review-card"><h3>Why it was flagged</h3>{invoice.factors?.length ? <ul className="factor-list">{invoice.factors.map((factor) => <li key={factor.code}><span className="factor-dot" /><span><strong>{factor.label}</strong><small>{factor.detail}</small></span><b>+{factor.points}</b></li>)}</ul> : <p className="muted">No configured exception was detected.</p>}</div>
          <div className="review-card memory-card"><div className="card-title-row"><h3>What Hindsight remembers</h3><span className={memory.sources?.length ? 'live-dot' : memory.available ? 'offline-dot' : 'offline-dot'}>{memory.sources?.length ? 'GROUNDED' : memory.available ? 'NO MATCHES' : 'OFFLINE'}</span></div>
            {memory.summary ? <p className="memory-summary">{memory.summary}</p> : <p className="muted">{memory.error ? `Memory service is unavailable: ${memory.error}` : 'No matching vendor memories yet.'}</p>}
            {memory.sources?.length > 0 && <div className="memory-sources"><span className="eyebrow">SOURCE CASES</span>{memory.sources.map((source, index) => <blockquote key={index}>{source}</blockquote>)}</div>}
            <div className="mini-profile"><span>{invoice.vendor_profile?.resolved_cases || 0} resolved vendor cases</span><span>{invoice.vendor_profile?.prior_variance_cases || 0} previous PO variances</span><span>Usual terms: {invoice.vendor_profile?.usual_payment_terms || 'Not established'}</span></div>
          </div>
        </div>
        <div className="amount-comparison"><div><span>Invoice amount</span><strong>{money(invoice.invoice_amount)}</strong></div><span className="comparison-arrow">−</span><div><span>Purchase order</span><strong>{money(invoice.purchase_order_amount)}</strong></div><div className={Math.abs(invoice.variance_pct) > 2 ? 'variance-chip variance-chip-bad' : 'variance-chip'}>{invoice.variance_pct > 0 ? '+' : ''}{invoice.variance_pct}% variance</div></div>
        {!invoice.decision ? <form className="resolution-form" onSubmit={saveDecision}><h3>Record the human outcome</h3><div className="resolution-controls"><label>Decision<select value={decision} onChange={(event) => setDecision(event.target.value)}><option value="hold">Hold for correction</option><option value="escalated">Escalate to manager</option><option value="approved">Approve under policy</option></select></label><label className="resolution-note">Resolution notes<textarea required minLength="8" maxLength="1200" value={resolution} onChange={(event) => setResolution(event.target.value)} placeholder="What evidence was checked, and how was this exception resolved?" /></label></div><div className="modal-foot"><span className="muted">Confirmed outcomes become vendor-specific Hindsight memory.</span><button className="button button-primary" disabled={saving}>{saving ? 'Saving…' : 'Save decision & teach memory'}</button></div>{error && <div className="alert alert-error">{error}</div>}</form> : <div className="alert alert-success"><strong>Decision recorded: {invoice.decision}</strong><br />{invoice.resolution}{notice && <p>{notice}</p>}</div>}
      </section>
    </div>
  )
}

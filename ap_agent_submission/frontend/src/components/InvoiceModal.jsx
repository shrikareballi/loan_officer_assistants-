import { useState } from 'react'
import { api } from '../api'

const today = new Date().toISOString().slice(0, 10)
const nextMonth = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10)

export default function InvoiceModal({ onClose, onReviewed }) {
  const [form, setForm] = useState({
    vendor: '', invoice_number: '', purchase_order: '', invoice_date: today,
    due_date: nextMonth, invoice_amount: '5320', purchase_order_amount: '5000',
    payment_terms: 'Net 30',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))

  async function submit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const review = await api.reviewInvoice({
        ...form,
        invoice_amount: Number(form.invoice_amount),
        purchase_order_amount: Number(form.purchase_order_amount),
      })
      onReviewed(review)
    } catch (exception) {
      setError(exception.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="overlay" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="invoice-modal-title">
        <div className="modal-head"><div><span className="eyebrow">ACCOUNTS PAYABLE</span><h2 id="invoice-modal-title">Review an invoice</h2><p>Compare the invoice with its purchase order and vendor history.</p></div><button className="icon-button" onClick={onClose} aria-label="Close">×</button></div>
        <form onSubmit={submit}>
          <div className="form-grid">
            <label>Vendor name<input required minLength="2" value={form.vendor} onChange={update('vendor')} placeholder="Northstar Office Supply" /></label>
            <label>Invoice number<input required value={form.invoice_number} onChange={update('invoice_number')} placeholder="NS-1204" /></label>
            <label>Purchase order<input required value={form.purchase_order} onChange={update('purchase_order')} placeholder="PO-3510" /></label>
            <label>Payment terms<input required value={form.payment_terms} onChange={update('payment_terms')} placeholder="Net 30" /></label>
            <label>Invoice date<input required type="date" value={form.invoice_date} onChange={update('invoice_date')} /></label>
            <label>Due date<input required type="date" value={form.due_date} onChange={update('due_date')} /></label>
            <label>Invoice amount ($)<input required type="number" min="0.01" step="0.01" value={form.invoice_amount} onChange={update('invoice_amount')} /></label>
            <label>Purchase order amount ($)<input required type="number" min="0.01" step="0.01" value={form.purchase_order_amount} onChange={update('purchase_order_amount')} /></label>
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          <div className="modal-foot"><span className="muted">Recommendations support a human review; they do not authorize payment.</span><button className="button button-primary" disabled={saving}>{saving ? 'Analyzing vendor history…' : 'Analyze invoice'} <span>→</span></button></div>
        </form>
      </section>
    </div>
  )
}

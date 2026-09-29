const money = (value) => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD', maximumFractionDigits: 0,
}).format(value || 0)

export default function InvoiceTable({ invoices = [], onSelect, compact = false }) {
  if (!invoices.length) {
    return <div className="empty-state"><span className="empty-icon">▤</span><strong>No invoices yet</strong><span>New invoice reviews will appear here.</span></div>
  }
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Vendor / invoice</th><th>Due date</th><th>Amount</th><th>PO variance</th><th>Risk</th><th>Decision</th></tr></thead>
        <tbody>{invoices.slice(0, compact ? 5 : 100).map((invoice) => (
          <tr key={invoice.id} onClick={() => onSelect(invoice)} className="click-row" tabIndex={0} onKeyDown={(event) => event.key === 'Enter' && onSelect(invoice)}>
            <td><div className="vendor-cell"><span className="vendor-avatar">{invoice.vendor.slice(0, 1).toUpperCase()}</span><span><strong>{invoice.vendor}</strong><small>{invoice.invoice_number} · {invoice.purchase_order}</small></span></div></td>
            <td>{invoice.due_date}</td>
            <td className="amount-cell">{money(invoice.invoice_amount)}</td>
            <td className={Math.abs(invoice.variance_pct) > 2 ? 'variance-bad' : 'muted'}>{invoice.variance_pct > 0 ? '+' : ''}{invoice.variance_pct}%</td>
            <td><span className={`risk-pill risk-${invoice.risk_level.toLowerCase()}`}>{invoice.risk_level}</span></td>
            <td>{invoice.decision ? <span className="decision-label">{invoice.decision}</span> : <span className="pending-label">Needs review</span>}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

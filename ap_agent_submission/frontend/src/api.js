async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof payload.detail === 'string' ? payload.detail : 'Request failed.'
    throw new Error(detail)
  }
  return payload
}

export const api = {
  health: () => request('/health'),
  dashboard: () => request('/dashboard'),
  invoices: () => request('/invoices'),
  vendors: () => request('/vendors'),
  vendorMemory: (vendor) => request(`/vendors/${encodeURIComponent(vendor)}/memory`),
  reviewInvoice: (invoice) => request('/invoices/review', {
    method: 'POST',
    body: JSON.stringify(invoice),
  }),
  resolveInvoice: (id, payload) => request(`/invoices/${id}/resolve`, {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
}

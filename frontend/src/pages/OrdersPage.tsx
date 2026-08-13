import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getOrders, getOrderSummary } from '../api'

const statuses = [
  ['in_progress', 'Pågående'],
  ['backorder', 'Restorder'],
  ['attention', 'Behöver hjälp'],
  ['completed', 'Klar'],
  ['cancelled', 'Avbokad'],
] as const

const statusLabels = Object.fromEntries(statuses)

export function OrdersPage() {
  const [urlParams, setUrlParams] = useSearchParams()
  const search = urlParams.get('q') || ''
  const status = urlParams.get('status') || ''
  const requestedPage = Number.parseInt(urlParams.get('page') || '1', 10)
  const page = Number.isFinite(requestedPage) && requestedPage > 0 ? requestedPage : 1
  const apiParams = useMemo(() => {
    const value = new URLSearchParams({ page: String(page), page_size: '50' })
    if (search) value.set('q', search)
    if (status) value.set('status', status)
    return value
  }, [page, search, status])
  const orders = useQuery({ queryKey: ['orders', apiParams.toString()], queryFn: () => getOrders(apiParams) })
  const summary = useQuery({ queryKey: ['order-summary'], queryFn: getOrderSummary })
  const updateUrl = (changes: Record<string, string | null>, replace = false) => {
    const next = new URLSearchParams(urlParams)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setUrlParams(next, { replace })
  }
  const updateSearch = (value: string) => updateUrl({ q: value, page: null }, true)
  const updateStatus = (value: string) => updateUrl({ status: value, page: null })
  const updatePage = (value: number) => updateUrl({ page: value > 1 ? String(value) : null })

  return <section className="orders-page">
    <div className="orders-head"><div><p className="eyebrow">CRM · Orderöversikt</p><h1>Orderflöde</h1><p>Följ ordern från beställning till leverans och se vilka artiklar som är kopplade till katalogen.</p></div><div className="summary"><strong>{summary.data?.total ?? '—'}</strong><span>ordrar totalt</span><strong>{summary.data?.unmatched_items ?? '—'}</strong><span>olänkade orderrader</span></div></div>
    <div className="order-toolbar"><label className="order-search">⌕<input value={search} onChange={(event) => updateSearch(event.target.value)} placeholder="Sök ordernummer, kund, e-post eller registreringsnummer" /></label><select value={status} onChange={(event) => updateStatus(event.target.value)}><option value="">Alla statusar</option>{statuses.map(([value, label]) => <option key={value} value={value}>{label} ({summary.data?.by_status[value] ?? 0})</option>)}</select></div>
    {orders.isLoading && <div className="state">Hämtar orderflödet…</div>}
    {orders.isError && <div className="state error">Orderflödet kunde inte hämtas.</div>}
    {orders.data && <>
      <div className="order-result-head"><span>{orders.data.total} ordrar</span><span>Sida {orders.data.page} av {orders.data.pages || 1}</span></div>
      <div className="order-table-wrap"><table className="order-table"><thead><tr><th>Order</th><th>Datum</th><th>Kund</th><th>Orderrader</th><th>Reg.nr</th><th>Status</th><th>Ansvarig</th><th></th></tr></thead><tbody>{orders.data.items.map((order) => { const unmatched = order.items.filter((item) => item.link_status !== 'linked').length; return <tr key={order.id}><td><Link to={`/orders/${order.id}`}><strong>#{order.external_id}</strong></Link></td><td>{order.ordered_at ? new Date(order.ordered_at).toLocaleDateString('sv-SE') : '—'}</td><td><Link to={`/orders/${order.id}`}><strong>{order.customer.name}</strong><small>{order.customer.email || order.customer.city || ''}</small></Link></td><td><span className="order-items-text">{order.items.map((item) => item.description).join(' + ') || 'Inga orderrader'}</span>{unmatched > 0 && <small className="unmatched">{unmatched} ej länkad{unmatched > 1 ? 'e' : ''}</small>}</td><td>{order.registration_number || '—'}</td><td><span className={`status-pill ${order.status}`}>{statusLabels[order.status] || order.status}</span></td><td>{order.sales_person || '—'}</td><td><Link className="row-link" to={`/orders/${order.id}`} aria-label={`Öppna order ${order.external_id}`}>→</Link></td></tr>})}</tbody></table>{orders.data.items.length === 0 && <div className="state">Inga ordrar matchar sökningen.</div>}</div>
      {orders.data.pages > 1 && <div className="pagination"><button disabled={page <= 1} onClick={() => updatePage(page - 1)}>← Föregående</button><span>{page} / {orders.data.pages}</span><button disabled={page >= orders.data.pages} onClick={() => updatePage(page + 1)}>Nästa →</button></div>}
    </>}
  </section>
}

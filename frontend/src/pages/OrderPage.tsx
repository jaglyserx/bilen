import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getOrder } from '../api'

export function OrderPage() {
  const { id = '' } = useParams()
  const query = useQuery({ queryKey: ['order', id], queryFn: () => getOrder(id) })
  if (query.isLoading) return <div className="state">Hämtar order…</div>
  if (!query.data) return <div className="state error">Ordern hittades inte.</div>
  const order = query.data
  return <article className="order-detail">
    <Link className="back" to="/orders">← Till orderflödet</Link>
    <div className="order-title"><div><p className="eyebrow">Order #{order.external_id}</p><h1>{order.customer.name}</h1><p>{order.workflow_status || order.status}</p></div><span className={`status-pill ${order.status}`}>{order.status.replace('_', ' ')}</span></div>
    <div className="detail-grid"><section><h2>Orderrader</h2>{order.items.map((item) => <div className="order-line" key={item.id}><div><span className="tag">{item.kind === 'primary' ? 'Produkt' : item.kind === 'electrical' ? 'Elsats' : 'Produkt'}</span><h3>{item.description}</h3><code>{item.source_sku || 'Artikelnummer saknas'} · {item.quantity} st</code></div>{item.product ? <Link className="linked-product" to={`/products/${item.product.id}`}>Kopplad till<br/><strong>{item.product.article_number}</strong> →</Link> : <span className="unmatched">Ej kopplad till katalogen</span>}</div>)}</section><aside><h2>Kund & fordon</h2><dl><dt>Verkstad</dt><dd>{order.workshop ? <Link to={`/workshops/${order.workshop.id}`}>{order.workshop.name}</Link> : '—'}</dd><dt>E-post</dt><dd>{order.customer.email || '—'}</dd><dt>Telefon</dt><dd>{order.customer.phone || '—'}</dd><dt>Ort</dt><dd>{order.customer.city || '—'}</dd><dt>Registrering</dt><dd>{order.registration_number || '—'}</dd><dt>Fordon</dt><dd>{order.vehicle_label || '—'}</dd><dt>Ansvarig</dt><dd>{order.sales_person || '—'}</dd><dt>Summa</dt><dd>{order.total_amount ? `${order.total_amount} ${order.currency}` : '—'}</dd></dl></aside></div>
  </article>
}

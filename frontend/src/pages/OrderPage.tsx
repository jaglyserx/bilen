import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { confirmOrder, getOrder } from '../api'

const statusLabels: Record<string, string> = {
  draft: 'Offert', in_progress: 'Pågående', backorder: 'Restorder', attention: 'Behöver hjälp', completed: 'Klar', cancelled: 'Avbokad',
}

export function OrderPage() {
  const { id = '' } = useParams()
  const queryClient = useQueryClient()
  const query = useQuery({ queryKey: ['order', id], queryFn: () => getOrder(id) })
  const confirmation = useMutation({ mutationFn: () => confirmOrder(id), onSuccess: (order) => { queryClient.setQueryData(['order', id], order); void queryClient.invalidateQueries({ queryKey: ['orders'] }); void queryClient.invalidateQueries({ queryKey: ['order-summary'] }) } })
  if (query.isLoading) return <div className="state">Hämtar order…</div>
  if (!query.data) return <div className="state error">Ordern hittades inte.</div>
  const order = query.data
  return <article className="order-detail">
    <Link className="back" to="/orders">← Till orderflödet</Link>
    <div className="order-title"><div><p className="eyebrow">{order.status === 'draft' ? 'Offert' : 'Order'} #{order.external_id}</p><h1>{order.customer.name}</h1><p>{order.workflow_status || order.status}</p></div><div className="order-title-actions"><span className={`status-pill ${order.status}`}>{statusLabels[order.status] || order.status}</span>{order.status === 'draft' && <button className="primary" disabled={confirmation.isPending} onClick={() => confirmation.mutate()}>{confirmation.isPending ? 'Bekräftar…' : 'Bekräfta som order'}</button>}</div></div>
    {order.status === 'draft' && <div className="offer-notice"><strong>Detta är en offert.</strong><span>När den bekräftas skapas integrationshändelser för verkstadsmeddelande och kundens betalningslänk.</span>{(!order.customer.email || !order.workshop) && <span className="form-error">Kundens e-post och en aktiv verkstad måste finnas innan offerten kan bekräftas.</span>}{confirmation.isError && <span className="form-error">Offerten kunde inte bekräftas. Kontrollera e-post och verkstad.</span>}</div>}
    <div className="detail-grid"><section><h2>Orderrader</h2>{order.items.map((item) => <div className="order-line" key={item.id}><div><span className="tag">Produkt</span><h3>{item.description}</h3><code>{item.source_sku || 'Artikelnummer saknas'} · {item.quantity} st</code></div>{item.product ? <Link className="linked-product" to={`/products/${item.product.id}`}>Kopplad till<br/><strong>{item.product.article_number}</strong> →</Link> : <span className="unmatched">Ej kopplad till katalogen</span>}</div>)}</section><aside><h2>Kund & fordon</h2><dl><dt>Verkstad</dt><dd>{order.workshop ? <Link to={`/workshops/${order.workshop.id}`}>{order.workshop.name}</Link> : 'Väljs senare'}</dd><dt>E-post</dt><dd>{order.customer.email || '—'}</dd><dt>Telefon</dt><dd>{order.customer.phone || '—'}</dd><dt>Ort</dt><dd>{order.customer.city || '—'}</dd><dt>Registrering</dt><dd>{order.registration_number || '—'}</dd><dt>Fordon</dt><dd>{order.vehicle_label || '—'}</dd><dt>Ansvarig</dt><dd>{order.sales_person || '—'}</dd><dt>Summa</dt><dd>{order.total_amount ? `${order.total_amount} ${order.currency}` : '—'}</dd></dl></aside></div>
  </article>
}

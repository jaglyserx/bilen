import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getWorkshop } from '../api'

export function WorkshopPage() {
  const { id = '' } = useParams()
  const query = useQuery({ queryKey: ['workshop', id], queryFn: () => getWorkshop(id) })
  if (query.isLoading) return <div className="state">Hämtar verkstad…</div>
  if (!query.data) return <div className="state error">Verkstaden hittades inte.</div>
  const workshop = query.data
  return <article className="workshop-detail"><Link className="back" to="/workshops">← Till verkstäder</Link><div className="order-title"><div><p className="eyebrow">{workshop.city || 'Verkstad'}</p><h1>{workshop.name}</h1><p>{[workshop.address, workshop.postal_code, workshop.city].filter(Boolean).join(', ')}</p></div><span className={`status-pill ${workshop.is_active ? 'completed' : 'cancelled'}`}>{workshop.is_active ? 'Aktiv' : 'Inaktiv'}</span></div><div className="detail-grid"><section><h2>Operativ information</h2><div className="info-block"><h3>Bokning</h3><p>{workshop.booking_instructions || 'Inga särskilda bokningsinstruktioner.'}</p><h3>Aktuellt</h3><p>{workshop.current_info || 'Ingen aktuell kapacitetsinformation.'}</p><h3>Verkstadsinfo</h3><p>{workshop.workshop_info || '—'}</p><h3>Begränsningar</h3><p>{workshop.restrictions || 'Inga angivna.'}</p></div><h2>Avtal</h2><div className="info-block"><p>{workshop.agreement_terms || 'Inga avtalsvillkor angivna.'}</p><p>{workshop.discount_terms}</p></div></section><aside><h2>Kontakt</h2><dl><dt>Kontaktperson</dt><dd>{workshop.contact_person || '—'}</dd><dt>Telefon</dt><dd>{workshop.phone || '—'}</dd><dt>E-post</dt><dd>{workshop.email || '—'}</dd><dt>Ansvarig B&J</dt><dd>{workshop.internal_owner || '—'}</dd><dt>Lånebil</dt><dd>{workshop.loan_car_available == null ? '—' : workshop.loan_car_available ? 'Ja' : 'Nej'}</dd><dt>Husbil</dt><dd>{workshop.supports_motorhomes == null ? '—' : workshop.supports_motorhomes ? 'Ja' : 'Nej'}</dd></dl></aside></div></article>
}

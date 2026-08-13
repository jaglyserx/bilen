import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { getWorkshops } from '../api'

export function WorkshopsPage() {
  const [url, setUrl] = useSearchParams()
  const q = url.get('q') || ''
  const page = Math.max(1, Number.parseInt(url.get('page') || '1', 10) || 1)
  const showAll = url.get('active') === 'all'
  const params = new URLSearchParams({ page: String(page), page_size: '50' })
  if (q) params.set('q', q)
  if (showAll) params.set('active', '')
  const query = useQuery({ queryKey: ['workshops', params.toString()], queryFn: () => getWorkshops(params) })
  const update = (changes: Record<string, string | null>, replace = false) => { const next = new URLSearchParams(url); Object.entries(changes).forEach(([key, value]) => value ? next.set(key, value) : next.delete(key)); setUrl(next, { replace }) }
  return <section className="workshops-page"><div className="workshops-head"><p className="eyebrow">Samarbetspartners</p><h1>Verkstäder</h1><p>Hitta kontaktuppgifter, bokningsrutiner och aktuell kapacitet hos anslutna verkstäder.</p></div><div className="order-toolbar"><label className="order-search">⌕<input value={q} onChange={(event) => update({ q: event.target.value, page: null }, true)} placeholder="Sök namn, ort, postnummer eller kontaktperson" /></label><select value={showAll ? 'all' : 'active'} onChange={(event) => update({ active: event.target.value === 'all' ? 'all' : null, page: null })}><option value="active">Aktiva verkstäder</option><option value="all">Alla verkstäder</option></select></div>{query.isLoading && <div className="state">Hämtar verkstäder…</div>}{query.isError && <div className="state error">Verkstäderna kunde inte hämtas.</div>}{query.data && <><div className="order-result-head"><span>{query.data.total} verkstäder</span><span>Sida {query.data.page} av {query.data.pages || 1}</span></div><div className="workshop-grid">{query.data.items.map((workshop) => <Link className="workshop-card" to={`/workshops/${workshop.id}`} key={workshop.id}><div className="card-top"><span className={`status-dot ${workshop.is_active ? 'active' : ''}`}>{workshop.is_active ? 'Aktiv' : 'Inaktiv'}</span><span>{workshop.city || 'Ort saknas'}</span></div><h2>{workshop.name}</h2><p>{[workshop.address, workshop.postal_code, workshop.city].filter(Boolean).join(', ')}</p><dl><dt>Kontakt</dt><dd>{workshop.contact_person || '—'}</dd><dt>Telefon</dt><dd>{workshop.phone || '—'}</dd></dl><div className="capabilities">{workshop.loan_car_available && <span>Lånebil</span>}{workshop.supports_motorhomes && <span>Husbil</span>}</div></Link>)}</div>{query.data.pages > 1 && <div className="pagination"><button disabled={page <= 1} onClick={() => update({ page: page > 2 ? String(page - 1) : null })}>← Föregående</button><span>{page} / {query.data.pages}</span><button disabled={page >= query.data.pages} onClick={() => update({ page: String(page + 1) })}>Nästa →</button></div>}</>}</section>
}

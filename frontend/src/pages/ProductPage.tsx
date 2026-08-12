import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { getProduct } from '../api'

const yesNo = (value?: boolean | null) => value == null ? 'Ej angivet' : value ? 'Ja' : 'Nej'

export function ProductPage() {
  const { id = '' } = useParams()
  const { data: product, isLoading, isError } = useQuery({ queryKey: ['product', id], queryFn: () => getProduct(id) })
  if (isLoading) return <div className="state">Laddar produkt…</div>
  if (isError || !product) return <div className="state error"><h1>Produkten kunde inte visas</h1><Link to="/">Tillbaka till katalogen</Link></div>
  const price = product.prices.find(p => p.kind === 'retail_inc_vat')
  return <article className="detail"><Link to="/" className="back">← Till katalogen</Link><div className="detail-head"><div><p className="eyebrow">{product.manufacturer.name} · {product.article_number}</p><h1>{product.name || product.towbar_type || 'Bildel'}</h1><p className="lead">{product.description}</p></div><aside><span>Pris inkl. moms</span><strong>{price ? `${Number(price.amount).toLocaleString('sv-SE')} kr` : 'På förfrågan'}</strong>{product.webshop_url && <a href={product.webshop_url} target="_blank" rel="noreferrer" className="primary">Visa i webbutiken</a>}</aside></div>
    <div className="detail-grid"><section><h2>Fordonsanpassning</h2>{product.fitments.map(f => <div className="fitment-row" key={f.id}><strong>{f.vehicle.source_label}</strong>{f.fitment_notes && <p>{f.fitment_notes}</p>}</div>)}</section><section><h2>Specifikation</h2><dl><dt>Typ</dt><dd>{product.towbar_type || '–'}</dd><dt>Max dragvikt</dt><dd>{product.max_towing_weight_kg ? `${product.max_towing_weight_kg} kg` : '–'}</dd><dt>Max kultryck</dt><dd>{product.max_ball_weight_kg ? `${product.max_ball_weight_kg} kg` : '–'}</dd><dt>Utskärning</dt><dd>{yesNo(product.cutout_required)}</dd><dt>Låsbar</dt><dd>{yesNo(product.lockable)}</dd><dt>Monteringstid</dt><dd>{product.installation_minutes ? `${product.installation_minutes} min` : '–'}</dd><dt>EAN</dt><dd>{product.ean || '–'}</dd></dl></section></div>
    {product.links && product.links.length > 0 && <section className="links"><h2>Dokument och länkar</h2>{product.links.map(link => <a key={`${link.kind}-${link.url}`} href={link.url} target="_blank" rel="noreferrer">{link.kind === 'installation' ? 'Monteringsanvisning' : link.kind === 'wiring' ? 'Kopplingsschema' : 'Webbutik'} ↗</a>)}</section>}</article>
}

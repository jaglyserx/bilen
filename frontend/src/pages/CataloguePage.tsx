import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { getFilters, getProducts } from '../api'
import type { Price, Product } from '../types'

function retailPrice(prices: Price[]) { return prices.find(p => p.kind === 'retail_inc_vat') }

function ProductCard({ product }: { product: Product }) {
  const price = retailPrice(product.prices)
  return <Link to={`/products/${product.id}`} className="card">
    <div className="card-top"><span className="tag">{product.towbar_type || 'Bildel'}</span><span className="sku">{product.article_number}</span></div>
    <h2>{product.name || `${product.manufacturer.name} ${product.article_number}`}</h2>
    <p className="maker">{product.manufacturer.name}</p>
    <p className="fitment">{product.fitments[0]?.vehicle.source_label || 'Fordonsinformation saknas'}</p>
    {product.fitments.length > 1 && <p className="more">+ {product.fitments.length - 1} fler fordonsanpassningar</p>}
    <div className="card-bottom"><strong>{price ? `${Number(price.amount).toLocaleString('sv-SE')} kr` : 'Pris på förfrågan'}</strong><span>Visa detaljer →</span></div>
  </Link>
}

export function CataloguePage() {
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState(params.get('q') || '')
  useEffect(() => { const timeout = setTimeout(() => { const next = new URLSearchParams(params); if (query) next.set('q', query); else next.delete('q'); next.set('page', '1'); setParams(next, { replace: true }) }, 350); return () => clearTimeout(timeout) }, [query]) // eslint-disable-line react-hooks/exhaustive-deps
  const apiParams = new URLSearchParams(params); if (!apiParams.has('page_size')) apiParams.set('page_size', '24')
  const products = useQuery({ queryKey: ['products', apiParams.toString()], queryFn: () => getProducts(apiParams) })
  const filters = useQuery({ queryKey: ['filters'], queryFn: getFilters })
  const setFilter = (name: string, value: string) => { const next = new URLSearchParams(params); if (value) next.set(name, value); else next.delete(name); if (name !== 'page') next.set('page', '1'); setParams(next) }
  const page = Number(params.get('page') || 1)
  return <>
    <section className="hero"><p className="eyebrow">Hitta rätt del till rätt bil</p><h1>Sök bland våra bildelar</h1><p>Artikelnummer, bilmärke, modell eller produkttyp.</p><label className="search"><span>⌕</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Sök t.ex. Alfa Romeo 147 eller A-035" aria-label="Sök produkter" /></label></section>
    <section className="toolbar">
      <select value={params.get('manufacturer') || ''} onChange={e => setFilter('manufacturer', e.target.value)} aria-label="Tillverkare"><option value="">Alla tillverkare</option>{filters.data?.manufacturers.map(x => <option key={x} value={x}>{x}</option>)}</select>
      <select value={params.get('towbar_type') || ''} onChange={e => setFilter('towbar_type', e.target.value)} aria-label="Produkttyp"><option value="">Alla produkttyper</option>{filters.data?.towbar_types.map(x => <option key={x}>{x}</option>)}</select>
      <select value={params.get('vehicle_make') || ''} onChange={e => setFilter('vehicle_make', e.target.value)} aria-label="Bilmärke"><option value="">Alla bilmärken</option>{filters.data?.vehicle_makes.map(x => <option key={x}>{x}</option>)}</select>
      <select value={params.get('sort') || 'name'} onChange={e => setFilter('sort', e.target.value)} aria-label="Sortering"><option value="name">Namn</option><option value="manufacturer">Tillverkare</option><option value="article_number">Artikelnummer</option></select>
    </section>
    <div className="result-head"><p>{products.data ? `${products.data.total.toLocaleString('sv-SE')} produkter` : 'Laddar katalog…'}</p></div>
    {products.isError && <div className="state error">Katalogen kunde inte hämtas. Kontrollera att API:t är igång.</div>}
    {products.isLoading && <div className="grid">{Array.from({length: 8}, (_, i) => <div className="card skeleton" key={i} />)}</div>}
    {products.data?.items.length === 0 && <div className="state"><h2>Inga produkter hittades</h2><p>Prova ett annat sökord eller ta bort ett filter.</p></div>}
    <div className="grid">{products.data?.items.map(product => <ProductCard key={product.id} product={product} />)}</div>
    {products.data && products.data.pages > 1 && <nav className="pagination" aria-label="Sidnavigering"><button disabled={page <= 1} onClick={() => setFilter('page', String(page - 1))}>← Föregående</button><span>Sida {page} av {products.data.pages}</span><button disabled={page >= products.data.pages} onClick={() => setFilter('page', String(page + 1))}>Nästa →</button></nav>}
  </>
}

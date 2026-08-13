import { useMutation, useQuery } from '@tanstack/react-query'
import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createOrder, getProducts, getWorkshops } from '../api'
import type { Product } from '../types'

type SelectedProduct = { product: Product; quantity: number }

export function NewOrderPage() {
  const navigate = useNavigate()
  const [productSearch, setProductSearch] = useState('')
  const [vehicleLabel, setVehicleLabel] = useState('')
  const [postalCode, setPostalCode] = useState('')
  const [city, setCity] = useState('')
  const [selected, setSelected] = useState<SelectedProduct[]>([])
  const [workshopId, setWorkshopId] = useState('')
  const productParams = new URLSearchParams({ vehicle: vehicleLabel, page_size: '20' })
  if (productSearch.trim()) productParams.set('q', productSearch)
  const products = useQuery({ queryKey: ['product-picker', productParams.toString()], queryFn: () => getProducts(productParams), enabled: vehicleLabel.trim().length >= 2 })
  const postalPrefix = postalCode.replace(/\D/g, '').slice(0, 2)
  const workshopParams = new URLSearchParams({ page_size: '200' })
  if (postalPrefix.length === 2) workshopParams.set('postal_prefix', postalPrefix)
  else if (city.trim().length >= 2) workshopParams.set('city', city.trim())
  const hasLocation = postalPrefix.length === 2 || city.trim().length >= 2
  const workshops = useQuery({ queryKey: ['nearby-workshops-picker', workshopParams.toString()], queryFn: () => getWorkshops(workshopParams), enabled: hasLocation })
  const mutation = useMutation({ mutationFn: createOrder, onSuccess: (order) => navigate(`/orders/${order.id}`) })
  const addProduct = (product: Product) => { setSelected((items) => items.some((item) => item.product.id === product.id) ? items : [...items, { product, quantity: 1 }]); setProductSearch('') }
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    mutation.mutate({ customer: { name: String(form.get('name') || ''), email: String(form.get('email') || ''), phone: String(form.get('phone') || '') || undefined, delivery_address: String(form.get('address') || '') || undefined, postal_code: postalCode || undefined, city: city || undefined }, workshop_id: workshopId, items: selected.map((item) => ({ product_id: item.product.id, quantity: item.quantity })), registration_number: String(form.get('registration_number') || '') || undefined, vehicle_label: vehicleLabel || undefined, vehicle_year: String(form.get('vehicle_year') || '') || undefined, notes: String(form.get('notes') || '') || undefined, sales_person: String(form.get('sales_person') || '') || undefined })
  }
  return <section className="new-order-page">
    <Link className="back" to="/orders">← Till orderflödet</Link>
    <div className="form-heading"><p className="eyebrow">CRM · Ny offert</p><h1>Skapa offert</h1><p>Spara kundens förslag nu och bekräfta det som en order när kunden tackar ja.</p></div>
    <form onSubmit={submit}><div className="order-form-grid">
      <section className="form-section"><h2>1. Kund</h2><div className="fields"><label>Namn *<input required name="name" /></label><label>E-post *<input required type="email" name="email" /></label><label>Telefon<input name="phone" /></label><label>Adress<input name="address" /></label><label>Postnummer<input name="postal_code" value={postalCode} onChange={(event) => { setPostalCode(event.target.value); setWorkshopId('') }} /></label><label>Ort<input name="city" value={city} onChange={(event) => { setCity(event.target.value); setWorkshopId('') }} /></label></div></section>
      <section className="form-section"><h2>2. Fordon</h2><div className="fields"><label>Registreringsnummer<input name="registration_number" /></label><label>Årsmodell<input name="vehicle_year" /></label><label className="wide">Fordon / modell<input name="vehicle_label" value={vehicleLabel} onChange={(event) => setVehicleLabel(event.target.value)} placeholder="Exempel: Volvo V70" /></label></div></section>
      <section className="form-section wide-section"><h2>3. Produkter som passar *</h2>{vehicleLabel.trim().length < 2 ? <p className="selection-hint">Ange bilmodell ovan för att visa produkter med registrerad passform.</p> : <><label className="product-picker">Filtrera kompatibla produkter<input value={productSearch} onChange={(event) => setProductSearch(event.target.value)} placeholder="Artikelnummer eller produktnamn (valfritt)" /></label><div className="picker-results">{products.isLoading && <p>Söker passande produkter…</p>}{products.data?.items.map((product) => <button type="button" onClick={() => addProduct(product)} key={product.id}><strong>{product.article_number}</strong><span>{product.name || 'Namnlös produkt'} · {product.manufacturer.name}</span></button>)}{products.data?.items.length === 0 && <p>Inga produkter har en registrerad passform för modellen.</p>}</div></>}<div className="selected-products">{selected.map((item, index) => <div key={item.product.id}><div><strong>{item.product.article_number}</strong><span>{item.product.name}</span></div><label>Antal<input type="number" min="1" max="100" value={item.quantity} onChange={(event) => setSelected((items) => items.map((current, position) => position === index ? { ...current, quantity: Number(event.target.value) } : current))} /></label><button type="button" onClick={() => setSelected((items) => items.filter((current) => current.product.id !== item.product.id))}>Ta bort</button></div>)}{selected.length === 0 && <p>Inga produkter valda ännu.</p>}</div></section>
      <section className="form-section wide-section"><h2>4. Verkstad nära kunden *</h2>{!hasLocation ? <p className="selection-hint">Ange kundens postnummer eller ort för att visa närliggande aktiva verkstäder.</p> : <label>Verkstäder i {postalPrefix ? `postområde ${postalPrefix}` : city}<select required value={workshopId} onChange={(event) => setWorkshopId(event.target.value)}><option value="">Välj verkstad</option>{workshops.data?.items.map((workshop) => <option value={workshop.id} key={workshop.id}>{workshop.name} · {workshop.postal_code || ''} {workshop.city || ''}</option>)}</select>{workshops.data?.items.length === 0 && <span className="field-note">Ingen aktiv verkstad hittades i området.</span>}</label>}</section>
      <section className="form-section wide-section"><h2>5. Internt</h2><div className="fields"><label>Ansvarig<input name="sales_person" /></label><label className="wide">Anteckningar<textarea name="notes" rows={4} /></label></div></section>
    </div>{mutation.isError && <p className="form-error">Offerten kunde inte sparas. Kontrollera uppgifterna och försök igen.</p>}<div className="form-actions"><Link to="/orders">Avbryt</Link><button className="primary" disabled={mutation.isPending || selected.length === 0 || !workshopId}>{mutation.isPending ? 'Sparar…' : 'Spara & skicka offert'}</button></div></form>
  </section>
}

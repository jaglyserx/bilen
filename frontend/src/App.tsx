import { Link, Route, Routes } from 'react-router-dom'
import { CataloguePage } from './pages/CataloguePage'
import { ProductPage } from './pages/ProductPage'
import { OrderPage } from './pages/OrderPage'
import { OrdersPage } from './pages/OrdersPage'
import { WorkshopPage } from './pages/WorkshopPage'
import { WorkshopsPage } from './pages/WorkshopsPage'

export default function App() {
  return <><header><Link to="/" className="brand"><span className="mark">B&J</span><span>Bilen & Jag<small>Verksamhetssystem</small></span></Link><nav><Link to="/">Produkter</Link><Link to="/orders">Orderflöde</Link><Link to="/workshops">Verkstäder</Link></nav></header><main><Routes><Route path="/" element={<CataloguePage />} /><Route path="/products/:id" element={<ProductPage />} /><Route path="/orders" element={<OrdersPage />} /><Route path="/orders/:id" element={<OrderPage />} /><Route path="/workshops" element={<WorkshopsPage />} /><Route path="/workshops/:id" element={<WorkshopPage />} /></Routes></main><footer>Bilen & Jag · Produktkatalog, orderflöde och verkstäder</footer></>
}

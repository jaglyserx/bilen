import { Link, Route, Routes } from 'react-router-dom'
import { CataloguePage } from './pages/CataloguePage'
import { ProductPage } from './pages/ProductPage'
import { OrderPage } from './pages/OrderPage'
import { OrdersPage } from './pages/OrdersPage'

export default function App() {
  return <><header><Link to="/" className="brand"><span className="mark">B&J</span><span>Bilen & Jag<small>Verksamhetssystem</small></span></Link><nav><Link to="/">Produkter</Link><Link to="/orders">Orderflöde</Link></nav></header><main><Routes><Route path="/" element={<CataloguePage />} /><Route path="/products/:id" element={<ProductPage />} /><Route path="/orders" element={<OrdersPage />} /><Route path="/orders/:id" element={<OrderPage />} /></Routes></main><footer>Bilen & Jag · Produktkatalog och orderflöde</footer></>
}

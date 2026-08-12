import { Link, Route, Routes } from 'react-router-dom'
import { CataloguePage } from './pages/CataloguePage'
import { ProductPage } from './pages/ProductPage'

export default function App() {
  return <><header><Link to="/" className="brand"><span className="mark">B&J</span><span>Bilen & Jag<small>Produktkatalog</small></span></Link></header><main><Routes><Route path="/" element={<CataloguePage />} /><Route path="/products/:id" element={<ProductPage />} /></Routes></main><footer>Produktinformation för fordonsdelar · Kontakta oss för att bekräfta passform</footer></>
}

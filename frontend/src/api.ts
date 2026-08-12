import type { Filters, Product, ProductPage } from './types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`)
  if (!response.ok) throw new Error(response.status === 404 ? 'Produkten hittades inte' : 'Katalogen kunde inte hämtas')
  return response.json() as Promise<T>
}

export function getProducts(params: URLSearchParams) { return request<ProductPage>(`/products?${params}`) }
export function getProduct(id: string) { return request<Product>(`/products/${id}`) }
export function getFilters() { return request<Filters>('/filters') }

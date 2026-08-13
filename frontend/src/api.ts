import type { Filters, Order, OrderPage, OrderSummary, Product, ProductPage, Workshop, WorkshopPage } from './types'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`)
  if (!response.ok) throw new Error(response.status === 404 ? 'Posten hittades inte' : 'Informationen kunde inte hämtas')
  return response.json() as Promise<T>
}

export function getProducts(params: URLSearchParams) { return request<ProductPage>(`/products?${params}`) }
export function getProduct(id: string) { return request<Product>(`/products/${id}`) }
export function getFilters() { return request<Filters>('/filters') }
export function getOrders(params: URLSearchParams) { return request<OrderPage>(`/orders?${params}`) }
export function getOrder(id: string) { return request<Order>(`/orders/${id}`) }
export function getOrderSummary() { return request<OrderSummary>('/orders/summary') }
export function getWorkshops(params: URLSearchParams) { return request<WorkshopPage>(`/workshops?${params}`) }
export function getWorkshop(id: string) { return request<Workshop>(`/workshops/${id}`) }

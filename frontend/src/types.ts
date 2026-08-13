export type Price = { kind: string; amount: string; currency: string; vat_included: boolean }
export type Vehicle = { id: string; make: string | null; model: string | null; body_style: string | null; year_from: number | null; year_to: number | null; source_label: string }
export type Fitment = { id: string; fitment_notes: string; electrical_connection: string | null; camper_van_notes: string | null; vehicle: Vehicle }
export type Product = {
  id: string; article_number: string; name: string | null; towbar_type: string | null; status: string;
  ean: string | null; webshop_url: string | null; manufacturer: { id: string; name: string };
  prices: Price[]; fitments: Fitment[]; description?: string | null; max_towing_weight_kg?: string | null;
  max_ball_weight_kg?: string | null; weight_kg?: string | null; cutout_required?: boolean | null;
  lockable?: boolean | null; size?: string | null; installation_minutes?: number | null;
  inventory?: { location: string; quantity: number | null; availability: string | null }[];
  links?: { kind: string; url: string }[]; categories?: { id: string; name: string; slug: string }[];
}
export type ProductPage = { items: Product[]; page: number; page_size: number; total: number; pages: number }
export type Filters = { manufacturers: string[]; towbar_types: string[]; vehicle_makes: string[]; statuses: string[] }
export type OrderItem = { id: string; kind: string; source_sku: string | null; description: string; quantity: number; link_status: string; product: { id: string; article_number: string; name: string | null } | null }
export type Order = { id: string; external_id: string; ordered_at: string | null; status: string; workflow_status: string | null; sales_person: string | null; sales_channel: string | null; total_amount: string | null; currency: string; vehicle_label: string | null; registration_number: string | null; customer: { id: string; name: string; email: string | null; phone: string | null; city: string | null }; workshop: { id: string; name: string; city: string | null } | null; items: OrderItem[] }
export type OrderCreate = { customer: { name: string; email?: string; phone?: string; delivery_address?: string; postal_code?: string; city?: string }; workshop_id: string; items: { product_id: string; quantity: number }[]; registration_number?: string; vehicle_label?: string; vehicle_year?: string; notes?: string; sales_person?: string }
export type OrderPage = { items: Order[]; page: number; page_size: number; total: number; pages: number }
export type OrderSummary = { total: number; by_status: Record<string, number>; unmatched_items: number }
export type Workshop = { id: string; name: string; contact_person: string | null; address: string | null; postal_code: string | null; city: string | null; phone: string | null; email: string | null; booking_instructions: string | null; agreement_terms: string | null; workshop_info: string | null; discount_terms: string | null; internal_owner: string | null; written_agreement: boolean | null; terms_updated_at: string | null; current_info: string | null; is_active: boolean; restrictions: string | null; supports_motorhomes: boolean | null; loan_car_available: boolean | null }
export type WorkshopPage = { items: Workshop[]; page: number; page_size: number; total: number; pages: number }

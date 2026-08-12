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

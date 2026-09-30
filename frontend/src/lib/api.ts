export type Pharmacy = { id: string; name: string; address?: string | null };
export type Category = { id: string; name: string };
export type Supplier = { id: string; name: string; contact_info?: string | null };
export type Medicine = {
  id: string;
  name: string;
  generic_name: string;
  manufacturer?: string | null;
  strength?: string | null;
  category_id: string;
  min_stock_level: number;
};
export type PharmacyLocation = {
  id: string;
  name: string;
  type: 'Block' | 'Rack' | 'Shelf' | 'Bin';
  level: number;
  parent_id?: string | null;
  pharmacy_id: string;
};
export type SearchLocation = { location_id: string; location_path: string[]; quantity: number };
export type SearchBatch = {
  batch_id: string;
  batch_number: string;
  expiry_date: string;
  expiry_status: 'EXPIRED' | 'EXPIRING_SOON' | 'SAFE';
  quantity: number;
  locations: SearchLocation[];
};
export type SearchMedicine = {
  medicine_id: string;
  name: string;
  generic_name: string;
  manufacturer?: string | null;
  min_stock_level: number;
  total_quantity: number;
  batches: SearchBatch[];
};
export type SearchResponse = { results: SearchMedicine[]; total: number; limit: number; offset: number };
export type Dashboard = {
  medicine_count: number;
  total_stock: number;
  low_stock_count: number;
  expiring_soon_quantity: number;
  expired_quantity: number;
  sales_today: number;
  low_stock_items: { medicine_id: string; name: string; quantity: number; minimum: number }[];
  expiry_alerts: { batch_id: string; medicine_name: string; batch_number: string; expiry_date: string; quantity: number; status: string }[];
  recent_movements: { id: string; medicine_name: string; batch_number: string; location_name: string; change_qty: number; reason: string; created_at: string }[];
};
export type StockRow = {
  medicine_id: string;
  medicine_name: string;
  batch_id: string;
  batch_number: string;
  expiry_date: string;
  expired: boolean;
  location_id: string;
  location_name: string;
  quantity: number;
};
export type Batch = {
  id: string;
  medicine_id: string;
  supplier_id: string;
  batch_number: string;
  manufacturing_date?: string | null;
  expiry_date: string;
  cost_price: number;
  selling_price: number;
};
export type PurchaseItemInput = {
  medicine_id: string;
  batch_number: string;
  manufacturing_date?: string;
  expiry_date: string;
  cost_price: number;
  selling_price: number;
  quantity: number;
  location_id: string;
};
export type PurchaseRecord = {
  id: string;
  supplier_id: string;
  purchase_date: string;
  invoice_number?: string | null;
  total_amount: number;
  items: { batch_id: string; batch_number: string; quantity: number; location_id: string }[];
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (response.status === 204) return undefined as T;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === 'string' ? payload.detail : `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return payload as T;
}

const query = (params: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => value !== undefined && search.set(key, String(value)));
  return `?${search.toString()}`;
};
const post = <T>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) });

export const api = {
  pharmacies: () => request<Pharmacy[]>('/pharmacies/'),
  createPharmacy: (body: { name: string; address?: string }) => post<Pharmacy>('/pharmacies/', body),
  dashboard: (id: string) => request<Dashboard>(`/dashboard/${id}`),
  categories: (id: string) => request<Category[]>(`/categories/${query({ pharmacy_id: id })}`),
  createCategory: (body: { pharmacy_id: string; name: string }) => post<Category>('/categories/', body),
  suppliers: (id: string) => request<Supplier[]>(`/suppliers/${query({ pharmacy_id: id })}`),
  createSupplier: (body: { pharmacy_id: string; name: string; contact_info?: string }) => post<Supplier>('/suppliers/', body),
  medicines: (id: string) => request<Medicine[]>(`/medicines/${query({ pharmacy_id: id, limit: 100 })}`),
  createMedicine: (body: object) => post<Medicine>('/medicines/', body),
  locations: (id: string) => request<PharmacyLocation[]>(`/locations/${query({ pharmacy_id: id, limit: 100 })}`),
  createLocation: (body: object) => post<PharmacyLocation>('/locations/', body),
  search: (id: string, q: string, offset = 0) => request<SearchResponse>(`/medicines/search${query({ pharmacy_id: id, q, limit: 20, offset })}`),
  stock: (id: string) => request<StockRow[]>(`/stock${query({ pharmacy_id: id, limit: 100 })}`),
  purchases: (id: string) => request<PurchaseRecord[]>(`/purchases${query({ pharmacy_id: id, limit: 100 })}`),
  receivePurchase: (body: object) => post<PurchaseRecord>('/purchases', body),
  transferStock: (body: object) => post<unknown>('/stock/transfers', body),
  createSale: (body: object) => post<unknown>('/sales/', body),
  transactions: (id: string) => request<{ id: string; batch_id: string; location_id: string; medicine_name: string; batch_number: string; location_name: string; reason: string; change_qty: number; created_at: string }[]>(`/transactions${query({ pharmacy_id: id, limit: 100 })}`),
};

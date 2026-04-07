const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CardSale {
  id: string;
  transaction_date: string;
  card_number: string;
  approval_number: string;
  approval_amount: number;
  vat_amount: number;
  tip_amount: number;
  acquirer: string;
  issuer: string;
  transaction_type: string;
  status: string;
  installment_months: string;
  is_check_card: boolean;
  simple_pay: string;
  deposit_date: string;
  deposit_amount: number;
  fee: number;
  store_name: string;
  terminal_id: string;
  created_at: string;
}

export interface SalesSummary {
  acquirer: string;
  total_amount: number;
  count: number;
}

export interface ScrapeResponse {
  status: string;
  total_count: number;
  new_count: number;
  message: string;
}

export interface SalesResponse {
  data: CardSale[];
  total_count: number;
}

export async function fetchSales(params: {
  start_date?: string;
  end_date?: string;
  acquirer?: string;
  page?: number;
  page_size?: number;
}): Promise<SalesResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) searchParams.set(key, String(value));
  });

  const res = await fetch(`${API_BASE}/api/sales?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch sales");
  return res.json();
}

export async function fetchSummary(params: {
  start_date?: string;
  end_date?: string;
}): Promise<SalesSummary[]> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) searchParams.set(key, String(value));
  });

  const res = await fetch(`${API_BASE}/api/sales/summary?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function triggerScrape(
  start_date: string,
  end_date: string
): Promise<ScrapeResponse> {
  const res = await fetch(`${API_BASE}/api/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start_date, end_date }),
  });
  if (!res.ok) throw new Error("Failed to trigger scrape");
  return res.json();
}

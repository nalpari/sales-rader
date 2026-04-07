"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchSales, CardSale } from "@/lib/api";
import SalesTable from "@/components/SalesTable";
import DateRangeFilter from "@/components/DateRangeFilter";

export default function SalesPage() {
  const today = new Date().toISOString().slice(0, 10);
  const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().slice(0, 10);

  const [startDate, setStartDate] = useState(weekAgo);
  const [endDate, setEndDate] = useState(today);
  const [sales, setSales] = useState<CardSale[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  const loadSales = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchSales({ start_date: startDate, end_date: endDate, page, page_size: pageSize });
      setSales(result.data);
      setTotalCount(result.total_count);
    } catch {
      console.error("Failed to fetch sales");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, page]);

  useEffect(() => { loadSales(); }, [loadSales]);

  const handleSearch = () => { setPage(1); loadSales(); };
  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-10 border-b border-border bg-surface-card/80 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="group flex items-center justify-center w-7 h-7 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer">
              <svg className="w-4 h-4 text-slate-light group-hover:text-navy transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </Link>
            <h1 className="text-base font-semibold text-navy">매출 상세</h1>
          </div>
          <DateRangeFilter
            startDate={startDate} endDate={endDate}
            onStartDateChange={setStartDate} onEndDateChange={setEndDate}
            onSearch={handleSearch}
          />
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">
        <div className="animate-in">
          {loading ? (
            <div className="space-y-1.5">
              {[...Array(10)].map((_, i) => (<div key={i} className="h-11 rounded-lg shimmer" />))}
            </div>
          ) : (
            <SalesTable sales={sales} page={page} totalPages={totalPages} totalCount={totalCount} onPageChange={setPage} />
          )}
        </div>
      </main>
    </div>
  );
}

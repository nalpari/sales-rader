"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchSummary, SalesSummary } from "@/lib/api";
import SalesSummaryCard from "@/components/SalesSummaryCard";
import ScrapeButton from "@/components/ScrapeButton";
import DateRangeFilter from "@/components/DateRangeFilter";

export default function Home() {
  const today = new Date().toISOString().slice(0, 10);
  const monthAgo = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);

  const [startDate, setStartDate] = useState(monthAgo);
  const [endDate, setEndDate] = useState(today);
  const [summaries, setSummaries] = useState<SalesSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSummary = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSummary({ start_date: startDate, end_date: endDate });
      setSummaries(data);
    } catch {
      console.error("Failed to fetch summary");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  useEffect(() => { loadSummary(); }, [loadSummary]);

  return (
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-border bg-surface-card/80 backdrop-blur-md">
        <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue to-blue-light flex items-center justify-center shadow-sm">
              <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <span className="font-display text-lg text-navy">Sales Rader</span>
          </div>
          <Link
            href="/sales"
            className="group flex items-center gap-1 text-sm text-slate-light hover:text-blue transition-colors cursor-pointer"
          >
            상세 내역
            <svg className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-6 space-y-6">
        {/* Scrape */}
        <section className="animate-in" style={{ animationDelay: "0.05s" }}>
          <ScrapeButton onComplete={loadSummary} />
        </section>

        {/* Filter + Summary */}
        <section className="animate-in" style={{ animationDelay: "0.12s" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-navy">매출 현황</h2>
            <DateRangeFilter
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
              onSearch={loadSummary}
            />
          </div>
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[...Array(4)].map((_, i) => (<div key={i} className="h-24 rounded-xl shimmer" />))}
            </div>
          ) : (
            <SalesSummaryCard summaries={summaries} />
          )}
        </section>
      </main>
    </div>
  );
}

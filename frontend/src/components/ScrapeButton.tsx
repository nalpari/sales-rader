"use client";

import { useState } from "react";
import { triggerScrape } from "@/lib/api";

interface Props {
  onComplete: () => void;
}

export default function ScrapeButton({ onComplete }: Props) {
  const [startDate, setStartDate] = useState(new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleScrape = async () => {
    setLoading(true);
    setMessage("");
    try {
      const result = await triggerScrape(startDate, endDate);
      setMessage(result.message);
      onComplete();
    } catch {
      setMessage("스크래핑 실패. 다시 시도해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-border bg-surface-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-5 h-5 rounded-md bg-orange/10 flex items-center justify-center">
          <svg className="w-3 h-3 text-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-navy">데이터 수집</h3>
      </div>

      <div className="flex flex-wrap items-end gap-2.5">
        <div>
          <label className="block text-[11px] font-medium text-muted mb-1 uppercase tracking-wider">시작일</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
            className="h-9 rounded-lg border border-border bg-surface px-3 text-sm text-navy focus:outline-none focus:ring-2 focus:ring-blue/20 focus:border-blue/40 transition-all cursor-pointer" />
        </div>
        <div>
          <label className="block text-[11px] font-medium text-muted mb-1 uppercase tracking-wider">종료일</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
            className="h-9 rounded-lg border border-border bg-surface px-3 text-sm text-navy focus:outline-none focus:ring-2 focus:ring-blue/20 focus:border-blue/40 transition-all cursor-pointer" />
        </div>
        <button onClick={handleScrape} disabled={loading}
          className={`h-9 rounded-lg px-4 text-sm font-semibold text-white transition-all duration-200 cursor-pointer ${
            loading ? "bg-muted cursor-wait" : "bg-gradient-to-r from-blue to-blue-light hover:shadow-lg hover:shadow-blue/20 active:scale-[0.97]"
          }`}>
          {loading ? (
            <span className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="32" strokeLinecap="round" />
              </svg>
              수집 중
            </span>
          ) : "수집 실행"}
        </button>
      </div>

      {message && (
        <div className="mt-3 flex items-center gap-1.5 rounded-lg bg-success-bg border border-success-border px-3 py-2">
          <svg className="w-3.5 h-3.5 text-success flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs font-medium text-success">{message}</p>
        </div>
      )}
    </div>
  );
}

"use client";

import { SalesSummary } from "@/lib/api";

interface Props {
  summaries: SalesSummary[];
}

export default function SalesSummaryCard({ summaries }: Props) {
  const total = summaries.reduce((sum, s) => sum + s.total_amount, 0);
  const totalCount = summaries.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="space-y-4">
      {/* Hero total */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy to-navy-light p-6 text-white">
        <div className="relative z-10">
          <p className="text-xs font-medium text-blue-pale/70 tracking-widest uppercase mb-1">Total Revenue</p>
          <p className="font-display text-4xl tracking-tight">
            {total.toLocaleString()}
            <span className="text-lg text-white/30 ml-1">원</span>
          </p>
          <p className="text-sm text-white/40 mt-1 tabular-nums">{totalCount.toLocaleString()}건</p>
        </div>
        <div className="absolute -right-6 -top-6 w-36 h-36 rounded-full bg-blue/15 blur-xl" />
        <div className="absolute right-16 -bottom-10 w-28 h-28 rounded-full bg-blue-light/10 blur-lg" />
      </div>

      {/* Acquirer grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
        {summaries.map((s, i) => {
          const pct = total > 0 ? ((s.total_amount / total) * 100).toFixed(1) : "0";
          return (
            <div
              key={s.acquirer}
              className="group rounded-xl border border-border bg-surface-card p-4 hover:shadow-md hover:border-blue/20 transition-all duration-200 cursor-default animate-in"
              style={{ animationDelay: `${0.15 + i * 0.04}s` }}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-navy">{s.acquirer}</p>
                <span className="text-[10px] font-medium text-muted bg-surface-hover rounded-full px-1.5 py-0.5 tabular-nums">
                  {pct}%
                </span>
              </div>
              <p className="text-lg font-bold text-navy tabular-nums">
                {s.total_amount.toLocaleString()}
                <span className="text-xs text-muted font-normal ml-0.5">원</span>
              </p>
              <p className="text-xs text-muted mt-0.5 tabular-nums">{s.count}건</p>
              <div className="mt-3 h-1 rounded-full bg-border-light overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue/40 group-hover:bg-blue transition-all duration-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

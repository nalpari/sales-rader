"use client";

import { useState } from "react";
import { CardSale } from "@/lib/api";

interface Props {
  sales: CardSale[];
  page: number;
  totalPages: number;
  totalCount: number;
  onPageChange: (page: number) => void;
}

function PageNumbers({ page, totalPages, onPageChange }: { page: number; totalPages: number; onPageChange: (p: number) => void }) {
  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }
  return (
    <>
      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`dot-${i}`} className="px-1 text-xs text-muted select-none">...</span>
        ) : (
          <button key={p} onClick={() => onPageChange(p)}
            className={`min-w-[30px] h-8 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer ${
              p === page ? "bg-blue text-white shadow-sm" : "text-slate-mid hover:bg-surface-hover"
            }`}>
            {p}
          </button>
        )
      )}
    </>
  );
}

function PageJumpInput({ totalPages, onPageChange }: { totalPages: number; onPageChange: (p: number) => void }) {
  const [value, setValue] = useState("");
  const handleSubmit = () => {
    const num = parseInt(value, 10);
    if (num >= 1 && num <= totalPages) { onPageChange(num); setValue(""); }
  };
  return (
    <div className="flex items-center gap-1 ml-2 pl-2 border-l border-border">
      <input type="number" min={1} max={totalPages} value={value}
        onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        placeholder="p."
        className="w-11 h-8 rounded-lg border border-border bg-surface px-2 text-xs text-center text-navy placeholder:text-muted/40 focus:outline-none focus:ring-2 focus:ring-blue/20 focus:border-blue/40 transition-all" />
      <button onClick={handleSubmit}
        className="h-8 rounded-lg bg-navy px-2.5 text-[11px] font-semibold text-white hover:bg-navy-light transition-colors duration-150 active:scale-[0.97] cursor-pointer">
        이동
      </button>
    </div>
  );
}

export default function SalesTable({ sales, page, totalPages, totalCount, onPageChange }: Props) {
  return (
    <div>
      <div className="mb-2.5 flex items-center justify-between">
        <p className="text-xs text-muted">총 <span className="font-semibold text-navy tabular-nums">{totalCount.toLocaleString()}</span>건</p>
        <p className="text-xs text-muted tabular-nums">{page} / {totalPages} 페이지</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border bg-surface-card shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-surface">
              {["거래일시","카드번호","매입사","금액","승인번호","구분","할부","간편결제"].map((h, i) => (
                <th key={h} className={`px-4 py-2.5 text-[11px] font-semibold text-muted tracking-wider uppercase ${i === 3 ? "text-right" : i === 5 ? "text-center" : "text-left"}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sales.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-14 text-center">
                  <svg className="w-8 h-8 text-border mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <p className="text-sm text-muted">데이터가 없습니다</p>
                </td>
              </tr>
            ) : (
              sales.map((sale, i) => (
                <tr key={sale.id}
                  className="border-b border-border-light last:border-0 hover:bg-blue-ghost/50 transition-colors duration-100 animate-in"
                  style={{ animationDelay: `${i * 0.015}s` }}>
                  <td className="px-4 py-2.5 whitespace-nowrap text-navy tabular-nums text-xs">
                    {new Date(sale.transaction_date).toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-light tracking-wide">{sale.card_number}</td>
                  <td className="px-4 py-2.5 text-xs font-medium text-navy">{sale.acquirer}</td>
                  <td className="px-4 py-2.5 text-right whitespace-nowrap font-semibold text-navy tabular-nums text-xs">
                    {sale.approval_amount.toLocaleString()}<span className="text-muted ml-0.5">원</span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-light tracking-wide">{sale.approval_number}</td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold leading-tight ${
                      sale.transaction_type === "취소"
                        ? "bg-danger-bg text-danger border border-danger-border"
                        : "bg-success-bg text-success border border-success-border"
                    }`}>
                      {sale.transaction_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-slate-light">
                    {sale.installment_months === "00" ? "일시불" : `${sale.installment_months}개월`}
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted">{sale.simple_pay || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-0.5">
          <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-mid hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
          </button>
          <PageNumbers page={page} totalPages={totalPages} onPageChange={onPageChange} />
          <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-mid hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
          </button>
          <PageJumpInput totalPages={totalPages} onPageChange={onPageChange} />
        </div>
      )}
    </div>
  );
}

"use client";

interface Props {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onSearch: () => void;
}

export default function DateRangeFilter({ startDate, endDate, onStartDateChange, onEndDateChange, onSearch }: Props) {
  return (
    <div className="flex items-center gap-1.5">
      <input type="date" value={startDate} onChange={(e) => onStartDateChange(e.target.value)}
        className="h-8 rounded-lg border border-border bg-surface px-2 text-xs text-navy focus:outline-none focus:ring-2 focus:ring-blue/20 focus:border-blue/40 transition-all cursor-pointer" />
      <span className="text-muted text-xs">—</span>
      <input type="date" value={endDate} onChange={(e) => onEndDateChange(e.target.value)}
        className="h-8 rounded-lg border border-border bg-surface px-2 text-xs text-navy focus:outline-none focus:ring-2 focus:ring-blue/20 focus:border-blue/40 transition-all cursor-pointer" />
      <button onClick={onSearch}
        className="h-8 rounded-lg bg-blue px-3 text-xs font-semibold text-white hover:bg-blue-light transition-colors duration-150 active:scale-[0.97] cursor-pointer">
        조회
      </button>
    </div>
  );
}

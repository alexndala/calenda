"use client";
import { useCalendaStore } from "@/lib/store";
import { useFundAnalysis } from "@/lib/api";
import { FundSearch } from "@/components/FundSearch";
import type { FundLookThroughRow } from "@/lib/types";

function fmtDate(s: string | null): string {
  if (!s) return "—";
  return s; // already "YYYY-MM-DD"
}

function daysLabel(days: number | null): string {
  if (days === null) return "—";
  if (days === 0) return "Today";
  if (days === 1) return "Tomorrow";
  return `${days}d`;
}

function daysClass(days: number | null): string {
  if (days === null) return "text-slate-400";
  if (days <= 7) return "text-red-600 font-semibold";
  if (days <= 21) return "text-amber-600 font-medium";
  return "text-slate-600";
}

function LookThroughTable({ rows }: { rows: FundLookThroughRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-slate-400 py-6 text-center">
        No earnings events in the next 90 days for your look-through holdings.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-slate-100">
            <th className="text-left py-2 px-3 text-slate-500 font-medium">Ticker</th>
            <th className="text-left py-2 px-3 text-slate-500 font-medium">Company</th>
            <th className="text-right py-2 px-3 text-slate-500 font-medium">Eff. Weight</th>
            <th className="text-right py-2 px-3 text-slate-500 font-medium">Days</th>
            <th className="text-left py-2 px-3 text-slate-500 font-medium">Next Earnings</th>
            <th className="text-left py-2 px-3 text-slate-500 font-medium">Fund(s)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.ticker} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
              <td className="py-2 px-3 font-medium text-slate-900">{row.ticker}</td>
              <td className="py-2 px-3 text-slate-600 max-w-[140px] truncate">{row.company_name}</td>
              <td className="py-2 px-3 text-right tabular-nums text-slate-700">
                {row.effective_weight_pct.toFixed(2)}%
              </td>
              <td className={`py-2 px-3 text-right tabular-nums ${daysClass(row.days_to_earnings)}`}>
                {daysLabel(row.days_to_earnings)}
              </td>
              <td className="py-2 px-3 text-slate-500 tabular-nums">
                {fmtDate(row.next_earnings_date)}
              </td>
              <td className="py-2 px-3 text-slate-400 max-w-[120px] truncate" title={row.fund_source}>
                {row.fund_source}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FundsView() {
  const { fundPositions } = useCalendaStore();

  const { data: rows = [], isLoading, isError, error } = useFundAnalysis(fundPositions);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-1">
          Fund Look-Through
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Add SA unit trusts and your allocation to see look-through earnings exposure,
          ranked by effective weight.
        </p>
        <FundSearch />
      </div>

      {fundPositions.length === 0 && (
        <div className="text-center py-10 text-slate-400 text-sm">
          Add SA unit trusts above to see look-through earnings exposure.
        </div>
      )}

      {fundPositions.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            Look-Through Earnings Exposure
            <span className="ml-2 text-xs font-normal text-slate-400">(next 90 days)</span>
          </h3>
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            {isLoading && (
              <div className="animate-pulse space-y-2 p-4">
                {[0, 1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-8 bg-slate-100 rounded" />
                ))}
              </div>
            )}
            {isError && (
              <div className="p-4 text-sm text-red-600">
                Failed to load look-through data: {(error as Error)?.message ?? "Unknown error"}
              </div>
            )}
            {!isLoading && !isError && <LookThroughTable rows={rows} />}
          </div>
        </section>
      )}
    </div>
  );
}

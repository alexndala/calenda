"use client";
import type { PortfolioRiskRow } from "@/lib/types";

interface Props {
  rows: PortfolioRiskRow[];
  onTickerClick: (ticker: string) => void;
}

function fmtDollars(n: number | null, decimals = 0): string {
  if (n == null) return "—";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(decimals)}`;
}

function fmtPct(n: number | null): string {
  if (n == null) return "—";
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

function swingColor(swing: number | null, marketValue: number | null): string {
  if (swing == null || marketValue == null || marketValue === 0) return "text-slate-600";
  const pct = (swing / marketValue) * 100;
  if (pct >= 5) return "text-red-600 font-semibold";
  if (pct >= 2) return "text-amber-600 font-medium";
  return "text-slate-600";
}

function pnlColor(pnl: number | null): string {
  if (pnl == null) return "text-slate-600";
  if (pnl > 0) return "text-green-600";
  if (pnl < 0) return "text-red-600";
  return "text-slate-600";
}

// --- Upcoming Exposure Table ---
export function UpcomingExposureTable({ rows, onTickerClick }: Props) {
  const upcoming = rows
    .filter((r) => r.days_to_earnings != null && r.days_to_earnings <= 30)
    .sort(
      (a, b) =>
        (b.expected_dollar_swing ?? 0) - (a.expected_dollar_swing ?? 0)
    );

  if (upcoming.length === 0) {
    return (
      <p className="text-sm text-slate-400 py-4 text-center">
        No earnings in the next 30 days for your positions.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Ticker</th>
            <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Shares</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mkt Val</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Earnings</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Med. Move</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Exp. Swing</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Beat%</th>
          </tr>
        </thead>
        <tbody>
          {upcoming.map((row) => (
            <tr
              key={row.ticker}
              className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
              onClick={() => onTickerClick(row.ticker)}
            >
              <td className="py-2 px-3 font-mono font-semibold text-slate-900">{row.ticker}</td>
              <td className="py-2 px-3 text-slate-700 max-w-[160px] truncate">{row.company_name}</td>
              <td className="py-2 px-3 text-right text-slate-700">{row.shares.toLocaleString()}</td>
              <td className="py-2 px-3 text-right text-slate-700">{fmtDollars(row.market_value)}</td>
              <td className="py-2 px-3 text-right text-slate-600">
                {row.next_earnings_date
                  ? `${row.next_earnings_date} (${row.days_to_earnings}d)`
                  : "—"}
              </td>
              <td className="py-2 px-3 text-right text-slate-600">
                {row.median_pct_move != null
                  ? `±${row.median_pct_move.toFixed(1)}%`
                  : "—"}
              </td>
              <td className={`py-2 px-3 text-right ${swingColor(row.expected_dollar_swing, row.market_value)}`}>
                {row.expected_dollar_swing != null
                  ? `±${fmtDollars(row.expected_dollar_swing)}`
                  : "—"}
              </td>
              <td className="py-2 px-3 text-right text-slate-600">
                {row.eps_beat_rate != null
                  ? `${(row.eps_beat_rate * 100).toFixed(0)}%`
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-slate-400 mt-2 px-3">
        Expected swing = max |median % move| (days -1, 0, +1) × market value.
        Click a row to open the research panel.
      </p>
    </div>
  );
}

// --- All Positions Table ---
export function AllPositionsTable({ rows }: { rows: PortfolioRiskRow[] }) {
  const sorted = [...rows].sort(
    (a, b) => (b.market_value ?? 0) - (a.market_value ?? 0)
  );

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Ticker</th>
            <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Shares</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Avg Cost</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Price</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Mkt Val</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">P&amp;L</th>
            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">P&amp;L%</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.ticker} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-2 px-3 font-mono font-semibold text-slate-900">{row.ticker}</td>
              <td className="py-2 px-3 text-slate-700 max-w-[160px] truncate">{row.company_name}</td>
              <td className="py-2 px-3 text-right text-slate-700">{row.shares.toLocaleString()}</td>
              <td className="py-2 px-3 text-right text-slate-600">
                {row.avg_cost > 0 ? `$${row.avg_cost.toFixed(2)}` : "—"}
              </td>
              <td className="py-2 px-3 text-right text-slate-700">
                {row.current_price != null ? `$${row.current_price.toFixed(2)}` : "—"}
              </td>
              <td className="py-2 px-3 text-right text-slate-700">{fmtDollars(row.market_value)}</td>
              <td className={`py-2 px-3 text-right ${pnlColor(row.unrealized_pnl)}`}>
                {fmtDollars(row.unrealized_pnl)}
              </td>
              <td className={`py-2 px-3 text-right ${pnlColor(row.unrealized_pnl_pct)}`}>
                {fmtPct(row.unrealized_pnl_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

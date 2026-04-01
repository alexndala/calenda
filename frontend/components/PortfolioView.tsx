"use client";
import { useCalendaStore } from "@/lib/store";
import { usePortfolioAnalysis } from "@/lib/api";
import { CsvUpload } from "@/components/CsvUpload";
import { UpcomingExposureTable, AllPositionsTable } from "@/components/PortfolioRiskTable";
import type { PortfolioRiskRow } from "@/lib/types";

function fmtDollars(n: number, decimals = 0): string {
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(1)}K`;
  return `${sign}$${abs.toFixed(decimals)}`;
}

function fmtPct(n: number): string {
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  valueClass?: string;
}

function StatCard({ label, value, sub, valueClass = "text-slate-900" }: StatCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-semibold tabular-nums ${valueClass}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function SummaryStats({ rows }: { rows: PortfolioRiskRow[] }) {
  const totalValue = rows.reduce((s, r) => s + (r.market_value ?? 0), 0);
  const totalPnl = rows.reduce((s, r) => s + (r.unrealized_pnl ?? 0), 0);
  const totalPnlPct = totalValue > 0 ? (totalPnl / (totalValue - totalPnl)) * 100 : 0;
  const totalSwing = rows.reduce((s, r) => s + (r.expected_dollar_swing ?? 0), 0);
  const upcomingCount = rows.filter(
    (r) => r.days_to_earnings != null && r.days_to_earnings <= 30
  ).length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard
        label="Portfolio Value"
        value={fmtDollars(totalValue)}
        sub={`${rows.length} positions`}
      />
      <StatCard
        label="Unrealized P&L"
        value={fmtDollars(totalPnl)}
        sub={fmtPct(totalPnlPct)}
        valueClass={totalPnl >= 0 ? "text-green-600" : "text-red-600"}
      />
      <StatCard
        label="Total Exp. Swing"
        value={totalSwing > 0 ? `±${fmtDollars(totalSwing)}` : "—"}
        sub="across all earnings events"
      />
      <StatCard
        label="Upcoming Earnings"
        value={String(upcomingCount)}
        sub="positions in next 30 days"
        valueClass={upcomingCount > 0 ? "text-amber-600" : "text-slate-900"}
      />
    </div>
  );
}

export function PortfolioView() {
  const { positions, setPositions, clearPositions, openEvent, currentDateRange } =
    useCalendaStore();

  const { data: rows = [], isLoading, isError, error } = usePortfolioAnalysis(positions);

  function handleTickerClick(ticker: string) {
    // Open the event detail panel by finding the nearest upcoming earnings event for this ticker.
    // We use the ticker as both id and ticker — the EventDetailPanel fetches by ticker.
    openEvent(ticker, ticker);
  }

  // --- Empty state: no positions loaded ---
  if (positions.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto">
          <h2 className="text-base font-semibold text-slate-900 mb-1">Portfolio Risk Dashboard</h2>
          <p className="text-sm text-slate-500 mb-6">
            Upload your broker CSV to see upcoming earnings exposure, expected dollar swings, and
            your full position summary.
          </p>
          <CsvUpload onImport={setPositions} />
        </div>
      </div>
    );
  }

  // --- Loading state ---
  if (isLoading) {
    return (
      <div className="flex-1 overflow-y-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="grid grid-cols-4 gap-3">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-100 rounded-lg h-20" />
            ))}
          </div>
          <div className="bg-slate-100 rounded-lg h-48" />
          <div className="bg-slate-100 rounded-lg h-64" />
        </div>
      </div>
    );
  }

  // --- Error state ---
  if (isError) {
    return (
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-xl mx-auto rounded-md bg-red-50 border border-red-200 p-4">
          <p className="text-sm font-medium text-red-700 mb-1">Failed to analyze portfolio</p>
          <p className="text-xs text-red-600">{(error as Error)?.message ?? "Unknown error"}</p>
          <button
            onClick={clearPositions}
            className="mt-3 text-xs text-red-600 underline hover:no-underline"
          >
            Clear positions and start over
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Portfolio Risk Dashboard</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {positions.length} positions loaded
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-600 cursor-pointer hover:text-slate-900 flex items-center gap-1.5">
            <span className="inline-block px-2 py-1 bg-slate-100 rounded text-xs hover:bg-slate-200 transition-colors">
              Replace CSV
            </span>
            <input
              type="file"
              accept=".csv,.txt"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => {
                  const text = (ev.target?.result as string) ?? "";
                  import("@/lib/csvParser").then(({ parseCsvPositions }) => {
                    try {
                      const result = parseCsvPositions(text);
                      if (result.positions.length > 0) setPositions(result.positions);
                    } catch {
                      // silently ignore — user can use the full CsvUpload flow
                    }
                  });
                };
                reader.readAsText(file);
                e.target.value = "";
              }}
            />
          </label>
          <button
            onClick={clearPositions}
            className="text-xs text-slate-400 hover:text-red-600 transition-colors px-2 py-1 rounded"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Summary stats */}
      <SummaryStats rows={rows} />

      {/* Upcoming earnings exposure */}
      <section>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">
          Upcoming Earnings Exposure
          <span className="ml-2 text-xs font-normal text-slate-400">(next 30 days)</span>
        </h3>
        <div className="bg-white border border-slate-200 rounded-lg">
          <UpcomingExposureTable rows={rows} onTickerClick={handleTickerClick} />
        </div>
      </section>

      {/* All positions */}
      <section className="pb-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">All Positions</h3>
        <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <AllPositionsTable rows={rows} />
        </div>
      </section>
    </div>
  );
}

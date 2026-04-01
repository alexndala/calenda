"use client";
import { useEventDetail } from "@/lib/api";
import { useCalendaStore } from "@/lib/store";
import type { BeatMissEntry, PriceReactionDay } from "@/lib/types";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useEffect } from "react";

const BEAT_COLOR = "#22c55e";
const MISS_COLOR = "#ef4444";
const NEUTRAL_COLOR = "#94a3b8";

function SectionSkeleton() {
  return (
    <div className="animate-pulse space-y-2">
      <div className="h-3 bg-slate-200 rounded w-1/3" />
      <div className="h-20 bg-slate-100 rounded" />
    </div>
  );
}

function BeatRate({ rate, label }: { rate: number | null; label: string }) {
  if (rate === null) return null;
  const pct = Math.round(rate * 100);
  const color = pct >= 75 ? BEAT_COLOR : pct >= 50 ? "#f59e0b" : MISS_COLOR;
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="font-semibold" style={{ color }}>
        {pct}%
      </span>
    </div>
  );
}

function BeatMissChart({ history }: { history: BeatMissEntry[] }) {
  const data = history.map((q) => ({
    quarter: q.quarter,
    surprise:
      q.eps_actual != null && q.eps_estimate != null
        ? ((q.eps_actual - q.eps_estimate) / Math.abs(q.eps_estimate || 1)) * 100
        : 0,
    beat: q.eps_beat,
  }));

  return (
    <ResponsiveContainer width="100%" height={80}>
      <BarChart data={data} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
        <XAxis dataKey="quarter" tick={{ fontSize: 9 }} />
        <YAxis tick={{ fontSize: 9 }} tickFormatter={(v) => `${v.toFixed(0)}%`} />
        <Tooltip
          formatter={(val: number) => [`${val.toFixed(1)}%`, "EPS Surprise"]}
          labelStyle={{ fontSize: 10 }}
          contentStyle={{ fontSize: 10 }}
        />
        <ReferenceLine y={0} stroke="#cbd5e1" />
        <Bar dataKey="surprise" radius={[2, 2, 0, 0]}>
          {data.map((entry, idx) => (
            <Cell
              key={idx}
              fill={entry.beat === true ? BEAT_COLOR : entry.beat === false ? MISS_COLOR : NEUTRAL_COLOR}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function PriceReactionChart({ days }: { days: PriceReactionDay[] }) {
  const data = days.map((d) => ({
    day: d.day === 0 ? "0 (E-day)" : `${d.day > 0 ? "+" : ""}${d.day}`,
    median: d.median_pct,
    p25: d.p25,
    p75: d.p75,
    band: d.p25 != null && d.p75 != null ? [d.p25, d.p75] : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={100}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="reactionBand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1e293b" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#1e293b" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="day" tick={{ fontSize: 9 }} />
        <YAxis tick={{ fontSize: 9 }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
        <ReferenceLine y={0} stroke="#cbd5e1" />
        <Tooltip
          formatter={(val: number) => [`${val?.toFixed(2) ?? "—"}%`]}
          labelStyle={{ fontSize: 10 }}
          contentStyle={{ fontSize: 10 }}
        />
        <Area
          type="monotone"
          dataKey="p75"
          stroke="none"
          fill="url(#reactionBand)"
          fillOpacity={1}
        />
        <Area
          type="monotone"
          dataKey="median"
          stroke="#1e293b"
          strokeWidth={2}
          fill="none"
          dot={{ r: 2, fill: "#1e293b" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function EpsTrendChart({ trend }: { trend: number[] }) {
  const data = trend.map((eps, i) => ({ q: `Q${i + 1}`, eps }));
  return (
    <ResponsiveContainer width="100%" height={60}>
      <BarChart data={data} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
        <XAxis dataKey="q" tick={{ fontSize: 9 }} />
        <YAxis tick={{ fontSize: 9 }} />
        <Tooltip
          formatter={(val: number) => [`$${val.toFixed(2)}`, "EPS"]}
          contentStyle={{ fontSize: 10 }}
        />
        <Bar dataKey="eps" fill="#1e293b" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function EventDetailPanel() {
  const { openEventTicker, closeEvent } = useCalendaStore();
  const { data: detail, isLoading, isError } = useEventDetail(openEventTicker);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") closeEvent();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closeEvent]);

  return (
    <>
      {/* Backdrop (mobile) */}
      <div
        className="fixed inset-0 bg-black/20 z-20 lg:hidden"
        onClick={closeEvent}
        aria-hidden="true"
      />

      {/* Panel */}
      <aside className="fixed right-0 top-0 h-full w-[380px] bg-white border-l border-slate-200 z-30 overflow-y-auto shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 sticky top-0 bg-white">
          <div>
            <h2 className="font-semibold text-slate-900">{openEventTicker}</h2>
            <p className="text-xs text-slate-500">Earnings Analytics</p>
          </div>
          <button
            onClick={closeEvent}
            className="text-slate-400 hover:text-slate-900 text-lg leading-none px-1"
            aria-label="Close panel"
          >
            ×
          </button>
        </div>

        <div className="p-4 space-y-6">
          {isLoading && (
            <>
              <SectionSkeleton />
              <SectionSkeleton />
              <SectionSkeleton />
            </>
          )}

          {isError && (
            <div className="rounded bg-red-50 border border-red-100 p-3 text-sm text-red-600">
              No earnings analytics available for {openEventTicker}.
            </div>
          )}

          {detail && (
            <>
              {/* Estimates */}
              <section>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Upcoming Estimates
                </h3>
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">EPS Estimate</span>
                    <span className="font-medium">
                      {detail.eps_estimate != null
                        ? `$${detail.eps_estimate.toFixed(2)}`
                        : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">Revenue Estimate</span>
                    <span className="font-medium">
                      {detail.revenue_estimate != null
                        ? `$${(detail.revenue_estimate / 1e9).toFixed(2)}B`
                        : "—"}
                    </span>
                  </div>
                </div>
              </section>

              {/* Beat/miss rates */}
              {detail.beat_miss_history.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Beat/Miss History (Last {detail.beat_miss_history.length}Q)
                  </h3>
                  {detail.insufficient_history && (
                    <p className="text-xs text-amber-600 mb-2">
                      Fewer than 4 quarters available — rates may not be representative.
                    </p>
                  )}
                  <div className="space-y-1 mb-3">
                    <BeatRate rate={detail.eps_beat_rate} label="EPS Beat Rate" />
                    <BeatRate rate={detail.rev_beat_rate} label="Revenue Beat Rate" />
                  </div>
                  <BeatMissChart history={detail.beat_miss_history} />
                  <p className="text-xs text-slate-400 mt-1">EPS surprise % per quarter (green=beat, red=miss)</p>
                </section>
              )}

              {detail.beat_miss_history.length === 0 && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Beat/Miss History
                  </h3>
                  <p className="text-xs text-slate-400">Insufficient history</p>
                </section>
              )}

              {/* Price reaction */}
              {detail.price_reaction_by_day.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Avg Price Reaction (±5 Days)
                  </h3>
                  <PriceReactionChart days={detail.price_reaction_by_day} />
                  <p className="text-xs text-slate-400 mt-1">
                    Median % move relative to earnings day (day 0), shaded band = p25–p75
                  </p>
                </section>
              )}

              {/* EPS trend */}
              {detail.eps_trend.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    EPS Trend (Last {detail.eps_trend.length}Q)
                  </h3>
                  <EpsTrendChart trend={detail.eps_trend} />
                </section>
              )}

              {/* Portfolio impact placeholder */}
              <section>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Portfolio Impact
                </h3>
                <div className="rounded bg-slate-50 border border-dashed border-slate-200 p-3 text-xs text-slate-400 text-center">
                  Coming in phase 2 — add your positions to see $ impact
                </div>
              </section>
            </>
          )}
        </div>
      </aside>
    </>
  );
}

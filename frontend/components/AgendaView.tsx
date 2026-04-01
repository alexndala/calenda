"use client";
import { useCalendarEvents } from "@/lib/api";
import { useCalendaStore } from "@/lib/store";
import type { CalendarEvent } from "@/lib/types";
import { useState } from "react";
import clsx from "clsx";

type SortKey = "date" | "ticker" | "type" | "market_cap";

function formatMarketCap(cap: number | null): string {
  if (cap === null) return "—";
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(0)}B`;
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(0)}M`;
  return `$${cap}`;
}

function formatDetail(e: CalendarEvent): string {
  if (e.type === "earnings") {
    const est = e.details.eps_estimate;
    return est != null ? `EPS est. $${Number(est).toFixed(2)}` : "—";
  }
  if (e.type === "dividend") {
    const amt = e.details.amount;
    return amt != null ? `$${Number(amt).toFixed(4)}/sh` : "—";
  }
  if (e.type === "split") {
    const ratio = e.details.ratio;
    return ratio != null ? `${Number(ratio).toFixed(0)}:1` : "—";
  }
  if (e.type === "ipo") {
    return (e.details.price_range as string) || "—";
  }
  return "—";
}

const TYPE_COLORS: Record<string, string> = {
  earnings: "bg-slate-900 text-white",
  dividend: "bg-slate-500 text-white",
  split: "bg-slate-200 text-slate-800",
  ipo: "bg-slate-100 text-slate-600 border border-dashed border-slate-400",
};

export function AgendaView() {
  const { selectedTypes, universe, customTickers, timingFilters, openEvent, currentDateRange, positions } =
    useCalendaStore();
  const ownedTickers = new Set(positions.map((p) => p.ticker));
  const { start, end } = currentDateRange;
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortAsc, setSortAsc] = useState(true);

  const { data: events = [], isLoading, isError, refetch } = useCalendarEvents({
    start,
    end,
    index: universe,
    customTickers,
    types: Array.from(selectedTypes),
  });

  const filtered = events.filter((e: CalendarEvent) => {
    if (e.type === "earnings" && e.timing) {
      return timingFilters.has(e.timing as "BMO" | "AMC" | "TNS");
    }
    return true;
  });

  const sorted = [...filtered].sort((a, b) => {
    let cmp = 0;
    if (sortKey === "date") cmp = a.date.localeCompare(b.date);
    else if (sortKey === "ticker") cmp = a.ticker.localeCompare(b.ticker);
    else if (sortKey === "type") cmp = a.type.localeCompare(b.type);
    else if (sortKey === "market_cap") {
      cmp = (a.market_cap ?? -1) - (b.market_cap ?? -1);
    }
    return sortAsc ? cmp : -cmp;
  });

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  function SortHeader({ label, key }: { label: string; key: SortKey }) {
    const active = sortKey === key;
    return (
      <th
        onClick={() => toggleSort(key)}
        className={clsx(
          "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none whitespace-nowrap",
          active ? "text-slate-900" : "text-slate-500 hover:text-slate-700"
        )}
      >
        {label} {active ? (sortAsc ? "↑" : "↓") : ""}
      </th>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-slate-500">Loading events...</span>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">Failed to load events</p>
          <button
            onClick={() => refetch()}
            className="px-3 py-1 text-sm bg-slate-900 text-white rounded hover:bg-slate-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (sorted.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-slate-400">
        No events match your filters this month
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-white border-b border-slate-200 z-10">
          <tr>
            <SortHeader label="Date" key="date" />
            <SortHeader label="Ticker" key="ticker" />
            <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Company
            </th>
            <SortHeader label="Type" key="type" />
            <SortHeader label="Mkt Cap" key="market_cap" />
            <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Detail
            </th>
            <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Timing
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e: CalendarEvent) => (
            <tr
              key={e.id}
              onClick={() => openEvent(e.id, e.ticker)}
              className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
            >
              <td className="px-3 py-2 text-slate-500 whitespace-nowrap">{e.date}</td>
              <td className="px-3 py-2 font-medium text-slate-900">
                {e.ticker}
                {ownedTickers.has(e.ticker) && (
                  <span className="ml-1 text-amber-500 text-xs" title="In your portfolio">★</span>
                )}
              </td>
              <td className="px-3 py-2 text-slate-600 truncate max-w-[200px]">{e.company_name}</td>
              <td className="px-3 py-2">
                <span className={clsx("text-xs px-1.5 py-0.5 rounded", TYPE_COLORS[e.type])}>
                  {e.type}
                </span>
              </td>
              <td className="px-3 py-2 text-slate-500 whitespace-nowrap">
                {formatMarketCap(e.market_cap)}
              </td>
              <td className="px-3 py-2 text-slate-500">{formatDetail(e)}</td>
              <td className="px-3 py-2 text-slate-400 text-xs">{e.timing ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

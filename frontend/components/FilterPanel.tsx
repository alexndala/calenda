"use client";
import { useCalendaStore } from "@/lib/store";
import type { EventType, IndexName, TimingFilter } from "@/lib/types";
import { TickerSearch } from "./TickerSearch";

const EVENT_TYPES: { value: EventType; label: string }[] = [
  { value: "earnings", label: "Earnings" },
  { value: "dividend", label: "Dividends" },
  { value: "split", label: "Splits" },
  { value: "ipo", label: "IPOs" },
];

const TIMING_OPTIONS: { value: TimingFilter; label: string }[] = [
  { value: "BMO", label: "Before Open" },
  { value: "AMC", label: "After Close" },
  { value: "TNS", label: "Time N/A" },
];

const INDEX_GROUPS: { label: string; indices: { value: IndexName; label: string }[] }[] = [
  {
    label: "US",
    indices: [
      { value: "sp500", label: "S&P 500" },
      { value: "nasdaq100", label: "NASDAQ 100" },
    ],
  },
  {
    label: "South Africa",
    indices: [
      { value: "jse_top40", label: "JSE Top 40" },
      { value: "jse_allshare", label: "JSE All Share" },
    ],
  },
  {
    label: "Asia",
    indices: [
      { value: "topix", label: "TOPIX Core 30" },
      { value: "ftse_china_a50", label: "FTSE China A50" },
    ],
  },
  {
    label: "Europe",
    indices: [
      { value: "ftse100", label: "FTSE 100" },
      { value: "eurostoxx50", label: "EURO STOXX 50" },
    ],
  },
  {
    label: "Other",
    indices: [{ value: "custom", label: "Custom" }],
  },
];

export function FilterPanel() {
  const {
    selectedTypes,
    toggleType,
    universe,
    setUniverse,
    timingFilters,
    toggleTiming,
  } = useCalendaStore();

  return (
    <div className="p-4 space-y-6">
      {/* Universe */}
      <section>
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Universe
        </h2>
        <div className="space-y-3">
          {INDEX_GROUPS.map((group) => (
            <div key={group.label}>
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1 px-1">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.indices.map((idx) => (
                  <button
                    key={idx.value}
                    onClick={() => setUniverse(idx.value)}
                    className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                      universe === idx.value
                        ? "bg-slate-900 text-white"
                        : "text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {idx.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
        {universe === "custom" && (
          <div className="mt-2">
            <TickerSearch />
          </div>
        )}
      </section>

      {/* Event types */}
      <section>
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Event Types
        </h2>
        <div className="space-y-1.5">
          {EVENT_TYPES.map(({ value, label }) => (
            <label key={value} className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={selectedTypes.has(value)}
                onChange={() => toggleType(value)}
                className="rounded border-slate-300 text-slate-900 focus:ring-slate-500"
              />
              <span className="text-sm text-slate-700 group-hover:text-slate-900">
                {label}
              </span>
            </label>
          ))}
        </div>
      </section>

      {/* Timing filter (earnings only) */}
      {selectedTypes.has("earnings") && (
        <section>
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Earnings Timing
          </h2>
          <div className="space-y-1.5">
            {TIMING_OPTIONS.map(({ value, label }) => (
              <label key={value} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={timingFilters.has(value)}
                  onChange={() => toggleTiming(value)}
                  className="rounded border-slate-300 text-slate-900 focus:ring-slate-500"
                />
                <span className="text-sm text-slate-700 group-hover:text-slate-900">
                  {label}
                </span>
              </label>
            ))}
          </div>
        </section>
      )}

      {/* Legend */}
      <section>
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Color Key
        </h2>
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm border-l-4 border-earnings bg-slate-50" />
            Earnings
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm border-l-4 border-dividend bg-slate-50" />
            Dividend
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm border-l-4 border-split bg-slate-50" />
            Split
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="w-3 h-3 rounded-sm border-l-[4px] border-dashed border-ipo bg-slate-50" />
            IPO
          </div>
        </div>
      </section>
    </div>
  );
}

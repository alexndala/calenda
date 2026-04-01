"use client";
import { useTickerSearch } from "@/lib/api";
import { useCalendaStore } from "@/lib/store";
import { useState } from "react";

export function TickerSearch() {
  const { customTickers, setCustomTickers } = useCalendaStore();
  const [input, setInput] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);

  const { data: suggestions = [], isLoading } = useTickerSearch(
    input.length >= 1 ? input : ""
  );

  function addTicker(ticker: string) {
    const upper = ticker.toUpperCase().trim();
    if (!upper || customTickers.includes(upper)) return;
    setCustomTickers([...customTickers, upper]);
    setInput("");
    setShowDropdown(false);
  }

  function removeTicker(ticker: string) {
    setCustomTickers(customTickers.filter((t) => t !== ticker));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && input.trim()) {
      addTicker(input.trim());
    }
    if (e.key === "Escape") {
      setShowDropdown(false);
    }
  }

  return (
    <div className="relative">
      {/* Tags */}
      {customTickers.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {customTickers.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-1 bg-slate-900 text-white text-xs rounded px-2 py-0.5"
            >
              {t}
              <button
                onClick={() => removeTicker(t)}
                className="hover:text-red-300 ml-0.5"
                aria-label={`Remove ${t}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input */}
      <input
        type="text"
        value={input}
        onChange={(e) => {
          setInput(e.target.value.toUpperCase());
          setShowDropdown(true);
        }}
        onKeyDown={handleKeyDown}
        onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
        placeholder="Add ticker (e.g. AAPL)"
        className="w-full px-2 py-1.5 text-sm border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-slate-400"
      />

      {/* Suggestions dropdown */}
      {showDropdown && input.length >= 1 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded shadow-lg max-h-48 overflow-y-auto">
          {isLoading && (
            <div className="px-3 py-2 text-xs text-slate-400">Searching...</div>
          )}
          {!isLoading && suggestions.length === 0 && (
            <div className="px-3 py-2 text-xs text-slate-400">No tickers found</div>
          )}
          {suggestions.map((s) => (
            <button
              key={s.ticker}
              onMouseDown={() => addTicker(s.ticker)}
              className="w-full text-left px-3 py-2 text-xs hover:bg-slate-50 flex items-center justify-between"
            >
              <span className="font-medium text-slate-900">{s.ticker}</span>
              <span className="text-slate-400 truncate ml-2 max-w-[120px]">{s.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

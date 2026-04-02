"use client";
import { useFundSearch } from "@/lib/api";
import { useCalendaStore } from "@/lib/store";
import { useState } from "react";
import type { FundPosition } from "@/lib/types";

export function FundSearch() {
  const { fundPositions, setFundPositions } = useCalendaStore();
  const [input, setInput] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [pendingFund, setPendingFund] = useState<{ code: string; name: string } | null>(null);
  const [allocationInput, setAllocationInput] = useState("");

  const { data: suggestions = [], isLoading } = useFundSearch(
    input.length >= 2 ? input : ""
  );

  function selectFund(code: string, name: string) {
    setPendingFund({ code, name });
    setInput(name);
    setShowDropdown(false);
    setAllocationInput("");
  }

  function addFund() {
    if (!pendingFund) return;
    const alloc = parseFloat(allocationInput);
    if (isNaN(alloc) || alloc <= 0 || alloc > 100) return;

    const existing = fundPositions.find((p) => p.fund_code === pendingFund.code);
    if (existing) {
      // Update allocation if already added
      setFundPositions(
        fundPositions.map((p) =>
          p.fund_code === pendingFund.code ? { ...p, allocation_pct: alloc } : p
        )
      );
    } else {
      setFundPositions([
        ...fundPositions,
        { fund_code: pendingFund.code, fund_name: pendingFund.name, allocation_pct: alloc },
      ]);
    }
    setInput("");
    setAllocationInput("");
    setPendingFund(null);
  }

  function removeFund(code: string) {
    setFundPositions(fundPositions.filter((p) => p.fund_code !== code));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setShowDropdown(false);
      setPendingFund(null);
      setInput("");
    }
  }

  function handleAllocationKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") addFund();
    if (e.key === "Escape") {
      setPendingFund(null);
      setInput("");
      setAllocationInput("");
    }
  }

  return (
    <div className="space-y-3">
      {/* Added fund chips */}
      {fundPositions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {fundPositions.map((pos) => (
            <span
              key={pos.fund_code}
              className="inline-flex items-center gap-1.5 bg-slate-900 text-white text-xs rounded px-2.5 py-1"
            >
              <span className="font-medium">{pos.fund_name}</span>
              <span className="text-slate-300">— {pos.allocation_pct}%</span>
              <button
                onClick={() => removeFund(pos.fund_code)}
                className="hover:text-red-300 ml-0.5 leading-none"
                aria-label={`Remove ${pos.fund_name}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input row */}
      <div className="flex gap-2 items-start">
        <div className="relative flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setPendingFund(null);
              setShowDropdown(true);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => input.length >= 2 && setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
            placeholder="Search SA fund (e.g. Allan Gray)"
            className="w-full px-2 py-1.5 text-sm border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-slate-400"
          />

          {showDropdown && input.length >= 2 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded shadow-lg max-h-48 overflow-y-auto">
              {isLoading && (
                <div className="px-3 py-2 text-xs text-slate-400">Searching...</div>
              )}
              {!isLoading && suggestions.length === 0 && (
                <div className="px-3 py-2 text-xs text-slate-400">No funds found</div>
              )}
              {suggestions.map((s) => (
                <button
                  key={s.code}
                  onMouseDown={() => selectFund(s.code, s.name)}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-slate-50 flex items-center justify-between"
                >
                  <span className="font-medium text-slate-900">{s.name}</span>
                  <span className="text-slate-400 ml-2 shrink-0">{s.code}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Allocation input — shown when a fund is selected */}
        {pendingFund && (
          <>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={allocationInput}
                onChange={(e) => setAllocationInput(e.target.value)}
                onKeyDown={handleAllocationKeyDown}
                placeholder="Alloc %"
                min={0}
                max={100}
                step={1}
                autoFocus
                className="w-24 px-2 py-1.5 text-sm border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
              <span className="text-xs text-slate-400">%</span>
            </div>
            <button
              onClick={addFund}
              disabled={!allocationInput || parseFloat(allocationInput) <= 0}
              className="px-3 py-1.5 text-xs font-medium bg-slate-900 text-white rounded hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Add
            </button>
          </>
        )}
      </div>
    </div>
  );
}

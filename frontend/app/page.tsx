"use client";
import { useCalendaStore } from "@/lib/store";
import { AgendaView } from "@/components/AgendaView";
import { CalendarView } from "@/components/CalendarView";
import { EventDetailPanel } from "@/components/EventDetailPanel";
import { FilterPanel } from "@/components/FilterPanel";
import { PortfolioView } from "@/components/PortfolioView";

export default function Home() {
  const { viewMode, setViewMode, universe, openEventId, positions } = useCalendaStore();

  // effectiveView is just viewMode — kept for readability
  const effectiveView = viewMode;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left sidebar */}
      <aside className="w-64 shrink-0 border-r border-slate-200 bg-white overflow-y-auto">
        <div className="p-4 border-b border-slate-200">
          <h1 className="text-lg font-semibold text-slate-900">Calenda</h1>
          <p className="text-xs text-slate-500 mt-0.5">Earnings Research Cockpit</p>
        </div>
        <FilterPanel />
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 bg-white">
          <div className="flex items-center gap-1 bg-slate-100 rounded-md p-0.5">
            <button
              onClick={() => setViewMode("calendar")}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                effectiveView === "calendar"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Calendar
            </button>
            <button
              onClick={() => setViewMode("agenda")}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                effectiveView === "agenda"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Agenda
            </button>
            <button
              onClick={() => setViewMode("portfolio")}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors flex items-center gap-1 ${
                effectiveView === "portfolio"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Portfolio
              {positions.length > 0 && (
                <span className="text-xs bg-amber-100 text-amber-700 px-1 rounded-full">
                  {positions.length}
                </span>
              )}
            </button>
          </div>
          {effectiveView !== "portfolio" && (
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 bg-earnings rounded-sm" /> Earnings
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 bg-dividend rounded-sm" /> Dividend
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 bg-split rounded-sm" /> Split
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 bg-ipo rounded-sm" /> IPO
              </span>
            </div>
          )}
        </div>

        {/* Main view */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {effectiveView === "calendar" && <CalendarView />}
          {effectiveView === "agenda" && <AgendaView />}
          {effectiveView === "portfolio" && <PortfolioView />}
        </div>
      </main>

      {/* Right panel — event detail */}
      {openEventId && <EventDetailPanel />}
    </div>
  );
}

import { create } from "zustand";
import type { CalendarEvent, EventType, FundPosition, IndexName, Position, TimingFilter, ViewMode } from "./types";

const POSITIONS_KEY = "calenda-positions";
const FUND_POSITIONS_KEY = "calenda-fund-positions";

function loadPositions(): Position[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(POSITIONS_KEY) || "[]");
  } catch {
    return [];
  }
}

function loadFundPositions(): FundPosition[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(FUND_POSITIONS_KEY) || "[]");
  } catch {
    return [];
  }
}

interface CalendaStore {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;

  positions: Position[];
  setPositions: (positions: Position[]) => void;
  clearPositions: () => void;

  fundPositions: FundPosition[];
  setFundPositions: (positions: FundPosition[]) => void;

  selectedTypes: Set<EventType>;
  toggleType: (type: EventType) => void;

  universe: IndexName;
  setUniverse: (universe: IndexName) => void;

  customTickers: string[];
  setCustomTickers: (tickers: string[]) => void;

  timingFilters: Set<TimingFilter>;
  toggleTiming: (timing: TimingFilter) => void;

  openEventId: string | null;
  openEventTicker: string | null;
  openEventData: CalendarEvent | null;
  openEvent: (id: string, ticker: string, event?: CalendarEvent) => void;
  closeEvent: () => void;

  currentDateRange: { start: Date; end: Date };
  setDateRange: (start: Date, end: Date) => void;
}

const today = new Date();
const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
const lastOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

export const useCalendaStore = create<CalendaStore>((set) => ({
  viewMode: "calendar",
  setViewMode: (mode) => set({ viewMode: mode }),

  positions: loadPositions(),
  setPositions: (positions) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(POSITIONS_KEY, JSON.stringify(positions));
    }
    set({ positions });
  },
  clearPositions: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(POSITIONS_KEY);
    }
    set({ positions: [] });
  },

  fundPositions: loadFundPositions(),
  setFundPositions: (positions) => {
    if (typeof window !== "undefined") {
      localStorage.setItem(FUND_POSITIONS_KEY, JSON.stringify(positions));
    }
    set({ fundPositions: positions });
  },

  // Default: Earnings + Dividends checked; Splits + IPOs unchecked
  selectedTypes: new Set<EventType>(["earnings", "dividend"]),
  toggleType: (type) =>
    set((s) => {
      const next = new Set(s.selectedTypes);
      next.has(type) ? next.delete(type) : next.add(type);
      return { selectedTypes: next };
    }),

  universe: "sp500",
  setUniverse: (universe) => set({ universe }),

  customTickers: [],
  setCustomTickers: (tickers) => set({ customTickers: tickers }),

  // All timings visible by default
  timingFilters: new Set<TimingFilter>(["BMO", "AMC", "TNS"]),
  toggleTiming: (timing) =>
    set((s) => {
      const next = new Set(s.timingFilters);
      next.has(timing) ? next.delete(timing) : next.add(timing);
      return { timingFilters: next };
    }),

  openEventId: null,
  openEventTicker: null,
  openEventData: null,
  openEvent: (id, ticker, event) => set({ openEventId: id, openEventTicker: ticker, openEventData: event ?? null }),
  closeEvent: () => set({ openEventId: null, openEventTicker: null, openEventData: null }),

  currentDateRange: { start: firstOfMonth, end: lastOfMonth },
  setDateRange: (start, end) => {
    set({ currentDateRange: { start, end }, openEventId: null, openEventTicker: null, openEventData: null });
  },
}));

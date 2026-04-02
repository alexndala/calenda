import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  CalendarEvent,
  EarningsDetail,
  FundInfo,
  FundLookThroughRow,
  FundPosition,
  IndexName,
  PortfolioRiskRow,
  Position,
  TickerSearchResult,
} from "./types";

const BASE = "/api";

function toISODate(d: Date): string {
  return d.toISOString().split("T")[0];
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// --- Hooks ---

export function useCalendarEvents(params: {
  start: Date;
  end: Date;
  index: IndexName;
  customTickers: string[];
  types: string[];
}) {
  const { start, end, index, customTickers, types } = params;
  const query = new URLSearchParams({
    start: toISODate(start),
    end: toISODate(end),
    index,
    types: types.join(","),
    ...(index === "custom" && customTickers.length > 0
      ? { tickers: customTickers.join(",") }
      : {}),
  });

  return useQuery<CalendarEvent[], Error>({
    queryKey: ["events", toISODate(start), toISODate(end), index, customTickers, types],
    queryFn: () => fetchJSON<CalendarEvent[]>(`${BASE}/events?${query}`),
    staleTime: 1000 * 60 * 5, // 5 min
    retry: 1,
  });
}

export function useEventDetail(ticker: string | null) {
  return useQuery<EarningsDetail, Error>({
    queryKey: ["eventDetail", ticker],
    queryFn: () => fetchJSON<EarningsDetail>(`${BASE}/events/${ticker}/detail`),
    enabled: !!ticker,
    staleTime: 1000 * 60 * 15, // 15 min
    retry: 0, // don't retry 404s
  });
}

export function useIndexTickers(index: IndexName) {
  return useQuery<string[], Error>({
    queryKey: ["indexTickers", index],
    queryFn: () => fetchJSON<string[]>(`${BASE}/indices/${index}`),
    enabled: index !== "custom",
    staleTime: 1000 * 60 * 60 * 24, // 24h
    retry: 1,
  });
}

export function usePortfolioAnalysis(positions: Position[]) {
  return useQuery<PortfolioRiskRow[], Error>({
    queryKey: [
      "portfolio",
      positions.map((p) => `${p.ticker}:${p.shares}`).join(","),
    ],
    queryFn: () =>
      postJSON<PortfolioRiskRow[]>(`${BASE}/portfolio/analyze`, { positions }),
    enabled: positions.length > 0,
    staleTime: 1000 * 60 * 5, // 5 min — matches backend cache TTL
    retry: 1,
  });
}

export function useTickerSearch(query: string) {
  return useQuery<TickerSearchResult[], Error>({
    queryKey: ["tickerSearch", query],
    queryFn: () =>
      fetchJSON<TickerSearchResult[]>(`${BASE}/tickers/search?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 1,
    staleTime: 1000 * 60 * 60, // 1h
    retry: 0,
  });
}

export function useFundSearch(query: string) {
  return useQuery<FundInfo[], Error>({
    queryKey: ["fundSearch", query],
    queryFn: () =>
      fetchJSON<FundInfo[]>(`${BASE}/funds/search?q=${encodeURIComponent(query)}`),
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 60, // 1h
    retry: 0,
  });
}

export function useFundAnalysis(positions: FundPosition[]) {
  return useQuery<FundLookThroughRow[], Error>({
    queryKey: ["fundAnalysis", positions.map((p) => `${p.fund_code}:${p.allocation_pct}`).join(",")],
    queryFn: () => postJSON<FundLookThroughRow[]>(`${BASE}/funds/analyze`, positions),
    enabled: positions.length > 0,
    staleTime: 1000 * 60 * 5, // 5 min
    retry: 1,
  });
}

export type EventType = "earnings" | "dividend" | "split" | "ipo";
export type ViewMode = "calendar" | "agenda" | "portfolio";
export type IndexName =
  | "sp500"
  | "nasdaq100"
  | "jse_top40"
  | "jse_allshare"
  | "topix"
  | "ftse100"
  | "ftse_china_a50"
  | "eurostoxx50"
  | "custom";
export type TimingFilter = "BMO" | "AMC" | "TNS";

export interface CalendarEvent {
  id: string;
  ticker: string;
  company_name: string;
  date: string; // ISO date string "YYYY-MM-DD"
  type: EventType;
  market_cap: number | null;
  timing: string | null;
  details: Record<string, unknown>;
}

export interface BeatMissEntry {
  quarter: string;
  eps_actual: number | null;
  eps_estimate: number | null;
  eps_beat: boolean | null;
  rev_actual: number | null;
  rev_estimate: number | null;
  rev_beat: boolean | null;
}

export interface PriceReactionDay {
  day: number;
  median_pct: number | null;
  p25: number | null;
  p75: number | null;
}

export interface InsiderTransaction {
  date: string;           // "YYYY-MM-DD"
  name: string;
  role: string;
  transaction_type: "Buy" | "Sell" | "Acquisition" | "Disposal" | "Unknown";
  shares: number | null;
  price_per_share: number | null;
  value: number | null;
}

export interface EarningsDetail {
  eps_estimate: number | null;
  revenue_estimate: number | null;
  analyst_count: number | null;
  beat_miss_history: BeatMissEntry[];
  eps_beat_rate: number | null;
  rev_beat_rate: number | null;
  price_reaction_by_day: PriceReactionDay[];
  eps_trend: number[];
  insufficient_history: boolean;
  insider_activity: InsiderTransaction[];
}

export interface TickerSearchResult {
  ticker: string;
  name: string;
}

export interface Position {
  ticker: string;
  shares: number;
  avg_cost: number;
}

export interface PortfolioRiskRow {
  ticker: string;
  company_name: string;
  shares: number;
  avg_cost: number;
  current_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  next_earnings_date: string | null; // "YYYY-MM-DD"
  days_to_earnings: number | null;
  median_pct_move: number | null;
  expected_dollar_swing: number | null;
  eps_beat_rate: number | null;
  insufficient_history: boolean;
}

export interface FundHolding {
  ticker: string;        // JSE code without .JO
  company_name: string;
  weight_pct: number;
}

export interface FundInfo {
  code: string;
  name: string;
}

export interface FundPosition {
  fund_code: string;
  fund_name: string;
  allocation_pct: number;  // 0-100
}

export interface FundLookThroughRow {
  ticker: string;                   // with .JO
  company_name: string;
  effective_weight_pct: number;
  fund_source: string;
  next_earnings_date: string | null;
  days_to_earnings: number | null;
  median_pct_move: number | null;
}

export interface EventFilters {
  types: Set<EventType>;
  universe: IndexName;
  customTickers: string[];
  timings: Set<TimingFilter>;
}

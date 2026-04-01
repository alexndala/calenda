from __future__ import annotations
from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class EventType(str, Enum):
    EARNINGS = "earnings"
    DIVIDEND = "dividend"
    SPLIT = "split"
    IPO = "ipo"


class CalendarEvent(BaseModel):
    id: str
    ticker: str
    company_name: str
    date: date
    type: EventType
    market_cap: Optional[float] = None
    timing: Optional[str] = None  # BMO | AMC | TNS
    details: dict = {}


class PortfolioPosition(BaseModel):
    ticker: str
    shares: float
    avg_cost: float  # per-share average cost


class PortfolioRiskRow(BaseModel):
    ticker: str
    company_name: str
    shares: float
    avg_cost: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None         # shares × current_price
    unrealized_pnl: Optional[float] = None       # (current_price - avg_cost) × shares
    unrealized_pnl_pct: Optional[float] = None   # unrealized_pnl / (avg_cost × shares)
    next_earnings_date: Optional[date] = None
    days_to_earnings: Optional[int] = None
    # max(abs(median_pct)) across days [-1, 0, +1] in price_reaction_by_day
    # e.g. day[-1]=+2.1%, day[0]=+8.2%, day[+1]=+4.3%  → median_pct_move = 8.2
    # None when price_reaction_by_day is empty (insufficient history)
    median_pct_move: Optional[float] = None
    # abs(median_pct_move / 100) × market_value
    # e.g. abs(8.2 / 100) × $42,500 = $3,485
    # None when median_pct_move or market_value is None
    expected_dollar_swing: Optional[float] = None
    eps_beat_rate: Optional[float] = None
    insufficient_history: bool = False


class EarningsDetail(BaseModel):
    eps_estimate: Optional[float] = None
    revenue_estimate: Optional[float] = None
    analyst_count: Optional[int] = None
    # beat: actual >= estimate (no threshold — raw beat/miss)
    beat_miss_history: list[dict] = []  # [{quarter, eps_actual, eps_estimate, eps_beat, rev_actual, rev_estimate, rev_beat}]
    eps_beat_rate: Optional[float] = None   # 0.0–1.0, e.g. 0.875 = beat 7 of last 8Q
    rev_beat_rate: Optional[float] = None
    # median % closing price change per day, -5..+5 relative to earnings day (day 0)
    price_reaction_by_day: list[dict] = []  # [{day, median_pct, p25, p75}]
    eps_trend: list[float] = []  # last 6Q actual EPS, ascending chronological
    insufficient_history: bool = False  # true when < 4Q of data available

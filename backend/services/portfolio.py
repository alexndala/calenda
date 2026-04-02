"""
Portfolio risk analysis service.

Computes expected earnings-driven dollar swing for each position:
  expected_dollar_swing = abs(max_abs_median_pct / 100) × market_value
where max_abs_median_pct = max(abs(median_pct)) across days [-1, 0, +1].
"""
import asyncio
import logging
import re
from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from cache import NOT_FOUND_SENTINEL, detail_cache
from models import EarningsDetail, PortfolioPosition, PortfolioRiskRow
from services.earnings import get_earnings_detail

logger = logging.getLogger(__name__)

TICKER_RE = re.compile(r"^[A-Z0-9\-]{1,10}(\.[A-Z]{1,2})?$", re.IGNORECASE)


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _get_current_price(t: yf.Ticker) -> Optional[float]:
    """Try fast_info first (cheaper), fall back to full info."""
    try:
        fi = t.fast_info
        for key in ("lastPrice", "last_price"):
            val = fi.get(key) if hasattr(fi, "get") else getattr(fi, key, None)
            price = _safe_float(val)
            if price and price > 0:
                return price
    except Exception:
        pass
    try:
        info = t.info or {}
        for key in ("currentPrice", "regularMarketPrice", "navPrice"):
            price = _safe_float(info.get(key))
            if price and price > 0:
                return price
    except Exception:
        pass
    return None


def _get_company_name(t: yf.Ticker, ticker: str) -> str:
    try:
        info = t.info or {}
        return info.get("longName") or info.get("shortName") or ticker
    except Exception:
        return ticker


def _get_next_earnings_date(t: yf.Ticker) -> Optional[date]:
    """Return nearest future earnings date from calendar, or None."""
    try:
        cal = t.calendar
        today = date.today()
        if isinstance(cal, dict):
            raw = cal.get("Earnings Date", [])
            if raw:
                d = pd.Timestamp(raw[0]).date()
                return d if d >= today else None
        elif cal is not None and hasattr(cal, "columns") and "Earnings Date" in cal.columns:
            raw = cal.loc["Earnings Date"].values
            if len(raw) > 0:
                d = pd.Timestamp(raw[0]).date()
                return d if d >= today else None
    except Exception:
        pass
    return None


def _peak_median_pct(price_reaction_by_day: list[dict]) -> Optional[float]:
    """Max abs(median_pct) across days -1, 0, +1."""
    target = {-1, 0, 1}
    candidates = [
        abs(d["median_pct"])
        for d in price_reaction_by_day
        if d.get("day") in target and d.get("median_pct") is not None
    ]
    return max(candidates) if candidates else None


def _analyze_one(pos: PortfolioPosition) -> PortfolioRiskRow:
    """Synchronous per-ticker analysis — called via asyncio.to_thread."""
    ticker = pos.ticker
    today = date.today()

    company_name = ticker
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    next_earnings_date: Optional[date] = None
    days_to_earnings: Optional[int] = None
    median_pct_move: Optional[float] = None
    expected_dollar_swing: Optional[float] = None
    eps_beat_rate: Optional[float] = None
    insufficient_history = False

    try:
        t = yf.Ticker(ticker)

        # Current price + company name
        current_price = _get_current_price(t)
        company_name = _get_company_name(t, ticker)

        if current_price is not None and current_price > 0:
            market_value = round(current_price * pos.shares, 2)
            if pos.avg_cost > 0:
                unrealized_pnl = round((current_price - pos.avg_cost) * pos.shares, 2)
                unrealized_pnl_pct = round(
                    (current_price - pos.avg_cost) / pos.avg_cost * 100, 2
                )

        # EPS analytics — try detail cache first to avoid redundant yfinance calls
        cache_key = f"detail:{ticker}"
        cached = detail_cache.get(cache_key)
        detail: Optional[EarningsDetail] = None

        if cached and cached != NOT_FOUND_SENTINEL:
            try:
                detail = EarningsDetail(**cached) if isinstance(cached, dict) else None
            except Exception:
                detail = None

        if detail is None:
            detail = get_earnings_detail(ticker)
            if detail:
                detail_cache.set(cache_key, detail.model_dump())

        if detail:
            eps_beat_rate = detail.eps_beat_rate
            insufficient_history = detail.insufficient_history
            peak = _peak_median_pct(detail.price_reaction_by_day)
            if peak is not None:
                median_pct_move = round(peak, 4)
                if market_value is not None:
                    expected_dollar_swing = round(
                        abs(median_pct_move / 100) * market_value, 2
                    )

        # Next earnings date
        next_earnings_date = _get_next_earnings_date(t)
        if next_earnings_date:
            days_to_earnings = (next_earnings_date - today).days
            if days_to_earnings < 0:
                next_earnings_date = None
                days_to_earnings = None

    except Exception as exc:
        logger.warning("Portfolio analysis failed for %s: %s", ticker, exc)

    return PortfolioRiskRow(
        ticker=ticker,
        company_name=company_name,
        shares=pos.shares,
        avg_cost=pos.avg_cost,
        current_price=current_price,
        market_value=market_value,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        next_earnings_date=next_earnings_date,
        days_to_earnings=days_to_earnings,
        median_pct_move=median_pct_move,
        expected_dollar_swing=expected_dollar_swing,
        eps_beat_rate=eps_beat_rate,
        insufficient_history=insufficient_history,
    )


async def analyze_portfolio(
    positions: list[PortfolioPosition],
) -> list[PortfolioRiskRow]:
    """
    Analyze portfolio positions concurrently (max 10 in-flight yfinance calls).
    Partial failures return rows with None for unavailable fields — never raises.
    Returns rows sorted by expected_dollar_swing DESC (None last).
    """
    sem = asyncio.Semaphore(10)

    async def _fetch(pos: PortfolioPosition) -> PortfolioRiskRow:
        async with sem:
            return await asyncio.to_thread(_analyze_one, pos)

    rows = await asyncio.gather(*[_fetch(pos) for pos in positions])

    # Sort: rows with expected_dollar_swing first, descending; None last
    return sorted(
        rows,
        key=lambda r: (r.expected_dollar_swing is None, -(r.expected_dollar_swing or 0)),
    )

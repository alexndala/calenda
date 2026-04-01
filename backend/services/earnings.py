"""
Earnings data service: next event dates, EPS/revenue estimates, beat/miss history.
"""
from __future__ import annotations
import logging
import re
from datetime import date, datetime
from typing import Optional

import pandas as pd
import yfinance as yf

from models import CalendarEvent, EarningsDetail, EventType
from services.price_history import compute_price_reaction

logger = logging.getLogger(__name__)

TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def get_earnings_events(
    tickers: list[str], start: date, end: date
) -> list[CalendarEvent]:
    """
    Fetch upcoming earnings dates for a list of tickers in [start, end].
    Returns lightweight CalendarEvent list (no analytics — those are on-demand).
    """
    events: list[CalendarEvent] = []

    for ticker in tickers:
        if not TICKER_RE.match(ticker):
            continue
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            company_name = info.get("longName") or info.get("shortName") or ticker
            market_cap = _safe_float(info.get("marketCap"))

            # Try calendar first (most reliable for upcoming)
            calendar = t.calendar
            next_date: Optional[date] = None
            timing: Optional[str] = None

            if calendar is not None and not isinstance(calendar, dict):
                # Old-style DataFrame
                if hasattr(calendar, "columns") and "Earnings Date" in calendar.columns:
                    raw = calendar.loc["Earnings Date"].values
                    if len(raw) > 0:
                        next_date = pd.Timestamp(raw[0]).date()
            elif isinstance(calendar, dict):
                raw = calendar.get("Earnings Date", [])
                if raw:
                    next_date = pd.Timestamp(raw[0]).date()
                timing_raw = calendar.get("Earnings Call Time")
                if timing_raw:
                    t_str = str(timing_raw).lower()
                    if "before" in t_str:
                        timing = "BMO"
                    elif "after" in t_str:
                        timing = "AMC"
                    else:
                        timing = "TNS"

            if next_date is None:
                # Fallback: earnings_dates index (includes historical + upcoming)
                try:
                    ed = t.earnings_dates
                    if ed is not None and not ed.empty:
                        future = ed[ed.index.date >= start]
                        if not future.empty:
                            next_date = future.index[0].date()
                except Exception:
                    pass

            if next_date is None:
                continue

            if not (start <= next_date <= end):
                continue

            # Extract estimates from calendar
            eps_est = None
            rev_est = None
            if isinstance(calendar, dict):
                eps_est = _safe_float(calendar.get("EPS Estimate"))
                rev_est = _safe_float(calendar.get("Revenue Estimate"))

            events.append(
                CalendarEvent(
                    id=f"earnings-{ticker}-{next_date}",
                    ticker=ticker,
                    company_name=company_name,
                    date=next_date,
                    type=EventType.EARNINGS,
                    market_cap=market_cap,
                    timing=timing,
                    details={
                        "eps_estimate": eps_est,
                        "revenue_estimate": rev_est,
                    },
                )
            )
        except Exception as exc:
            logger.warning("Earnings fetch failed for %s: %s", ticker, exc)
            continue

    return events


def get_earnings_detail(ticker: str) -> Optional[EarningsDetail]:
    """
    Fetch full analytics for a single ticker's earnings detail panel.
    Includes beat/miss history (last 8Q), price reaction (±5 days), EPS trend.
    """
    if not TICKER_RE.match(ticker):
        return None

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        # Upcoming estimate
        calendar = t.calendar
        eps_estimate = None
        rev_estimate = None
        if isinstance(calendar, dict):
            eps_estimate = _safe_float(calendar.get("EPS Estimate"))
            rev_estimate = _safe_float(calendar.get("Revenue Estimate"))

        # Historical earnings (beat/miss)
        beat_miss_history: list[dict] = []
        eps_beat_rate: Optional[float] = None
        rev_beat_rate: Optional[float] = None
        eps_trend: list[float] = []
        earnings_dates_for_reaction: list[date] = []

        try:
            # earnings_dates is more reliable than earnings_history in current yfinance.
            # Past rows have "Reported EPS" + "EPS Estimate"; future rows have "EPS Estimate" only.
            ed = t.earnings_dates
            if ed is not None and not ed.empty:
                now = pd.Timestamp.now(tz=ed.index.tz)

                # Fallback: get upcoming EPS estimate from earnings_dates if calendar missed it
                future_ed = ed[ed.index > now]
                if not future_ed.empty and eps_estimate is None:
                    eps_estimate = _safe_float(future_ed.iloc[-1].get("EPS Estimate"))

                # Historical beat/miss: past dates that have an actual result
                past = ed[ed.index <= now].dropna(subset=["Reported EPS"]).tail(8)
                total = len(past)
                eps_beats = 0

                for idx, row in past.iterrows():
                    eps_actual = _safe_float(row.get("Reported EPS"))
                    eps_est_q = _safe_float(row.get("EPS Estimate"))

                    eps_beat = None
                    if eps_actual is not None and eps_est_q is not None:
                        eps_beat = eps_actual >= eps_est_q
                        if eps_beat:
                            eps_beats += 1

                    # Compute quarter string from date (avoid invalid %q strftime code)
                    quarter_str = f"{idx.year}-Q{(idx.month - 1) // 3 + 1}"

                    beat_miss_history.append(
                        {
                            "quarter": quarter_str,
                            "eps_actual": eps_actual,
                            "eps_estimate": eps_est_q,
                            "eps_beat": eps_beat,
                            "rev_actual": None,   # not available from earnings_dates
                            "rev_estimate": None,
                            "rev_beat": None,
                        }
                    )

                    if eps_actual is not None:
                        eps_trend.append(eps_actual)

                    # Collect the date for price reaction calculation
                    if hasattr(idx, "date"):
                        earnings_dates_for_reaction.append(idx.date())

                if total > 0:
                    eps_beat_rate = round(eps_beats / total, 4)
                    # rev_beat_rate stays None — no revenue data in earnings_dates

        except Exception as exc:
            logger.warning("earnings_dates failed for %s: %s", ticker, exc)

        # Price reaction
        price_reaction_by_day: list[dict] = []
        if earnings_dates_for_reaction:
            price_reaction_by_day = compute_price_reaction(ticker, earnings_dates_for_reaction)

        insufficient = len(beat_miss_history) < 4

        return EarningsDetail(
            eps_estimate=eps_estimate,
            revenue_estimate=rev_estimate,
            beat_miss_history=beat_miss_history,
            eps_beat_rate=eps_beat_rate,
            rev_beat_rate=rev_beat_rate,
            price_reaction_by_day=price_reaction_by_day,
            eps_trend=eps_trend[-6:],  # last 6Q only
            insufficient_history=insufficient,
        )

    except Exception as exc:
        logger.error("Earnings detail failed for %s: %s", ticker, exc)
        return None

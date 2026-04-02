"""Dividend events: upcoming ex-dividend dates and amounts."""
import logging
import re
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from models import CalendarEvent, EventType

logger = logging.getLogger(__name__)
TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def get_dividend_events(tickers: list[str], start: date, end: date) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []

    for ticker in tickers:
        if not TICKER_RE.match(ticker):
            continue
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            company_name = info.get("longName") or info.get("shortName") or ticker
            market_cap = _safe_float(info.get("marketCap"))

            # Try next ex-dividend date from info
            next_div_date: Optional[date] = None
            next_div_date_raw = info.get("exDividendDate")
            if next_div_date_raw:
                try:
                    if isinstance(next_div_date_raw, (int, float)):
                        next_div_date = date.fromtimestamp(next_div_date_raw)
                    else:
                        next_div_date = pd.Timestamp(next_div_date_raw).date()
                except Exception:
                    pass

            # Also check historical dividends series for upcoming entries
            try:
                divs = t.dividends
                if divs is not None and not divs.empty:
                    future_divs = divs[divs.index.date >= start]
                    if not future_divs.empty:
                        candidate = future_divs.index[0].date()
                        if next_div_date is None or candidate < next_div_date:
                            next_div_date = candidate
            except Exception:
                pass

            if next_div_date is None or not (start <= next_div_date <= end):
                continue

            dividend_amount = _safe_float(info.get("lastDividendValue"))

            events.append(
                CalendarEvent(
                    id=f"dividend-{ticker}-{next_div_date}",
                    ticker=ticker,
                    company_name=company_name,
                    date=next_div_date,
                    type=EventType.DIVIDEND,
                    market_cap=market_cap,
                    details={"amount": dividend_amount},
                )
            )
        except Exception as exc:
            logger.warning("Dividend fetch failed for %s: %s", ticker, exc)
            continue

    return events

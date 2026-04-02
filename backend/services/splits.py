"""Stock split events: upcoming splits within the date range."""
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


def get_split_events(tickers: list[str], start: date, end: date) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []

    for ticker in tickers:
        if not TICKER_RE.match(ticker):
            continue
        try:
            t = yf.Ticker(ticker)
            splits = t.splits
            if splits is None or splits.empty:
                continue

            # Splits series is historical — filter to our window
            future = splits[splits.index.date >= start]
            future = future[future.index.date <= end]
            if future.empty:
                continue

            info = t.info or {}
            company_name = info.get("longName") or info.get("shortName") or ticker
            market_cap = _safe_float(info.get("marketCap"))

            for split_ts, ratio in future.items():
                split_date = split_ts.date()
                events.append(
                    CalendarEvent(
                        id=f"split-{ticker}-{split_date}",
                        ticker=ticker,
                        company_name=company_name,
                        date=split_date,
                        type=EventType.SPLIT,
                        market_cap=market_cap,
                        details={"ratio": float(ratio)},
                    )
                )
        except Exception as exc:
            logger.warning("Split fetch failed for %s: %s", ticker, exc)
            continue

    return events

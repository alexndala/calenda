"""Stock split events: upcoming splits within the date range."""
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from cache import events_cache
from models import CalendarEvent, EventType

logger = logging.getLogger(__name__)
TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")

_MAX_WORKERS = 40
_SPLITS_CACHE_TTL = 86400  # 24h — splits are announced weeks in advance


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _fetch_ticker_splits_raw(ticker: str) -> list[dict]:
    """Fetch and cache the full split history for a ticker as plain dicts (date-agnostic).

    Returns a list of {"date": date, "ratio": float, "company_name": str, "market_cap": float|None}.
    Cached for 24h so month navigation never re-fetches the same ticker.
    """
    cache_key = f"splits_raw:{ticker}"
    cached = events_cache.get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    rows: list[dict] = []
    try:
        t = yf.Ticker(ticker)
        splits = t.splits
        if splits is None or splits.empty:
            events_cache.set(cache_key, rows, ttl=_SPLITS_CACHE_TTL)
            return rows

        info = t.info or {}
        company_name = info.get("longName") or info.get("shortName") or ticker
        market_cap = _safe_float(info.get("marketCap"))

        for split_ts, ratio in splits.items():
            rows.append({
                "date": split_ts.date(),
                "ratio": float(ratio),
                "company_name": company_name,
                "market_cap": market_cap,
            })
    except Exception as exc:
        logger.warning("Split fetch failed for %s: %s", ticker, exc)

    events_cache.set(cache_key, rows, ttl=_SPLITS_CACHE_TTL)
    return rows


def _filter_ticker_splits(ticker: str, start: date, end: date) -> list[CalendarEvent]:
    """Return CalendarEvents for a ticker by filtering its cached split history."""
    rows = _fetch_ticker_splits_raw(ticker)
    events: list[CalendarEvent] = []
    for row in rows:
        split_date = row["date"]
        if start <= split_date <= end:
            events.append(
                CalendarEvent(
                    id=f"split-{ticker}-{split_date}",
                    ticker=ticker,
                    company_name=row["company_name"],
                    date=split_date,
                    type=EventType.SPLIT,
                    market_cap=row["market_cap"],
                    details={"ratio": row["ratio"]},
                )
            )
    return events


def get_split_events(tickers: list[str], start: date, end: date) -> list[CalendarEvent]:
    valid = [t for t in tickers if TICKER_RE.match(t)]
    events: list[CalendarEvent] = []

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = {pool.submit(_filter_ticker_splits, ticker, start, end): ticker for ticker in valid}
        for future in as_completed(futures):
            events.extend(future.result())

    return events

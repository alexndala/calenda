"""
Historical price reaction around earnings events.

For each prior earnings date, compute the % change in closing price for
each trading day in the -5..+5 window relative to the earnings date (day 0).
Aggregate across events using MEDIAN (not mean) to reduce outlier impact.

Returns [{day: int, median_pct: float, p25: float, p75: float}] for days -5..+5.
"""
from __future__ import annotations
import logging
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

WINDOW = 5  # trading days before and after earnings


def _get_trading_days_offset(base_date: pd.Timestamp, offset: int, price_df: pd.DataFrame) -> Optional[pd.Timestamp]:
    """
    Return the trading day `offset` days from base_date.
    Weekend/holiday alignment: if base_date is not in price_df index, snap to nearest.
    """
    dates = price_df.index
    if len(dates) == 0:
        return None

    # Find closest date to base_date
    idx = dates.searchsorted(base_date)
    idx = min(idx, len(dates) - 1)
    adjusted_idx = idx + offset

    if adjusted_idx < 0 or adjusted_idx >= len(dates):
        return None
    return dates[adjusted_idx]


def compute_price_reaction(ticker: str, earnings_dates: list[date]) -> list[dict]:
    """
    Compute median ±5 day price reaction across all provided earnings dates.

    Args:
        ticker: Stock ticker symbol
        earnings_dates: List of prior earnings event dates (at least 4 recommended)

    Returns:
        List of {day, median_pct, p25, p75} for days -5 to +5, empty on failure.
    """
    if not earnings_dates or len(earnings_dates) < 2:
        return []

    try:
        # Download 3 years of daily price history in one call
        df = yf.download(
            ticker,
            period="3y",
            interval="1d",
            auto_adjust=True,
            progress=False,
        )
        if df.empty or "Close" not in df.columns:
            logger.warning("No price data for %s", ticker)
            return []

        # Flatten MultiIndex columns if present (yfinance sometimes returns ticker-keyed)
        if isinstance(df.columns, pd.MultiIndex):
            df = df[ticker] if ticker in df.columns.get_level_values(0) else df

        close = df["Close"].dropna()
        if len(close) < 20:
            return []

    except Exception as exc:
        logger.error("yfinance download failed for %s: %s", ticker, exc)
        return []

    # For each day offset, collect % changes across all earnings events
    day_pct_changes: dict[int, list[float]] = {d: [] for d in range(-WINDOW, WINDOW + 1)}

    for event_date in earnings_dates:
        base_ts = pd.Timestamp(event_date)
        base_day = _get_trading_days_offset(base_ts, 0, close.to_frame())
        if base_day is None or base_day not in close.index:
            continue

        base_price = close.loc[base_day]
        if base_price == 0 or pd.isna(base_price):
            continue

        for offset in range(-WINDOW, WINDOW + 1):
            target_day = _get_trading_days_offset(base_ts, offset, close.to_frame())
            if target_day is None:
                continue
            target_price = close.get(target_day)
            if target_price is None or pd.isna(target_price):
                continue
            pct = (float(target_price) - float(base_price)) / float(base_price) * 100
            day_pct_changes[offset].append(pct)

    result = []
    for day in range(-WINDOW, WINDOW + 1):
        changes = day_pct_changes[day]
        if len(changes) < 2:
            result.append({"day": day, "median_pct": None, "p25": None, "p75": None})
            continue
        arr = np.array(changes)
        result.append(
            {
                "day": day,
                "median_pct": round(float(np.median(arr)), 3),
                "p25": round(float(np.percentile(arr, 25)), 3),
                "p75": round(float(np.percentile(arr, 75)), 3),
            }
        )
    return result

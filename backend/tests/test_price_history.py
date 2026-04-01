"""Unit tests: price history calculation logic."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from datetime import date, timedelta
from unittest.mock import patch
import pandas as pd

from services.price_history import compute_price_reaction, _get_trading_days_offset


def _make_price_series(n: int = 200, start="2023-01-02") -> pd.Series:
    """Synthetic daily close prices."""
    idx = pd.bdate_range(start=start, periods=n)
    prices = 100 + np.cumsum(np.random.randn(n))
    return pd.Series(prices, index=idx, name="Close")


def test_get_trading_days_offset_forward():
    close = _make_price_series()
    df = close.to_frame()
    base = df.index[10]
    result = _get_trading_days_offset(base, 5, df)
    assert result == df.index[15]


def test_get_trading_days_offset_backward():
    close = _make_price_series()
    df = close.to_frame()
    base = df.index[10]
    result = _get_trading_days_offset(base, -5, df)
    assert result == df.index[5]


def test_get_trading_days_offset_out_of_bounds():
    close = _make_price_series(n=10)
    df = close.to_frame()
    base = df.index[-1]
    result = _get_trading_days_offset(base, 100, df)
    assert result is None


def test_compute_price_reaction_insufficient_dates():
    result = compute_price_reaction("AAPL", [date(2025, 1, 30)])
    assert result == []


def test_compute_price_reaction_empty_download():
    with patch("services.price_history.yf.download") as mock_dl:
        mock_dl.return_value = pd.DataFrame()
        result = compute_price_reaction("FAKE", [date(2025, 1, 30), date(2025, 4, 30)])
        assert result == []


def test_compute_price_reaction_structure():
    """With mocked price data, result should have 11 entries (-5..+5)."""
    close = _make_price_series(n=500, start="2022-01-03")

    mock_df = pd.DataFrame({"Close": close, "Open": close, "High": close, "Low": close, "Volume": 1})

    with patch("services.price_history.yf.download") as mock_dl:
        mock_dl.return_value = mock_df
        dates = [close.index[50].date(), close.index[100].date(),
                 close.index[150].date(), close.index[200].date()]
        result = compute_price_reaction("AAPL", dates)

    assert len(result) == 11
    assert result[5]["day"] == 0  # day 0 is index 5 (from -5)
    for entry in result:
        assert "day" in entry
        assert "median_pct" in entry
        assert "p25" in entry
        assert "p75" in entry


def test_compute_price_reaction_day0_near_zero():
    """On earnings day itself (day 0), % change from base should be ~0."""
    close = _make_price_series(n=300, start="2022-01-03")
    mock_df = pd.DataFrame({"Close": close, "Open": close, "High": close, "Low": close, "Volume": 1})

    with patch("services.price_history.yf.download") as mock_dl:
        mock_dl.return_value = mock_df
        dates = [close.index[i * 30].date() for i in range(1, 8)]
        result = compute_price_reaction("AAPL", dates)

    day0 = next(r for r in result if r["day"] == 0)
    assert day0["median_pct"] is not None
    assert abs(day0["median_pct"]) < 0.01  # ~0% on day 0 vs itself

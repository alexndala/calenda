"""Unit tests: earnings beat/miss calculation with mocked yfinance."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from services.earnings import get_earnings_events, get_earnings_detail


def _mock_ticker(calendar=None, earnings_history=None, info=None, earnings_dates=None):
    mock = MagicMock()
    mock.calendar = calendar
    mock.info = info or {"longName": "Test Corp", "marketCap": 1e12}
    mock.earnings_dates = earnings_dates
    mock.earnings_history = earnings_history
    return mock


def test_get_earnings_events_from_calendar():
    calendar = {
        "Earnings Date": [pd.Timestamp("2026-04-30")],
        "EPS Estimate": [1.62],
        "Revenue Estimate": [95e9],
        "Earnings Call Time": ["After Market Hours"],
    }
    mock_ticker = _mock_ticker(calendar=calendar)

    with patch("services.earnings.yf.Ticker", return_value=mock_ticker):
        events = get_earnings_events(["AAPL"], date(2026, 4, 1), date(2026, 4, 30))

    assert len(events) == 1
    assert events[0].ticker == "AAPL"
    assert events[0].type.value == "earnings"
    assert events[0].date == date(2026, 4, 30)
    assert events[0].timing == "AMC"


def test_get_earnings_events_skips_out_of_range():
    calendar = {"Earnings Date": [pd.Timestamp("2027-01-15")], "EPS Estimate": [1.0]}
    mock_ticker = _mock_ticker(calendar=calendar)

    with patch("services.earnings.yf.Ticker", return_value=mock_ticker):
        events = get_earnings_events(["AAPL"], date(2026, 4, 1), date(2026, 4, 30))

    assert events == []


def test_get_earnings_events_skips_invalid_ticker():
    with patch("services.earnings.yf.Ticker") as mock_yf:
        events = get_earnings_events(["INVALID!TICKER"], date(2026, 4, 1), date(2026, 4, 30))

    mock_yf.assert_not_called()
    assert events == []


def test_beat_miss_calculation():
    """Verify beat rate math: 3 beats in 4 quarters = 0.75."""
    history_data = pd.DataFrame(
        {
            "epsActual": [1.2, 0.9, 1.5, 1.1],
            "epsEstimate": [1.0, 1.0, 1.3, 1.0],
            "revenueActual": [100e9, 90e9, 110e9, 95e9],
            "revenueEstimate": [95e9, 95e9, 105e9, 100e9],
        },
        index=pd.to_datetime(["2025-01-30", "2025-04-30", "2025-07-30", "2025-10-30"]),
    )

    mock_ticker_obj = _mock_ticker(earnings_history=history_data)
    mock_ticker_obj.calendar = {}

    with patch("services.earnings.yf.Ticker", return_value=mock_ticker_obj), \
         patch("services.earnings.compute_price_reaction", return_value=[]):
        detail = get_earnings_detail("AAPL")

    assert detail is not None
    # Beats: Q1 (1.2>1.0), Q3 (1.5>1.3), Q4 (1.1>1.0) = 3/4 = 0.75
    assert detail.eps_beat_rate == 0.75
    # Revenue beats: Q1, Q3 = 2/4 = 0.5
    assert detail.rev_beat_rate == 0.5


def test_earnings_detail_returns_none_for_invalid_ticker():
    result = get_earnings_detail("!INVALID!")
    assert result is None

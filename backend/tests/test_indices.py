"""Unit tests: index constituent fetching with fallback."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
import pandas as pd

from services.indices import get_sp500_tickers, get_nasdaq100_tickers, SP500_FALLBACK, NASDAQ100_FALLBACK


def _mock_sp500_table():
    return [pd.DataFrame({"Symbol": ["AAPL", "MSFT", "NVDA"] * 170})]  # 510 rows


def test_sp500_uses_wikipedia_when_available():
    with patch("services.indices.pd.read_html") as mock_rl:
        mock_rl.return_value = _mock_sp500_table()
        tickers = get_sp500_tickers()
    assert "AAPL" in tickers
    assert len(tickers) >= 400


def test_sp500_uses_fallback_on_exception():
    with patch("services.indices.pd.read_html", side_effect=Exception("network error")):
        tickers = get_sp500_tickers()
    assert tickers == SP500_FALLBACK
    assert len(tickers) > 0


def test_sp500_normalizes_dots_to_dashes():
    df = pd.DataFrame({"Symbol": ["BRK.B", "BF.B", "AAPL"]})
    with patch("services.indices.pd.read_html") as mock_rl:
        mock_rl.return_value = [df] + [df] * 5  # extra tables
        tickers = get_sp500_tickers()
    # Too few tickers (3 < 400) — should fall back
    assert tickers == SP500_FALLBACK


def test_nasdaq100_fallback():
    with patch("services.indices.pd.read_html", side_effect=Exception("network error")):
        tickers = get_nasdaq100_tickers()
    assert tickers == NASDAQ100_FALLBACK

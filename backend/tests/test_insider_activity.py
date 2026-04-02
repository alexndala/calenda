"""Tests for insider activity service — OpenBB and SENS paths are both mocked."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from services.insider_activity import get_insider_activity, _get_us_insider_activity, _get_jse_insider_activity
from models import InsiderTransaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_obb_item(
    filing_date,
    name: str = "John Smith",
    role: str = "CEO",
    code: str = "P",
    shares: int = 1000,
    price: float = 150.0,
) -> MagicMock:
    item = MagicMock()
    item.filing_date = filing_date
    item.reporting_name = name
    item.reporting_relationship = role
    item.transaction_code = code
    item.securities_transacted = shares
    item.price = price
    item.value = shares * price
    return item


def _make_obb_result(items: list) -> MagicMock:
    result = MagicMock()
    result.results = items
    return result


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

def test_us_ticker_routes_to_openbb():
    """Non-.JO ticker → calls _get_us_insider_activity."""
    with patch("services.insider_activity._get_us_insider_activity", return_value=[]) as mock_us, \
         patch("services.insider_activity._get_jse_insider_activity", return_value=[]) as mock_jse:
        get_insider_activity("AAPL")
    mock_us.assert_called_once_with("AAPL", 90)
    mock_jse.assert_not_called()


def test_jse_ticker_routes_to_sens():
    """.JO ticker → calls _get_jse_insider_activity."""
    with patch("services.insider_activity._get_us_insider_activity", return_value=[]) as mock_us, \
         patch("services.insider_activity._get_jse_insider_activity", return_value=[]) as mock_jse:
        get_insider_activity("NPN.JO")
    mock_jse.assert_called_once_with("NPN.JO", 90)
    mock_us.assert_not_called()


# ---------------------------------------------------------------------------
# OpenBB (US) path
# ---------------------------------------------------------------------------

def test_us_happy_path_returns_transactions():
    """Valid OpenBB result → returns InsiderTransaction list."""
    recent_date = MagicMock()
    recent_date.date.return_value = date.today() - timedelta(days=5)
    item = _make_obb_item(filing_date=recent_date, code="P")

    mock_result = _make_obb_result([item])
    with patch.dict("sys.modules", {"openbb": MagicMock(obb=MagicMock(
        equity=MagicMock(ownership=MagicMock(insider_trading=MagicMock(return_value=mock_result)))
    ))}):
        result = _get_us_insider_activity("AAPL", lookback_days=90)

    assert len(result) == 1
    assert isinstance(result[0], InsiderTransaction)
    assert result[0].transaction_type == "Buy"
    assert result[0].name == "John Smith"
    assert result[0].role == "CEO"
    assert result[0].shares == 1000


def test_us_sell_transaction_type():
    """SEC code 'S' → transaction_type == 'Sell'."""
    recent_date = MagicMock()
    recent_date.date.return_value = date.today() - timedelta(days=10)
    item = _make_obb_item(filing_date=recent_date, code="S")

    mock_result = _make_obb_result([item])
    with patch.dict("sys.modules", {"openbb": MagicMock(obb=MagicMock(
        equity=MagicMock(ownership=MagicMock(insider_trading=MagicMock(return_value=mock_result)))
    ))}):
        result = _get_us_insider_activity("AAPL", lookback_days=90)

    assert result[0].transaction_type == "Sell"


def test_us_openbb_failure_returns_empty_list():
    """OpenBB raises exception → returns [] without propagating."""
    with patch.dict("sys.modules", {"openbb": MagicMock(obb=MagicMock(
        equity=MagicMock(ownership=MagicMock(insider_trading=MagicMock(side_effect=Exception("API error"))))
    ))}):
        result = _get_us_insider_activity("AAPL", lookback_days=90)

    assert result == []


def test_us_filters_old_transactions():
    """Transaction older than lookback_days → excluded from results."""
    old_date = MagicMock()
    old_date.date.return_value = date.today() - timedelta(days=120)
    item = _make_obb_item(filing_date=old_date, code="P")

    mock_result = _make_obb_result([item])
    with patch.dict("sys.modules", {"openbb": MagicMock(obb=MagicMock(
        equity=MagicMock(ownership=MagicMock(insider_trading=MagicMock(return_value=mock_result)))
    ))}):
        result = _get_us_insider_activity("AAPL", lookback_days=90)

    assert result == []


# ---------------------------------------------------------------------------
# SENS (JSE) path
# ---------------------------------------------------------------------------

def test_jse_happy_path_returns_transactions():
    """SENS returns director dealings → InsiderTransaction list."""
    mock_transactions = [
        InsiderTransaction(
            date=date.today() - timedelta(days=7),
            name="Director",
            role="Director",
            transaction_type="Acquisition",
        )
    ]
    with patch("services.insider_activity.get_jse_director_dealings",
               return_value={"NPN.JO": mock_transactions}) as mock_sens:
        result = _get_jse_insider_activity("NPN.JO", lookback_days=90)

    mock_sens.assert_called_once_with(["NPN.JO"], lookback_days=90)
    assert len(result) == 1
    assert result[0].transaction_type == "Acquisition"


def test_jse_ticker_not_in_result_returns_empty():
    """SENS returns data for other tickers but not the requested one → []."""
    with patch("services.insider_activity.get_jse_director_dealings",
               return_value={"SBK.JO": []}):
        result = _get_jse_insider_activity("NPN.JO", lookback_days=90)

    assert result == []


def test_jse_sens_failure_returns_empty():
    """SENS scraper raises → returns [] without propagating."""
    with patch("services.insider_activity.get_jse_director_dealings",
               side_effect=Exception("Connection refused")):
        result = _get_jse_insider_activity("NPN.JO", lookback_days=90)

    assert result == []

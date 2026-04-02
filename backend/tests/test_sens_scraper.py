"""Tests for SENS scraper — all HTTP calls are mocked."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from services.sens_scraper import get_jse_earnings_dates

# Minimal HTML table that matches the expected SENS page structure
_SENS_HTML_TEMPLATE = """
<html><body>
<table>
  <tr><th>Date</th><th>Issuer</th><th>Subject</th></tr>
  {rows}
</table>
</body></html>
"""


def _make_row(ann_date: str, issuer: str, subject: str) -> str:
    return f"<tr><td>{ann_date}</td><td>{issuer}</td><td>{subject}</td></tr>"


def _mock_response(html: str, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


def test_happy_path_returns_matched_ticker():
    """SENS page with NPN announcement → returns NPN.JO mapped to that date."""
    html = _SENS_HTML_TEMPLATE.format(
        rows=_make_row("2026-05-15", "NPN", "Preliminary results for the year ended")
    )
    mock_resp = _mock_response(html)

    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = get_jse_earnings_dates(["NPN.JO", "SBK.JO"])

    assert result == {"NPN.JO": date(2026, 5, 15)}


def test_empty_tickers_list_returns_empty_without_http_call():
    """No tickers → returns {} without making any HTTP request."""
    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        result = get_jse_earnings_dates([])

    mock_client_cls.assert_not_called()
    assert result == {}


def test_non_jse_tickers_only_returns_empty_without_http_call():
    """US-only tickers (no .JO) → returns {} without HTTP call."""
    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        result = get_jse_earnings_dates(["AAPL", "MSFT"])

    mock_client_cls.assert_not_called()
    assert result == {}


def test_http_error_returns_empty():
    """HTTP 500 → returns {} gracefully (no exception raised to caller)."""
    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client_cls.return_value = mock_client

        result = get_jse_earnings_dates(["NPN.JO"])

    assert result == {}


def test_html_structure_changed_returns_empty():
    """Page with no <table> → returns {} and logs warning (HTML may have changed)."""
    html = "<html><body><p>No table here</p></body></html>"
    mock_resp = _mock_response(html)

    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = get_jse_earnings_dates(["NPN.JO"])

    assert result == {}


def test_ticker_not_in_sens_result_not_in_returned_dict():
    """SENS has SBK but not NPN → NPN.JO absent from result (no KeyError)."""
    html = _SENS_HTML_TEMPLATE.format(
        rows=_make_row("2026-05-20", "SBK", "Condensed financial results")
    )
    mock_resp = _mock_response(html)

    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = get_jse_earnings_dates(["NPN.JO", "SBK.JO"])

    assert "NPN.JO" not in result
    assert result == {"SBK.JO": date(2026, 5, 20)}


def test_non_earnings_subject_filtered_out():
    """Announcement with irrelevant subject → not included in results."""
    html = _SENS_HTML_TEMPLATE.format(
        rows=_make_row("2026-05-15", "NPN", "Change of director")
    )
    mock_resp = _mock_response(html)

    with patch("services.sens_scraper.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = get_jse_earnings_dates(["NPN.JO"])

    assert result == {}

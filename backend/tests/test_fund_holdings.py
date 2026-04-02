"""Tests for fund_holdings service (profiledata.co.za scraper)."""
import pytest
from unittest.mock import MagicMock, patch

from services.fund_holdings import get_fund_holdings, search_funds, SA_FUND_FALLBACK
from models import FundHolding


HOLDINGS_HTML_HAPPY = """
<html><body>
<table>
  <tr><th>Security</th><th>Sector</th><th>Asset Class</th><th>Country</th><th>% Fund</th></tr>
  <tr>
    <td><a href="Summary.aspx?c=NPN">Naspers</a></td>
    <td>Technology</td><td>Equity</td><td>SA</td><td>8.5%</td>
  </tr>
  <tr>
    <td><a href="Summary.aspx?c=SBK">Standard Bank</a></td>
    <td>Financials</td><td>Equity</td><td>SA</td><td>5.2%</td>
  </tr>
</table>
</body></html>
"""

HOLDINGS_HTML_WITH_NON_EQUITY = """
<html><body>
<table>
  <tr><th>Security</th><th>Sector</th><th>Asset Class</th><th>Country</th><th>% Fund</th></tr>
  <tr>
    <td><a href="Summary.aspx?c=FSR">FirstRand</a></td>
    <td>Financials</td><td>Equity</td><td>SA</td><td>6.1%</td>
  </tr>
  <tr>
    <td>R186 Government Bond</td>
    <td>Fixed Income</td><td>Bond</td><td>SA</td><td>12.3%</td>
  </tr>
  <tr>
    <td>Cash and Money Market</td>
    <td>Cash</td><td>Cash</td><td>SA</td><td>3.0%</td>
  </tr>
</table>
</body></html>
"""

HOLDINGS_HTML_NO_TABLE = """
<html><body><p>Fund not found.</p></body></html>
"""


def _mock_response(html: str, status_code: int = 200):
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestGetFundHoldings:
    def test_happy_path_returns_equity_holdings(self):
        with patch("services.fund_holdings.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = _mock_response(HOLDINGS_HTML_HAPPY)

            result = get_fund_holdings("AGBF")

        assert len(result) == 2
        npn = next(h for h in result if h.ticker == "NPN")
        assert npn.company_name == "Naspers"
        assert npn.weight_pct == 8.5

        sbk = next(h for h in result if h.ticker == "SBK")
        assert sbk.weight_pct == 5.2

    def test_skips_non_equity_rows(self):
        """Bond and cash rows have no anchor link — should be skipped."""
        with patch("services.fund_holdings.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = _mock_response(HOLDINGS_HTML_WITH_NON_EQUITY)

            result = get_fund_holdings("CORONBAL")

        assert len(result) == 1
        assert result[0].ticker == "FSR"
        assert result[0].weight_pct == 6.1

    def test_no_table_returns_empty(self):
        with patch("services.fund_holdings.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = _mock_response(HOLDINGS_HTML_NO_TABLE)

            result = get_fund_holdings("BADCODE")

        assert result == []

    def test_http_failure_returns_empty(self):
        with patch("services.fund_holdings.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection refused")

            result = get_fund_holdings("AGBF")

        assert result == []

    def test_empty_fund_code_returns_empty(self):
        result = get_fund_holdings("")
        assert result == []

    def test_skips_rows_with_zero_weight(self):
        html = """
        <html><body><table>
          <tr><th>Security</th><th>S</th><th>A</th><th>C</th><th>% Fund</th></tr>
          <tr>
            <td><a href="Summary.aspx?c=SOL">Sasol</a></td>
            <td></td><td></td><td></td><td>0.0%</td>
          </tr>
          <tr>
            <td><a href="Summary.aspx?c=AGL">Anglo</a></td>
            <td></td><td></td><td></td><td>4.5%</td>
          </tr>
        </table></body></html>
        """
        with patch("services.fund_holdings.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.get.return_value = _mock_response(html)

            result = get_fund_holdings("STX40")

        assert len(result) == 1
        assert result[0].ticker == "AGL"


class TestSearchFunds:
    def test_search_by_name_substring(self):
        results = search_funds("allan")
        assert len(results) > 0
        assert all("Allan Gray" in r.name for r in results)

    def test_search_by_code(self):
        results = search_funds("STX40")
        assert any(r.code == "STX40" for r in results)

    def test_short_query_returns_empty(self):
        results = search_funds("a")
        assert results == []

    def test_unknown_query_returns_empty(self):
        results = search_funds("XYZQWERTY123")
        assert results == []

    def test_results_capped_at_10(self):
        # Search for a common term that should match many funds
        results = search_funds("fund")
        assert len(results) <= 10

    def test_results_sorted_by_name(self):
        results = search_funds("coronation")
        names = [r.name for r in results]
        assert names == sorted(names)

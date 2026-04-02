"""
Fund holdings scraper: profiledata.co.za (Marriott fund research tool).
Public HTML, no auth. Holdings update monthly — cache at 24h TTL.

WARNING: HTML scraper — profiledata.co.za redesigns will break this.
Pre-ship: manually verify Holdings.aspx table structure and JSE ticker link pattern.
Check: https://marriott.profiledata.co.za/Holdings.aspx?c=SLEA3
  (a) table exists with >= 5 columns
  (b) Security column has <a href="...?c=NPN"> for JSE-listed holdings
  (c) bond/cash/offshore rows have no anchor link
  (d) last column is % Fund weight
"""

import logging
import re

import httpx
from bs4 import BeautifulSoup

from models import FundHolding, FundInfo

logger = logging.getLogger(__name__)

PROFILEDATA_HOLDINGS_URL = "https://marriott.profiledata.co.za/Holdings.aspx"

# Curated fallback list of popular SA unit trust codes (profiledata codes).
# Used when the fund is entered directly or search is unavailable.
# Update quarterly as popular funds are added. Codes verified against profiledata URLs.
SA_FUND_FALLBACK: list[FundInfo] = [
    FundInfo(code="AGBF", name="Allan Gray Balanced Fund"),
    FundInfo(code="AGEF", name="Allan Gray Equity Fund"),
    FundInfo(code="AGOF", name="Allan Gray Optimal Fund"),
    FundInfo(code="CORONBAL", name="Coronation Balanced Plus"),
    FundInfo(code="CORONEQUITY", name="Coronation Equity Fund"),
    FundInfo(code="CORONMARKET", name="Coronation Market Plus"),
    FundInfo(code="STX40", name="Satrix 40 Portfolio"),
    FundInfo(code="SLEA3", name="Satrix Low Equity Balanced Index Fund"),
    FundInfo(code="STXDIV", name="Satrix Dividend Plus Portfolio"),
    FundInfo(code="NINETY1EQ", name="Ninety One Equity Fund"),
    FundInfo(code="NINETY1BAL", name="Ninety One Balanced Fund"),
    FundInfo(code="PSGBAL", name="PSG Balanced Fund"),
    FundInfo(code="PSGEQUITY", name="PSG Equity Fund"),
    FundInfo(code="PRUDBAL", name="Prudential Balanced Fund"),
    FundInfo(code="PRUDEQUITY", name="Prudential Equity Fund"),
    FundInfo(code="OLDMUTBAL", name="Old Mutual Balanced Fund"),
    FundInfo(code="OLDMUTEQUITY", name="Old Mutual Equity Fund"),
    FundInfo(code="SBSABAL", name="SIM Balanced Fund"),
    FundInfo(code="MARIBAL", name="Marriott Balanced Fund"),
    FundInfo(code="SYGBAL", name="Sygnia Balanced Fund"),
]


def get_fund_holdings(fund_code: str) -> list[FundHolding]:
    """
    Scrape profiledata.co.za for JSE equity holdings of a fund.
    Skips non-equity holdings (bonds, cash, offshore — no JSE ticker link).
    Returns [] on any failure — caller must treat as best-effort.
    """
    if not fund_code or not fund_code.strip():
        return []

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(
                PROFILEDATA_HOLDINGS_URL,
                params={"c": fund_code.strip()},
                headers={"User-Agent": "Mozilla/5.0 (compatible; Calenda/1.0)"},
                follow_redirects=True,
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if table is None:
            logger.warning(
                "fund_holdings: no table found for %s — HTML may have changed or fund code invalid",
                fund_code,
            )
            return []

        holdings: list[FundHolding] = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            # Security column (first cell) has <a href="...?c=NPN"> for JSE-listed holdings.
            # Bond, cash, and offshore rows have no anchor link — skip them.
            security_cell = cells[0]
            ticker_link = security_cell.find("a", href=lambda h: h and "?c=" in h)
            if ticker_link is None:
                continue

            href = ticker_link.get("href", "")
            match = re.search(r"[?&]c=([A-Z0-9]+)", href)
            if match is None:
                continue

            ticker = match.group(1)
            company_name = ticker_link.get_text(strip=True)

            # % Fund is typically the last column
            weight_str = cells[-1].get_text(strip=True).replace("%", "").strip()
            try:
                weight_pct = float(weight_str)
            except ValueError:
                continue

            if weight_pct <= 0:
                continue

            holdings.append(
                FundHolding(
                    ticker=ticker,
                    company_name=company_name,
                    weight_pct=weight_pct,
                )
            )

        if not holdings:
            logger.warning(
                "fund_holdings: 0 equity holdings parsed for %s — "
                "verify table structure and that fund code is correct",
                fund_code,
            )

        return holdings

    except Exception as exc:
        logger.warning("fund_holdings scraper failed for %s: %s", fund_code, exc)
        return []


def search_funds(query: str) -> list[FundInfo]:
    """
    Search SA unit trusts by name or code.
    Filters the curated SA_FUND_FALLBACK list — no external request required.
    Returns up to 10 results, sorted by name.
    """
    if len(query) < 2:
        return []
    q = query.lower().strip()
    results = [
        f for f in SA_FUND_FALLBACK
        if q in f.name.lower() or q in f.code.lower()
    ]
    return sorted(results, key=lambda f: f.name)[:10]

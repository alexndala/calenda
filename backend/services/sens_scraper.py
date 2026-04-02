"""
SENS scraper: extract near-term JSE earnings dates from the JSE SENS public page.
Best-effort — returns {} on any failure. yfinance calendar remains the primary source.

WARNING: HTML scraper — JSE website redesigns will break this.
Monitor with: logger.warning("SENS returned 0 dates") after each call.

Pre-ship verification required: manually check jse.co.za/current-companies/sens for
2-3 real announcements (e.g. NPN or SBK). Confirm (a) the page has a <table> structure,
(b) the dateFrom/dateTo/category params filter correctly (if not, post-filter instead),
(c) the EARNINGS_KEYWORDS set matches real announcement titles.
"""

import logging
from datetime import date, timedelta

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SENS_URL = "https://www.jse.co.za/current-companies/sens"

# Subject-line keywords that indicate a financial results announcement.
# Matched case-insensitively against the announcement subject field.
EARNINGS_KEYWORDS = {
    "preliminary results",
    "condensed financial results",
    "trading statement",
    "provisional results",
    "financial results",
}


def get_jse_earnings_dates(tickers: list[str]) -> dict[str, date]:
    """
    Scrape SENS for earnings announcements for given JSE tickers (near-term, ≤30 days).

    Returns {ticker_with_JO_suffix: announcement_date} for matched tickers.
    Returns {} on any failure — caller must treat as best-effort supplement.

    Sync: called from get_earnings_events() inside asyncio.to_thread.
    """
    if not tickers:
        return {}

    # SENS uses short codes (NPN), not yfinance-style tickers (NPN.JO).
    code_to_ticker = {t.replace(".JO", ""): t for t in tickers if t.endswith(".JO")}
    target_codes = set(code_to_ticker.keys())
    if not target_codes:
        return {}

    results: dict[str, date] = {}

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                SENS_URL,
                params={
                    "dateFrom": date.today().isoformat(),
                    "dateTo": (date.today() + timedelta(days=30)).isoformat(),
                    "category": "Financial Results",
                },
                headers={"User-Agent": "Mozilla/5.0 (compatible; Calenda/1.0)"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Expected structure: <table> with rows [date | issuer_code | subject ...]
        # If JSE redesigns the page, this will return {} and log a warning.
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            ann_date_str = cells[0].get_text(strip=True)
            issuer_code = cells[1].get_text(strip=True).upper()
            subject = cells[2].get_text(strip=True).lower()

            if issuer_code not in target_codes:
                continue
            if not any(kw in subject for kw in EARNINGS_KEYWORDS):
                continue

            try:
                ann_date = date.fromisoformat(ann_date_str[:10])
                results[code_to_ticker[issuer_code]] = ann_date
            except (ValueError, KeyError):
                continue

    except Exception as exc:
        logger.warning("SENS scraper failed: %s — falling back to yfinance only", exc)
        return {}

    if not results:
        logger.warning(
            "SENS scraper returned 0 dates for %d tickers — "
            "HTML structure may have changed or no announcements in 30-day window",
            len(target_codes),
        )

    return results


def get_jse_director_dealings(
    tickers: list[str], lookback_days: int = 90
) -> dict[str, list]:
    """
    Scrape SENS Director Dealings category for given JSE tickers.
    Returns {ticker: [InsiderTransaction, ...]} for matched tickers.
    Returns {} on any failure — caller must treat as best-effort.

    WARNING: HTML scraper — JSE website redesigns will break this.
    Pre-ship verification required: check jse.co.za/current-companies/sens with
    category filter to confirm the exact category param value for director dealings.
    """
    if not tickers:
        return {}

    from models import InsiderTransaction  # avoid circular import

    code_to_ticker = {t.replace(".JO", ""): t for t in tickers if t.endswith(".JO")}
    target_codes = set(code_to_ticker.keys())
    if not target_codes:
        return {}

    results: dict[str, list] = {}
    start_date = date.today() - timedelta(days=lookback_days)

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                SENS_URL,
                params={
                    "dateFrom": start_date.isoformat(),
                    "dateTo": date.today().isoformat(),
                    "category": "Director Dealings",  # VERIFY: check live SENS page
                },
                headers={"User-Agent": "Mozilla/5.0 (compatible; Calenda/1.0)"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            ann_date_str = cells[0].get_text(strip=True)
            issuer_code = cells[1].get_text(strip=True).upper()
            subject = cells[2].get_text(strip=True)

            if issuer_code not in target_codes:
                continue

            try:
                ann_date = date.fromisoformat(ann_date_str[:10])
            except ValueError:
                continue

            # Parse transaction type from subject line
            subject_lower = subject.lower()
            if any(kw in subject_lower for kw in ("purchase", "acquisition", "bought")):
                trans_type = "Acquisition"
            elif any(kw in subject_lower for kw in ("disposal", "sale", "sold")):
                trans_type = "Disposal"
            else:
                trans_type = "Unknown"

            ticker = code_to_ticker[issuer_code]
            if ticker not in results:
                results[ticker] = []
            results[ticker].append(InsiderTransaction(
                date=ann_date,
                name="Director",    # SENS subject doesn't reliably include name
                role="Director",
                transaction_type=trans_type,
            ))

    except Exception as exc:
        logger.warning("SENS director dealings failed: %s", exc)
        return {}

    return results

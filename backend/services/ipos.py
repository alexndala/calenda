"""
IPO calendar service using Alpha Vantage free tier.
25 requests/day cap — data is cached for 72h and synced in background once per day.
"""

import logging
import os
from datetime import date

import httpx

from config import ipo_enabled
from models import CalendarEvent, EventType

logger = logging.getLogger(__name__)

AV_IPO_URL = "https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey={key}"


async def fetch_ipo_calendar() -> list[dict]:
    """Fetch raw IPO calendar from Alpha Vantage. Returns list of raw dicts."""
    av_key = os.getenv("ALPHA_VANTAGE_KEY", "").strip()
    if not ipo_enabled() or not av_key:
        logger.info("Alpha Vantage IPO source disabled")
        return []

    url = AV_IPO_URL.format(key=av_key)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            # Alpha Vantage returns CSV for IPO_CALENDAR
            lines = resp.text.strip().splitlines()
            if len(lines) < 2:
                return []
            headers = [h.strip() for h in lines[0].split(",")]
            rows = []
            for line in lines[1:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == len(headers):
                    rows.append(dict(zip(headers, parts)))
            return rows
    except Exception as exc:
        logger.error("Alpha Vantage IPO fetch failed: %s", exc)
        return []


def parse_ipo_events(
    raw_rows: list[dict], start: date, end: date
) -> list[CalendarEvent]:
    events = []
    for row in raw_rows:
        try:
            ipo_date_str = row.get("ipoDate") or row.get("date") or ""
            if not ipo_date_str:
                continue
            ipo_date = date.fromisoformat(ipo_date_str)
            if not (start <= ipo_date <= end):
                continue

            ticker = row.get("symbol") or row.get("ticker") or "UNKNOWN"
            company = row.get("name") or row.get("company") or ticker

            price_range = row.get("priceRange") or row.get("price_range") or ""
            shares = row.get("shares") or row.get("numberOfShares") or ""

            events.append(
                CalendarEvent(
                    id=f"ipo-{ticker}-{ipo_date}",
                    ticker=ticker,
                    company_name=company,
                    date=ipo_date,
                    type=EventType.IPO,
                    details={
                        "price_range": price_range,
                        "shares": shares,
                        "source": "alphavantage",
                    },
                )
            )
        except Exception as exc:
            logger.warning("IPO row parse failed: %s — %s", row, exc)
            continue
    return events

"""
Events router: lightweight event list and on-demand detail panel.
"""
import asyncio
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from cache import NOT_FOUND_SENTINEL, detail_cache, events_cache
from models import CalendarEvent, EarningsDetail
from services.dividends import get_dividend_events
from services.earnings import get_earnings_detail, get_earnings_events
from services.indices import (
    get_eurostoxx50_tickers,
    get_ftse100_tickers,
    get_ftse_china_a50_tickers,
    get_jse_allshare_tickers,
    get_jse_top40_tickers,
    get_nasdaq100_tickers,
    get_sp500_tickers,
    get_topix_tickers,
)
from services.ipos import fetch_ipo_calendar, parse_ipo_events
from services.splits import get_split_events

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

VALID_TYPES = {"earnings", "dividend", "split", "ipo"}
VALID_INDICES = {
    "sp500", "nasdaq100",
    "jse_top40", "jse_allshare",
    "topix", "ftse100", "ftse_china_a50", "eurostoxx50",
    "custom",
}


_INDEX_GETTERS = {
    "sp500": get_sp500_tickers,
    "nasdaq100": get_nasdaq100_tickers,
    "jse_top40": get_jse_top40_tickers,
    "jse_allshare": get_jse_allshare_tickers,
    "topix": get_topix_tickers,
    "ftse100": get_ftse100_tickers,
    "ftse_china_a50": get_ftse_china_a50_tickers,
    "eurostoxx50": get_eurostoxx50_tickers,
}


def _get_tickers_for_index(index: str, custom_tickers: list[str]) -> list[str]:
    getter = _INDEX_GETTERS.get(index)
    if getter is None:
        return custom_tickers
    cache_key = f"__{index}_tickers__"
    cached = events_cache.get(cache_key)
    if cached and cached != NOT_FOUND_SENTINEL:
        return cached
    tickers = getter()
    events_cache.set(cache_key, tickers, ttl=86400)
    return tickers


@router.get("/api/events", response_model=list[CalendarEvent])
@limiter.limit("60/minute")
async def get_events(
    request: Request,
    start: date,
    end: date,
    index: str = "sp500",
    tickers: Optional[str] = None,
    types: Optional[str] = "earnings,dividend",
):
    if index not in VALID_INDICES:
        raise HTTPException(status_code=400, detail=f"Invalid index: {index}")

    requested_types = {t.strip() for t in (types or "earnings,dividend").split(",")}
    invalid = requested_types - VALID_TYPES
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid types: {invalid}")

    custom = [t.strip().upper() for t in (tickers or "").split(",") if t.strip()]
    ticker_list = _get_tickers_for_index(index, custom)

    cache_key = f"events:{index}:{','.join(sorted(ticker_list[:5]))}:{start}:{end}:{','.join(sorted(requested_types))}"
    cached = events_cache.get(cache_key)
    if cached and cached != NOT_FOUND_SENTINEL:
        return cached

    tasks = []
    if "earnings" in requested_types:
        tasks.append(asyncio.to_thread(get_earnings_events, ticker_list, start, end))
    if "dividend" in requested_types:
        tasks.append(asyncio.to_thread(get_dividend_events, ticker_list, start, end))
    if "split" in requested_types:
        tasks.append(asyncio.to_thread(get_split_events, ticker_list, start, end))
    if "ipo" in requested_types:
        raw = await fetch_ipo_calendar()
        tasks.append(asyncio.to_thread(parse_ipo_events, raw, start, end))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_events: list[CalendarEvent] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("Event fetch task failed: %s", result)
            continue
        all_events.extend(result)

    all_events.sort(key=lambda e: e.date)
    events_cache.set(cache_key, all_events)
    return all_events


@router.get("/api/events/{ticker}/detail")
@limiter.limit("30/minute")
async def get_event_detail(request: Request, ticker: str):
    ticker = ticker.upper()
    cache_key = f"detail:{ticker}"

    if detail_cache.is_not_found(cache_key):
        raise HTTPException(status_code=404, detail=f"No earnings data for {ticker}")

    cached = detail_cache.get(cache_key)
    if cached is not None:
        return cached

    detail = await asyncio.to_thread(get_earnings_detail, ticker)
    if detail is None:
        detail_cache.set_not_found(cache_key)
        raise HTTPException(status_code=404, detail=f"No earnings data for {ticker}")

    detail_cache.set(cache_key, detail.model_dump())
    return detail.model_dump()

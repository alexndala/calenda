"""Ticker search and index constituent endpoints."""
from __future__ import annotations
import logging
import re
from typing import Optional

import yfinance as yf
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

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

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

TICKER_RE = re.compile(r"^[A-Z]{1,10}$", re.IGNORECASE)


@router.get("/api/tickers/search")
@limiter.limit("30/minute")
async def search_tickers(request: Request, q: str):
    """Autocomplete: returns matching tickers with company names."""
    q = q.strip().upper()
    if not q or len(q) > 10 or not TICKER_RE.match(q):
        return []
    try:
        results = yf.Search(q, max_results=10)
        quotes = results.quotes if hasattr(results, "quotes") else []
        return [
            {"ticker": item.get("symbol", ""), "name": item.get("longname") or item.get("shortname") or ""}
            for item in quotes
            if item.get("quoteType") in ("EQUITY", "ETF")
        ]
    except Exception as exc:
        logger.warning("Ticker search failed for %s: %s", q, exc)
        return []


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


@router.get("/api/indices/{index}")
@limiter.limit("10/minute")
async def get_index_tickers(request: Request, index: str):
    """Return ticker list for a named index."""
    getter = _INDEX_GETTERS.get(index)
    if getter is None:
        raise HTTPException(status_code=400, detail=f"Unknown index: {index}")
    return getter()

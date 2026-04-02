"""
Funds router: SA unit trust look-through earnings exposure.
  GET  /api/funds/search?q={query}    → list[FundInfo]
  GET  /api/funds/{code}/holdings     → list[FundHolding]
  POST /api/funds/analyze             → list[FundLookThroughRow]
"""
import asyncio
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from cache import events_cache
from models import FundHolding, FundInfo, FundLookThroughRow, FundPosition
from services.earnings import get_earnings_events
from services.fund_holdings import get_fund_holdings, search_funds

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/api/funds/search", response_model=list[FundInfo])
@limiter.limit("30/minute")
async def fund_search(request: Request, q: str = ""):
    """Search SA unit trusts by name or code."""
    cache_key = f"fund_search:{q.lower().strip()}"
    cached = events_cache.get(cache_key)
    if cached is not None:
        return cached
    results = search_funds(q)
    events_cache.set(cache_key, results, ttl=3600)
    return results


@router.get("/api/funds/{code}/holdings", response_model=list[FundHolding])
@limiter.limit("30/minute")
async def fund_holdings(request: Request, code: str):
    """Get JSE equity holdings for a fund. 24h cache — holdings update monthly."""
    cache_key = f"fund_holdings:{code.upper()}"
    cached = events_cache.get(cache_key)
    if cached is not None:
        return cached
    holdings = await asyncio.to_thread(get_fund_holdings, code)
    events_cache.set(cache_key, holdings, ttl=86400)
    return holdings


@router.post("/api/funds/analyze", response_model=list[FundLookThroughRow])
@limiter.limit("30/minute")
async def analyze_funds(request: Request, positions: list[FundPosition]):
    """
    Compute look-through earnings exposure across SA unit trust holdings.
    Aggregates effective weights (adviser_alloc × holding_weight / 100),
    sums if same JSE stock appears in multiple funds, fetches next earnings
    dates, and returns rows sorted by effective_weight_pct descending.
    """
    if not positions:
        return []

    # Aggregate effective weights across all funds
    # {ticker_jse: {effective_weight_pct, company_name, fund_sources}}
    ticker_exposure: dict[str, dict] = {}

    for pos in positions:
        if pos.allocation_pct <= 0:
            continue

        cache_key = f"fund_holdings:{pos.fund_code.upper()}"
        holdings: list[FundHolding] | None = events_cache.get(cache_key)
        if holdings is None:
            holdings = await asyncio.to_thread(get_fund_holdings, pos.fund_code)
            events_cache.set(cache_key, holdings, ttl=86400)

        for holding in holdings:
            effective = round(pos.allocation_pct * holding.weight_pct / 100, 4)
            ticker_jse = f"{holding.ticker}.JO"

            if ticker_jse not in ticker_exposure:
                ticker_exposure[ticker_jse] = {
                    "effective_weight_pct": 0.0,
                    "company_name": holding.company_name,
                    "fund_sources": [],
                }

            ticker_exposure[ticker_jse]["effective_weight_pct"] += effective
            if pos.fund_name not in ticker_exposure[ticker_jse]["fund_sources"]:
                ticker_exposure[ticker_jse]["fund_sources"].append(pos.fund_name)

    if not ticker_exposure:
        return []

    # Fetch earnings dates for all look-through tickers (reuse existing service)
    tickers = list(ticker_exposure.keys())
    today = date.today()
    events = await asyncio.to_thread(
        get_earnings_events,
        tickers,
        today,
        today + timedelta(days=90),
    )
    earnings_by_ticker = {e.ticker: e.date for e in events}

    rows: list[FundLookThroughRow] = []
    for ticker_jse, data in ticker_exposure.items():
        next_date = earnings_by_ticker.get(ticker_jse)
        days = (next_date - today).days if next_date else None
        fund_source = ", ".join(data["fund_sources"])

        rows.append(
            FundLookThroughRow(
                ticker=ticker_jse,
                company_name=data["company_name"],
                effective_weight_pct=round(data["effective_weight_pct"], 3),
                fund_source=fund_source,
                next_earnings_date=next_date,
                days_to_earnings=days,
            )
        )

    rows.sort(key=lambda r: r.effective_weight_pct, reverse=True)
    return rows

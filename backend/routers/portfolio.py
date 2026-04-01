"""Portfolio risk analysis endpoint."""
from __future__ import annotations
import re

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models import PortfolioPosition, PortfolioRiskRow
from services.portfolio import TICKER_RE, analyze_portfolio

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

MAX_POSITIONS = 200


class PortfolioRequest:
    def __init__(self, positions: list[PortfolioPosition]):
        self.positions = positions


from pydantic import BaseModel


class PortfolioAnalyzeRequest(BaseModel):
    positions: list[PortfolioPosition]


@router.post("/api/portfolio/analyze", response_model=list[PortfolioRiskRow])
@limiter.limit("10/minute")
async def analyze_portfolio_endpoint(
    request: Request,
    body: PortfolioAnalyzeRequest,
):
    """
    Analyze portfolio risk: expected dollar swing per position around earnings.
    Returns rows sorted by expected_dollar_swing DESC.
    """
    positions = body.positions
    if not positions:
        return []
    if len(positions) > MAX_POSITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_POSITIONS} positions per request",
        )

    # Validate and deduplicate tickers
    seen: set[str] = set()
    clean: list[PortfolioPosition] = []
    for pos in positions:
        ticker = pos.ticker.upper().strip()
        if not TICKER_RE.match(ticker):
            continue  # skip invalid tickers silently
        if ticker in seen:
            continue
        seen.add(ticker)
        clean.append(PortfolioPosition(ticker=ticker, shares=pos.shares, avg_cost=pos.avg_cost))

    if not clean:
        raise HTTPException(status_code=400, detail="No valid tickers provided")

    return await analyze_portfolio(clean)

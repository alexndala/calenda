"""
Calenda — Earnings & Corporate Actions Research Cockpit
FastAPI backend entry point.
"""
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from cache import events_cache
from routers.events import router as events_router
from routers.funds import router as funds_router
from routers.portfolio import router as portfolio_router
from routers.tickers import router as tickers_router
from services.earnings import get_earnings_events
from services.indices import get_sp500_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


async def _warm_cache() -> None:
    """
    Pre-warm S&P 500 earnings for current + next month.
    Batches 50 tickers at a time with semaphore to avoid hammering Yahoo.
    """
    logger.info("Cache pre-warm starting...")
    tickers = get_sp500_tickers()
    today = date.today()
    start = today.replace(day=1)
    end = (today.replace(day=1) + timedelta(days=62)).replace(day=1) - timedelta(days=1)

    sem = asyncio.Semaphore(10)
    completed = 0

    async def fetch_chunk(chunk: list[str]) -> None:
        nonlocal completed
        async with sem:
            events = await asyncio.to_thread(get_earnings_events, chunk, start, end)
            completed += len(chunk)
            logger.debug("Pre-warm: %d/%d tickers done", completed, len(tickers))

    chunks = [tickers[i : i + 50] for i in range(0, len(tickers), 50)]
    for chunk in chunks:
        await fetch_chunk(chunk)
        await asyncio.sleep(0.5)

    logger.info("Cache pre-warm complete — %d tickers processed", len(tickers))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background pre-warm — don't await, fire and forget
    asyncio.create_task(_warm_cache())
    yield


app = FastAPI(
    title="Calenda API",
    description="Earnings & Corporate Actions Research Cockpit",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_extra = os.environ.get("CORS_ORIGINS", "").split(",")
_origins = _default_origins + [o.strip() for o in _extra if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)
app.include_router(funds_router)
app.include_router(tickers_router)
app.include_router(portfolio_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

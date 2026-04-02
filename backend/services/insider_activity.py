"""
Insider activity service: director dealings (JSE via SENS) and insider
transactions (US via OpenBB / SEC EDGAR Form 4).
Best-effort — returns [] on any failure. Never raises to caller.

US: wraps OpenBB `obb.equity.ownership.insider_trading()` which hits SEC EDGAR.
    Free, no API key required. Lazy import — openbb is large (~200MB).
JSE: wraps get_jse_director_dealings() from sens_scraper — same HTML scraper
    pattern as earnings, different SENS category.
"""

import logging
from datetime import date

from models import InsiderTransaction
from services.sens_scraper import get_jse_director_dealings

logger = logging.getLogger(__name__)


def get_insider_activity(ticker: str, lookback_days: int = 90) -> list[InsiderTransaction]:
    """
    Fetch insider transactions for a single ticker.
    JSE tickers (.JO suffix): SENS Director Dealings.
    US tickers: OpenBB SEC EDGAR Form 4.
    Returns [] on any failure.
    """
    if ticker.endswith(".JO"):
        return _get_jse_insider_activity(ticker, lookback_days)
    return _get_us_insider_activity(ticker, lookback_days)


def _get_us_insider_activity(ticker: str, lookback_days: int) -> list[InsiderTransaction]:
    try:
        from openbb import obb  # lazy import — openbb is large

        result = obb.equity.ownership.insider_trading(symbol=ticker, limit=20)
        if not result or not result.results:
            return []

        transactions: list[InsiderTransaction] = []
        cutoff = date.today().__class__.fromordinal(
            date.today().toordinal() - lookback_days
        )

        for item in result.results:
            raw_date = getattr(item, "filing_date", None) or getattr(item, "transaction_date", None)
            if raw_date is None:
                continue
            trans_date = raw_date.date() if hasattr(raw_date, "date") else raw_date
            if trans_date < cutoff:
                continue

            # SEC transaction codes: P=Purchase, A=Award, S=Sale, D=Disposition
            code = str(getattr(item, "transaction_code", "") or "").upper()
            if code in ("P", "A"):
                trans_type = "Buy"
            elif code in ("S", "D"):
                trans_type = "Sell"
            else:
                trans_type = "Unknown"

            shares_raw = getattr(item, "securities_transacted", None)
            price_raw = getattr(item, "price", None)
            value_raw = getattr(item, "value", None)

            transactions.append(InsiderTransaction(
                date=trans_date,
                name=str(getattr(item, "reporting_name", "Unknown") or "Unknown"),
                role=str(getattr(item, "reporting_relationship", "Insider") or "Insider"),
                transaction_type=trans_type,
                shares=int(shares_raw) if shares_raw is not None else None,
                price_per_share=float(price_raw) if price_raw is not None else None,
                value=float(value_raw) if value_raw is not None else None,
            ))

        return transactions

    except Exception as exc:
        logger.warning("US insider activity failed for %s: %s", ticker, exc)
        return []


def _get_jse_insider_activity(ticker: str, lookback_days: int) -> list[InsiderTransaction]:
    try:
        dealings = get_jse_director_dealings([ticker], lookback_days=lookback_days)
        return dealings.get(ticker, [])
    except Exception as exc:
        logger.warning("JSE director dealings failed for %s: %s", ticker, exc)
        return []

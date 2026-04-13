"""Dividend events: upcoming ex-dividend dates and amounts."""
import logging
import re
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf
from pandas.tseries.offsets import BDay

from models import CalendarEvent, EventType

logger = logging.getLogger(__name__)
# Allow 1-5 uppercase letters + optional 1-2 letter exchange suffix (.JO, .L, .DE, etc.)
TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _parse_date(val) -> Optional[date]:
    """Parse a date from a Unix timestamp (int/float) or pd.Timestamp."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return date.fromtimestamp(val)
        return pd.Timestamp(val).date()
    except Exception:
        return None


def _last_trading_date(ex_date: date) -> date:
    """Return the last day to buy shares and still qualify for the dividend (ex_date - 1 business day)."""
    return (pd.Timestamp(ex_date) - BDay(1)).date()


def get_dividend_events(tickers: list[str], start: date, end: date) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []

    for ticker in tickers:
        if not TICKER_RE.match(ticker):
            continue
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
            company_name = info.get("longName") or info.get("shortName") or ticker
            market_cap = _safe_float(info.get("marketCap"))
            currency: Optional[str] = info.get("currency")

            # Try next ex-dividend date from info
            next_div_date: Optional[date] = _parse_date(info.get("exDividendDate"))

            # Also check historical dividends series for upcoming entries
            try:
                divs = t.dividends
                if divs is not None and not divs.empty:
                    future_divs = divs[divs.index.date >= start]
                    if not future_divs.empty:
                        candidate = future_divs.index[0].date()
                        if next_div_date is None or candidate < next_div_date:
                            next_div_date = candidate
            except Exception:
                pass

            if next_div_date is None or not (start <= next_div_date <= end):
                continue

            dividend_amount = _safe_float(info.get("lastDividendValue"))
            last_trading_date = _last_trading_date(next_div_date)

            # Try to get payment date from the ticker calendar
            payment_date: Optional[date] = None
            try:
                cal = t.calendar
                raw_pay: object = None
                if isinstance(cal, dict):
                    raw_pay = cal.get("Dividend Date")
                elif cal is not None and hasattr(cal, "to_dict"):
                    cal_dict = cal.to_dict()
                    raw_pay = cal_dict.get("Dividend Date", {}).get(0)
                payment_date = _parse_date(raw_pay)
            except Exception:
                pass

            events.append(
                CalendarEvent(
                    id=f"dividend-{ticker}-{next_div_date}",
                    ticker=ticker,
                    company_name=company_name,
                    date=next_div_date,
                    type=EventType.DIVIDEND,
                    market_cap=market_cap,
                    details={
                        "amount": dividend_amount,
                        "currency": currency,
                        "payment_date": payment_date.isoformat() if payment_date else None,
                        "last_trading_date": last_trading_date.isoformat(),
                        # yfinance provides no ordinary/special split — ordinary_amount mirrors amount
                        "ordinary_amount": dividend_amount,
                        "special_amount": None,
                    },
                )
            )
        except Exception as exc:
            logger.warning("Dividend fetch failed for %s: %s", ticker, exc)
            continue

    return events

"""Unit tests: Pydantic model serialization."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from models import CalendarEvent, EarningsDetail, EventType


def test_calendar_event_serialization():
    e = CalendarEvent(
        id="earnings-AAPL-2026-04-30",
        ticker="AAPL",
        company_name="Apple Inc.",
        date=date(2026, 4, 30),
        type=EventType.EARNINGS,
        market_cap=3_000_000_000_000,
        timing="AMC",
        details={"eps_estimate": 1.62},
    )
    d = e.model_dump()
    assert d["ticker"] == "AAPL"
    assert d["type"] == "earnings"
    assert d["timing"] == "AMC"
    assert d["details"]["eps_estimate"] == 1.62


def test_calendar_event_dividend():
    e = CalendarEvent(
        id="dividend-MSFT-2026-05-15",
        ticker="MSFT",
        company_name="Microsoft Corp.",
        date=date(2026, 5, 15),
        type=EventType.DIVIDEND,
        details={"amount": 0.75},
    )
    assert e.market_cap is None
    assert e.timing is None


def test_earnings_detail_defaults():
    d = EarningsDetail()
    assert d.beat_miss_history == []
    assert d.eps_beat_rate is None
    assert d.insufficient_history is False


def test_earnings_detail_beat_rates():
    d = EarningsDetail(
        eps_beat_rate=0.875,
        rev_beat_rate=0.625,
        beat_miss_history=[
            {"quarter": "2025Q4", "eps_actual": 2.0, "eps_estimate": 1.8, "eps_beat": True,
             "rev_actual": 100e9, "rev_estimate": 98e9, "rev_beat": True}
        ],
        eps_trend=[1.2, 1.4, 1.6, 1.8, 2.0, 2.2],
    )
    assert d.eps_beat_rate == 0.875
    assert len(d.eps_trend) == 6


def test_earnings_detail_insufficient_history():
    d = EarningsDetail(insufficient_history=True, beat_miss_history=[
        {"quarter": "2025Q4", "eps_actual": 1.0, "eps_estimate": 0.9, "eps_beat": True,
         "rev_actual": None, "rev_estimate": None, "rev_beat": None}
    ])
    assert d.insufficient_history is True

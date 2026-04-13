"""Runtime data-source routing configuration."""

import os


def _env(name: str, default: str) -> str:
    val = os.getenv(name, default)
    return (val or default).strip().lower()


def get_price_provider() -> str:
    return _env("PRICE_PROVIDER", "yfinance")


def get_fundamentals_provider() -> str:
    return _env("FUNDAMENTALS_PROVIDER", "openbb")


def get_ipo_provider() -> str:
    return _env("IPO_PROVIDER", "alphavantage")


def alpha_vantage_key_present() -> bool:
    return bool((os.getenv("ALPHA_VANTAGE_KEY", "") or "").strip())


def openbb_fundamentals_enabled() -> bool:
    return get_fundamentals_provider() == "openbb"


def ipo_enabled() -> bool:
    return get_ipo_provider() == "alphavantage" and alpha_vantage_key_present()


def source_health() -> dict:
    return {
        "price": get_price_provider(),
        "fundamentals": get_fundamentals_provider(),
        "ipo": get_ipo_provider(),
        "openbb_fundamentals_enabled": openbb_fundamentals_enabled(),
        "alpha_vantage_key_present": alpha_vantage_key_present(),
        "ipo_enabled": ipo_enabled(),
    }

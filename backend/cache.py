"""
TTL cache with market-session-aware expiry.

During live market hours (9:30am–4:00pm ET, Mon–Fri), events expire quickly (5 min).
Outside market hours, cache is valid until next market open — no new data arrives anyway.
"""
from __future__ import annotations
import time
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

import pytz

ET = pytz.timezone("America/New_York")
NOT_FOUND_SENTINEL = "__not_found__"


def _market_open_today(now_et: datetime) -> Optional[datetime]:
    """Return today's market open as a timezone-aware datetime, or None if today is not a trading day."""
    if now_et.weekday() >= 5:  # Sat=5, Sun=6
        return None
    return now_et.replace(hour=9, minute=30, second=0, microsecond=0)


def _next_market_open(now_et: datetime) -> datetime:
    """Return the next market open datetime (Mon–Fri 9:30am ET)."""
    candidate = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    if candidate <= now_et:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def get_cache_ttl_seconds() -> int:
    """Return appropriate TTL in seconds based on current market session."""
    now_et = datetime.now(ET)
    open_today = _market_open_today(now_et)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

    if open_today and open_today <= now_et <= market_close:
        # Live session — refresh every 5 minutes
        return 300

    # Outside market hours — cache until next open
    next_open = _next_market_open(now_et)
    seconds_until_open = int((next_open - now_et).total_seconds())
    # Minimum 5 min so we don't cache for 0 seconds right at open
    return max(seconds_until_open, 300)


class TTLCache:
    """Thread-safe TTL cache. Supports "not found" sentinels (cached for 24h)."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Any:
        """Return cached value, or None if missing/expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache value with given TTL (seconds). Defaults to market-session TTL."""
        if ttl is None:
            ttl = get_cache_ttl_seconds()
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def set_not_found(self, key: str) -> None:
        """Cache a 'not found' sentinel for 24h to avoid repeated misses."""
        self.set(key, NOT_FOUND_SENTINEL, ttl=86400)

    def is_not_found(self, key: str) -> bool:
        val = self.get(key)
        return val == NOT_FOUND_SENTINEL

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# Singleton cache instances
events_cache = TTLCache()
detail_cache = TTLCache()
index_cache = TTLCache()  # 24h TTL always

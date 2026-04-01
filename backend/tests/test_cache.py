"""Unit tests: TTL cache behavior."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cache import TTLCache, NOT_FOUND_SENTINEL


def test_basic_set_get():
    c = TTLCache()
    c.set("key", "value", ttl=60)
    assert c.get("key") == "value"


def test_expiry():
    c = TTLCache()
    c.set("key", "value", ttl=1)
    time.sleep(1.1)
    assert c.get("key") is None


def test_not_found_sentinel():
    c = TTLCache()
    c.set_not_found("missing-ticker")
    assert c.is_not_found("missing-ticker")
    assert c.get("missing-ticker") == NOT_FOUND_SENTINEL


def test_invalidate():
    c = TTLCache()
    c.set("key", "value", ttl=60)
    c.invalidate("key")
    assert c.get("key") is None


def test_clear():
    c = TTLCache()
    c.set("a", 1, ttl=60)
    c.set("b", 2, ttl=60)
    c.clear()
    assert c.get("a") is None
    assert c.get("b") is None


def test_missing_key_returns_none():
    c = TTLCache()
    assert c.get("nonexistent") is None


def test_overwrite():
    c = TTLCache()
    c.set("key", "v1", ttl=60)
    c.set("key", "v2", ttl=60)
    assert c.get("key") == "v2"

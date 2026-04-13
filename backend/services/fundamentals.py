"""
OpenBB fundamentals adapter used for on-demand earnings detail endpoints.

Best-effort only: returns {} on any failure and never raises.
"""

import logging
import os
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_OPENBB_IMPORT_WARNED = False

_EPS_ESTIMATE_FIELDS = (
    "eps_estimate",
    "eps_mean",
    "estimated_eps",
    "estimated_eps_avg",
    "eps_avg",
)
_REVENUE_ESTIMATE_FIELDS = (
    "revenue_estimate",
    "revenue_mean",
    "estimated_revenue",
    "estimated_revenue_avg",
    "revenue_avg",
)
_ANALYST_COUNT_FIELDS = (
    "analyst_count",
    "number_of_analysts",
    "num_analysts",
)

_EPS_ACTUAL_FIELDS = (
    "eps_actual",
    "reported_eps",
    "eps",
    "actual_eps",
)
_REVENUE_ACTUAL_FIELDS = (
    "revenue_actual",
    "reported_revenue",
    "actual_revenue",
    "revenue",
)

_DATE_FIELDS = (
    "date",
    "report_date",
    "fiscal_date_ending",
    "period_ending",
    "fiscal_period_end",
)


def _safe_float(val: Any) -> Optional[float]:
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    try:
        i = int(float(val))
        return i if i >= 0 else None
    except (TypeError, ValueError):
        return None


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return row

    for fn_name in ("model_dump", "dict"):
        fn = getattr(row, fn_name, None)
        if callable(fn):
            try:
                data = fn()
                if isinstance(data, dict):
                    return data
            except Exception:
                pass

    out: dict[str, Any] = {}
    for key in dir(row):
        if key.startswith("_"):
            continue
        try:
            val = getattr(row, key)
        except Exception:
            continue
        if callable(val):
            continue
        out[key] = val
    return out


def _pick_first(data: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        val = data.get(field)
        if val is not None and val != "":
            return val
    return None


def _parse_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return pd.Timestamp(val).date()
    except Exception:
        return None


def _extract_results(result: Any) -> list[Any]:
    if result is None:
        return []
    if isinstance(result, list):
        return result

    rows = getattr(result, "results", None)
    if rows is None:
        return []
    if isinstance(rows, list):
        return rows
    try:
        return list(rows)
    except Exception:
        return []


def _call_openbb_endpoint(obb: Any, path: tuple[str, ...], ticker: str) -> list[Any]:
    target = obb
    for piece in path:
        target = getattr(target, piece, None)
        if target is None:
            return []

    if not callable(target):
        return []

    variants = (
        {"symbol": ticker, "limit": 12},
        {"symbol": ticker},
        {"ticker": ticker, "limit": 12},
        {"ticker": ticker},
    )
    for kwargs in variants:
        try:
            return _extract_results(target(**kwargs))
        except TypeError:
            continue
        except Exception:
            continue
    return []


def _get_upcoming_estimates(rows: list[Any]) -> dict[str, Any]:
    today = date.today()
    candidates: list[dict[str, Any]] = []

    for row in rows:
        data = _row_to_dict(row)
        eps = _safe_float(_pick_first(data, _EPS_ESTIMATE_FIELDS))
        revenue = _safe_float(_pick_first(data, _REVENUE_ESTIMATE_FIELDS))
        analysts = _safe_int(_pick_first(data, _ANALYST_COUNT_FIELDS))
        row_date = _parse_date(_pick_first(data, _DATE_FIELDS))

        if eps is None and revenue is None and analysts is None:
            continue
        candidates.append(
            {
                "date": row_date,
                "eps_estimate": eps,
                "revenue_estimate": revenue,
                "analyst_count": analysts,
            }
        )

    if not candidates:
        return {}

    dated = [c for c in candidates if c["date"] is not None]
    future = sorted([c for c in dated if c["date"] >= today], key=lambda c: c["date"])
    if future:
        return future[0]

    if dated:
        return sorted(dated, key=lambda c: c["date"], reverse=True)[0]

    return candidates[0]


def _get_beat_miss_history(rows: list[Any]) -> dict[str, Any]:
    parsed: list[dict[str, Any]] = []
    today = date.today()

    for row in rows:
        data = _row_to_dict(row)
        row_date = _parse_date(_pick_first(data, _DATE_FIELDS))
        if row_date is None or row_date > today:
            continue

        eps_actual = _safe_float(_pick_first(data, _EPS_ACTUAL_FIELDS))
        eps_estimate = _safe_float(_pick_first(data, _EPS_ESTIMATE_FIELDS))
        rev_actual = _safe_float(_pick_first(data, _REVENUE_ACTUAL_FIELDS))
        rev_estimate = _safe_float(_pick_first(data, _REVENUE_ESTIMATE_FIELDS))

        if eps_actual is None and rev_actual is None:
            continue

        parsed.append(
            {
                "date": row_date,
                "eps_actual": eps_actual,
                "eps_estimate": eps_estimate,
                "rev_actual": rev_actual,
                "rev_estimate": rev_estimate,
            }
        )

    if not parsed:
        return {}

    parsed.sort(key=lambda r: r["date"])
    last = parsed[-8:]

    beat_miss_history: list[dict[str, Any]] = []
    eps_trend: list[float] = []
    earnings_dates: list[date] = []
    eps_total = 0
    eps_beats = 0
    rev_total = 0
    rev_beats = 0

    for row in last:
        d = row["date"]
        eps_actual = row["eps_actual"]
        eps_estimate = row["eps_estimate"]
        rev_actual = row["rev_actual"]
        rev_estimate = row["rev_estimate"]

        eps_beat = None
        if eps_actual is not None and eps_estimate is not None:
            eps_total += 1
            eps_beat = eps_actual >= eps_estimate
            if eps_beat:
                eps_beats += 1

        rev_beat = None
        if rev_actual is not None and rev_estimate is not None:
            rev_total += 1
            rev_beat = rev_actual >= rev_estimate
            if rev_beat:
                rev_beats += 1

        if eps_actual is not None:
            eps_trend.append(eps_actual)
        earnings_dates.append(d)

        beat_miss_history.append(
            {
                "quarter": f"{d.year}-Q{(d.month - 1) // 3 + 1}",
                "eps_actual": eps_actual,
                "eps_estimate": eps_estimate,
                "eps_beat": eps_beat,
                "rev_actual": rev_actual,
                "rev_estimate": rev_estimate,
                "rev_beat": rev_beat,
            }
        )

    return {
        "beat_miss_history": beat_miss_history,
        "eps_beat_rate": round(eps_beats / eps_total, 4) if eps_total > 0 else None,
        "rev_beat_rate": round(rev_beats / rev_total, 4) if rev_total > 0 else None,
        "eps_trend": eps_trend[-6:],
        "earnings_dates": earnings_dates,
    }


def get_openbb_fundamentals(ticker: str) -> dict[str, Any]:
    """
    Return best-effort fundamentals snapshot for US tickers.

    Shape:
      {
        eps_estimate,
        revenue_estimate,
        analyst_count,
        beat_miss_history,
        eps_beat_rate,
        rev_beat_rate,
        eps_trend,
        earnings_dates,
      }
    """
    global _OPENBB_IMPORT_WARNED

    if ticker.endswith(".JO"):
        return {}

    # Avoid external provider calls during unit tests unless explicitly requested.
    if os.getenv("PYTEST_CURRENT_TEST") and os.getenv("CALENDA_TEST_OPENBB") != "1":
        return {}

    try:
        from openbb import obb  # lazy import; openbb is large
    except Exception as exc:
        if not _OPENBB_IMPORT_WARNED:
            logger.warning(
                "OpenBB fundamentals unavailable, using yfinance fallback: %s", exc
            )
            _OPENBB_IMPORT_WARNED = True
        return {}

    estimate_paths = (
        ("equity", "estimates", "analyst"),
        ("equity", "fundamental", "estimates"),
        ("equity", "calendar", "earnings"),
    )
    history_paths = (
        ("equity", "calendar", "earnings"),
        ("equity", "fundamental", "earnings"),
    )

    estimate_rows: list[Any] = []
    for path in estimate_paths:
        estimate_rows = _call_openbb_endpoint(obb, path, ticker)
        if estimate_rows:
            break

    history_rows: list[Any] = []
    for path in history_paths:
        history_rows = _call_openbb_endpoint(obb, path, ticker)
        if history_rows:
            break

    estimates = _get_upcoming_estimates(estimate_rows)
    history = _get_beat_miss_history(history_rows)

    merged = {
        "eps_estimate": estimates.get("eps_estimate"),
        "revenue_estimate": estimates.get("revenue_estimate"),
        "analyst_count": estimates.get("analyst_count"),
        "beat_miss_history": history.get("beat_miss_history", []),
        "eps_beat_rate": history.get("eps_beat_rate"),
        "rev_beat_rate": history.get("rev_beat_rate"),
        "eps_trend": history.get("eps_trend", []),
        "earnings_dates": history.get("earnings_dates", []),
    }

    has_any = (
        merged["eps_estimate"] is not None
        or merged["revenue_estimate"] is not None
        or merged["analyst_count"] is not None
        or bool(merged["beat_miss_history"])
        or bool(merged["eps_trend"])
    )
    return merged if has_any else {}

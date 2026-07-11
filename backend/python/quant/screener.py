"""Quantitative stock screener for TWSE (and arbitrary) symbols.

Powers the interactive "what should I trade?" page: it scans a curated
universe of liquid Taiwan listings, computes a technicals-only composite
score per symbol (RSI/trend/MACD/Bollinger via the analysis harness — NO
sentiment, which is far too slow for a multi-symbol scan), and returns the
rows ranked best-to-worst.

Design notes
------------
- Pure Python (stdlib + requests via the data layer) — no numpy/pandas.
- Indicator math is NOT duplicated: we reuse ``harness.StockAnalysisHarness``
  for scoring/signals and ``indicators`` for RSI/volatility/drawdown.
- Data degrades gracefully (yahoo -> stooq -> synthetic). A symbol whose data
  falls back to synthetic is NEVER silently ranked next to real data: its row
  carries ``source: "synthetic"`` + a ``warning`` and a ``null`` composite
  score, so it always sorts last and the UI can flag it.
- Concurrent fetch (ThreadPoolExecutor) with a per-symbol timeout and an
  overall wall-clock budget, plus a short in-module TTL cache so repeated UI
  hits are instant.

Public API
----------
``screen(market="tw", days=365, symbols=None, refresh=False) -> dict``

Returns::

    {
      "market": str,              # "tw" | "custom"
      "generated_at": str,        # ISO-8601 UTC, "...Z"
      "cached": bool,             # True if served from the TTL cache
      "days": int,                # history window used
      "universe_size": int,       # symbols attempted
      "scanned": int,             # symbols that produced a row
      "errors": [                 # symbols that raised (never fatal)
        {"symbol": str, "error": str}
      ],
      "warnings": [str, ...],     # de-duplicated data warnings across rows
      "rows": [ <ROW>, ... ],     # sorted by score desc, synthetic/nulls last
    }

Each ``<ROW>`` (the shape the TypeScript client must mirror 1:1)::

    {
      "symbol": str,              # e.g. "2330"
      "name": str,                # e.g. "TSMC"  (never empty)
      "sector": str,             # human sector label, never empty
      "last_price": float,
      "score": float | None,      # composite in [-1, 1]; None if synthetic
      "technical_score": float | None,  # same as score (no sentiment); mirror
      "verdict": str,             # strong_buy|buy|hold|sell|strong_sell|"n/a"
      "rsi": float | None,        # RSI(14), 0..100
      "trend": str,               # "up" | "down" | "flat"
      "momentum_1m": float | None,# fractional change over ~30 calendar days
      "momentum_3m": float | None,# fractional change over ~90 calendar days
      "volatility": float | None, # annualized, fractional (e.g. 0.31)
      "max_drawdown": float | None,   # negative fraction (e.g. -0.24)
      "source": str,              # "yahoo" | "stooq" | "binance" | "synthetic"
      "warning": str | None,      # populated when data degraded
    }
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import threading
import time
from datetime import timezone
from typing import Dict, List, Optional

from .data import PriceSeries, get_price_series
from .harness import StockAnalysisHarness, _verdict
from .indicators import annualized_volatility, max_drawdown, rsi, sma
from .planner import SECTORS

# ── Universe ─────────────────────────────────────────────────────────────
# A module-level list makes it trivial to extend. Each entry is
# (symbol, company name, sector label). We seed it from planner.py's Taiwan
# sectors (single source of truth for names) and top up with well-known liquid
# TWSE listings so a scan covers ~30-45 names across sectors.
#
# Supplemental names use the correct TWSE company/ETF names.

# Sector labels for the supplemental names below (keeps the label vocabulary
# consistent with the planner-derived rows).
_SEMI = "Taiwan Semiconductors"
_FIN = "Taiwan Financials"
_ELEC = "Taiwan Electronics Hardware"
_TELECOM = "Taiwan Telecom"
_SHIPPING = "Taiwan Shipping"
_ETF = "Taiwan ETFs"
_MATERIALS = "Taiwan Materials"
_AUTO = "Taiwan Auto & Industrials"
_RETAIL = "Taiwan Retail & Consumer"

# Supplemental liquid TWSE listings not covered by the planner sectors.
_SUPPLEMENTAL_TW: List[tuple] = [
    ("2308", "Delta Electronics", _ELEC),
    ("2379", "Realtek", _SEMI),
    ("3711", "ASE Technology", _SEMI),
    ("2408", "Nanya Technology", _SEMI),
    ("3034", "Novatek", _SEMI),
    ("2409", "AU Optronics", _ELEC),
    ("2474", "Catcher Technology", _ELEC),
    ("2327", "Yageo", _ELEC),
    ("2354", "Foxconn Technology", _ELEC),
    ("2884", "E.SUN FHC", _FIN),
    ("2885", "Yuanta FHC", _FIN),
    ("2886", "Mega FHC", _FIN),
    ("2892", "First FHC", _FIN),
    ("2880", "Hua Nan FHC", _FIN),
    ("2801", "Chang Hwa Bank", _FIN),
    ("1301", "Formosa Plastics", _MATERIALS),
    ("1303", "Nan Ya Plastics", _MATERIALS),
    ("1326", "Formosa Chemicals", _MATERIALS),
    ("2002", "China Steel", _MATERIALS),
    ("1216", "Uni-President", _RETAIL),
    ("2912", "President Chain Store", _RETAIL),
    ("2207", "Hotai Motor", _AUTO),
    ("9910", "Feng Tay Enterprises", _AUTO),
    ("2615", "Wan Hai Lines", _SHIPPING),
    ("0051", "Yuanta Mid-Cap 100 ETF", _ETF),
    ("00878", "Cathay Sustainability High Div ETF", _ETF),
    ("006208", "Fubon Taiwan 50 ETF", _ETF),
]


def _build_tw_universe() -> List[Dict[str, str]]:
    """Build the curated TWSE universe: planner sectors first, then supplements.

    Deduplicates by symbol (planner names win). Returns a list of
    ``{"symbol", "name", "sector"}`` dicts.
    """
    seen: Dict[str, Dict[str, str]] = {}

    # 1) planner-derived Taiwan sectors (single source of truth for names)
    for meta in SECTORS.values():
        if meta.get("market") != "TW":
            continue
        label = meta["label"]
        for sym, name in meta["tickers"].items():
            key = sym.upper()
            if key not in seen:
                seen[key] = {"symbol": sym, "name": name, "sector": label}

    # 2) supplemental liquid TWSE names
    for sym, name, label in _SUPPLEMENTAL_TW:
        key = sym.upper()
        if key not in seen:
            seen[key] = {"symbol": sym, "name": name, "sector": label}

    return list(seen.values())


TW_UNIVERSE: List[Dict[str, str]] = _build_tw_universe()


# ── Cache ────────────────────────────────────────────────────────────────
_CACHE_TTL_SECONDS = 600  # 10 minutes
_cache: Dict[tuple, dict] = {}
_cache_lock = threading.Lock()

# Concurrency / latency budget for a scan.
_MAX_WORKERS = 8
_PER_SYMBOL_TIMEOUT = 12.0   # seconds, per-symbol future timeout
_SCAN_TIME_BUDGET = 25.0     # seconds, overall wall-clock cap


def _now_iso() -> str:
    return dt.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _trend_flag(closes: List[float]) -> str:
    """Trend direction using SMA200 when available, else SMA50/SMA20 (harness-like).

    Returns "up", "down", or "flat".
    """
    last = closes[-1]
    sma200 = sma(closes, 200)
    if sma200[-1] is not None:
        return "up" if last > sma200[-1] else "down"
    # Fall back to the harness fast/slow relationship for shorter history.
    sma20, sma50 = sma(closes, 20), sma(closes, 50)
    if sma20[-1] is not None and sma50[-1] is not None:
        return "up" if sma20[-1] > sma50[-1] else "down"
    return "flat"


def _screen_one(entry: Dict[str, str], days: int) -> dict:
    """Compute the row for a single universe entry. Never raises for data problems.

    Retries the fetch once on exception before falling back; a synthetic result
    yields a flagged row with ``score = None`` so it is never ranked as real.
    """
    symbol, name, sector = entry["symbol"], entry["name"], entry["sector"]

    series: Optional[PriceSeries] = None
    for attempt in range(2):
        try:
            series = get_price_series(symbol, days)
            break
        except Exception:
            series = None
            if attempt == 0:
                continue
    if series is None:
        # Both attempts raised (should be rare — data layer swallows most).
        series = get_price_series(symbol, days)

    closes = series.closes
    base_row = {
        "symbol": symbol,
        "name": name,
        "sector": sector,
        "source": series.source,
        "warning": series.warning,
    }

    # Synthetic data must never be ranked alongside real data.
    is_synthetic = series.source == "synthetic"

    if len(closes) < 30:
        base_row.update({
            "last_price": round(closes[-1], 4) if closes else None,
            "score": None, "technical_score": None, "verdict": "n/a",
            "rsi": None, "trend": "flat",
            "momentum_1m": None, "momentum_3m": None,
            "volatility": None, "max_drawdown": None,
            "warning": (series.warning or "") + " Insufficient price history.",
        })
        return base_row

    # Technicals-only scoring via the harness (no sentiment).
    harness = StockAnalysisHarness(days=days, include_sentiment=False)
    signals = harness._technical_signals(closes)
    technical_score = (
        sum(s["score"] for s in signals) / len(signals) if signals else 0.0
    )
    technical_score = round(max(-1.0, min(1.0, technical_score)), 4)

    r = rsi(closes, 14)
    rsi_val = round(r[-1], 2) if r[-1] is not None else None
    mom_1m = round(
        harness._change_over_calendar_days(series.dates, closes, 30), 4
    )
    mom_3m = round(
        harness._change_over_calendar_days(series.dates, closes, 90), 4
    )
    vol = round(annualized_volatility(closes), 4)
    mdd = round(max_drawdown(closes), 4)
    trend = _trend_flag(closes)

    base_row.update({
        "last_price": round(closes[-1], 4),
        "rsi": rsi_val,
        "trend": trend,
        "momentum_1m": mom_1m,
        "momentum_3m": mom_3m,
        "volatility": vol,
        "max_drawdown": mdd,
    })

    if is_synthetic:
        # Real-looking metrics would be misleading — null the score/verdict so
        # the row is clearly marked and always sorts last.
        base_row.update({
            "score": None,
            "technical_score": None,
            "verdict": "n/a",
        })
    else:
        base_row.update({
            "score": technical_score,
            "technical_score": technical_score,
            "verdict": _verdict(technical_score),
        })

    return base_row


def _sort_key(row: dict):
    """Sort rows by score desc, pushing null scores (synthetic/insufficient) last."""
    score = row.get("score")
    if score is None:
        return (1, 0.0)
    return (0, -score)


def _run_scan(universe: List[Dict[str, str]], days: int, market: str) -> dict:
    """Execute a concurrent scan of ``universe`` within the time budget."""
    rows: List[dict] = []
    errors: List[dict] = []
    deadline = time.monotonic() + _SCAN_TIME_BUDGET

    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        future_to_entry = {
            pool.submit(_screen_one, entry, days): entry for entry in universe
        }
        for future in concurrent.futures.as_completed(future_to_entry):
            entry = future_to_entry[future]
            remaining = min(_PER_SYMBOL_TIMEOUT, deadline - time.monotonic())
            if remaining <= 0:
                # Budget exhausted — record the rest as errors and stop waiting.
                errors.append({"symbol": entry["symbol"], "error": "scan time budget exceeded"})
                future.cancel()
                continue
            try:
                rows.append(future.result(timeout=remaining))
            except Exception as exc:
                errors.append({
                    "symbol": entry["symbol"],
                    "error": f"{exc.__class__.__name__}: {exc}",
                })

    rows.sort(key=_sort_key)

    # De-duplicated, symbol-tagged warnings for the UI banner.
    warnings: List[str] = []
    seen_w = set()
    for row in rows:
        w = row.get("warning")
        if w:
            msg = f"{row['symbol']}: {w.strip()}"
            if msg not in seen_w:
                seen_w.add(msg)
                warnings.append(msg)

    return {
        "market": market,
        "generated_at": _now_iso(),
        "cached": False,
        "days": days,
        "universe_size": len(universe),
        "scanned": len(rows),
        "errors": errors,
        "warnings": warnings,
        "rows": rows,
    }


def screen(
    market: str = "tw",
    days: int = 365,
    symbols: Optional[List[str]] = None,
    refresh: bool = False,
) -> dict:
    """Screen a universe of symbols and return ranked rows.

    Parameters
    ----------
    market: "tw" for the curated TWSE universe. Ignored when ``symbols`` is
        given (market becomes "custom").
    days: history window (clamped 30..2000 by the data layer).
    symbols: optional caller-provided list to screen arbitrary symbols instead
        of the curated universe. Names default to the symbol; sector to "Custom".
    refresh: bypass the TTL cache and force a fresh scan.

    Returns the response dict documented in the module docstring.
    """
    days = max(30, min(int(days), 2000))

    if symbols:
        universe = [
            {"symbol": s.strip().upper(), "name": s.strip().upper(), "sector": "Custom"}
            for s in symbols
            if s and s.strip()
        ]
        market_key = "custom"
    else:
        universe = TW_UNIVERSE
        market_key = "tw"

    cache_key = (market_key, days, tuple(e["symbol"] for e in universe))

    if not refresh:
        with _cache_lock:
            hit = _cache.get(cache_key)
            if hit is not None and (time.monotonic() - hit["_ts"]) < _CACHE_TTL_SECONDS:
                result = dict(hit["result"])
                result["cached"] = True
                return result

    result = _run_scan(universe, days, market_key)

    with _cache_lock:
        _cache[cache_key] = {"_ts": time.monotonic(), "result": result}

    # Return a copy so the caller can't mutate the cached object.
    return dict(result)

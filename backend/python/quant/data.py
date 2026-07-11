"""Price data layer.

Fetch order per symbol type:
    crypto (``*USDT``/``*USD`` pairs) -> Binance public klines (no key needed)
    everything else                   -> Stooq daily CSV (no key needed)
    on any failure                    -> deterministic synthetic series so the
                                         UI keeps working offline (mirrors the
                                         mock fallback used by sentiment.ts)
"""

from __future__ import annotations

import csv
import datetime as dt
import io
from datetime import timezone
import math
import random
import zlib
from dataclasses import dataclass, asdict
from typing import List, Optional

import requests

REQUEST_TIMEOUT = 10

CRYPTO_QUOTES = ("USDT", "USD", "BUSD", "USDC")


@dataclass
class Candle:
    date: str  # ISO date (YYYY-MM-DD)
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class PriceSeries:
    symbol: str
    source: str  # "stooq" | "binance" | "synthetic"
    candles: List[Candle]
    warning: Optional[str] = None

    @property
    def closes(self) -> List[float]:
        return [c.close for c in self.candles]

    @property
    def dates(self) -> List[str]:
        return [c.date for c in self.candles]

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "source": self.source,
            "candles": [asdict(c) for c in self.candles],
            "warning": self.warning,
        }


def is_crypto(symbol: str) -> bool:
    s = symbol.upper()
    return any(s.endswith(q) and len(s) > len(q) for q in CRYPTO_QUOTES)


def _stooq_symbol(symbol: str) -> str:
    s = symbol.lower()
    # Taiwan listed numbers (e.g. 2330) -> 2330.tw, otherwise assume US listing
    if "." in s:
        return s
    if s.isdigit():
        return f"{s}.tw"
    return f"{s}.us"


def fetch_stooq_daily(symbol: str, days: int) -> List[Candle]:
    url = f"https://stooq.com/q/d/l/?s={_stooq_symbol(symbol)}&i=d"
    r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    text = r.text.strip()
    if not text or text.lower().startswith("no data") or "<html" in text[:200].lower():
        raise ValueError(f"Stooq returned no data for {symbol}")

    rows = list(csv.DictReader(io.StringIO(text)))
    candles: List[Candle] = []
    for row in rows:
        try:
            candles.append(
                Candle(
                    date=row["Date"],
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume") or 0),
                )
            )
        except (KeyError, ValueError):
            continue
    if not candles:
        raise ValueError(f"Stooq CSV unparseable for {symbol}")
    return candles[-days:]


def _yahoo_symbol(symbol: str) -> str:
    s = symbol.upper()
    # Taiwan listed numbers (e.g. 2330) -> 2330.TW; US tickers pass through
    if s.isdigit():
        return f"{s}.TW"
    return s


def fetch_yahoo_daily(symbol: str, days: int) -> List[Candle]:
    if days > 1460:
        rng = "10y"
    elif days > 730:
        rng = "5y"
    elif days > 365:
        rng = "2y"
    elif days > 180:
        rng = "1y"
    else:
        rng = "6mo"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{_yahoo_symbol(symbol)}"
    r = requests.get(
        url,
        params={"range": rng, "interval": "1d"},
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    r.raise_for_status()
    result = (r.json().get("chart") or {}).get("result") or []
    if not result:
        raise ValueError(f"Yahoo returned no data for {symbol}")
    node = result[0]
    ts = node.get("timestamp") or []
    quote = ((node.get("indicators") or {}).get("quote") or [{}])[0]
    candles: List[Candle] = []
    for i, t in enumerate(ts):
        try:
            c = quote["close"][i]
            if c is None:
                continue
            candles.append(
                Candle(
                    date=dt.datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"),
                    open=float(quote["open"][i] or c),
                    high=float(quote["high"][i] or c),
                    low=float(quote["low"][i] or c),
                    close=float(c),
                    volume=float(quote["volume"][i] or 0),
                )
            )
        except (KeyError, IndexError, TypeError):
            continue
    if not candles:
        raise ValueError(f"Yahoo chart empty for {symbol}")
    return candles[-days:]


def fetch_binance_daily(symbol: str, days: int) -> List[Candle]:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": "1d", "limit": min(days, 1000)}
    r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    out: List[Candle] = []
    for k in r.json():
        out.append(
            Candle(
                date=dt.datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
            )
        )
    if not out:
        raise ValueError(f"Binance returned no klines for {symbol}")
    return out


def synthetic_daily(symbol: str, days: int) -> List[Candle]:
    # Deterministic per symbol so charts/backtests are reproducible offline.
    # zlib.crc32 is a stable hash across processes/restarts, unlike the builtin
    # hash() which Python salts per process via PYTHONHASHSEED.
    rng = random.Random(zlib.crc32(symbol.upper().encode("utf-8")))
    price = 50 + rng.random() * 200
    drift, vol = 0.0003, 0.02
    today = dt.date.today()
    candles: List[Candle] = []
    for i in range(days):
        date = today - dt.timedelta(days=days - i)
        if date.weekday() >= 5:  # skip weekends like a real exchange
            continue
        ret = rng.gauss(drift, vol)
        o = price
        price = max(1.0, price * math.exp(ret))
        hi = max(o, price) * (1 + abs(rng.gauss(0, 0.004)))
        lo = min(o, price) * (1 - abs(rng.gauss(0, 0.004)))
        candles.append(
            Candle(
                date=date.isoformat(),
                open=round(o, 4),
                high=round(hi, 4),
                low=round(lo, 4),
                close=round(price, 4),
                volume=round(1e6 * (0.5 + rng.random()), 0),
            )
        )
    return candles


def get_price_series(symbol: str, days: int = 365) -> PriceSeries:
    """Fetch daily OHLCV with graceful degradation to synthetic data."""
    symbol = symbol.strip().upper()
    days = max(30, min(int(days), 2000))
    if is_crypto(symbol):
        try:
            return PriceSeries(symbol, "binance", fetch_binance_daily(symbol, days))
        except Exception as exc:
            return PriceSeries(
                symbol, "synthetic", synthetic_daily(symbol, days),
                warning=f"Live data unavailable ({exc.__class__.__name__}); using synthetic demo data.",
            )

    for source, fetcher in (("yahoo", fetch_yahoo_daily), ("stooq", fetch_stooq_daily)):
        try:
            return PriceSeries(symbol, source, fetcher(symbol, days))
        except Exception:
            continue
    return PriceSeries(
        symbol,
        "synthetic",
        synthetic_daily(symbol, days),
        warning="Live data unavailable; using synthetic demo data.",
    )

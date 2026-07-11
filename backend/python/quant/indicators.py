"""Pure-Python technical indicators.

Every function takes a list of floats (closing prices unless noted) and
returns a list of the same length, padded with ``None`` where the indicator
is not yet defined. Keeping lengths aligned makes charting and signal
generation trivial.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

Series = List[Optional[float]]


def sma(values: List[float], period: int) -> Series:
    out: Series = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    window_sum = sum(values[:period])
    out[period - 1] = window_sum / period
    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        out[i] = window_sum / period
    return out


def ema(values: List[float], period: int) -> Series:
    out: Series = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period  # seed with SMA
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: List[float], period: int = 14) -> Series:
    out: Series = [None] * len(values)
    if len(values) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        diff = values[i] - values[i - 1]
        gains += max(diff, 0)
        losses += max(-diff, 0)
    avg_gain, avg_loss = gains / period, losses / period

    def _rsi(g: float, l: float) -> float:
        if l == 0:
            return 100.0
        rs = g / l
        return 100 - 100 / (1 + rs)

    out[period] = _rsi(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        diff = values[i] - values[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(diff, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-diff, 0)) / period
        out[i] = _rsi(avg_gain, avg_loss)
    return out


def macd(
    values: List[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[Series, Series, Series]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast, ema_slow = ema(values, fast), ema(values, slow)
    line: Series = [
        (f - s) if f is not None and s is not None else None
        for f, s in zip(ema_fast, ema_slow)
    ]
    defined = [v for v in line if v is not None]
    sig_defined = ema(defined, signal) if len(defined) >= signal else [None] * len(defined)
    sig: Series = [None] * len(values)
    offset = len(values) - len(defined)
    for j, v in enumerate(sig_defined):
        sig[offset + j] = v
    hist: Series = [
        (m - s) if m is not None and s is not None else None for m, s in zip(line, sig)
    ]
    return line, sig, hist


def bollinger(
    values: List[float], period: int = 20, num_std: float = 2.0
) -> Tuple[Series, Series, Series]:
    """Returns (upper, middle, lower)."""
    middle = sma(values, period)
    upper: Series = [None] * len(values)
    lower: Series = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1 : i + 1]
        mean = middle[i]
        if mean is None:
            continue
        var = sum((v - mean) ** 2 for v in window) / period
        std = math.sqrt(var)
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std
    return upper, middle, lower


def daily_returns(values: List[float]) -> List[float]:
    return [
        (values[i] / values[i - 1] - 1) if values[i - 1] else 0.0
        for i in range(1, len(values))
    ]


def annualized_volatility(values: List[float], trading_days: int = 252) -> float:
    rets = daily_returns(values)
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(trading_days)


def max_drawdown(values: List[float]) -> float:
    """Largest peak-to-trough decline, as a negative fraction (e.g. -0.23)."""
    peak = float("-inf")
    mdd = 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, v / peak - 1)
    return mdd

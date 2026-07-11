"""Trading strategies.

A strategy is a function ``(closes, **params) -> positions`` where
``positions`` is a list of 0/1 target exposures, one per bar. The backtester
applies position changes on the NEXT bar's close to avoid look-ahead bias.

Register new strategies in ``STRATEGIES`` so they automatically appear in
``GET /api/strategies`` and in the frontend's strategy dropdown.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from .indicators import bollinger, macd, rsi, sma

Positions = List[int]


def sma_crossover(closes: List[float], fast: int = 20, slow: int = 50) -> Positions:
    """Long when the fast SMA is above the slow SMA (trend following)."""
    fast_line, slow_line = sma(closes, fast), sma(closes, slow)
    pos: Positions = []
    for f, s in zip(fast_line, slow_line):
        pos.append(1 if f is not None and s is not None and f > s else 0)
    return pos


def rsi_mean_reversion(closes: List[float], period: int = 14, oversold: float = 30, overbought: float = 70) -> Positions:
    """Buy when RSI drops below `oversold`, exit when it rises above `overbought`."""
    r = rsi(closes, period)
    pos: Positions = []
    holding = 0
    for v in r:
        if v is not None:
            if v < oversold:
                holding = 1
            elif v > overbought:
                holding = 0
        pos.append(holding)
    return pos


def macd_momentum(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Positions:
    """Long while the MACD line is above its signal line."""
    line, sig, _ = macd(closes, fast, slow, signal)
    pos: Positions = []
    for m, s in zip(line, sig):
        pos.append(1 if m is not None and s is not None and m > s else 0)
    return pos


def bollinger_reversion(closes: List[float], period: int = 20, num_std: float = 2.0) -> Positions:
    """Buy at the lower band, exit at the middle band (mean reversion)."""
    upper, middle, lower = bollinger(closes, period, num_std)
    pos: Positions = []
    holding = 0
    for c, mid, lo in zip(closes, middle, lower):
        if lo is not None and c <= lo:
            holding = 1
        elif mid is not None and c >= mid:
            holding = 0
        pos.append(holding)
    return pos


def trend_momentum(closes: List[float], regime: int = 200, lookback: int = 63) -> Positions:
    """Regime-filtered momentum (designed to be tested against a 0050 benchmark).

    Long only when BOTH hold:
      - price is above its `regime`-day SMA (bull regime filter), and
      - the `lookback`-day return is positive (momentum confirmation).

    The aim is not to out-pick the index but to sidestep deep bear-market
    drawdowns while staying invested in uptrends. In sideways/whipsaw markets
    it will typically lag buy & hold after costs — judge it on the backtest,
    not on this description.
    """
    regime_line = sma(closes, regime)
    pos: Positions = []
    for i, c in enumerate(closes):
        in_regime = regime_line[i] is not None and c > regime_line[i]
        has_momentum = i >= lookback and closes[i - lookback] > 0 and c / closes[i - lookback] > 1.0
        pos.append(1 if in_regime and has_momentum else 0)
    return pos


def buy_and_hold(closes: List[float]) -> Positions:
    """Benchmark: fully invested from the first bar."""
    return [1] * len(closes)


STRATEGIES: Dict[str, dict] = {
    "sma_crossover": {
        "fn": sma_crossover,
        "label": "SMA Crossover (trend)",
        "description": "Long when the fast SMA is above the slow SMA.",
        "params": {"fast": 20, "slow": 50},
    },
    "rsi_mean_reversion": {
        "fn": rsi_mean_reversion,
        "label": "RSI Mean Reversion",
        "description": "Buy oversold (RSI < 30), sell overbought (RSI > 70).",
        "params": {"period": 14, "oversold": 30, "overbought": 70},
    },
    "macd_momentum": {
        "fn": macd_momentum,
        "label": "MACD Momentum",
        "description": "Long while the MACD line is above its signal line.",
        "params": {"fast": 12, "slow": 26, "signal": 9},
    },
    "bollinger_reversion": {
        "fn": bollinger_reversion,
        "label": "Bollinger Reversion",
        "description": "Buy at the lower band, exit at the middle band.",
        "params": {"period": 20, "num_std": 2.0},
    },
    "trend_momentum": {
        "fn": trend_momentum,
        "label": "Trend Momentum (regime filter)",
        "description": "Long only above the 200-day SMA with positive 63-day momentum; sits in cash otherwise. Built to be benchmarked against 0050.",
        "params": {"regime": 200, "lookback": 63},
    },
    "buy_and_hold": {
        "fn": buy_and_hold,
        "label": "Buy & Hold (benchmark)",
        "description": "Fully invested for the whole period.",
        "params": {},
    },
}


def get_strategy(name: str) -> Callable[..., Positions]:
    if name not in STRATEGIES:
        raise KeyError(f"Unknown strategy '{name}'. Available: {', '.join(STRATEGIES)}")
    return STRATEGIES[name]["fn"]


def public_catalog() -> list[dict]:
    """JSON-safe strategy list for the API (functions stripped)."""
    return [
        {"name": name, "label": meta["label"], "description": meta["description"], "params": meta["params"]}
        for name, meta in STRATEGIES.items()
    ]

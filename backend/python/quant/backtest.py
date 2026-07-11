"""Backtest engine.

Simulates a long/flat strategy on daily closes:
    - target positions come from a strategy (see strategies.py)
    - position changes execute on the NEXT bar's close (no look-ahead)
    - commission charged in basis points on every position change

Outputs an equity curve, the trade list, and standard performance metrics,
plus a buy-and-hold benchmark over the same window.
"""

from __future__ import annotations

import math
from typing import List, Optional

from .data import Candle, PriceSeries, get_price_series
from .indicators import max_drawdown
from .strategies import get_strategy

TRADING_DAYS = 252


def _null_trade_metrics() -> dict:
    return {
        "profit_factor": None,
        "expectancy": None,
        "avg_win": None,
        "avg_loss": None,
        "payoff_ratio": None,
    }


def _trade_metrics(closed: List[dict]) -> dict:
    """Trade-quality metrics from CLOSED trades (sells carrying a ``return``).

    All fields are null when undefined (no closed trades, no losers, etc.)
    so the buy-and-hold benchmark path — which never closes a trade — yields
    nulls without crashing.
    """
    rets = [t["return"] for t in closed if "return" in t]
    if not rets:
        return _null_trade_metrics()

    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r < 0]  # exclude flat (0) trades from win/loss means

    gross_win = sum(wins)
    gross_loss = sum(losses)
    profit_factor = round(gross_win / abs(gross_loss), 4) if losses else None

    expectancy = round(sum(rets) / len(rets), 4)
    avg_win = round(sum(wins) / len(wins), 4) if wins else None
    avg_loss = round(sum(losses) / len(losses), 4) if losses else None
    payoff_ratio = (
        round(avg_win / abs(avg_loss), 4)
        if (avg_win is not None and avg_loss is not None and avg_loss != 0)
        else None
    )

    return {
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "payoff_ratio": payoff_ratio,
    }


def _metrics(equity: List[float], dates: List[str], closed: Optional[List[dict]] = None) -> dict:
    closed = closed or []
    if len(equity) < 2 or equity[0] <= 0:
        base = {
            "total_return": 0.0, "cagr": 0.0, "sharpe": 0.0,
            "max_drawdown": 0.0, "volatility": 0.0,
        }
        base.update(_trade_metrics(closed))
        return base
    total_return = equity[-1] / equity[0] - 1
    years = max(len(equity) / TRADING_DAYS, 1e-9)
    cagr = (equity[-1] / equity[0]) ** (1 / years) - 1 if equity[-1] > 0 else -1.0

    rets = [equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)) if equity[i - 1] > 0]
    mean = sum(rets) / len(rets) if rets else 0.0
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1) if len(rets) > 1 else 0.0
    std = math.sqrt(var)
    sharpe = (mean / std) * math.sqrt(TRADING_DAYS) if std > 0 else 0.0
    vol = std * math.sqrt(TRADING_DAYS)

    return {
        "total_return": round(total_return, 4),
        "cagr": round(cagr, 4),
        "sharpe": round(sharpe, 2),
        "max_drawdown": round(max_drawdown(equity), 4),
        "volatility": round(vol, 4),
        **_trade_metrics(closed),
    }


def _simulate(
    candles: List[Candle],
    positions: List[int],
    initial_capital: float,
    commission_bps: float,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
) -> dict:
    """Simulate long/flat with next-bar execution.

    Optional ``stop_loss_pct`` / ``take_profit_pct`` are risk overlays applied
    in the simulation layer (never per-strategy). While holding, if bar *i*'s
    close breaches ``entry*(1-sl)`` or ``entry*(1+tp)``, a forced exit is
    scheduled and — like every other decision — executes on bar *i+1*'s close.
    After a forced exit the strategy may re-enter only once its RAW signal has
    gone flat and turned long again, preventing instant re-entry loops.
    """
    closes = [c.close for c in candles]
    dates = [c.date for c in candles]
    fee = commission_bps / 10_000

    cash = initial_capital
    shares = 0.0
    equity: List[float] = []
    trades: List[dict] = []
    entry_price: Optional[float] = None
    forced_exit = False       # a stop/take breach observed at bar i-1, execute now
    reentry_locked = False    # true after a forced exit until raw signal resets to flat

    for i, price in enumerate(closes):
        # Execute yesterday's decision at today's close (next-bar execution).
        raw_target = positions[i - 1] if i > 0 else 0

        # Release the re-entry lock once the raw signal has gone flat.
        if reentry_locked and raw_target == 0:
            reentry_locked = False

        # A forced exit (stop/take) overrides the strategy target for this bar.
        if forced_exit:
            target = 0
        elif reentry_locked:
            target = 0
        else:
            target = raw_target

        holding = shares > 0
        if target == 1 and not holding:
            cost = cash * fee
            shares = (cash - cost) / price
            cash = 0.0
            entry_price = price
            trades.append({"date": dates[i], "side": "buy", "price": round(price, 4)})
        elif target == 0 and holding:
            proceeds = shares * price
            cash = proceeds * (1 - fee)
            pnl = (price / entry_price - 1) if entry_price else 0.0
            exit_kind = "stop_take" if forced_exit else "signal"
            trades.append({
                "date": dates[i], "side": "sell", "price": round(price, 4),
                "return": round(pnl, 4), "exit": exit_kind,
            })
            shares = 0.0
            entry_price = None
        equity.append(cash + shares * price)

        # Observe stop/take breach on THIS bar's close; act on the next bar.
        forced_exit = False
        if shares > 0 and entry_price:
            hit_stop = stop_loss_pct is not None and price <= entry_price * (1 - stop_loss_pct)
            hit_take = take_profit_pct is not None and price >= entry_price * (1 + take_profit_pct)
            if hit_stop or hit_take:
                forced_exit = True
                reentry_locked = True

    # Mark open position to market rather than force-closing it.
    closed = [t for t in trades if t["side"] == "sell"]
    wins = sum(1 for t in closed if t.get("return", 0) > 0)
    win_rate = round(wins / len(closed), 4) if closed else None

    return {
        "equity_curve": [round(e, 2) for e in equity],
        "dates": dates,
        "trades": trades,
        "num_trades": len(closed),
        "win_rate": win_rate,
        "final_equity": round(equity[-1], 2) if equity else initial_capital,
        "metrics": _metrics(equity, dates, closed),
    }


def _benchmark_candles(dates: List[str], bench: PriceSeries) -> List[Candle]:
    """Align a benchmark's closes onto the strategy's date grid (forward-fill)."""
    by_date = {c.date: c.close for c in bench.candles}
    aligned: List[Optional[float]] = []
    prev: Optional[float] = None
    for d in dates:
        if d in by_date:
            prev = by_date[d]
        aligned.append(prev)
    first = next((v for v in aligned if v is not None), None)
    if first is None:
        raise ValueError(f"No overlapping history for benchmark {bench.symbol}")
    filled = [v if v is not None else first for v in aligned]
    return [Candle(date=d, open=v, high=v, low=v, close=v, volume=0) for d, v in zip(dates, filled)]


def _clamp_optional(value: Optional[float], lo: float, hi: float) -> Optional[float]:
    """Clamp an optional risk fraction; ``None`` means the overlay is off."""
    if value is None:
        return None
    return max(lo, min(float(value), hi))


def run_backtest(
    symbol: str,
    strategy: str = "sma_crossover",
    params: Optional[dict] = None,
    days: int = 365,
    initial_capital: float = 10_000.0,
    commission_bps: float = 10.0,
    series: Optional[PriceSeries] = None,
    benchmark_symbol: Optional[str] = None,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
) -> dict:
    """Run one strategy over daily data and compare it to buy & hold.

    ``benchmark_symbol`` lets the buy-&-hold comparison run on a different
    instrument (e.g. strategy on 2330 vs holding 0050).

    ``stop_loss_pct`` / ``take_profit_pct`` are optional risk overlays applied
    to the strategy leg only (the benchmark is pure buy & hold). ``None``
    disables each. They are clamped: stop 0.005–0.9, take 0.005–2.0.
    """
    stop_loss_pct = _clamp_optional(stop_loss_pct, 0.005, 0.9)
    take_profit_pct = _clamp_optional(take_profit_pct, 0.005, 2.0)

    series = series or get_price_series(symbol, days)
    closes = series.closes
    if len(closes) < 30:
        raise ValueError(f"Not enough price history for {symbol} ({len(closes)} bars)")

    positions = get_strategy(strategy)(closes, **(params or {}))
    result = _simulate(
        series.candles, positions, initial_capital, commission_bps,
        stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
    )

    bench_symbol = (benchmark_symbol or symbol).strip().upper()
    bench_warning = None
    if bench_symbol != series.symbol:
        bench_series = get_price_series(bench_symbol, days)
        bench_warning = bench_series.warning
        bench_candles = _benchmark_candles(series.dates, bench_series)
    else:
        bench_candles = series.candles
    benchmark = _simulate(bench_candles, [1] * len(bench_candles), initial_capital, commission_bps)

    return {
        "symbol": series.symbol,
        "source": series.source,
        "warning": series.warning,
        "strategy": strategy,
        "params": params or {},
        "days": len(closes),
        "start": series.dates[0],
        "end": series.dates[-1],
        "initial_capital": initial_capital,
        "commission_bps": commission_bps,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
        "result": result,
        "benchmark": {
            "symbol": bench_symbol,
            "warning": bench_warning,
            "equity_curve": benchmark["equity_curve"],
            "final_equity": benchmark["final_equity"],
            "metrics": benchmark["metrics"],
        },
    }

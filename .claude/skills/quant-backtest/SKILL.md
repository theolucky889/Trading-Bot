---
name: quant-backtest
description: >-
  How to add trading strategies and run backtests in the Trading Bot.
  Use whenever working on backend/python/quant/strategies.py or backtest.py —
  adding/tuning a strategy, changing execution semantics, commissions, or
  performance metrics (CAGR, Sharpe, drawdown, win rate), or the /api/backtest
  contract. Also use when asked to "backtest", "test a strategy", "compare
  strategies", or rerun/update previous backtest results.
---

# Quant Backtest Engine

Files: `backend/python/quant/strategies.py` (registry) and `backtest.py`
(simulation). Served by `POST /api/backtest` → `BacktestView.vue`.

## Strategy contract

```python
def my_strategy(closes: list[float], **params) -> list[int]:
    """Return one target position (0=flat, 1=long) per bar."""
```

Register it in `STRATEGIES` with `fn`, `label`, `description`, and default
`params`. That single registration exposes it in `GET /api/strategies` and
the frontend dropdown automatically — no other wiring needed.

## Execution semantics (do not break these)

- **Next-bar execution:** the position decided at bar *i* is applied at bar
  *i+1*'s close. This prevents look-ahead bias; a strategy that trades on the
  same bar it observes will show inflated, fake performance.
- Commission: `commission_bps` charged on every position change (default 10).
- Open positions at the end are marked to market, not force-closed; win rate
  counts only closed round-trips.
- Every run includes a buy-and-hold benchmark over the identical window —
  results are meaningless without it. `run_backtest(benchmark_symbol=...)`
  runs the benchmark on a different instrument (e.g. strategy on 2330 vs
  holding 0050); the benchmark's closes are forward-filled onto the strategy's
  date grid. The response's `benchmark` object carries `symbol` and `warning`.

## Related module: investment planner

`quant/planner.py` (DCA planner: sector catalog, equal-weight allocation,
monthly-DCA historical simulation vs a benchmark, ±1σ projection) is also
quant-developer territory. It buys at the first trading close of each month
and simulates only over months where ALL holdings and the benchmark have
data. Exposed via `GET /api/sectors` and `POST /api/plan` → `PlanView.vue`
(`src/api/plan.ts` mirrors the response).

## Metrics (backtest.py::_metrics)

`total_return`, `cagr` (252 trading days/yr), `sharpe` (rf=0, daily returns
annualized), `max_drawdown` (negative fraction), `volatility` (annualized).
All must be finite; `max_drawdown <= 0` always.

## Verification (run after every change)

```bash
cd E:/Github/Trading-Bot
python -c "
from backend.python.quant.data import PriceSeries, synthetic_daily
from backend.python.quant.backtest import run_backtest
from backend.python.quant.strategies import STRATEGIES
import math
s = PriceSeries('TEST','synthetic',synthetic_daily('TEST',400))
for name in STRATEGIES:
    r = run_backtest('TEST', name, series=s)
    m = r['result']['metrics']
    assert len(r['result']['equity_curve']) == r['days']
    assert m['max_drawdown'] <= 0
    assert all(math.isfinite(v) for v in m.values())
    print(f'{name:22s} ret={m[\"total_return\"]:+.4f} trades={r[\"result\"][\"num_trades\"]}')"
```

## Interpreting results honestly

- Synthetic-source results (`source: "synthetic"`) are for plumbing tests
  only; never present them as real performance.
- Compare against the benchmark: beating buy & hold after costs is the bar.
- Don't tune params on the same window you report — that's overfitting; if
  asked to optimize, say so and suggest an out-of-sample split.

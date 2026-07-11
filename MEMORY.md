# Project Memory

Running log of state, decisions, and known limitations that aren't obvious
from the code. Newest entries first. See CLAUDE.md for structure/commands.

## 2026-07-05 (later) — trend_momentum, 0050 benchmark, investment planner

- Added `trend_momentum` strategy (200-day SMA regime filter + 63-day
  momentum) built to be judged against 0050; backtests now accept
  `benchmark_symbol` so any run can compare vs holding 0050 (benchmark closes
  forward-filled onto the strategy's date grid).
- Added `quant/planner.py` + `POST /api/plan`, `GET /api/sectors` +
  `PlanView.vue` (`/plan`): monthly budget × time span × sector picks →
  equal-weight DCA allocation, historical simulation vs 0050 DCA, ±1σ
  projection. 9 curated sectors (6 TW, 2 US, crypto).
- Honest benchmark reality observed in live QA: trend_momentum on 2330 beat
  0050 B&H over 2y (+129% vs +125%), but a diversified 36-month
  semis+financials+ETF plan LAGGED pure 0050 DCA (+124% vs +135%). No claim
  that any strategy reliably beats the index; UI always shows the comparison.
- Extended Yahoo fetch ranges to 5y/10y for multi-year plans.

## 2026-07-05 — Quant engine, backtest, analysis harness, agent harness

**Built**
- `backend/python/quant/`: data layer (Yahoo → Stooq → synthetic fallback),
  pure-Python indicators (SMA/EMA/RSI/MACD/Bollinger), 5 strategies
  (sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_reversion,
  buy_and_hold), next-bar backtester with CAGR/Sharpe/MDD/win-rate, and
  `StockAnalysisHarness` (technicals 0.7 + sentiment 0.3 → verdict).
- FastAPI endpoints: `/api/analyze`, `/api/history`, `/api/strategies`,
  `POST /api/backtest` (plus existing `/api/sentiment`, `/api/health`).
- Frontend: `AnalysisView.vue` (`/analysis`), `BacktestView.vue` (`/backtest`),
  typed clients `src/api/analysis.ts` + `backtest.ts`, Navbar links,
  vite `/api` proxy split (auth → :3000, rest → :8000).
- Claude harness: `.claude/agents/` (market-analyst, quant-developer,
  fullstack-integrator, qa-verifier) + `.claude/skills/`
  (stock-analysis-orchestrator, stock-analysis, quant-backtest).

**Decisions**
- No numpy/pandas: keeps backend installable anywhere; lists + math suffice
  at daily-bar scale.
- Data fallback chain returns synthetic demo data with a `warning` instead of
  erroring, so the UI works offline (mirrors sentiment.ts mock pattern).
- Stooq is blocked by a JS-verification wall on this network — Yahoo chart
  API is the primary stock source (verified working for AAPL and 2330.TW);
  Binance for crypto (verified for BTCUSDT).
- Next-bar execution + bps commission + mandatory buy-and-hold benchmark to
  keep backtests honest.

**Fixed en route**
- `floating-vue` was imported in main.ts but missing from package.json → installed.
- Missing `*.vue` module shim broke `npm run type-check` → added to env.d.ts.
- `/api/login` was called relatively but unproxied → now proxied to :3000.

**Known limitations / next steps**
- Auth (server.js) needs a local MongoDB; SECRET_KEY is hardcoded — move to env.
- Strategies are long/flat only (no shorting, sizing, or multi-asset portfolios).
- FinBERT sentiment model falls back to VADER (not installed).
- No out-of-sample split in the backtester — param tuning on the report window
  overfits; noted in quant-backtest skill.
- `_workspace/` (agent artifacts) should be added to .gitignore when first used.

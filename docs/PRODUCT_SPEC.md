# Product Specification — Trading Bot

**Version:** 0.2 (as-built, 2026-07-10)
**Status:** Documents current behavior plus explicitly-marked gaps. Companion document: `docs/QA_REPORT.md`.

---

## 1. Product overview

Trading Bot is a personal **algorithmic trading assistant** for retail investors covering three markets: **US stocks**, **Taiwan stocks (TWSE)**, and **crypto**. It does not place orders; it is an analysis and planning tool with four core capabilities:

1. **Stock Analysis** — technical indicators + news sentiment fused into a single Buy/Hold/Sell verdict with per-signal explanations.
2. **Strategy Backtesting** — run rule-based strategies over historical data with realistic execution assumptions and a buy-and-hold benchmark (optionally a different instrument, e.g. strategy on 2330 vs holding 0050).
3. **Investment Planner** — monthly dollar-cost-averaging plans across user-selected sectors, historically simulated and benchmarked against 0050, with a ±1σ forward projection.
4. **Market Sentiment Engine** — VADER sentiment over Google News for arbitrary queries (multi-query supported).

**Guiding principles (enforced conventions):**
- Quant code is pure Python (stdlib + `requests`) — no numpy/pandas by design.
- Price data degrades gracefully (live → fallback → deterministic synthetic) and every degraded response carries a `warning` the UI **must** display.
- Backtests use next-bar execution (no look-ahead) and always include a benchmark.
- API response shapes are mirrored 1:1 by TypeScript types in `src/api/`; both sides change together.
- Nothing shown is investment advice; planner responses carry a mandatory disclaimer.

**Target user:** an individual retail investor (TW/US/crypto) comfortable with basic quant concepts (SMA, RSI, Sharpe) who wants explainable signals, not a black box.

---

## 2. System architecture

```
┌─────────────────────────────┐
│ Vue 3 + TS + Vite + Tailwind│  algorithmic-trading-bot/  (dev :5173)
│  views + typed API clients  │
└──────────┬──────────────────┘
           │ vite proxy
   ┌───────┴────────────────────────────────┐
   │ /api/login, /api/register → :3000      │
   │ all other /api/*          → :8000      │
   │ /av → Alpha Vantage, /twse → TWSE (legacy)
   └───────┬───────────────────┬────────────┘
┌──────────▼─────────┐  ┌──────▼──────────────┐
│ Express auth server │  │ FastAPI app          │
│ backend/server.js   │  │ backend/app.py       │
│ MongoDB (users)     │  │ python/quant/* +     │
│ bcrypt + JWT (1h)   │  │ sentiment_analysis   │
└─────────────────────┘  └──────┬──────────────┘
                                │ outbound
                    Yahoo Finance → Stooq → synthetic (stocks)
                    Binance → synthetic (crypto)
                    Google News RSS (sentiment)
```

- **Frontend:** Vue 3 `<script setup>` + TypeScript, vue-router (history mode), Pinia (installed, unused), chart.js, Tailwind (currently via CDN — see QA M7), floating-vue tooltips.
- **Analysis backend:** FastAPI (`:8000`), stateless, no auth, no DB. All computation per-request.
- **Auth backend:** Express (`:3000`) + MongoDB `trading-bot` DB, bcrypt-hashed passwords, JWT signed tokens (1h expiry).

### Data layer contract (backend/python/quant/data.py)
| Symbol shape | Interpretation | Source order |
|---|---|---|
| ends in USDT/USD/BUSD/USDC | crypto pair | Binance klines → synthetic |
| all digits (e.g. `2330`, `0050`) | TWSE listing | Yahoo (`.TW`) → Stooq (`.tw`) → synthetic |
| anything else (e.g. `AAPL`) | US listing | Yahoo → Stooq (`.us`) → synthetic |

Synthetic data is a seeded random walk (weekends skipped) and always sets `source: "synthetic"` + a human-readable `warning`. `days` is clamped to [30, 2000].

---

## 3. Feature specifications by page

Navigation (Navbar, all pages): Dashboard `/` · Trade `/trade` · Analysis `/analysis` · Backtest `/backtest` · Plan `/plan` · Settings `/settings` · About `/about` · Login `/login` (Register `/register` reachable from Login only).

### 3.1 Dashboard (`/`) — DashboardView.vue
Landing page; portfolio snapshot + multi-symbol price comparison.
- **Balance widget:** Total Assets / Debt / Net Assets cards + Cash/Stock progress bars. *(Currently hardcoded mock values — no portfolio backend exists.)*
- **Comparison controls:** category (US / Taiwan / Crypto), multi-select symbols from a static list per category, graph type (line/bar).
- **Per-symbol charts:** price chart + volume & return/loss placeholders, re-rendered on any control change.
- **News section:** static placeholder items; **Start Trading** CTA (no action).
- **Data sources:** legacy path — Alpha Vantage via `/av` proxy (US), TWSE via `/twse` proxy, Binance direct (crypto). *(Broken today — QA H1/H2. Spec intent: migrate to internal `GET /api/history`.)*

### 3.2 Stock Analysis (`/analysis`) — AnalysisView.vue
- **Inputs:** symbol (free text, uppercased), lookback (6mo/1y/2y), include-sentiment toggle (default on).
- **Output:**
  - **Verdict card** — one of Strong Buy / Buy / Hold / Sell / Strong Sell, color-coded, with composite score in [-1, 1] and a score gauge.
  - **Stat cards** — last price + data source, 30-day change, annualized volatility, max drawdown, technical & sentiment sub-scores.
  - **Price chart** — Close + SMA20 + SMA50 (chart.js line).
  - **Signals list** — each signal shows indicator name, human-readable reason, and its score contribution: SMA 20/50 trend (±1.0), RSI(14) (+0.8 oversold / −0.8 overbought / 0 neutral), MACD(12,26,9) (±0.6), Bollinger(20,2) %B (±0.5 at band extremes).
  - **News sentiment panel** — positive/neutral/negative counts + top-5 headlines with outbound links.
- **Scoring:** technical = mean of signal scores; composite = 0.7·technical + 0.3·sentiment (avg VADER compound), clamped to [-1,1]. Verdict thresholds: ≥0.5 strong_buy · ≥0.15 buy · ≥−0.15 hold · ≥−0.5 sell · else strong_sell.
- **Degradation:** synthetic-data warning banner (yellow) above results; sentiment failure degrades to score 0 with its own warning; API errors render a red banner.
- **Validation:** min 30 bars of history or HTTP 422.

### 3.3 Strategy Backtest (`/backtest`) — BacktestView.vue
- **Inputs:** symbol, strategy (dropdown populated from `GET /api/strategies`), period (6mo/1y/2y), optional benchmark symbol (e.g. `0050`), initial capital (min 100), per-strategy numeric parameters (auto-generated fields from the catalog defaults).
- **Strategy catalog (extensible via `STRATEGIES` registry):**
  | name | logic | default params |
  |---|---|---|
  | sma_crossover | long while fast SMA > slow SMA | fast 20, slow 50 |
  | rsi_mean_reversion | buy RSI<oversold, exit RSI>overbought | 14 / 30 / 70 |
  | macd_momentum | long while MACD > signal line | 12 / 26 / 9 |
  | bollinger_reversion | buy at lower band, exit at middle | 20 / 2.0 |
  | trend_momentum | long only above 200-day SMA **and** positive 63-day return (regime-filtered momentum, built to be judged vs 0050) | regime 200, lookback 63 |
  | buy_and_hold | always long (benchmark) | — |
- **Execution model:** long/flat only; signals execute at the **next bar's close** (no look-ahead); commission in bps (default 10, clamped 0–500) charged on every position change; open positions marked to market, not force-closed.
- **Output:** metric cards (Total Return, CAGR, Sharpe, Max Drawdown, Trades, Win Rate — win rate `—` when no closed trades), run summary line (period, bars, data source, commission, benchmark return), equity-curve chart (strategy vs benchmark buy & hold, dashed), scrollable trade table (date, side, price, per-trade return on sells).
- **Benchmark:** same symbol by default; a different `benchmark_symbol` is fetched separately and forward-filled onto the strategy's date grid.
- **Validation:** unknown strategy → 422 listing valid names; bad param names → 422 "Invalid params"; days clamped [60, 2000].

### 3.4 Investment Plan (`/plan`) — PlanView.vue
- **Inputs:** monthly budget (>0), time span (1/2/3/5 years), benchmark (default `0050`), sector multi-select cards (from `GET /api/sectors`): 6 Taiwan sectors (semis, financials, electronics, telecom, shipping, ETFs), 2 US sectors (tech, consumer), crypto. Each card lists its constituent tickers.
- **Allocation rule:** equal weight per selected sector, equal weight per ticker inside a sector — deliberately simple and explainable, no return-chasing optimization.
- **Historical simulation:** DCA buys at the first trading close of each month over the past N months (intersection of months where **all** holdings + benchmark have data; shortened with a warning if insufficient). Compared against putting the identical monthly amount into the benchmark.
- **Output:** summary cards (invested, final value, plan return, benchmark DCA return, ahead/behind delta), growth chart (plan vs benchmark vs invested-cash line), allocation table (weight, per-month amount, simulated shares/value per holding), projection panel (expected / +1σ optimistic / −1σ pessimistic future value from historical monthly return & volatility, with a "rough range, not a forecast" note).
- **Mandatory disclaimer** rendered at the bottom; all per-symbol data warnings shown in a banner.
- **Validation:** months 3–120 (backend), budget > 0, ≥1 sector, unknown sector ids → 422.

### 3.5 Trade (`/trade`) — TradeView.vue *(prototype)*
Tabbed console: Overview (mock running-bot status, current trade, trade history), Performance / Trades / Settings / Help (empty stubs), and **AI Engine** — the embedded Sentiment Engine (§3.6). Spec intent: this becomes the live-bot control surface (start/stop, positions, executed trades) once an execution backend exists. *(Currently entirely mock and unstyled — QA M11.)*

### 3.6 Sentiment Engine (Trade → AI Engine) — SentimentEngine.vue
- **Inputs:** multi-query textarea (comma/newline separated, deduped, max 10, live "detected N queries" chips), article count (5–30), model (VADER; FinBERT listed but falls back to VADER with a warning).
- **Behavior:** analyzes queries sequentially against `GET /api/sentiment`; per-query result list with avg compound + pos/neu/neg counts; selecting a result shows summary cards and the article list (label badge, compound score, source, timestamp, ~280-char excerpt, outbound link). Falls back to labeled mock data with a warning when the backend is unreachable.
- **History panel:** "My Recent Searches" for logged-in users, click to re-run. *(Endpoint not implemented — QA H3.)*

### 3.7 Authentication (`/login`, `/register`)
- **Register:** email + password + confirm; POST `/api/register`; bcrypt(10) hash; duplicate email → 409 with friendly message; success modal → auto-redirect to Login after 3s.
- **Login:** POST `/api/login`; unknown email → 404 "Please register first"; wrong password → 401; success returns JWT (1h), stored in `localStorage` (`auth_token`, `auth_email`); success modal → redirect to Dashboard.
- **Session:** `getAuthHeader()` helper attaches `Authorization: Bearer <token>`. *(No route guards, no protected endpoints, no logout, no token refresh — QA M3. Spec intent: guard Trade/Settings, add logout to Navbar, apply `authenticateToken` server-side.)*

### 3.8 Settings (`/settings`), About (`/about`)
Static placeholders. Spec intent for Settings: default market/benchmark, sentiment on/off default, API keys.

---

## 4. API contract (FastAPI :8000, JSON)

TypeScript mirrors: `src/api/analysis.ts`, `backtest.ts`, `plan.ts`, `sentiment.ts`.

| Method & path | Params / body | Returns | Errors |
|---|---|---|---|
| GET `/api/health` | — | `{ok: true}` | — |
| GET `/api/analyze` | `symbol` (req), `days` (365), `include_sentiment` (true) | `AnalysisResult`: symbol, source, warning, generated_at, last_price, change_30d, stats{volatility_annualized, max_drawdown, high, low}, signals[], technical_score, sentiment{score, summary, articles, warning?}\|null, composite_score, verdict, chart{dates, closes, sma20, sma50} | 400 empty symbol, 422 <30 bars |
| GET `/api/history` | `symbol`, `days` | `{symbol, source, candles[{date,open,high,low,close,volume}], warning}` | 400 |
| GET `/api/strategies` | — | `{strategies: [{name, label, description, params}]}` | — |
| POST `/api/backtest` | `{symbol, strategy, params{}, days, initial_capital, commission_bps, benchmark_symbol?}` | `BacktestResult`: run config + `result{equity_curve, dates, trades, num_trades, win_rate\|null, final_equity, metrics}` + `benchmark{symbol, warning, equity_curve, final_equity, metrics}`; metrics = {total_return, cagr, sharpe, max_drawdown, volatility} | 400, 422 unknown strategy / bad params / short history |
| GET `/api/sectors` | — | `{sectors: [{id, label, market, tickers[{symbol,name}]}]}` | — |
| POST `/api/plan` | `{monthly_budget>0, months 3–120, sectors[], benchmark="0050"}` | `PlanResult`: inputs + warnings[] + allocation[] + simulation{month_labels, invested, portfolio_value, benchmark_value, summary} + projection + disclaimer | 422 unknown/empty sectors, insufficient history |
| GET `/api/sentiment` | `query` (req), `num_articles` 1–50, `model` | `{query, model, generated_at, summary{positive,neutral,negative,avg_compound}, articles[], warning?}` | empty query → empty payload with warning |

**Auth server (Express :3000):** POST `/api/register` `{email, password}` → 201/400/409/500 · POST `/api/login` `{email, password}` → 200 `{message, token}` /404/401/500.

**Not implemented but referenced by UI:** `GET /api/sentiment/history` (see QA H3).

---

## 5. Non-functional requirements

- **Availability without upstream data:** every price-driven feature must keep working offline via the synthetic fallback, and must visibly label degraded data (yellow warning banner). Never silently show synthetic data as real — this includes benchmarks (QA M4).
- **Correctness:** no look-ahead in backtests; benchmark always present; metrics rounded (4dp, Sharpe 2dp); TS types must match responses exactly (`npm run type-check` gates the build).
- **Performance targets:** analyze/backtest ≤ ~3s for 2y daily data (pure-Python engine is O(n) per indicator); sentiment currently exceeds acceptable latency (QA M6) — target ≤ 8s for 10 articles.
- **Security:** secrets via environment only (QA H4); CORS locked to the frontend origin in production (QA M9); rate-limited auth endpoints (QA M10); tokens verified on any future user-scoped endpoint.
- **Compliance/tone:** every simulated/projected figure carries the disclaimer; verdicts are labeled as model output, not advice.
- **Quality gates:** `npm run type-check`, `npm run lint`, `npm run test:unit`; backend smoke snippets in `.claude/skills/*/SKILL.md`.

---

## 6. Known gaps & roadmap (proposed)

**Now (broken → fix):** QA HIGH items — Dashboard chart pipeline (move to `/api/history`), sentiment history endpoint or removal, JWT secret, register proxy/validation.

**Next (product debt):**
- Real portfolio model behind the Dashboard (positions, cash, P&L) — replaces hardcoded balance cards.
- Route guards + logout + register link in Navbar; persist sentiment history per user (gives Login a purpose).
- Trade page: replace mocks with paper-trading loop driven by an existing strategy, or clearly label as "coming soon".
- Proper Tailwind v4 build pipeline; remove CDN scripts and dead scaffold code.

**Later (ideas):**
- Strategy parameter sweeps/optimization view; save & compare backtest runs.
- Alerts (verdict changes, signal crossovers) via scheduled jobs.
- FinBERT as an optional installed model; multilingual news for TW symbols.
- Export plan/backtest results (CSV/PNG).

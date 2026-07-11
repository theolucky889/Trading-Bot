# QA Report — Trading Bot

**Date:** 2026-07-10
**Scope:** Full site — Vue 3 frontend (`algorithmic-trading-bot/`), FastAPI backend (`backend/app.py` + `backend/python/`), Express auth server (`backend/server.js`), repo hygiene.
**Method:** Static code review of every view/API client/backend module, `npm run type-check` (✅ pass), `npx vitest run` (✅ 1/1 pass), FastAPI smoke tests via TestClient (health, strategies, sectors, analyze, backtest, plan, edge cases), and a Node.js reproduction of the suspected chart bug (confirmed).

Severity definitions:
- **HIGH** — user-visible feature is broken, crashes, or a security exposure.
- **MID** — degraded/incorrect behavior, violated project convention, or hardening gap.
- **LOW** — polish, dead code, deprecations, minor text/UX issues.

---

## HIGH

### H1. Dashboard charts crash on any control change — swallowed `destroy()` loop (ASI bug)
**File:** `algorithmic-trading-bot/src/chart.js:15-18`
```js
if (!priceCtx || !volumeCtx) return console.error('canvas not found')

// 1️⃣ Destroy any existing charts
[stockPriceChartId, volumeChartId].forEach(...)
```
JavaScript does **not** insert a semicolon before `[`, so this parses as
`return console.error(...)[stockPriceChartId, volumeChartId].forEach(...)`.
Consequences (verified with a Node repro):
- When canvases **exist**, the destroy loop is part of the skipped `return` and **never runs** → re-rendering a chart on the same canvas throws Chart.js *"Canvas is already in use"*. Changing graph type, category, or stock selection on the Dashboard breaks the charts.
- When canvases are **missing**, it throws `TypeError: Cannot read properties of undefined` instead of logging.

**Fix:** add a semicolon / restructure: `;[stockPriceChartId, volumeChartId].forEach(...)` or use a normal `for` loop, and `return` on its own line.

### H2. Dashboard US-stock data is dead: missing API key + retired Alpha Vantage endpoint
**Files:** `src/api/quotes.js:3-20`, `src/api.js:4-14`, no `.env` file exists
- `VITE_ALPHA_KEY` is read from env but **no `.env` exists** → requests go out with `apikey=undefined`.
- `TIME_SERIES_DAILY_ADJUSTED` is a **premium-only** Alpha Vantage endpoint; free keys get an error payload.
- Either way `data['Time Series (Daily)']` is `undefined` and `Object.keys(series)` throws → Dashboard price charts render blank with only a console error. No error is shown to the user.

**Fix:** point the Dashboard at the project's own `/api/history` endpoint (it already exists, has fallbacks, and returns warnings) and delete the Alpha Vantage path, or provision a key + use `TIME_SERIES_DAILY`.

### H3. "My Recent Searches" calls an endpoint that does not exist
**File:** `src/components/SentimentEngine.vue:313` → `GET /api/sentiment/history`
No such route exists on FastAPI or the Express server (smoke test confirms **404**). The history panel on Trade → AI Engine shows *"History API failed: 404"* for every logged-in user, and `loadHistory()` is re-invoked after **every** analyze run. The UI also reads `item._id`, `numArticles`, `createdAt` — a MongoDB-shaped contract nobody implemented.
**Fix:** implement the endpoint (persist runs per user) or remove the history panel until it exists.

### H4. Hardcoded JWT secret committed to the repo
**File:** `backend/server.js:10` — `const SECRET_KEY = 'your_secret_key'`
Anyone can mint valid tokens. Also no env-based config anywhere in the auth server (port, Mongo URL all hardcoded).
**Fix:** load from `process.env.JWT_SECRET` (fail fast if unset); rotate the secret.

---

## MID

### M1. Registration silently does nothing when passwords don't match
**File:** `src/views/RegisterView.vue:112-115` — mismatch hits `return` without setting `errorMessage`. User clicks "Create account" and nothing happens. Inputs also lack `required`, so empty email/password submits to the server.

### M2. RegisterView bypasses the dev proxy with a hardcoded URL
**File:** `src/views/RegisterView.vue:118` — `fetch('http://localhost:3000/api/register')` while LoginView correctly uses `/api/login`. Registration breaks for any non-localhost access (LAN, prod build) and depends on the Express CORS config.

### M3. Authentication is decorative — nothing is actually protected
- No route guards in `src/router/index.ts`; every page works logged out.
- The JWT is stored but no API validates it; FastAPI has zero auth.
- `authenticateToken` in `server.js:77-86` is **never applied** to any route, and it verifies the raw `Authorization` header **including the `Bearer ` prefix**, so it would always 403 if it were ever used.

### M4. Backtest view hides the benchmark's data warning (project-convention violation)
**File:** `src/views/BacktestView.vue` — displays `result.warning` but never `result.benchmark.warning`. CLAUDE.md: *"the UI must surface that warning, never hide it."* A backtest can show a real strategy beating a **synthetic** 0050 benchmark with no indication.

### M5. Synthetic data is not actually deterministic
**File:** `backend/python/quant/data.py:186` — `random.Random(hash(symbol.upper()) & 0xFFFFFFFF)`. Python salts `str.__hash__` per process (`PYTHONHASHSEED`), so "deterministic per symbol so charts/backtests are reproducible offline" is false across server restarts.
**Fix:** use a stable hash, e.g. `zlib.crc32(symbol.encode())` or `hashlib.md5`.

### M6. Sentiment analysis can take 30–80+ seconds
**File:** `backend/python/sentiment_analysis.py:47-60, 101` — for each article the backend fetches the full article page sequentially (timeout 8s each, up to 50 articles). `/api/analyze` includes sentiment **by default**, so the flagship Analysis page inherits this latency with no frontend timeout or progress indication.
**Fix:** parallelize with a thread pool + short cap, or analyze titles only by default.

### M7. Tailwind/Vue/axios loaded twice via CDN in index.html
**File:** `algorithmic-trading-bot/index.html`
- Styling relies on the **Tailwind Play CDN** (`cdn.tailwindcss.com`) — explicitly not for production (console warning, runtime JIT, FOUC) while `tailwindcss@4` sits installed but unconfigured and unimported.
- A second full copy of **Vue 3.2.31** (global build) and **axios 0.27** are loaded from CDN alongside the bundled Vue 3.5 / axios 0.21 — dead weight and version-drift risk.
- `styles.css` and `icon.png` are referenced but don't exist in `public/` → 404s on every load.

### M8. Repo hygiene: 3,195 `backend/node_modules` files tracked in git
- `backend/node_modules/**` was committed before `backend/.gitignore` was added and is still tracked.
- Root `.gitignore` contains an absolute Windows path (`E:\Github\...`), which is not a valid ignore pattern.
- `backend/__pycache__/` shows as untracked (nothing ignores `__pycache__/`).
**Fix:** `git rm -r --cached backend/node_modules`, add proper `__pycache__/`, fix root `.gitignore`.

### M9. Invalid CORS combination on FastAPI
**File:** `backend/app.py:20-26` — `allow_origins=["*"]` together with `allow_credentials=True` violates the CORS spec; browsers reject credentialed requests against a wildcard origin. Works today only because nothing sends credentials. Marked "tighten in prod" but there is no prod configuration path.

### M10. Auth server hardening gaps
**File:** `backend/server.js`
- `mongoose.connect()` result unhandled — if MongoDB is down the server starts anyway and every register/login 500s with a generic message.
- No rate limiting / lockout on `/api/login` (brute-forceable), no password policy, no server-side email format validation.
- `useNewUrlParser`/`useUnifiedTopology` are deprecated no-ops on modern mongoose.

### M11. Trade page is an unstyled mock
**File:** `src/views/TradeView.vue` — classes `tradebot-container`, `left-sidebar`, `active` etc. have **no CSS anywhere** (no `<style>` block, not Tailwind), so the sidebar/tab layout renders as a plain unstyled list. All data is hardcoded; "Stop Trading" fires a placeholder `alert()`; Performance/Trades/Settings/Help tabs are empty.

### M12. Outdated dependencies with known advisories
**File:** `algorithmic-trading-bot/package.json` — `axios ^0.21` (known SSRF/ReDoS advisories in 0.21.x), `chart.js ^3.0.0` (v4 is current). The unused CDN axios 0.27 compounds the confusion.

---

## LOW

| # | Issue | Location |
|---|-------|----------|
| L1 | Navbar has no Register link, no active-route highlighting, no logout/logged-in indicator | `src/components/Navbar.vue` |
| L2 | Dashboard sidebar duplicates the navbar with dead `<a href="#">` links; balance/progress widgets are hardcoded numbers | `src/views/DashboardView.vue:5-24, 33-56, 195-201` |
| L3 | Dead scaffold code shipped: `HelloWorld`, `TheWelcome`, `WelcomeItem`, icon components, `stores/counter.ts`, legacy `src/Dashboard.vue`, unused `HomeView`, unimported `assets/main.css` | `src/` |
| L4 | Only one unit test exists and it tests the Vite scaffold's `HelloWorld`, not app code; no backend tests; Cypress configured but no meaningful e2e specs | `src/components/__tests__/` |
| L5 | Pluralization bug: renders "1 query / 3 query**ies**" | `SentimentEngine.vue:14` |
| L6 | `change_30d` uses `closes[-30]` (29 trading bars ≈ 6 weeks), labeled "30d" | `harness.py:143`, `AnalysisView.vue:65` |
| L7 | Deprecated `datetime.utcnow()` / `utcfromtimestamp()` (removal-tracked in Python 3.12+) | `app.py`, `harness.py`, `data.py`, `sentiment_analysis.py` |
| L8 | Backtest/Analysis "Period" options say months/years but backend mixes calendar days and trading bars (365 "days" ⇒ ~252 bars) | `data.py:114-124`, views |
| L9 | Login/Register inputs lack `required`/client validation; login success modal + auto-redirect race (both fire) | `LoginView.vue`, `RegisterView.vue` |
| L10 | `/av` and `/twse` proxy rules + `src/api.js` `fetchStockData`/mock volume functions are legacy, unused by the current API layer | `vite.config.ts:26-36`, `src/api.js` |
| L11 | Sentiment "FinBERT" appears in two dropdowns but silently falls back to VADER (warning only surfaced in some paths) | `SentimentEngine.vue:46`, `sentiment_analysis.py:88-93` |
| L12 | `<meta http-equiv="X-UA-Compatible" content="IE=edge">` obsolete; `icon.png` favicon referenced but only `favicon.ico` exists | `index.html` |

---

## Verification results

| Check | Result |
|---|---|
| `npm run type-check` (vue-tsc) | ✅ pass |
| `npx vitest run` | ✅ 1/1 pass (scaffold test only) |
| `GET /api/health`, `/api/strategies`, `/api/sectors` | ✅ 200, shapes match TS types |
| `GET /api/analyze` (synthetic fallback) | ✅ 200, `warning` populated |
| `POST /api/backtest` (bad params / neg days / empty sectors) | ✅ 422 / clamped / 422 |
| `GET /api/sentiment/history` | ❌ 404 (H3 confirmed) |
| chart.js ASI repro (Node) | ❌ destroy loop never runs; TypeError on missing canvas (H1 confirmed) |

## Recommended fix order
1. **H1 + H2** — Dashboard is the landing page and is visibly broken.
2. **H4 + M2 + M1** — auth correctness/security (secret, hardcoded URL, silent validation).
3. **H3** — implement or remove sentiment history.
4. **M4 + M5** — data-integrity conventions (benchmark warning, deterministic synthetic).
5. **M7 + M8** — build/repo hygiene (Tailwind pipeline, tracked node_modules).
6. Remaining MID hardening, then LOW cleanups opportunistically.

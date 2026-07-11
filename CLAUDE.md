# Trading Bot

Algorithmic trading assistant: Vue 3 dashboard + FastAPI analysis/backtest/auth
backend. Supports US stocks, Taiwan stocks (TWSE), and crypto.

## Repository layout

```
algorithmic-trading-bot/   Vue 3 + TS + Vite + Tailwind frontend
  src/api/                 typed API clients (analysis.ts, backtest.ts, sentiment.ts, auth.ts)
  src/views/               route views (AnalysisView, BacktestView, DashboardView, ...)
  src/router/index.ts      routes — new views also need a Navbar.vue link
backend/
  app.py                   FastAPI app (analysis, backtest, sentiment + auth, port 8000)
  auth.py                  self-contained auth: register/login/session +
                           per-user sentiment history (SQLite, stdlib JWT)
  data/trading_bot.db      auth SQLite DB (auto-created, gitignored)
  server.js                LEGACY optional Express+MongoDB auth (not wired to proxy)
  python/sentiment_analysis.py   VADER sentiment over Google News RSS
  python/quant/            quant engine: data.py, indicators.py, strategies.py,
                           backtest.py, harness.py (see .claude/skills/ docs)
  requirements.txt         Python deps
```

## Running

```bash
# Backend: analysis, backtest, sentiment AND auth (from repo root).
# No MongoDB / Node server needed — auth is FastAPI + SQLite (backend/auth.py).
# Set JWT_SECRET in production (see backend/.env.example); otherwise an
# ephemeral secret is generated at startup and tokens reset on restart.
python -m uvicorn backend.app:app --reload --port 8000

# Frontend (all /api/* → :8000)
cd algorithmic-trading-bot && npm run dev

# LEGACY only (optional, needs MongoDB; NOT wired to the dev proxy):
#   node backend/server.js
```

## Commands

- Frontend type-check: `cd algorithmic-trading-bot && npm run type-check` (must pass; build runs it)
- Frontend build: `npm run build` · unit tests: `npm run test:unit` · lint: `npm run lint`
- Backend smoke tests: verification snippets in `.claude/skills/stock-analysis/SKILL.md`
  and `.claude/skills/quant-backtest/SKILL.md`

## Conventions

- Quant code is pure Python (stdlib + requests) — no numpy/pandas by design.
- Price data degrades gracefully: yahoo → stooq → deterministic synthetic with
  a `warning` field; the UI must surface that warning, never hide it.
- Backtests use next-bar execution (no look-ahead) and always include a
  buy-and-hold benchmark.
- API response shapes are mirrored 1:1 by the TypeScript types in `src/api/`;
  change both sides in the same task.
- UI idiom: dark Tailwind (gray-900/800 gradients, `rounded-3xl ring-1
  ring-gray-700/40` cards, indigo accents), charts via `chart.js/auto` with
  instance cleanup.

## 하네스: Stock Analysis (analysis + backtest agent team)

**목표:** 주식 분석·퀀트 백테스트 기능을 에이전트 팀으로 안전하게 확장한다.

**트리거:** 분석 하네스/지표/시그널/전략/백테스트/Analysis·Backtest UI 관련
멀티스텝 작업 요청 시 `stock-analysis-orchestrator` 스킬을 사용하라.
단일 파일 질문·단순 조회는 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-05 | 초기 구성: 에이전트 4종(market-analyst, quant-developer, fullstack-integrator, qa-verifier) + 스킬 3종, 퀀트 엔진/백테스트 API/Analysis·Backtest 뷰 구축 | 전체 | - |
| 2026-07-05 | trend_momentum 전략 + 백테스트 benchmark_symbol(0050 비교) + 투자 플래너(quant/planner.py, /api/plan, /api/sectors, PlanView) 추가 | strategies.py, backtest.py, planner.py, app.py, 프론트 | "0050을 이길 전략 + 월 예산/섹터/기간 투자 플랜" 요청 |
| 2026-07-10 | QA/PM 수정 배치: H1 chart.js ASI destroy 버그, H2 Dashboard→/api/history 이관(src/api/history.ts, Alpha Vantage 삭제), H3 /api/sentiment/history GET·POST(Express+Mongo, JWT 보호, vite 프록시), H4 JWT_SECRET env 필수화(.env.example), M1/M2 Register 검증·프록시 경로, M3 라우트 가드(/trade,/settings)+로그아웃, M4 벤치마크 warning 표시, M5 synthetic seed zlib.crc32, L1 Navbar 개선 | server.js, data.py, chart.js, DashboardView, RegisterView, LoginView, Navbar, BacktestView, SentimentEngine, router, vite.config.ts | docs/QA_REPORT.md + docs/PRODUCT_SPEC.md 로드맵 "Now/Next" 구현 요청 |
| 2026-07-10 | QA 잔여 이슈 배치: M6 감성분석 병렬화(ThreadPool 8 + 10s 예산, 30–80s→~2.4s), M7/L12 Tailwind v4 빌드 파이프라인(@tailwindcss/vite, CDN 스크립트 제거), M8 node_modules 언트래킹+.gitignore 정비, M9 CORS_ORIGINS env화, M10 로그인 rate limit+비밀번호 정책, M11 TradeView Tailwind 재스타일, M12 axios 1.x/chart.js 4 업그레이드, L2–L11 정리(스캐폴드 삭제, 의미있는 테스트 7개, change_30d 달력일 기준, utcnow 제거, 복수형/FinBERT 경고 등), 레거시 styles.css 삭제+Login 버튼 Tailwind화 | sentiment_analysis.py, harness.py, data.py, app.py, server.js, index.html, main.ts, vite.config.ts, TradeView, DashboardView, SentimentEngine, Login/RegisterView, 테스트 | "QA가 발견한 이슈 전부 수정" 요청; Playwright 비주얼 스모크로 4개 라우트 검증 |
| 2026-07-10 | 자체 인증 백엔드: backend/auth.py(FastAPI+SQLite, stdlib PBKDF2/HS256 JWT, 로그인 rate limit) — /api/register·login·me + /api/sentiment/history 이전, 프록시 단일화(/api→:8000), server.js LEGACY 표시(MongoDB 불필요) | auth.py, app.py, vite.config.ts, server.js, .env.example | "login/sign up 처리 백엔드 생성" 요청, FastAPI+SQLite 선택; Playwright E2E(가입→로그인→가드→히스토리→로그아웃) 검증 |
| 2026-07-11 | 페이퍼 트레이딩: quant/paper.py 엔진(가짜 $100k·실시간 실가격 체결, synthetic 거래 거부, STRATEGIES 재사용, lazy tick 백필, 수수료 10bps, 자금 보존 검증) + /api/paper/* (JWT 보호) + src/api/paper.ts + TradeView 전면 재구축(계좌/포지션/봇/수동거래/거래내역/성과차트, 15s 폴링). 검증 중 버그 2건 수정: 신규 봇 과거 전체 리플레이 → 최신 바부터 시작, JWT 시크릿 이중 생성 → 단일 해석 후 주입 | paper.py, app.py, auth.py 연동, paper.ts, TradeView.vue | "데모 계정 가짜 돈 + 실데이터 가격/거래로 트레이드봇" 요청; TestClient 16/16 + Playwright 브라우저 E2E 검증 |
| 2026-07-11 | TWSE 퀀트 스크리너: quant/screener.py(42종목 유니버스, 하네스 재사용 기술점수 랭킹, 병렬 스캔 ~14s + 10분 캐시, synthetic 랭킹 배제) + GET /api/screener + ScreenerView(/screener, 정렬 테이블·섹터/버딕트/RSI/추세 필터·검색) + 행별 Analyze/Backtest/Bot 딥링크(query symbol 프리필, Analysis 자동 실행) | screener.py, app.py, screener.ts, ScreenerView.vue, Navbar, router, Analysis/Backtest/TradeView 프리필 | "TWSE 종목 보여주고 뭘 거래할지 고르는 인터랙티브 퀀트 분석" 요청; Playwright로 42행 렌더·검색·딥링크 검증 |
| 2026-07-11 | **프로젝트 이관**: backend/ 전체(quant 엔진·auth·paper·screener·planner·sentiment + SQLite 데이터)를 E:\Github\Quantitative_Trading으로 복사·흡수. 그쪽 Express(:3000)가 공개 진입점, FastAPI는 내부 사이드카(127.0.0.1:8000, /api/quant/* 프록시, INTERNAL_KEY 신뢰 헤더). 엔진 융합: T86 기관 수급 시그널 + 대만 실비용 모델 추가(대상 저장소에만). 이 저장소는 Vue 프론트 포함 원본 그대로 유지(아카이브 후보) | → Quantitative_Trading | owner: "모든 기능을 Quantitative_Trading으로 병합, UI는 그쪽 것 유지, 1개 프로젝트로 작업" |

from __future__ import annotations

import datetime as dt
import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .auth import _resolve_jwt_secret, build_auth_router, decode_token
from .python.sentiment_analysis import analyze_market_sentiment
from .python.quant import paper
from .python.quant.backtest import run_backtest
from .python.quant.data import get_price_series
from .python.quant.harness import analyze_stock
from .python.quant.planner import build_plan, sector_catalog
from .python.quant.screener import screen
from .python.quant.strategies import STRATEGIES, public_catalog

app = FastAPI(title="Trading Bot API", version="0.2.0")

# CORS is driven by the CORS_ORIGINS env var (comma-separated list of exact
# origins). Defaults to the Vite dev server. A wildcard "*" together with
# credentials is invalid per the CORS spec (browsers reject credentialed
# requests against a wildcard origin), so credentials are only enabled when an
# explicit, non-wildcard origin list is configured.
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
_allow_credentials = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth (register / login / session + per-user sentiment history) ──
# Self-contained FastAPI + SQLite auth (backend/auth.py). Replaces the legacy
# Express + MongoDB server (backend/server.js, no longer wired to the proxy).
#
# The JWT secret MUST be resolved exactly once and injected into the auth
# router: _resolve_jwt_secret() generates a fresh ephemeral secret per call
# when JWT_SECRET is unset, so calling it twice would leave the auth router
# minting tokens the paper endpoints reject.
_JWT_SECRET = _resolve_jwt_secret()
app.include_router(build_auth_router(jwt_secret=_JWT_SECRET))

# Point the paper-trading engine at the SAME SQLite file the auth store uses so
# tokens and demo accounts live in one DB. PAPER_DB_PATH wins if set explicitly;
# otherwise we align with AUTH_DB_PATH (so a test that isolates auth isolates
# paper too), falling back to the module's default (backend/data/trading_bot.db).
_paper_db_path = (
    os.getenv("PAPER_DB_PATH")
    or os.getenv("AUTH_DB_PATH")
    or paper._DEFAULT_DB_PATH
)
paper.configure(_paper_db_path)


class PaperHTTPError(HTTPException):
    """HTTPException whose body is rendered as ``{message}`` (not ``{detail}``).

    The paper/auth-facing endpoints return user-visible errors keyed by
    ``message`` so the Vue client can read ``data.message`` consistently across
    login, register, and the Trade page.
    """


@app.exception_handler(PaperHTTPError)
def _paper_http_error_handler(_request, exc: PaperHTTPError):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


def require_email(authorization: Optional[str] = Header(default=None)) -> str:
    """Resolve the caller's email from a Bearer token or raise 401.

    Reuses auth.decode_token with the shared JWT secret. The 401 body is keyed
    by ``message`` to match the auth router's convention (the Vue client reads
    ``data.message``) and so the frontend can detect an expired token and clear
    its storage.
    """
    token = authorization or ""
    if token.startswith("Bearer "):
        token = token[len("Bearer "):].strip()
    payload = decode_token(token, _JWT_SECRET) if token else None
    if not payload or not payload.get("email"):
        raise PaperHTTPError(status_code=401, detail="Unauthorized")
    return payload["email"]


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/sentiment")
def sentiment(query: str, num_articles: int = 10, model: str = "vader"):
    query = (query or "").strip()
    if not query:
        return {
            "query": "",
            "model": model,
            "generated_at": dt.datetime.now(dt.timezone.utc)
            .replace(tzinfo=None)
            .isoformat()
            + "Z",
            "summary": {"positive": 0, "neutral": 0, "negative": 0, "avg_compound": 0},
            "articles": [],
            "warning": "Empty query",
        }

    num_articles = max(1, min(int(num_articles), 50))
    return analyze_market_sentiment(query=query, num_articles=num_articles, model=model)


# ── Stock analysis harness ──────────────────────────────────────────


@app.get("/api/analyze")
def analyze(symbol: str, days: int = 365, include_sentiment: bool = True):
    """Full analysis: indicators + signals + sentiment -> composite verdict."""
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    try:
        return analyze_stock(symbol, days=days, include_sentiment=include_sentiment)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/history")
def history(symbol: str, days: int = 365):
    """Raw daily OHLCV for charting."""
    symbol = (symbol or "").strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    return get_price_series(symbol, days).to_dict()


# ── Quant backtesting ───────────────────────────────────────────────


@app.get("/api/strategies")
def strategies():
    return {"strategies": public_catalog()}


class BacktestRequest(BaseModel):
    symbol: str
    strategy: str = "sma_crossover"
    params: dict = Field(default_factory=dict)
    days: int = 365
    initial_capital: float = 10_000.0
    commission_bps: float = 10.0
    benchmark_symbol: Optional[str] = None  # e.g. "0050" to compare vs holding the index ETF


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    symbol = req.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")
    if req.strategy not in STRATEGIES:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown strategy '{req.strategy}'. Available: {', '.join(STRATEGIES)}",
        )
    try:
        return run_backtest(
            symbol=symbol,
            strategy=req.strategy,
            params=req.params,
            days=max(60, min(req.days, 2000)),
            initial_capital=max(100.0, req.initial_capital),
            commission_bps=max(0.0, min(req.commission_bps, 500.0)),
            benchmark_symbol=req.benchmark_symbol,
        )
    except TypeError as exc:
        # Bad strategy params (unexpected keyword etc.)
        raise HTTPException(status_code=422, detail=f"Invalid params: {exc}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ── Quant screener ──────────────────────────────────────────────────
# Public market-data endpoint (no auth): ranks a universe by technicals-only
# composite score. The first cold scan takes ~15-25s; warm calls hit the
# in-module TTL cache (cached: true). refresh=true bypasses the cache.


@app.get("/api/screener")
def screener(market: str = "tw", days: int = 365, refresh: bool = False):
    market = (market or "").strip().lower()
    if market not in ("tw",):
        raise HTTPException(
            status_code=422,
            detail=f"Unknown market '{market}'. Available: tw",
        )
    days = max(30, min(int(days), 2000))
    return screen(market=market, days=days, refresh=refresh)


# ── Investment planner ──────────────────────────────────────────────


@app.get("/api/sectors")
def sectors():
    return {"sectors": sector_catalog()}


class PlanRequest(BaseModel):
    monthly_budget: float = Field(gt=0)
    months: int = Field(ge=3, le=120)
    sectors: list[str]
    benchmark: str = "0050"


@app.post("/api/plan")
def plan(req: PlanRequest):
    try:
        return build_plan(
            monthly_budget=req.monthly_budget,
            months=req.months,
            sectors=req.sectors,
            benchmark=req.benchmark or "0050",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# ── Paper trading (demo account) ────────────────────────────────────
# All Bearer-protected via require_email (reuses auth.decode_token). PaperError
# maps to HTTP 422 with a {message} body (PaperHTTPError), matching the auth
# convention the Vue client reads. tick-on-read: the state endpoint advances
# bots before returning the snapshot.


def _paper_guard(fn):
    """Run a paper engine call, mapping PaperError → 422 {message}."""
    try:
        return fn()
    except paper.PaperError as exc:
        raise PaperHTTPError(status_code=422, detail=str(exc))


@app.get("/api/paper/state")
def paper_state(email: str = Depends(require_email)):
    # tick-on-read: advance running bots over new real bars, then snapshot.
    _paper_guard(lambda: paper.tick(email))
    return _paper_guard(lambda: paper.get_state(email))


@app.get("/api/paper/trades")
def paper_trades(limit: int = 50, email: str = Depends(require_email)):
    return _paper_guard(lambda: paper.get_trades(email, limit=limit))


class PaperBotRequest(BaseModel):
    symbol: str
    strategy: str = "sma_crossover"
    params: dict = Field(default_factory=dict)
    allocated_cash: float = 10_000.0


@app.post("/api/paper/bots")
def paper_create_bot(req: PaperBotRequest, email: str = Depends(require_email)):
    return _paper_guard(
        lambda: paper.create_bot(
            email=email,
            symbol=req.symbol,
            strategy=req.strategy,
            params=req.params,
            allocated_cash=req.allocated_cash,
        )
    )


class PaperStatusRequest(BaseModel):
    status: str


@app.post("/api/paper/bots/{bot_id}/status")
def paper_bot_status(
    bot_id: int, req: PaperStatusRequest, email: str = Depends(require_email)
):
    return _paper_guard(lambda: paper.set_bot_status(email, bot_id, req.status))


@app.delete("/api/paper/bots/{bot_id}")
def paper_delete_bot(bot_id: int, email: str = Depends(require_email)):
    return _paper_guard(lambda: paper.delete_bot(email, bot_id))


class PaperTradeRequest(BaseModel):
    symbol: str
    side: str
    notional_usd: float


@app.post("/api/paper/trade")
def paper_manual_trade(req: PaperTradeRequest, email: str = Depends(require_email)):
    return _paper_guard(
        lambda: paper.manual_trade(email, req.symbol, req.side, req.notional_usd)
    )


@app.post("/api/paper/reset")
def paper_reset(email: str = Depends(require_email)):
    return _paper_guard(lambda: paper.reset(email))

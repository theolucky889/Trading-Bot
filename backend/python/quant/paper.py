"""Paper-trading (demo account) engine.

Fake money, REAL market prices, simulated bot trades. Backs the Trade page.

Design mirrors the rest of the quant stack:

  * Prices come from :mod:`.data` (Yahoo / Binance / Stooq). If the resolved
    source is ``synthetic`` we DO NOT execute — synthetic prices are plumbing
    fixtures, never real fills. The state/warnings surface that instead.
  * Bot signals reuse the strategy registry in :mod:`.strategies` (no
    duplicated logic), long/flat, next-bar close execution (a signal decided
    on bar *t* fills at the close of *t+1*), commission 10 bps per position
    change — consistent with :mod:`.backtest`.
  * No background threads. ``tick(email)`` lazily advances every running bot
    over all NEW daily bars since its ``last_processed_date`` (backfill:
    replays real historical bars the user missed and records the trades the
    bot would have made at those bars' real closes). Daily equity snapshots
    are written during tick.

Storage is SQLite (stdlib ``sqlite3``) in the same ``backend/data/trading_bot.db``
the auth module uses, with a module-level lock-guarded connection opened
``check_same_thread=False`` + WAL — same convention as ``auth.AuthStore``. The
DB path is injectable so tests can point at a temp file.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from .data import PriceSeries, get_price_series
from .strategies import STRATEGIES, get_strategy

# ── Constants ────────────────────────────────────────────────────────

INITIAL_CASH = 100_000.0
COMMISSION_BPS = 10.0
FEE = COMMISSION_BPS / 10_000  # fraction charged per position change

# How much daily history to pull when advancing bots. ~2 years covers deep
# backfills (a bot backdated many months) while staying within the data layer.
BOT_HISTORY_DAYS = 730

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "trading_bot.db",
)


# ── Errors ───────────────────────────────────────────────────────────


class PaperError(ValueError):
    """Bad input at the API boundary — the caller maps this to HTTP 422."""


# ── Store ────────────────────────────────────────────────────────────


class PaperStore:
    """Lock-guarded SQLite wrapper for paper-trading state.

    A single module-level lock serialises access so the store is safe under
    FastAPI's threaded pool. The connection is opened ``check_same_thread=False``
    with WAL — matching ``auth.AuthStore``.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.RLock()
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS paper_accounts (
                    email        TEXT PRIMARY KEY,
                    cash         REAL NOT NULL,
                    initial_cash REAL NOT NULL,
                    created_at   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_bots (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    email               TEXT NOT NULL,
                    symbol              TEXT NOT NULL,
                    strategy            TEXT NOT NULL,
                    params_json         TEXT NOT NULL,
                    allocated_cash      REAL NOT NULL,
                    status              TEXT NOT NULL,
                    position_qty        REAL NOT NULL DEFAULT 0,
                    avg_price           REAL,
                    last_processed_date TEXT,
                    created_at          TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_trades (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    email       TEXT NOT NULL,
                    bot_id      INTEGER,
                    symbol      TEXT NOT NULL,
                    side        TEXT NOT NULL,
                    qty         REAL NOT NULL,
                    price       REAL NOT NULL,
                    commission  REAL NOT NULL,
                    executed_at TEXT NOT NULL,
                    kind        TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS paper_positions (
                    email     TEXT NOT NULL,
                    symbol    TEXT NOT NULL,
                    qty       REAL NOT NULL,
                    avg_price REAL NOT NULL,
                    PRIMARY KEY (email, symbol)
                );

                CREATE TABLE IF NOT EXISTS paper_equity (
                    email  TEXT NOT NULL,
                    date   TEXT NOT NULL,
                    equity REAL NOT NULL,
                    PRIMARY KEY (email, date)
                );

                CREATE INDEX IF NOT EXISTS idx_paper_trades_email
                    ON paper_trades (email, executed_at DESC, id DESC);
                CREATE INDEX IF NOT EXISTS idx_paper_bots_email
                    ON paper_bots (email);
                """
            )
            self._conn.commit()


# Module-level singleton store, lazily bound to the default DB path.
_store: Optional[PaperStore] = None


def _get_store() -> PaperStore:
    global _store
    if _store is None:
        _store = PaperStore(os.getenv("PAPER_DB_PATH", _DEFAULT_DB_PATH))
    return _store


def configure(db_path: str) -> PaperStore:
    """Point the module at a specific SQLite path (used by tests)."""
    global _store
    _store = PaperStore(db_path)
    return _store


# ── Helpers ──────────────────────────────────────────────────────────


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat() + "Z"


def _norm_email(email: str) -> str:
    e = (email or "").strip().lower()
    if not e:
        raise PaperError("email is required")
    return e


def _norm_symbol(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if not s:
        raise PaperError("symbol is required")
    return s


def _ensure_account(store: PaperStore, email: str) -> sqlite3.Row:
    """Return the account row, auto-creating it with $100k on first use."""
    with store._lock:
        cur = store._conn.execute(
            "SELECT email, cash, initial_cash, created_at FROM paper_accounts WHERE email = ?",
            (email,),
        )
        row = cur.fetchone()
        if row is None:
            store._conn.execute(
                "INSERT INTO paper_accounts (email, cash, initial_cash, created_at) "
                "VALUES (?, ?, ?, ?)",
                (email, INITIAL_CASH, INITIAL_CASH, _now_iso()),
            )
            store._conn.commit()
            cur = store._conn.execute(
                "SELECT email, cash, initial_cash, created_at FROM paper_accounts WHERE email = ?",
                (email,),
            )
            row = cur.fetchone()
        return row


def _validate_strategy(strategy: str, params: Optional[dict]) -> dict:
    """Validate strategy name + params against the registry (like backtest does).

    Raises :class:`PaperError` (HTTP 422 at the boundary) on unknown strategy or
    param that the strategy function does not accept. Returns the merged params
    dict (defaults overlaid with the caller's overrides).
    """
    if strategy not in STRATEGIES:
        raise PaperError(
            f"Unknown strategy '{strategy}'. Available: {', '.join(STRATEGIES)}"
        )
    defaults = dict(STRATEGIES[strategy]["params"])
    params = params or {}
    if not isinstance(params, dict):
        raise PaperError("params must be an object")
    for key in params:
        if key not in defaults:
            raise PaperError(
                f"Unknown param '{key}' for strategy '{strategy}'. "
                f"Accepted: {', '.join(defaults) or '(none)'}"
            )
    merged = {**defaults, **params}
    # Smoke-run the strategy on a tiny series to surface bad param types early.
    try:
        get_strategy(strategy)([1.0] * 5, **merged)
    except PaperError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface as a 422-style error
        raise PaperError(f"Invalid params for '{strategy}': {exc}") from exc
    return merged


def _price_series_for(symbol: str, days: int = BOT_HISTORY_DAYS) -> PriceSeries:
    return get_price_series(symbol, days)


def _bot_market_value(bot: sqlite3.Row, price: Optional[float]) -> float:
    qty = bot["position_qty"] or 0.0
    if qty <= 0 or price is None:
        return 0.0
    return qty * price


# ── Bot advancement (the core tick loop) ─────────────────────────────


def _advance_bot(store: PaperStore, bot: sqlite3.Row) -> Dict[str, Any]:
    """Replay every NEW real daily bar for one running bot.

    Applies next-bar execution: the target decided at bar *t* fills at the
    close of *t+1*. Only bars strictly after ``last_processed_date`` are
    processed, so repeated ticks are idempotent. Bot cash lives inside the
    bot's own ledger (``allocated_cash`` fully deployed when long, back to cash
    when flat); the account cash is untouched by bot trades.

    Returns a per-bot summary dict incl. ``source``/``warning`` and how many
    trades/bars were processed.
    """
    email = bot["email"]
    symbol = bot["symbol"]
    strategy = bot["strategy"]
    params = json.loads(bot["params_json"])

    series = _price_series_for(symbol)
    summary: Dict[str, Any] = {
        "bot_id": bot["id"],
        "symbol": symbol,
        "source": series.source,
        "warning": series.warning,
        "new_trades": 0,
        "bars_processed": 0,
    }

    # Real data only: never execute on synthetic prices.
    if series.source == "synthetic":
        summary["warning"] = (
            series.warning
            or f"No real market data for {symbol}; bot idle (no trades executed)."
        )
        return summary

    candles = series.candles
    if len(candles) < 2:
        summary["warning"] = f"Not enough real history for {symbol}; bot idle."
        return summary

    closes = [c.close for c in candles]
    dates = [c.date for c in candles]

    # Target positions over the whole real series (strategy sees only closes).
    positions = get_strategy(strategy)(closes, **params)

    last_done = bot["last_processed_date"]
    qty = bot["position_qty"] or 0.0
    avg_price = bot["avg_price"]
    # Reconstruct the bot's cash ledger: when flat it holds its full allocation
    # net of past commissions; when long that cash is deployed into qty.
    # We track it forward from the DB state.
    holding = qty > 0

    new_trades: List[dict] = []
    processed_up_to = last_done

    for i in range(1, len(candles)):
        exec_date = dates[i]
        # Skip bars already processed (idempotent backfill).
        if last_done is not None and exec_date <= last_done:
            processed_up_to = exec_date
            continue

        price = closes[i]
        target = positions[i - 1]  # decision from prior bar, fills at today's close
        summary["bars_processed"] += 1

        if target == 1 and not holding:
            # Deploy the bot's full free cash into the position.
            free_cash = _bot_free_cash(store, bot["id"])
            cost = free_cash * FEE
            deploy = free_cash - cost
            if deploy > 0 and price > 0:
                buy_qty = deploy / price
                qty = buy_qty
                avg_price = price
                holding = True
                new_trades.append(
                    {
                        "email": email,
                        "bot_id": bot["id"],
                        "symbol": symbol,
                        "side": "buy",
                        "qty": buy_qty,
                        "price": price,
                        "commission": cost,
                        "executed_at": exec_date,
                        "kind": "bot",
                    }
                )
                _record_trade(store, new_trades[-1])
                _set_bot_position(store, bot["id"], qty, avg_price)
        elif target == 0 and holding:
            proceeds = qty * price
            cost = proceeds * FEE
            new_trades.append(
                {
                    "email": email,
                    "bot_id": bot["id"],
                    "symbol": symbol,
                    "side": "sell",
                    "qty": qty,
                    "price": price,
                    "commission": cost,
                    "executed_at": exec_date,
                    "kind": "bot",
                }
            )
            _record_trade(store, new_trades[-1])
            qty = 0.0
            avg_price = None
            holding = False
            _set_bot_position(store, bot["id"], qty, avg_price)

        processed_up_to = exec_date

    # Persist how far this bot has advanced.
    if processed_up_to != last_done:
        with store._lock:
            store._conn.execute(
                "UPDATE paper_bots SET last_processed_date = ?, position_qty = ?, avg_price = ? "
                "WHERE id = ?",
                (processed_up_to, qty, avg_price, bot["id"]),
            )
            store._conn.commit()

    summary["new_trades"] = len(new_trades)
    summary["last_price"] = closes[-1]
    return summary


def _bot_free_cash(store: PaperStore, bot_id: int) -> float:
    """The bot's uninvested cash = allocation − net commissions paid so far.

    Bot trades don't touch account cash; a bot's economics live entirely in its
    allocation. When flat, free cash = allocation minus every commission it has
    ever paid (buys and sells) plus/minus realised P&L. We compute it from the
    trade ledger so backfills stay consistent.
    """
    with store._lock:
        brow = store._conn.execute(
            "SELECT allocated_cash FROM paper_bots WHERE id = ?", (bot_id,)
        ).fetchone()
        allocation = brow["allocated_cash"] if brow else 0.0
        rows = store._conn.execute(
            "SELECT side, qty, price, commission FROM paper_trades WHERE bot_id = ? ORDER BY id",
            (bot_id,),
        ).fetchall()
    cash = allocation
    for r in rows:
        if r["side"] == "buy":
            cash -= r["qty"] * r["price"] + r["commission"]
        else:  # sell
            cash += r["qty"] * r["price"] - r["commission"]
    return cash


def _record_trade(store: PaperStore, t: dict) -> None:
    with store._lock:
        store._conn.execute(
            "INSERT INTO paper_trades "
            "(email, bot_id, symbol, side, qty, price, commission, executed_at, kind) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                t["email"],
                t["bot_id"],
                t["symbol"],
                t["side"],
                t["qty"],
                t["price"],
                t["commission"],
                t["executed_at"],
                t["kind"],
            ),
        )
        store._conn.commit()


def _set_bot_position(store: PaperStore, bot_id: int, qty: float, avg_price: Optional[float]) -> None:
    with store._lock:
        store._conn.execute(
            "UPDATE paper_bots SET position_qty = ?, avg_price = ? WHERE id = ?",
            (qty, avg_price, bot_id),
        )
        store._conn.commit()


def _snapshot_equity(store: PaperStore, email: str) -> None:
    """Write today's equity snapshot (one row per email+date, upserted)."""
    state = _compute_equity(store, email)
    today = dt.date.today().isoformat()
    with store._lock:
        store._conn.execute(
            "INSERT INTO paper_equity (email, date, equity) VALUES (?, ?, ?) "
            "ON CONFLICT(email, date) DO UPDATE SET equity = excluded.equity",
            (email, today, state),
        )
        store._conn.commit()


def _compute_equity(store: PaperStore, email: str) -> float:
    """Total account equity = account cash + all bot ledgers + manual positions,
    marked to the latest real close where available (bot allocation used as a
    fallback when a bot's symbol has no real price)."""
    with store._lock:
        acct = store._conn.execute(
            "SELECT cash FROM paper_accounts WHERE email = ?", (email,)
        ).fetchone()
        cash = acct["cash"] if acct else 0.0
        bots = store._conn.execute(
            "SELECT id, symbol, allocated_cash, position_qty, avg_price FROM paper_bots WHERE email = ?",
            (email,),
        ).fetchall()
        positions = store._conn.execute(
            "SELECT symbol, qty, avg_price FROM paper_positions WHERE email = ? AND qty > 0",
            (email,),
        ).fetchall()

    total = cash
    price_cache: Dict[str, Optional[float]] = {}

    def latest_price(sym: str) -> Optional[float]:
        if sym not in price_cache:
            s = _price_series_for(sym, days=90)
            price_cache[sym] = s.closes[-1] if (s.source != "synthetic" and s.closes) else None
        return price_cache[sym]

    for b in bots:
        free = _bot_free_cash(store, b["id"])
        qty = b["position_qty"] or 0.0
        if qty > 0:
            p = latest_price(b["symbol"])
            total += free + (qty * p if p is not None else qty * (b["avg_price"] or 0.0))
        else:
            total += free

    for pos in positions:
        p = latest_price(pos["symbol"])
        total += pos["qty"] * (p if p is not None else pos["avg_price"])

    return round(total, 2)


# ── Public API ───────────────────────────────────────────────────────


def tick(email: str) -> Dict[str, Any]:
    """Advance every running bot over all new real daily bars and snapshot equity.

    Idempotent per day/bar: bars at or before a bot's ``last_processed_date``
    are skipped. Returns a summary with per-bot results and any warnings.
    """
    store = _get_store()
    email = _norm_email(email)
    _ensure_account(store, email)

    with store._lock:
        bots = store._conn.execute(
            "SELECT id, email, symbol, strategy, params_json, allocated_cash, status, "
            "position_qty, avg_price, last_processed_date, created_at "
            "FROM paper_bots WHERE email = ? AND status = 'running'",
            (email,),
        ).fetchall()

    bot_summaries = []
    warnings: List[str] = []
    for bot in bots:
        summ = _advance_bot(store, bot)
        bot_summaries.append(summ)
        if summ.get("warning"):
            warnings.append(f"[{summ['symbol']}] {summ['warning']}")

    _snapshot_equity(store, email)

    return {
        "email": email,
        "ticked_at": _now_iso(),
        "bots": bot_summaries,
        "warnings": warnings,
    }


def get_state(email: str) -> Dict[str, Any]:
    """Full paper-account snapshot for the Trade page.

    Note: the API layer is expected to call :func:`tick` before this on a state
    read; ``get_state`` itself only reports current DB state (marked to the
    latest real close), it does not advance bots.
    """
    store = _get_store()
    email = _norm_email(email)
    acct = _ensure_account(store, email)

    with store._lock:
        bots = store._conn.execute(
            "SELECT id, symbol, strategy, params_json, allocated_cash, status, "
            "position_qty, avg_price, last_processed_date, created_at "
            "FROM paper_bots WHERE email = ? ORDER BY id",
            (email,),
        ).fetchall()
        manual = store._conn.execute(
            "SELECT symbol, qty, avg_price FROM paper_positions WHERE email = ? AND qty > 0 ORDER BY symbol",
            (email,),
        ).fetchall()

    warnings: List[str] = []
    price_cache: Dict[str, Dict[str, Any]] = {}

    def price_info(sym: str) -> Dict[str, Any]:
        if sym not in price_cache:
            s = _price_series_for(sym, days=90)
            real = s.source != "synthetic" and bool(s.closes)
            price_cache[sym] = {
                "price": s.closes[-1] if real else None,
                "source": s.source,
                "warning": s.warning,
            }
        return price_cache[sym]

    positions_out: List[dict] = []
    manual_market_value = 0.0

    # Bot-held positions.
    bots_out: List[dict] = []
    for b in bots:
        pinfo = price_info(b["symbol"])
        qty = b["position_qty"] or 0.0
        avg = b["avg_price"]
        cur_price = pinfo["price"]
        mkt_val = round(qty * cur_price, 2) if (qty > 0 and cur_price is not None) else 0.0
        unreal = (
            round((cur_price - avg) * qty, 2)
            if (qty > 0 and cur_price is not None and avg is not None)
            else 0.0
        )
        free_cash = round(_bot_free_cash(store, b["id"]), 2)
        bot_equity = round(free_cash + mkt_val, 2) if qty > 0 else free_cash
        bots_out.append(
            {
                "id": b["id"],
                "symbol": b["symbol"],
                "strategy": b["strategy"],
                "params": json.loads(b["params_json"]),
                "allocated_cash": round(b["allocated_cash"], 2),
                "status": b["status"],
                "position_qty": round(qty, 8),
                "avg_price": round(avg, 4) if avg is not None else None,
                "current_price": round(cur_price, 4) if cur_price is not None else None,
                "market_value": mkt_val,
                "free_cash": free_cash,
                "bot_equity": bot_equity,
                "unrealized_pnl": unreal,
                "last_processed_date": b["last_processed_date"],
                "source": pinfo["source"],
                "warning": pinfo["warning"],
                "created_at": b["created_at"],
            }
        )
        if qty > 0:
            positions_out.append(
                {
                    "symbol": b["symbol"],
                    "qty": round(qty, 8),
                    "avg_price": round(avg, 4) if avg is not None else None,
                    "current_price": round(cur_price, 4) if cur_price is not None else None,
                    "market_value": mkt_val,
                    "unrealized_pnl": unreal,
                    "kind": "bot",
                    "bot_id": b["id"],
                    "source": pinfo["source"],
                }
            )
        if pinfo["warning"]:
            w = f"[{b['symbol']}] {pinfo['warning']}"
            if w not in warnings:
                warnings.append(w)

    # Manual positions.
    for m in manual:
        pinfo = price_info(m["symbol"])
        qty = m["qty"]
        avg = m["avg_price"]
        cur_price = pinfo["price"]
        mkt_val = round(qty * cur_price, 2) if cur_price is not None else round(qty * avg, 2)
        unreal = round((cur_price - avg) * qty, 2) if cur_price is not None else 0.0
        manual_market_value += mkt_val
        positions_out.append(
            {
                "symbol": m["symbol"],
                "qty": round(qty, 8),
                "avg_price": round(avg, 4),
                "current_price": round(cur_price, 4) if cur_price is not None else None,
                "market_value": mkt_val,
                "unrealized_pnl": unreal,
                "kind": "manual",
                "bot_id": None,
                "source": pinfo["source"],
            }
        )
        if pinfo["warning"]:
            w = f"[{m['symbol']}] {pinfo['warning']}"
            if w not in warnings:
                warnings.append(w)

    # Equity is computed from the SAME prices reported above (account cash +
    # each bot's equity + manual market values) so the response is internally
    # consistent — no second price fetch that could drift on live bars.
    equity = round(
        acct["cash"] + sum(b["bot_equity"] for b in bots_out) + manual_market_value, 2
    )
    initial = acct["initial_cash"]
    total_pnl = round(equity - initial, 2)
    return_pct = round((equity / initial - 1) * 100, 4) if initial > 0 else 0.0

    with store._lock:
        eq_rows = store._conn.execute(
            "SELECT date, equity FROM paper_equity WHERE email = ? ORDER BY date",
            (email,),
        ).fetchall()
    equity_curve = [{"date": r["date"], "equity": round(r["equity"], 2)} for r in eq_rows]

    return {
        "email": email,
        "account": {
            "cash": round(acct["cash"], 2),
            "equity": equity,
            "initial_cash": round(initial, 2),
            "total_pnl": total_pnl,
            "return_pct": return_pct,
        },
        "positions": positions_out,
        "bots": bots_out,
        "equity_curve": equity_curve,
        "warnings": warnings,
    }


def create_bot(
    email: str,
    symbol: str,
    strategy: str,
    params: Optional[dict] = None,
    allocated_cash: float = 10_000.0,
    last_processed_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a running bot with an allocation deducted from account cash.

    Validates the strategy + params against the registry (``PaperError`` → 422
    on bad input) and that the allocation is positive and ≤ available cash.

    ``last_processed_date`` seeds the backfill cursor. Left ``None`` (the
    normal case) it is set to the symbol's latest available real bar, so a new
    bot starts trading from *now* — backfill only ever replays bars that
    arrive after creation. Tests may backdate it explicitly to force a
    historical replay window.
    """
    store = _get_store()
    email = _norm_email(email)
    symbol = _norm_symbol(symbol)
    merged_params = _validate_strategy(strategy, params)

    try:
        allocated_cash = float(allocated_cash)
    except (TypeError, ValueError):
        raise PaperError("allocated_cash must be a number")
    if allocated_cash <= 0:
        raise PaperError("allocated_cash must be positive")

    acct = _ensure_account(store, email)
    if allocated_cash > acct["cash"] + 1e-9:
        raise PaperError(
            f"Allocation {allocated_cash:.2f} exceeds available cash {acct['cash']:.2f}"
        )

    if last_processed_date is None:
        # Start trading from *now*: seed the cursor with the latest real bar so
        # the next tick only processes bars that arrive after creation, never a
        # retroactive replay of history.
        series = _price_series_for(symbol)
        if series.candles:
            last_processed_date = series.candles[-1].date
        else:
            last_processed_date = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    now = _now_iso()
    with store._lock:
        cur = store._conn.execute(
            "INSERT INTO paper_bots "
            "(email, symbol, strategy, params_json, allocated_cash, status, "
            "position_qty, avg_price, last_processed_date, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'running', 0, NULL, ?, ?)",
            (email, symbol, strategy, json.dumps(merged_params), allocated_cash,
             last_processed_date, now),
        )
        bot_id = cur.lastrowid
        store._conn.execute(
            "UPDATE paper_accounts SET cash = cash - ? WHERE email = ?",
            (allocated_cash, email),
        )
        store._conn.commit()

    return {
        "id": bot_id,
        "email": email,
        "symbol": symbol,
        "strategy": strategy,
        "params": merged_params,
        "allocated_cash": round(allocated_cash, 2),
        "status": "running",
        "last_processed_date": last_processed_date,
        "created_at": now,
    }


def set_bot_status(email: str, bot_id: int, status: str) -> Dict[str, Any]:
    """Set a bot to ``running`` or ``stopped``. Stopping leaves its position
    intact (frozen); restarting resumes backfill from where it left off."""
    store = _get_store()
    email = _norm_email(email)
    if status not in ("running", "stopped"):
        raise PaperError("status must be 'running' or 'stopped'")
    with store._lock:
        row = store._conn.execute(
            "SELECT id FROM paper_bots WHERE id = ? AND email = ?", (bot_id, email)
        ).fetchone()
        if row is None:
            raise PaperError(f"Bot {bot_id} not found")
        store._conn.execute(
            "UPDATE paper_bots SET status = ? WHERE id = ? AND email = ?",
            (status, bot_id, email),
        )
        store._conn.commit()
    return {"id": bot_id, "status": status}


def delete_bot(email: str, bot_id: int) -> Dict[str, Any]:
    """Delete a bot, liquidating any open position at the latest real close and
    refunding the resulting free cash to the account.

    If the bot holds a position but its symbol has no real price, we refund the
    bot's free cash plus the position marked at its average (avoids destroying
    money) and flag a warning.
    """
    store = _get_store()
    email = _norm_email(email)
    with store._lock:
        bot = store._conn.execute(
            "SELECT id, symbol, allocated_cash, position_qty, avg_price FROM paper_bots "
            "WHERE id = ? AND email = ?",
            (bot_id, email),
        ).fetchone()
    if bot is None:
        raise PaperError(f"Bot {bot_id} not found")

    warning = None
    qty = bot["position_qty"] or 0.0
    free_cash = _bot_free_cash(store, bot_id)

    if qty > 0:
        series = _price_series_for(bot["symbol"], days=90)
        if series.source != "synthetic" and series.closes:
            price = series.closes[-1]
            proceeds = qty * price
            cost = proceeds * FEE
            _record_trade(
                store,
                {
                    "email": email,
                    "bot_id": bot_id,
                    "symbol": bot["symbol"],
                    "side": "sell",
                    "qty": qty,
                    "price": price,
                    "commission": cost,
                    "executed_at": series.dates[-1],
                    "kind": "bot",
                },
            )
            refund = free_cash + proceeds - cost
        else:
            # No real price: refund at average cost to conserve money.
            refund = free_cash + qty * (bot["avg_price"] or 0.0)
            warning = (
                f"No real price for {bot['symbol']}; position liquidated at "
                f"average cost on deletion."
            )
    else:
        refund = free_cash

    with store._lock:
        store._conn.execute(
            "UPDATE paper_accounts SET cash = cash + ? WHERE email = ?",
            (refund, email),
        )
        store._conn.execute("DELETE FROM paper_bots WHERE id = ? AND email = ?", (bot_id, email))
        store._conn.commit()

    return {"id": bot_id, "refunded": round(refund, 2), "warning": warning}


def manual_trade(email: str, symbol: str, side: str, notional_usd: float) -> Dict[str, Any]:
    """Buy/sell a manual position at the LATEST real close.

    ``notional_usd`` is the target trade value; sells clamp to the held qty.
    Commission applies. Account cash is debited on buys, credited on sells. If
    the symbol has no real price (synthetic source), NO trade is executed and a
    warning is returned.
    """
    store = _get_store()
    email = _norm_email(email)
    symbol = _norm_symbol(symbol)
    side = (side or "").strip().lower()
    if side not in ("buy", "sell"):
        raise PaperError("side must be 'buy' or 'sell'")
    try:
        notional_usd = float(notional_usd)
    except (TypeError, ValueError):
        raise PaperError("notional_usd must be a number")
    if notional_usd <= 0:
        raise PaperError("notional_usd must be positive")

    acct = _ensure_account(store, email)

    series = _price_series_for(symbol, days=90)
    if series.source == "synthetic" or not series.closes:
        return {
            "executed": False,
            "symbol": symbol,
            "side": side,
            "warning": series.warning
            or f"No real market data for {symbol}; no trade executed.",
            "source": series.source,
        }

    price = series.closes[-1]
    exec_date = series.dates[-1]

    with store._lock:
        pos = store._conn.execute(
            "SELECT qty, avg_price FROM paper_positions WHERE email = ? AND symbol = ?",
            (email, symbol),
        ).fetchone()
        held_qty = pos["qty"] if pos else 0.0
        held_avg = pos["avg_price"] if pos else 0.0

        if side == "buy":
            gross = notional_usd
            commission = gross * FEE
            total_cost = gross + commission
            if total_cost > acct["cash"] + 1e-9:
                raise PaperError(
                    f"Insufficient cash: need {total_cost:.2f}, have {acct['cash']:.2f}"
                )
            qty = gross / price
            new_qty = held_qty + qty
            new_avg = (held_qty * held_avg + qty * price) / new_qty if new_qty > 0 else price
            store._conn.execute(
                "INSERT INTO paper_positions (email, symbol, qty, avg_price) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(email, symbol) DO UPDATE SET qty = excluded.qty, avg_price = excluded.avg_price",
                (email, symbol, new_qty, new_avg),
            )
            store._conn.execute(
                "UPDATE paper_accounts SET cash = cash - ? WHERE email = ?",
                (total_cost, email),
            )
            traded_qty = qty
        else:  # sell
            desired_qty = notional_usd / price
            qty = min(desired_qty, held_qty)  # clamp to held qty
            if qty <= 0:
                raise PaperError(f"No {symbol} position to sell")
            proceeds = qty * price
            commission = proceeds * FEE
            net = proceeds - commission
            new_qty = held_qty - qty
            if new_qty <= 1e-12:
                store._conn.execute(
                    "DELETE FROM paper_positions WHERE email = ? AND symbol = ?",
                    (email, symbol),
                )
            else:
                store._conn.execute(
                    "UPDATE paper_positions SET qty = ? WHERE email = ? AND symbol = ?",
                    (new_qty, email, symbol),
                )
            store._conn.execute(
                "UPDATE paper_accounts SET cash = cash + ? WHERE email = ?",
                (net, email),
            )
            traded_qty = qty

        store._conn.execute(
            "INSERT INTO paper_trades "
            "(email, bot_id, symbol, side, qty, price, commission, executed_at, kind) "
            "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, 'manual')",
            (email, symbol, side, traded_qty, price, commission, exec_date),
        )
        store._conn.commit()

    return {
        "executed": True,
        "symbol": symbol,
        "side": side,
        "qty": round(traded_qty, 8),
        "price": round(price, 4),
        "commission": round(commission, 2),
        "executed_at": exec_date,
        "source": series.source,
        "warning": None,
    }


def get_trades(email: str, limit: int = 50) -> List[dict]:
    """Most-recent trades (bot + manual), newest first."""
    store = _get_store()
    email = _norm_email(email)
    _ensure_account(store, email)
    try:
        limit = max(1, min(int(limit), 500))
    except (TypeError, ValueError):
        limit = 50
    with store._lock:
        rows = store._conn.execute(
            "SELECT id, bot_id, symbol, side, qty, price, commission, executed_at, kind "
            "FROM paper_trades WHERE email = ? "
            "ORDER BY executed_at DESC, id DESC LIMIT ?",
            (email, limit),
        ).fetchall()
    return [
        {
            "id": r["id"],
            "bot_id": r["bot_id"],
            "symbol": r["symbol"],
            "side": r["side"],
            "qty": round(r["qty"], 8),
            "price": round(r["price"], 4),
            "commission": round(r["commission"], 2),
            "executed_at": r["executed_at"],
            "kind": r["kind"],
        }
        for r in rows
    ]


def reset(email: str) -> Dict[str, Any]:
    """Wipe the user's paper state back to $100k fresh."""
    store = _get_store()
    email = _norm_email(email)
    now = _now_iso()
    with store._lock:
        store._conn.execute("DELETE FROM paper_bots WHERE email = ?", (email,))
        store._conn.execute("DELETE FROM paper_trades WHERE email = ?", (email,))
        store._conn.execute("DELETE FROM paper_positions WHERE email = ?", (email,))
        store._conn.execute("DELETE FROM paper_equity WHERE email = ?", (email,))
        store._conn.execute(
            "INSERT INTO paper_accounts (email, cash, initial_cash, created_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(email) DO UPDATE SET cash = excluded.cash, "
            "initial_cash = excluded.initial_cash, created_at = excluded.created_at",
            (email, INITIAL_CASH, INITIAL_CASH, now),
        )
        store._conn.commit()
    return {"email": email, "cash": INITIAL_CASH, "reset_at": now}

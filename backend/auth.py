"""Self-contained auth backend for the Trading Bot FastAPI app.

Replaces the legacy Express + MongoDB auth server (backend/server.js) with a
single stdlib-only implementation:

  * SQLite (stdlib ``sqlite3``) for users + per-user sentiment search history.
  * PBKDF2-HMAC-SHA256 password hashing (600k iterations, per-user salt).
  * Hand-rolled HS256 JWTs (stdlib ``hmac``/``hashlib``/``base64``/``json``).
  * In-memory, per-IP login rate limiting.

No new pip dependencies. Everything below the FastAPI wiring is transport
agnostic so it can be unit-tested directly.

The router built by :func:`build_auth_router` returns error bodies keyed by
``message`` (not FastAPI's default ``detail``) because the Vue views read
``data.message`` from failed responses.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("trading_bot.auth")

# ── Configuration ────────────────────────────────────────────────────

MIN_PASSWORD_LENGTH = 8

# Mirror the client-side email check (RegisterView.vue / legacy server.js).
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# PBKDF2 work factor. 600k iterations for SHA256 per OWASP guidance (2023+).
PBKDF2_ITERATIONS = 600_000

# JWT lifetime.
JWT_TTL_SECONDS = 60 * 60  # 1 hour

# Login rate limiting (in-memory, per process, per IP).
LOGIN_RATE_MAX = int(os.getenv("LOGIN_RATE_MAX", "10"))
LOGIN_RATE_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_WINDOW_MS", str(15 * 60 * 1000))) // 1000

_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "trading_bot.db")


# ── JWT secret ───────────────────────────────────────────────────────


def _resolve_jwt_secret() -> bytes:
    """Return the HS256 signing key.

    Uses ``JWT_SECRET`` from the environment. If unset, an ephemeral random
    secret is generated so the app still runs in development — but tokens then
    invalidate on every restart, which we log loudly. We never fall back to a
    hardcoded string (that would let anyone mint valid tokens).
    """
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret.encode("utf-8")
    ephemeral = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET is not set; generated an ephemeral random secret. "
        "Tokens invalidate on every restart. Set JWT_SECRET in production "
        "(see backend/.env.example)."
    )
    return ephemeral.encode("utf-8")


# ── base64url helpers (no padding) ───────────────────────────────────


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


# ── SQLite store ─────────────────────────────────────────────────────


class AuthStore:
    """Thin SQLite wrapper for users + sentiment history.

    A single module-level lock serialises writes so the store is safe under
    FastAPI's threaded ``TestClient`` and uvicorn's default thread pool. The
    connection is opened with ``check_same_thread=False`` and WAL mode.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # WAL improves concurrent read/write; harmless (and skipped) for :memory:.
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    email         TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt          TEXT NOT NULL,
                    created_at    TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sentiment_history (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    email        TEXT NOT NULL,
                    query        TEXT NOT NULL,
                    num_articles INTEGER,
                    model        TEXT,
                    avg_compound REAL,
                    created_at   TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_history_email
                    ON sentiment_history (email, created_at DESC);
                """
            )
            self._conn.commit()

    # ── users ────────────────────────────────────────────────────────

    def get_user(self, email: str) -> Optional[sqlite3.Row]:
        email = email.strip().lower()
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, email, password_hash, salt, created_at "
                "FROM users WHERE email = ?",
                (email,),
            )
            return cur.fetchone()

    def create_user(self, email: str, password: str) -> bool:
        """Insert a new user. Returns False if the email already exists."""
        email = email.strip().lower()
        salt = os.urandom(16)
        pw_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        created_at = _utc_now_iso()
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO users (email, password_hash, salt, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (email, _b64url_encode(pw_hash), _b64url_encode(salt), created_at),
                )
                self._conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def verify_password(self, row: sqlite3.Row, password: str) -> bool:
        salt = _b64url_decode(row["salt"])
        expected = _b64url_decode(row["password_hash"])
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(candidate, expected)

    # ── sentiment history ────────────────────────────────────────────

    def add_history(
        self,
        email: str,
        query: str,
        num_articles: Optional[int],
        model: Optional[str],
        avg_compound: Optional[float],
    ) -> dict:
        email = email.strip().lower()
        created_at = _utc_now_iso()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO sentiment_history "
                "(email, query, num_articles, model, avg_compound, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (email, query, num_articles, model, avg_compound, created_at),
            )
            self._conn.commit()
            new_id = cur.lastrowid
        return _history_row_to_dict(
            {
                "id": new_id,
                "email": email,
                "query": query,
                "num_articles": num_articles,
                "model": model,
                "avg_compound": avg_compound,
                "created_at": created_at,
            }
        )

    def list_history(self, email: str, limit: int = 20) -> list[dict]:
        email = email.strip().lower()
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, email, query, num_articles, model, avg_compound, created_at "
                "FROM sentiment_history WHERE email = ? "
                "ORDER BY created_at DESC, id DESC LIMIT ?",
                (email, limit),
            )
            rows = cur.fetchall()
        return [_history_row_to_dict(dict(r)) for r in rows]


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat() + "Z"


def _history_row_to_dict(row: dict) -> dict:
    """Map a SQLite history row to the Mongo-style shape the frontend reads."""
    return {
        "_id": str(row["id"]),
        "email": row["email"],
        "query": row["query"],
        "numArticles": row["num_articles"],
        "model": row["model"],
        "avgCompound": row["avg_compound"],
        "createdAt": row["created_at"],
    }


# ── Login rate limiter (in-memory, per process, per IP) ──────────────


class RateLimiter:
    """Sliding-window counter of failed/attempted logins per IP.

    Per process only (state is lost on restart and not shared across workers).
    Matches the legacy Express behaviour of 10 attempts / 15 minutes per IP.
    """

    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check_and_record(self, key: str) -> bool:
        """Record an attempt for ``key``. Return True if it is allowed."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(hits) >= self.max_attempts:
                self._hits[key] = hits
                return False
            hits.append(now)
            self._hits[key] = hits
            return True


# ── JWT (HS256, hand-rolled) ─────────────────────────────────────────


def _sign(signing_input: bytes, secret: bytes) -> str:
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return _b64url_encode(sig)


def make_token(email: str, secret: bytes, ttl_seconds: int = JWT_TTL_SECONDS) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"email": email, "iat": now, "exp": now + ttl_seconds}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _sign(signing_input, secret)
    return f"{header_b64}.{payload_b64}.{signature}"


def decode_token(token: str, secret: bytes) -> Optional[dict]:
    """Verify signature + expiry. Return the payload dict or None if invalid."""
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError:
        return None
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = _sign(signing_input, secret)
    if not hmac.compare_digest(expected_sig, signature):
        return None
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None
    if header.get("alg") != "HS256":
        return None
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)) or int(time.time()) >= exp:
        return None
    return payload


# ── Request/response bodies ──────────────────────────────────────────


class Credentials(BaseModel):
    email: str = ""
    password: str = ""


class HistoryCreate(BaseModel):
    query: str = ""
    numArticles: Optional[int] = None
    model: Optional[str] = None
    avgCompound: Optional[float] = None


def _err(status_code: int, message: str) -> JSONResponse:
    # The Vue views read `data.message`, so we return {message} rather than
    # FastAPI's default {detail}.
    return JSONResponse(status_code=status_code, content={"message": message})


# ── Router factory ───────────────────────────────────────────────────


def build_auth_router(
    store: Optional[AuthStore] = None,
    jwt_secret: Optional[bytes] = None,
) -> APIRouter:
    """Build the auth APIRouter.

    ``store`` and ``jwt_secret`` are injectable for tests. Defaults resolve the
    DB path from ``AUTH_DB_PATH`` (or ``backend/data/trading_bot.db``) and the
    JWT secret from ``JWT_SECRET``.
    """
    if store is None:
        db_path = os.getenv("AUTH_DB_PATH", _DEFAULT_DB_PATH)
        store = AuthStore(db_path)
    if jwt_secret is None:
        jwt_secret = _resolve_jwt_secret()

    limiter = RateLimiter(LOGIN_RATE_MAX, LOGIN_RATE_WINDOW_SECONDS)
    router = APIRouter()

    def current_email(authorization: Optional[str] = Header(default=None)) -> Optional[str]:
        """Resolve the caller's email from a Bearer token, or None."""
        if not authorization:
            return None
        token = authorization
        if token.startswith("Bearer "):
            token = token[len("Bearer "):].strip()
        if not token:
            return None
        payload = decode_token(token, jwt_secret)
        if not payload:
            return None
        return payload.get("email")

    # ── register ──────────────────────────────────────────────────
    @router.post("/api/register")
    def register(body: Credentials):
        email = (body.email or "").strip()
        password = body.password or ""
        if not email or not password:
            return _err(400, "Email and password are required")
        if not EMAIL_RE.match(email):
            return _err(400, "Please enter a valid email address.")
        if len(password) < MIN_PASSWORD_LENGTH:
            return _err(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if not store.create_user(email, password):
            return _err(409, "User already exists")
        return JSONResponse(status_code=201, content={"message": "Registration successful"})

    # ── login ─────────────────────────────────────────────────────
    @router.post("/api/login")
    def login(body: Credentials, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        if not limiter.check_and_record(client_ip):
            return _err(429, "Too many login attempts. Please try again later.")

        email = (body.email or "").strip()
        password = body.password or ""
        row = store.get_user(email)
        if row is None:
            return _err(404, "Account not registered. Please register first.")
        if not store.verify_password(row, password):
            return _err(401, "Invalid password")
        token = make_token(row["email"], jwt_secret)
        return JSONResponse(
            status_code=200, content={"message": "Login successful", "token": token}
        )

    # ── me ────────────────────────────────────────────────────────
    @router.get("/api/me")
    def me(email: Optional[str] = Depends(current_email)):
        if not email:
            return _err(401, "Unauthorized")
        row = store.get_user(email)
        if row is None:
            return _err(401, "Unauthorized")
        return {"email": row["email"], "created_at": row["created_at"]}

    # ── sentiment history ─────────────────────────────────────────
    @router.get("/api/sentiment/history")
    def get_history(email: Optional[str] = Depends(current_email)):
        if not email:
            return _err(401, "Unauthorized")
        return store.list_history(email, limit=20)

    @router.post("/api/sentiment/history")
    def post_history(body: HistoryCreate, email: Optional[str] = Depends(current_email)):
        if not email:
            return _err(401, "Unauthorized")
        query = (body.query or "").strip()
        if not query:
            return _err(400, "query is required")
        record = store.add_history(
            email=email,
            query=query,
            num_articles=body.numArticles if isinstance(body.numArticles, int) else None,
            model=body.model if isinstance(body.model, str) else None,
            avg_compound=body.avgCompound
            if isinstance(body.avgCompound, (int, float))
            else None,
        )
        return JSONResponse(status_code=201, content=record)

    return router

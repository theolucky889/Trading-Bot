from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import bcrypt
import requests as http_requests
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .python.sentiment_analysis import analyze_market_sentiment

app = FastAPI(title="Trading Bot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth config ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-before-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

security = HTTPBearer(auto_error=False)

# ── File-based storage ─────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE   = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "sentiment_history.json"
KEYS_FILE    = DATA_DIR / "user_keys.json"
PREDICTIONS_FILE = DATA_DIR / "predictions.json"
USER_VOTES_FILE  = DATA_DIR / "user_votes.json"


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_json(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── JWT helpers ────────────────────────────────────────────────────────────────
def _create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def _email_from_creds(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[str]:
    if not credentials:
        return None
    return _decode_token(credentials.credentials)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    return _email_from_creds(credentials)


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    email = _email_from_creds(credentials)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return email


# ── Key helpers ────────────────────────────────────────────────────────────────
def _get_user_keys(email: str) -> dict:
    keys = _read_json(KEYS_FILE)
    entry = next((k for k in keys if k.get("email") == email), None)
    return entry or {}


def _set_user_keys(email: str, av_key: str, binance_key: str) -> None:
    keys = _read_json(KEYS_FILE)
    entry = next((k for k in keys if k.get("email") == email), None)
    if entry:
        entry["alpha_vantage_key"] = av_key
        entry["binance_key"] = binance_key
    else:
        keys.append({"email": email, "alpha_vantage_key": av_key, "binance_key": binance_key})
    _write_json(KEYS_FILE, keys)


# ── Pydantic models ────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str


class KeysRequest(BaseModel):
    alpha_vantage_key: str = ""
    binance_key: str = ""


class VoteRequest(BaseModel):
    symbol: str
    direction: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/register", status_code=201)
def register(body: AuthRequest):
    users = _read_json(USERS_FILE)
    if any(u["email"] == body.email for u in users):
        raise HTTPException(status_code=409, detail="Email already registered")
    users.append({"email": body.email, "password": _hash_password(body.password)})
    _write_json(USERS_FILE, users)
    return {"message": "Registration successful"}


@app.post("/api/login")
def login(body: AuthRequest):
    users = _read_json(USERS_FILE)
    user = next((u for u in users if u["email"] == body.email), None)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Account not registered. Please register first.",
        )
    if not _verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Login successful", "token": _create_token(body.email)}


@app.get("/api/sentiment")
def sentiment(
    query: str,
    num_articles: int = 10,
    model: str = "vader",
    current_user: Optional[str] = Depends(get_current_user),
):
    query = (query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    num_articles = max(1, min(int(num_articles), 50))

    result = analyze_market_sentiment(query=query, num_articles=num_articles, model=model)

    if current_user:
        history = _read_json(HISTORY_FILE)
        entry = {
            "_id": f"{current_user}_{datetime.utcnow().timestamp()}",
            "email": current_user,
            "query": query,
            "model": result.get("model", model),
            "numArticles": num_articles,
            "generatedAt": result.get("generated_at"),
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "summary": result.get("summary"),
        }
        history.insert(0, entry)
        # keep newest 50 per user + all other users' entries
        user_entries = [h for h in history if h.get("email") == current_user][:50]
        other_entries = [h for h in history if h.get("email") != current_user]
        _write_json(HISTORY_FILE, user_entries + other_entries)

    return result


@app.get("/api/sentiment/history")
def sentiment_history(current_user: str = Depends(require_auth)):
    history = _read_json(HISTORY_FILE)
    return [h for h in history if h.get("email") == current_user][:50]


# ── Settings: API key management ───────────────────────────────────────────────
@app.get("/api/settings/keys")
def get_keys(current_user: str = Depends(require_auth)):
    entry = _get_user_keys(current_user)
    av = entry.get("alpha_vantage_key", "")
    bn = entry.get("binance_key", "")
    # Return masked versions so the frontend can show "key saved" without exposing the real value
    def mask(k: str) -> str:
        if len(k) <= 8:
            return "*" * len(k)
        return k[:4] + "*" * (len(k) - 8) + k[-4:]
    return {
        "alpha_vantage_key": mask(av) if av else "",
        "alpha_vantage_set": bool(av),
        "binance_key": mask(bn) if bn else "",
        "binance_set": bool(bn),
    }


@app.put("/api/settings/keys")
def save_keys(body: KeysRequest, current_user: str = Depends(require_auth)):
    _set_user_keys(current_user, body.alpha_vantage_key.strip(), body.binance_key.strip())
    return {"message": "API keys saved"}


# ── Market data proxy (backend uses stored keys, never exposes them to browser) ─
AV_BASE = "https://www.alphavantage.co/query"

def _require_av_key(email: str) -> str:
    key = _get_user_keys(email).get("alpha_vantage_key", "")
    if not key:
        raise HTTPException(
            status_code=400,
            detail="Alpha Vantage API key not set. Go to Settings → API Keys to add it.",
        )
    return key


@app.get("/api/market/stock/{symbol}")
def market_stock(symbol: str, current_user: str = Depends(require_auth)):
    av_key = _require_av_key(current_user)
    try:
        resp = http_requests.get(AV_BASE, params={
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol.upper(),
            "apikey": av_key,
            "outputsize": "compact",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpha Vantage request failed: {exc}")

    if "Note" in data:
        raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached (25 req/day on free tier). Try again later.")
    if "Information" in data:
        raise HTTPException(status_code=401, detail="Alpha Vantage API key is invalid or the daily limit is exceeded.")

    series = data.get("Time Series (Daily)")
    if not series:
        raise HTTPException(status_code=404, detail=f"No price data returned for {symbol}. Check the symbol name.")

    dates = sorted(series.keys(), reverse=True)[:60]
    dates.reverse()
    return {
        "symbol": symbol.upper(),
        "labels": dates,
        "prices": [float(series[d]["5. adjusted close"]) for d in dates],
    }


@app.get("/api/market/forex/{from_symbol}/{to_symbol}")
def market_forex(from_symbol: str, to_symbol: str, current_user: str = Depends(require_auth)):
    av_key = _require_av_key(current_user)
    try:
        resp = http_requests.get(AV_BASE, params={
            "function": "FX_DAILY",
            "from_symbol": from_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "apikey": av_key,
            "outputsize": "compact",
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpha Vantage request failed: {exc}")

    if "Note" in data:
        raise HTTPException(status_code=429, detail="Alpha Vantage rate limit reached. Try again later.")
    if "Information" in data:
        raise HTTPException(status_code=401, detail="Alpha Vantage API key is invalid or the daily limit is exceeded.")

    series = data.get("Time Series FX (Daily)")
    if not series:
        raise HTTPException(status_code=404, detail=f"No forex data for {from_symbol}/{to_symbol}.")

    dates = sorted(series.keys(), reverse=True)[:60]
    dates.reverse()
    return {
        "pair": f"{from_symbol.upper()}/{to_symbol.upper()}",
        "labels": dates,
        "prices": [float(series[d]["4. close"]) for d in dates],
    }


@app.get("/api/market/crypto/{symbol}")
def market_crypto(symbol: str, limit: int = 60):
    """Crypto via Binance public API — no key required."""
    symbol = symbol.upper()
    try:
        resp = http_requests.get(
            "https://api.binance.com/api/v3/klines",
            params={"symbol": symbol, "interval": "1d", "limit": min(limit, 200)},
            timeout=15,
        )
        resp.raise_for_status()
        klines = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Binance request failed: {exc}")

    if not isinstance(klines, list) or len(klines) == 0:
        raise HTTPException(status_code=404, detail=f"No crypto data for {symbol}.")

    return {
        "symbol": symbol,
        "labels": [str(k[0]) for k in klines],
        "prices": [float(k[4]) for k in klines],  # close price
    }


# ── Community prediction votes ─────────────────────────────────────────────────
@app.get("/api/predictions/votes")
def get_votes(symbols: str = ""):
    """Return vote counts. If symbols is empty, returns top 20 by total votes (for trending)."""
    predictions = _read_json_dict(PREDICTIONS_FILE)
    requested = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not requested:
        # Return top 20 most voted for trending section
        sorted_preds = sorted(
            predictions.items(),
            key=lambda x: x[1].get("up", 0) + x[1].get("down", 0),
            reverse=True,
        )
        return dict(sorted_preds[:20])
    return {
        sym: predictions.get(sym, {"up": 0, "down": 0})
        for sym in requested
    }


@app.post("/api/predictions/vote")
def submit_vote(body: VoteRequest, current_user: str = Depends(require_auth)):
    """Submit or toggle a community prediction vote. Requires auth."""
    direction = body.direction.upper()
    if direction not in ("UP", "DOWN"):
        raise HTTPException(status_code=400, detail="direction must be 'UP' or 'DOWN'")

    symbol = body.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol is required")

    predictions = _read_json_dict(PREDICTIONS_FILE)
    user_votes = _read_json_dict(USER_VOTES_FILE)

    symbol_counts = predictions.get(symbol, {"up": 0, "down": 0})
    user_symbol_votes = user_votes.get(current_user, {})
    existing = user_symbol_votes.get(symbol)

    if existing == direction:
        # Toggle off — remove the vote
        del user_symbol_votes[symbol]
        if direction == "UP":
            symbol_counts["up"] = max(0, symbol_counts["up"] - 1)
        else:
            symbol_counts["down"] = max(0, symbol_counts["down"] - 1)
    else:
        # Switch from opposite or cast a fresh vote
        if existing == "UP":
            symbol_counts["up"] = max(0, symbol_counts["up"] - 1)
        elif existing == "DOWN":
            symbol_counts["down"] = max(0, symbol_counts["down"] - 1)

        user_symbol_votes[symbol] = direction
        if direction == "UP":
            symbol_counts["up"] = symbol_counts.get("up", 0) + 1
        else:
            symbol_counts["down"] = symbol_counts.get("down", 0) + 1

    predictions[symbol] = symbol_counts
    user_votes[current_user] = user_symbol_votes

    PREDICTIONS_FILE.write_text(json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8")
    USER_VOTES_FILE.write_text(json.dumps(user_votes, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"symbol": symbol, **symbol_counts}


@app.get("/api/predictions/myvotes")
def get_my_votes(current_user: str = Depends(require_auth)):
    """Return the authenticated user's current votes (symbol -> direction)."""
    user_votes = _read_json_dict(USER_VOTES_FILE)
    return user_votes.get(current_user, {})
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
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

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# ── File-based storage ─────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
HISTORY_FILE = DATA_DIR / "sentiment_history.json"


def _read_json(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_json(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


# ── Pydantic models ────────────────────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/register", status_code=201)
def register(body: AuthRequest):
    users = _read_json(USERS_FILE)
    if any(u["email"] == body.email for u in users):
        raise HTTPException(status_code=409, detail="Email already registered")
    users.append({"email": body.email, "password": pwd_ctx.hash(body.password)})
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
    if not pwd_ctx.verify(body.password, user["password"]):
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
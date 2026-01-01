from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .python.sentiment_analysis import analyze_market_sentiment

app = FastAPI(title="Trading Bot API", version="0.1.0")

# Dev-friendly CORS (tighten in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
            "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "summary": {"positive": 0, "neutral": 0, "negative": 0, "avg_compound": 0},
            "articles": [],
            "warning": "Empty query",
        }

    num_articles = max(1, min(int(num_articles), 50))
    return analyze_market_sentiment(query=query, num_articles=num_articles, model=model)

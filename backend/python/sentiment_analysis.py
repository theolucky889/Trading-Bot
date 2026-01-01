from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Literal, Optional, Tuple
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

Label = Literal["positive", "neutral", "negative"]

_analyzer = SentimentIntensityAnalyzer()


@dataclass
class ArticleSentiment:
    title: str
    link: str
    source: Optional[str]
    published: Optional[str]
    excerpt: Optional[str]
    compound: float
    label: Label


def _label_from_compound(compound: float) -> Label:
    # Common VADER thresholds
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _safe_parse_time(value: str | None) -> Optional[str]:
    if not value:
        return None
    try:
        return dtparser.parse(value).isoformat()
    except Exception:
        return value


def _extract_text_excerpt(url: str, timeout: int = 8) -> Optional[str]:
    # Lightweight extractor: grab visible <p> text and return first ~280 chars
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = " ".join([t for t in paragraphs if t])
        text = " ".join(text.split())
        if not text:
            return None
        return text[:280]
    except Exception:
        return None


def fetch_google_news_rss(query: str, num_articles: int = 10, lang: str = "en-US", region: str = "US") -> List[dict]:
    q = quote_plus(query)
    # Google News RSS Search endpoint
    url = f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={region}:{lang.split('-')[0]}"
    feed = feedparser.parse(url)
    entries = feed.get("entries", [])[: max(0, int(num_articles))]
    out = []
    for e in entries:
        out.append(
            {
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "source": (e.get("source") or {}).get("title") if isinstance(e.get("source"), dict) else None,
                "published": _safe_parse_time(e.get("published") or e.get("updated")),
            }
        )
    return out


def analyze_sentiment_vader(text: str) -> Tuple[float, Label]:
    scores = _analyzer.polarity_scores(text or "")
    compound = float(scores.get("compound", 0.0))
    return compound, _label_from_compound(compound)


def analyze_market_sentiment(query: str, num_articles: int = 10, model: str = "vader") -> dict:
    # Currently, we ship VADER by default. If user requests finbert but it's not installed,
    # we fall back to VADER.
    model_used = model
    if model.lower() != "vader":
        model_used = "vader"

    entries = fetch_google_news_rss(query, num_articles=num_articles)
    articles: List[ArticleSentiment] = []

    for e in entries:
        title = e.get("title") or ""
        link = e.get("link") or ""
        excerpt = _extract_text_excerpt(link) if link else None

        # Use excerpt if available; otherwise analyze title only.
        text_for_sentiment = (excerpt or "") + " " + title
        compound, label = analyze_sentiment_vader(text_for_sentiment)

        articles.append(
            ArticleSentiment(
                title=title,
                link=link,
                source=e.get("source"),
                published=e.get("published"),
                excerpt=excerpt,
                compound=round(compound, 4),
                label=label,
            )
        )

    pos = sum(1 for a in articles if a.label == "positive")
    neg = sum(1 for a in articles if a.label == "negative")
    neu = sum(1 for a in articles if a.label == "neutral")
    avg = round(sum(a.compound for a in articles) / len(articles), 4) if articles else 0.0

    payload = {
        "query": query,
        "model": model_used,
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "summary": {"positive": pos, "neutral": neu, "negative": neg, "avg_compound": avg},
        "articles": [asdict(a) for a in articles],
    }
    if model.lower() == "finbert":
        payload["warning"] = "finbert not installed; fell back to vader"
    return payload

def analyze(query: str, num_articles: int = 10, model: str = "vader") -> dict:
    return analyze_market_sentiment(query, num_articles=num_articles, model=model)

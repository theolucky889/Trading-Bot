"""Stock analysis harness.

Pipeline: price data -> indicators -> technical signals -> news sentiment
-> weighted composite score in [-1, 1] -> verdict.

Each signal carries its own score and a human-readable reason so the frontend
can show *why* the harness reached its verdict, not just the number.
"""

from __future__ import annotations

import datetime as dt
from datetime import timezone
from typing import List, Optional

from .data import PriceSeries, get_price_series
from .indicators import annualized_volatility, bollinger, macd, max_drawdown, rsi, sma

# Composite weights: technicals carry most of the signal, sentiment tilts it.
WEIGHT_TECHNICAL = 0.7
WEIGHT_SENTIMENT = 0.3

VERDICTS = [
    (0.5, "strong_buy"),
    (0.15, "buy"),
    (-0.15, "hold"),
    (-0.5, "sell"),
]


def _verdict(score: float) -> str:
    for threshold, label in VERDICTS:
        if score >= threshold:
            return label
    return "strong_sell"


class StockAnalysisHarness:
    """Runs the full analysis pipeline for one symbol."""

    def __init__(self, days: int = 365, include_sentiment: bool = True, num_articles: int = 10):
        self.days = days
        self.include_sentiment = include_sentiment
        self.num_articles = num_articles

    # ── technical signals ────────────────────────────────────────────
    def _technical_signals(self, closes: List[float]) -> List[dict]:
        signals: List[dict] = []
        last = closes[-1]

        sma20, sma50 = sma(closes, 20), sma(closes, 50)
        if sma20[-1] is not None and sma50[-1] is not None:
            above = sma20[-1] > sma50[-1]
            signals.append({
                "name": "trend",
                "indicator": "SMA 20/50",
                "score": 1.0 if above else -1.0,
                "value": round(sma20[-1] - sma50[-1], 4),
                "reason": "Fast SMA above slow SMA (uptrend)" if above
                          else "Fast SMA below slow SMA (downtrend)",
            })

        r = rsi(closes, 14)
        if r[-1] is not None:
            v = r[-1]
            if v < 30:
                score, reason = 0.8, f"RSI {v:.0f} — oversold, potential rebound"
            elif v > 70:
                score, reason = -0.8, f"RSI {v:.0f} — overbought, pullback risk"
            else:
                score, reason = 0.0, f"RSI {v:.0f} — neutral zone"
            signals.append({"name": "momentum", "indicator": "RSI(14)",
                            "score": score, "value": round(v, 2), "reason": reason})

        line, sig_line, hist = macd(closes)
        if hist[-1] is not None:
            bullish = hist[-1] > 0
            signals.append({
                "name": "macd",
                "indicator": "MACD(12,26,9)",
                "score": 0.6 if bullish else -0.6,
                "value": round(hist[-1], 4),
                "reason": "MACD above signal line (bullish momentum)" if bullish
                          else "MACD below signal line (bearish momentum)",
            })

        upper, middle, lower = bollinger(closes)
        if upper[-1] is not None and lower[-1] is not None:
            band = upper[-1] - lower[-1]
            pct_b = (last - lower[-1]) / band if band else 0.5
            if pct_b < 0.05:
                score, reason = 0.5, "Price at lower Bollinger band (stretched down)"
            elif pct_b > 0.95:
                score, reason = -0.5, "Price at upper Bollinger band (stretched up)"
            else:
                score, reason = 0.0, "Price inside Bollinger bands"
            signals.append({"name": "bollinger", "indicator": "Bollinger(20,2)",
                            "score": score, "value": round(pct_b, 3), "reason": reason})

        return signals

    # ── sentiment ────────────────────────────────────────────────────
    def _sentiment(self, symbol: str) -> Optional[dict]:
        if not self.include_sentiment:
            return None
        try:
            from .. import sentiment_analysis

            data = sentiment_analysis.analyze_market_sentiment(
                query=f"{symbol} stock", num_articles=self.num_articles
            )
            summary = data.get("summary", {})
            return {
                "score": float(summary.get("avg_compound", 0.0)),
                "summary": summary,
                "articles": data.get("articles", [])[:5],
            }
        except Exception as exc:
            return {"score": 0.0, "summary": None, "articles": [],
                    "warning": f"Sentiment unavailable: {exc.__class__.__name__}"}

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _change_over_calendar_days(dates: List[str], closes: List[float], days: int) -> float:
        """Return the fractional price change over the last ``days`` CALENDAR days.

        The frontend labels this "30-day change", so we anchor on the calendar
        date ``days`` days before the latest bar and use the close of the first
        bar on or after that date (markets are closed on weekends/holidays).
        Falls back to the oldest available bar when history is shorter than the
        requested window.
        """
        if not closes:
            return 0.0
        last = closes[-1]
        # If dates are missing/misaligned, fall back to the oldest bar.
        if not dates or len(dates) != len(closes):
            base = closes[0]
            return last / base - 1 if base else 0.0
        try:
            cutoff = dt.date.fromisoformat(dates[-1][:10]) - dt.timedelta(days=days)
        except (ValueError, TypeError):
            base = closes[0]
            return last / base - 1 if base else 0.0
        # Find the first bar on or after the cutoff date.
        base_idx = 0
        for i, d in enumerate(dates):
            try:
                if dt.date.fromisoformat(d[:10]) >= cutoff:
                    base_idx = i
                    break
            except (ValueError, TypeError):
                continue
        base = closes[base_idx]
        return last / base - 1 if base else 0.0

    # ── main entry ───────────────────────────────────────────────────
    def analyze(self, symbol: str, series: Optional[PriceSeries] = None) -> dict:
        series = series or get_price_series(symbol, self.days)
        closes = series.closes
        if len(closes) < 30:
            raise ValueError(f"Not enough price history for {symbol} ({len(closes)} bars)")

        signals = self._technical_signals(closes)
        technical_score = (
            sum(s["score"] for s in signals) / len(signals) if signals else 0.0
        )

        sentiment = self._sentiment(series.symbol)
        sentiment_score = sentiment["score"] if sentiment else 0.0

        if sentiment is not None:
            composite = WEIGHT_TECHNICAL * technical_score + WEIGHT_SENTIMENT * sentiment_score
        else:
            composite = technical_score
        composite = max(-1.0, min(1.0, composite))

        sma20, sma50 = sma(closes, 20), sma(closes, 50)
        change_30d = self._change_over_calendar_days(series.dates, closes, 30)

        return {
            "symbol": series.symbol,
            "source": series.source,
            "warning": series.warning,
            "generated_at": dt.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            "last_price": round(closes[-1], 4),
            "change_30d": round(change_30d, 4),
            "stats": {
                "volatility_annualized": round(annualized_volatility(closes), 4),
                "max_drawdown": round(max_drawdown(closes), 4),
                "high": round(max(closes), 4),
                "low": round(min(closes), 4),
            },
            "signals": signals,
            "technical_score": round(technical_score, 4),
            "sentiment": sentiment,
            "composite_score": round(composite, 4),
            "verdict": _verdict(composite),
            "chart": {
                "dates": series.dates,
                "closes": closes,
                "sma20": [round(v, 4) if v is not None else None for v in sma20],
                "sma50": [round(v, 4) if v is not None else None for v in sma50],
            },
        }


def analyze_stock(symbol: str, days: int = 365, include_sentiment: bool = True) -> dict:
    """Convenience wrapper used by the API layer."""
    return StockAnalysisHarness(days=days, include_sentiment=include_sentiment).analyze(symbol)

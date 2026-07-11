"""Quantitative analysis harness for the Trading Bot.

Modules:
    data       - OHLCV price fetching (Stooq / Binance, synthetic fallback)
    indicators - pure-Python technical indicators (SMA, EMA, RSI, MACD, Bollinger)
    strategies - signal generators + strategy registry
    backtest   - event-free vectorized backtester with performance metrics
    harness    - StockAnalysisHarness combining technicals + news sentiment
"""

from .harness import StockAnalysisHarness, analyze_stock
from .backtest import run_backtest
from .strategies import STRATEGIES

__all__ = ["StockAnalysisHarness", "analyze_stock", "run_backtest", "STRATEGIES"]

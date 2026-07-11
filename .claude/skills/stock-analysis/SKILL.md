---
name: stock-analysis
description: >-
  How the Trading Bot's stock analysis harness works and how to extend it.
  Use whenever working on backend/python/quant/harness.py, indicators.py, or
  data.py — adding indicators or signals, changing composite scoring, weights,
  verdict thresholds, sentiment integration, or the /api/analyze contract.
  Also use when asked to "analyze a stock", interpret a verdict, or debug why
  a symbol returns synthetic data.
---

# Stock Analysis Harness

Pipeline (all in `backend/python/quant/`):

```
data.py: get_price_series(symbol, days)      # yahoo → stooq → synthetic fallback
  → indicators.py                            # SMA/EMA/RSI/MACD/Bollinger, pure Python
  → harness.py: StockAnalysisHarness.analyze # signals → scores → verdict
  → app.py: GET /api/analyze                 # served to AnalysisView.vue
```

## Signal contract

Each technical signal is a dict — the frontend (`src/api/analysis.ts`) types this
exactly, so keep the shape stable:

```python
{"name": str, "indicator": str, "score": float,  # in [-1, 1]
 "value": float, "reason": str}                  # reason is REQUIRED — the UI shows it
```

Composite: `0.7 * mean(signal scores) + 0.3 * sentiment avg_compound`, clamped
to [-1, 1]. Verdict thresholds (harness.py `VERDICTS`): ≥0.5 strong_buy,
≥0.15 buy, ≥-0.15 hold, ≥-0.5 sell, else strong_sell.

## Adding a new signal

1. Implement the indicator in `indicators.py` — return a list padded with
   `None` to the input length (this keeps chart/signal indexing aligned).
2. Add a block in `StockAnalysisHarness._technical_signals` producing one
   signal dict with a meaningful `reason` for each branch.
3. The composite score adapts automatically (it averages all signals).
4. If the frontend should chart the new indicator, extend the `chart` payload
   in `analyze()` AND the `AnalysisResult` type in `src/api/analysis.ts` AND
   `AnalysisView.vue` — same task, never later.

## Data source rules

- `get_price_series` returns `PriceSeries(symbol, source, candles, warning)`.
- Symbol conventions: US tickers as-is (`AAPL`); Taiwan numeric (`2330` →
  Yahoo `2330.TW`); crypto pairs ending in USDT/USD/etc go to Binance.
- On any fetch failure it falls back to deterministic synthetic data with a
  `warning` — never raise from the data layer for network problems. The
  frontend shows the warning banner; keep that field populated.

## Sentiment

`harness.py::_sentiment` calls `backend/python/sentiment_analysis.py`
(VADER over Google News RSS). It must never break the analysis: failures
return `score 0.0` with a `warning`. Query format is `"{symbol} stock"`.

## Verification (run after every change)

```bash
cd E:/Github/Trading-Bot
python -c "
from backend.python.quant.data import PriceSeries, synthetic_daily
from backend.python.quant.harness import StockAnalysisHarness
s = PriceSeries('TEST','synthetic',synthetic_daily('TEST',400))
r = StockAnalysisHarness(include_sentiment=False).analyze('TEST', series=s)
assert -1 <= r['composite_score'] <= 1 and r['verdict'] and r['signals']
assert all(sig['reason'] for sig in r['signals'])
print('OK', r['verdict'], [s['name'] for s in r['signals']])"
```

If you changed weights, thresholds, or the response shape, also update this
skill file and add a row to CLAUDE.md's harness change log.

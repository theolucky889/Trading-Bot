import type { SentimentArticle, SentimentSummary } from './sentiment'

export type Verdict = 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell'

export type AnalysisSignal = {
  name: string
  indicator: string
  score: number
  value: number
  reason: string
}

export type AnalysisSentiment = {
  score: number
  summary: SentimentSummary | null
  articles: SentimentArticle[]
  warning?: string
} | null

export type AnalysisResult = {
  symbol: string
  source: string
  warning: string | null
  generated_at: string
  last_price: number
  change_30d: number
  stats: {
    volatility_annualized: number
    max_drawdown: number
    high: number
    low: number
  }
  signals: AnalysisSignal[]
  technical_score: number
  sentiment: AnalysisSentiment
  composite_score: number
  verdict: Verdict
  chart: {
    dates: string[]
    closes: number[]
    sma20: (number | null)[]
    sma50: (number | null)[]
  }
}

export async function fetchAnalysis(
  symbol: string,
  days = 365,
  includeSentiment = true
): Promise<AnalysisResult> {
  const url =
    `/api/analyze?symbol=${encodeURIComponent(symbol)}` +
    `&days=${encodeURIComponent(days)}` +
    `&include_sentiment=${includeSentiment}`

  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Analysis API failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

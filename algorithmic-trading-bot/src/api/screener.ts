// Typed client for GET /api/screener — mirrors backend/python/quant/screener.py
// (documented in _workspace/9_analyst_screener.md) 1:1. Note the many nullable
// metric fields: a synthetic / insufficient-history row carries score: null,
// verdict: "n/a", and always sorts last.

export type ScreenerVerdict =
  | 'strong_buy'
  | 'buy'
  | 'hold'
  | 'sell'
  | 'strong_sell'
  | 'n/a'

export type ScreenerTrend = 'up' | 'down' | 'flat'

export type ScreenerRow = {
  symbol: string
  name: string
  sector: string
  last_price: number | null
  score: number | null
  technical_score: number | null
  verdict: ScreenerVerdict
  rsi: number | null
  trend: ScreenerTrend
  momentum_1m: number | null
  momentum_3m: number | null
  volatility: number | null
  max_drawdown: number | null
  source: string
  warning: string | null
}

export type ScreenerError = {
  symbol: string
  error: string
}

export type ScreenerResponse = {
  market: string
  generated_at: string
  cached: boolean
  days: number
  universe_size: number
  scanned: number
  errors: ScreenerError[]
  warnings: string[]
  rows: ScreenerRow[]
}

export async function fetchScreener(
  market = 'tw',
  days = 365,
  refresh = false
): Promise<ScreenerResponse> {
  const url =
    `/api/screener?market=${encodeURIComponent(market)}` +
    `&days=${encodeURIComponent(days)}` +
    `&refresh=${refresh}`

  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Screener API failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

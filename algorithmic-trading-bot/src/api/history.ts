// Mirrors GET /api/history (FastAPI, backend/app.py) 1:1.
// Response shape: { symbol, source, candles[{date,open,high,low,close,volume}], warning }

export type Candle = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export type PriceHistory = {
  symbol: string
  source: string
  candles: Candle[]
  warning: string | null
}

export async function fetchHistory(symbol: string, days = 365): Promise<PriceHistory> {
  const url =
    `/api/history?symbol=${encodeURIComponent(symbol)}` + `&days=${encodeURIComponent(days)}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `History API failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export type StrategyInfo = {
  name: string
  label: string
  description: string
  params: Record<string, number>
}

export type BacktestMetrics = {
  total_return: number
  cagr: number
  sharpe: number
  max_drawdown: number
  volatility: number
}

export type BacktestTrade = {
  date: string
  side: 'buy' | 'sell'
  price: number
  return?: number
}

export type BacktestResult = {
  symbol: string
  source: string
  warning: string | null
  strategy: string
  params: Record<string, number>
  days: number
  start: string
  end: string
  initial_capital: number
  commission_bps: number
  result: {
    equity_curve: number[]
    dates: string[]
    trades: BacktestTrade[]
    num_trades: number
    win_rate: number | null
    final_equity: number
    metrics: BacktestMetrics
  }
  benchmark: {
    symbol: string
    warning: string | null
    equity_curve: number[]
    final_equity: number
    metrics: BacktestMetrics
  }
}

export async function fetchStrategies(): Promise<StrategyInfo[]> {
  const res = await fetch('/api/strategies', { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`Strategies API failed: ${res.status} ${res.statusText}`)
  const data = await res.json()
  return data.strategies
}

export async function runBacktest(req: {
  symbol: string
  strategy: string
  params?: Record<string, number>
  days?: number
  initial_capital?: number
  commission_bps?: number
  benchmark_symbol?: string
}): Promise<BacktestResult> {
  const res = await fetch('/api/backtest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(req)
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Backtest API failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

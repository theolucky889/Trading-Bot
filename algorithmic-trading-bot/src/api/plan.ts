export type SectorTicker = { symbol: string; name: string }

export type Sector = {
  id: string
  label: string
  market: 'TW' | 'US' | 'CRYPTO'
  tickers: SectorTicker[]
}

export type PlanAllocation = {
  symbol: string
  name: string
  sector: string
  sector_label: string
  weight: number
  monthly_amount: number
  shares: number
  final_value: number
}

export type PlanResult = {
  monthly_budget: number
  months: number
  sectors: string[]
  benchmark: string
  warnings: string[]
  allocation: PlanAllocation[]
  simulation: {
    month_labels: string[]
    invested: number[]
    portfolio_value: number[]
    benchmark_value: number[]
    summary: {
      months_simulated: number
      invested: number
      final_value: number
      total_return: number
      benchmark_final_value: number
      benchmark_return: number
    }
  }
  projection: {
    months: number
    expected_monthly_return: number
    monthly_volatility: number
    invested: number
    expected: number
    optimistic: number
    pessimistic: number
    note: string
  }
  disclaimer: string
}

export async function fetchSectors(): Promise<Sector[]> {
  const res = await fetch('/api/sectors', { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error(`Sectors API failed: ${res.status} ${res.statusText}`)
  return (await res.json()).sectors
}

export async function buildPlan(req: {
  monthly_budget: number
  months: number
  sectors: string[]
  benchmark?: string
}): Promise<PlanResult> {
  const res = await fetch('/api/plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(req)
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    throw new Error(
      typeof detail === 'string' ? detail : `Plan API failed: ${res.status} ${res.statusText}`
    )
  }
  return res.json()
}

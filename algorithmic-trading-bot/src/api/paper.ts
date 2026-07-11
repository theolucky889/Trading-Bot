// Typed client for the paper-trading (demo account) engine.
// Shapes mirror backend/python/quant/paper.py 1:1 (see
// _workspace/7_quant_paper_engine.md — field names/types/nullability are
// load-bearing). All monetary values are numbers (USD), rounded server-side.
// null is used where noted; do not assume non-null.

import { getAuthHeader } from './auth'

// ── Enums ────────────────────────────────────────────────────────────
export type Side = 'buy' | 'sell'
export type BotStatus = 'running' | 'stopped'
export type PaperKind = 'bot' | 'manual'

// ── State (GET /api/paper/state) ─────────────────────────────────────
export interface PaperAccount {
  cash: number // uninvested account cash (excludes bot allocations)
  equity: number // total: cash + Σ bot_equity + Σ manual market value
  initial_cash: number // 100000 (or whatever reset set)
  total_pnl: number // equity - initial_cash
  return_pct: number // (equity/initial - 1) * 100
}

export interface PaperPosition {
  symbol: string
  qty: number // shares/units held (up to 8 dp)
  avg_price: number | null // entry average; null only if unknown
  current_price: number | null // latest real close; null if synthetic/no data
  market_value: number // qty * current_price (falls back to qty*avg if no price)
  unrealized_pnl: number // (current_price - avg_price) * qty; 0 if no price
  kind: PaperKind
  bot_id: number | null // set when kind === 'bot', else null
  source: string // 'yahoo' | 'binance' | 'synthetic' | ...
}

export interface PaperBot {
  id: number
  symbol: string
  strategy: string // registry key, e.g. 'sma_crossover'
  params: Record<string, number> // merged (defaults + overrides)
  allocated_cash: number
  status: BotStatus
  position_qty: number // 0 when flat
  avg_price: number | null // null when flat
  current_price: number | null // latest real close; null if synthetic/no data
  market_value: number // 0 when flat
  free_cash: number // bot's uninvested ledger cash (alloc - net flows)
  bot_equity: number // free_cash + market_value (bot's total worth)
  unrealized_pnl: number // 0 when flat or no price
  last_processed_date: string | null // ISO date; null until first tick with real data
  source: string
  warning: string | null // per-bot price warning, e.g. synthetic fallback
  created_at: string // ISO datetime + 'Z'
}

export interface EquityPoint {
  date: string // ISO date 'YYYY-MM-DD'
  equity: number
}

export interface PaperState {
  email: string
  account: PaperAccount
  positions: PaperPosition[] // bot-held AND manual positions with live P&L
  bots: PaperBot[]
  equity_curve: EquityPoint[] // daily snapshots, ascending by date
  warnings: string[]
}

// ── Created bot (POST /api/paper/bots) ───────────────────────────────
export interface CreatedBot {
  id: number
  email: string
  symbol: string
  strategy: string
  params: Record<string, number>
  allocated_cash: number
  status: 'running'
  last_processed_date: string | null
  created_at: string
}

// ── Bot status (POST /api/paper/bots/{id}/status) ────────────────────
export interface StatusResult {
  id: number
  status: BotStatus
}

// ── Delete bot (DELETE /api/paper/bots/{id}) ─────────────────────────
export interface DeleteResult {
  id: number
  refunded: number // cash returned to account
  warning: string | null
}

// ── Manual trade (POST /api/paper/trade) — discriminated union ───────
export interface ManualExecuted {
  executed: true
  symbol: string
  side: Side
  qty: number // filled quantity (sells may be clamped < requested)
  price: number // real close used as the fill price
  commission: number
  executed_at: string // ISO date of the bar used
  source: string // 'yahoo' | 'binance' | ...
  warning: null
}

export interface ManualSkipped {
  executed: false
  symbol: string
  side: Side
  warning: string // why nothing happened
  source: string // 'synthetic'
}

export type ManualResult = ManualExecuted | ManualSkipped

// ── Trades (GET /api/paper/trades) ───────────────────────────────────
export interface PaperTrade {
  id: number
  bot_id: number | null // null for manual trades
  symbol: string
  side: Side
  qty: number
  price: number // real close the trade filled at
  commission: number
  executed_at: string // ISO date 'YYYY-MM-DD'
  kind: PaperKind
}

// ── Reset (POST /api/paper/reset) ────────────────────────────────────
export interface ResetResult {
  email: string
  cash: number // 100000
  reset_at: string // ISO datetime + 'Z'
}

// ── HTTP plumbing ────────────────────────────────────────────────────

/** Thrown on any non-OK paper response. `status` lets callers detect 401. */
export class PaperApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'PaperApiError'
    this.status = status
  }
}

function jsonHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json'
  }
  const auth = getAuthHeader()
  if ('Authorization' in auth && auth.Authorization) {
    headers.Authorization = auth.Authorization
  }
  return headers
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    // The paper/auth endpoints key user-facing errors by `message`; fall back
    // to FastAPI's `detail` and then the status line.
    const msg = body?.message ?? body?.detail ?? `${res.status} ${res.statusText}`
    throw new PaperApiError(msg, res.status)
  }
  return res.json() as Promise<T>
}

// ── Public API ───────────────────────────────────────────────────────

export async function fetchPaperState(): Promise<PaperState> {
  const res = await fetch('/api/paper/state', { headers: jsonHeaders() })
  return handle<PaperState>(res)
}

export async function fetchPaperTrades(limit = 100): Promise<PaperTrade[]> {
  const res = await fetch(`/api/paper/trades?limit=${encodeURIComponent(limit)}`, {
    headers: jsonHeaders()
  })
  return handle<PaperTrade[]>(res)
}

export async function createPaperBot(req: {
  symbol: string
  strategy: string
  params?: Record<string, number>
  allocated_cash: number
}): Promise<CreatedBot> {
  const res = await fetch('/api/paper/bots', {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(req)
  })
  return handle<CreatedBot>(res)
}

export async function setPaperBotStatus(
  botId: number,
  status: BotStatus
): Promise<StatusResult> {
  const res = await fetch(`/api/paper/bots/${botId}/status`, {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify({ status })
  })
  return handle<StatusResult>(res)
}

export async function deletePaperBot(botId: number): Promise<DeleteResult> {
  const res = await fetch(`/api/paper/bots/${botId}`, {
    method: 'DELETE',
    headers: jsonHeaders()
  })
  return handle<DeleteResult>(res)
}

export async function submitManualTrade(req: {
  symbol: string
  side: Side
  notional_usd: number
}): Promise<ManualResult> {
  const res = await fetch('/api/paper/trade', {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(req)
  })
  return handle<ManualResult>(res)
}

export async function resetPaperAccount(): Promise<ResetResult> {
  const res = await fetch('/api/paper/reset', {
    method: 'POST',
    headers: jsonHeaders()
  })
  return handle<ResetResult>(res)
}

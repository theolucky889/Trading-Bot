<template>
  <div class="flex min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200">
    <!-- ░░░ Sidebar tabs ░░░ -->
    <aside class="w-64 bg-gradient-to-b from-gray-800 to-gray-900 p-4 shadow-xl rounded-r-3xl">
      <h2 class="text-lg font-bold mb-4 px-2 tracking-wide">Tradebot</h2>
      <ul class="space-y-1">
        <li v-for="tab in tabs" :key="tab.id">
          <button
            type="button"
            class="w-full text-left px-4 py-2 rounded-lg transition-colors flex items-center justify-between"
            :class="activeTab === tab.id
              ? 'bg-indigo-600 text-white font-semibold'
              : 'hover:bg-gray-700 text-gray-300'"
            @click="activeTab = tab.id"
          >
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.soon"
              class="ml-2 px-2 py-0.5 text-[10px] font-semibold rounded-full bg-gray-700 text-gray-400"
            >
              Soon
            </span>
          </button>
        </li>
      </ul>
    </aside>

    <!-- ░░░ Main content ░░░ -->
    <main class="flex-1 p-8 space-y-6 overflow-y-auto">
      <!-- Shared status bar: refresh + errors + warnings (visible on live tabs) -->
      <template v-if="isLiveTab">
        <div class="flex items-center justify-between gap-3">
          <h1 class="text-3xl font-extrabold">{{ activeLabel }}</h1>
          <div class="flex items-center gap-3">
            <span v-if="lastUpdated" class="text-xs text-gray-500">
              Updated {{ lastUpdated }}
            </span>
            <button
              type="button"
              :disabled="loading"
              class="px-4 py-2 text-sm rounded-xl bg-gray-700 hover:bg-gray-600 disabled:opacity-50 transition-colors"
              @click="refresh"
            >
              {{ loading ? 'Refreshing…' : 'Refresh' }}
            </button>
          </div>
        </div>

        <p
          v-if="error"
          class="p-4 bg-red-900/40 border border-red-700 rounded-xl text-red-300"
        >
          {{ error }}
        </p>

        <div
          v-if="state && state.warnings.length"
          class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300 space-y-1"
        >
          <p v-for="(w, i) in state.warnings" :key="i" class="text-sm">{{ w }}</p>
        </div>
      </template>

      <!-- ══════════════ Overview ══════════════ -->
      <div v-if="activeTab === 'overview'" class="space-y-6">
        <!-- Demo-account banner -->
        <section
          class="bg-gradient-to-r from-indigo-900/40 to-gray-800/60 p-5 rounded-3xl ring-1 ring-indigo-700/40 shadow-lg flex flex-wrap items-center justify-between gap-4"
        >
          <div>
            <p class="font-semibold text-indigo-200">Paper trading — fake money, real market prices</p>
            <p class="text-sm text-gray-400">
              Bots and manual trades fill at live closes. No real capital is at risk.
            </p>
          </div>
          <div v-if="!confirmingReset">
            <button
              type="button"
              class="px-4 py-2 text-sm rounded-xl bg-red-700/70 hover:bg-red-700 transition-colors"
              @click="confirmingReset = true"
            >
              Reset account
            </button>
          </div>
          <div v-else class="flex items-center gap-2">
            <span class="text-sm text-red-300">Wipe bots, trades &amp; positions?</span>
            <button
              type="button"
              :disabled="busy"
              class="px-3 py-2 text-sm rounded-xl bg-red-700 hover:bg-red-600 disabled:opacity-50 transition-colors"
              @click="doReset"
            >
              Confirm reset
            </button>
            <button
              type="button"
              class="px-3 py-2 text-sm rounded-xl bg-gray-700 hover:bg-gray-600 transition-colors"
              @click="confirmingReset = false"
            >
              Cancel
            </button>
          </div>
        </section>

        <!-- Account cards -->
        <section v-if="state" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Cash" :value="usd(state.account.cash)" neutral />
          <StatCard label="Equity" :value="usd(state.account.equity)" neutral />
          <StatCard
            label="Total P&L"
            :value="usd(state.account.total_pnl)"
            :positive="state.account.total_pnl >= 0"
          />
          <StatCard
            label="Return"
            :value="`${state.account.return_pct.toFixed(2)}%`"
            :positive="state.account.return_pct >= 0"
          />
        </section>
        <p v-else-if="!error" class="text-gray-500">Loading account…</p>

        <!-- Positions -->
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Positions</h2>
          <div v-if="state && state.positions.length" class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="text-gray-400 text-left">
                <tr>
                  <th class="py-2 pr-6">Symbol</th>
                  <th class="py-2 pr-6">Qty</th>
                  <th class="py-2 pr-6">Avg Price</th>
                  <th class="py-2 pr-6">Current</th>
                  <th class="py-2 pr-6">Market Value</th>
                  <th class="py-2 pr-6">Unrealized P&L</th>
                  <th class="py-2">Source</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(p, i) in state.positions"
                  :key="`${p.symbol}-${p.kind}-${p.bot_id ?? 'm'}-${i}`"
                  class="border-t border-gray-700/50"
                >
                  <td class="py-2 pr-6 font-medium">
                    {{ p.symbol }}
                    <span
                      class="ml-1 px-1.5 py-0.5 text-[10px] rounded-full"
                      :class="p.kind === 'bot' ? 'bg-indigo-900/60 text-indigo-300' : 'bg-gray-700 text-gray-300'"
                    >
                      {{ p.kind }}
                    </span>
                  </td>
                  <td class="py-2 pr-6">{{ fmtQty(p.qty) }}</td>
                  <td class="py-2 pr-6">{{ p.avg_price === null ? '—' : usd(p.avg_price) }}</td>
                  <td class="py-2 pr-6">{{ p.current_price === null ? '—' : usd(p.current_price) }}</td>
                  <td class="py-2 pr-6">{{ usd(p.market_value) }}</td>
                  <td class="py-2 pr-6" :class="p.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'">
                    {{ usd(p.unrealized_pnl) }}
                  </td>
                  <td class="py-2">
                    <span :class="sourceBadge(p.source)">{{ p.source }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="text-gray-500 text-sm">No open positions.</p>
        </section>

        <!-- Bots -->
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg space-y-4">
          <h2 class="text-xl font-bold">Bots</h2>
          <div v-if="state && state.bots.length" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div
              v-for="bot in state.bots"
              :key="bot.id"
              class="bg-gray-900/60 p-4 rounded-2xl ring-1 ring-gray-700/40 space-y-3"
            >
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="font-semibold">{{ bot.symbol }}</p>
                  <p class="text-xs text-gray-400">{{ bot.strategy }}</p>
                </div>
                <span
                  class="px-2 py-0.5 text-[11px] font-semibold rounded-full"
                  :class="bot.status === 'running'
                    ? 'bg-green-900/50 text-green-300'
                    : 'bg-gray-700 text-gray-300'"
                >
                  {{ bot.status }}
                </span>
              </div>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p class="text-[11px] text-gray-500 uppercase">Allocated</p>
                  <p>{{ usd(bot.allocated_cash) }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-gray-500 uppercase">Bot Equity</p>
                  <p>{{ usd(bot.bot_equity) }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-gray-500 uppercase">Position</p>
                  <p>{{ bot.position_qty > 0 ? `${fmtQty(bot.position_qty)} @ ${bot.avg_price === null ? '—' : usd(bot.avg_price)}` : 'flat' }}</p>
                </div>
                <div>
                  <p class="text-[11px] text-gray-500 uppercase">Unreal. P&L</p>
                  <p :class="bot.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'">
                    {{ usd(bot.unrealized_pnl) }}
                  </p>
                </div>
              </div>
              <p v-if="bot.warning" class="text-xs text-yellow-400">{{ bot.warning }}</p>
              <div class="flex items-center gap-2 pt-1">
                <button
                  v-if="bot.status === 'stopped'"
                  type="button"
                  :disabled="busy"
                  class="px-3 py-1.5 text-xs rounded-lg bg-green-700/70 hover:bg-green-700 disabled:opacity-50 transition-colors"
                  @click="changeBotStatus(bot.id, 'running')"
                >
                  Start
                </button>
                <button
                  v-else
                  type="button"
                  :disabled="busy"
                  class="px-3 py-1.5 text-xs rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 transition-colors"
                  @click="changeBotStatus(bot.id, 'stopped')"
                >
                  Stop
                </button>
                <button
                  type="button"
                  :disabled="busy"
                  class="px-3 py-1.5 text-xs rounded-lg bg-red-800/70 hover:bg-red-700 disabled:opacity-50 transition-colors"
                  @click="removeBot(bot.id)"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
          <p v-else class="text-gray-500 text-sm">No bots yet. Create one below.</p>

          <!-- New bot form -->
          <div class="border-t border-gray-700/50 pt-4">
            <h3 class="text-sm font-semibold text-gray-300 mb-3">New bot</h3>
            <div class="flex flex-wrap items-end gap-4">
              <div class="space-y-1">
                <label class="block text-xs font-medium text-gray-500">Symbol</label>
                <input
                  v-model="botForm.symbol"
                  placeholder="AAPL, BTCUSDT…"
                  class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg w-40 focus:ring-indigo-500 focus:border-indigo-500 uppercase"
                />
              </div>
              <div class="space-y-1">
                <label class="block text-xs font-medium text-gray-500">Strategy</label>
                <select
                  v-model="botForm.strategy"
                  class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option v-for="s in strategies" :key="s.name" :value="s.name">{{ s.label }}</option>
                </select>
              </div>
              <div class="space-y-1">
                <label class="block text-xs font-medium text-gray-500">Allocation ($)</label>
                <input
                  v-model.number="botForm.allocated_cash"
                  type="number"
                  min="1"
                  class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg w-36 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <button
                type="button"
                :disabled="busy || !botForm.symbol.trim()"
                class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl font-semibold shadow transition-colors"
                @click="addBot"
              >
                Create bot
              </button>
            </div>
            <!-- Per-strategy params -->
            <div v-if="Object.keys(botParams).length" class="flex flex-wrap items-end gap-4 mt-3">
              <p v-if="currentStrategy" class="text-xs text-gray-500 w-full">{{ currentStrategy.description }}</p>
              <div v-for="(_v, key) in botParams" :key="key" class="space-y-1">
                <label class="block text-[11px] font-medium text-gray-500">{{ key }}</label>
                <input
                  v-model.number="botParams[key]"
                  type="number"
                  step="any"
                  class="px-3 py-1.5 bg-gray-900 border border-gray-700 rounded-lg w-24 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </section>

        <!-- Manual trade -->
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg space-y-4">
          <h2 class="text-xl font-bold">Manual trade</h2>
          <div class="flex flex-wrap items-end gap-4">
            <div class="space-y-1">
              <label class="block text-xs font-medium text-gray-500">Symbol</label>
              <input
                v-model="tradeForm.symbol"
                placeholder="BTCUSDT, AAPL…"
                class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg w-40 focus:ring-indigo-500 focus:border-indigo-500 uppercase"
              />
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-medium text-gray-500">Side</label>
              <select
                v-model="tradeForm.side"
                class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>
            <div class="space-y-1">
              <label class="block text-xs font-medium text-gray-500">Notional ($)</label>
              <input
                v-model.number="tradeForm.notional_usd"
                type="number"
                min="1"
                class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg w-36 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <button
              type="button"
              :disabled="busy || !tradeForm.symbol.trim()"
              class="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl font-semibold shadow transition-colors"
              @click="submitTrade"
            >
              Submit trade
            </button>
          </div>
          <p
            v-if="tradeMessage"
            class="p-3 rounded-xl text-sm"
            :class="tradeExecuted
              ? 'bg-green-900/40 border border-green-700 text-green-300'
              : 'bg-yellow-900/40 border border-yellow-700 text-yellow-300'"
          >
            {{ tradeMessage }}
          </p>
        </section>
      </div>

      <!-- ══════════════ Trades ══════════════ -->
      <div v-else-if="activeTab === 'trades'" class="space-y-4">
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Trade History</h2>
          <div v-if="trades.length" class="overflow-x-auto max-h-[32rem] overflow-y-auto">
            <table class="w-full text-sm">
              <thead class="text-gray-400 text-left sticky top-0 bg-gray-800">
                <tr>
                  <th class="py-2 pr-6">Time</th>
                  <th class="py-2 pr-6">Kind</th>
                  <th class="py-2 pr-6">Symbol</th>
                  <th class="py-2 pr-6">Side</th>
                  <th class="py-2 pr-6">Qty</th>
                  <th class="py-2 pr-6">Price</th>
                  <th class="py-2">Commission</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in trades" :key="t.id" class="border-t border-gray-700/50">
                  <td class="py-2 pr-6">{{ t.executed_at }}</td>
                  <td class="py-2 pr-6">
                    <span
                      class="px-1.5 py-0.5 text-[10px] rounded-full"
                      :class="t.kind === 'bot' ? 'bg-indigo-900/60 text-indigo-300' : 'bg-gray-700 text-gray-300'"
                    >
                      {{ t.kind }}
                    </span>
                  </td>
                  <td class="py-2 pr-6 font-medium">{{ t.symbol }}</td>
                  <td class="py-2 pr-6" :class="t.side === 'buy' ? 'text-green-400' : 'text-red-400'">
                    {{ t.side.toUpperCase() }}
                  </td>
                  <td class="py-2 pr-6">{{ fmtQty(t.qty) }}</td>
                  <td class="py-2 pr-6">{{ usd(t.price) }}</td>
                  <td class="py-2">{{ usd(t.commission) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="text-gray-500 text-sm">No trades yet.</p>
        </section>
      </div>

      <!-- ══════════════ Performance ══════════════ -->
      <div v-else-if="activeTab === 'performance'" class="space-y-4">
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Equity Over Time</h2>
          <canvas
            v-show="state && state.equity_curve.length"
            ref="equityCanvas"
            class="w-full"
            height="120"
          />
          <p v-if="state && !state.equity_curve.length" class="text-gray-500 text-sm">
            No equity snapshots yet — they accrue as bots tick each day.
          </p>
        </section>
      </div>

      <!-- ══════════════ AI Engine (unchanged) ══════════════ -->
      <div v-else-if="activeTab === 'ai'" class="space-y-4">
        <h1 class="text-3xl font-extrabold">AI Engine</h1>
        <p class="text-sm text-gray-400">
          News sentiment analysis (VADER / FinBERT optional).
        </p>
        <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg text-gray-900">
          <SentimentEngine />
        </section>
      </div>

      <!-- ══════════════ Settings / Help placeholders ══════════════ -->
      <div v-else class="space-y-4">
        <h1 class="text-3xl font-extrabold">{{ activeLabel }}</h1>
        <section class="bg-gray-800/80 p-10 rounded-3xl ring-1 ring-gray-700/40 shadow-lg text-center">
          <i class="fas fa-hourglass-half text-3xl text-indigo-400 mb-3" />
          <p class="text-lg font-semibold text-gray-200">Coming soon</p>
          <p class="text-sm text-gray-400 mt-1">
            This section is a placeholder and is not yet implemented.
          </p>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  defineComponent,
  h,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch
} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Chart from 'chart.js/auto'
import SentimentEngine from '../components/SentimentEngine.vue'
import { fetchStrategies, type StrategyInfo } from '@/api/backtest'
import {
  PaperApiError,
  createPaperBot,
  deletePaperBot,
  fetchPaperState,
  fetchPaperTrades,
  resetPaperAccount,
  setPaperBotStatus,
  submitManualTrade,
  type BotStatus,
  type PaperState,
  type PaperTrade,
  type Side
} from '@/api/paper'

type TabId = 'overview' | 'trades' | 'performance' | 'ai' | 'settings' | 'help'

const tabs: { id: TabId; label: string; soon?: boolean }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'trades', label: 'Trades' },
  { id: 'performance', label: 'Performance' },
  { id: 'ai', label: 'AI Engine' },
  { id: 'settings', label: 'Settings', soon: true },
  { id: 'help', label: 'Help & Feedback', soon: true }
]

const POLL_MS = 15_000

const router = useRouter()
const route = useRoute()
const activeTab = ref<TabId>('overview')
const activeLabel = computed(() => tabs.find((t) => t.id === activeTab.value)?.label ?? '')
const isLiveTab = computed(() =>
  ['overview', 'trades', 'performance'].includes(activeTab.value)
)

const state = ref<PaperState | null>(null)
const trades = ref<PaperTrade[]>([])
const strategies = ref<StrategyInfo[]>([])
const loading = ref(false)
const busy = ref(false) // guards mutating actions (create/delete/trade/reset)
const error = ref('')
const lastUpdated = ref('')

const confirmingReset = ref(false)

const botForm = ref<{ symbol: string; strategy: string; allocated_cash: number }>({
  symbol: 'AAPL',
  strategy: 'sma_crossover',
  allocated_cash: 20_000
})
const botParams = ref<Record<string, number>>({})

const currentStrategy = computed(() =>
  strategies.value.find((s) => s.name === botForm.value.strategy)
)
watch(currentStrategy, (s) => {
  botParams.value = s ? { ...s.params } : {}
})

const tradeForm = ref<{ symbol: string; side: Side; notional_usd: number }>({
  symbol: 'BTCUSDT',
  side: 'buy',
  notional_usd: 1_000
})
const tradeMessage = ref('')
const tradeExecuted = ref(false)

const equityCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null

// ── Formatting helpers ───────────────────────────────────────────────
const usd = (v: number) =>
  `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const fmtQty = (v: number) =>
  v.toLocaleString(undefined, { maximumFractionDigits: 8 })
function sourceBadge(source: string): string {
  const base = 'px-1.5 py-0.5 text-[10px] rounded-full '
  return source === 'synthetic'
    ? base + 'bg-yellow-900/50 text-yellow-300'
    : base + 'bg-gray-700 text-gray-300'
}

// ── 401 handling ─────────────────────────────────────────────────────
function handleApiError(e: unknown): void {
  if (e instanceof PaperApiError && e.status === 401) {
    // Token expired / invalid — clear storage and bounce to login.
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_email')
    stopPolling()
    router.push({ name: 'login', query: { redirect: '/trade' } })
    return
  }
  error.value = e instanceof Error ? e.message : String(e)
}

// ── Data loading ─────────────────────────────────────────────────────
async function refresh(): Promise<void> {
  loading.value = true
  try {
    const [s, t] = await Promise.all([fetchPaperState(), fetchPaperTrades()])
    state.value = s
    trades.value = t
    lastUpdated.value = new Date().toLocaleTimeString()
    error.value = ''
    if (activeTab.value === 'performance') await drawEquity()
  } catch (e) {
    handleApiError(e)
  } finally {
    loading.value = false
  }
}

// ── Mutating actions ─────────────────────────────────────────────────
async function addBot(): Promise<void> {
  if (!botForm.value.symbol.trim()) return
  busy.value = true
  try {
    await createPaperBot({
      symbol: botForm.value.symbol.trim().toUpperCase(),
      strategy: botForm.value.strategy,
      params: { ...botParams.value },
      allocated_cash: botForm.value.allocated_cash
    })
    error.value = ''
    await refresh()
  } catch (e) {
    handleApiError(e)
  } finally {
    busy.value = false
  }
}

async function changeBotStatus(botId: number, status: BotStatus): Promise<void> {
  busy.value = true
  try {
    await setPaperBotStatus(botId, status)
    await refresh()
  } catch (e) {
    handleApiError(e)
  } finally {
    busy.value = false
  }
}

async function removeBot(botId: number): Promise<void> {
  busy.value = true
  try {
    const res = await deletePaperBot(botId)
    if (res.warning) {
      tradeExecuted.value = false
      tradeMessage.value = res.warning
    }
    await refresh()
  } catch (e) {
    handleApiError(e)
  } finally {
    busy.value = false
  }
}

async function submitTrade(): Promise<void> {
  if (!tradeForm.value.symbol.trim()) return
  busy.value = true
  tradeMessage.value = ''
  try {
    const res = await submitManualTrade({
      symbol: tradeForm.value.symbol.trim().toUpperCase(),
      side: tradeForm.value.side,
      notional_usd: tradeForm.value.notional_usd
    })
    if (res.executed) {
      tradeExecuted.value = true
      tradeMessage.value =
        `Filled ${res.side} ${fmtQty(res.qty)} ${res.symbol} @ ${usd(res.price)} ` +
        `(commission ${usd(res.commission)}, ${res.source})`
    } else {
      tradeExecuted.value = false
      tradeMessage.value = res.warning
    }
    error.value = ''
    await refresh()
  } catch (e) {
    handleApiError(e)
  } finally {
    busy.value = false
  }
}

async function doReset(): Promise<void> {
  busy.value = true
  try {
    await resetPaperAccount()
    confirmingReset.value = false
    tradeMessage.value = ''
    await refresh()
  } catch (e) {
    handleApiError(e)
  } finally {
    busy.value = false
  }
}

// ── Performance chart ────────────────────────────────────────────────
async function drawEquity(): Promise<void> {
  await nextTick()
  if (!equityCanvas.value || !state.value) return
  const curve = state.value.equity_curve
  chart?.destroy()
  chart = null
  if (!curve.length) return
  const invested = state.value.account.initial_cash
  chart = new Chart(equityCanvas.value, {
    type: 'line',
    data: {
      labels: curve.map((p) => p.date),
      datasets: [
        {
          label: 'Equity',
          data: curve.map((p) => p.equity),
          borderColor: '#818cf8',
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: 'Initial cash',
          data: curve.map(() => invested),
          borderColor: '#6b7280',
          pointRadius: 0,
          borderWidth: 1.5,
          borderDash: [6, 4]
        }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: '#d1d5db' } } },
      scales: {
        x: { ticks: { color: '#9ca3af', maxTicksLimit: 10 }, grid: { color: 'rgba(75,85,99,.2)' } },
        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(75,85,99,.2)' } }
      }
    }
  })
}

// Redraw when switching to the Performance tab.
watch(activeTab, (tab) => {
  if (tab === 'performance') drawEquity()
})

// ── Polling lifecycle ────────────────────────────────────────────────
function startPolling(): void {
  stopPolling()
  pollTimer = setInterval(() => {
    if (!busy.value) refresh()
  }, POLL_MS)
}
function stopPolling(): void {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  // Prefill the New-bot form symbol from ?symbol= (e.g. Screener "Bot" action).
  const q = route.query.symbol
  const prefill = Array.isArray(q) ? q[0] : q
  if (prefill && prefill.trim()) botForm.value.symbol = prefill.trim().toUpperCase()

  try {
    strategies.value = await fetchStrategies()
    if (
      strategies.value.length &&
      !strategies.value.find((s) => s.name === botForm.value.strategy)
    ) {
      botForm.value.strategy = strategies.value[0].name
    }
    botParams.value = { ...(currentStrategy.value?.params ?? {}) }
  } catch {
    // Strategy list is non-fatal; the dropdown just stays empty.
  }
  await refresh()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
  chart?.destroy()
  chart = null
})

// ── Small stat card, local to this view ──────────────────────────────
const StatCard = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
    positive: { type: Boolean, default: true },
    neutral: { type: Boolean, default: false }
  },
  setup(props) {
    return () =>
      h('div', { class: 'bg-gray-800/80 p-4 rounded-2xl ring-1 ring-gray-700/40' }, [
        h('p', { class: 'text-xs text-gray-400 uppercase tracking-wide' }, props.label),
        h(
          'p',
          {
            class: [
              'text-xl font-bold mt-1',
              props.neutral ? 'text-gray-200' : props.positive ? 'text-green-400' : 'text-red-400'
            ]
          },
          props.value
        )
      ])
  }
})
</script>

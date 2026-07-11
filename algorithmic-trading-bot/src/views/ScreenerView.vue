<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8 space-y-8">
    <!-- Header -->
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-4xl font-extrabold mb-2">TWSE Stock Screener</h1>
        <p class="text-gray-400 max-w-2xl">
          Ranks the curated Taiwan (TWSE) universe by a technicals-only quant score, best to worst —
          so you can pick what to analyze, backtest, or trade.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="data" class="text-xs text-gray-500 text-right leading-5">
          Generated {{ fmtTime(data.generated_at) }}
          <span
            class="ml-2 px-2 py-0.5 rounded-full text-[10px] align-middle"
            :class="data.cached
              ? 'bg-gray-700 text-gray-300'
              : 'bg-indigo-900/60 text-indigo-300'"
          >
            {{ data.cached ? 'cached' : 'fresh' }}
          </span>
        </span>
        <button
          type="button"
          :disabled="loading"
          class="px-5 py-2 text-sm rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 font-semibold shadow-lg transition-colors"
          @click="refresh"
        >
          {{ loading ? 'Scanning…' : 'Refresh' }}
        </button>
      </div>
    </header>

    <!-- Loading (cold scan) -->
    <section
      v-if="loading"
      class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg flex items-center gap-4"
    >
      <span class="h-6 w-6 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
      <div>
        <p class="font-semibold">Scanning {{ universeHint }} stocks…</p>
        <p class="text-sm text-gray-400">A cold scan fetches live prices for the whole universe — this can take 15–25 seconds.</p>
      </div>
    </section>

    <!-- Fetch error -->
    <p v-if="error" class="p-4 bg-red-900/40 border border-red-700 rounded-xl text-red-300">{{ error }}</p>

    <!-- Data warnings banner -->
    <div
      v-if="data && data.warnings.length"
      class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300 space-y-1"
    >
      <p class="font-semibold text-sm">Data warnings ({{ data.warnings.length }})</p>
      <p v-for="(w, i) in data.warnings" :key="i" class="text-sm">{{ w }}</p>
    </div>

    <template v-if="data">
      <!-- Filters -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg space-y-4">
        <!-- Sector chips -->
        <div class="space-y-2">
          <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Sectors</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="s in sectors"
              :key="s"
              type="button"
              class="px-3 py-1.5 text-xs rounded-full ring-1 transition-colors"
              :class="selectedSectors.has(s)
                ? 'bg-indigo-600 text-white ring-indigo-500'
                : 'bg-gray-900/60 text-gray-300 ring-gray-700 hover:bg-gray-700'"
              @click="toggleSector(s)"
            >
              {{ s }}
            </button>
            <button
              v-if="selectedSectors.size"
              type="button"
              class="px-3 py-1.5 text-xs rounded-full text-gray-400 hover:text-gray-200"
              @click="selectedSectors = new Set()"
            >
              clear
            </button>
          </div>
        </div>

        <div class="flex flex-wrap items-end gap-6">
          <!-- Verdict filter -->
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide">Verdict</label>
            <select
              v-model="verdictFilter"
              class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All</option>
              <option value="buyish">Buy-ish</option>
              <option value="hold">Hold</option>
              <option value="sellish">Sell-ish</option>
            </select>
          </div>

          <!-- RSI band -->
          <div class="space-y-1">
            <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide">RSI band</label>
            <select
              v-model="rsiBand"
              class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">Any</option>
              <option value="oversold">Oversold (&lt;30)</option>
              <option value="neutral">Neutral (30–70)</option>
              <option value="overbought">Overbought (&gt;70)</option>
            </select>
          </div>

          <!-- Uptrend toggle -->
          <label class="flex items-center gap-2 py-2 text-sm text-gray-400">
            <input v-model="onlyUptrend" type="checkbox" class="rounded" />
            Only uptrend
          </label>

          <!-- Search -->
          <div class="space-y-1 flex-1 min-w-[12rem]">
            <label class="block text-xs font-medium text-gray-500 uppercase tracking-wide">Search</label>
            <input
              v-model="search"
              placeholder="Symbol or name…"
              class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <p class="text-sm text-gray-500">
          Showing {{ filteredRows.length }} of {{ data.rows.length }} · universe {{ data.universe_size }} ·
          scanned {{ data.scanned }}<span v-if="data.errors.length"> · {{ data.errors.length }} errored</span>
        </p>
      </section>

      <!-- Ranked table -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-gray-400 text-left">
              <tr>
                <th class="py-2 pr-4">#</th>
                <th
                  v-for="col in columns"
                  :key="col.key"
                  class="py-2 pr-4 select-none"
                  :class="col.sortable ? 'cursor-pointer hover:text-gray-200' : ''"
                  @click="col.sortable && setSort(col.key)"
                >
                  {{ col.label }}
                  <span v-if="col.sortable && sortKey === col.key" class="text-indigo-400">
                    {{ sortDir === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th class="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, i) in filteredRows"
                :key="row.symbol"
                class="border-t border-gray-700/50 hover:bg-gray-900/40"
              >
                <td class="py-2 pr-4 text-gray-500">{{ i + 1 }}</td>
                <td class="py-2 pr-4 font-semibold">{{ row.symbol }}</td>
                <td class="py-2 pr-4">
                  {{ row.name }}
                  <span
                    v-if="isSynthetic(row)"
                    class="ml-1 px-1.5 py-0.5 text-[10px] rounded-full bg-yellow-900/50 text-yellow-300"
                    :title="row.warning ?? 'Synthetic / insufficient data'"
                  >
                    synthetic
                  </span>
                </td>
                <td class="py-2 pr-4 text-gray-400">{{ row.sector }}</td>
                <td class="py-2 pr-4">{{ fmtPrice(row.last_price) }}</td>
                <!-- Composite score bar -->
                <td class="py-2 pr-4">
                  <div v-if="row.score !== null" class="flex items-center gap-2">
                    <div class="w-20 h-2 rounded-full bg-black/40 overflow-hidden">
                      <div
                        class="h-full"
                        :class="row.score >= 0 ? 'bg-green-500' : 'bg-red-500'"
                        :style="{ width: `${Math.abs(row.score) * 100}%` }"
                      />
                    </div>
                    <span class="tabular-nums" :class="row.score >= 0 ? 'text-green-400' : 'text-red-400'">
                      {{ row.score.toFixed(2) }}
                    </span>
                  </div>
                  <span v-else class="text-gray-600">—</span>
                </td>
                <!-- Verdict badge -->
                <td class="py-2 pr-4">
                  <span class="px-2 py-0.5 text-[11px] font-semibold rounded-full" :class="verdictBadge(row.verdict)">
                    {{ verdictLabel(row.verdict) }}
                  </span>
                </td>
                <td class="py-2 pr-4">
                  <span v-if="row.rsi !== null" :class="rsiClass(row.rsi)">{{ row.rsi.toFixed(0) }}</span>
                  <span v-else class="text-gray-600">—</span>
                </td>
                <td class="py-2 pr-4">
                  <span :class="trendClass(row.trend)">{{ trendArrow(row.trend) }}</span>
                </td>
                <td class="py-2 pr-4">{{ fmtPct(row.momentum_1m) }}</td>
                <td class="py-2 pr-4">{{ fmtPct(row.momentum_3m) }}</td>
                <td class="py-2 pr-4 text-gray-300">{{ fmtPctPlain(row.volatility) }}</td>
                <td class="py-2 pr-4 text-red-400">{{ fmtPctPlain(row.max_drawdown) }}</td>
                <!-- Actions -->
                <td class="py-2">
                  <div class="flex items-center gap-1.5">
                    <RouterLink
                      :to="{ path: '/analysis', query: { symbol: row.symbol } }"
                      class="px-2 py-1 text-[11px] rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
                    >
                      Analyze
                    </RouterLink>
                    <RouterLink
                      :to="{ path: '/backtest', query: { symbol: row.symbol } }"
                      class="px-2 py-1 text-[11px] rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
                    >
                      Backtest
                    </RouterLink>
                    <RouterLink
                      :to="{ path: '/trade', query: { symbol: row.symbol } }"
                      class="px-2 py-1 text-[11px] rounded-lg bg-indigo-700/70 hover:bg-indigo-700 transition-colors"
                    >
                      Bot
                    </RouterLink>
                  </div>
                </td>
              </tr>
              <tr v-if="!filteredRows.length">
                <td colspan="15" class="py-6 text-center text-gray-500">No stocks match the current filters.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  fetchScreener,
  type ScreenerResponse,
  type ScreenerRow,
  type ScreenerTrend,
  type ScreenerVerdict
} from '@/api/screener'

const data = ref<ScreenerResponse | null>(null)
const loading = ref(false)
const error = ref('')

// ── Filters ──────────────────────────────────────────────────────────
const selectedSectors = ref<Set<string>>(new Set())
const verdictFilter = ref<'all' | 'buyish' | 'hold' | 'sellish'>('all')
const rsiBand = ref<'all' | 'oversold' | 'neutral' | 'overbought'>('all')
const onlyUptrend = ref(false)
const search = ref('')

// ── Sorting (score desc default) ─────────────────────────────────────
type SortKey =
  | 'symbol'
  | 'name'
  | 'sector'
  | 'last_price'
  | 'score'
  | 'rsi'
  | 'momentum_1m'
  | 'momentum_3m'
  | 'volatility'
  | 'max_drawdown'
const sortKey = ref<SortKey>('score')
const sortDir = ref<'asc' | 'desc'>('desc')

const columns: { key: SortKey; label: string; sortable: boolean }[] = [
  { key: 'symbol', label: 'Symbol', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'sector', label: 'Sector', sortable: true },
  { key: 'last_price', label: 'Price', sortable: true },
  { key: 'score', label: 'Score', sortable: true },
  { key: 'symbol', label: 'Verdict', sortable: false },
  { key: 'rsi', label: 'RSI', sortable: true },
  { key: 'symbol', label: 'Trend', sortable: false },
  { key: 'momentum_1m', label: '1M %', sortable: true },
  { key: 'momentum_3m', label: '3M %', sortable: true },
  { key: 'volatility', label: 'Vol', sortable: true },
  { key: 'max_drawdown', label: 'Max DD', sortable: true }
]

const universeHint = computed(() => data.value?.universe_size ?? 42)

const sectors = computed(() => {
  if (!data.value) return [] as string[]
  return Array.from(new Set(data.value.rows.map((r) => r.sector))).sort()
})

function isSynthetic(row: ScreenerRow): boolean {
  return row.score === null || row.source === 'synthetic'
}

function toggleSector(s: string): void {
  const next = new Set(selectedSectors.value)
  if (next.has(s)) next.delete(s)
  else next.add(s)
  selectedSectors.value = next
}

function setSort(key: SortKey): void {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    // Numeric columns default to desc (best first); text columns to asc.
    sortDir.value = key === 'symbol' || key === 'name' || key === 'sector' ? 'asc' : 'desc'
  }
}

// ── Filter + sort pipeline (client-side) ─────────────────────────────
const filteredRows = computed(() => {
  if (!data.value) return [] as ScreenerRow[]
  const q = search.value.trim().toLowerCase()

  const rows = data.value.rows.filter((r) => {
    if (selectedSectors.value.size && !selectedSectors.value.has(r.sector)) return false

    if (verdictFilter.value === 'buyish' && !['strong_buy', 'buy'].includes(r.verdict)) return false
    if (verdictFilter.value === 'hold' && r.verdict !== 'hold') return false
    if (verdictFilter.value === 'sellish' && !['strong_sell', 'sell'].includes(r.verdict)) return false

    if (onlyUptrend.value && r.trend !== 'up') return false

    if (rsiBand.value !== 'all') {
      if (r.rsi === null) return false
      if (rsiBand.value === 'oversold' && r.rsi >= 30) return false
      if (rsiBand.value === 'neutral' && (r.rsi < 30 || r.rsi > 70)) return false
      if (rsiBand.value === 'overbought' && r.rsi <= 70) return false
    }

    if (q && !r.symbol.toLowerCase().includes(q) && !r.name.toLowerCase().includes(q)) return false

    return true
  })

  const dir = sortDir.value === 'asc' ? 1 : -1
  const key = sortKey.value
  return rows.slice().sort((a, b) => {
    const av = a[key]
    const bv = b[key]
    // Synthetic / null values always sort to the bottom regardless of direction.
    const aNull = av === null || av === undefined
    const bNull = bv === null || bv === undefined
    if (aNull && bNull) return 0
    if (aNull) return 1
    if (bNull) return -1
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
    return String(av).localeCompare(String(bv)) * dir
  })
})

// ── Formatting / styling helpers ─────────────────────────────────────
function fmtTime(iso: string): string {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}
function fmtPrice(v: number | null): string {
  return v === null ? '—' : v.toLocaleString(undefined, { maximumFractionDigits: 2 })
}
function fmtPct(v: number | null): string {
  return v === null ? '—' : `${v >= 0 ? '+' : ''}${(v * 100).toFixed(1)}%`
}
function fmtPctPlain(v: number | null): string {
  return v === null ? '—' : `${(v * 100).toFixed(1)}%`
}

const VERDICT_LABELS: Record<ScreenerVerdict, string> = {
  strong_buy: 'Strong Buy',
  buy: 'Buy',
  hold: 'Hold',
  sell: 'Sell',
  strong_sell: 'Strong Sell',
  'n/a': 'N/A'
}
function verdictLabel(v: ScreenerVerdict): string {
  return VERDICT_LABELS[v] ?? v
}
function verdictBadge(v: ScreenerVerdict): string {
  switch (v) {
    case 'strong_buy':
      return 'bg-green-700 text-white'
    case 'buy':
      return 'bg-green-900/60 text-green-300'
    case 'sell':
      return 'bg-red-900/60 text-red-300'
    case 'strong_sell':
      return 'bg-red-700 text-white'
    case 'hold':
      return 'bg-gray-700 text-gray-200'
    default:
      return 'bg-yellow-900/50 text-yellow-300'
  }
}

function rsiClass(rsi: number): string {
  if (rsi < 30) return 'text-green-400 font-semibold'
  if (rsi > 70) return 'text-red-400 font-semibold'
  return 'text-gray-300'
}

function trendArrow(t: ScreenerTrend): string {
  return t === 'up' ? '↑' : t === 'down' ? '↓' : '→'
}
function trendClass(t: ScreenerTrend): string {
  return t === 'up' ? 'text-green-400' : t === 'down' ? 'text-red-400' : 'text-gray-500'
}

// ── Loading ──────────────────────────────────────────────────────────
async function load(refreshFlag: boolean): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    data.value = await fetchScreener('tw', 365, refreshFlag)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function refresh(): void {
  load(true)
}

onMounted(() => load(false))
</script>

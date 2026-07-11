<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8 space-y-8">
    <header>
      <h1 class="text-4xl font-extrabold mb-2">Strategy Backtest</h1>
      <p class="text-gray-400">
        Run a quantitative strategy over historical data and compare it against buy &amp; hold.
      </p>
    </header>

    <!-- Controls -->
    <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg space-y-4">
      <div class="flex flex-wrap items-end gap-6">
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Symbol</label>
          <input
            v-model="symbol"
            placeholder="AAPL, 2330, BTCUSDT…"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 uppercase"
            @keyup.enter="run"
          />
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Strategy</label>
          <select
            v-model="selectedStrategy"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option v-for="s in strategies" :key="s.name" :value="s.name">{{ s.label }}</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Period</label>
          <select
            v-model.number="days"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option :value="180">6 months</option>
            <option :value="365">1 year</option>
            <option :value="730">2 years</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Benchmark (optional)</label>
          <input
            v-model="benchmarkSymbol"
            placeholder="0050"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl w-32 focus:ring-indigo-500 focus:border-indigo-500 uppercase"
          />
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Initial Capital</label>
          <input
            v-model.number="initialCapital"
            type="number"
            min="100"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl w-36 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <button
          :disabled="loading || !symbol.trim()"
          class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl font-semibold shadow-lg transition-colors"
          @click="run"
        >
          {{ loading ? 'Running…' : 'Run Backtest' }}
        </button>
      </div>

      <!-- Strategy params -->
      <div v-if="currentStrategy && Object.keys(paramValues).length" class="flex flex-wrap items-end gap-4">
        <p class="text-sm text-gray-400 w-full">{{ currentStrategy.description }}</p>
        <div v-for="(v, key) in paramValues" :key="key" class="space-y-1">
          <label class="block text-xs font-medium text-gray-500">{{ key }}</label>
          <input
            v-model.number="paramValues[key]"
            type="number"
            step="any"
            class="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg w-28 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>
    </section>

    <p v-if="error" class="p-4 bg-red-900/40 border border-red-700 rounded-xl text-red-300">{{ error }}</p>
    <p v-if="result?.warning" class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300">
      {{ result.warning }}
    </p>
    <p
      v-if="result?.benchmark?.warning"
      class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300"
    >
      Benchmark {{ result.benchmark.symbol }}: {{ result.benchmark.warning }}
    </p>

    <template v-if="result">
      <!-- Metrics -->
      <section class="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <MetricCard label="Total Return" :value="pct(result.result.metrics.total_return)"
                    :positive="result.result.metrics.total_return >= 0" />
        <MetricCard label="CAGR" :value="pct(result.result.metrics.cagr)"
                    :positive="result.result.metrics.cagr >= 0" />
        <MetricCard label="Sharpe" :value="result.result.metrics.sharpe.toFixed(2)"
                    :positive="result.result.metrics.sharpe >= 0" />
        <MetricCard label="Max Drawdown" :value="pct(result.result.metrics.max_drawdown)" :positive="false" />
        <MetricCard label="Trades" :value="String(result.result.num_trades)" neutral />
        <MetricCard
          label="Win Rate"
          :value="result.result.win_rate === null ? '—' : pct(result.result.win_rate)"
          neutral
        />
      </section>

      <p class="text-sm text-gray-400">
        {{ result.symbol }} · {{ result.start }} → {{ result.end }} · {{ result.days }} bars ·
        data: {{ result.source }} · commission {{ result.commission_bps }} bps ·
        benchmark {{ result.benchmark.symbol }} (buy &amp; hold) return {{ pct(result.benchmark.metrics.total_return) }}
      </p>

      <!-- Equity curve -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
        <h2 class="text-xl font-bold mb-4">Equity Curve vs Buy &amp; Hold</h2>
        <canvas ref="equityCanvas" class="w-full" height="110" />
      </section>

      <!-- Trades -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
        <h2 class="text-xl font-bold mb-4">Trades ({{ result.result.trades.length }})</h2>
        <div class="overflow-x-auto max-h-80 overflow-y-auto">
          <table class="w-full text-sm">
            <thead class="text-gray-400 text-left sticky top-0 bg-gray-800">
              <tr><th class="py-2 pr-6">Date</th><th class="py-2 pr-6">Side</th><th class="py-2 pr-6">Price</th><th class="py-2">Return</th></tr>
            </thead>
            <tbody>
              <tr v-for="(t, i) in result.result.trades" :key="i" class="border-t border-gray-700/50">
                <td class="py-2 pr-6">{{ t.date }}</td>
                <td class="py-2 pr-6" :class="t.side === 'buy' ? 'text-green-400' : 'text-red-400'">
                  {{ t.side.toUpperCase() }}
                </td>
                <td class="py-2 pr-6">{{ t.price.toLocaleString() }}</td>
                <td class="py-2" :class="(t.return ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'">
                  {{ t.return !== undefined ? pct(t.return) : '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, defineComponent, h } from 'vue'
import { useRoute } from 'vue-router'
import Chart from 'chart.js/auto'
import { fetchStrategies, runBacktest, type BacktestResult, type StrategyInfo } from '@/api/backtest'

const route = useRoute()

const symbol = ref('AAPL')
const days = ref(365)
const initialCapital = ref(10000)
const benchmarkSymbol = ref('')
const strategies = ref<StrategyInfo[]>([])
const selectedStrategy = ref('sma_crossover')
const paramValues = ref<Record<string, number>>({})
const loading = ref(false)
const error = ref('')
const result = ref<BacktestResult | null>(null)
const equityCanvas = ref<HTMLCanvasElement | null>(null)

let chart: Chart | null = null

const currentStrategy = computed(() =>
  strategies.value.find((s) => s.name === selectedStrategy.value)
)

watch(currentStrategy, (s) => {
  paramValues.value = s ? { ...s.params } : {}
})

const pct = (v: number) => `${(v * 100).toFixed(2)}%`

function drawChart(r: BacktestResult) {
  if (!equityCanvas.value) return
  chart?.destroy()
  chart = new Chart(equityCanvas.value, {
    type: 'line',
    data: {
      labels: r.result.dates,
      datasets: [
        { label: r.strategy, data: r.result.equity_curve, borderColor: '#818cf8', pointRadius: 0, borderWidth: 2 },
        { label: `${r.benchmark.symbol} Buy & Hold`, data: r.benchmark.equity_curve, borderColor: '#6b7280', pointRadius: 0, borderWidth: 1.5, borderDash: [6, 4] }
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

async function run() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const r = await runBacktest({
      symbol: symbol.value.trim().toUpperCase(),
      strategy: selectedStrategy.value,
      params: paramValues.value,
      days: days.value,
      initial_capital: initialCapital.value,
      benchmark_symbol: benchmarkSymbol.value.trim().toUpperCase() || undefined
    })
    result.value = r
    await new Promise((resolve) => requestAnimationFrame(resolve))
    drawChart(r)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Prefill from ?symbol= (e.g. from the Screener "Backtest" action). No auto-run.
  const q = route.query.symbol
  const prefill = Array.isArray(q) ? q[0] : q
  if (prefill && prefill.trim()) symbol.value = prefill.trim().toUpperCase()

  try {
    strategies.value = await fetchStrategies()
    if (strategies.value.length && !strategies.value.find((s) => s.name === selectedStrategy.value)) {
      selectedStrategy.value = strategies.value[0].name
    }
    paramValues.value = { ...(currentStrategy.value?.params ?? {}) }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})

onBeforeUnmount(() => chart?.destroy())

/* Small metric card, local to this view */
const MetricCard = defineComponent({
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

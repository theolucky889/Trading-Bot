<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8 space-y-8">
    <header>
      <h1 class="text-4xl font-extrabold mb-2">Stock Analysis</h1>
      <p class="text-gray-400">
        Technical indicators + news sentiment, combined into a single verdict by the analysis harness.
      </p>
    </header>

    <!-- Controls -->
    <section class="flex flex-wrap items-end gap-6">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-gray-400">Symbol</label>
        <input
          v-model="symbol"
          placeholder="AAPL, 2330, BTCUSDT…"
          class="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 uppercase"
          @keyup.enter="analyze"
        />
      </div>
      <div class="space-y-1">
        <label class="block text-sm font-medium text-gray-400">Lookback</label>
        <select
          v-model.number="days"
          class="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option :value="180">6 months</option>
          <option :value="365">1 year</option>
          <option :value="730">2 years</option>
        </select>
      </div>
      <label class="flex items-center gap-2 py-3 text-sm text-gray-400">
        <input v-model="includeSentiment" type="checkbox" class="rounded" />
        Include news sentiment
      </label>
      <button
        :disabled="loading || !symbol.trim()"
        class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl font-semibold shadow-lg transition-colors"
        @click="analyze"
      >
        {{ loading ? 'Analyzing…' : 'Analyze' }}
      </button>
    </section>

    <p v-if="error" class="p-4 bg-red-900/40 border border-red-700 rounded-xl text-red-300">{{ error }}</p>
    <p v-if="result?.warning" class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300">
      {{ result.warning }}
    </p>

    <template v-if="result">
      <!-- Verdict -->
      <section class="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div :class="['p-6 rounded-3xl shadow-xl ring-1 ring-gray-700/40 lg:col-span-1', verdictBg]">
          <p class="text-sm uppercase tracking-widest opacity-80">Verdict</p>
          <p class="text-3xl font-extrabold mt-1">{{ verdictLabel }}</p>
          <p class="mt-2 text-sm opacity-80">Composite score {{ result.composite_score.toFixed(2) }}</p>
          <div class="mt-3 h-2 bg-black/30 rounded-full overflow-hidden">
            <div class="h-full bg-white/80" :style="{ width: `${((result.composite_score + 1) / 2) * 100}%` }" />
          </div>
        </div>
        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40">
          <p class="text-sm text-gray-400">Last Price ({{ result.source }})</p>
          <p class="text-2xl font-bold mt-1">{{ result.last_price.toLocaleString() }}</p>
          <p :class="result.change_30d >= 0 ? 'text-green-400' : 'text-red-400'" class="text-sm mt-1">
            {{ (result.change_30d * 100).toFixed(2) }}% / 30d
          </p>
        </div>
        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40">
          <p class="text-sm text-gray-400">Annualized Volatility</p>
          <p class="text-2xl font-bold mt-1">{{ (result.stats.volatility_annualized * 100).toFixed(1) }}%</p>
          <p class="text-sm text-gray-400 mt-1">Max drawdown {{ (result.stats.max_drawdown * 100).toFixed(1) }}%</p>
        </div>
        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40">
          <p class="text-sm text-gray-400">Scores</p>
          <p class="text-sm mt-2">Technical <span class="font-bold">{{ result.technical_score.toFixed(2) }}</span></p>
          <p class="text-sm mt-1">
            Sentiment
            <span class="font-bold">{{ result.sentiment ? result.sentiment.score.toFixed(2) : 'off' }}</span>
          </p>
        </div>
      </section>

      <!-- Price chart -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
        <h2 class="text-xl font-bold mb-4">{{ result.symbol }} — Close, SMA20, SMA50</h2>
        <canvas ref="priceCanvas" class="w-full" height="110" />
      </section>

      <!-- Signals -->
      <section class="grid lg:grid-cols-2 gap-8">
        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Technical Signals</h2>
          <ul class="space-y-3">
            <li
              v-for="s in result.signals"
              :key="s.name"
              class="flex items-start justify-between gap-4 p-3 bg-gray-900/60 rounded-xl"
            >
              <div>
                <p class="font-semibold">{{ s.indicator }}</p>
                <p class="text-sm text-gray-400">{{ s.reason }}</p>
              </div>
              <span
                :class="s.score > 0 ? 'text-green-400' : s.score < 0 ? 'text-red-400' : 'text-gray-400'"
                class="font-bold whitespace-nowrap"
              >
                {{ s.score > 0 ? '+' : '' }}{{ s.score.toFixed(1) }}
              </span>
            </li>
          </ul>
        </div>

        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">News Sentiment</h2>
          <template v-if="result.sentiment && result.sentiment.summary">
            <div class="flex gap-6 mb-4 text-sm">
              <span class="text-green-400">▲ {{ result.sentiment.summary.positive }} positive</span>
              <span class="text-gray-400">■ {{ result.sentiment.summary.neutral }} neutral</span>
              <span class="text-red-400">▼ {{ result.sentiment.summary.negative }} negative</span>
            </div>
            <ul class="space-y-2">
              <li v-for="a in result.sentiment.articles" :key="a.link" class="text-sm">
                <a :href="a.link" target="_blank" rel="noopener" class="hover:text-indigo-400">
                  <span
                    :class="a.label === 'positive' ? 'text-green-400' : a.label === 'negative' ? 'text-red-400' : 'text-gray-500'"
                  >●</span>
                  {{ a.title }}
                </a>
              </li>
            </ul>
          </template>
          <p v-else class="text-gray-400 text-sm">
            {{ result.sentiment?.warning ?? 'Sentiment disabled for this run.' }}
          </p>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import Chart from 'chart.js/auto'
import { fetchAnalysis, type AnalysisResult } from '@/api/analysis'

const route = useRoute()

const symbol = ref('AAPL')
const days = ref(365)
const includeSentiment = ref(true)
const loading = ref(false)
const error = ref('')
const result = ref<AnalysisResult | null>(null)
const priceCanvas = ref<HTMLCanvasElement | null>(null)

let chart: Chart | null = null

const VERDICT_LABELS: Record<string, string> = {
  strong_buy: 'Strong Buy',
  buy: 'Buy',
  hold: 'Hold',
  sell: 'Sell',
  strong_sell: 'Strong Sell'
}

const verdictLabel = computed(() => (result.value ? VERDICT_LABELS[result.value.verdict] : ''))
const verdictBg = computed(() => {
  switch (result.value?.verdict) {
    case 'strong_buy': return 'bg-green-700'
    case 'buy': return 'bg-green-800'
    case 'sell': return 'bg-red-800'
    case 'strong_sell': return 'bg-red-700'
    default: return 'bg-gray-700'
  }
})

function drawChart(r: AnalysisResult) {
  if (!priceCanvas.value) return
  chart?.destroy()
  chart = new Chart(priceCanvas.value, {
    type: 'line',
    data: {
      labels: r.chart.dates,
      datasets: [
        { label: 'Close', data: r.chart.closes, borderColor: '#818cf8', pointRadius: 0, borderWidth: 2 },
        { label: 'SMA20', data: r.chart.sma20, borderColor: '#34d399', pointRadius: 0, borderWidth: 1.5 },
        { label: 'SMA50', data: r.chart.sma50, borderColor: '#f59e0b', pointRadius: 0, borderWidth: 1.5 }
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

async function analyze() {
  if (!symbol.value.trim()) return
  loading.value = true
  error.value = ''
  try {
    const r = await fetchAnalysis(symbol.value.trim().toUpperCase(), days.value, includeSentiment.value)
    result.value = r
    // wait for <template v-if="result"> to render the canvas
    await new Promise((resolve) => requestAnimationFrame(resolve))
    drawChart(r)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

// Prefill from ?symbol= (e.g. from the Screener "Analyze" action) and auto-run.
onMounted(() => {
  const q = route.query.symbol
  const prefill = Array.isArray(q) ? q[0] : q
  if (prefill && prefill.trim()) {
    symbol.value = prefill.trim().toUpperCase()
    analyze()
  }
})

onBeforeUnmount(() => chart?.destroy())
</script>

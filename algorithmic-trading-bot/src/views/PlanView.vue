<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8 space-y-8">
    <header>
      <h1 class="text-4xl font-extrabold mb-2">Investment Plan</h1>
      <p class="text-gray-400">
        Pick a monthly budget, a time span, and the sectors you believe in — get a
        dollar-cost-averaging plan, its historical simulation, and a comparison against holding 0050.
      </p>
    </header>

    <!-- Form -->
    <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg space-y-6">
      <div class="flex flex-wrap items-end gap-6">
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Monthly Budget</label>
          <input
            v-model.number="monthlyBudget"
            type="number"
            min="1"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl w-40 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Time Span</label>
          <select
            v-model.number="months"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option :value="12">1 year</option>
            <option :value="24">2 years</option>
            <option :value="36">3 years</option>
            <option :value="60">5 years</option>
          </select>
        </div>
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Benchmark</label>
          <input
            v-model="benchmark"
            class="px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl w-28 focus:ring-indigo-500 focus:border-indigo-500 uppercase"
          />
        </div>
        <button
          :disabled="loading || !selectedSectors.length || monthlyBudget <= 0"
          class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-xl font-semibold shadow-lg transition-colors"
          @click="run"
        >
          {{ loading ? 'Building…' : 'Build Plan' }}
        </button>
      </div>

      <!-- Sector picker -->
      <div>
        <p class="text-sm font-medium text-gray-400 mb-3">Sectors ({{ selectedSectors.length }} selected)</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <label
            v-for="s in sectors"
            :key="s.id"
            :class="[
              'p-4 rounded-xl border cursor-pointer transition-colors',
              selectedSectors.includes(s.id)
                ? 'border-indigo-500 bg-indigo-900/30'
                : 'border-gray-700 bg-gray-900/60 hover:border-gray-500'
            ]"
          >
            <input v-model="selectedSectors" type="checkbox" :value="s.id" class="hidden" />
            <p class="font-semibold">
              {{ s.label }}
              <span class="text-xs text-gray-500 ml-1">{{ s.market }}</span>
            </p>
            <p class="text-xs text-gray-400 mt-1">
              {{ s.tickers.map((t) => t.name).join(' · ') }}
            </p>
          </label>
        </div>
      </div>
    </section>

    <p v-if="error" class="p-4 bg-red-900/40 border border-red-700 rounded-xl text-red-300">{{ error }}</p>
    <div v-if="result?.warnings.length" class="p-4 bg-yellow-900/40 border border-yellow-700 rounded-xl text-yellow-300 space-y-1">
      <p v-for="(w, i) in result.warnings" :key="i" class="text-sm">{{ w }}</p>
    </div>

    <template v-if="result">
      <!-- Summary -->
      <section class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div class="bg-gray-800/80 p-4 rounded-2xl ring-1 ring-gray-700/40">
          <p class="text-xs text-gray-400 uppercase">Invested</p>
          <p class="text-xl font-bold mt-1">{{ money(result.simulation.summary.invested) }}</p>
          <p class="text-xs text-gray-500">{{ result.simulation.summary.months_simulated }} months</p>
        </div>
        <div class="bg-gray-800/80 p-4 rounded-2xl ring-1 ring-gray-700/40">
          <p class="text-xs text-gray-400 uppercase">Final Value</p>
          <p class="text-xl font-bold mt-1">{{ money(result.simulation.summary.final_value) }}</p>
        </div>
        <div class="bg-gray-800/80 p-4 rounded-2xl ring-1 ring-gray-700/40">
          <p class="text-xs text-gray-400 uppercase">Plan Return</p>
          <p class="text-xl font-bold mt-1" :class="pctColor(result.simulation.summary.total_return)">
            {{ pct(result.simulation.summary.total_return) }}
          </p>
        </div>
        <div class="bg-gray-800/80 p-4 rounded-2xl ring-1 ring-gray-700/40">
          <p class="text-xs text-gray-400 uppercase">{{ result.benchmark }} DCA Return</p>
          <p class="text-xl font-bold mt-1" :class="pctColor(result.simulation.summary.benchmark_return)">
            {{ pct(result.simulation.summary.benchmark_return) }}
          </p>
        </div>
        <div
          class="p-4 rounded-2xl ring-1 ring-gray-700/40"
          :class="beatBenchmark ? 'bg-green-900/40' : 'bg-red-900/30'"
        >
          <p class="text-xs text-gray-400 uppercase">vs {{ result.benchmark }}</p>
          <p class="text-xl font-bold mt-1" :class="beatBenchmark ? 'text-green-400' : 'text-red-400'">
            {{ beatBenchmark ? 'Ahead' : 'Behind' }}
            {{ pct(Math.abs(result.simulation.summary.total_return - result.simulation.summary.benchmark_return)) }}
          </p>
          <p class="text-xs text-gray-500">historical simulation</p>
        </div>
      </section>

      <!-- Growth chart -->
      <section class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
        <h2 class="text-xl font-bold mb-4">
          Plan vs {{ result.benchmark }} — same {{ money(result.monthly_budget) }}/month
        </h2>
        <canvas ref="growthCanvas" class="w-full" height="110" />
      </section>

      <!-- Allocation + projection -->
      <section class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Monthly Allocation</h2>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="text-gray-400 text-left">
                <tr>
                  <th class="py-2 pr-4">Holding</th>
                  <th class="py-2 pr-4">Sector</th>
                  <th class="py-2 pr-4">Weight</th>
                  <th class="py-2 pr-4">Per Month</th>
                  <th class="py-2">Simulated Value</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in result.allocation" :key="a.symbol" class="border-t border-gray-700/50">
                  <td class="py-2 pr-4 font-semibold">{{ a.symbol }} <span class="text-gray-400 font-normal">{{ a.name }}</span></td>
                  <td class="py-2 pr-4 text-gray-400">{{ a.sector_label }}</td>
                  <td class="py-2 pr-4">{{ (a.weight * 100).toFixed(1) }}%</td>
                  <td class="py-2 pr-4">{{ money(a.monthly_amount) }}</td>
                  <td class="py-2">{{ money(a.final_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-xl font-bold mb-4">Projection ({{ result.projection.months }} months ahead)</h2>
          <ul class="space-y-3 text-sm">
            <li class="flex justify-between"><span class="text-gray-400">You would invest</span><span class="font-bold">{{ money(result.projection.invested) }}</span></li>
            <li class="flex justify-between"><span class="text-gray-400">Expected</span><span class="font-bold">{{ money(result.projection.expected) }}</span></li>
            <li class="flex justify-between"><span class="text-green-400">Optimistic (+1σ)</span><span class="font-bold text-green-400">{{ money(result.projection.optimistic) }}</span></li>
            <li class="flex justify-between"><span class="text-red-400">Pessimistic (−1σ)</span><span class="font-bold text-red-400">{{ money(result.projection.pessimistic) }}</span></li>
          </ul>
          <p class="text-xs text-gray-500 mt-4">{{ result.projection.note }}</p>
        </div>
      </section>

      <p class="text-xs text-gray-500 border-t border-gray-700/50 pt-4">{{ result.disclaimer }}</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import Chart from 'chart.js/auto'
import { buildPlan, fetchSectors, type PlanResult, type Sector } from '@/api/plan'

const sectors = ref<Sector[]>([])
const selectedSectors = ref<string[]>(['tw_semiconductors', 'tw_etf'])
const monthlyBudget = ref(10000)
const months = ref(24)
const benchmark = ref('0050')
const loading = ref(false)
const error = ref('')
const result = ref<PlanResult | null>(null)
const growthCanvas = ref<HTMLCanvasElement | null>(null)

let chart: Chart | null = null

const beatBenchmark = computed(
  () =>
    !!result.value &&
    result.value.simulation.summary.total_return >= result.value.simulation.summary.benchmark_return
)

const money = (v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })
const pct = (v: number) => `${(v * 100).toFixed(2)}%`
const pctColor = (v: number) => (v >= 0 ? 'text-green-400' : 'text-red-400')

function drawChart(r: PlanResult) {
  if (!growthCanvas.value) return
  chart?.destroy()
  chart = new Chart(growthCanvas.value, {
    type: 'line',
    data: {
      labels: r.simulation.month_labels,
      datasets: [
        { label: 'Your plan', data: r.simulation.portfolio_value, borderColor: '#818cf8', pointRadius: 0, borderWidth: 2, fill: false },
        { label: `${r.benchmark} DCA`, data: r.simulation.benchmark_value, borderColor: '#6b7280', pointRadius: 0, borderWidth: 1.5, borderDash: [6, 4] },
        { label: 'Invested', data: r.simulation.invested, borderColor: '#374151', pointRadius: 0, borderWidth: 1 }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: '#d1d5db' } } },
      scales: {
        x: { ticks: { color: '#9ca3af', maxTicksLimit: 12 }, grid: { color: 'rgba(75,85,99,.2)' } },
        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(75,85,99,.2)' } }
      }
    }
  })
}

async function run() {
  loading.value = true
  error.value = ''
  try {
    const r = await buildPlan({
      monthly_budget: monthlyBudget.value,
      months: months.value,
      sectors: selectedSectors.value,
      benchmark: benchmark.value.trim().toUpperCase() || '0050'
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
  try {
    sectors.value = await fetchSectors()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
})

onBeforeUnmount(() => chart?.destroy())
</script>

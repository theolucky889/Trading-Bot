<template>
  <div class="flex min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 font-inter">
    <!-- ░░░ Sidebar ░░░ -->
    <aside class="w-72 bg-gradient-to-b from-gray-800 to-gray-900 p-6 flex flex-col justify-between shadow-xl rounded-r-3xl">
      <nav>
        <ul class="space-y-3">
          <li v-for="item in menuItems" :key="item.name">
            <a
              href="#"
              class="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors group"
            >
              <i class="fas fa-circle text-xs group-hover:text-indigo-400" />
              <span class="tracking-wide">{{ item.name }}</span>
            </a>
          </li>
        </ul>
      </nav>
      <button
        v-tooltip="'Create a new order'"
        class="flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-lg transition-colors"
      >
        <i class="fas fa-plus" /> <span>New Order</span>
      </button>
    </aside>

    <!-- ░░░ Main Content ░░░ -->
    <main class="flex-1 p-8 space-y-10 overflow-y-auto">
      <h1 class="text-4xl font-extrabold mb-2">Trading Bot Dashboard</h1>

      <!-- Balance Widget -->
      <section class="bg-gray-900/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-xl">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
          <BalanceCard
            label="Total Assets"
            :value="200000"
            icon="fas fa-coins"
            color="text-indigo-400"
          />
          <BalanceCard
            label="Debt"
            :value="50000"
            icon="fas fa-hand-holding-usd"
            color="text-red-400"
          />
          <BalanceCard
            label="Net Assets"
            :value="150000"
            icon="fas fa-piggy-bank"
            color="text-green-400"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ProgressBar label="Cash"  :percent="60" bar-color="bg-green-500"  :value="100000" />
          <ProgressBar label="Stock" :percent="70" bar-color="bg-blue-500"   :value="100000" />
        </div>
      </section>

      <!-- Controls -->
      <section class="flex flex-wrap items-end gap-6">
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Select Category</label>
          <select
            v-model="selectedCategory"
            class="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="us-stocks">US Stocks</option>
            <option value="taiwan-stocks">Taiwan Stocks</option>
            <option value="crypto">Crypto</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Select Stocks (Compare)</label>
          <select
            v-model="selectedStocks"
            multiple
            class="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option v-for="s in availableStocks" :key="s.value" :value="s.value">
              {{ s.label }}
            </option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-400">Select Graph Type</label>
          <select
            v-model="selectedGraph"
            class="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="line">Line</option>
            <option value="bar">Bar</option>
          </select>
        </div>
      </section>

      <!-- Charts -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-10">
        <div v-for="stock in selectedStocks" :key="stock" class="space-y-10">
          <div class="bg-gray-800/80 p-6 rounded-3xl shadow-lg ring-1 ring-gray-700/40">
            <h2 class="text-xl font-bold mb-4">{{ stock }} Stock Price</h2>
            <canvas :id="stock + selectedGraph + 'StockPriceChart'" class="h-72" />
          </div>

          <div class="bg-gray-800/80 p-6 rounded-3xl shadow-lg ring-1 ring-gray-700/40">
            <h2 class="text-xl font-bold mb-4">Trade Volume &amp; Return/Loss</h2>
            <canvas :id="stock + 'TradeVolumeChart'" class="h-56 mb-8" />
            <canvas :id="stock + 'ReturnLossChart'" class="h-56" />
          </div>
        </div>
      </section>

      <!-- News + CTA -->
      <section class="grid lg:grid-cols-3 gap-8">
        <div class="lg:col-span-2 bg-gray-800/80 p-6 rounded-3xl ring-1 ring-gray-700/40 shadow-lg">
          <h2 class="text-2xl font-bold mb-4">Latest News</h2>
          <ul class="space-y-2 list-disc list-inside text-gray-300">
            <li>AlgoHouse raises $10M in Series A funding</li>
            <li>AlgoHouse bot helps investors make better decisions</li>
            <li>AlgoHouse introduces new features for users</li>
          </ul>
        </div>
        <div class="flex items-end justify-end">
          <button class="px-6 py-4 bg-green-600 hover:bg-green-700 rounded-2xl font-semibold shadow-lg transition-colors">
            Start Trading
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { updateCharts } from '@/chartManager.js'
import BalanceCard from '@/components/BalanceCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'

/* ── reactive state ───────────────────────────────*/
const selectedCategory = ref('us-stocks')
const selectedGraph    = ref('line')
const selectedStocks   = ref(['AAPL'])

/* ── static lists ────────────────────────────────*/
const stockLists = {
  'us-stocks': [
    { value: 'AAPL',  label: 'Apple (AAPL)' },
    { value: 'TSLA',  label: 'Tesla (TSLA)' },
    { value: 'AMZN',  label: 'Amazon (AMZN)' },
    { value: 'GOOGL', label: 'Google (GOOGL)' }
  ],
  'taiwan-stocks': [
    { value: '2330', label: 'TSMC (2330)' },
    { value: '2303', label: 'UMC (2303)' },
    { value: '0050', label: 'Yuanta 50 ETF (0050)' }
  ],
  crypto: [
    { value: 'BTCUSDT', label: 'Bitcoin (BTC)' },
    { value: 'ETHUSDT', label: 'Ethereum (ETH)' },
    { value: 'BNBUSDT', label: 'BNB (BNB)' }
  ]
}

const availableStocks = computed(() => stockLists[selectedCategory.value] ?? [])

/* ── sync selection on category change ───────────*/
watch(
  selectedCategory,
  () => {
    if (!availableStocks.value.find(s => selectedStocks.value.includes(s.value))) {
      selectedStocks.value = [availableStocks.value[0]?.value]
    }
  },
  { immediate: true }
)

/* ── redraw charts on any change ────────────────*/
watch(
  () => ({
    g: selectedGraph.value,
    c: selectedCategory.value,
    s: [...selectedStocks.value]
  }),
  ({ g, c, s }) => updateCharts(s, c, g),
  { flush: 'post' }
)

/* ── initial draw ───────────────────────────────*/
onMounted(() => {
  updateCharts(selectedStocks.value, selectedCategory.value, selectedGraph.value)
})

/* ── sidebar menu items ─────────────────────────*/
const menuItems = ref([
  { name: 'Dashboard' },
  { name: 'Trade' },
  { name: 'Settings' },
  { name: 'About' },
  { name: 'Login' }
])
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
</style>
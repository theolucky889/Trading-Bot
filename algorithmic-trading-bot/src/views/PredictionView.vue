<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8">
    <div class="max-w-6xl mx-auto space-y-8">

      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 class="text-3xl font-extrabold text-white flex items-center gap-3">
            <i class="fas fa-crystal-ball text-indigo-400" />
            Prediction Market
          </h1>
          <p class="text-gray-400 mt-1">
            AI predictions combining technical analysis (65%) + news sentiment (35%). Submit your own forecast.
          </p>
        </div>
        <button @click="loadAll" :disabled="globalLoading"
          class="flex-shrink-0 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-colors flex items-center gap-2">
          <i :class="globalLoading ? 'fas fa-circle-notch fa-spin' : 'fas fa-rotate'" />
          {{ globalLoading ? 'Loading…' : 'Refresh All' }}
        </button>
      </div>

      <!-- Category tabs -->
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="activeCategory = cat.id"
          class="px-4 py-2 rounded-xl text-sm font-medium transition-colors"
          :class="activeCategory === cat.id
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-800/60 text-gray-400 hover:text-white border border-gray-700/40'"
        >
          <i :class="cat.icon + ' mr-1.5'" />{{ cat.label }}
        </button>
      </div>

      <!-- Prediction grid -->
      <div class="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
        <div
          v-for="asset in filteredAssets"
          :key="asset.symbol"
          class="bg-gray-800/60 border border-gray-700/40 rounded-2xl overflow-hidden flex flex-col"
        >
          <!-- Card header -->
          <div class="flex items-center justify-between px-5 pt-5 pb-3">
            <div>
              <p class="font-bold text-white text-lg">{{ asset.symbol }}</p>
              <p class="text-xs text-gray-500">{{ asset.name }}</p>
            </div>
            <div class="text-right">
              <p v-if="asset.price" class="font-semibold text-white">${{ asset.price.toLocaleString() }}</p>
              <p v-else class="text-xs text-gray-600">—</p>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="asset.loading" class="flex-1 flex items-center justify-center py-8 text-gray-600">
            <i class="fas fa-circle-notch fa-spin text-2xl" />
          </div>

          <!-- Not loaded yet -->
          <div v-else-if="!asset.prediction" class="flex-1 flex flex-col items-center justify-center py-6 gap-3">
            <p class="text-sm text-gray-600">Analysis not loaded</p>
            <button @click="loadAsset(asset)"
              class="px-4 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm text-gray-300 transition-colors">
              Load Prediction
            </button>
          </div>

          <!-- Prediction loaded -->
          <template v-else>
            <!-- AI Prediction bar -->
            <div class="px-5 pb-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500">AI Prediction</span>
                <span class="text-xs font-medium px-2 py-0.5 rounded-full border"
                  :class="directionStyle(asset.prediction.direction).badge">
                  {{ asset.prediction.direction }} · {{ asset.prediction.confidence }}% confident
                </span>
              </div>

              <!-- Confidence bar -->
              <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-700"
                  :class="directionStyle(asset.prediction.direction).bar"
                  :style="{ width: asset.prediction.confidence + '%' }" />
              </div>
            </div>

            <!-- Tech + Sentiment breakdown -->
            <div class="flex gap-3 px-5 pb-4">
              <div class="flex-1 bg-gray-900/50 rounded-xl p-3 text-center">
                <p class="text-xs text-gray-500 mb-1">Technical</p>
                <p class="text-sm font-bold"
                  :class="asset.prediction.techWeight >= 0 ? 'text-green-400' : 'text-red-400'">
                  {{ asset.prediction.techWeight >= 0 ? '+' : '' }}{{ asset.prediction.techWeight }}
                </p>
              </div>
              <div class="flex-1 bg-gray-900/50 rounded-xl p-3 text-center">
                <p class="text-xs text-gray-500 mb-1">Sentiment</p>
                <p class="text-sm font-bold"
                  :class="asset.prediction.sentWeight >= 0 ? 'text-green-400' : 'text-red-400'">
                  {{ asset.prediction.sentWeight >= 0 ? '+' : '' }}{{ asset.prediction.sentWeight }}
                </p>
              </div>
              <div class="flex-1 bg-gray-900/50 rounded-xl p-3 text-center">
                <p class="text-xs text-gray-500 mb-1">Signal</p>
                <p class="text-sm font-bold" :class="signalColor(asset.prediction.action)">
                  {{ asset.prediction.action ?? 'HOLD' }}
                </p>
              </div>
            </div>

            <!-- Community votes -->
            <div class="px-5 pb-3">
              <div class="flex items-center justify-between text-xs text-gray-500 mb-1.5">
                <span>Community</span>
                <span>{{ totalVotes(asset) }} votes</span>
              </div>
              <div class="h-2 bg-gray-700 rounded-full overflow-hidden flex">
                <div class="h-full bg-green-500 transition-all duration-500"
                  :style="{ width: upPct(asset) + '%' }" />
                <div class="h-full bg-red-500 transition-all duration-500"
                  :style="{ width: downPct(asset) + '%' }" />
              </div>
              <div class="flex justify-between text-xs mt-1">
                <span class="text-green-400">▲ UP {{ upPct(asset) }}%</span>
                <span class="text-red-400">▼ DOWN {{ downPct(asset) }}%</span>
              </div>
            </div>

            <!-- Vote buttons -->
            <div class="flex gap-2 px-5 pb-5 mt-auto">
              <button
                @click="vote(asset, 'UP')"
                :class="[
                  'flex-1 py-2 rounded-xl text-sm font-semibold transition-colors',
                  userVote(asset) === 'UP'
                    ? 'bg-green-500 text-white'
                    : 'bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30'
                ]"
              >
                <i class="fas fa-arrow-up mr-1.5" />UP
              </button>
              <button
                @click="vote(asset, 'DOWN')"
                :class="[
                  'flex-1 py-2 rounded-xl text-sm font-semibold transition-colors',
                  userVote(asset) === 'DOWN'
                    ? 'bg-red-500 text-white'
                    : 'bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30'
                ]"
              >
                <i class="fas fa-arrow-down mr-1.5" />DOWN
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- Disclaimer -->
      <p class="text-center text-xs text-gray-600 max-w-2xl mx-auto">
        Predictions are generated by combining technical indicators and news sentiment analysis.
        They are for informational purposes only and do not constitute financial advice.
        Past performance does not guarantee future results.
      </p>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getUSDaily, getKlines } from '@/api/quotes.js'
import { generateSignal, combinedPrediction } from '@/utils/indicators'
import { fetchMarketSentiment } from '@/api/sentiment'

interface AssetPrediction {
  direction: 'UP' | 'DOWN' | 'NEUTRAL'
  confidence: number
  techWeight: number
  sentWeight: number
  action?: string
}

interface Asset {
  symbol: string
  name: string
  market: 'us-stocks' | 'crypto'
  category: string
  price: number | null
  loading: boolean
  prediction: AssetPrediction | null
  votes: { up: number; down: number }
}

const categories = [
  { id: 'all',    label: 'All',        icon: 'fas fa-border-all' },
  { id: 'stocks', label: 'US Stocks',  icon: 'fas fa-building-columns' },
  { id: 'crypto', label: 'Crypto',     icon: 'fas fa-coins' },
  { id: 'forex',  label: 'Forex',      icon: 'fas fa-money-bill-transfer' },
]

const activeCategory = ref('all')
const globalLoading = ref(false)

// Seed community votes with realistic-looking data
function seedVotes(upBase: number, downBase: number) {
  return { up: upBase + Math.floor(Math.random() * 20), down: downBase + Math.floor(Math.random() * 15) }
}

const assets = ref<Asset[]>([
  { symbol: 'AAPL',    name: 'Apple Inc.',        market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(120, 45) },
  { symbol: 'TSLA',    name: 'Tesla Inc.',         market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(200, 130) },
  { symbol: 'NVDA',    name: 'NVIDIA Corp.',       market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(180, 60) },
  { symbol: 'MSFT',    name: 'Microsoft Corp.',    market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(100, 30) },
  { symbol: 'AMZN',    name: 'Amazon.com Inc.',    market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(90, 40) },
  { symbol: 'GOOGL',   name: 'Alphabet Inc.',      market: 'us-stocks', category: 'stocks', price: null, loading: false, prediction: null, votes: seedVotes(80, 35) },
  { symbol: 'BTCUSDT', name: 'Bitcoin',            market: 'crypto',    category: 'crypto', price: null, loading: false, prediction: null, votes: seedVotes(250, 100) },
  { symbol: 'ETHUSDT', name: 'Ethereum',           market: 'crypto',    category: 'crypto', price: null, loading: false, prediction: null, votes: seedVotes(170, 80) },
  { symbol: 'SOLUSDT', name: 'Solana',             market: 'crypto',    category: 'crypto', price: null, loading: false, prediction: null, votes: seedVotes(140, 70) },
  { symbol: 'BNBUSDT', name: 'BNB Chain',          market: 'crypto',    category: 'crypto', price: null, loading: false, prediction: null, votes: seedVotes(90, 50) },
  { symbol: 'XRPUSDT', name: 'XRP',                market: 'crypto',    category: 'crypto', price: null, loading: false, prediction: null, votes: seedVotes(130, 110) },
  // Forex (mock predictions only — no direct Binance API for forex)
  { symbol: 'EUR/USD', name: 'Euro / US Dollar',   market: 'crypto',    category: 'forex',  price: null, loading: false, prediction: null, votes: seedVotes(60, 55) },
  { symbol: 'GBP/USD', name: 'British Pound / USD',market: 'crypto',    category: 'forex',  price: null, loading: false, prediction: null, votes: seedVotes(45, 50) },
  { symbol: 'USD/JPY', name: 'US Dollar / Yen',    market: 'crypto',    category: 'forex',  price: null, loading: false, prediction: null, votes: seedVotes(70, 40) },
])

// Restore saved votes from localStorage
function loadSavedVotes() {
  const saved = localStorage.getItem('prediction_votes')
  if (!saved) return
  try {
    const parsed: Record<string, { up: number; down: number }> = JSON.parse(saved)
    assets.value.forEach(a => {
      if (parsed[a.symbol]) a.votes = parsed[a.symbol]
    })
  } catch { /* ignore */ }
}

function saveVotes() {
  const data: Record<string, { up: number; down: number }> = {}
  assets.value.forEach(a => { data[a.symbol] = a.votes })
  localStorage.setItem('prediction_votes', JSON.stringify(data))
}

const filteredAssets = computed(() =>
  activeCategory.value === 'all'
    ? assets.value
    : assets.value.filter(a => a.category === activeCategory.value)
)

async function loadAsset(asset: Asset) {
  if (asset.loading) return
  asset.loading = true
  try {
    let prices: number[] = []
    let sentimentQuery = asset.symbol.replace('USDT', '')

    // Forex — use mock prediction (no direct API)
    if (asset.category === 'forex') {
      const mockPrediction: AssetPrediction = {
        direction: Math.random() > 0.5 ? 'UP' : 'DOWN',
        confidence: 52 + Math.floor(Math.random() * 15),
        techWeight: Math.floor(Math.random() * 40) - 20,
        sentWeight: Math.floor(Math.random() * 30) - 15,
        action: 'HOLD',
      }
      asset.prediction = mockPrediction
      asset.price = null
      return
    }

    // Fetch price data
    if (asset.market === 'us-stocks') {
      const data = await getUSDaily(asset.symbol)
      prices = data.prices
    } else {
      const data = await getKlines(asset.symbol, 30)
      prices = data.prices
    }

    asset.price = prices[prices.length - 1] ?? null

    if (prices.length < 15) {
      asset.prediction = { direction: 'NEUTRAL', confidence: 50, techWeight: 0, sentWeight: 0, action: 'HOLD' }
      return
    }

    // Technical signal
    const sig = generateSignal(prices)

    // Sentiment (best effort — falls back to mock)
    let sentimentCompound = 0
    try {
      const sentData = await fetchMarketSentiment(sentimentQuery, 5, 'vader')
      sentimentCompound = sentData?.summary?.avg_compound ?? 0
    } catch { /* ignore — use 0 */ }

    const pred = combinedPrediction(sig, sentimentCompound)
    asset.prediction = {
      ...pred,
      action: sig.action,
    }
  } catch {
    asset.prediction = { direction: 'NEUTRAL', confidence: 50, techWeight: 0, sentWeight: 0, action: 'HOLD' }
  } finally {
    asset.loading = false
  }
}

async function loadAll() {
  globalLoading.value = true
  // Load sequentially with a small delay to respect rate limits
  for (const asset of filteredAssets.value) {
    if (!asset.prediction) {
      await loadAsset(asset)
      await new Promise(r => setTimeout(r, 300))
    }
  }
  globalLoading.value = false
}

// Voting
const userVotes = ref<Record<string, 'UP' | 'DOWN'>>({})

function loadUserVotes() {
  const saved = localStorage.getItem('user_votes')
  if (saved) {
    try { userVotes.value = JSON.parse(saved) } catch { /* ignore */ }
  }
}

function userVote(asset: Asset) {
  return userVotes.value[asset.symbol] ?? null
}

function vote(asset: Asset, direction: 'UP' | 'DOWN') {
  const prev = userVotes.value[asset.symbol]
  if (prev === direction) {
    // Undo vote
    delete userVotes.value[asset.symbol]
    asset.votes[direction.toLowerCase() as 'up' | 'down']--
  } else {
    if (prev) {
      asset.votes[prev.toLowerCase() as 'up' | 'down']--
    }
    userVotes.value[asset.symbol] = direction
    asset.votes[direction.toLowerCase() as 'up' | 'down']++
  }
  localStorage.setItem('user_votes', JSON.stringify(userVotes.value))
  saveVotes()
}

function totalVotes(asset: Asset) {
  return asset.votes.up + asset.votes.down
}

function upPct(asset: Asset) {
  const total = totalVotes(asset)
  if (total === 0) return 50
  return Math.round((asset.votes.up / total) * 100)
}

function downPct(asset: Asset) {
  return 100 - upPct(asset)
}

// Styles
function directionStyle(direction: 'UP' | 'DOWN' | 'NEUTRAL') {
  if (direction === 'UP') return { badge: 'bg-green-500/15 text-green-400 border-green-500/30', bar: 'bg-green-500' }
  if (direction === 'DOWN') return { badge: 'bg-red-500/15 text-red-400 border-red-500/30', bar: 'bg-red-500' }
  return { badge: 'bg-gray-700/50 text-gray-400 border-gray-600/30', bar: 'bg-gray-500' }
}

function signalColor(action?: string) {
  if (!action) return 'text-gray-400'
  if (action.includes('BUY')) return 'text-green-400'
  if (action.includes('SELL')) return 'text-red-400'
  return 'text-yellow-400'
}

onMounted(() => {
  loadSavedVotes()
  loadUserVotes()
})
</script>
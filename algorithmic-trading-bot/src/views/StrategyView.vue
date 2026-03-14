<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8">
    <div class="max-w-5xl mx-auto space-y-8">

      <!-- Header -->
      <div>
        <h1 class="text-3xl font-extrabold text-white flex items-center gap-3">
          <i class="fas fa-magnifying-glass-chart text-indigo-400" />
          Strategy Analyzer
        </h1>
        <p class="text-gray-400 mt-1">
          Multi-indicator technical analysis — RSI · EMA · MACD · Bollinger Bands — with risk/reward management.
        </p>
      </div>

      <!-- Controls -->
      <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 flex flex-wrap gap-4 items-end">
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Market</label>
          <select v-model="market" @change="onMarketChange"
            class="bg-gray-900/70 border border-gray-600 text-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            <option value="us-stocks">US Stocks</option>
            <option value="crypto">Crypto</option>
            <option value="taiwan-stocks">Taiwan Stocks</option>
          </select>
        </div>

        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Symbol</label>
          <select v-model="symbol"
            class="bg-gray-900/70 border border-gray-600 text-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
            <option v-for="s in symbolList" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
        </div>

        <button @click="analyze" :disabled="loading"
          class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-colors flex items-center gap-2">
          <i v-if="loading" class="fas fa-circle-notch fa-spin" />
          <i v-else class="fas fa-play" />
          {{ loading ? 'Analyzing…' : 'Run Analysis' }}
        </button>
      </div>

      <!-- Error -->
      <div v-if="error" class="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm flex gap-2">
        <i class="fas fa-circle-exclamation mt-0.5 flex-shrink-0" />{{ error }}
      </div>

      <!-- Results -->
      <template v-if="signal">

        <!-- Signal banner -->
        <div class="rounded-2xl p-6 border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          :class="signalStyle.bg">
          <div>
            <p class="text-xs font-semibold uppercase tracking-widest opacity-70">{{ symbol }} · {{ market }}</p>
            <p class="text-4xl font-extrabold mt-1" :class="signalStyle.text">{{ signal.action }}</p>
            <p class="text-sm opacity-70 mt-1">Entry @ ${{ signal.entryPrice.toLocaleString() }}</p>
          </div>
          <div class="flex flex-col items-end gap-1">
            <p class="text-xs opacity-60">Confidence</p>
            <p class="text-5xl font-black" :class="signalStyle.text">{{ signal.confidence }}%</p>
          </div>
        </div>

        <!-- Key metrics -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-4">
            <p class="text-xs text-gray-500">Risk Score</p>
            <p class="text-2xl font-bold mt-1" :class="riskColor(signal.riskScore)">{{ signal.riskScore }}/10</p>
            <p class="text-xs text-gray-500 mt-1">{{ signal.riskScore <= 3 ? 'Low risk' : signal.riskScore <= 6 ? 'Medium risk' : 'High risk' }}</p>
          </div>
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-4">
            <p class="text-xs text-gray-500">Stop Loss</p>
            <p class="text-2xl font-bold mt-1 text-red-400">${{ signal.stopLoss.toLocaleString() }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ ((signal.entryPrice - signal.stopLoss) / signal.entryPrice * 100).toFixed(1) }}% below entry</p>
          </div>
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-4">
            <p class="text-xs text-gray-500">Take Profit</p>
            <p class="text-2xl font-bold mt-1 text-green-400">${{ signal.takeProfit.toLocaleString() }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ ((signal.takeProfit - signal.entryPrice) / signal.entryPrice * 100).toFixed(1) }}% above entry</p>
          </div>
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-4">
            <p class="text-xs text-gray-500">Risk/Reward</p>
            <p class="text-2xl font-bold mt-1 text-indigo-400">1:{{ signal.riskRewardRatio }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ signal.riskRewardRatio >= 2 ? 'Excellent ratio' : signal.riskRewardRatio >= 1.5 ? 'Good ratio' : 'Marginal' }}</p>
          </div>
        </div>

        <!-- Indicator gauges -->
        <div class="grid md:grid-cols-2 gap-6">

          <!-- RSI -->
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="font-semibold text-white flex items-center gap-2">
                <i class="fas fa-gauge text-indigo-400 text-sm" />RSI (14)
              </h3>
              <span class="text-lg font-bold" :class="rsiColor(signal.rsiValue)">{{ signal.rsiValue }}</span>
            </div>
            <!-- RSI bar -->
            <div class="relative h-3 bg-gray-700 rounded-full overflow-hidden">
              <div class="absolute inset-y-0 left-0 w-[30%] bg-green-500/30 rounded-l-full" />
              <div class="absolute inset-y-0 left-[30%] w-[40%] bg-gray-600/30" />
              <div class="absolute inset-y-0 left-[70%] right-0 bg-red-500/30 rounded-r-full" />
              <!-- Needle -->
              <div class="absolute top-0 bottom-0 w-1 bg-white rounded-full shadow"
                :style="{ left: signal.rsiValue + '%' }" />
            </div>
            <div class="flex justify-between text-xs text-gray-500">
              <span>0 — Oversold</span><span class="text-center">50</span><span>100 — Overbought</span>
            </div>
            <p class="text-xs" :class="rsiColor(signal.rsiValue)">
              {{ signal.rsiValue < 30 ? 'Oversold — strong buy zone' : signal.rsiValue > 70 ? 'Overbought — caution' : signal.rsiValue < 50 ? 'Below midpoint — mild bullish' : 'Above midpoint — mild bearish' }}
            </p>
          </div>

          <!-- EMA Alignment -->
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 space-y-3">
            <h3 class="font-semibold text-white flex items-center gap-2">
              <i class="fas fa-chart-line text-indigo-400 text-sm" />EMA Alignment
            </h3>
            <div class="flex items-center gap-3">
              <i class="text-2xl fas"
                :class="signal.emaAlignment === 'bullish' ? 'fa-arrow-trend-up text-green-400' : signal.emaAlignment === 'bearish' ? 'fa-arrow-trend-down text-red-400' : 'fa-arrows-left-right text-yellow-400'" />
              <div>
                <p class="font-semibold text-white capitalize">{{ signal.emaAlignment }}</p>
                <p class="text-xs text-gray-400">
                  {{ signal.emaAlignment === 'bullish' ? 'EMA 9 > EMA 21 > EMA 50 — all three stacked bullish' : signal.emaAlignment === 'bearish' ? 'EMA 9 < EMA 21 < EMA 50 — all three stacked bearish' : 'EMAs not aligned — wait for clearer trend' }}
                </p>
              </div>
            </div>
          </div>

          <!-- MACD -->
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 space-y-3">
            <h3 class="font-semibold text-white flex items-center gap-2">
              <i class="fas fa-wave-square text-indigo-400 text-sm" />MACD (12,26,9)
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                :class="signal.macdBullish ? 'bg-green-500/20' : 'bg-red-500/20'">
                <i class="fas text-lg" :class="signal.macdBullish ? 'fa-arrow-up text-green-400' : 'fa-arrow-down text-red-400'" />
              </div>
              <div>
                <p class="font-semibold" :class="signal.macdBullish ? 'text-green-400' : 'text-red-400'">
                  {{ signal.macdBullish ? 'Bullish momentum' : 'Bearish momentum' }}
                </p>
                <p class="text-xs text-gray-400">
                  {{ signal.macdBullish ? 'Histogram positive or recovering — buyers in control' : 'Histogram negative — sellers in control' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Bollinger Bands -->
          <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 space-y-3">
            <h3 class="font-semibold text-white flex items-center gap-2">
              <i class="fas fa-compress text-indigo-400 text-sm" />Bollinger Bands (20,2)
            </h3>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                :class="signal.bbZone === 'oversold' ? 'bg-green-500/20' : signal.bbZone === 'overbought' ? 'bg-red-500/20' : 'bg-gray-700/60'">
                <i class="fas text-lg"
                  :class="signal.bbZone === 'oversold' ? 'fa-circle-down text-green-400' : signal.bbZone === 'overbought' ? 'fa-circle-up text-red-400' : 'fa-circle text-gray-400'" />
              </div>
              <div>
                <p class="font-semibold text-white capitalize">{{ signal.bbZone }}</p>
                <p class="text-xs text-gray-400">
                  {{ signal.bbZone === 'oversold' ? 'At lower band — statistical mean-reversion zone' : signal.bbZone === 'overbought' ? 'At upper band — overextended, pullback likely' : 'Mid-band — no extreme reading' }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Signal reasoning -->
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6">
          <h2 class="font-semibold text-white mb-4 flex items-center gap-2">
            <i class="fas fa-list-check text-indigo-400" />Signal Reasoning
          </h2>
          <ul class="space-y-2">
            <li v-for="(r, i) in signal.reasons" :key="i"
              class="flex items-start gap-3 text-sm">
              <i class="fas mt-0.5 flex-shrink-0"
                :class="r.bullish ? 'fa-circle-check text-green-400' : 'fa-circle-xmark text-red-400'" />
              <span :class="r.bullish ? 'text-gray-200' : 'text-gray-400'">{{ r.text }}</span>
            </li>
          </ul>
        </div>

        <!-- Strategy summary -->
        <div class="bg-indigo-600/10 border border-indigo-500/30 rounded-2xl p-6">
          <h2 class="font-semibold text-white mb-3 flex items-center gap-2">
            <i class="fas fa-lightbulb text-indigo-400" />Strategy Summary
          </h2>
          <p class="text-sm text-gray-300 leading-relaxed">
            <span v-if="signal.action === 'STRONG BUY' || signal.action === 'BUY'">
              Technical indicators align for a <span class="text-green-400 font-semibold">{{ signal.action }}</span>.
              Consider entering near <strong class="text-white">${{ signal.entryPrice.toLocaleString() }}</strong> with
              a stop loss at <strong class="text-red-400">${{ signal.stopLoss.toLocaleString() }}</strong>
              ({{ ((signal.entryPrice - signal.stopLoss) / signal.entryPrice * 100).toFixed(1) }}% risk) and
              a take-profit target at <strong class="text-green-400">${{ signal.takeProfit.toLocaleString() }}</strong>
              for a <strong class="text-white">1:{{ signal.riskRewardRatio }}</strong> risk/reward ratio.
              Risk score is <span :class="riskColor(signal.riskScore)">{{ signal.riskScore }}/10</span> — always size positions according to your risk tolerance.
            </span>
            <span v-else-if="signal.action === 'STRONG SELL' || signal.action === 'SELL'">
              Indicators suggest a <span class="text-red-400 font-semibold">{{ signal.action }}</span> signal.
              Avoid new long positions. If already holding, consider reducing exposure or setting a tight stop at
              <strong class="text-red-400">${{ signal.stopLoss.toLocaleString() }}</strong>.
            </span>
            <span v-else>
              Indicators are mixed — <span class="text-yellow-400 font-semibold">HOLD</span> or wait for clearer confirmation before entering.
              A breakout above EMA alignment or MACD crossover would provide a stronger signal.
            </span>
          </p>
        </div>

      </template>

      <!-- Empty state -->
      <div v-else-if="!loading" class="text-center py-16 text-gray-600">
        <i class="fas fa-magnifying-glass-chart text-6xl mb-4 block" />
        <p class="text-lg">Select a market and symbol, then click <strong class="text-gray-400">Run Analysis</strong>.</p>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { getUSDaily, getTWSEDaily, getKlines } from '@/api/quotes.js'
import { generateSignal, type TradingSignal } from '@/utils/indicators'

const market = ref('us-stocks')
const symbol = ref('AAPL')
const loading = ref(false)
const error = ref('')
const signal = ref<TradingSignal | null>(null)

const stockLists: Record<string, { value: string; label: string }[]> = {
  'us-stocks': [
    { value: 'AAPL',  label: 'Apple (AAPL)' },
    { value: 'TSLA',  label: 'Tesla (TSLA)' },
    { value: 'AMZN',  label: 'Amazon (AMZN)' },
    { value: 'GOOGL', label: 'Google (GOOGL)' },
    { value: 'MSFT',  label: 'Microsoft (MSFT)' },
    { value: 'NVDA',  label: 'NVIDIA (NVDA)' },
    { value: 'META',  label: 'Meta (META)' },
  ],
  crypto: [
    { value: 'BTCUSDT', label: 'Bitcoin (BTC)' },
    { value: 'ETHUSDT', label: 'Ethereum (ETH)' },
    { value: 'BNBUSDT', label: 'BNB (BNB)' },
    { value: 'SOLUSDT', label: 'Solana (SOL)' },
    { value: 'XRPUSDT', label: 'XRP (XRP)' },
  ],
  'taiwan-stocks': [
    { value: '2330', label: 'TSMC (2330)' },
    { value: '2303', label: 'UMC (2303)' },
    { value: '0050', label: 'Yuanta 50 ETF (0050)' },
  ],
}

const symbolList = computed(() => stockLists[market.value] ?? [])

function onMarketChange() {
  symbol.value = symbolList.value[0]?.value ?? ''
  signal.value = null
}

async function analyze() {
  error.value = ''
  signal.value = null
  loading.value = true
  try {
    let prices: number[] = []

    if (market.value === 'us-stocks') {
      const data = await getUSDaily(symbol.value)
      prices = data.prices
    } else if (market.value === 'taiwan-stocks') {
      const data = await getTWSEDaily(symbol.value)
      prices = data.prices
    } else {
      const data = await getKlines(symbol.value)
      prices = data.prices
    }

    if (!prices || prices.length < 15) {
      error.value = 'Not enough price data to compute indicators. Check your API key in Settings.'
      return
    }

    signal.value = generateSignal(prices)
  } catch (e: any) {
    error.value = e?.message || 'Failed to fetch price data. Check your API key in Settings.'
  } finally {
    loading.value = false
  }
}

const signalStyle = computed(() => {
  if (!signal.value) return { bg: '', text: '' }
  switch (signal.value.action) {
    case 'STRONG BUY':  return { bg: 'bg-green-500/10 border-green-500/30', text: 'text-green-400' }
    case 'BUY':         return { bg: 'bg-green-500/10 border-green-500/20', text: 'text-green-300' }
    case 'STRONG SELL': return { bg: 'bg-red-500/10 border-red-500/30', text: 'text-red-400' }
    case 'SELL':        return { bg: 'bg-red-500/10 border-red-500/20', text: 'text-red-300' }
    default:            return { bg: 'bg-yellow-500/10 border-yellow-500/20', text: 'text-yellow-400' }
  }
})

function riskColor(score: number) {
  if (score <= 3) return 'text-green-400'
  if (score <= 6) return 'text-yellow-400'
  return 'text-red-400'
}

function rsiColor(val: number) {
  if (val < 30) return 'text-green-400'
  if (val > 70) return 'text-red-400'
  return 'text-gray-300'
}
</script>
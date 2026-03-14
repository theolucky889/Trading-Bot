<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8">
    <div class="max-w-3xl mx-auto space-y-8">

      <div>
        <h1 class="text-3xl font-extrabold text-white">Settings</h1>
        <p class="text-gray-400 mt-1">Configure your trading bot preferences and API keys.</p>
      </div>

      <!-- API Keys -->
      <section class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-5">
        <h2 class="text-lg font-semibold text-white flex items-center gap-2">
          <i class="fas fa-key text-indigo-400" />
          API Keys
        </h2>

        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Alpha Vantage API Key</label>
          <p class="text-xs text-gray-500 mb-2">Used for US stock price data. Get a free key at alphavantage.co.</p>
          <div class="flex gap-2">
            <input
              v-model="alphaKey"
              :type="showAlphaKey ? 'text' : 'password'"
              placeholder="Enter your Alpha Vantage key"
              class="flex-1 bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            />
            <button
              type="button"
              @click="showAlphaKey = !showAlphaKey"
              class="px-3 py-2 rounded-xl bg-gray-700 hover:bg-gray-600 text-gray-300 transition"
            >
              <i :class="showAlphaKey ? 'fas fa-eye-slash' : 'fas fa-eye'" />
            </button>
          </div>
        </div>

        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Binance API Key</label>
          <p class="text-xs text-gray-500 mb-2">Used for crypto data. Required only for authenticated Binance endpoints.</p>
          <input
            v-model="binanceKey"
            :type="showBinanceKey ? 'text' : 'password'"
            placeholder="Enter your Binance API key"
            class="w-full bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          />
        </div>
      </section>

      <!-- Trading Preferences -->
      <section class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-5">
        <h2 class="text-lg font-semibold text-white flex items-center gap-2">
          <i class="fas fa-sliders text-indigo-400" />
          Trading Preferences
        </h2>

        <div class="grid sm:grid-cols-2 gap-4">
          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-300">Default Market</label>
            <select
              v-model="defaultMarket"
              class="w-full bg-gray-900/70 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            >
              <option value="us-stocks">US Stocks</option>
              <option value="taiwan-stocks">Taiwan Stocks</option>
              <option value="crypto">Crypto</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-300">Risk Level</label>
            <select
              v-model="riskLevel"
              class="w-full bg-gray-900/70 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            >
              <option value="low">Low — preserve capital</option>
              <option value="medium">Medium — balanced</option>
              <option value="high">High — aggressive growth</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-300">Default Chart Type</label>
            <select
              v-model="defaultChart"
              class="w-full bg-gray-900/70 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            >
              <option value="line">Line</option>
              <option value="bar">Bar</option>
            </select>
          </div>

          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-300">Sentiment Model</label>
            <select
              v-model="sentimentModel"
              class="w-full bg-gray-900/70 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
            >
              <option value="vader">VADER (fast, local)</option>
              <option value="finbert">FinBERT (optional)</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Notifications -->
      <section class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-4">
        <h2 class="text-lg font-semibold text-white flex items-center gap-2">
          <i class="fas fa-bell text-indigo-400" />
          Notifications
        </h2>
        <label class="flex items-center gap-3 cursor-pointer">
          <div
            class="w-10 h-5 rounded-full transition-colors relative"
            :class="emailAlerts ? 'bg-indigo-600' : 'bg-gray-700'"
            @click="emailAlerts = !emailAlerts"
          >
            <span
              class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
              :class="emailAlerts ? 'translate-x-5' : 'translate-x-0.5'"
            />
          </div>
          <span class="text-sm text-gray-300">Email alerts for significant price moves</span>
        </label>
        <label class="flex items-center gap-3 cursor-pointer">
          <div
            class="w-10 h-5 rounded-full transition-colors relative"
            :class="tradeAlerts ? 'bg-indigo-600' : 'bg-gray-700'"
            @click="tradeAlerts = !tradeAlerts"
          >
            <span
              class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
              :class="tradeAlerts ? 'translate-x-5' : 'translate-x-0.5'"
            />
          </div>
          <span class="text-sm text-gray-300">Trade execution notifications</span>
        </label>
      </section>

      <!-- Save -->
      <div class="flex items-center gap-4">
        <button
          @click="save"
          class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl text-sm transition-colors"
        >
          <i class="fas fa-floppy-disk mr-2" />Save Settings
        </button>
        <span v-if="saved" class="text-green-400 text-sm flex items-center gap-1.5">
          <i class="fas fa-check" />Saved!
        </span>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const alphaKey = ref(localStorage.getItem('vite_alpha_key') ?? '')
const binanceKey = ref(localStorage.getItem('binance_key') ?? '')
const showAlphaKey = ref(false)
const showBinanceKey = ref(false)

const defaultMarket = ref(localStorage.getItem('default_market') ?? 'us-stocks')
const riskLevel = ref(localStorage.getItem('risk_level') ?? 'medium')
const defaultChart = ref(localStorage.getItem('default_chart') ?? 'line')
const sentimentModel = ref(localStorage.getItem('sentiment_model') ?? 'vader')

const emailAlerts = ref(localStorage.getItem('email_alerts') === 'true')
const tradeAlerts = ref(localStorage.getItem('trade_alerts') === 'true')

const saved = ref(false)

function save() {
  localStorage.setItem('vite_alpha_key', alphaKey.value)
  localStorage.setItem('binance_key', binanceKey.value)
  localStorage.setItem('default_market', defaultMarket.value)
  localStorage.setItem('risk_level', riskLevel.value)
  localStorage.setItem('default_chart', defaultChart.value)
  localStorage.setItem('sentiment_model', sentimentModel.value)
  localStorage.setItem('email_alerts', String(emailAlerts.value))
  localStorage.setItem('trade_alerts', String(tradeAlerts.value))

  saved.value = true
  setTimeout(() => (saved.value = false), 2000)
}
</script>
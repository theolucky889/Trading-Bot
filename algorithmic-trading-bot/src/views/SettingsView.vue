<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8">
    <div class="max-w-3xl mx-auto space-y-8">

      <div>
        <h1 class="text-3xl font-extrabold text-white">Settings</h1>
        <p class="text-gray-400 mt-1">Configure your trading bot preferences and API keys.</p>
      </div>

      <!-- API Keys -->
      <section class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-white flex items-center gap-2">
              <i class="fas fa-key text-indigo-400" />
              API Keys
            </h2>
            <p class="text-xs text-gray-500 mt-1">
              Keys are stored securely on the server — never exposed in your browser.
              <span v-if="!auth.isLoggedIn" class="text-yellow-400">Log in to save API keys.</span>
            </p>
          </div>
          <div v-if="keysLoading" class="text-xs text-gray-500 flex items-center gap-1.5 mt-1">
            <i class="fas fa-circle-notch fa-spin" /> Loading…
          </div>
        </div>

        <p v-if="keysError" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {{ keysError }}
        </p>

        <!-- Alpha Vantage -->
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Alpha Vantage API Key</label>
          <p class="text-xs text-gray-500 mb-2">
            Used for US stocks and Forex data. Get a free key at
            <a href="https://www.alphavantage.co/support/#api-key" target="_blank" rel="noreferrer"
               class="text-indigo-400 hover:underline">alphavantage.co</a>
            (free, 25 req/day).
          </p>
          <div v-if="avKeySet && !editingAvKey"
               class="flex items-center justify-between bg-gray-900/50 border border-gray-700 rounded-xl px-4 py-2.5">
            <span class="text-sm text-gray-400 font-mono">{{ avKeyMasked }}</span>
            <button @click="editingAvKey = true; alphaKey = ''"
                    class="text-xs text-indigo-400 hover:text-indigo-300 transition">Change</button>
          </div>
          <div v-else class="flex gap-2">
            <input
              v-model="alphaKey"
              :type="showAlphaKey ? 'text' : 'password'"
              placeholder="Enter your Alpha Vantage key"
              class="flex-1 bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            />
            <button type="button" @click="showAlphaKey = !showAlphaKey"
                    class="px-3 py-2 rounded-xl bg-gray-700 hover:bg-gray-600 text-gray-300 transition">
              <i :class="showAlphaKey ? 'fas fa-eye-slash' : 'fas fa-eye'" />
            </button>
          </div>
        </div>

        <!-- Binance -->
        <div class="space-y-1">
          <label class="block text-sm font-medium text-gray-300">Binance API Key</label>
          <p class="text-xs text-gray-500 mb-2">Optional. Only needed for authenticated Binance endpoints. Crypto market data works without it.</p>
          <div v-if="binanceKeySet && !editingBinanceKey"
               class="flex items-center justify-between bg-gray-900/50 border border-gray-700 rounded-xl px-4 py-2.5">
            <span class="text-sm text-gray-400 font-mono">{{ binanceKeyMasked }}</span>
            <button @click="editingBinanceKey = true; binanceKey = ''"
                    class="text-xs text-indigo-400 hover:text-indigo-300 transition">Change</button>
          </div>
          <div v-else>
            <input
              v-model="binanceKey"
              :type="showBinanceKey ? 'text' : 'password'"
              placeholder="Enter your Binance API key"
              class="w-full bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
            />
          </div>
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
              <option value="crypto">Crypto</option>
              <option value="forex">Forex</option>
              <option value="taiwan-stocks">Taiwan Stocks</option>
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
      <div class="flex items-center gap-4 flex-wrap">
        <button
          @click="save"
          :disabled="saving"
          class="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-colors flex items-center gap-2"
        >
          <i v-if="saving" class="fas fa-circle-notch fa-spin" />
          <i v-else class="fas fa-floppy-disk" />
          {{ saving ? 'Saving…' : 'Save Settings' }}
        </button>
        <span v-if="saved" class="text-green-400 text-sm flex items-center gap-1.5">
          <i class="fas fa-check" />Saved!
        </span>
        <span v-if="saveError" class="text-red-400 text-sm flex items-center gap-1.5">
          <i class="fas fa-circle-exclamation" />{{ saveError }}
        </span>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// ── API Keys (stored on backend per user account) ─────────────────────────────
const alphaKey = ref('')
const binanceKey = ref('')
const showAlphaKey = ref(false)
const showBinanceKey = ref(false)
const avKeySet = ref(false)
const avKeyMasked = ref('')
const binanceKeySet = ref(false)
const binanceKeyMasked = ref('')
const editingAvKey = ref(false)
const editingBinanceKey = ref(false)
const keysLoading = ref(false)
const keysError = ref('')

async function loadKeys() {
  if (!auth.isLoggedIn) return
  keysLoading.value = true
  keysError.value = ''
  try {
    const res = await fetch('/api/settings/keys', {
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    if (res.ok) {
      const data = await res.json()
      avKeySet.value = data.alpha_vantage_set
      avKeyMasked.value = data.alpha_vantage_key
      binanceKeySet.value = data.binance_set
      binanceKeyMasked.value = data.binance_key
    }
  } catch {
    keysError.value = 'Could not load saved keys.'
  } finally {
    keysLoading.value = false
  }
}

// ── Trading preferences (non-sensitive, localStorage is fine) ─────────────────
const defaultMarket = ref(localStorage.getItem('default_market') ?? 'us-stocks')
const riskLevel = ref(localStorage.getItem('risk_level') ?? 'medium')
const defaultChart = ref(localStorage.getItem('default_chart') ?? 'line')
const sentimentModel = ref(localStorage.getItem('sentiment_model') ?? 'vader')
const emailAlerts = ref(localStorage.getItem('email_alerts') === 'true')
const tradeAlerts = ref(localStorage.getItem('trade_alerts') === 'true')

const saved = ref(false)
const saving = ref(false)
const saveError = ref('')

async function save() {
  saveError.value = ''
  saving.value = true

  try {
    // Save API keys to backend if user is logged in and entered new values
    if (auth.isLoggedIn && (alphaKey.value || binanceKey.value || editingAvKey.value || editingBinanceKey.value)) {
      const res = await fetch('/api/settings/keys', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${auth.token}`,
        },
        body: JSON.stringify({
          alpha_vantage_key: editingAvKey.value ? alphaKey.value : undefined,
          binance_key: editingBinanceKey.value ? binanceKey.value : undefined,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to save API keys')
      }
      // Reload masked keys and reset edit state
      editingAvKey.value = false
      editingBinanceKey.value = false
      alphaKey.value = ''
      binanceKey.value = ''
      await loadKeys()
    } else if (!auth.isLoggedIn && (alphaKey.value || binanceKey.value)) {
      saveError.value = 'Log in to save API keys to your account.'
    }

    // Save non-sensitive preferences to localStorage
    localStorage.setItem('default_market', defaultMarket.value)
    localStorage.setItem('risk_level', riskLevel.value)
    localStorage.setItem('default_chart', defaultChart.value)
    localStorage.setItem('sentiment_model', sentimentModel.value)
    localStorage.setItem('email_alerts', String(emailAlerts.value))
    localStorage.setItem('trade_alerts', String(tradeAlerts.value))

    saved.value = true
    setTimeout(() => (saved.value = false), 2500)
  } catch (e: any) {
    saveError.value = e?.message || 'Save failed'
  } finally {
    saving.value = false
  }
}

onMounted(loadKeys)
</script>
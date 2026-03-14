<template>
  <div class="flex min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200">

    <!-- Sidebar -->
    <aside class="w-56 flex-shrink-0 bg-gray-800/60 border-r border-gray-700/40 p-4">
      <p class="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3 px-2">Menu</p>
      <ul class="space-y-1">
        <li
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          class="flex items-center gap-2.5 px-3 py-2 rounded-xl cursor-pointer text-sm transition-colors"
          :class="activeTab === tab.id
            ? 'bg-indigo-600 text-white font-medium'
            : 'text-gray-400 hover:text-white hover:bg-gray-700/60'"
        >
          <i :class="[tab.icon, 'text-xs w-4 text-center']" />
          {{ tab.label }}
        </li>
      </ul>
    </aside>

    <!-- Main content -->
    <main class="flex-1 p-8 overflow-y-auto">

      <!-- Overview -->
      <div v-if="activeTab === 'overview'" class="space-y-8">
        <div>
          <h1 class="text-3xl font-extrabold text-white">Tradebot</h1>
          <p class="text-gray-400 mt-1">
            Bot is currently
            <span class="text-green-400 font-medium">running</span>
            and has made <span class="text-white font-semibold">{{ tradeCount }}</span> trades today.
          </p>
        </div>

        <!-- Status card -->
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-400 mb-1">Trading Status</p>
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse" />
              <span class="font-semibold text-green-400">Active</span>
            </div>
          </div>
          <button
            @click="stopTrading"
            class="px-5 py-2.5 bg-red-600/20 hover:bg-red-600/40 border border-red-500/40 text-red-400 hover:text-red-300 font-medium rounded-xl text-sm transition-colors"
          >
            <i class="fas fa-stop mr-2" />Stop Trading
          </button>
        </div>

        <!-- Current trade -->
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Current Trade</h2>
          <TradeItem v-if="currentTrade" :trade="currentTrade" />
          <p v-else class="text-gray-500 text-sm">No active trade.</p>
        </div>

        <!-- Trade history -->
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Trade History</h2>
          <div class="space-y-3">
            <TradeItem v-for="trade in tradeHistory" :key="trade.id" :trade="trade" />
          </div>
        </div>
      </div>

      <!-- Performance -->
      <div v-else-if="activeTab === 'performance'" class="space-y-4">
        <h1 class="text-3xl font-extrabold text-white">Performance</h1>
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-8 text-center text-gray-500">
          <i class="fas fa-chart-line text-4xl mb-3 text-gray-600" />
          <p>Performance analytics coming soon.</p>
        </div>
      </div>

      <!-- Trades -->
      <div v-else-if="activeTab === 'trades'" class="space-y-4">
        <h1 class="text-3xl font-extrabold text-white">Trades</h1>
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-3">
          <TradeItem v-for="trade in tradeHistory" :key="trade.id" :trade="trade" />
        </div>
      </div>

      <!-- AI Engine -->
      <div v-else-if="activeTab === 'ai'" class="space-y-4">
        <div>
          <h1 class="text-3xl font-extrabold text-white">AI Engine</h1>
          <p class="text-gray-400 mt-1 text-sm">News sentiment analysis powered by VADER.</p>
        </div>
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6">
          <SentimentEngine />
        </div>
      </div>

      <!-- Settings -->
      <div v-else-if="activeTab === 'settings'" class="space-y-4">
        <h1 class="text-3xl font-extrabold text-white">Settings</h1>
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-8 text-center text-gray-500">
          <i class="fas fa-gear text-4xl mb-3 text-gray-600" />
          <p>Bot-specific settings coming soon. See the global <router-link to="/settings" class="text-indigo-400 hover:underline">Settings page</router-link>.</p>
        </div>
      </div>

      <!-- Help -->
      <div v-else-if="activeTab === 'help'" class="space-y-4">
        <h1 class="text-3xl font-extrabold text-white">Help &amp; Feedback</h1>
        <div class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6 space-y-4 text-sm text-gray-300">
          <p><i class="fas fa-circle-question text-indigo-400 mr-2" /><strong>How do I start the bot?</strong> — Use the Dashboard to select stocks and click "Start Trading".</p>
          <p><i class="fas fa-circle-question text-indigo-400 mr-2" /><strong>What data sources are used?</strong> — Alpha Vantage (US stocks), TWSE (Taiwan), Binance (Crypto).</p>
          <p><i class="fas fa-circle-question text-indigo-400 mr-2" /><strong>How is sentiment scored?</strong> — News headlines are scored with VADER, a rule-based NLP model optimised for financial text.</p>
        </div>
      </div>

    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import TradeItem from '../components/TradeItem.vue'
import SentimentEngine from '../components/SentimentEngine.vue'

interface Trade {
  id: number
  time: string
  type: 'Buy' | 'Sell'
  quantity: number
  symbol: string
  price: number
}

export default defineComponent({
  components: { TradeItem, SentimentEngine },
  setup() {
    const tabs = [
      { id: 'overview',    label: 'Overview',      icon: 'fas fa-house' },
      { id: 'performance', label: 'Performance',   icon: 'fas fa-chart-line' },
      { id: 'trades',      label: 'Trades',        icon: 'fas fa-list' },
      { id: 'ai',          label: 'AI Engine',     icon: 'fas fa-brain' },
      { id: 'settings',    label: 'Settings',      icon: 'fas fa-gear' },
      { id: 'help',        label: 'Help & Feedback', icon: 'fas fa-circle-question' },
    ] as const

    const activeTab = ref<typeof tabs[number]['id']>('overview')
    const tradeCount = ref(5)

    const currentTrade: Trade = {
      id: 1, time: '12:00 PM', type: 'Buy', quantity: 5, symbol: '$AAPL', price: 150,
    }

    const tradeHistory: Trade[] = [
      { id: 1, time: '12:00 PM', type: 'Buy',  quantity: 5, symbol: '$AAPL', price: 150 },
      { id: 2, time: '11:00 AM', type: 'Sell', quantity: 5, symbol: '$AAPL', price: 155 },
      { id: 3, time: '10:00 AM', type: 'Buy',  quantity: 5, symbol: '$AAPL', price: 160 },
    ]

    const stopTrading = () => alert('Stopping Trading (Placeholder)')

    return { tabs, activeTab, tradeCount, currentTrade, tradeHistory, stopTrading }
  },
})
</script>
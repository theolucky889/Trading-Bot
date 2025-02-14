<template>
  <div class="tradebot-container">
    <div class="left-sidebar">
      <ul>
        <li :class="{ active: activeTab === 'overview' }" @click="activeTab = 'overview'">
          Overview
        </li>
        <li :class="{ active: activeTab === 'performance' }" @click="activeTab = 'performance'">
          Performance
        </li>
        <li :class="{ active: activeTab === 'trades' }" @click="activeTab = 'trades'">Trades</li>
        <li :class="{ active: activeTab === 'settings' }" @click="activeTab = 'settings'">
          Settings
        </li>
        <li :class="{ active: activeTab === 'help' }" @click="activeTab = 'help'">
          Help & Feedback
        </li>
      </ul>
    </div>
    <div class="main-content font-extrabold mb-8 mt-6">
      <h2>Tradebot</h2>
      <p>Tradebot is currently running and has made {{ tradeCount }} trades today.</p>

      <h3>Trading Status</h3>
      <div class="stop-trading">
        <button @click="stopTrading">Stop Trading</button>
      </div>

      <h3>Current Trade</h3>
      <TradeItem v-if="currentTrade" :trade="currentTrade" />

      <h3>Trade History</h3>
      <div v-for="(trade, index) in tradeHistory" :key="index">
        <TradeItem :trade="trade" />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import TradeItem from './TradeItem.vue' // Create this component for individual trade display

interface Trade {
  id: number
  time: string
  type: 'Buy' | 'Sell'
  quantity: number
  symbol: string
  price: number
}

export default defineComponent({
  components: {
    TradeItem,
  },
  setup() {
    const activeTab = ref('overview')
    const tradeCount = ref(5) // Replace with actual trade count logic

    const currentTrade: Trade = {
      // Replace with actual trade data.
      id: 1,
      time: '12:00 PM',
      type: 'Buy',
      quantity: 5,
      symbol: '$AAPL',
      price: 150,
    }

    const tradeHistory: Trade[] = [
      // Replace with actual trade history logic.
      {
        id: 1,
        time: '12:00 PM',
        type: 'Buy',
        quantity: 5,
        symbol: '$AAPL',
        price: 150,
      },
      {
        id: 2,
        time: '11:00 AM',
        type: 'Sell',
        quantity: 5,
        symbol: '$AAPL',
        price: 155,
      },
      {
        id: 3,
        time: '10:00 AM',
        type: 'Buy',
        quantity: 5,
        symbol: '$AAPL',
        price: 160,
      },
    ]

    const stopTrading = () => {
      // Implement stop trading logic here
      alert('Stopping Trading (Placeholder)')
    }

    return {
      activeTab,
      tradeCount,
      currentTrade,
      tradeHistory,
      stopTrading,
    }
  },
})
</script>

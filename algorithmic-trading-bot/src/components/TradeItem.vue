<template>
  <div class="flex items-center gap-4 bg-gray-900/50 border border-gray-700/30 rounded-xl px-4 py-3">
    <!-- Buy / Sell badge -->
    <span
      class="flex-shrink-0 w-14 text-center text-xs font-bold py-1 rounded-lg"
      :class="trade.type === 'Buy'
        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
        : 'bg-red-500/20 text-red-400 border border-red-500/30'"
    >
      {{ trade.type }}
    </span>

    <!-- Details -->
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-white">
        {{ trade.quantity }} shares of <span class="text-indigo-300">{{ trade.symbol }}</span>
        @ <span class="text-white">${{ trade.price }}</span>
      </p>
      <p class="text-xs text-gray-500 mt-0.5">Trade #{{ trade.id }}</p>
    </div>

    <!-- Time -->
    <span class="text-xs text-gray-500 flex-shrink-0">{{ trade.time }}</span>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'

interface Trade {
  id: number
  time: string
  type: 'Buy' | 'Sell'
  quantity: number
  symbol: string
  price: number
}

export default defineComponent({
  props: {
    trade: {
      type: Object as PropType<Trade>,
      required: true,
    },
  },
})
</script>
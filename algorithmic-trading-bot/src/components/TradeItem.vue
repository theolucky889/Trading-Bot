<template>
  <div class="flex items-center gap-3 rounded-xl bg-gray-900/60 ring-1 ring-gray-700/40 px-4 py-3">
    <span
      class="h-2.5 w-2.5 shrink-0 rounded-full"
      :class="trade.type === 'Buy' ? 'bg-green-400' : 'bg-red-400'"
    />
    <div class="flex flex-1 items-center justify-between gap-3">
      <div class="text-sm text-gray-300">
        <span class="font-semibold text-gray-100">Trade #{{ trade.id }}</span>
        <span class="mx-1 text-gray-500">·</span>
        <span :class="trade.type === 'Buy' ? 'text-green-400' : 'text-red-400'">{{ trade.type }}</span>
        {{ trade.quantity }} shares of {{ trade.symbol }} at ${{ trade.price }}/share
      </div>
      <div class="text-xs text-gray-500 whitespace-nowrap">
        {{ trade.time }}
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'

// Interface for a trade (matches the parent component)
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

<template>
  <div class="trade-item">
    <div :class="trade.type === 'Buy' ? 'buy-icon' : 'sell-icon'"></div>
    <!-- Buy/Sell icon -->
    <div class="trade-details">
      <div>
        <strong>Trade #{{ trade.id }}</strong> <br />
        {{ trade.time }}, {{ trade.type }} {{ trade.quantity }} shares of {{ trade.symbol }} at ${{
          trade.price
        }}
        per share
      </div>
      <div class="trade-time">
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

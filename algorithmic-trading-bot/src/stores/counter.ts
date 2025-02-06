import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('trading', {
  state: () => ({
    stockPrices: {} as Record<string, number>, // Ex. BTC: 50000, AAPL: 175
  }),
  actions: {
    setPrice(symbol: string, price: number) {
      this.stockPrices[symbol] = price
    },
  },
})

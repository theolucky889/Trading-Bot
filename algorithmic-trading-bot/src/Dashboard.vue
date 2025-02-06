<script setup>
import { ref } from 'vue'

const stocks = ref([
  { name: 'BTC', price: 50000 },
  { name: 'ETH', price: 300 },
  { name: 'XRP', price: 0.2 },
  { name: 'AAPL:', price: 175 },
])
</script>

<template>
  <div>
    <h1>Dashboard</h1>
    <ul>
      <li v-for="stock in stocks" :key="stock.name">{{ stock.name }} - ${{ stock.price }}</li>
    </ul>
  </div>
</template>

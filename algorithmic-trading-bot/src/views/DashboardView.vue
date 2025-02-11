<template>
  <div class="flex h-screen bg-gray-900 text-white">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 p-6 flex flex-col justify-between shadow-lg rounded-r-lg">
      <nav>
        <ul>
          <li class="mb-4">
            <a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">Home</a>
          </li>
          <li class="mb-4">
            <a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">Market</a>
          </li>
          <li class="mb-4">
            <a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">Portfolio</a>
          </li>
          <li class="mb-4">
            <a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">News</a>
          </li>
          <li><a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">Bot</a></li>
        </ul>
      </nav>
      <!-- <button class="btn-futuristic p-3 bg-blue-600 hover:bg-blue-700 transition rounded-lg">
        New Order
      </button> -->
      <button v-tooltip="'Create a new order'" @mouseover="console.log('Tooltip active')" class="btn-futuristic">New Order</button>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 p-8 overflow-auto">
      <h1 class="text-4xl font-extrabold mb-8">Trading Bot Dashboard</h1>

      <!-- Category Selection -->
      <div class="flex items-center mb-6">
        <label for="categorySelect" class="mr-3 font-semibold">Select Category:</label>
        <select
          v-model="selectedCategory"
          class="p-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring focus:ring-blue-500"
        >
          <option value="us-stocks">US Stocks</option>
          <option value="taiwan-stocks">Taiwan Stocks</option>
          <option value="crypto">Crypto</option>
        </select>
      </div>

      <!-- Stock Selection -->
      <div class="flex items-center mb-6">
        <label for="stockSelect" class="mr-3 font-semibold">Select Stocks (Compare):</label>
        <select
          v-model="selectedStocks"
          multiple
          class="p-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring focus:ring-blue-500"
        >
          <option
            v-for="stock in availableStocks[selectedCategory]"
            :key="stock.symbol"
            :value="stock.symbol"
          >
            {{ stock.name }} ({{ stock.symbol }})
          </option>
        </select>
      </div>

      <!-- Current Balance -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="p-6 bg-gray-800 rounded-lg shadow-lg">
          <h2 class="text-2xl font-bold">Your Current Balance</h2>
          <p class="text-lg">Cash: $100,000</p>
          <p class="text-lg">Stock: $100,000</p>
        </div>
      </div>

      <!-- Graph Selection -->
      <div class="flex items-center mb-6">
        <label for="graphType" class="mr-3 font-semibold">Select Graph Type:</label>
        <select
          v-model="selectedGraph"
          class="p-3 bg-gray-800 border border-gray-600 rounded-lg focus:ring focus:ring-blue-500"
        >
          <option value="line">Line</option>
          <option value="bar">Bar</option>
        </select>
      </div>

      <!-- Stock Charts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div
          class="p-6 bg-gray-800 rounded-lg shadow-lg"
          v-for="stock in selectedStocks"
          :key="stock"
        >
          <h2 class="text-2xl font-bold">{{ stock }} Stock Price</h2>
          <canvas :id="stock + selectedGraph + 'StockPriceChart'"></canvas>
        </div>
      </div>

      <!-- Latest News -->
      <div class="p-6 bg-gray-800 rounded-lg shadow-lg mb-8">
        <h2 class="text-2xl font-bold">Latest News</h2>
        <ul class="list-disc pl-5">
          <li>AlgoHouse raises $10M in Series A funding</li>
          <li>AlgoHouse bot helps investors make better decisions</li>
          <li>AlgoHouse introduces new features for users</li>
        </ul>
      </div>

      <!-- Start Trading Button -->
      <div class="flex justify-end">
        <button class="btn-futuristic p-3 bg-green-600 hover:bg-green-700 transition rounded-lg">
          Start Trading
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { renderCharts } from '../chart.js'
import { fetchStockData } from '../api.js'

const selectedCategory = ref('us-stocks')
const selectedGraph = ref('line')
const selectedStocks = ref(['AAPL'])

const availableStocks = ref({
  'us-stocks': [
    { name: 'Apple', symbol: 'AAPL' },
    { name: 'Tesla', symbol: 'TSLA' },
    { name: 'Amazon', symbol: 'AMZN' },
    { name: 'Google', symbol: 'GOOGL' },
  ],
  'taiwan-stocks': [
    { name: 'TSMC', symbol: '2330.TW' },
    { name: 'Hon Hai', symbol: '2317.TW' },
  ],
  crypto: [
    { name: 'Bitcoin', symbol: 'BTCUSDT' },
    { name: 'Ethereum', symbol: 'ETHUSDT' },
  ],
})

const updateCharts = async () => {
  await fetchStockData(selectedStocks.value, selectedCategory.value)
  selectedStocks.value.forEach((stock) => {
    renderCharts(`${stock}${selectedGraph.value}StockPriceChart`)
  })
}

onMounted(updateCharts)
watch([selectedGraph, selectedStocks], updateCharts)
</script>

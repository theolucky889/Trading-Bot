<template>
  <div class="flex h-screen bg-gray-900 text-white">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-800 p-6 flex flex-col justify-between shadow-lg rounded-r-lg">
      <nav>
        <ul>
          <li v-for="item in menuItems" :key="item.name" class="mb-4">
            <a href="#" class="block p-3 rounded-lg hover:bg-gray-700 transition">
              {{ item.name }}
            </a>
          </li>
        </ul>
      </nav>
      <button
        v-tooltip="'Create a new order'"
        class="p-3 bg-blue-600 hover:bg-blue-700 transition rounded-lg"
      >
        New Order
      </button>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 p-8 overflow-auto">
      <h1 class="text-4xl font-extrabold">Trading Bot Dashboard</h1>

      <!-- Current Balance Section -->
      <div class="bg-gray-900 p-6 rounded-xl shadow-md">
        <!-- Top Row: Total Assets, Debt, Net Assets -->
        <div class="flex justify-between space-x-6 mb-4">
          <div class="bg-gray-800 p-4 rounded-lg flex-1 text-center">
            <h2 class="text-lg font-semibold">Total Assets</h2>
            <p class="text-xl font-bold">$200,000</p>
          </div>
          <div class="bg-gray-800 p-4 rounded-lg flex-1 text-center">
            <h2 class="text-lg font-semibold">Debt</h2>
            <p class="text-xl font-bold">$50,000</p>
          </div>
          <div class="bg-gray-800 p-4 rounded-lg flex-1 text-center">
            <h2 class="text-lg font-semibold">Net Assets</h2>
            <p class="text-xl font-bold">$150,000</p>
          </div>
        </div>

        <!-- Cash Indicator -->
        <div class="mb-4">
          <h3 class="text-md font-semibold mb-1">Cash: $100,000</h3>
          <div class="bg-gray-700 rounded-full h-4 overflow-hidden">
            <div class="bg-green-500 h-full" style="width: 60%"></div>
          </div>
        </div>

        <!-- Stock Indicator -->
        <div>
          <h3 class="text-md font-semibold mb-1">Stock: $100,000</h3>
          <div class="bg-gray-700 rounded-full h-4 overflow-hidden">
            <div class="bg-blue-500 h-full" style="width: 70%"></div>
          </div>
        </div>
      </div>

      <!-- Category & Stocks Selection (Side by Side) -->
      <div class="flex items-center space-x-6 mb-6">
        <!-- Category Selection -->
        <div class="flex items-center">
          <label class="mr-3 font-semibold">Select Category:</label>
          <select
            v-model="selectedCategory"
            class="p-3 bg-gray-800 border border-gray-600 rounded-lg"
          >
            <option value="us-stocks">US Stocks</option>
            <option value="taiwan-stocks">Taiwan Stocks</option>
            <option value="crypto">Crypto</option>
          </select>
        </div>

        <!-- Stock Selection -->
        <div class="flex items-center">
          <label class="mr-3 font-semibold">Select Stocks (Compare):</label>
          <select
            v-model="selectedStocks"
            multiple
            class="p-3 bg-gray-800 border border-gray-600 rounded-lg"
          >
            <option value="AAPL">Apple (AAPL)</option>
            <option value="TSLA">Tesla (TSLA)</option>
            <option value="AMZN">Amazon (AMZN)</option>
            <option value="GOOGL">Google (GOOGL)</option>
          </select>
        </div>
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

      <!-- Graph Selection -->
      <div class="flex items-center mb-6">
        <label class="mr-3 font-semibold">Select Graph Type:</label>
        <select v-model="selectedGraph" class="p-3 bg-gray-800 border border-gray-600 rounded-lg">
          <option value="line">Line</option>
          <option value="bar">Bar</option>
        </select>
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
        <button class="p-3 bg-green-600 hover:bg-green-700 transition rounded-lg">
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

const menuItems = ref([
  { name: 'Home' },
  { name: 'Market' },
  { name: 'Portfolio' },
  { name: 'News' },
  { name: 'Bot' },
])

const updateCharts = async () => {
  try {
    console.log('Fetching stock data for:', selectedStocks.value)
    await fetchStockData(selectedStocks.value, selectedCategory.value)
    console.log('Rendering charts')
    selectedStocks.value.forEach((stock) => {
      renderCharts(`${stock}${selectedGraph.value}StockPriceChart`)
    })
  } catch (error) {
    console.error('Error updating charts:', error)
  }
}

onMounted(updateCharts)
watch([selectedGraph, selectedStocks], updateCharts)
</script>

<template>
  <div class="flex flex-col items-center justify-center p-8 bg-gray-900 text-white min-h-screen">
    <h1 class="text-3xl font-bold mb-8">Trading Bot Dashboard</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="p-6 bg-gray-800 rounded-lg shadow-lg">
        <h2 class="text-xl font-bold">Your Current Balance</h2>
        <p class="text-lg">Cash: $100,000</p>
        <p class="text-lg">Stock: $100,000</p>
      </div>
      <div class="p-6 bg-gray-800 rounded-lg shadow-lg">
        <h2 class="text-xl font-bold">Overview</h2>
        <div class="flex flex-col">
          <div class="mb-4">
            <h3 class="text-lg">Stock Price</h3>
            <canvas id="stockPriceChart"></canvas>
          </div>
          <div>
            <h3 class="text-lg">Volume</h3>
            <canvas id="volumeChart"></canvas>
          </div>
        </div>
      </div>
      <div class="p-6 bg-gray-800 rounded-lg shadow-lg">
        <h2 class="text-xl font-bold">Latest News</h2>
        <ul>
          <li>AlgoHouse raises $10M in Series A funding</li>
          <li>AlgoHouse bot helps investors make better decisions</li>
          <li>AlgoHouse introduces new features for users</li>
        </ul>
      </div>
    </div>
    <button class="btn-futuristic mt-4">New Order</button>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { renderCharts } from '../chart.js';

onMounted(() => {
  renderCharts('stockPriceChart', 'volumeChart');
});
</script>

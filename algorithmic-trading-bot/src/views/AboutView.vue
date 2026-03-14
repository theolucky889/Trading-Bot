<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-gray-200 p-8">
    <div class="max-w-4xl mx-auto space-y-10">

      <!-- Hero -->
      <div class="text-center py-8">
        <div class="inline-flex items-center justify-center w-20 h-20 bg-indigo-600/20 rounded-3xl mb-6">
          <i class="fas fa-robot text-indigo-400 text-4xl" />
        </div>
        <h1 class="text-4xl font-extrabold text-white">AlgoHouse</h1>
        <p class="text-gray-400 mt-3 max-w-xl mx-auto">
          An algorithmic trading dashboard that combines real-time market data, AI-powered sentiment analysis,
          and smart order execution — all in one place.
        </p>
      </div>

      <!-- Feature grid -->
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="f in features"
          :key="f.title"
          class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-5 space-y-3"
        >
          <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="f.bg">
            <i :class="[f.icon, f.color, 'text-lg']" />
          </div>
          <h3 class="font-semibold text-white">{{ f.title }}</h3>
          <p class="text-sm text-gray-400">{{ f.description }}</p>
        </div>
      </div>

      <!-- Tech stack -->
      <section class="bg-gray-800/60 border border-gray-700/40 rounded-2xl p-6">
        <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <i class="fas fa-layer-group text-indigo-400" />
          Tech Stack
        </h2>
        <div class="grid sm:grid-cols-2 gap-3">
          <div v-for="t in techStack" :key="t.name" class="flex items-center gap-3">
            <span class="w-2 h-2 rounded-full bg-indigo-400 flex-shrink-0" />
            <span class="text-sm text-gray-300 font-medium">{{ t.name }}</span>
            <span class="text-xs text-gray-500">— {{ t.desc }}</span>
          </div>
        </div>
      </section>

      <!-- Version -->
      <p class="text-center text-xs text-gray-600">AlgoHouse v0.2.0 · Built with Vue 3 + FastAPI</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const features = [
  {
    title: 'Live Market Charts',
    description: 'Interactive price, volume, and return/loss charts powered by Chart.js with real data from Alpha Vantage, TWSE, and Binance.',
    icon: 'fas fa-chart-line',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  {
    title: 'AI Sentiment Engine',
    description: 'Analyse news sentiment for any stock or crypto using VADER. Results are stored in your personal history.',
    icon: 'fas fa-brain',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
  },
  {
    title: 'Multi-Market Support',
    description: 'Monitor US stocks, Taiwan Stock Exchange (TWSE) listings, and cryptocurrency pairs in a single dashboard.',
    icon: 'fas fa-globe',
    color: 'text-green-400',
    bg: 'bg-green-500/10',
  },
  {
    title: 'Trade History',
    description: 'Track your current and historical trades with buy/sell indicators, execution time, and price per share.',
    icon: 'fas fa-list-check',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
  },
  {
    title: 'Secure Authentication',
    description: 'JWT-based login with bcrypt-hashed passwords. Your session is stored locally and expires automatically.',
    icon: 'fas fa-shield-halved',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
  },
  {
    title: 'Configurable Settings',
    description: 'Store your API keys, choose your default market, risk level, chart style, and notification preferences.',
    icon: 'fas fa-sliders',
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10',
  },
]

const techStack = [
  { name: 'Vue 3', desc: 'frontend framework (Composition API)' },
  { name: 'Vite', desc: 'dev server and bundler' },
  { name: 'Tailwind CSS v4', desc: 'utility-first styling' },
  { name: 'Pinia', desc: 'state management' },
  { name: 'Chart.js', desc: 'interactive charts' },
  { name: 'FastAPI', desc: 'Python backend API' },
  { name: 'VADER Sentiment', desc: 'NLP sentiment scoring' },
  { name: 'Alpha Vantage', desc: 'US stock data' },
  { name: 'Binance API', desc: 'crypto kline data' },
  { name: 'TWSE API', desc: 'Taiwan stock data' },
]
</script>
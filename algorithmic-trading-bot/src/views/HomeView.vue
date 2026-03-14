<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 flex flex-col items-center justify-center text-center px-4">
    <div class="inline-flex items-center justify-center w-20 h-20 bg-indigo-600/20 rounded-3xl mb-6">
      <i class="fas fa-robot text-indigo-400 text-4xl" />
    </div>
    <h1 class="text-5xl font-extrabold text-white mb-4">AlgoHouse</h1>
    <p class="text-gray-400 text-lg max-w-md mb-10">
      Algorithmic trading powered by real-time data and AI sentiment analysis.
    </p>
    <div class="flex gap-4">
      <RouterLink
        to="/"
        class="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors"
      >
        Go to Dashboard
      </RouterLink>
      <RouterLink
        to="/login"
        class="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold rounded-xl border border-gray-700 transition-colors"
      >
        Sign In
      </RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
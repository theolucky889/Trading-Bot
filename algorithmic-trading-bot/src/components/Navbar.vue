<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="navbar bg-gray-900 p-4 flex justify-between items-center">
    <div class="text-xl text-white font-bold">TradingBot Dashboard</div>
    <div class="flex space-x-4">
      <RouterLink class="text-white hover:text-blue-400" to="/">Home</RouterLink>
      <RouterLink class="text-white hover:text-blue-400" to="/auth">Auth</RouterLink>
      <RouterLink class="text-white hover:text-blue-400" to="/dashboard">Dashboard</RouterLink>
      <RouterLink class="text-white hover:text-blue-400" to="/trade">Trade</RouterLink>
      <RouterLink class="text-white hover:text-blue-400" to="/settings">Settings</RouterLink>
    </div>
  </nav>
</template>

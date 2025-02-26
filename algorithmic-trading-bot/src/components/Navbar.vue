<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="bg-gray-800 text-white p-4">
    <div class="container mx-auto flex justify-between items-center">
      <RouterLink to="/" class="text-xl font-bold">Trading Bot</RouterLink>
      <div class="space-x-4">
        <RouterLink to="/" class="hover:text-gray-300">Dashboard</RouterLink>
        <RouterLink to="/trade" class="hover:text-gray-300">Trade</RouterLink>
        <RouterLink to="/settings" class="hover:text-gray-300">Settings</RouterLink>
        <RouterLink to="/about" class="hover:text-gray-300">About</RouterLink>
        <RouterLink to="/login" class="hover:text-gray-300">Login</RouterLink>
      </div>
    </div>
  </nav>
</template>

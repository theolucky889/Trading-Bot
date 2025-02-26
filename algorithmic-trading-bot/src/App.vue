<template>
  <div id="app" class="min-h-screen bg-gray-900">
    <Navbar />
    <!-- Add router view -->
    <router-view></router-view>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>

<style>
#app {
  font-family: 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>

<template>
  <div id="app">
    <Navbar />
    <!-- Add router view -->
    <router-view></router-view>
  </div>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>
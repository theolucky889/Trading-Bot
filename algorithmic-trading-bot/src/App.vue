<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="app-container">
    <nav>
      <RouterLink to="/">Dashboard</RouterLink>
      <RouterLink to="/settings">Settings</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<style>
.app-container {
  font-family: Arial, sans-serif;
}
nav {
  display: flex;
  gap: 15px;
  padding: 10px;
  background: #333;
}
nav a {
  color: white;
  text-decoration: none;
}
</style>

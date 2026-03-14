<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <nav class="sticky top-0 z-50 bg-gray-900/95 backdrop-blur border-b border-gray-800 shadow-lg">
    <div class="max-w-screen-2xl mx-auto flex items-center justify-between px-6 py-3">

      <!-- Brand -->
      <RouterLink to="/" class="flex items-center gap-2 text-white font-bold text-lg tracking-tight">
        <i class="fas fa-robot text-indigo-400" />
        AlgoHouse
      </RouterLink>

      <!-- Nav links -->
      <div class="hidden md:flex items-center gap-1">
        <RouterLink
          to="/"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-gauge-high mr-1.5 text-xs" />Dashboard
        </RouterLink>
        <RouterLink
          to="/trade"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-arrow-right-arrow-left mr-1.5 text-xs" />Trade
        </RouterLink>
        <RouterLink
          to="/strategy"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-chart-line mr-1.5 text-xs" />Strategy
        </RouterLink>
        <RouterLink
          to="/prediction"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-brain mr-1.5 text-xs" />Predictions
        </RouterLink>
        <RouterLink
          to="/settings"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-gear mr-1.5 text-xs" />Settings
        </RouterLink>
        <RouterLink
          to="/about"
          class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          active-class="text-white bg-gray-800"
        >
          <i class="fas fa-circle-info mr-1.5 text-xs" />About
        </RouterLink>
      </div>

      <!-- Auth section -->
      <div class="flex items-center gap-3">
        <template v-if="auth.isLoggedIn">
          <span class="hidden sm:flex items-center gap-2 text-sm text-gray-400">
            <span class="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">
              {{ auth.email?.charAt(0).toUpperCase() }}
            </span>
            {{ auth.email }}
          </span>
          <button
            @click="logout"
            class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <i class="fas fa-right-from-bracket text-xs" />
            Logout
          </button>
        </template>
        <template v-else>
          <RouterLink
            to="/login"
            class="px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-gray-800 transition-colors"
          >
            Login
          </RouterLink>
          <RouterLink
            to="/register"
            class="px-4 py-2 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors"
          >
            Sign Up
          </RouterLink>
        </template>
      </div>

    </div>
  </nav>
</template>
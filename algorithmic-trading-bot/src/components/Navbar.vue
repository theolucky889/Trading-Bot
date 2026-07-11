<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const authEmail = ref(localStorage.getItem('auth_email') || '')
const isLoggedIn = computed(() => !!authEmail.value)

// Keep the logged-in indicator in sync when navigating (covers login/logout).
watch(
  () => route.fullPath,
  () => {
    authEmail.value = localStorage.getItem('auth_email') || ''
  }
)

onMounted(() => {
  authEmail.value = localStorage.getItem('auth_email') || ''
})

function logout() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('auth_email')
  authEmail.value = ''
  router.push('/')
}

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/trade', label: 'Trade' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/backtest', label: 'Backtest' },
  { to: '/screener', label: 'Screener' },
  { to: '/plan', label: 'Plan' },
  { to: '/settings', label: 'Settings' },
  { to: '/about', label: 'About' }
]

const linkClass = (to) => {
  // Exact match for the dashboard root; prefix match for the rest.
  const active = to === '/' ? route.path === '/' : route.path.startsWith(to)
  return active ? 'text-indigo-400 font-semibold' : 'hover:text-gray-300'
}
</script>

<template>
  <nav class="bg-gray-800 text-white p-4">
    <div class="container mx-auto flex justify-between items-center">
      <RouterLink to="/" class="text-xl font-bold">Trading Bot</RouterLink>
      <div class="flex items-center space-x-4">
        <RouterLink v-for="l in links" :key="l.to" :to="l.to" :class="linkClass(l.to)">
          {{ l.label }}
        </RouterLink>

        <template v-if="isLoggedIn">
          <span class="text-sm text-gray-400 hidden sm:inline">{{ authEmail }}</span>
          <button
            @click="logout"
            class="rounded-lg bg-indigo-600 hover:bg-indigo-700 px-3 py-1 text-sm transition-colors"
          >
            Logout
          </button>
        </template>
        <template v-else>
          <RouterLink to="/login" :class="linkClass('/login')">Login</RouterLink>
          <RouterLink to="/register" :class="linkClass('/register')">Register</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 flex items-center justify-center px-4">
    <div class="w-full max-w-md">

      <!-- Card -->
      <div class="bg-gray-800/60 backdrop-blur border border-gray-700/50 rounded-2xl shadow-2xl p-8">

        <!-- Header -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-14 h-14 bg-indigo-600/20 rounded-2xl mb-4">
            <i class="fas fa-robot text-indigo-400 text-2xl" />
          </div>
          <h1 class="text-2xl font-bold text-white">Welcome back</h1>
          <p class="text-gray-400 text-sm mt-1">Sign in to your AlgoHouse account</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="login" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
            <div class="relative">
              <i class="fas fa-envelope absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
              <input
                v-model="email"
                type="email"
                required
                placeholder="you@example.com"
                class="w-full bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
            <div class="relative">
              <i class="fas fa-lock absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="••••••••"
                class="w-full bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl pl-10 pr-10 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition"
              >
                <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'" class="text-sm" />
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMessage" class="flex items-start gap-2.5 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
            <i class="fas fa-circle-exclamation mt-0.5 flex-shrink-0" />
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-xl py-3 text-sm transition-colors mt-2"
          >
            <i v-if="loading" class="fas fa-circle-notch fa-spin" />
            <span>{{ loading ? 'Signing in…' : 'Sign In' }}</span>
          </button>
        </form>

        <!-- Footer -->
        <p class="text-center text-sm text-gray-400 mt-6">
          Don't have an account?
          <RouterLink to="/register" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Create one
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const errorMessage = ref('')
const loading = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function login() {
  errorMessage.value = ''
  loading.value = true

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      errorMessage.value = data?.detail || data?.message || 'An error occurred during login.'
      return
    }

    if (data?.token) {
      auth.setAuth(data.token, email.value)
    }

    router.push({ name: 'dashboard' })
  } catch {
    errorMessage.value = 'Could not connect to the server. Is the backend running?'
  } finally {
    loading.value = false
  }
}
</script>
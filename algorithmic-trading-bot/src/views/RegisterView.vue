<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 flex items-center justify-center px-4">
    <div class="w-full max-w-md">

      <!-- Card -->
      <div class="bg-gray-800/60 backdrop-blur border border-gray-700/50 rounded-2xl shadow-2xl p-8">

        <!-- Header -->
        <div class="text-center mb-8">
          <div class="inline-flex items-center justify-center w-14 h-14 bg-indigo-600/20 rounded-2xl mb-4">
            <i class="fas fa-user-plus text-indigo-400 text-2xl" />
          </div>
          <h1 class="text-2xl font-bold text-white">Create an account</h1>
          <p class="text-gray-400 text-sm mt-1">Start trading smarter with AlgoHouse</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="register" class="space-y-4">
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
                minlength="8"
                placeholder="At least 8 characters"
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

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1.5">Confirm Password</label>
            <div class="relative">
              <i class="fas fa-lock absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
              <input
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="Repeat your password"
                class="w-full bg-gray-900/70 border border-gray-700 text-white placeholder-gray-500 rounded-xl pl-10 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                :class="{ 'border-red-500 focus:ring-red-500': confirmPassword && password !== confirmPassword }"
              />
            </div>
            <p v-if="confirmPassword && password !== confirmPassword" class="text-red-400 text-xs mt-1.5">
              Passwords do not match.
            </p>
          </div>

          <!-- Error -->
          <div v-if="errorMessage" class="flex items-start gap-2.5 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 text-sm">
            <i class="fas fa-circle-exclamation mt-0.5 flex-shrink-0" />
            {{ errorMessage }}
          </div>

          <!-- Success -->
          <div v-if="successMessage" class="flex items-start gap-2.5 bg-green-500/10 border border-green-500/30 text-green-400 rounded-xl px-4 py-3 text-sm">
            <i class="fas fa-circle-check mt-0.5 flex-shrink-0" />
            {{ successMessage }}
          </div>

          <p class="text-xs text-gray-500">
            By creating an account you agree to our
            <a href="#" class="text-indigo-400 hover:underline">Terms of Service</a> and
            <a href="#" class="text-indigo-400 hover:underline">Privacy Policy</a>.
          </p>

          <button
            type="submit"
            :disabled="loading || (!!confirmPassword && password !== confirmPassword)"
            class="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-xl py-3 text-sm transition-colors"
          >
            <i v-if="loading" class="fas fa-circle-notch fa-spin" />
            <span>{{ loading ? 'Creating account…' : 'Create Account' }}</span>
          </button>
        </form>

        <!-- Footer -->
        <p class="text-center text-sm text-gray-400 mt-6">
          Already have an account?
          <RouterLink to="/login" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
            Sign in
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const loading = ref(false)

const router = useRouter()

const register = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  loading.value = true
  try {
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    const data = await response.json().catch(() => null)

    if (response.status === 409) {
      errorMessage.value = 'This email is already registered.'
      return
    }
    if (!response.ok) {
      errorMessage.value = data?.detail || data?.message || 'An error occurred during registration.'
      return
    }

    successMessage.value = 'Account created! Redirecting to login…'
    setTimeout(() => router.push('/login'), 1500)
  } catch {
    errorMessage.value = 'Could not connect to the server. Is the backend running?'
  } finally {
    loading.value = false
  }
}
</script>
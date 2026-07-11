<template>
  <div class="login-page bg-gray-900 min-h-screen flex flex-col items-center justify-center text-white">
    <h2 class="text-3xl font-bold mb-8">Login to your account</h2>

    <form @submit.prevent="login">
      <div class="mb-4">
        <input
          type="email"
          v-model="email"
          placeholder="Email"
          required
          autocomplete="email"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div class="mb-4">
        <input
          type="password"
          v-model="password"
          placeholder="Password"
          required
          autocomplete="current-password"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <button
        type="submit"
        class="w-96 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-lg transition-colors"
      >
        Login
      </button>
    </form>

    <!-- Error Message -->
    <div v-if="errorMessage" class="mt-4 text-red-500">
      {{ errorMessage }}
    </div>

    <!-- Success banner: brief confirmation, then auto-redirect (single flow) -->
    <div v-if="success" class="mt-4 rounded-lg bg-green-900/40 border border-green-700 px-4 py-3 text-green-300">
      Login successful — redirecting…
    </div>

    <!-- Link to Register -->
    <div class="mt-4">
      <p>Don't have an account? <router-link to="/register" class="text-blue-500">Register here</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const success = ref(false)
const router = useRouter()
const route = useRoute()

async function login() {
  errorMessage.value = ''

  try {
    // ✅ Use Vite proxy (no CORS issues)
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    })

    const data = await response.json().catch(() => null)

    if (!response.ok) {
      errorMessage.value = data?.message || 'An error occurred during login.'
      return
    }

    // ✅ Save JWT token
    if (data?.token) {
      localStorage.setItem('auth_token', data.token)
      localStorage.setItem('auth_email', email.value) // optional
    }

    // Single flow: show a brief success state, then auto-redirect once.
    success.value = true
    setTimeout(redirectToDashboard, 800)
  } catch (error) {
    console.error('Login failed:', error)
    errorMessage.value = 'An error occurred during login.'
  }
}

function redirectToDashboard() {
  // Honor a redirect-back query set by the route guard; otherwise go to the dashboard.
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect) {
    router.push(redirect)
  } else {
    router.push({ name: 'dashboard' })
  }
}
</script>

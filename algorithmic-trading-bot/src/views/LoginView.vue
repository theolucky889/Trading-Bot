<template>
  <div class="login-page bg-gray-900 min-h-screen flex flex-col items-center justify-center text-white">
    <h2 class="text-3xl font-bold mb-8">Login to your account</h2>

    <form @submit.prevent="login">
      <div class="mb-4">
        <input
          type="email"
          v-model="email"
          placeholder="Email"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div class="mb-4">
        <input
          type="password"
          v-model="password"
          placeholder="Password"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <button type="submit" class="btn-futuristic">Login</button>
    </form>

    <!-- Error Message -->
    <div v-if="errorMessage" class="mt-4 text-red-500">
      {{ errorMessage }}
    </div>

    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div class="bg-white text-black p-6 rounded-lg shadow-lg">
        <h3 class="text-xl font-bold mb-4">Login Successful!</h3>
        <p>You will be redirected to the dashboard shortly.</p>
        <button @click="redirectToDashboard" class="mt-4 btn-futuristic">Go to Dashboard</button>
      </div>
    </div>

    <!-- Link to Register -->
    <div class="mt-4">
      <p>Don't have an account? <router-link to="/register" class="text-blue-500">Register here</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const showSuccessModal = ref(false)
const router = useRouter()

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

    showSuccessModal.value = true
    setTimeout(redirectToDashboard, 800) // shorter feels better
  } catch (error) {
    console.error('Login failed:', error)
    errorMessage.value = 'An error occurred during login.'
  }
}

function redirectToDashboard() {
  showSuccessModal.value = false
  // ✅ Your router dashboard path is '/'
  router.push({ name: 'dashboard' }) // or router.push('/')
}
</script>

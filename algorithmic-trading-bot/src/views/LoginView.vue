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
  console.log('Login function called')
  console.log('Email:', email.value)
  console.log('Password:', password.value)

  try {
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    })

    console.log('Response status:', response.status)

    if (response.ok) {
      console.log('Login successful!')
      errorMessage.value = ''
      showSuccessModal.value = true
      setTimeout(redirectToDashboard, 3000) // Automatically redirect after 3 seconds
    } else {
      const errorData = await response.json()
      console.error('Login error:', errorData.message)
      errorMessage.value = errorData.message || 'An error occurred during login.'
    }
  } catch (error) {
    console.error('Login failed:', error)
    errorMessage.value = 'An error occurred during login.'
  }
}

function redirectToDashboard() {
  showSuccessModal.value = false
  router.push('/dashboard')
}
</script> 
<template>
  <div
    class="register-page bg-gray-900 min-h-screen flex flex-col items-center justify-center text-white"
  >
    <h2 class="text-3xl font-bold mb-8">Create your account</h2>

    <form @submit.prevent="register">
      <!-- Use @submit.prevent to prevent default form submission -->
      <div class="mb-4 relative">
        <input
          type="email"
          v-model="email"
          placeholder="Email"
          required
          autocomplete="email"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          @click="email = ''"
          class="absolute right-4 top-4 text-gray-500 hover:text-gray-400"
          v-if="email"
        >
          <i class="fas fa-times"></i>
          <!-- Use an icon library (like Font Awesome) or replace with an SVG -->
        </button>
      </div>
      <div class="mb-4 relative">
        <input
          type="password"
          v-model="password"
          placeholder="Password"
          required
          minlength="8"
          autocomplete="new-password"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <button
          type="button"
          @click="password = ''"
          class="absolute right-4 top-4 text-gray-500 hover:text-gray-400"
          v-if="password"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="mb-4 relative">
        <input
          type="password"
          v-model="confirmPassword"
          placeholder="Confirm password"
          required
          minlength="8"
          autocomplete="new-password"
          class="w-96 bg-gray-800 border border-gray-700 p-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          @click="confirmPassword = ''"
          class="absolute right-4 top-4 text-gray-500 hover:text-gray-400"
          v-if="confirmPassword"
        >
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="mb-6 text-sm">
        By creating an account, you agree to our
        <a href="#" class="text-blue-500">Terms of Service</a> and
        <a href="#" class="text-blue-500">Privacy Policy</a>
      </div>

      <div class="mb-4">
        This site is protected by reCAPTCHA and the Google
        <a href="#" class="text-blue-500">Privacy Policy</a> and
        <a href="#" class="text-blue-500">Terms of Service</a> apply.
      </div>

      <button
        type="submit"
        class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-8 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        Create account
      </button>
    </form>

    <!-- Success banner: brief confirmation, then auto-redirect (single flow) -->
    <div v-if="success" class="mt-4 rounded-lg bg-green-900/40 border border-green-700 px-4 py-3 text-green-300">
      Registration successful — redirecting to login…
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="mt-4 text-red-500">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const success = ref(false)
const errorMessage = ref('')
const router = useRouter()

const register = async () => {
  try {
    // 1. Client-side validation
    errorMessage.value = ''

    if (!email.value.trim() || !password.value) {
      errorMessage.value = 'Please enter both an email and a password.'
      return
    }

    if (password.value.length < 8) {
      errorMessage.value = 'Password must be at least 8 characters.'
      return
    }

    if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Passwords do not match.'
      return
    }

    // 2. Send registration request via the dev proxy (→ Express :3000)
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value,
        password: password.value,
      }),
    })

    // 3. Handle response
    if (response.ok) {
      // Registration successful – redirect or show success message
      errorMessage.value = ''
      success.value = true
      setTimeout(redirectToLogin, 1200)
    } else if (response.status === 409) {
      errorMessage.value = 'This email is already registered. Please use a different email.'
    } else {
      const errorData = await response.json()
      errorMessage.value = errorData.message || 'An error occurred during registration.'
    }
  } catch (error) {
    // Handle any network or other errors
    console.error('Registration failed:', error)
    errorMessage.value = 'An error occurred during registration.'
  }
}

function redirectToLogin() {
  router.push('/login')
}
</script>

import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const email = ref<string | null>(localStorage.getItem('auth_email'))

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(newToken: string, userEmail: string) {
    token.value = newToken
    email.value = userEmail
    localStorage.setItem('auth_token', newToken)
    localStorage.setItem('auth_email', userEmail)
  }

  function logout() {
    token.value = null
    email.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_email')
  }

  return { token, email, isLoggedIn, setAuth, logout }
})
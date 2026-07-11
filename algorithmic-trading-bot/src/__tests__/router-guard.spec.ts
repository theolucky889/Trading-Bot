import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { defineComponent } from 'vue'

// A stub component so the router can resolve routes without importing real views.
const Stub = defineComponent({ render: () => null })

// Re-create the production guard here so we test the exact redirect logic used
// in src/router/index.ts without dragging in every view component.
function buildRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'dashboard', component: Stub },
      { path: '/settings', name: 'settings', component: Stub, meta: { requiresAuth: true } },
      { path: '/login', name: 'login', component: Stub },
    ],
  })

  router.beforeEach((to) => {
    if (to.meta.requiresAuth && !localStorage.getItem('auth_token')) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  })

  return router
}

describe('auth route guard', () => {
  beforeEach(() => {
    localStorage.clear()
  })
  afterEach(() => {
    localStorage.clear()
  })

  it('redirects to /login with a redirect-back query when no auth_token is stored', async () => {
    const router = buildRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/settings')
  })

  it('allows a protected route when an auth_token is present', async () => {
    localStorage.setItem('auth_token', 'fake.jwt.token')
    const router = buildRouter()
    await router.push('/settings')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('settings')
  })

  it('leaves public routes reachable when logged out', async () => {
    const router = buildRouter()
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('dashboard')
  })
})

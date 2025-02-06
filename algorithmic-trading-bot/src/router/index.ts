import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../Dashboard.vue'
import Settings from '@/pages/Settings.vue'
;``

const routes = [
  { path: '/', component: Dashboard },
  { path: '/settings', component: Settings },
  // Add more routes here in the futues
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router

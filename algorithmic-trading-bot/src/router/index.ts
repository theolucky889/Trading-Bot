import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'
import SettingsView from '../views/SettingsView.vue'
import TradeView from '../views/TradeView.vue'
import RegisterView from '../views/RegisterView.vue'

const routes = [
  { path: '/', component: HomeView },
  { path: '/auth', component: AuthView },
  { path: '/dashboard', component: DashboardView },
  { path: '/settings', component: SettingsView },
  { path: '/trade', component: TradeView },
  { path: '/register', component: RegisterView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import TradeView from '../views/TradeView.vue'
import AnalysisView from '../views/AnalysisView.vue'
import BacktestView from '../views/BacktestView.vue'
import ScreenerView from '../views/ScreenerView.vue'
import PlanView from '../views/PlanView.vue'
import SettingsView from '../views/SettingsView.vue'
import AboutView from '../views/AboutView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/trade', name: 'trade', component: TradeView, meta: { requiresAuth: true } },
    { path: '/analysis', name: 'analysis', component: AnalysisView },
    { path: '/backtest', name: 'backtest', component: BacktestView },
    { path: '/screener', name: 'screener', component: ScreenerView },
    { path: '/plan', name: 'plan', component: PlanView },
    { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } },
    { path: '/about', name: 'about', component: AboutView },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView }
  ]
})

// Route guard: protected routes require a stored auth token.
// Redirect to /login with a redirect-back query so login can return here.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('auth_token')) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router

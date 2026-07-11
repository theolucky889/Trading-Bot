/// <reference types="vite/client" />

// Shim for SFCs without <script lang="ts"> (DashboardView, LoginView, ...)
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

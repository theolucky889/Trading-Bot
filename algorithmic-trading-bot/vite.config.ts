import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue            from '@vitejs/plugin-vue'
import vueJsx         from '@vitejs/plugin-vue-jsx'
import vueDevTools    from 'vite-plugin-vue-devtools'
import tailwindcss    from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx(), vueDevTools(), tailwindcss()],

  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },

  server: {
    proxy: {
      // All /api/* → FastAPI (backend/app.py, port 8000). Auth (register,
      // login, session, per-user sentiment history) is now served by FastAPI
      // + SQLite (backend/auth.py); the legacy Express server (server.js) is
      // no longer wired to the dev proxy.
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})

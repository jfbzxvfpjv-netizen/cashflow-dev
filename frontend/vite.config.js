// ============================================================================
// Vite — Configuración del frontend Vue.js 3
// ============================================================================
// El proxy de desarrollo redirige /api y /auth al backend FastAPI en el
// puerto 8000 para evitar problemas de CORS durante el desarrollo local.
// En producción, Nginx gestiona el proxy directamente.
// ============================================================================

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

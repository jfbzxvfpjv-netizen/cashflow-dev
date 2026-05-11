// ============================================================================
// Vite — Configuracion del frontend Vue.js 3
// ============================================================================
// El proxy de desarrollo redirige /api y /auth al backend FastAPI en el
// puerto 8000 para evitar problemas de CORS durante el desarrollo local.
// En produccion, Nginx gestiona el proxy directamente.
//
// resolve.alias['WebSdk']: el paquete @digitalpersona/devices hace
// internamente `import 'WebSdk'` (side-effect, sin destructuring) para
// satisfacer al bundler. La WebSdk real se carga via <script> en index.html
// y queda en window.WebSdk. El alias apunta a un shim vacio que solo
// resuelve el import sin afectar runtime.
// ============================================================================
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'WebSdk': fileURLToPath(new URL('./src/lib/websdk-shim.js', import.meta.url))
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

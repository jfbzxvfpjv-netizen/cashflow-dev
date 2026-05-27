<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">Gestión de Flujo de Caja</h1>
        <p class="text-sm text-gray-500 mt-1">Bata — Malabo</p>
      </div>
      <div class="bg-white rounded-lg shadow-lg p-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">Iniciar sesión</h2>
        <div v-if="sessionExpired" class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800 flex items-start gap-2">
          <span class="text-yellow-600">⚠</span>
          <span>La sesión ha expirado. Inicie sesión de nuevo.</span>
        </div>
        <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-start gap-2" role="alert">
          <span class="text-red-600 font-bold">✕</span>
          <span>{{ errorMessage }}</span>
        </div>
        <form @submit.prevent="handleLogin" novalidate>
          <div class="mb-4">
            <label for="username" class="block text-sm font-medium text-gray-600 mb-1">Usuario</label>
            <input id="username" ref="usernameInput" v-model="username" @input="clearError"
              type="text" autocomplete="username" required :disabled="loading"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="Nombre de usuario" />
          </div>
          <div class="mb-6">
            <label for="password" class="block text-sm font-medium text-gray-600 mb-1">Contraseña</label>
            <div class="relative">
              <input id="password" v-model="password" @input="clearError"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password" required :disabled="loading"
                class="w-full px-3 py-2 pr-12 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 relative"
                placeholder="Contraseña" />
              <button type="button" @click.prevent="showPassword = !showPassword" @mousedown.prevent="" tabindex="-1" :disabled="loading"
                class="absolute right-0 top-0 h-full px-3 text-gray-500 hover:text-gray-700 flex items-center z-10 cursor-pointer"
                :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                :title="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'">
                <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
                  <circle cx="12" cy="12" r="3" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.94 17.94A10.06 10.06 0 0112 19c-7 0-11-7-11-7a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 7 11 7a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22" />
                </svg>
              </button>
            </div>
          </div>
          <button type="submit" :disabled="loading || !username || !password"
            class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2">
            <svg v-if="loading" class="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
            </svg>
            <span>{{ loading ? 'Accediendo...' : 'Acceder' }}</span>
          </button>
        </form>
      </div>
      <p class="text-center text-xs text-gray-400 mt-4">R2i Network — Uso interno restringido</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter(); const route = useRoute(); const auth = useAuthStore()
const username = ref(''); const password = ref(''); const loading = ref(false); const errorMessage = ref('')
const sessionExpired = computed(() => route.query.expired === '1')

onMounted(() => { if (auth.isAuthenticated) router.push({ name: 'dashboard' }) })

async function handleLogin() {
  loading.value = true; errorMessage.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push(route.query.redirect || '/dashboard')
  } catch (err) {
    const s = err.response?.status
    if (s === 429) errorMessage.value = 'Demasiados intentos. Espere 10 minutos.'
    else if (s === 401) errorMessage.value = 'Usuario o contraseña incorrectos.'
    else if (s === 403) errorMessage.value = err.response?.data?.detail || 'Cuenta desactivada.'
    else errorMessage.value = 'Error de conexión con el servidor.'
  } finally { loading.value = false }
}
</script>

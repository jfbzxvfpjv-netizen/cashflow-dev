<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">Gestión de Flujo de Caja</h1>
        <p class="text-sm text-gray-500 mt-1">Bata — Malabo</p>
      </div>
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">Iniciar sesión</h2>
        <div v-if="sessionExpired" class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
          La sesión ha expirado. Inicie sesión de nuevo.
        </div>
        <div v-if="errorMessage" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {{ errorMessage }}
        </div>
        <form @submit.prevent="handleLogin">
          <div class="mb-4">
            <label for="username" class="block text-sm font-medium text-gray-600 mb-1">Usuario</label>
            <input id="username" v-model="username" type="text" autocomplete="username" required :disabled="loading"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="Nombre de usuario" />
          </div>
          <div class="mb-6">
            <label for="password" class="block text-sm font-medium text-gray-600 mb-1">Contraseña</label>
            <input id="password" v-model="password" type="password" autocomplete="current-password" required :disabled="loading"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              placeholder="Contraseña" />
          </div>
          <button type="submit" :disabled="loading || !username || !password"
            class="w-full py-2 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors">
            <span v-if="loading">Accediendo...</span>
            <span v-else>Acceder</span>
          </button>
        </form>
      </div>
      <p class="text-center text-xs text-gray-400 mt-4">Uso interno — Acceso restringido</p>
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

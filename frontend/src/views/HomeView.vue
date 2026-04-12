<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center space-y-4">
      <h1 class="text-3xl font-bold text-gray-800">Flujo de Caja</h1>
      <p class="text-gray-500">Infraestructura operativa — M2 completado</p>
      <div class="flex gap-4 justify-center text-sm">
        <span
          class="px-3 py-1 rounded-full"
          :class="backendOk ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
        >
          Backend: {{ backendOk ? 'OK' : 'sin conexión' }}
        </span>
        <span class="px-3 py-1 rounded-full bg-green-100 text-green-700">
          Frontend: OK
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const backendOk = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/api/v1/health')
    backendOk.value = res.ok
  } catch {
    backendOk.value = false
  }
})
</script>

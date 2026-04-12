<template>
  <div v-if="isDev" class="bg-red-600 text-white text-center text-xs font-bold py-1 sticky top-0 z-50">
    ⚠️ ENTORNO DE DESARROLLO — Los datos pueden resetearse en cualquier momento
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const isDev = ref(false)
onMounted(async () => {
  try { const r = await fetch('/api/health'); const d = await r.json(); isDev.value = d.env === 'development' } catch {}
})
</script>

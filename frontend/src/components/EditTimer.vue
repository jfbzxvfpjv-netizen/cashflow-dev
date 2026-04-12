<!--
  Módulo 6 — EditTimer.vue
  Contador regresivo que muestra el tiempo restante de la ventana de edición.
  Al llegar a cero deshabilita los controles de edición sin recargar la página.
-->
<template>
  <div v-if="remaining > 0" class="inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-mono"
       :class="remaining < 120 ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'">
    <span>⏱</span>
    <span>{{ formatted }}</span>
  </div>
  <div v-else class="inline-flex items-center gap-1 px-2 py-1 rounded text-sm bg-gray-100 text-gray-500">
    <span>🔒</span>
    <span>Edición bloqueada</span>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  secondsRemaining: { type: Number, default: 0 }
})
const emit = defineEmits(['expired'])

const remaining = ref(props.secondsRemaining)
let timer = null

const formatted = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})

function startTimer() {
  if (timer) clearInterval(timer)
  remaining.value = props.secondsRemaining
  if (remaining.value <= 0) return
  timer = setInterval(() => {
    remaining.value--
    if (remaining.value <= 0) {
      clearInterval(timer)
      emit('expired')
    }
  }, 1000)
}

watch(() => props.secondsRemaining, () => startTimer())
onMounted(() => startTimer())
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <!-- Cabecera con nombre y badge si es provisional -->
    <div class="flex items-center justify-between mb-3">
      <div class="text-sm">
        <span class="text-gray-600">Firma de</span>
        <strong class="ml-1 text-gray-800">{{ signerName || '?' }}</strong>
      </div>
      <span v-if="provisional"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 border border-amber-300">
        Firma provisional
      </span>
    </div>

    <!-- Mensaje si es provisional -->
    <p v-if="provisional"
       class="mb-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1">
      Este empleado no tiene huella enrolada. La firma quedara marcada como provisional para revision posterior.
    </p>

    <!-- Canvas -->
    <div class="relative">
      <canvas ref="canvasEl"
              :width="canvasWidth"
              :height="canvasHeight"
              class="w-full border border-gray-300 rounded bg-white touch-none"
              :class="signed ? 'opacity-60' : 'cursor-crosshair'"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
              @touchstart.prevent="startDrawingTouch"
              @touchmove.prevent="drawTouch"
              @touchend.prevent="stopDrawing" />
      <!-- Marca de agua visual cuando esta firmado -->
      <div v-if="signed"
           class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <span class="bg-green-600 text-white text-sm font-medium px-3 py-1 rounded shadow">
          ✓ Firma capturada
        </span>
      </div>
      <!-- Placeholder cuando esta vacio -->
      <div v-if="!hasInk && !signed"
           class="absolute inset-0 flex items-center justify-center pointer-events-none text-gray-300 text-sm italic">
        Firma aqui con el raton o el dedo
      </div>
    </div>

    <!-- Botones -->
    <div class="flex justify-end gap-2 mt-3">
      <!-- Estado pre-confirmacion: Limpiar + Confirmar -->
      <template v-if="!signed">
        <button @click="clearCanvas"
                :disabled="!hasInk"
                :class="[
                  'px-3 py-1.5 text-sm rounded transition-colors',
                  !hasInk
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                ]">
          Limpiar
        </button>
        <button @click="confirmSignature"
                :disabled="!hasInk"
                :class="[
                  'px-3 py-1.5 text-sm rounded transition-colors font-medium',
                  !hasInk
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                ]">
          Confirmar firma
        </button>
      </template>
      <!-- Estado post-confirmacion: Re-firmar -->
      <template v-else>
        <button @click="resign"
                class="px-3 py-1.5 text-sm rounded transition-colors font-medium bg-indigo-600 hover:bg-indigo-700 text-white">
          Re-firmar (descartar y volver a empezar)
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  signerName: { type: String, default: '' },
  provisional: { type: Boolean, default: false },
  canvasWidth: { type: Number, default: 600 },
  canvasHeight: { type: Number, default: 180 },
})

const emit = defineEmits(['signed', 'reset'])

const canvasEl = ref(null)
const ctx = ref(null)
const drawing = ref(false)
const hasInk = ref(false)
const signed = ref(false)
const lastX = ref(0)
const lastY = ref(0)

function getCanvasCoords(clientX, clientY) {
  const rect = canvasEl.value.getBoundingClientRect()
  const scaleX = canvasEl.value.width / rect.width
  const scaleY = canvasEl.value.height / rect.height
  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY,
  }
}

function startDrawing(e) {
  if (signed.value) return
  drawing.value = true
  const { x, y } = getCanvasCoords(e.clientX, e.clientY)
  lastX.value = x
  lastY.value = y
}

function draw(e) {
  if (!drawing.value || signed.value) return
  const { x, y } = getCanvasCoords(e.clientX, e.clientY)
  ctx.value.beginPath()
  ctx.value.moveTo(lastX.value, lastY.value)
  ctx.value.lineTo(x, y)
  ctx.value.stroke()
  lastX.value = x
  lastY.value = y
  hasInk.value = true
}

function stopDrawing() {
  drawing.value = false
}

function startDrawingTouch(e) {
  if (signed.value) return
  drawing.value = true
  const touch = e.touches[0]
  const { x, y } = getCanvasCoords(touch.clientX, touch.clientY)
  lastX.value = x
  lastY.value = y
}

function drawTouch(e) {
  if (!drawing.value || signed.value) return
  const touch = e.touches[0]
  const { x, y } = getCanvasCoords(touch.clientX, touch.clientY)
  ctx.value.beginPath()
  ctx.value.moveTo(lastX.value, lastY.value)
  ctx.value.lineTo(x, y)
  ctx.value.stroke()
  lastX.value = x
  lastY.value = y
  hasInk.value = true
}

function clearCanvas() {
  if (signed.value) return
  ctx.value.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  hasInk.value = false
}

function confirmSignature() {
  if (!hasInk.value || signed.value) return
  signed.value = true
  const dataUrl = canvasEl.value.toDataURL('image/png')
  const imageB64 = dataUrl.split(',')[1]
  emit('signed', {
    imageB64,
    signerName: props.signerName,
    provisional: props.provisional,
  })
}

function reset() {
  signed.value = false
  hasInk.value = false
  if (ctx.value) {
    ctx.value.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  }
}

function resign() {
  reset()
  emit('reset')
}

defineExpose({ reset })

onMounted(() => {
  const canvas = canvasEl.value
  ctx.value = canvas.getContext('2d')
  ctx.value.strokeStyle = '#1e3a8a'
  ctx.value.lineWidth = 2
  ctx.value.lineCap = 'round'
  ctx.value.lineJoin = 'round'
})
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white rounded shadow-lg p-4 w-full max-w-lg">
      <h3 class="text-lg font-semibold mb-2">Captura de firma</h3>
      <p class="text-sm text-gray-600 mb-3">
        Firme con el ratón, dedo o lápiz digital sobre el área en blanco.
      </p>

      <div class="border-2 border-dashed border-gray-300 rounded">
        <canvas
          ref="canvas"
          class="block w-full bg-white touch-none cursor-crosshair"
          :width="canvasWidth"
          :height="canvasHeight"
          @pointerdown="startStroke"
          @pointermove="continueStroke"
          @pointerup="endStroke"
          @pointerleave="endStroke"
        ></canvas>
      </div>

      <div class="text-xs text-gray-500 mt-1" v-if="hasStrokes">
        Trazos: {{ strokeCount }} — Tiempo: {{ durationDisplay }}
      </div>

      <div class="flex justify-between mt-4 gap-2">
        <button
          @click="clearCanvas"
          class="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          :disabled="!hasStrokes"
        >
          Limpiar
        </button>
        <div class="flex gap-2">
          <button
            @click="cancel"
            class="px-3 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
          >
            Cancelar
          </button>
          <button
            @click="confirm"
            class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300"
            :disabled="!hasStrokes"
          >
            Confirmar firma
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  signerName: { type: String, default: '' }
})

const emit = defineEmits(['cancel', 'captured'])

const canvas = ref(null)
const canvasWidth = 480
const canvasHeight = 200

const drawing = ref(false)
const hasStrokes = ref(false)
const strokeCount = ref(0)
const startTimestamp = ref(null)
const lastTimestamp = ref(null)

let ctx = null
let lastX = 0
let lastY = 0

const durationDisplay = computed(() => {
  if (!startTimestamp.value || !lastTimestamp.value) return '0 ms'
  return (lastTimestamp.value - startTimestamp.value) + ' ms'
})

watch(() => props.visible, async (val) => {
  if (val) {
    await nextTick()
    initCanvas()
  }
})

function initCanvas() {
  if (!canvas.value) return
  ctx = canvas.value.getContext('2d')
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  clearCanvas()
}

function getRelativeCoords(e) {
  const rect = canvas.value.getBoundingClientRect()
  const scaleX = canvas.value.width / rect.width
  const scaleY = canvas.value.height / rect.height
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  }
}

function startStroke(e) {
  drawing.value = true
  const { x, y } = getRelativeCoords(e)
  lastX = x
  lastY = y
  if (!startTimestamp.value) startTimestamp.value = Date.now()
  strokeCount.value++
  hasStrokes.value = true
  e.preventDefault()
}

function continueStroke(e) {
  if (!drawing.value) return
  const { x, y } = getRelativeCoords(e)
  ctx.beginPath()
  ctx.moveTo(lastX, lastY)
  ctx.lineTo(x, y)
  ctx.stroke()
  lastX = x
  lastY = y
  lastTimestamp.value = Date.now()
  e.preventDefault()
}

function endStroke() {
  drawing.value = false
}

function clearCanvas() {
  if (!ctx) return
  ctx.fillStyle = '#fff'
  ctx.fillRect(0, 0, canvasWidth, canvasHeight)
  hasStrokes.value = false
  strokeCount.value = 0
  startTimestamp.value = null
  lastTimestamp.value = null
}

function cancel() {
  clearCanvas()
  emit('cancel')
}

function confirm() {
  if (!hasStrokes.value) return
  const dataUrl = canvas.value.toDataURL('image/png')
  const base64 = dataUrl.split(',')[1]
  const duration = (lastTimestamp.value && startTimestamp.value)
    ? (lastTimestamp.value - startTimestamp.value)
    : 0
  emit('captured', {
    signature_data: base64,
    width_px: canvasWidth,
    height_px: canvasHeight,
    duration_ms: duration,
    device_model: 'mouse-touch-fallback'
  })
  clearCanvas()
}
</script>

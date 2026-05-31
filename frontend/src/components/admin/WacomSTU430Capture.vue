<template>
  <div class="space-y-2">
    <!-- Estado: sin conectar -->
    <div v-if="!connected" class="border-2 border-dashed border-purple-300 rounded p-4 text-center bg-purple-50">
      <p class="text-sm text-purple-800 mb-3">
        Wacom STU-430 vía USB (WebHID). Solo Chrome/Edge/Brave.
      </p>
      <button @click="connect" :disabled="connecting"
              class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm disabled:opacity-50">
        {{ connecting ? 'Conectando...' : 'Conectar Wacom STU-430' }}
      </button>
      <p v-if="connectError" class="text-sm text-red-600 mt-2">{{ connectError }}</p>
      <p v-if="!webhidSupported" class="text-xs text-orange-700 mt-2">
        ⚠ WebHID no soportado en este navegador
      </p>
    </div>

    <!-- Estado: conectada, capturando -->
    <div v-else>
      <div class="text-xs text-green-700 mb-2 flex items-center justify-between">
        <span>✓ Conectada a {{ deviceName }} ({{ tabletWidth }}×{{ tabletHeight }})</span>
        <button v-if="!signed" @click="disconnect" class="text-xs text-gray-500 hover:underline">desconectar</button>
      </div>

      <canvas
        ref="canvasEl"
        :width="canvasWidth"
        :height="canvasHeight"
        class="border-2 border-gray-300 rounded bg-white block"
        style="touch-action: none;"
      ></canvas>

      <div class="flex gap-2 mt-2">
        <button v-if="!signed" @click="clearCanvas" :disabled="!hasInk"
                class="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50">
          Limpiar
        </button>
        <button v-if="!signed" @click="confirmSignature" :disabled="!hasInk"
                class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50">
          Confirmar firma
        </button>
        <button v-if="signed" @click="resign"
                class="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50">
          Volver a firmar
        </button>
        <span v-if="signed" class="text-sm text-green-700 self-center ml-2">✓ Firma capturada</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  signerName: { type: String, default: '' },
  provisional: { type: Boolean, default: false },
  canvasWidth: { type: Number, default: 600 },
  canvasHeight: { type: Number, default: 240 },  // ratio cercano a 8:5 del STU-430
})
const emit = defineEmits(['signed', 'reset'])

const canvasEl = ref(null)
const connected = ref(false)
const connecting = ref(false)
const connectError = ref('')
const signed = ref(false)
const hasInk = ref(false)
const deviceName = ref('')
const tabletWidth = ref(9600)
const tabletHeight = ref(6000)
const webhidSupported = ref(true)

let device = null
let ctx = null
let lastX = null, lastY = null
let inputListener = null

onMounted(() => {
  if (!('hid' in navigator)) {
    webhidSupported.value = false
  }
})

onUnmounted(() => {
  disconnect()
})

async function connect() {
  connectError.value = ''
  if (!('hid' in navigator)) {
    connectError.value = 'WebHID no soportado en este navegador'
    return
  }
  connecting.value = true
  try {
    const devs = await navigator.hid.requestDevice({ filters: [{ vendorId: 0x056A }] })
    if (!devs.length) {
      connectError.value = 'No se seleccionó dispositivo'
      return
    }
    device = devs[0]
    if (!device.opened) await device.open()
    deviceName.value = device.productName

    // Leer capabilities (feature report 0x09)
    try {
      const dv = await device.receiveFeatureReport(0x09)
      const tw = dv.getUint16(1)
      const th = dv.getUint16(3)
      if (tw > 1000 && th > 1000) {
        tabletWidth.value = tw
        tabletHeight.value = th
      }
    } catch (e) {
      // Si falla, mantenemos defaults 9600x6000
      console.warn('No se pudieron leer capabilities:', e.message)
    }

    connected.value = true
    // Inicializar canvas en el siguiente tick
    await new Promise(r => requestAnimationFrame(r))
    initCanvas()
    attachListener()
    await clearTabletLCD()
  } catch (e) {
    connectError.value = 'Error: ' + (e.message || e)
  } finally {
    connecting.value = false
  }
}

function initCanvas() {
  if (!canvasEl.value) return
  ctx = canvasEl.value.getContext('2d')
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#000'
  ctx.lineWidth = 2
  ctx.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  hasInk.value = false
  signed.value = false
  lastX = null; lastY = null
}

function attachListener() {
  if (!device) return
  inputListener = (event) => {
    if (event.reportId !== 0x01 || signed.value) return
    const data = new Uint8Array(event.data.buffer)
    if (data.length < 6) return
    const statusByte = data[0]
    const x = (data[2] << 8) | data[3]
    const y = (data[4] << 8) | data[5]
    const touching = (statusByte & 0x80) !== 0
    if (touching && x > 0 && y > 0) {
      const cx = (x / tabletWidth.value) * canvasEl.value.width
      const cy = (y / tabletHeight.value) * canvasEl.value.height
      if (lastX !== null && ctx) {
        ctx.beginPath()
        ctx.moveTo(lastX, lastY)
        ctx.lineTo(cx, cy)
        ctx.stroke()
        hasInk.value = true
      }
      lastX = cx; lastY = cy
    } else {
      lastX = null; lastY = null
    }
  }
  device.addEventListener('inputreport', inputListener)
}

function clearCanvas() {
  if (!ctx || !canvasEl.value) return
  ctx.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height)
  hasInk.value = false
  lastX = null; lastY = null
  clearTabletLCD()
}

async function clearTabletLCD() {
  if (!device) return
  try {
    await device.sendFeatureReport(0x20, new Uint8Array([0]))
  } catch (e) {
    console.warn('clearScreen STU-430 fallo:', e.message)
  }
}

function confirmSignature() {
  if (!hasInk.value || signed.value || !canvasEl.value) return
  signed.value = true
  const dataUrl = canvasEl.value.toDataURL('image/png')
  const imageB64 = dataUrl.split(',')[1]
  emit('signed', {
    imageB64,
    signerName: props.signerName,
    provisional: props.provisional,
  })
  clearTabletLCD()
}

function resign() {
  clearCanvas()
  signed.value = false
  emit('reset')
}

async function disconnect() {
  if (device && inputListener) {
    try { device.removeEventListener('inputreport', inputListener) } catch (e) {}
  }
  if (device && device.opened) {
    try { await device.close() } catch (e) {}
  }
  device = null
  inputListener = null
  connected.value = false
  signed.value = false
  hasInk.value = false
}

function reset() {
  clearCanvas()
  signed.value = false
}

defineExpose({ reset })
</script>

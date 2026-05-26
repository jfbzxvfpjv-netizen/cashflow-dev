<template>
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[95vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800">
          Enrolar huella — {{ employeeName || 'Empleado #' + employeeId }}
        </h2>
        <button @click="handleClose" class="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
      </div>

      <!-- Body -->
      <div class="p-6">
        <!-- Paso 1: seleccionar dedo -->
        <div v-if="step === 'select-finger'" class="space-y-4">
          <p class="text-sm text-gray-700">Selecciona el dedo a enrolar:</p>
          <div class="grid grid-cols-2 gap-3">
            <button
              v-for="finger in ALL_FINGERS"
              :key="finger.code"
              @click="selectFinger(finger.code)"
              :disabled="isAlreadyEnrolled(finger.code)"
              :class="[
                'p-3 rounded-lg border-2 text-left transition-colors',
                isAlreadyEnrolled(finger.code)
                  ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-white border-gray-300 hover:border-indigo-500 hover:bg-indigo-50'
              ]"
            >
              <div class="font-medium">{{ finger.label }}</div>
              <div v-if="isAlreadyEnrolled(finger.code)" class="text-xs text-amber-600 mt-1">
                Ya enrolado
              </div>
              <div v-else class="text-xs text-gray-500 mt-1 font-mono">{{ finger.code }}</div>
            </button>
          </div>
        </div>

        <!-- Paso 2: capturar 4 muestras -->
        <div v-else-if="step === 'capturing'" class="space-y-4">
          <div class="flex items-center justify-between text-sm">
            <span class="text-gray-700">
              Dedo: <strong>{{ fingerLabel(selectedFinger) }}</strong>
            </span>
            <button
              @click="cancelEnrolment"
              class="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              Cambiar dedo
            </button>
          </div>

          <!-- Barra de progreso 4 segmentos -->
          <div class="grid grid-cols-4 gap-2">
            <div
              v-for="i in 4"
              :key="i"
              class="h-2 rounded transition-colors"
              :class="i - 1 < captures.length
                ? 'bg-green-500'
                : (i - 1 === currentCaptureIndex ? 'bg-indigo-400' : 'bg-gray-200')"
            />
          </div>

          <!-- Capture box activa, key fuerza remontaje entre capturas -->
          <FingerprintCaptureBox
            :key="'capture-' + currentCaptureIndex"
            :label="`Captura ${currentCaptureIndex + 1} de 4`"
            :min-quality="35"
            @captured="onSampleCaptured"
            @failed="onCaptureFailed"
          />

          <!-- Resumen de capturas ya OK -->
          <div v-if="captures.length > 0" class="bg-gray-50 rounded p-3">
            <div class="text-xs font-semibold text-gray-600 mb-2">Capturas aceptadas:</div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div
                v-for="(c, i) in captures"
                :key="i"
                class="bg-white border border-green-200 rounded p-2 flex justify-between"
              >
                <span class="text-green-700 font-medium">#{{ i + 1 }} ✓</span>
                <span class="text-gray-600">Q{{ c.quality }} · M{{ c.minutiae }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Paso 3: enviando al backend -->
        <div v-else-if="step === 'submitting'" class="space-y-4 text-center py-8">
          <div class="text-4xl mb-2 animate-pulse">⏳</div>
          <p class="text-gray-700">Enrolando huella en el sistema...</p>
          <p class="text-xs text-gray-500">Procesando 4 plantillas con SourceAFIS</p>
        </div>

        <!-- Paso 4: completado -->
        <div v-else-if="step === 'done'" class="space-y-4 text-center py-8">
          <div class="text-5xl mb-2">✓</div>
          <p class="text-green-700 font-semibold text-lg">Huella enrolada correctamente</p>
          <p class="text-sm text-gray-600">
            Dedo <strong>{{ fingerLabel(selectedFinger) }}</strong> enrolado con 4 plantillas.
          </p>
        </div>

        <!-- Error visible en todos los pasos donde aplique -->
        <div v-if="submitError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <div class="font-medium mb-1">Error en el enrolment</div>
          <div>{{ submitError }}</div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <button
          v-if="step !== 'done' && step !== 'submitting'"
          @click="handleClose"
          class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded transition-colors"
        >
          Cancelar
        </button>
        <button
          v-if="step === 'done'"
          @click="handleClose"
          class="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors font-medium"
        >
          Cerrar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../../services/api'
import FingerprintCaptureBox from './FingerprintCaptureBox.vue'

const props = defineProps({
  employeeId: { type: Number, required: true },
  employeeName: { type: String, default: '' },
  existingFingers: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'enrolled'])

// Catalogo de dedos alineado con backend VALID_FINGER_POSITIONS
const ALL_FINGERS = [
  { code: 'right_thumb',  label: 'Pulgar D' },
  { code: 'right_index',  label: 'Indice D' },
  { code: 'right_middle', label: 'Corazon D' },
  { code: 'right_ring',   label: 'Anular D' },
  { code: 'right_pinky',  label: 'Menique D' },
  { code: 'left_thumb',   label: 'Pulgar I' },
  { code: 'left_index',   label: 'Indice I' },
  { code: 'left_middle',  label: 'Corazon I' },
  { code: 'left_ring',    label: 'Anular I' },
  { code: 'left_pinky',   label: 'Menique I' },
]

const step = ref('select-finger')
const selectedFinger = ref(null)
const captures = ref([])
const submitError = ref(null)

const currentCaptureIndex = computed(() => captures.value.length)

function isAlreadyEnrolled(code) {
  return props.existingFingers.includes(code)
}

function fingerLabel(code) {
  const f = ALL_FINGERS.find(x => x.code === code)
  return f ? f.label : code
}

function selectFinger(code) {
  if (isAlreadyEnrolled(code)) return
  selectedFinger.value = code
  captures.value = []
  submitError.value = null
  step.value = 'capturing'
}

function cancelEnrolment() {
  selectedFinger.value = null
  captures.value = []
  submitError.value = null
  step.value = 'select-finger'
}

function onSampleCaptured({ imageB64, quality, minutiae }) {
  captures.value.push({ imageB64, quality, minutiae })
  if (captures.value.length === 4) {
    submitEnrolment()
  }
}

function onCaptureFailed(msg) {
  submitError.value = msg
}

async function submitEnrolment() {
  step.value = 'submitting'
  submitError.value = null
  try {
    await api.post('/fingerprints/enroll', {
      employee_id: props.employeeId,
      finger_position: selectedFinger.value,
      images_b64: captures.value.map(c => c.imageB64),
    })
    step.value = 'done'
    emit('enrolled', {
      employee_id: props.employeeId,
      finger_position: selectedFinger.value,
    })
  } catch (err) {
    submitError.value = err.response?.data?.detail || err.message || 'Error desconocido'
    captures.value = []
    step.value = 'capturing'
  }
}

function handleClose() {
  emit('close')
}
</script>

<!--
  Módulo 6 — TransactionNewView.vue
  Formulario completo para registrar una transacción nueva: categoría, subcategoría,
  tipo, importe, concepto, proyecto/obra, contraparte y vehículo.
-->
<template>
  <div class="p-4 max-w-3xl mx-auto">
    <h1 class="text-xl font-bold mb-4">Nueva Transacción</h1>

    <div v-if="error" class="bg-red-100 text-red-700 p-3 rounded mb-4 text-sm">{{ error }}</div>
    <div v-if="success" class="bg-green-100 text-green-700 p-3 rounded mb-4 text-sm">
      Transacción {{ success }} registrada correctamente.
      <router-link :to="`/transactions`" class="underline ml-2">Ver listado</router-link>
    </div>

    <form @submit.prevent="submit" class="bg-white rounded shadow p-4 space-y-4">
      <!-- Tipo e importe -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Tipo *</label>
          <select v-model="form.type" class="w-full border rounded px-3 py-2" required>
            <option value="income">Ingreso</option>
            <option value="expense">Egreso</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Importe (XAF) *</label>
          <input v-model.number="form.amount" type="number" min="1" step="1"
                 class="w-full border rounded px-3 py-2" required />
        </div>
      </div>

      <!-- Concepto -->
      <div>
        <label class="block text-sm font-medium mb-1">Concepto *</label>
        <input v-model="form.concept" type="text" minlength="3"
               class="w-full border rounded px-3 py-2" required />
      </div>

      <!-- Categoría y subcategoría -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">Categoría *</label>

          <!-- S10: Badge de sugerencia -->
          <div v-if="suggestion"
               class="mb-2 flex items-center gap-2 text-xs rounded border p-2"
               :class="{
                 'text-green-700 bg-green-50 border-green-200': suggestion.confidence === 'high',
                 'text-yellow-800 bg-yellow-50 border-yellow-200': suggestion.confidence === 'medium',
                 'text-orange-800 bg-orange-50 border-orange-200': suggestion.confidence === 'medium-low'
               }">
            <span v-if="suggestion.confidence === 'high'" class="font-medium">✓ Auto-aplicado:</span>
            <span v-else class="font-medium">Sugerencia:</span>
            <span>{{ suggestion.category_name }} / {{ suggestion.subcategory_name }}</span>
            <span class="text-gray-500">({{ suggestion.sample_count }} mov.)</span>
            <button v-if="suggestion.confidence !== 'high'" type="button"
                    @click="applySuggestion"
                    class="ml-auto px-2 py-0.5 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
              Aplicar
            </button>
            <button type="button" @click="dismissSuggestion"
                    class="text-gray-400 hover:text-gray-700 text-base leading-none">×</button>
          </div>

          <select v-model="form.category_id" @change="onCategoryManualChange"
                  class="w-full border rounded px-3 py-2" required>
            <option :value="null" disabled>Seleccionar...</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">Subcategoría *</label>
          <select v-model="form.subcategory_id" class="w-full border rounded px-3 py-2" required>
            <option :value="null" disabled>Seleccionar...</option>
            <option v-for="s in subcategories" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
      </div>

      <!-- Proyecto y obra -->
      <div>
        <label class="block text-sm font-medium mb-1">Proyecto / Obra *</label>
        <ProjectWorkSelector v-model="form.projects" />
      </div>

      <!-- Contraparte -->
      <div>
        <label class="block text-sm font-medium mb-1">Contraparte *</label>
        <p v-if="counterpartyHint" class="text-xs text-gray-600 mb-1 italic">{{ counterpartyHint }}</p>
        <CounterpartySelector @update="onCounterpartyChange" />
      </div>

      <!-- Vehículo (opcional) -->
      <div>
        <label class="block text-sm font-medium mb-1">Vehículo <span v-if="vehicleRequired" class="text-red-500">*</span><span v-else class="text-gray-500 text-xs">(opcional)</span></label>
        <select v-model="form.vehicle_id" class="w-full border rounded px-3 py-2">
          <option :value="null">— Ninguno —</option>
          <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.plate }} {{ v.brand || '' }}</option>
        </select>
      </div>

      <!-- F5: Firma de la contraparte (SignatureSection polimorfico) -->
      <div v-if="contraparteType">
        <label class="block text-sm font-medium mb-2">Firma de la contraparte *</label>
        <SignatureSection :contraparte-type="contraparteType"
                          :contraparte-id="contraparteId"
                          @signature-ready="onSignatureReady" />
      </div>
      <div v-else class="bg-amber-50 border border-amber-200 text-amber-700 text-sm rounded p-3">
        Selecciona primero una contraparte para capturar la firma.
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <router-link to="/transactions" class="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300 text-sm">
          Cancelar
        </router-link>
        <div v-if="exceedsThreshold" class="bg-yellow-50 border border-yellow-300 rounded p-3 mb-3 text-sm text-yellow-800">
          ⚠️ Esta operación de <strong>{{ Number(form.amount).toLocaleString() }} XAF</strong> en
          <strong>{{ exceedsThreshold.category }}</strong> supera el umbral configurado
          ({{ Number(exceedsThreshold.threshold).toLocaleString() }} XAF) y quedará
          <strong>pendiente de aprobación</strong> hasta que el admin la apruebe.
        </div>
        <button type="submit" :disabled="submitting || !signaturePayload"
                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm disabled:opacity-50"
                :title="!signaturePayload ? 'Captura la firma antes de registrar' : ''">
          {{ submitting ? 'Registrando...' : 'Registrar Transacción' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import transactionService from '@/services/transactionService'
import suggestionService from '@/services/suggestionService'
import ProjectWorkSelector from '@/components/ProjectWorkSelector.vue'
import CounterpartySelector from '@/components/CounterpartySelector.vue'
import SignatureSection from '@/components/admin/SignatureSection.vue'
import { useAuthStore } from '@/stores/auth'

// H-Role guard: solo gestor accede a /transactions/new
const __authGuard = useAuthStore()
const __routerGuard = useRouter()
onMounted(() => {
  if (!__authGuard.hasRole('gestor')) {
    __routerGuard.replace('/transactions')
  }
})

const router = useRouter()

const form = ref({
  type: 'expense', amount: null, concept: '',
  category_id: null, subcategory_id: null,
  projects: [{ project_id: null, work_id: null }],
  supplier_id: null, employee_id: null, partner_id: null,
  counterparty_free: null, vehicle_id: null
})

const categories = ref([])
const subcategories = ref([])
const vehicles = ref([])
const error = ref('')
const success = ref('')
const submitting = ref(false)

// === S10: Sugerencias de categorización ===
const suggestion = ref(null)
const userEditedCategory = ref(false)

// F5: estado de la firma capturada por SignatureSection
const signaturePayload = ref(null)

// Reglas de contraparte y vehiculo segun categoria (M14)
const selectedCategoryMeta = computed(() => {
  const cat = categories.value.find(c => c.id === form.value.category_id)
  return cat || null
})
const expectedCounterparty = computed(() => selectedCategoryMeta.value?.counterparty_type || null)
const vehicleRequired = computed(() => !!selectedCategoryMeta.value?.requires_vehicle)
const counterpartyHintMap = {
  employee: 'Esta categoría requiere seleccionar un empleado.',
  supplier: 'Esta categoría requiere seleccionar un proveedor.',
  partner:  'Esta categoría requiere seleccionar un socio.',
  external: 'Esta categoría requiere texto libre (no usar el catálogo).',
  any:      'Selecciona contraparte del catálogo o introduce texto libre.',
  none:     'Operación interna: no admite contraparte.',
}
const counterpartyHint = computed(() => expectedCounterparty.value ? counterpartyHintMap[expectedCounterparty.value] : null)

// D: umbrales de aprobacion (M10a) — para warning preventivo al gestor
const thresholds = ref([])
async function loadThresholds() {
  try {
    const r = await transactionService.listThresholds()
    thresholds.value = r.data || []
  } catch (_) { thresholds.value = [] }
}
const exceedsThreshold = computed(() => {
  if (!form.value.amount || !form.value.category_id || form.value.type !== 'expense') return null
  const userDeleg = auth.user?.delegacion
  const match = thresholds.value.find(t =>
    t.category_id === form.value.category_id &&
    (!userDeleg || t.delegacion === userDeleg)
  )
  if (!match) return null
  if (Number(form.value.amount) >= Number(match.threshold_amount)) {
    return { threshold: Number(match.threshold_amount), category: match.category_name }
  }
  return null
})

const contraparteType = computed(() => {
  if (form.value.supplier_id !== null && form.value.supplier_id !== undefined) return 'supplier'
  if (form.value.employee_id !== null && form.value.employee_id !== undefined) return 'employee'
  if (form.value.partner_id !== null && form.value.partner_id !== undefined) return 'partner'
  if (form.value.counterparty_free !== null && form.value.counterparty_free !== '' && form.value.counterparty_free !== undefined) return 'free'
  return null
})

const contraparteId = computed(() => {
  if (contraparteType.value === 'supplier') return form.value.supplier_id
  if (contraparteType.value === 'employee') return form.value.employee_id
  if (contraparteType.value === 'partner') return form.value.partner_id
  return null
})

function onSignatureReady(payload) {
  signaturePayload.value = payload
}

// Si cambia la contraparte, invalidamos la firma anterior
watch([contraparteType, contraparteId], () => {
  signaturePayload.value = null
})
let suggestionDebounceTimer = null

async function fetchSuggestion() {
  // No pedir sugerencias si el usuario ya edito manualmente la categoria
  if (userEditedCategory.value) return

  const ctx = {
    concept: form.value.concept,
    supplier_id: form.value.supplier_id,
    employee_id: form.value.employee_id,
    partner_id: form.value.partner_id,
    counterparty_free: form.value.counterparty_free,
    project_id: form.value.projects?.[0]?.project_id || null,
    delegacion: __authGuard.user?.delegacion || null
  }

  const result = await suggestionService.fetch(ctx)
  if (!result) {
    suggestion.value = null
    return
  }
  suggestion.value = result

  // Auto-aplicar si confianza alta
  if (result.confidence === 'high') {
    await applySuggestion()
  }
}

async function applySuggestion() {
  if (!suggestion.value) return
  form.value.category_id = suggestion.value.category_id
  // Cargar subcategorias de la nueva categoria, luego asignar la subcategoria sugerida
  await loadSubcategories()
  form.value.subcategory_id = suggestion.value.subcategory_id
}

function dismissSuggestion() {
  suggestion.value = null
}

function onCategoryManualChange() {
  // El usuario eligio una categoria manualmente — desactivar sugerencias en este formulario
  userEditedCategory.value = true
  suggestion.value = null
  loadSubcategories()
}

function debouncedFetchSuggestion() {
  if (suggestionDebounceTimer) clearTimeout(suggestionDebounceTimer)
  suggestionDebounceTimer = setTimeout(() => fetchSuggestion(), 500)
}

// Watchers con debounce — uno por campo para garantizar deteccion fiable
watch(() => form.value.concept, debouncedFetchSuggestion)
watch(() => form.value.supplier_id, debouncedFetchSuggestion)
watch(() => form.value.employee_id, debouncedFetchSuggestion)
watch(() => form.value.partner_id, debouncedFetchSuggestion)
watch(() => form.value.counterparty_free, debouncedFetchSuggestion)
watch(() => form.value.projects?.[0]?.project_id, debouncedFetchSuggestion)

async function loadCategories() {
  const { data } = await api.get('/categories')
  categories.value = Array.isArray(data) ? data : (data.items || [])
}

async function loadSubcategories() {
  form.value.subcategory_id = null
  if (!form.value.category_id) { subcategories.value = []; return }
  const { data } = await api.get('/subcategories', { params: { category_id: form.value.category_id } })
  subcategories.value = Array.isArray(data) ? data : (data.items || [])
}

async function loadVehicles() {
  const { data } = await api.get('/vehicles')
  vehicles.value = Array.isArray(data) ? data : (data.items || [])
}

function onCounterpartyChange(cp) {
  form.value.supplier_id = cp.supplier_id
  form.value.employee_id = cp.employee_id
  form.value.partner_id = cp.partner_id
  form.value.counterparty_free = cp.counterparty_free
}

async function submit() {
  error.value = ''
  success.value = ''

  // F5: la firma es obligatoria para registrar la transaccion
  if (!signaturePayload.value) {
    error.value = 'Falta capturar la firma de la contraparte'
    return
  }
  // M14: validar contraparte y vehiculo segun la categoria seleccionada
  if (expectedCounterparty.value) {
    const ct = expectedCounterparty.value
    const cf = (form.value.counterparty_free || '').trim()
    if (ct === 'employee' && !form.value.employee_id) {
      error.value = 'Esta categoría requiere seleccionar un empleado'; return
    }
    if (ct === 'supplier' && !form.value.supplier_id) {
      error.value = 'Esta categoría requiere seleccionar un proveedor'; return
    }
    if (ct === 'partner' && !form.value.partner_id) {
      error.value = 'Esta categoría requiere seleccionar un socio'; return
    }
    if (ct === 'external' && !cf) {
      error.value = 'Esta categoría requiere identificar la contraparte con texto libre'; return
    }
    if (ct === 'any' && !(form.value.employee_id || form.value.supplier_id || form.value.partner_id || cf)) {
      error.value = 'Esta categoría requiere una contraparte (catálogo o texto libre)'; return
    }
    if (ct === 'none' && (form.value.employee_id || form.value.supplier_id || form.value.partner_id || cf)) {
      error.value = 'Esta categoría es operación interna y no admite contraparte'; return
    }
  }
  if (vehicleRequired.value && !form.value.vehicle_id) {
    error.value = 'Esta categoría requiere seleccionar un vehículo'; return
  }
  // Validar proyectos/obras: cada item debe tener ambos campos completos
  const projsValid = (form.value.projects || []).filter(p => p && p.project_id && p.work_id)
  if (projsValid.length === 0) {
    error.value = 'Debes seleccionar al menos un proyecto y su obra'
    return
  }
  form.value.projects = projsValid

  submitting.value = true
  try {
    // Mapeo contraparteType (frontend) -> signer_type (backend)
    const signerTypeMap = {
      supplier: 'supplier',
      employee: 'employee',
      partner: 'partner',
      free: 'free_text'
    }
    const signerType = signerTypeMap[contraparteType.value]

    // Strip prefijo data:image/png;base64, si lo lleva el wacom_image_b64
    const stripDataUrl = (b64) => {
      if (!b64) return null
      const idx = b64.indexOf(',')
      return idx >= 0 ? b64.slice(idx + 1) : b64
    }

    // Nombre del firmante: payload primero, fallback al counterparty_free
    const signerName = signaturePayload.value.signer_name
      || form.value.counterparty_free
      || 'Sin nombre'

    // Construir el objeto signature anidado segun el contrato del backend
    const signature = {
      signer_type: signerType,
      signer_name: signerName,
      signature_method: signaturePayload.value.signature_method,
      employee_id: form.value.employee_id,
      supplier_id: form.value.supplier_id,
      partner_id: form.value.partner_id,
    }

    if (signaturePayload.value.signature_method === 'fingerprint') {
      signature.fingerprint_score = Math.round(Number(signaturePayload.value.fingerprint_score) || 0)
      signature.fingerprint_finger_position = signaturePayload.value.fingerprint_finger_position
      signature.fingerprint_attempts = signaturePayload.value.fingerprint_attempts
    } else {
      // wacom o wacom_provisional
      signature.signature_data = stripDataUrl(signaturePayload.value.wacom_image_b64)
      signature.fingerprint_failed_scores = signaturePayload.value.fingerprint_failed_scores
    }

    const body = { ...form.value, signature }
      const { data } = await transactionService.create(body)
      router.push('/transactions/' + data.id)
    form.value = {
      type: 'expense', amount: null, concept: '',
      category_id: null, subcategory_id: null,
      projects: [{ project_id: null, work_id: null }],
      supplier_id: null, employee_id: null, partner_id: null,
      counterparty_free: null, vehicle_id: null
    }
    subcategories.value = []
    signaturePayload.value = null
    suggestion.value = null
    userEditedCategory.value = false
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al registrar la transacción'
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loadCategories(); loadVehicles(); loadThresholds() })
</script>

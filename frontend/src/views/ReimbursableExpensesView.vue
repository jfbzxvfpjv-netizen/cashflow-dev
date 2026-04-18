<template>
  <div class="p-6">
    <!-- Cabecera -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold">Gastos reembolsables</h1>
        <p class="text-sm text-gray-500">Gastos adelantados por socios o empleados pendientes de reembolso</p>
      </div>
      <button @click="openCreate"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow">
        + Nuevo gasto reembolsable
      </button>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100 text-gray-700">
          <tr>
            <th class="px-3 py-2 text-left">Fecha</th>
            <th class="px-3 py-2 text-left">Solicitante</th>
            <th class="px-3 py-2 text-left">Concepto</th>
            <th class="px-3 py-2 text-left">Pago</th>
            <th class="px-3 py-2 text-left">Categoría / Subcat.</th>
            <th class="px-3 py-2 text-left">Proyecto / Obra</th>
            <th class="px-3 py-2 text-right">EUR</th>
            <th class="px-3 py-2 text-right">XAF</th>
            <th class="px-3 py-2 text-right">Pendiente</th>
            <th class="px-3 py-2 text-center">Estado</th>
            <th class="px-3 py-2 text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="11" class="px-3 py-6 text-center text-gray-500">
              No hay gastos reembolsables registrados
            </td>
          </tr>
          <tr v-for="it in items" :key="it.id" class="border-t hover:bg-gray-50">
            <td class="px-3 py-2">{{ fmtDate(it.created_at) }}</td>
            <td class="px-3 py-2">
              <span v-if="it.partner_name" class="text-blue-700">{{ it.partner_name }}</span>
              <span v-else-if="it.employee_name" class="text-green-700">{{ it.employee_name }}</span>
              <span v-else class="text-gray-400">—</span>
              <div class="text-xs text-gray-500">
                {{ it.partner_name ? 'Socio' : (it.employee_name ? 'Empleado' : '') }}
              </div>
            </td>
            <td class="px-3 py-2 max-w-xs truncate" :title="it.concept">{{ it.concept }}</td>
            <td class="px-3 py-2">{{ paymentLabel(it.payment_method) }}</td>
            <td class="px-3 py-2">
              <div>{{ it.category_name || '—' }}</div>
              <div class="text-xs text-gray-500">{{ it.subcategory_name || '' }}</div>
            </td>
            <td class="px-3 py-2">
              <div>{{ it.project_name || '—' }}</div>
              <div class="text-xs text-gray-500">{{ it.work_name || '' }}</div>
            </td>
            <td class="px-3 py-2 text-right">{{ fmt(it.amount_eur) }} €</td>
            <td class="px-3 py-2 text-right">{{ fmt(it.amount_xaf) }}</td>
            <td class="px-3 py-2 text-right font-medium">{{ fmt(it.pending_xaf) }}</td>
            <td class="px-3 py-2 text-center">
              <span :class="statusClass(it.status)" class="px-2 py-1 rounded text-xs font-medium">
                {{ statusLabel(it.status) }}
              </span>
            </td>
            <td class="px-3 py-2 text-center">
              <button v-if="it.status !== 'reimbursed'"
                @click="openReimburse(it)"
                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs">
                Reembolsar
              </button>
              <span v-else class="text-gray-400 text-xs">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal: Crear -->
    <div v-if="showCreate" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4">Nuevo gasto reembolsable</h2>

        <!-- Tipo de solicitante -->
        <label class="block text-sm font-medium mb-1">Solicitante *</label>
        <div class="flex gap-4 mb-3">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="form.requester_kind" value="partner" @change="onRequesterKindChange" />
            <span>Socio</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="form.requester_kind" value="employee" @change="onRequesterKindChange" />
            <span>Empleado</span>
          </label>
        </div>

        <label v-if="form.requester_kind === 'partner'" class="block text-sm font-medium mb-1">Socio *</label>
        <select v-if="form.requester_kind === 'partner'" v-model.number="form.partner_id"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona un socio —</option>
          <option v-for="p in partners" :key="p.id" :value="p.id">{{ p.full_name }}</option>
        </select>

        <label v-if="form.requester_kind === 'employee'" class="block text-sm font-medium mb-1">Empleado *</label>
        <select v-if="form.requester_kind === 'employee'" v-model.number="form.employee_id"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona un empleado —</option>
          <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Concepto *</label>
        <textarea v-model="form.concept" rows="2"
          class="w-full border rounded px-3 py-2 mb-3"
          placeholder="Descripción del gasto (mín. 3 caracteres)"></textarea>

        <label class="block text-sm font-medium mb-1">Método de pago *</label>
        <select v-model="form.payment_method" class="w-full border rounded px-3 py-2 mb-3">
          <option value="tarjeta_personal">Tarjeta personal</option>
          <option value="transferencia_personal">Transferencia personal</option>
          <option value="efectivo_personal">Efectivo personal</option>
        </select>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-sm font-medium mb-1">Importe EUR *</label>
            <input v-model.number="form.amount_eur" type="number" step="0.01" min="0.01"
              class="w-full border rounded px-3 py-2" placeholder="0.00" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Importe XAF *</label>
            <input v-model.number="form.amount_xaf" type="number" step="1" min="1"
              class="w-full border rounded px-3 py-2" placeholder="0" />
          </div>
        </div>
        <div class="text-xs text-gray-500 mb-3">
          Tipo de cambio calculado: <span class="font-medium">{{ computedRate }} XAF / EUR</span>
        </div>

        <label class="block text-sm font-medium mb-1">Categoría *</label>
        <select v-model.number="form.category_id" @change="onCategoryChange"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona una categoría —</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Subcategoría *</label>
        <select v-model.number="form.subcategory_id"
          :disabled="!form.category_id"
          class="w-full border rounded px-3 py-2 mb-3 disabled:bg-gray-100">
          <option :value="null">— Selecciona una subcategoría —</option>
          <option v-for="s in subcategories" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Proyecto *</label>
        <select v-model.number="form.project_id" @change="onProjectChange"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona un proyecto —</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Obra *</label>
        <select v-model.number="form.work_id"
          :disabled="!form.project_id"
          class="w-full border rounded px-3 py-2 mb-4 disabled:bg-gray-100">
          <option :value="null">— Selecciona una obra —</option>
          <option v-for="w in works" :key="w.id" :value="w.id">{{ w.name }}</option>
        </select>

        <div v-if="error" class="text-red-700 text-xs bg-red-50 border border-red-200 rounded p-2 mb-3">
          {{ error }}
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showCreate = false"
            class="px-4 py-2 border rounded hover:bg-gray-50">Cancelar</button>
          <button @click="submit"
            :disabled="!canSubmit"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded disabled:opacity-50">
            Crear
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Reembolsar -->
    <div v-if="showReimburse" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4">
        <h2 class="text-xl font-bold mb-4">Reembolsar gasto</h2>

        <div v-if="target" class="bg-gray-50 p-3 rounded mb-4 text-sm">
          <div>
            <span class="text-gray-500">Solicitante:</span>
            <span class="font-medium ml-1">
              {{ target.partner_name || target.employee_name || '—' }}
              <span class="text-xs text-gray-500">({{ target.partner_name ? 'Socio' : 'Empleado' }})</span>
            </span>
          </div>
          <div><span class="text-gray-500">Concepto:</span> <span class="font-medium">{{ target.concept }}</span></div>
          <div><span class="text-gray-500">Pago original:</span> {{ paymentLabel(target.payment_method) }}</div>
          <div class="grid grid-cols-3 gap-2 mt-2 pt-2 border-t">
            <div><span class="text-gray-500 text-xs">Total XAF</span><div class="font-medium">{{ fmt(target.amount_xaf) }}</div></div>
            <div><span class="text-gray-500 text-xs">Reembolsado</span><div class="font-medium">{{ fmt(target.amount_reimbursed) }}</div></div>
            <div><span class="text-gray-500 text-xs">Pendiente</span><div class="font-medium text-orange-600">{{ fmt(target.pending_xaf) }}</div></div>
          </div>
        </div>

        <label class="block text-sm font-medium mb-1">Importe a reembolsar en XAF *</label>
        <input v-model.number="reimbForm.amount_xaf" type="number" step="1" min="1"
          class="w-full border rounded px-3 py-2 mb-3" />
        <p class="text-xs text-gray-500 mb-4">
          Se registrará una transacción de egreso en tu sesión de caja abierta con la
          categoría y subcategoría elegidas al crear este reembolsable.
        </p>

        <div v-if="reimbError" class="text-red-700 text-xs bg-red-50 border border-red-200 rounded p-2 mb-3">
          {{ reimbError }}
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showReimburse = false"
            class="px-4 py-2 border rounded hover:bg-gray-50">Cancelar</button>
          <button @click="submitReimburse"
            class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded">
            Registrar reembolso
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../services/api'

const items = ref([])
const partners = ref([])
const employees = ref([])
const categories = ref([])
const subcategories = ref([])
const projects = ref([])
const works = ref([])

const showCreate = ref(false)
const showReimburse = ref(false)
const error = ref('')
const reimbError = ref('')

const form = reactive({
  requester_kind: 'partner',
  partner_id: null,
  employee_id: null,
  concept: '',
  payment_method: 'tarjeta_personal',
  amount_eur: null,
  amount_xaf: null,
  category_id: null,
  subcategory_id: null,
  project_id: null,
  work_id: null,
})

const reimbForm = reactive({ amount_xaf: null })
const target = ref(null)

const computedRate = computed(() => {
  if (form.amount_eur > 0 && form.amount_xaf > 0) {
    return (form.amount_xaf / form.amount_eur).toFixed(4)
  }
  return '—'
})

const canSubmit = computed(() => {
  const hasRequester = (form.requester_kind === 'partner' && form.partner_id) ||
                        (form.requester_kind === 'employee' && form.employee_id)
  return hasRequester &&
         form.concept && form.concept.trim().length >= 3 &&
         form.amount_eur > 0 && form.amount_xaf > 0 &&
         form.category_id && form.subcategory_id &&
         form.project_id && form.work_id
})

function fmt(v) {
  if (v === null || v === undefined) return '0'
  return new Intl.NumberFormat('es-ES').format(Number(v))
}
function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('es-ES')
}
function paymentLabel(m) {
  return { tarjeta_personal: 'Tarjeta personal', transferencia_personal: 'Transferencia personal', efectivo_personal: 'Efectivo personal' }[m] || m
}
function statusLabel(s) {
  return { pending: 'Pendiente', partial: 'Parcial', reimbursed: 'Reembolsado' }[s] || s
}
function statusClass(s) {
  return { pending: 'bg-yellow-100 text-yellow-800', partial: 'bg-blue-100 text-blue-800', reimbursed: 'bg-green-100 text-green-800' }[s] || 'bg-gray-100 text-gray-700'
}

async function load() {
  const r = await api.get('/reimbursable-expenses')
  items.value = r.data.items || r.data || []
}

async function loadCatalogs() {
  const [catRes, projRes, partRes, empRes] = await Promise.all([
    api.get('/categories'),
    api.get('/projects'),
    api.get('/partners'),
    api.get('/employees'),
  ])
  categories.value = catRes.data.items || catRes.data || []
  projects.value = projRes.data.items || projRes.data || []
  partners.value = partRes.data.items || partRes.data || []
  employees.value = empRes.data.items || empRes.data || []
}

async function onCategoryChange() {
  form.subcategory_id = null
  subcategories.value = []
  if (!form.category_id) return
  const r = await api.get('/subcategories', { params: { category_id: form.category_id } })
  subcategories.value = r.data.items || r.data || []
}

async function onProjectChange() {
  form.work_id = null
  works.value = []
  if (!form.project_id) return
  const r = await api.get('/works', { params: { project_id: form.project_id } })
  works.value = r.data.items || r.data || []
}

function onRequesterKindChange() {
  if (form.requester_kind === 'partner') {
    form.employee_id = null
  } else {
    form.partner_id = null
  }
}

function openCreate() {
  Object.assign(form, {
    requester_kind: 'partner',
    partner_id: null,
    employee_id: null,
    concept: '',
    payment_method: 'tarjeta_personal',
    amount_eur: null,
    amount_xaf: null,
    category_id: null,
    subcategory_id: null,
    project_id: null,
    work_id: null,
  })
  subcategories.value = []
  works.value = []
  error.value = ''
  showCreate.value = true
}

async function submit() {
  error.value = ''
  try {
    const payload = {
      concept: form.concept.trim(),
      payment_method: form.payment_method,
      amount_eur: form.amount_eur,
      amount_xaf: form.amount_xaf,
      category_id: form.category_id,
      subcategory_id: form.subcategory_id,
      project_id: form.project_id,
      work_id: form.work_id,
      partner_id: form.requester_kind === 'partner' ? form.partner_id : null,
      employee_id: form.requester_kind === 'employee' ? form.employee_id : null,
    }
    await api.post('/reimbursable-expenses', payload)
    showCreate.value = false
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Error al crear el gasto'
  }
}

function openReimburse(it) {
  target.value = it
  reimbForm.amount_xaf = it.pending_xaf
  reimbError.value = ''
  showReimburse.value = true
}

async function submitReimburse() {
  reimbError.value = ''
  try {
    await api.post(`/reimbursable-expenses/${target.value.id}/reimburse`, {
      amount_xaf: reimbForm.amount_xaf,
    })
    showReimburse.value = false
    await load()
  } catch (e) {
    reimbError.value = e.response?.data?.detail || e.message || 'Error al registrar reembolso'
  }
}

onMounted(async () => {
  await Promise.all([load(), loadCatalogs()])
})
</script>

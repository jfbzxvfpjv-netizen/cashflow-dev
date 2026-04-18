<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Anticipos y Préstamos</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        + Nuevo
      </button>
    </div>

    <!-- Filtro -->
    <div class="mb-4 flex gap-4">
      <select v-model="filterStatus" @change="load" class="min-w-[180px] border rounded px-3 py-2">
        <option value="">Todos los estados</option>
        <option value="open">Abiertos</option>
        <option value="partial">Parciales</option>
        <option value="closed">Cerrados</option>
      </select>
    </div>

    <!-- Tabla -->
    <div v-if="loading" class="text-gray-500">Cargando...</div>
    <table v-else class="min-w-full bg-white border">
      <thead class="bg-gray-100">
        <tr>
          <th class="px-4 py-2 text-left">Empleado</th>
          <th class="px-4 py-2 text-left">Tipo</th>
          <th class="px-4 py-2 text-right">Importe</th>
          <th class="px-4 py-2 text-right">Devuelto</th>
          <th class="px-4 py-2 text-right">Pendiente</th>
          <th class="px-4 py-2 text-left">Concepto</th>
          <th class="px-4 py-2 text-center">Estado</th>
          <th class="px-4 py-2 text-center">Tx</th>
          <th class="px-4 py-2 text-center">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id" class="border-t">
          <td class="px-4 py-2">{{ it.employee_name }}</td>
          <td class="px-4 py-2">{{ it.type === 'advance' ? 'Anticipo' : 'Préstamo' }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount) }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount_repaid) }}</td>
          <td class="px-4 py-2 text-right font-semibold">{{ fmt(it.pending) }}</td>
          <td class="px-4 py-2">{{ it.concept }}</td>
          <td class="px-4 py-2 text-center">
            <span :class="statusClass(it.status)" class="px-2 py-1 rounded text-xs">
              {{ it.status }}
            </span>
          </td>
          <td class="px-4 py-2 text-center text-xs text-gray-500">
            <span v-if="it.creation_transaction_id" :title="`Creación: #${it.creation_transaction_id}`">📄</span>
            <span v-if="it.repay_transaction_ids && it.repay_transaction_ids.length"
                  :title="`Repays: ${it.repay_transaction_ids.join(', ')}`">↩️</span>
          </td>
          <td class="px-4 py-2 text-center">
            <button v-if="it.status !== 'closed'" @click="openRepay(it)"
              class="text-blue-600 hover:underline text-sm">Devolver</button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="9" class="px-4 py-6 text-center text-gray-500">Sin registros</td>
        </tr>
      </tbody>
    </table>

    <!-- Modal: Nuevo anticipo -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Nuevo anticipo/préstamo</h2>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Empleado</label>
            <select v-model="form.employee_id" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Tipo</label>
            <select v-model="form.type" class="w-full border rounded px-3 py-2 truncate">
              <option value="advance">Anticipo</option>
              <option value="loan">Préstamo</option>
            </select>
          </div>
        </div>

        <label class="block mb-2 text-sm">Importe (XAF)</label>
        <input v-model.number="form.amount" type="number" min="1" class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm">Concepto</label>
        <textarea v-model="form.concept" class="w-full border rounded px-3 py-2 mb-3" rows="2"
                  placeholder="Breve descripción del motivo del anticipo"></textarea>

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">
            Clasificación contable de la transacción que se creará en caja al entregar el dinero.
          </p>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="form.category_id" @change="loadSubcatsForm" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="form.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!form.category_id">
                <option :value="null">—</option>
                <option v-for="s in subcatsForm" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="form.project_id" @change="loadWorksForm" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="form.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!form.project_id">
                <option :value="null">—</option>
                <option v-for="w in worksForm" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showCreate = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCreate" class="px-4 py-2 bg-blue-600 text-white rounded"
                  :disabled="!canSubmitCreate">Crear</button>
        </div>
      </div>
    </div>

    <!-- Modal: Devolver -->
    <div v-if="showRepay" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Devolución manual</h2>

        <div class="bg-gray-50 border rounded p-3 mb-4 text-sm">
          <div><span class="text-gray-500">Empleado:</span> {{ repayTarget?.employee_name }}</div>
          <div><span class="text-gray-500">Tipo:</span> {{ repayTarget?.type === 'advance' ? 'Anticipo' : 'Préstamo' }}</div>
          <div><span class="text-gray-500">Pendiente:</span> <span class="font-semibold">{{ fmt(repayTarget?.pending) }}</span> XAF</div>
        </div>

        <label class="block mb-2 text-sm">Importe a devolver (XAF)</label>
        <input v-model.number="repayForm.amount" type="number" min="1"
               :max="repayTarget?.pending" class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm">Concepto (opcional)</label>
        <input v-model="repayForm.concept" class="w-full border rounded px-3 py-2 mb-3"
               :placeholder="repayTarget?.concept" />

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">
            Clasificación contable de la transacción ingreso que se creará al recibir la devolución.
          </p>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="repayForm.category_id" @change="loadSubcatsRepay" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="repayForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!repayForm.category_id">
                <option :value="null">—</option>
                <option v-for="s in subcatsRepay" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="repayForm.project_id" @change="loadWorksRepay" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="repayForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!repayForm.project_id">
                <option :value="null">—</option>
                <option v-for="w in worksRepay" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showRepay = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitRepay" class="px-4 py-2 bg-blue-600 text-white rounded"
                  :disabled="!canSubmitRepay">Registrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { advancesService } from '../services/financialModulesService'
import api from '../services/api'

// Helper: extrae array de respuestas que pueden venir como array o paginado
function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items', 'data', 'results']) if (Array.isArray(d[k])) return d[k]
  }
  console.warn('[M9 Advances] respuesta inesperada:', d)
  return []
}

// Estado
const items      = ref([])
const employees  = ref([])
const categories = ref([])
const projects   = ref([])
const subcatsForm = ref([])
const worksForm   = ref([])
const subcatsRepay = ref([])
const worksRepay   = ref([])

const loading = ref(false)
const filterStatus = ref('')
const showCreate = ref(false)
const showRepay  = ref(false)
const repayTarget = ref(null)

const emptyCreateForm = () => ({
  employee_id: null, type: 'advance', amount: 0, concept: '',
  category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})
const emptyRepayForm = () => ({
  amount: 0, concept: '',
  category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})

const form = ref(emptyCreateForm())
const repayForm = ref(emptyRepayForm())

// Formato y estilo
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })
const statusClass = (s) => ({
  open: 'bg-blue-100 text-blue-700',
  partial: 'bg-yellow-100 text-yellow-700',
  closed: 'bg-green-100 text-green-700',
}[s] || 'bg-gray-100')

// Validación de submit
const canSubmitCreate = computed(() => {
  const f = form.value
  return f.employee_id && f.type && f.amount > 0 && f.concept && f.concept.length >= 3
    && f.category_id && f.subcategory_id && f.project_id && f.work_id
})
const canSubmitRepay = computed(() => {
  const f = repayForm.value
  return f.amount > 0 && f.category_id && f.subcategory_id && f.project_id && f.work_id
})

// Cargas
const load = async () => {
  loading.value = true
  try {
    items.value = await advancesService.list(filterStatus.value ? { status: filterStatus.value } : {})
  } finally { loading.value = false }
}

const loadCatalogs = async () => {
  employees.value  = extractArray((await api.get('/employees')).data).filter(e => e.active)
  categories.value = extractArray((await api.get('/categories')).data).filter(c => c.active)
  projects.value   = extractArray((await api.get('/projects')).data).filter(p => p.active)
}

// Cascadings
const loadSubcatsForm = async () => {
  if (!form.value.category_id) { subcatsForm.value = []; form.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: form.value.category_id } })
  subcatsForm.value = extractArray(r.data).filter(s => s.active)
  form.value.subcategory_id = null
}
const loadWorksForm = async () => {
  if (!form.value.project_id) { worksForm.value = []; form.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: form.value.project_id } })
  worksForm.value = extractArray(r.data).filter(w => w.active)
  form.value.work_id = null
}
const loadSubcatsRepay = async () => {
  if (!repayForm.value.category_id) { subcatsRepay.value = []; repayForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: repayForm.value.category_id } })
  subcatsRepay.value = extractArray(r.data).filter(s => s.active)
  repayForm.value.subcategory_id = null
}
const loadWorksRepay = async () => {
  if (!repayForm.value.project_id) { worksRepay.value = []; repayForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: repayForm.value.project_id } })
  worksRepay.value = extractArray(r.data).filter(w => w.active)
  repayForm.value.work_id = null
}

// Apertura de modales
const openCreate = () => {
  form.value = emptyCreateForm()
  subcatsForm.value = []
  worksForm.value = []
  showCreate.value = true
}
const openRepay = (it) => {
  repayTarget.value = it
  repayForm.value = emptyRepayForm()
  subcatsRepay.value = []
  worksRepay.value = []
  showRepay.value = true
}

// Submits
const submitCreate = async () => {
  try {
    await advancesService.create(form.value)
    showCreate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al crear el anticipo')
  }
}

const submitRepay = async () => {
  try {
    await advancesService.repay(repayTarget.value.id, repayForm.value)
    showRepay.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al registrar la devolución')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>

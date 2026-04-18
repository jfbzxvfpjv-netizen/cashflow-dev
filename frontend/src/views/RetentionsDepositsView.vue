<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Retenciones y Depósitos</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        + Nuevo
      </button>
    </div>

    <!-- Filtros -->
    <div class="mb-4 flex gap-4">
      <select v-model="filterStatus" @change="load" class="min-w-[180px] border rounded px-3 py-2">
        <option value="">Todos los estados</option>
        <option value="pending">Pendientes</option>
        <option value="released">Liberados</option>
      </select>
      <select v-model="filterType" @change="load" class="min-w-[180px] border rounded px-3 py-2">
        <option value="">Cualquier tipo</option>
        <option value="retention">Retenciones</option>
        <option value="deposit">Depósitos</option>
      </select>
    </div>

    <!-- Tabla -->
    <table class="min-w-full bg-white border">
      <thead class="bg-gray-100">
        <tr>
          <th class="px-4 py-2 text-left">Tipo</th>
          <th class="px-4 py-2 text-left">Contraparte</th>
          <th class="px-4 py-2 text-right">Importe</th>
          <th class="px-4 py-2 text-left">Concepto</th>
          <th class="px-4 py-2 text-left">F. Liberación</th>
          <th class="px-4 py-2 text-center">Estado</th>
          <th class="px-4 py-2 text-center">Tx</th>
          <th class="px-4 py-2 text-center">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id" class="border-t">
          <td class="px-4 py-2">{{ it.type === 'retention' ? 'Retención' : 'Depósito' }}</td>
          <td class="px-4 py-2">{{ it.supplier_name || it.employee_name || '—' }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount) }}</td>
          <td class="px-4 py-2">{{ it.concept }}</td>
          <td class="px-4 py-2">{{ it.release_date || '—' }}</td>
          <td class="px-4 py-2 text-center">
            <span :class="statusClass(it.status)" class="px-2 py-1 rounded text-xs">{{ it.status }}</span>
          </td>
          <td class="px-4 py-2 text-center text-xs text-gray-500">
            <span v-if="it.creation_transaction_id" :title="`Creación: #${it.creation_transaction_id}`">📄</span>
            <span v-if="it.release_transaction_id" :title="`Liberación: #${it.release_transaction_id}`">✅</span>
          </td>
          <td class="px-4 py-2 text-center">
            <button v-if="it.status === 'pending'" @click="openRelease(it)"
              class="text-green-600 hover:underline text-sm">Liberar</button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="8" class="px-4 py-6 text-center text-gray-500">Sin registros</td>
        </tr>
      </tbody>
    </table>

    <!-- Modal: Nueva retención/depósito -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Nueva retención/depósito</h2>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Tipo</label>
            <select v-model="form.type" class="w-full border rounded px-3 py-2 truncate">
              <option value="retention">Retención (dinero retenido en caja)</option>
              <option value="deposit">Depósito (fianza entregada a tercero)</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Importe (XAF)</label>
            <input v-model.number="form.amount" type="number" min="1" class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Proveedor</label>
            <select v-model="form.supplier_id" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Empleado</label>
            <select v-model="form.employee_id" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
          </div>
        </div>

        <label class="block mb-2 text-sm">Concepto</label>
        <input v-model="form.concept" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="Motivo de la retención/depósito" />

        <label class="block mb-2 text-sm">Fecha de liberación prevista (opcional)</label>
        <input v-model="form.release_date" type="date" class="w-full border rounded px-3 py-2 mb-3" />

        <!-- Bloque condicional: solo si es deposit -->
        <div v-if="form.type === 'deposit'" class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">
            En depósitos el dinero sale físicamente de caja al entregarlo — indique la clasificación contable.
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

        <!-- Aviso informativo para retention -->
        <div v-else class="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3 mb-3">
          En retenciones el dinero se queda físicamente en caja — no se crea transacción al crear.
          La clasificación contable se pedirá al liberar, cuando el dinero salga al destinatario final.
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showCreate = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCreate" class="px-4 py-2 bg-blue-600 text-white rounded"
                  :disabled="!canSubmitCreate">Crear</button>
        </div>
      </div>
    </div>

    <!-- Modal: Liberar -->
    <div v-if="showRelease" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Liberar {{ releaseTarget?.type === 'deposit' ? 'depósito' : 'retención' }}</h2>

        <div class="bg-gray-50 border rounded p-3 mb-4 text-sm">
          <div><span class="text-gray-500">Contraparte:</span> {{ releaseTarget?.supplier_name || releaseTarget?.employee_name }}</div>
          <div><span class="text-gray-500">Importe:</span> <span class="font-semibold">{{ fmt(releaseTarget?.amount) }}</span> XAF</div>
          <div><span class="text-gray-500">Concepto original:</span> {{ releaseTarget?.concept }}</div>
        </div>

        <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded p-3 mb-3">
          <span v-if="releaseTarget?.type === 'deposit'">
            Al liberar un depósito, el dinero vuelve del tercero a caja — se creará una transacción <strong>ingreso</strong>.
          </span>
          <span v-else>
            Al liberar una retención, el dinero retenido sale al destinatario — se creará una transacción <strong>egreso</strong>.
          </span>
        </div>

        <label class="block mb-2 text-sm">Concepto (opcional)</label>
        <input v-model="releaseForm.concept" class="w-full border rounded px-3 py-2 mb-3"
               :placeholder="releaseTarget?.concept" />

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Categoría</label>
            <select v-model="releaseForm.category_id" @change="loadSubcatsRelease" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Subcategoría</label>
            <select v-model="releaseForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!releaseForm.category_id">
              <option :value="null">—</option>
              <option v-for="s in subcatsRelease" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Proyecto</label>
            <select v-model="releaseForm.project_id" @change="loadWorksRelease" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Obra</label>
            <select v-model="releaseForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!releaseForm.project_id">
              <option :value="null">—</option>
              <option v-for="w in worksRelease" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showRelease = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitRelease" class="px-4 py-2 bg-green-600 text-white rounded"
                  :disabled="!canSubmitRelease">Liberar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { retentionsService } from '../services/financialModulesService'
import api from '../services/api'

function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items', 'data', 'results']) if (Array.isArray(d[k])) return d[k]
  }
  console.warn('[M9 Retentions] respuesta inesperada:', d)
  return []
}

// Estado
const items      = ref([])
const suppliers  = ref([])
const employees  = ref([])
const categories = ref([])
const projects   = ref([])
const subcatsForm    = ref([])
const worksForm      = ref([])
const subcatsRelease = ref([])
const worksRelease   = ref([])

const filterStatus = ref('')
const filterType   = ref('')
const showCreate   = ref(false)
const showRelease  = ref(false)
const releaseTarget = ref(null)

const emptyCreateForm = () => ({
  type: 'retention', supplier_id: null, employee_id: null,
  amount: 0, concept: '', release_date: null,
  category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})
const emptyReleaseForm = () => ({
  concept: '',
  category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})

const form        = ref(emptyCreateForm())
const releaseForm = ref(emptyReleaseForm())

// Formato y estilo
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })
const statusClass = (s) => s === 'pending'
  ? 'bg-yellow-100 text-yellow-700'
  : 'bg-green-100 text-green-700'

// Validaciones
const canSubmitCreate = computed(() => {
  const f = form.value
  if (f.amount <= 0) return false
  if (!f.concept || f.concept.length < 3) return false
  if (!f.supplier_id && !f.employee_id) return false
  if (f.type === 'deposit') {
    return f.category_id && f.subcategory_id && f.project_id && f.work_id
  }
  return true
})
const canSubmitRelease = computed(() => {
  const f = releaseForm.value
  return f.category_id && f.subcategory_id && f.project_id && f.work_id
})

// Cargas
const load = async () => {
  const params = {}
  if (filterStatus.value) params.status = filterStatus.value
  if (filterType.value)   params.type   = filterType.value
  items.value = await retentionsService.list(params)
}

const loadCatalogs = async () => {
  suppliers.value  = extractArray((await api.get('/suppliers')).data).filter(s => s.active)
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
const loadSubcatsRelease = async () => {
  if (!releaseForm.value.category_id) { subcatsRelease.value = []; releaseForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: releaseForm.value.category_id } })
  subcatsRelease.value = extractArray(r.data).filter(s => s.active)
  releaseForm.value.subcategory_id = null
}
const loadWorksRelease = async () => {
  if (!releaseForm.value.project_id) { worksRelease.value = []; releaseForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: releaseForm.value.project_id } })
  worksRelease.value = extractArray(r.data).filter(w => w.active)
  releaseForm.value.work_id = null
}

// Apertura de modales
const openCreate = () => {
  form.value = emptyCreateForm()
  subcatsForm.value = []
  worksForm.value   = []
  showCreate.value = true
}
const openRelease = (it) => {
  releaseTarget.value = it
  releaseForm.value = emptyReleaseForm()
  subcatsRelease.value = []
  worksRelease.value   = []
  showRelease.value = true
}

// Submits
const submitCreate = async () => {
  try {
    await retentionsService.create(form.value)
    showCreate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al crear el registro')
  }
}

const submitRelease = async () => {
  try {
    await retentionsService.release(releaseTarget.value.id, releaseForm.value)
    showRelease.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al liberar el registro')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>

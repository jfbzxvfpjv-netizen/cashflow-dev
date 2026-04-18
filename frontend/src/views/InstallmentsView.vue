<template>
  <div class="p-6">
    <!-- Header + filtros -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Pagos Fraccionados</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded">+ Nuevo</button>
    </div>
    <div class="mb-4 flex gap-4">
      <select v-model="filterStatus" @change="load" class="min-w-[180px] border rounded px-3 py-2">
        <option value="">Todos los estados</option>
        <option value="active">Activos</option>
        <option value="closed">Cerrados</option>
      </select>
    </div>

    <!-- Tabla -->
    <table class="w-full bg-white rounded shadow">
      <thead class="bg-gray-100 text-left text-sm">
        <tr>
          <th class="px-4 py-2">Concepto</th>
          <th class="px-4 py-2">Contraparte</th>
          <th class="px-4 py-2 text-right">Total</th>
          <th class="px-4 py-2 text-right">Pagado</th>
          <th class="px-4 py-2 text-right">Pendiente</th>
          <th class="px-4 py-2 text-center">Plazos</th>
          <th class="px-4 py-2">Estado</th>
          <th class="px-4 py-2">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!items.length">
          <td colspan="8" class="text-center py-6 text-gray-500">Sin pagos fraccionados</td>
        </tr>
        <tr v-for="it in items" :key="it.id" class="border-t">
          <td class="px-4 py-2">{{ it.concept }}</td>
          <td class="px-4 py-2">{{ it.supplier_name || it.employee_name || '—' }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.total_amount) }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount_paid) }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.pending) }}</td>
          <td class="px-4 py-2 text-center">{{ it.installments_paid }}/{{ it.installments_count }}</td>
          <td class="px-4 py-2">
            <span :class="it.status === 'closed' ? 'bg-gray-200' : 'bg-green-200'"
                  class="px-2 py-1 rounded text-xs">{{ it.status }}</span>
          </td>
          <td class="px-4 py-2">
            <button v-if="it.status !== 'closed'" @click="openPay(it)"
                    class="text-blue-600 hover:underline">Pagar plazo</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- ========== Modal: Nuevo pago fraccionado ========== -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Nuevo pago fraccionado</h2>

        <label class="block mb-2 text-sm">Concepto</label>
        <input v-model="form.concept" class="w-full border rounded px-3 py-2 mb-3" />

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Total acordado (XAF)</label>
            <input v-model.number="form.total_amount" type="number" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-2 text-sm">Número de plazos</label>
            <input v-model.number="form.installments_count" type="number" class="w-full border rounded px-3 py-2" />
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

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">
            Imputación por defecto — estos valores se aplicarán a todos los plazos pero se pueden cambiar al pagar cada uno.
          </p>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="form.default_category_id" @change="loadSubcatsForm" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="form.default_subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!form.default_category_id">
                <option :value="null">—</option>
                <option v-for="s in subcatsForm" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="form.default_project_id" @change="loadWorksForm" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="form.default_work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!form.default_project_id">
                <option :value="null">—</option>
                <option v-for="w in worksForm" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button @click="showCreate = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCreate" class="px-4 py-2 bg-blue-600 text-white rounded">Crear</button>
        </div>
      </div>
    </div>

    <!-- ========== Modal: Pagar plazo ========== -->
    <div v-if="showPay" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-2">Pagar plazo</h2>
        <p class="text-sm text-gray-600 mb-4">
          {{ payContext?.concept }} · Pendiente: {{ fmt(payContext?.pending) }} XAF
        </p>

        <label class="block mb-2 text-sm">Importe del plazo (XAF)</label>
        <input v-model.number="payForm.amount" type="number" class="w-full border rounded px-3 py-2 mb-3" />

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Categoría</label>
            <select v-model="payForm.category_id" @change="loadSubcatsPay" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Subcategoría</label>
            <select v-model="payForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!payForm.category_id">
              <option :value="null">—</option>
              <option v-for="s in subcatsPay" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label class="block mb-2 text-sm">Proyecto</label>
            <select v-model="payForm.project_id" @change="loadWorksPay" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Obra</label>
            <select v-model="payForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!payForm.project_id">
              <option :value="null">—</option>
              <option v-for="w in worksPay" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showPay = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitPay" class="px-4 py-2 bg-blue-600 text-white rounded">Pagar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { installmentsService } from '../services/financialModulesService'

// Helper defensivo — extrae array de respuesta (array crudo o paginado)
function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items','data','results']) if (Array.isArray(d[k])) return d[k]
  }
  console.warn('[M9] respuesta inesperada:', d)
  return []
}

// Estado
const items      = ref([])
const suppliers  = ref([])
const employees  = ref([])
const categories = ref([])
const projects   = ref([])
const subcatsForm = ref([])
const worksForm   = ref([])
const subcatsPay  = ref([])
const worksPay    = ref([])

const filterStatus = ref('')
const showCreate = ref(false)
const showPay    = ref(false)
const payContext = ref(null)

const form = ref({
  concept: '', total_amount: 0, installments_count: 2,
  supplier_id: null, employee_id: null,
  default_category_id: null, default_subcategory_id: null,
  default_project_id: null,  default_work_id: null,
})
const payForm = ref({
  amount: 0, category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})

// Formato de números
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })

// --- Cargas ---
const load = async () => {
  const params = filterStatus.value ? { status: filterStatus.value } : {}
  items.value = await installmentsService.list(params)
}

const loadCatalogs = async () => {
  suppliers.value  = extractArray((await api.get('/suppliers')).data).filter(s => s.active)
  employees.value  = extractArray((await api.get('/employees')).data).filter(e => e.active)
  categories.value = extractArray((await api.get('/categories')).data).filter(c => c.active)
  projects.value   = extractArray((await api.get('/projects')).data).filter(p => p.active)
}

// Cascading: subcategorías por categoría
const loadSubcatsForm = async () => {
  if (!form.value.default_category_id) { subcatsForm.value = []; form.value.default_subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: form.value.default_category_id } })
  subcatsForm.value = extractArray(r.data).filter(s => s.active)
}
const loadSubcatsPay = async () => {
  if (!payForm.value.category_id) { subcatsPay.value = []; payForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: payForm.value.category_id } })
  subcatsPay.value = extractArray(r.data).filter(s => s.active)
}

// Cascading: obras por proyecto
const loadWorksForm = async () => {
  if (!form.value.default_project_id) { worksForm.value = []; form.value.default_work_id = null; return }
  const r = await api.get('/works', { params: { project_id: form.value.default_project_id } })
  worksForm.value = extractArray(r.data).filter(w => w.active)
}
const loadWorksPay = async () => {
  if (!payForm.value.project_id) { worksPay.value = []; payForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: payForm.value.project_id } })
  worksPay.value = extractArray(r.data).filter(w => w.active)
}

// --- Apertura de modales ---
const openCreate = () => {
  form.value = {
    concept: '', total_amount: 0, installments_count: 2,
    supplier_id: null, employee_id: null,
    default_category_id: null, default_subcategory_id: null,
    default_project_id: null,  default_work_id: null,
  }
  subcatsForm.value = []
  worksForm.value = []
  showCreate.value = true
}

const openPay = async (it) => {
  payContext.value = it
  // Pre-rellenar el form de pago con los defaults del pago fraccionado
  payForm.value = {
    amount: 0,
    category_id:    it.default_category_id,
    subcategory_id: it.default_subcategory_id,
    project_id:     it.default_project_id,
    work_id:        it.default_work_id,
  }
  // Cargar subcategorías y obras si hay defaults
  if (it.default_category_id) await loadSubcatsPay()
  if (it.default_project_id)  await loadWorksPay()
  showPay.value = true
}

// --- Submits ---
const submitCreate = async () => {
  try {
    await installmentsService.create(form.value)
    showCreate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al crear el pago fraccionado')
  }
}

const submitPay = async () => {
  try {
    await installmentsService.pay(payContext.value.id, payForm.value)
    showPay.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al pagar el plazo')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>
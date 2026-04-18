<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold">Circulantes</h1>
      <button @click="openCreate" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        + Abrir circulante
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
    <table class="min-w-full bg-white border">
      <thead class="bg-gray-100">
        <tr>
          <th class="px-4 py-2 text-left">Empleado</th>
          <th class="px-4 py-2 text-right">Entregado</th>
          <th class="px-4 py-2 text-right">Justificado</th>
          <th class="px-4 py-2 text-right">Devuelto</th>
          <th class="px-4 py-2 text-right">Pendiente</th>
          <th class="px-4 py-2 text-center">Estado</th>
          <th class="px-4 py-2 text-center">Tx</th>
          <th class="px-4 py-2 text-center">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id" class="border-t">
          <td class="px-4 py-2">{{ it.employee_name }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount_given) }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount_justified) }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.amount_returned) }}</td>
          <td class="px-4 py-2 text-right font-semibold">{{ fmt(it.pending) }}</td>
          <td class="px-4 py-2 text-center">
            <span :class="statusClass(it.status)" class="px-2 py-1 rounded text-xs">{{ it.status }}</span>
          </td>
          <td class="px-4 py-2 text-center text-xs text-gray-500">
            <span v-if="it.creation_transaction_id" :title="`Apertura: #${it.creation_transaction_id}`">📄</span>
            <span v-if="it.close_transaction_id" :title="`Devolución: #${it.close_transaction_id}`">💰</span>
          </td>
          <td class="px-4 py-2 text-center">
            <button v-if="it.status !== 'closed'" @click="openJustify(it)"
              class="text-blue-600 hover:underline text-sm mr-2">Justificar</button>
            <button v-if="it.status !== 'closed'" @click="openClose(it)"
              class="text-green-600 hover:underline text-sm">Cerrar</button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="8" class="px-4 py-6 text-center text-gray-500">Sin circulantes</td>
        </tr>
      </tbody>
    </table>

    <!-- ============ Modal: Abrir circulante ============ -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Abrir circulante</h2>

        <div class="bg-blue-50 border border-blue-200 text-blue-800 text-xs rounded p-3 mb-4">
          Se creará una transacción egreso con categoría fija
          <strong>Circulantes / Apertura_Circulante</strong>. El saldo de caja bajará por el importe entregado.
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Empleado</label>
            <select v-model="form.employee_id" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Importe entregado (XAF)</label>
            <input v-model.number="form.amount_given" type="number" min="1" class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <label class="block mb-2 text-sm">Concepto (opcional)</label>
        <input v-model="form.concept" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="Ej: Combustible grupos Monte_Chocolate + Ayene" />

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

        <div class="flex justify-end gap-2">
          <button @click="showCreate = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCreate" class="px-4 py-2 bg-blue-600 text-white rounded" :disabled="!canSubmitCreate">
            Abrir
          </button>
        </div>
      </div>
    </div>

    <!-- ============ Modal: Justificar ============ -->
    <div v-if="showJustify" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Justificar gasto</h2>

        <div class="bg-gray-50 border rounded p-3 mb-4 text-sm">
          <div><span class="text-gray-500">Empleado:</span> {{ target?.employee_name }}</div>
          <div><span class="text-gray-500">Pendiente por justificar:</span>
            <span class="font-semibold">{{ fmt(target?.pending) }}</span> XAF</div>
        </div>

        <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded p-3 mb-3">
          Se crearán dos transacciones compensatorias (egreso con categoría real + ingreso
          <strong>Circulantes / Liquidacion_Circulante</strong>). El saldo de caja no cambia;
          sí se registra el gasto real por obra.
        </div>

        <label class="block mb-2 text-sm">Importe a justificar (XAF)</label>
        <input v-model.number="justifyForm.amount" type="number" min="1" :max="target?.pending"
               class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm">Concepto del gasto (opcional)</label>
        <input v-model="justifyForm.concept" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="Ej: Repostaje grupo Monte_Chocolate" />

        <p class="text-xs text-gray-500 mb-3 border-t pt-3">
          Clasificación real del gasto — aparecerá en los informes por categoría y por obra.
        </p>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Categoría</label>
            <select v-model="justifyForm.category_id" @change="loadSubcatsJustify" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Subcategoría</label>
            <select v-model="justifyForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!justifyForm.category_id">
              <option :value="null">—</option>
              <option v-for="s in subcatsJustify" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Proyecto</label>
            <select v-model="justifyForm.project_id" @change="loadWorksJustify" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">—</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Obra</label>
            <select v-model="justifyForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!justifyForm.project_id">
              <option :value="null">—</option>
              <option v-for="w in worksJustify" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>

        <div class="flex justify-end gap-2">
          <button @click="showJustify = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitJustify" class="px-4 py-2 bg-blue-600 text-white rounded" :disabled="!canSubmitJustify">
            Justificar
          </button>
        </div>
      </div>
    </div>

    <!-- ============ Modal: Cerrar ============ -->
    <div v-if="showClose" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Cerrar circulante</h2>

        <div class="bg-gray-50 border rounded p-3 mb-4 text-sm">
          <div><span class="text-gray-500">Empleado:</span> {{ target?.employee_name }}</div>
          <div><span class="text-gray-500">Entregado:</span> {{ fmt(target?.amount_given) }} XAF</div>
          <div><span class="text-gray-500">Justificado:</span> {{ fmt(target?.amount_justified) }} XAF</div>
          <div><span class="text-gray-500">Por devolver:</span>
            <span class="font-semibold">{{ fmt(target?.pending) }}</span> XAF</div>
        </div>

        <label class="block mb-2 text-sm">Importe devuelto (XAF)</label>
        <input v-model.number="closeForm.amount_returned" type="number" min="0"
               class="w-full border rounded px-3 py-2 mb-3" />

        <!-- Solo si hay devolución pedimos proyecto/obra -->
        <div v-if="Number(closeForm.amount_returned) > 0" class="border-t pt-3 mt-3 mb-3">
          <div class="bg-green-50 border border-green-200 text-green-800 text-xs rounded p-3 mb-3">
            Se creará transacción ingreso con categoría fija
            <strong>Circulantes / Devolucion_Sobrante</strong>. El saldo de caja subirá por el importe devuelto.
          </div>

          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="closeForm.project_id" @change="loadWorksClose" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="closeForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!closeForm.project_id">
                <option :value="null">—</option>
                <option v-for="w in worksClose" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div v-else class="bg-gray-50 border text-gray-600 text-xs rounded p-3 mb-3">
          Sin devolución — solo se marca el circulante como cerrado. No se crea transacción.
        </div>

        <label class="block mb-2 text-sm">Notas (opcional)</label>
        <input v-model="closeForm.notes" class="w-full border rounded px-3 py-2 mb-3" />

        <div class="flex justify-end gap-2">
          <button @click="showClose = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitClose" class="px-4 py-2 bg-green-600 text-white rounded" :disabled="!canSubmitClose">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { floatsService } from '../services/financialModulesService'
import api from '../services/api'

function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items', 'data', 'results']) if (Array.isArray(d[k])) return d[k]
  }
  console.warn('[M9 Floats] respuesta inesperada:', d)
  return []
}

// Estado
const items      = ref([])
const employees  = ref([])
const categories = ref([])
const projects   = ref([])
const worksForm    = ref([])
const subcatsJustify = ref([])
const worksJustify   = ref([])
const worksClose     = ref([])

const filterStatus = ref('')
const showCreate   = ref(false)
const showJustify  = ref(false)
const showClose    = ref(false)
const target       = ref(null)

const emptyCreateForm = () => ({
  employee_id: null, amount_given: 0, concept: '',
  project_id: null, work_id: null,
})
const emptyJustifyForm = () => ({
  amount: 0, concept: '',
  category_id: null, subcategory_id: null,
  project_id: null, work_id: null,
})
const emptyCloseForm = () => ({
  amount_returned: 0, notes: '',
  project_id: null, work_id: null,
})

const form         = ref(emptyCreateForm())
const justifyForm  = ref(emptyJustifyForm())
const closeForm    = ref(emptyCloseForm())

// Formato y estilo
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })
const statusClass = (s) => ({
  open: 'bg-blue-100 text-blue-700',
  partial: 'bg-yellow-100 text-yellow-700',
  closed: 'bg-green-100 text-green-700',
}[s] || 'bg-gray-100')

// Validaciones
const canSubmitCreate = computed(() => {
  const f = form.value
  return f.employee_id && f.amount_given > 0 && f.project_id && f.work_id
})
const canSubmitJustify = computed(() => {
  const f = justifyForm.value
  return f.amount > 0 && f.category_id && f.subcategory_id && f.project_id && f.work_id
})
const canSubmitClose = computed(() => {
  const f = closeForm.value
  if (f.amount_returned < 0) return false
  if (Number(f.amount_returned) > 0) return f.project_id && f.work_id
  return true
})

// Cargas
const load = async () => {
  items.value = await floatsService.list(filterStatus.value ? { status: filterStatus.value } : {})
}

const loadCatalogs = async () => {
  employees.value  = extractArray((await api.get('/employees')).data).filter(e => e.active)
  categories.value = extractArray((await api.get('/categories')).data).filter(c => c.active)
  projects.value   = extractArray((await api.get('/projects')).data).filter(p => p.active)
}

// Cascadings — apertura
const loadWorksForm = async () => {
  if (!form.value.project_id) { worksForm.value = []; form.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: form.value.project_id } })
  worksForm.value = extractArray(r.data).filter(w => w.active)
  form.value.work_id = null
}

// Cascadings — justificación
const loadSubcatsJustify = async () => {
  if (!justifyForm.value.category_id) { subcatsJustify.value = []; justifyForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: justifyForm.value.category_id } })
  subcatsJustify.value = extractArray(r.data).filter(s => s.active)
  justifyForm.value.subcategory_id = null
}
const loadWorksJustify = async () => {
  if (!justifyForm.value.project_id) { worksJustify.value = []; justifyForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: justifyForm.value.project_id } })
  worksJustify.value = extractArray(r.data).filter(w => w.active)
  justifyForm.value.work_id = null
}

// Cascadings — cierre
const loadWorksClose = async () => {
  if (!closeForm.value.project_id) { worksClose.value = []; closeForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: closeForm.value.project_id } })
  worksClose.value = extractArray(r.data).filter(w => w.active)
  closeForm.value.work_id = null
}

// Apertura de modales
const openCreate = () => {
  form.value = emptyCreateForm()
  worksForm.value = []
  showCreate.value = true
}
const openJustify = (it) => {
  target.value = it
  justifyForm.value = emptyJustifyForm()
  subcatsJustify.value = []
  worksJustify.value = []
  showJustify.value = true
}
const openClose = (it) => {
  target.value = it
  closeForm.value = { ...emptyCloseForm(), amount_returned: Number(it.pending) || 0 }
  worksClose.value = []
  showClose.value = true
}

// Submits
const submitCreate = async () => {
  try {
    await floatsService.create(form.value)
    showCreate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al abrir el circulante')
  }
}
const submitJustify = async () => {
  try {
    await floatsService.justify(target.value.id, justifyForm.value)
    showJustify.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al justificar')
  }
}
const submitClose = async () => {
  try {
    await floatsService.close(target.value.id, closeForm.value)
    showClose.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al cerrar el circulante')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>

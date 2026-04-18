<template>
  <div class="p-6">
    <!-- Cabecera -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold">Envíos de dinero</h1>
        <p class="text-sm text-gray-500">Western Union, MoneyGram y operadores locales</p>
      </div>
      <button @click="openCreate"
        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow">
        + Nuevo envío
      </button>
    </div>

    <!-- Panel de posición Bata ↔ Malabo -->
    <div v-if="position" class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
      <div class="bg-white p-4 rounded shadow">
        <div class="text-xs text-gray-500">Bata → Malabo</div>
        <div class="text-xl font-bold">{{ fmt(position.bata_to_malabo) }} XAF</div>
      </div>
      <div class="bg-white p-4 rounded shadow">
        <div class="text-xs text-gray-500">Malabo → Bata</div>
        <div class="text-xl font-bold">{{ fmt(position.malabo_to_bata) }} XAF</div>
      </div>
      <div class="bg-white p-4 rounded shadow">
        <div class="text-xs text-gray-500">Posición neta</div>
        <div class="text-xl font-bold">{{ fmt(position.net_position) }} XAF</div>
      </div>
      <div class="bg-white p-4 rounded shadow">
        <div class="text-xs text-gray-500">A favor de</div>
        <div class="text-sm font-medium">{{ position.favor_delegation || 'Equilibrado' }}</div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 mb-4">
      <select v-model="filterOperator" @change="load" class="border rounded px-3 py-2 text-sm">
        <option value="">Todos los operadores</option>
        <option value="western_union">Western Union</option>
        <option value="moneygram">MoneyGram</option>
        <option value="operador_local">Operador local</option>
      </select>
      <select v-model="filterDirection" @change="load" class="border rounded px-3 py-2 text-sm">
        <option value="">Todas las direcciones</option>
        <option value="sent">Enviados</option>
        <option value="received">Recibidos</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-100 text-gray-700">
          <tr>
            <th class="px-3 py-2 text-left">Fecha</th>
            <th class="px-3 py-2 text-left">Operador</th>
            <th class="px-3 py-2 text-left">Referencia</th>
            <th class="px-3 py-2 text-left">Remitente → Receptor</th>
            <th class="px-3 py-2 text-right">Importe</th>
            <th class="px-3 py-2 text-right">Comisión</th>
            <th class="px-3 py-2 text-center">Dirección</th>
            <th class="px-3 py-2 text-center">Ruta</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="items.length === 0">
            <td colspan="8" class="px-3 py-6 text-center text-gray-500">
              No hay envíos registrados
            </td>
          </tr>
          <tr v-for="it in items" :key="it.id" class="border-t hover:bg-gray-50">
            <td class="px-3 py-2">{{ fmtDate(it.created_at) }}</td>
            <td class="px-3 py-2">{{ it.operator_label || it.operator }}</td>
            <td class="px-3 py-2 font-mono text-xs">{{ it.reference_number }}</td>
            <td class="px-3 py-2">
              <div>{{ it.sender_name }}</div>
              <div class="text-xs text-gray-500">→ {{ it.receiver_name }}</div>
            </td>
            <td class="px-3 py-2 text-right">{{ fmt(it.amount) }}</td>
            <td class="px-3 py-2 text-right text-gray-600">
              {{ it.commission_amount ? fmt(it.commission_amount) : '—' }}
            </td>
            <td class="px-3 py-2 text-center">
              <span :class="it.direction === 'sent' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'"
                class="px-2 py-1 rounded text-xs font-medium">
                {{ it.direction_label || it.direction }}
              </span>
            </td>
            <td class="px-3 py-2 text-center text-xs text-gray-600">
              {{ it.delegacion_origin || 'Exterior' }} → {{ it.delegacion_dest || 'Exterior' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal: Crear -->
    <div v-if="showCreate" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold mb-4">Nuevo envío de dinero</h2>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-sm font-medium mb-1">Operador *</label>
            <select v-model="form.operator" class="w-full border rounded px-3 py-2">
              <option value="western_union">Western Union</option>
              <option value="moneygram">MoneyGram</option>
              <option value="operador_local">Operador local</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Dirección *</label>
            <select v-model="form.direction" class="w-full border rounded px-3 py-2">
              <option value="sent">Enviado</option>
              <option value="received">Recibido</option>
            </select>
          </div>
        </div>

        <label class="block text-sm font-medium mb-1">Referencia / localizador *</label>
        <input v-model="form.reference_number" type="text"
          class="w-full border rounded px-3 py-2 mb-3"
          placeholder="Ej. MTCN WU1234567890" />

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-sm font-medium mb-1">Remitente *</label>
            <select v-model.number="form.sender_id" @change="onSenderChange"
              class="w-full border rounded px-3 py-2 mb-1">
              <option :value="null">— Texto libre —</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
            <input v-model="form.sender_name" type="text"
              class="w-full border rounded px-3 py-2"
              placeholder="Nombre completo" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Receptor *</label>
            <select v-model.number="form.receiver_id" @change="onReceiverChange"
              class="w-full border rounded px-3 py-2 mb-1">
              <option :value="null">— Texto libre —</option>
              <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
            </select>
            <input v-model="form.receiver_name" type="text"
              class="w-full border rounded px-3 py-2"
              placeholder="Nombre completo" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-sm font-medium mb-1">Importe XAF *</label>
            <input v-model.number="form.amount" type="number" step="1" min="1"
              class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Comisión XAF</label>
            <input v-model.number="form.commission" type="number" step="1" min="0"
              class="w-full border rounded px-3 py-2" />
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block text-sm font-medium mb-1">Delegación origen</label>
            <select v-model="form.delegacion_origin" class="w-full border rounded px-3 py-2">
              <option :value="null">Exterior / No aplica</option>
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">Delegación destino</label>
            <select v-model="form.delegacion_dest" class="w-full border rounded px-3 py-2">
              <option :value="null">Exterior / No aplica</option>
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
        </div>

        <label class="block text-sm font-medium mb-1">Categoría *</label>
        <select v-model.number="form.category_id" @change="onCategoryChange"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona categoría —</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Subcategoría *</label>
        <select v-model.number="form.subcategory_id"
          :disabled="!form.category_id"
          class="w-full border rounded px-3 py-2 mb-3 disabled:bg-gray-100">
          <option :value="null">— Selecciona subcategoría —</option>
          <option v-for="s in subcats" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Proyecto *</label>
        <select v-model.number="form.project_id" @change="onProjectChange"
          class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona proyecto —</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>

        <label class="block text-sm font-medium mb-1">Obra *</label>
        <select v-model.number="form.work_id"
          :disabled="!form.project_id"
          class="w-full border rounded px-3 py-2 mb-4 disabled:bg-gray-100">
          <option :value="null">— Selecciona obra —</option>
          <option v-for="w in works" :key="w.id" :value="w.id">{{ w.name }}</option>
        </select>

        <div class="flex justify-end gap-2">
          <button @click="showCreate = false"
            class="px-4 py-2 border rounded hover:bg-gray-50">Cancelar</button>
          <button @click="submit"
            class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
            Registrar envío
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { moneyTransfersService } from '../services/financialModulesService'

// --- Estado ---
const items = ref([])
const position = ref(null)
const categories = ref([])
const subcats = ref([])
const projects = ref([])
const works = ref([])
const employees = ref([])
const filterOperator = ref('')
const filterDirection = ref('')
const showCreate = ref(false)

const defaultForm = () => ({
  operator: 'western_union',
  reference_number: '',
  sender_name: '',
  receiver_name: '',
  sender_id: null,
  receiver_id: null,
  amount: 0,
  commission: 0,
  direction: 'sent',
  delegacion_origin: null,
  delegacion_dest: null,
  category_id: null,
  subcategory_id: null,
  project_id: null,
  work_id: null,
})
const form = ref(defaultForm())

// --- Helpers ---
const extractArray = (r) => Array.isArray(r) ? r : (r?.items || r?.data || [])
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })
const fmtDate = (v) => {
  if (!v) return '—'
  const d = new Date(v)
  return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

// --- Carga ---
const load = async () => {
  try {
    const params = {}
    if (filterOperator.value) params.operator = filterOperator.value
    if (filterDirection.value) params.direction = filterDirection.value
    items.value = extractArray(await moneyTransfersService.list(params))
    try {
      position.value = await moneyTransfersService.position()
    } catch {
      position.value = null
    }
  } catch (e) {
    console.error('Error cargando envíos', e)
    items.value = []
  }
}

const loadCatalogs = async () => {
  try {
    const [cr, pr, er] = await Promise.all([
      api.get('/categories'),
      api.get('/projects'),
      api.get('/employees'),
    ])
    categories.value = extractArray(cr.data).filter(c => c.active)
    projects.value = extractArray(pr.data).filter(p => p.active)
    employees.value = extractArray(er.data).filter(e => e.active)
  } catch (e) {
    console.error('Error cargando catálogos', e)
  }
}

const onCategoryChange = async () => {
  form.value.subcategory_id = null
  subcats.value = []
  if (!form.value.category_id) return
  try {
    const r = await api.get('/subcategories', { params: { category_id: form.value.category_id } })
    subcats.value = extractArray(r.data).filter(s => s.active)
  } catch (e) {
    console.error('Error cargando subcategorías', e)
  }
}

const onProjectChange = async () => {
  form.value.work_id = null
  works.value = []
  if (!form.value.project_id) return
  try {
    const r = await api.get('/works', { params: { project_id: form.value.project_id } })
    works.value = extractArray(r.data).filter(w => w.active)
  } catch (e) {
    console.error('Error cargando obras', e)
  }
}

const onSenderChange = () => {
  if (form.value.sender_id) {
    const emp = employees.value.find(e => e.id === form.value.sender_id)
    if (emp) form.value.sender_name = emp.full_name
  }
}

const onReceiverChange = () => {
  if (form.value.receiver_id) {
    const emp = employees.value.find(e => e.id === form.value.receiver_id)
    if (emp) form.value.receiver_name = emp.full_name
  }
}

// --- Acciones ---
const openCreate = () => {
  form.value = defaultForm()
  subcats.value = []
  works.value = []
  showCreate.value = true
}

const submit = async () => {
  // Validaciones
  if (!form.value.reference_number || form.value.reference_number.trim().length < 3) {
    alert('La referencia debe tener al menos 3 caracteres'); return
  }
  if (!form.value.sender_name || form.value.sender_name.trim().length < 3) {
    alert('El nombre del remitente debe tener al menos 3 caracteres'); return
  }
  if (!form.value.receiver_name || form.value.receiver_name.trim().length < 3) {
    alert('El nombre del receptor debe tener al menos 3 caracteres'); return
  }
  if (!(form.value.amount > 0)) {
    alert('El importe debe ser mayor que cero'); return
  }
  if (form.value.commission < 0) {
    alert('La comisión no puede ser negativa'); return
  }
  if (!form.value.category_id) { alert('Selecciona una categoría'); return }
  if (!form.value.subcategory_id) { alert('Selecciona una subcategoría'); return }
  if (!form.value.project_id) { alert('Selecciona un proyecto'); return }
  if (!form.value.work_id) { alert('Selecciona una obra'); return }

  try {
    await moneyTransfersService.create(form.value)
    showCreate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al registrar el envío')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>
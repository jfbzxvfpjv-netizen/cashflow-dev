<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Cuentas de Socios</h1>
      <button @click="openCharge" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        + Cargar gasto a socio
      </button>
    </div>

    <!-- Saldos -->
    <h2 class="text-lg font-semibold mb-2">Saldos actuales</h2>
    <table class="w-full bg-white rounded shadow mb-6">
      <thead class="bg-gray-100 text-left text-sm">
        <tr>
          <th class="px-4 py-2">Socio</th>
          <th class="px-4 py-2 text-right">Participación</th>
          <th class="px-4 py-2 text-right">Saldo actual</th>
          <th class="px-4 py-2">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!balances.length">
          <td colspan="4" class="text-center py-6 text-gray-500">Sin socios</td>
        </tr>
        <tr v-for="b in balances" :key="b.partner_id" class="border-t">
          <td class="px-4 py-2">{{ b.partner_name }}</td>
          <td class="px-4 py-2 text-right">{{ b.participation_pct }}%</td>
          <td class="px-4 py-2 text-right"
              :class="Number(b.current_balance) > 0 ? 'text-red-600' : 'text-green-600'">
            {{ fmt(b.current_balance) }} XAF
          </td>
          <td class="px-4 py-2 text-sm">
            <button v-if="canContribute(b)" @click="openContribution(b)"
                    class="text-blue-600 hover:underline mr-3">Devolución</button>
            <button @click="openCompensate(b)"
                    class="text-green-600 hover:underline">Compensar dividendos</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Movimientos -->
    <h2 class="text-lg font-semibold mb-2">Movimientos recientes</h2>
    <table class="w-full bg-white rounded shadow">
      <thead class="bg-gray-100 text-left text-sm">
        <tr>
          <th class="px-4 py-2">Fecha</th>
          <th class="px-4 py-2">Socio</th>
          <th class="px-4 py-2">Tipo</th>
          <th class="px-4 py-2 text-right">Importe</th>
          <th class="px-4 py-2">Concepto</th>
          <th class="px-4 py-2 text-center">Tx</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!movements.length">
          <td colspan="6" class="text-center py-6 text-gray-500">Sin movimientos</td>
        </tr>
        <tr v-for="m in movements" :key="m.id" class="border-t">
          <td class="px-4 py-2 text-sm">{{ new Date(m.created_at).toLocaleDateString('es-ES') }}</td>
          <td class="px-4 py-2">{{ m.partner_name }}</td>
          <td class="px-4 py-2">
            <span class="px-2 py-1 rounded text-xs"
                  :class="{
                    'bg-red-100 text-red-800': m.type === 'charge',
                    'bg-blue-100 text-blue-800': m.type === 'contribution',
                    'bg-green-100 text-green-800': m.type === 'dividend_compensation',
                  }">
              {{ typeLabel(m.type) }}
            </span>
          </td>
          <td class="px-4 py-2 text-right">{{ fmt(m.amount) }}</td>
          <td class="px-4 py-2">{{ m.concept }}</td>
          <td class="px-4 py-2 text-center text-xs text-gray-500">
            <span v-if="m.transaction_id" :title="`Transacción #${m.transaction_id}`">📄</span>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- ===== Modal: Cargar gasto a socio ===== -->
    <div v-if="showCharge" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Cargar gasto a socio</h2>

        <div class="bg-red-50 border border-red-200 text-red-800 text-xs rounded p-3 mb-3">
          Egreso de caja a cuenta del socio — el saldo de caja baja y la deuda del socio sube.
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Socio</label>
            <select v-model="chargeForm.partner_id" class="w-full border rounded px-3 py-2 truncate">
              <option :value="null">— Socio —</option>
              <option v-for="b in balances" :key="b.partner_id" :value="b.partner_id">{{ b.partner_name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-2 text-sm">Delegación (caja de origen)</label>
            <select v-model="chargeForm.delegacion" class="w-full border rounded px-3 py-2">
              <option :value="null">— Delegación —</option>
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
        </div>

        <label class="block mb-2 text-sm">Importe (XAF)</label>
        <input v-model.number="chargeForm.amount" type="number" min="1" class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm">Concepto</label>
        <input v-model="chargeForm.concept" class="w-full border rounded px-3 py-2 mb-3" />

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">Imputación contable del egreso</p>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="chargeForm.category_id" @change="loadSubcatsCharge" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="chargeForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!chargeForm.category_id">
                <option :value="null">—</option>
                <option v-for="s in subcatsCharge" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="chargeForm.project_id" @change="loadWorksCharge" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="chargeForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!chargeForm.project_id">
                <option :value="null">—</option>
                <option v-for="w in worksCharge" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button @click="showCharge = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCharge" class="px-4 py-2 bg-blue-600 text-white rounded" :disabled="!canSubmitCharge">
            Registrar
          </button>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Aportación ===== -->
    <div v-if="showContribution" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Devolución del socio</h2>

        <div class="bg-green-50 border border-green-200 text-green-800 text-xs rounded p-3 mb-3">
          El socio devuelve dinero a caja para saldar deuda con la empresa — la caja sube y la deuda del socio baja.
          Se creará una transacción ingreso.
        </div>

        <div class="bg-gray-50 border rounded p-3 mb-4 text-sm">
          <div><span class="text-gray-500">Socio:</span> <strong>{{ selected?.partner_name }}</strong></div>
          <div><span class="text-gray-500">Saldo actual:</span> {{ fmt(selected?.current_balance) }} XAF</div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Importe devuelto (XAF)</label>
            <input v-model.number="contribForm.amount" type="number" min="1" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-2 text-sm">Delegación (caja de destino)</label>
            <select v-model="contribForm.delegacion" class="w-full border rounded px-3 py-2">
              <option :value="null">— Delegación —</option>
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
        </div>

        <label class="block mb-2 text-sm">Concepto</label>
        <input v-model="contribForm.concept" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="Motivo de la devolución" />

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">Imputación contable del ingreso</p>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="contribForm.category_id" @change="loadSubcatsContrib" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="contribForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!contribForm.category_id">
                <option :value="null">—</option>
                <option v-for="s in subcatsContrib" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="contribForm.project_id" @change="loadWorksContrib" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="contribForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!contribForm.project_id">
                <option :value="null">—</option>
                <option v-for="w in worksContrib" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button @click="showContribution = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitContribution" class="px-4 py-2 bg-blue-600 text-white rounded" :disabled="!canSubmitContrib">
            Registrar
          </button>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Compensar dividendos ===== -->
    <div v-if="showCompensate" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-xl mx-4">
        <h2 class="text-lg font-bold mb-2">Compensación por dividendos</h2>

        <div class="bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded p-3 mb-3">
          Apunte contable interno — NO crea transacción en caja. Solo reduce la deuda del socio.
        </div>

        <p class="text-sm mb-4">Socio: <strong>{{ selected?.partner_name }}</strong></p>

        <label class="block mb-2 text-sm">Importe a compensar (XAF)</label>
        <input v-model.number="compForm.amount" type="number" min="1" class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm">Concepto</label>
        <input v-model="compForm.concept" class="w-full border rounded px-3 py-2 mb-3" />

        <div class="flex justify-end gap-2">
          <button @click="showCompensate = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitCompensate" class="px-4 py-2 bg-green-600 text-white rounded">Compensar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api'
import { partnerAccountsService } from '../services/financialModulesService'

function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items', 'data', 'results']) if (Array.isArray(d[k])) return d[k]
  }
  return []
}

// Estado
const balances   = ref([])
const movements  = ref([])
const partnersFull = ref([])  // Para leer can_contribute
const categories = ref([])
const projects   = ref([])
const subcatsCharge  = ref([]); const worksCharge  = ref([])
const subcatsContrib = ref([]); const worksContrib = ref([])

const showCharge       = ref(false)
const showContribution = ref(false)
const showCompensate   = ref(false)
const selected         = ref(null)

const emptyCharge = () => ({
  partner_id: null, amount: 0, concept: '', delegacion: null,
  category_id: null, subcategory_id: null, project_id: null, work_id: null,
})
const emptyContrib = () => ({
  partner_id: null, amount: 0, concept: '', delegacion: null,
  category_id: null, subcategory_id: null, project_id: null, work_id: null,
})
const emptyComp = () => ({
  partner_id: null, amount: 0, concept: '',
})

const chargeForm  = ref(emptyCharge())
const contribForm = ref(emptyContrib())
const compForm    = ref(emptyComp())

// Utilidades
const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })

const typeLabel = (t) => ({
  charge: 'Cargo',
  contribution: 'Devolución',
  dividend_compensation: 'Comp. dividendos',
})[t] || t

// Determina si el socio puede hacer aportaciones leyendo de partnersFull
const canContribute = (b) => {
  const p = partnersFull.value.find(x => x.id === b.partner_id)
  return p && p.can_contribute
}

// Validaciones
const canSubmitCharge = computed(() => {
  const f = chargeForm.value
  return f.partner_id && f.amount > 0 && f.concept && f.delegacion
    && f.category_id && f.subcategory_id && f.project_id && f.work_id
})
const canSubmitContrib = computed(() => {
  const f = contribForm.value
  return f.partner_id && f.amount > 0 && f.concept && f.delegacion
    && f.category_id && f.subcategory_id && f.project_id && f.work_id
})

// Cargas
const load = async () => {
  balances.value  = await partnerAccountsService.balances()
  movements.value = await partnerAccountsService.movements()
  partnersFull.value = extractArray((await api.get('/partners')).data).filter(p => p.active)
}

const loadCatalogs = async () => {
  categories.value = extractArray((await api.get('/categories')).data).filter(c => c.active)
  projects.value   = extractArray((await api.get('/projects')).data).filter(p => p.active)
}

// Cascadings - Charge
const loadSubcatsCharge = async () => {
  if (!chargeForm.value.category_id) { subcatsCharge.value = []; chargeForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: chargeForm.value.category_id } })
  subcatsCharge.value = extractArray(r.data).filter(s => s.active)
  chargeForm.value.subcategory_id = null
}
const loadWorksCharge = async () => {
  if (!chargeForm.value.project_id) { worksCharge.value = []; chargeForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: chargeForm.value.project_id } })
  worksCharge.value = extractArray(r.data).filter(w => w.active)
  chargeForm.value.work_id = null
}

// Cascadings - Contribution
const loadSubcatsContrib = async () => {
  if (!contribForm.value.category_id) { subcatsContrib.value = []; contribForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: contribForm.value.category_id } })
  subcatsContrib.value = extractArray(r.data).filter(s => s.active)
  contribForm.value.subcategory_id = null
}
const loadWorksContrib = async () => {
  if (!contribForm.value.project_id) { worksContrib.value = []; contribForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: contribForm.value.project_id } })
  worksContrib.value = extractArray(r.data).filter(w => w.active)
  contribForm.value.work_id = null
}

// Apertura de modales
const openCharge = () => {
  chargeForm.value = emptyCharge()
  subcatsCharge.value = []; worksCharge.value = []
  showCharge.value = true
}
const openContribution = (b) => {
  selected.value = b
  contribForm.value = { ...emptyContrib(), partner_id: b.partner_id }
  subcatsContrib.value = []; worksContrib.value = []
  showContribution.value = true
}
const openCompensate = (b) => {
  selected.value = b
  compForm.value = { ...emptyComp(), partner_id: b.partner_id }
  showCompensate.value = true
}

// Submits
const submitCharge = async () => {
  try {
    await partnerAccountsService.charge(chargeForm.value)
    showCharge.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al registrar cargo')
  }
}
const submitContribution = async () => {
  try {
    await partnerAccountsService.contribution(contribForm.value)
    showContribution.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al registrar devolución')
  }
}
const submitCompensate = async () => {
  try {
    await partnerAccountsService.compensate(compForm.value)
    showCompensate.value = false
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al compensar')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await load()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-6">
    <!-- Título y selector de delegación -->
    <div class="flex flex-wrap items-center justify-between mb-6 gap-4">
      <h1 class="text-2xl font-bold text-gray-800">Panel Principal</h1>
      <div v-if="canSelectDelegacion" class="flex gap-2">
        <button
          v-for="d in ['Bata','Malabo','Consolidado']" :key="d"
          @click="selectedDelegacion = d; loadDashboard()"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            selectedDelegacion === d
              ? 'bg-blue-600 text-white shadow'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
        >{{ d }}</button>
      </div>
    </div>

    <!-- Indicadores principales -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-white rounded-xl shadow p-5 border-l-4 border-blue-500">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Saldo actual</p>
        <p class="text-2xl font-bold text-blue-700 mt-1">{{ formatAmount(data.saldo_actual) }} <span class="text-sm font-normal">XAF</span></p>
      </div>
      <div class="bg-white rounded-xl shadow p-5 border-l-4 border-green-500">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Ingresos hoy</p>
        <p class="text-2xl font-bold text-green-600 mt-1">{{ formatAmount(data.ingresos_hoy) }} <span class="text-sm font-normal">XAF</span></p>
      </div>
      <div class="bg-white rounded-xl shadow p-5 border-l-4 border-red-500">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Egresos hoy</p>
        <p class="text-2xl font-bold text-red-600 mt-1">{{ formatAmount(data.egresos_hoy) }} <span class="text-sm font-normal">XAF</span></p>
      </div>
      <div class="bg-white rounded-xl shadow p-5 border-l-4 border-purple-500">
        <p class="text-xs text-gray-500 uppercase tracking-wide">Transacciones hoy</p>
        <p class="text-2xl font-bold text-purple-700 mt-1">{{ data.transacciones_hoy }}</p>
      </div>
    </div>

    <!-- Alertas prioritarias -->
    <div v-if="hasAlerts" class="mb-6 space-y-2">
      <div v-if="data.alertas.pending_approval > 0"
        class="flex items-center justify-between bg-amber-50 border border-amber-200 rounded-lg p-3 cursor-pointer hover:bg-amber-100 transition"
        @click="$router.push('/approvals')">
        <div class="flex items-center gap-3">
          <span class="text-amber-500 text-xl">⚠️</span>
          <span class="text-sm text-amber-800 font-medium">
            {{ data.alertas.pending_approval }} transacción(es) pendiente(s) de aprobación
          </span>
        </div>
        <span class="text-amber-400">→</span>
      </div>
      <div v-if="data.alertas.authorized_pending > 0"
        class="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3 cursor-pointer hover:bg-blue-100 transition"
        @click="$router.push('/transactions?approval_status=authorized')">
        <div class="flex items-center gap-3">
          <span class="text-blue-500 text-xl">🔵</span>
          <span class="text-sm text-blue-800 font-medium">
            {{ data.alertas.authorized_pending }} transacción(es) autorizada(s) pendiente(s) de ejecución
          </span>
        </div>
        <span class="text-blue-400">→</span>
      </div>
      <div v-if="data.alertas.bank_withdrawals_pending > 0"
        class="flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-lg p-3 cursor-pointer hover:bg-indigo-100 transition"
        @click="$router.push('/bank-withdrawals')">
        <div class="flex items-center gap-3">
          <span class="text-indigo-500 text-xl">🏧</span>
          <span class="text-sm text-indigo-800 font-medium">
            {{ data.alertas.bank_withdrawals_pending }} retirada(s) bancaria(s) pendiente(s)
          </span>
        </div>
        <span class="text-indigo-400">→</span>
      </div>
    </div>

    <!-- Selector de fechas -->
    <div class="bg-white rounded-xl shadow p-4 mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500">Desde</label>
          <input type="date" v-model="dateStart" @change="loadDashboard()"
            class="border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-gray-500">Hasta</label>
          <input type="date" v-model="dateEnd" @change="loadDashboard()"
            class="border rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <div class="flex gap-1 flex-wrap">
          <button v-for="q in quickDates" :key="q.label" @click="applyQuick(q)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              isActiveQuick(q)
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
            ]"
          >{{ q.label }}</button>
        </div>
      </div>
    </div>

    <!-- Gráficos -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="bg-white rounded-xl shadow p-5">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Evolución del saldo</h3>
        <div style="height:280px">
          <Line v-if="chartEvolucionData" :data="chartEvolucionData" :options="chartEvolucionOpts" />
          <p v-else class="text-sm text-gray-400 text-center pt-20">Sin datos para el período seleccionado</p>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow p-5">
        <h3 class="text-sm font-semibold text-gray-700 mb-3">Ingresos vs Egresos</h3>
        <div style="height:280px">
          <Bar v-if="chartBarrasData" :data="chartBarrasData" :options="chartBarrasOpts" />
          <p v-else class="text-sm text-gray-400 text-center pt-20">Sin datos para el período seleccionado</p>
        </div>
      </div>
    </div>

    <!-- Filtros inline de la tabla -->
    <div class="bg-white rounded-xl shadow p-4 mb-2">
      <div class="flex flex-wrap items-center gap-3">
        <select v-model="filterTipo" @change="loadDashboard()"
          class="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">Todos los tipos</option>
          <option value="income">Ingresos</option>
          <option value="expense">Egresos</option>
        </select>
        <select v-model="filterCategory" @change="loadDashboard()"
          class="border rounded-lg px-3 py-1.5 text-sm">
          <option value="">Todas las categorías</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <button @click="exportTable('xlsx')"
          class="ml-auto px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 transition">
          📥 Excel
        </button>
        <button @click="exportTable('pdf')"
          class="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-medium hover:bg-red-700 transition">
          📄 PDF
        </button>
      </div>
    </div>

    <!-- Tabla de movimientos -->
    <div class="bg-white rounded-xl shadow overflow-hidden mb-6">
      <div v-if="loading" class="p-10 text-center text-gray-400">Cargando...</div>
      <div v-else-if="!movimientos.items || movimientos.items.length === 0" class="p-10 text-center text-gray-400">
        No hay movimientos en el período seleccionado
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 text-gray-600 uppercase text-xs">
              <th class="px-4 py-3 text-left">Fecha</th>
              <th class="px-4 py-3 text-left">Ref.</th>
              <th class="px-4 py-3 text-left">Concepto</th>
              <th class="px-4 py-3 text-left">Categoría</th>
              <th class="px-4 py-3 text-left">Contraparte</th>
              <th class="px-4 py-3 text-right">Importe</th>
              <th class="px-4 py-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in movimientos.items" :key="m.id"
              @click="$router.push(`/transactions/${m.id}`)"
              class="border-b border-gray-100 hover:bg-blue-50 cursor-pointer transition-colors"
              :class="{ 'opacity-50 line-through': m.cancelled }">
              <td class="px-4 py-3 whitespace-nowrap text-xs text-gray-500">
                {{ formatFecha(m.fecha) }}
              </td>
              <td class="px-4 py-3 font-mono text-xs">{{ m.referencia }}</td>
              <td class="px-4 py-3 max-w-xs truncate">{{ m.concepto }}</td>
              <td class="px-4 py-3 text-xs">{{ m.categoria }}</td>
              <td class="px-4 py-3 text-xs">{{ m.contraparte }}</td>
              <td class="px-4 py-3 text-right font-semibold whitespace-nowrap"
                :class="m.tipo === 'income' ? 'text-green-600' : 'text-red-600'">
                {{ m.tipo === 'income' ? '+' : '-' }} {{ formatAmount(m.importe) }}
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="estadoClass(m.estado)" class="px-2 py-0.5 rounded-full text-xs font-medium">
                  {{ m.estado }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Paginación -->
      <div v-if="movimientos.pages > 1" class="flex items-center justify-between px-4 py-3 bg-gray-50 border-t">
        <p class="text-xs text-gray-500">
          Página {{ movimientos.page }} de {{ movimientos.pages }} — {{ movimientos.total }} registros
        </p>
        <div class="flex gap-1">
          <button @click="goPage(movimientos.page - 1)" :disabled="movimientos.page <= 1"
            class="px-3 py-1 rounded bg-gray-200 text-xs disabled:opacity-50 hover:bg-gray-300">← Anterior</button>
          <button @click="goPage(movimientos.page + 1)" :disabled="movimientos.page >= movimientos.pages"
            class="px-3 py-1 rounded bg-gray-200 text-xs disabled:opacity-50 hover:bg-gray-300">Siguiente →</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import dashboardService from '@/services/dashboardService'
import reportService from '@/services/reportService'
import api from '@/services/api'
import { Line, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, BarElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Title, Tooltip, Legend, Filler
)

const router = useRouter()
const auth = useAuthStore()

// --- Estado ---
const loading = ref(false)
const data = ref({
  saldo_actual: 0, ingresos_hoy: 0, egresos_hoy: 0, transacciones_hoy: 0,
  alertas: { pending_approval: 0, authorized_pending: 0, bank_withdrawals_pending: 0 },
  movimientos: { items: [], total: 0, page: 1, pages: 0 },
  grafico_evolucion: [],
  grafico_ingresos_egresos: []
})
const movimientos = ref({ items: [], total: 0, page: 1, pages: 0, page_size: 50 })
const categories = ref([])

// Selector delegación
const selectedDelegacion = ref(
  auth.user?.role === 'gestor' ? auth.user.delegacion : 'Consolidado'
)
const canSelectDelegacion = computed(() =>
  ['admin', 'contable', 'consulta'].includes(auth.user?.role)
)

// Fechas
const today = new Date()
const dateStart = ref(formatDateISO(new Date(today.getFullYear(), today.getMonth(), 1)))
const dateEnd = ref(formatDateISO(today))
const currentPage = ref(1)

// Filtros inline
const filterTipo = ref('')
const filterCategory = ref('')

// Accesos rápidos
const quickDates = [
  { label: 'Hoy', fn: () => { const t = new Date(); return [t, t] } },
  { label: 'Ayer', fn: () => { const t = new Date(); t.setDate(t.getDate()-1); return [t, t] } },
  { label: 'Esta semana', fn: () => {
    const t = new Date(); const d = t.getDay() || 7;
    const s = new Date(t); s.setDate(t.getDate() - d + 1);
    return [s, t]
  }},
  { label: 'Este mes', fn: () => {
    const t = new Date(); return [new Date(t.getFullYear(), t.getMonth(), 1), t]
  }},
  { label: 'Mes anterior', fn: () => {
    const t = new Date();
    return [new Date(t.getFullYear(), t.getMonth()-1, 1), new Date(t.getFullYear(), t.getMonth(), 0)]
  }}
]
const activeQuick = ref('Este mes')

// --- Helpers ---
function formatDateISO(d) {
  return d.toISOString().split('T')[0]
}
function formatFecha(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('es-ES', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
}
function formatAmount(n) {
  if (n == null) return '0'
  return Math.round(Number(n)).toLocaleString('es-ES')
}
function estadoClass(e) {
  const map = {
    aprobada: 'bg-green-100 text-green-700',
    pendiente: 'bg-amber-100 text-amber-700',
    autorizada: 'bg-blue-100 text-blue-700',
    rechazada: 'bg-red-100 text-red-700',
    anulada: 'bg-gray-200 text-gray-500'
  }
  return map[e] || 'bg-gray-100 text-gray-600'
}

// --- Alertas ---
const hasAlerts = computed(() => {
  const a = data.value.alertas
  return a && (a.pending_approval > 0 || a.authorized_pending > 0 || a.bank_withdrawals_pending > 0)
})

// --- Gráficos ---
const chartEvolucionData = computed(() => {
  const g = data.value.grafico_evolucion
  if (!g || g.length === 0) return null
  return {
    labels: g.map(p => {
      const parts = p.fecha.split('-')
      return `${parts[2]}/${parts[1]}`
    }),
    datasets: [{
      label: 'Saldo (XAF)',
      data: g.map(p => p.saldo),
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37,99,235,0.08)',
      fill: true,
      tension: 0.3,
      pointRadius: g.length > 60 ? 0 : 3,
      pointHoverRadius: 5
    }]
  }
})
const chartEvolucionOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
  scales: { y: { ticks: { callback: v => (v/1e6).toFixed(1) + 'M' } }, x: { ticks: { maxTicksLimit: 15 } } }
}

const chartBarrasData = computed(() => {
  const g = data.value.grafico_ingresos_egresos
  if (!g || g.length === 0) return null
  return {
    labels: g.map(p => {
      if (p.fecha.startsWith('Sem')) return p.fecha
      const parts = p.fecha.split('-')
      return `${parts[2]}/${parts[1]}`
    }),
    datasets: [
      { label: 'Ingresos', data: g.map(p => p.ingresos), backgroundColor: '#16a34a' },
      { label: 'Egresos', data: g.map(p => p.egresos), backgroundColor: '#dc2626' }
    ]
  }
})
const chartBarrasOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: 'top' }, tooltip: { mode: 'index', intersect: false } },
  scales: { y: { ticks: { callback: v => (v/1e6).toFixed(1) + 'M' } }, x: { ticks: { maxTicksLimit: 15 } } }
}

// --- Cargar datos ---
async function loadDashboard() {
  loading.value = true
  try {
    const params = {
      date_start: dateStart.value,
      date_end: dateEnd.value,
      page: currentPage.value,
      page_size: 50
    }
    if (canSelectDelegacion.value) {
      params.delegacion = selectedDelegacion.value
    }
    if (filterTipo.value) params.tipo = filterTipo.value
    if (filterCategory.value) params.category_id = filterCategory.value

    const res = await dashboardService.getSummary(params)
    data.value = res.data
    movimientos.value = res.data.movimientos || { items: [], total: 0, page: 1, pages: 0 }
  } catch (e) {
    console.error('Error cargando dashboard:', e)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    const res = await api.get('/categories')
    categories.value = res.data || []
  } catch (e) {
    console.error('Error cargando categorías:', e)
  }
}

function applyQuick(q) {
  const [s, e] = q.fn()
  dateStart.value = formatDateISO(s)
  dateEnd.value = formatDateISO(e)
  activeQuick.value = q.label
  currentPage.value = 1
  loadDashboard()
}

function isActiveQuick(q) {
  return activeQuick.value === q.label
}

function goPage(p) {
  currentPage.value = p
  loadDashboard()
}

function exportTable(format) {
  const params = {
    date_start: dateStart.value,
    date_end: dateEnd.value,
    format
  }
  if (canSelectDelegacion.value && selectedDelegacion.value !== 'Consolidado') {
    params.delegacion = selectedDelegacion.value
  }
  if (filterCategory.value) params.category_id = filterCategory.value
  reportService.downloadPeriodReport(params)
}

// --- Montaje ---
onMounted(() => {
  loadCategories()
  loadDashboard()
})
</script>

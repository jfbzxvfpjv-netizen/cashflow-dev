<!-- M10b — Listado de periodos de nómina -->
<template>
  <div class="p-4 max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-xl font-bold">Nóminas</h1>
      <button v-if="isAdmin" @click="modal='new'"
              class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm">
        + Nuevo periodo
      </button>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded shadow p-3 mb-4 flex gap-2 items-end flex-wrap">
      <div>
        <label class="block text-xs text-gray-500">Año</label>
        <select v-model.number="filters.year" @change="load" class="border rounded px-2 py-1 text-sm">
          <option :value="null">Todos</option>
          <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
        </select>
      </div>
      <div v-if="isAdmin || isContable">
        <label class="block text-xs text-gray-500">Delegación</label>
        <select v-model="filters.delegacion" @change="load" class="border rounded px-2 py-1 text-sm">
          <option value="">Todas</option>
          <option value="Bata">Bata</option>
          <option value="Malabo">Malabo</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-500">Estado</label>
        <select v-model="filters.status" @change="load" class="border rounded px-2 py-1 text-sm">
          <option value="">Todos</option>
          <option value="draft">Borrador</option>
          <option value="paid">Pagado</option>
        </select>
      </div>
    </div>

    <!-- Listado -->
    <div class="bg-white rounded shadow overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left">Periodo</th>
            <th class="px-3 py-2 text-left">Delegación</th>
            <th class="px-3 py-2 text-left">Estado</th>
            <th class="px-3 py-2 text-right">Empleados</th>
            <th class="px-3 py-2 text-right">Total efectivo (XAF)</th>
            <th class="px-3 py-2 text-right">Pagados</th>
            <th class="px-3 py-2 text-right">Pendientes</th>
            <th class="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in periods" :key="p.id" class="border-t hover:bg-gray-50">
            <td class="px-3 py-2 font-medium">{{ formatPeriod(p) }}</td>
            <td class="px-3 py-2">{{ p.delegacion }}</td>
            <td class="px-3 py-2">
              <span :class="p.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                    class="px-2 py-0.5 rounded text-xs font-medium">
                {{ p.status === 'paid' ? 'Pagado' : 'Borrador' }}
              </span>
            </td>
            <td class="px-3 py-2 text-right">{{ p.total_employees }}</td>
            <td class="px-3 py-2 text-right font-mono">{{ Number(p.total_cash).toLocaleString() }}</td>
            <td class="px-3 py-2 text-right text-green-700">{{ p.paid_count }}</td>
            <td class="px-3 py-2 text-right text-orange-600">{{ p.pending_count }}</td>
            <td class="px-3 py-2">
              <router-link :to="`/payrolls/${p.id}`" class="text-blue-600 hover:underline text-xs">
                Ver detalle →
              </router-link>
            </td>
          </tr>
          <tr v-if="periods.length === 0">
            <td colspan="8" class="px-3 py-6 text-center text-gray-400">Sin periodos</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Nuevo periodo -->
    <div v-if="modal==='new'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="modal=null">
      <div class="bg-white rounded p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-3">Generar periodo de nómina</h2>
        <div v-if="merr" class="text-sm text-red-600 mb-2 p-2 bg-red-50 rounded">{{ merr }}</div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Año *</label>
            <select v-model.number="form.year" class="w-full border rounded px-2 py-1.5 text-sm">
              <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Mes *</label>
            <select v-model.number="form.month" class="w-full border rounded px-2 py-1.5 text-sm">
              <option v-for="(m, i) in monthNames" :key="i" :value="i+1">{{ m }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Delegación *</label>
            <select v-model="form.delegacion" class="w-full border rounded px-2 py-1.5 text-sm">
              <option value="Bata">Bata</option>
              <option value="Malabo">Malabo</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 mb-1">Notas</label>
            <textarea v-model="form.notes" rows="2" class="w-full border rounded px-2 py-1.5 text-sm"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button @click="modal=null" class="px-4 py-1.5 text-sm rounded border">Cancelar</button>
          <button @click="doGenerate" :disabled="busy"
                  class="px-4 py-1.5 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
            {{ busy ? 'Generando…' : 'Generar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import payrollService from '@/services/payrollService'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')
const isContable = computed(() => auth.user?.role === 'contable')

const periods = ref([])
const filters = reactive({ year: null, delegacion: '', status: '' })
const modal = ref(null)
const busy = ref(false)
const merr = ref('')

const currentYear = new Date().getFullYear()
const years = [currentYear - 1, currentYear, currentYear + 1]
const monthNames = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

const form = reactive({
  year: currentYear,
  month: new Date().getMonth() + 1,
  delegacion: auth.user?.delegacion || 'Bata',
  notes: '',
})

function formatPeriod(p) {
  return `${monthNames[p.month - 1]} ${p.year}`
}

async function load() {
  const params = {}
  if (filters.year) params.year = filters.year
  if (filters.delegacion) params.delegacion = filters.delegacion
  if (filters.status) params.status = filters.status
  const r = await payrollService.listPeriods(params)
  periods.value = r.data || []
}

async function doGenerate() {
  merr.value = ''
  busy.value = true
  try {
    const r = await payrollService.generatePeriod({
      year: form.year, month: form.month,
      delegacion: form.delegacion, notes: form.notes || null,
    })
    modal.value = null
    router.push(`/payrolls/${r.data.id}`)
  } catch (e) {
    merr.value = e.response?.data?.detail || 'Error generando periodo'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

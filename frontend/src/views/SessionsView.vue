<template>
  <div class="max-w-6xl mx-auto px-4 py-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Sesiones de caja</h1>
      <div v-if="canManage">
        <button v-if="!active" @click="modal='open'" class="bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700">＋ Abrir sesión</button>
        <button v-else @click="modal='close'" class="bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700">✕ Cerrar sesión</button>
      </div>
    </div>

    <!-- Sesión activa -->
    <div v-if="active" class="bg-green-50 border border-green-200 rounded-lg p-5 mb-6">
      <div class="flex justify-between items-start">
        <div>
          <span class="inline-block bg-green-500 text-white text-xs px-2 py-1 rounded-full mb-2">ABIERTA</span>
          <h3 class="font-semibold">{{ active.delegacion }}</h3>
          <p class="text-sm text-gray-600">Abierta: {{ fmtDt(active.opened_at) }}</p>
        </div>
        <div class="text-right">
          <p class="text-sm text-gray-500">Saldo apertura</p>
          <p class="text-xl font-bold">{{ fmt(active.opening_balance) }} XAF</p>
          <p class="text-sm text-gray-500 mt-1">{{ active.transaction_count || 0 }} movimientos</p>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="bg-white rounded-lg shadow p-4 mb-6 grid grid-cols-2 md:grid-cols-5 gap-3">
      <select v-model="f.delegacion" @change="load" class="border rounded px-3 py-2 text-sm"><option value="">Todas</option><option>Bata</option><option>Malabo</option></select>
      <select v-model="f.status" @change="load" class="border rounded px-3 py-2 text-sm"><option value="">Todos</option><option value="open">Abiertas</option><option value="closed">Cerradas</option></select>
      <input v-model="f.ds" @change="load" type="date" class="border rounded px-3 py-2 text-sm" />
      <input v-model="f.de" @change="load" type="date" class="border rounded px-3 py-2 text-sm" />
      <button @click="f={delegacion:'',status:'',ds:'',de:'',page:1};load()" class="text-sm text-gray-500 hover:text-gray-700">Limpiar</button>
    </div>

    <!-- Tabla -->
    <div class="bg-white rounded-lg shadow overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-gray-600"><tr>
          <th class="px-4 py-3 text-left">ID</th><th class="px-4 py-3 text-left">Gestor</th>
          <th class="px-4 py-3 text-left">Deleg.</th><th class="px-4 py-3 text-left">Apertura</th>
          <th class="px-4 py-3 text-left">Cierre</th><th class="px-4 py-3 text-right">Saldo apert.</th>
          <th class="px-4 py-3 text-right">Saldo cierre</th><th class="px-4 py-3 text-center">Movim.</th>
          <th class="px-4 py-3 text-center">Estado</th>
        </tr></thead>
        <tbody class="divide-y">
          <tr v-for="s in sessions" :key="s.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-mono text-gray-500">{{ s.id }}</td>
            <td class="px-4 py-3">{{ s.user_full_name }}</td>
            <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-xs font-medium" :class="s.delegacion==='Bata'?'bg-blue-100 text-blue-700':'bg-green-100 text-green-700'">{{ s.delegacion }}</span></td>
            <td class="px-4 py-3 text-gray-600">{{ fmtDt(s.opened_at) }}</td>
            <td class="px-4 py-3 text-gray-600">{{ s.closed_at ? fmtDt(s.closed_at) : '—' }}</td>
            <td class="px-4 py-3 text-right font-mono">{{ fmt(s.opening_balance) }}</td>
            <td class="px-4 py-3 text-right font-mono">{{ s.closing_balance != null ? fmt(s.closing_balance) : '—' }}</td>
            <td class="px-4 py-3 text-center">{{ s.transaction_count }}</td>
            <td class="px-4 py-3 text-center"><span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="s.status==='open'?'bg-green-100 text-green-700':'bg-gray-100 text-gray-600'">{{ s.status==='open'?'Abierta':'Cerrada' }}</span></td>
          </tr>
          <tr v-if="!sessions.length"><td colspan="9" class="px-4 py-8 text-center text-gray-400">Sin sesiones</td></tr>
        </tbody>
      </table>
      <div v-if="pages>1" class="flex justify-center gap-1 py-3 border-t">
        <button v-for="p in pages" :key="p" @click="f.page=p;load()" class="px-3 py-1 rounded" :class="p===f.page?'bg-blue-600 text-white':'bg-gray-100'">{{ p }}</button>
      </div>
    </div>

    <!-- Modal abrir -->
    <div v-if="modal==='open'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Abrir sesión</h2>
        <select v-if="auth.user?.role==='admin'" v-model="mf.delegacion" class="w-full border rounded px-3 py-2 mb-3"><option value="">— Delegación —</option><option>Bata</option><option>Malabo</option></select>
        <textarea v-model="mf.notes" rows="2" class="w-full border rounded px-3 py-2 mb-3" placeholder="Notas (opcional)"></textarea>
        <p v-if="merr" class="text-sm text-red-600 mb-3">{{ merr }}</p>
        <div class="flex justify-end gap-3">
          <button @click="modal=null" class="text-gray-600">Cancelar</button>
          <button @click="doOpen" :disabled="busy" class="bg-green-600 text-white px-5 py-2 rounded-lg disabled:opacity-50">{{ busy?'Abriendo...':'Abrir' }}</button>
        </div>
      </div>
    </div>

    <!-- Modal cerrar -->
    <div v-if="modal==='close'" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-lg font-semibold mb-4">Cerrar sesión</h2>
        <p class="text-sm text-gray-600 mb-4">Se calculará el saldo de cierre y los adjuntos quedarán bloqueados.</p>
        <textarea v-model="mf.notes" rows="2" class="w-full border rounded px-3 py-2 mb-3" placeholder="Notas de cierre (opcional)"></textarea>
        <p v-if="merr" class="text-sm text-red-600 mb-3">{{ merr }}</p>
        <div class="flex justify-end gap-3">
          <button @click="modal=null" class="text-gray-600">Cancelar</button>
          <button @click="doClose" :disabled="busy" class="bg-red-600 text-white px-5 py-2 rounded-lg disabled:opacity-50">{{ busy?'Cerrando...':'Cerrar' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import svc from '@/services/sessionService'
const auth = useAuthStore()
const canManage = computed(() => ['gestor','admin'].includes(auth.user?.role))
const active = ref(null), sessions = ref([]), pages = ref(1)
const f = ref({ delegacion:'', status:'', ds:'', de:'', page:1 })
const modal = ref(null), mf = ref({ delegacion:'', notes:'' }), merr = ref(''), busy = ref(false)

onMounted(async () => { await loadActive(); await load() })
async function loadActive() { try { active.value = (await svc.getActive()).data } catch { active.value = null } }
async function load() {
  const p = {}
  if (f.value.delegacion) p.delegacion = f.value.delegacion
  if (f.value.status) p.status = f.value.status
  if (f.value.ds) p.date_start = f.value.ds+'T00:00:00'
  if (f.value.de) p.date_end = f.value.de+'T23:59:59'
  p.page = f.value.page
  try { const { data } = await svc.list(p); sessions.value = data.items; pages.value = data.pages } catch { sessions.value = [] }
}
async function doOpen() {
  if (!mf.value.delegacion && auth.user?.delegacion) mf.value.delegacion = auth.user.delegacion;
  merr.value = ''; busy.value = true
  try { await svc.open(mf.value); modal.value = null; mf.value = { delegacion:'', notes:'' }; await loadActive(); await load() }
  catch (e) { merr.value = e.response?.data?.detail || 'Error' }
  finally { busy.value = false }
}
async function doClose() {
  if (!active.value) return; merr.value = ''; busy.value = true
  try { await svc.close(active.value.id, { notes: mf.value.notes }); modal.value = null; active.value = null; await load() }
  catch (e) { merr.value = e.response?.data?.detail || 'Error' }
  finally { busy.value = false }
}
function fmt(n) { return n != null ? new Intl.NumberFormat('es-GQ').format(n) : '—' }
function fmtDt(d) { return d ? new Date(d).toLocaleString('es-GQ',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}) : '—' }
</script>

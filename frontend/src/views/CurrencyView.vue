<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Operaciones en Divisa</h1>
      <div class="flex gap-2">
        <button @click="openBuy" class="bg-blue-600 text-white px-4 py-2 rounded">Comprar euros</button>
        <button @click="openDeliver" class="bg-green-600 text-white px-4 py-2 rounded">Entregar euros</button>
      </div>
    </div>

    <!-- Stock EUR por delegación -->
    <div class="grid grid-cols-2 gap-4 mb-6">
      <div v-for="s in stocks" :key="s.delegacion" class="bg-white rounded shadow p-4">
        <div class="text-sm text-gray-500">Stock EUR — {{ s.delegacion }}</div>
        <div class="text-3xl font-bold mt-1">{{ fmt(s.current_eur_stock) }} €</div>
        <div class="text-xs text-gray-400 mt-2">Act. {{ s.last_updated ? new Date(s.last_updated).toLocaleString('es-ES') : '—' }}</div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="mb-4 flex gap-4">
      <select v-model="filterDeleg" @change="load" class="min-w-[180px] border rounded px-3 py-2">
        <option value="">Ambas delegaciones</option>
        <option value="Bata">Bata</option>
        <option value="Malabo">Malabo</option>
      </select>
    </div>

    <!-- Histórico -->
    <table class="w-full bg-white rounded shadow">
      <thead class="bg-gray-100 text-left text-sm">
        <tr>
          <th class="px-4 py-2">Fecha</th>
          <th class="px-4 py-2">Delegación</th>
          <th class="px-4 py-2">Tipo</th>
          <th class="px-4 py-2 text-right">EUR</th>
          <th class="px-4 py-2 text-right">XAF</th>
          <th class="px-4 py-2 text-right">Tasa</th>
          <th class="px-4 py-2">Oficina / Destinatario</th>
          <th class="px-4 py-2 text-right">Stock EUR tras op.</th>
          <th class="px-4 py-2">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!items.length">
          <td colspan="9" class="text-center py-6 text-gray-500">Sin operaciones</td>
        </tr>
        <tr v-for="it in items" :key="it.id" class="border-t" :class="{ 'line-through text-gray-400': it.cancelled }">
          <td class="px-4 py-2 text-sm">{{ new Date(it.created_at).toLocaleString('es-ES') }}</td>
          <td class="px-4 py-2">{{ it.delegacion }}</td>
          <td class="px-4 py-2">
            <span :class="it.op_type === 'buy' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'"
                  class="px-2 py-1 rounded text-xs">
              {{ it.op_type === 'buy' ? 'Compra' : 'Entrega' }}
            </span>
          </td>
          <td class="px-4 py-2 text-right">{{ fmt(it.eur_amount) }} €</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.xaf_amount) }}</td>
          <td class="px-4 py-2 text-right">{{ Number(it.exchange_rate).toFixed(2) }}</td>
          <td class="px-4 py-2 truncate max-w-xs">{{ it.exchange_office }}</td>
          <td class="px-4 py-2 text-right">{{ fmt(it.eur_stock_after) }} €</td>
          <td class="px-4 py-2 text-sm">
            <template v-if="it.cancelled">
              <span class="text-gray-400 italic">Anulada</span>
            </template>
            <template v-else-if="it.op_type === 'deliver'">
              <button @click="openEdit(it)" class="text-blue-600 hover:underline mr-2" :disabled="!canEdit(it)" :class="{'text-gray-300 cursor-not-allowed': !canEdit(it)}">Editar</button>
              <button @click="openCancel(it)" class="text-red-600 hover:underline">Anular</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- ======= Modal COMPRAR ======= -->
    <div v-if="showBuy" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-4">Comprar euros</h2>

        <label class="block mb-2 text-sm">Delegación (caja de origen)</label>
        <select v-model="buyForm.delegacion" class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona delegación —</option>
          <option value="Bata">Bata</option>
          <option value="Malabo">Malabo</option>
        </select>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Importe XAF pagado</label>
            <input v-model.number="buyForm.xaf_amount" type="number" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-2 text-sm">Euros recibidos</label>
            <input v-model.number="buyForm.eur_amount" type="number" class="w-full border rounded px-3 py-2" />
          </div>
        </div>
        <div class="text-xs text-gray-500 mb-3" v-if="buyForm.xaf_amount > 0 && buyForm.eur_amount > 0">
          Tasa implícita: {{ (buyForm.xaf_amount / buyForm.eur_amount).toFixed(2) }} XAF/€
        </div>

        <label class="block mb-2 text-sm">Oficina de cambio</label>
        <input v-model="buyForm.exchange_office" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="p.ej. Cambio Malabo Centro" />

        <div class="border-t pt-3 mt-3 mb-3">
          <p class="text-xs text-gray-500 mb-3">Imputación contable del egreso en XAF</p>
          <div class="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label class="block mb-2 text-sm">Categoría</label>
              <select v-model="buyForm.category_id" @change="loadSubcats" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Subcategoría</label>
              <select v-model="buyForm.subcategory_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!buyForm.category_id">
                <option :value="null">—</option>
                <option v-for="s in subcats" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block mb-2 text-sm">Proyecto</label>
              <select v-model="buyForm.project_id" @change="loadWorks" class="w-full border rounded px-3 py-2 truncate">
                <option :value="null">—</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div>
              <label class="block mb-2 text-sm">Obra</label>
              <select v-model="buyForm.work_id" class="w-full border rounded px-3 py-2 truncate" :disabled="!buyForm.project_id">
                <option :value="null">—</option>
                <option v-for="w in works" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="flex justify-end gap-2 mt-4">
          <button @click="showBuy = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitBuy" class="px-4 py-2 bg-blue-600 text-white rounded">Comprar</button>
        </div>
      </div>
    </div>

    <!-- ======= Modal ENTREGAR ======= -->
    <div v-if="showDeliver" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-bold mb-2">Entregar euros</h2>
        <p class="text-xs text-gray-500 mb-4">La entrega no afecta la caja XAF — solo descuenta del stock EUR</p>

        <label class="block mb-2 text-sm">Delegación (caja de origen)</label>
        <select v-model="delForm.delegacion" class="w-full border rounded px-3 py-2 mb-3">
          <option :value="null">— Selecciona delegación —</option>
          <option value="Bata">Bata</option>
          <option value="Malabo">Malabo</option>
        </select>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Euros entregados</label>
            <input v-model.number="delForm.eur_amount" type="number" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-2 text-sm">Equivalente XAF (informativo)</label>
            <input v-model.number="delForm.xaf_equivalent" type="number" class="w-full border rounded px-3 py-2" />
          </div>
        </div>
        <div class="text-xs text-gray-500 mb-3" v-if="delForm.xaf_equivalent > 0 && delForm.eur_amount > 0">
          Tasa implícita: {{ (delForm.xaf_equivalent / delForm.eur_amount).toFixed(2) }} XAF/€
        </div>

        <label class="block mb-2 text-sm">Destinatario</label>
        <input v-model="delForm.recipient" class="w-full border rounded px-3 py-2 mb-3"
               placeholder="Nombre del destinatario" />

        <div class="flex justify-end gap-2 mt-4">
          <button @click="showDeliver = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitDeliver" class="px-4 py-2 bg-green-600 text-white rounded">Entregar</button>
        </div>
      </div>
    </div>

    <!-- ======= Modal EDITAR entrega ======= -->
    <div v-if="showEdit" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-xl mx-4">
        <h2 class="text-lg font-bold mb-2">Editar entrega</h2>
        <p class="text-xs text-gray-500 mb-4">Solo campos que se modifiquen. Si cambias los euros, el stock se recalcula.</p>

        <div class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="block mb-2 text-sm">Euros entregados</label>
            <input v-model.number="editForm.eur_amount" type="number" class="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label class="block mb-2 text-sm">Equivalente XAF</label>
            <input v-model.number="editForm.xaf_equivalent" type="number" class="w-full border rounded px-3 py-2" />
          </div>
        </div>
        <label class="block mb-2 text-sm">Destinatario</label>
        <input v-model="editForm.recipient" class="w-full border rounded px-3 py-2 mb-3" />

        <label class="block mb-2 text-sm" v-if="editOutOfWindow">Motivo (fuera de ventana nativa)</label>
        <textarea v-if="editOutOfWindow" v-model="editForm.reason" rows="2" class="w-full border rounded px-3 py-2 mb-3"></textarea>

        <div class="flex justify-end gap-2">
          <button @click="showEdit = false" class="px-4 py-2 border rounded">Cancelar</button>
          <button @click="submitEdit" class="px-4 py-2 bg-blue-600 text-white rounded">Guardar</button>
        </div>
      </div>
    </div>

    <!-- ======= Modal ANULAR entrega ======= -->
    <div v-if="showCancel" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow-lg w-full max-w-xl mx-4">
        <h2 class="text-lg font-bold mb-2">Anular entrega</h2>
        <p class="text-xs text-gray-500 mb-4">
          Los {{ fmt(cancelCtx?.eur_amount) }} € volverán al stock de {{ cancelCtx?.delegacion }}.
          Esta acción queda registrada y es irreversible desde la UI.
        </p>

        <label class="block mb-2 text-sm">Motivo</label>
        <textarea v-model="cancelReason" rows="3" class="w-full border rounded px-3 py-2 mb-3"
                  placeholder="Motivo de la anulación"></textarea>

        <div class="flex justify-end gap-2">
          <button @click="showCancel = false" class="px-4 py-2 border rounded">Cerrar</button>
          <button @click="submitCancel" class="px-4 py-2 bg-red-600 text-white rounded">Anular</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { currencyService } from '../services/financialModulesService'

function extractArray(d) {
  if (Array.isArray(d)) return d
  if (d && typeof d === 'object') {
    for (const k of ['items','data','results']) if (Array.isArray(d[k])) return d[k]
  }
  return []
}

const items      = ref([])
const stocks     = ref([])
const categories = ref([]); const subcats  = ref([])
const projects   = ref([]); const works    = ref([])
const filterDeleg = ref('')

const showBuy     = ref(false)
const showDeliver = ref(false)

const buyForm = ref({
  xaf_amount: 0, eur_amount: 0, exchange_office: '', delegacion: null,
  category_id: null, subcategory_id: null, project_id: null, work_id: null,
})
const delForm = ref({ eur_amount: 0, xaf_equivalent: 0, recipient: '', delegacion: null })

const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('es-ES', { maximumFractionDigits: 0 })

const loadStocks = async () => {
  stocks.value = []
  for (const d of ['Bata', 'Malabo']) {
    try {
      const s = await currencyService.stock(d)
      stocks.value.push(s)
    } catch {}
  }
}

const load = async () => {
  const params = filterDeleg.value ? { delegacion: filterDeleg.value } : {}
  items.value = await currencyService.list(params)
}

const loadCatalogs = async () => {
  categories.value = extractArray((await api.get('/categories')).data).filter(c => c.active)
  projects.value   = extractArray((await api.get('/projects')).data).filter(p => p.active)
}
const loadSubcats = async () => {
  if (!buyForm.value.category_id) { subcats.value = []; buyForm.value.subcategory_id = null; return }
  const r = await api.get('/subcategories', { params: { category_id: buyForm.value.category_id } })
  subcats.value = extractArray(r.data).filter(s => s.active)
}
const loadWorks = async () => {
  if (!buyForm.value.project_id) { works.value = []; buyForm.value.work_id = null; return }
  const r = await api.get('/works', { params: { project_id: buyForm.value.project_id } })
  works.value = extractArray(r.data).filter(w => w.active)
}

const openBuy = () => {
  buyForm.value = {
    xaf_amount: 0, eur_amount: 0, exchange_office: '', delegacion: null,
    category_id: null, subcategory_id: null, project_id: null, work_id: null,
  }
  subcats.value = []; works.value = []
  showBuy.value = true
}
const openDeliver = () => {
  delForm.value = { eur_amount: 0, xaf_equivalent: 0, recipient: '', delegacion: null }
  showDeliver.value = true
}

const submitBuy = async () => {
  if (!buyForm.value.delegacion) { alert('Selecciona la delegación'); return }
  try {
    await currencyService.buy(buyForm.value)
    showBuy.value = false
    await Promise.all([load(), loadStocks()])
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al comprar euros')
  }
}
const submitDeliver = async () => {
  if (!delForm.value.delegacion) { alert('Selecciona la delegación'); return }
  try {
    await currencyService.deliver(delForm.value)
    showDeliver.value = false
    await Promise.all([load(), loadStocks()])
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al entregar euros')
  }
}


// --- Edición y anulación de entregas ---
const showEdit = ref(false)
const showCancel = ref(false)
const editCtx = ref(null)
const cancelCtx = ref(null)
const cancelReason = ref('')
const editForm = ref({ eur_amount: null, xaf_equivalent: null, recipient: '', reason: '' })
const editOutOfWindow = ref(false)

const canEdit = (it) => {
  if (it.cancelled) return false
  // Permitir click y dejar al backend decidir (admin puede fuera de ventana)
  return true
}

const openEdit = (it) => {
  editCtx.value = it
  editForm.value = {
    eur_amount: Number(it.eur_amount),
    xaf_equivalent: Number(it.xaf_amount),
    recipient: it.exchange_office,
    reason: '',
  }
  // Ventana nativa: 15 min tras created_at
  const now = new Date()
  const until = it.editable_until ? new Date(it.editable_until) : null
  editOutOfWindow.value = !until || now > until
  showEdit.value = true
}

const openCancel = (it) => {
  cancelCtx.value = it
  cancelReason.value = ''
  showCancel.value = true
}

const submitEdit = async () => {
  try {
    await currencyService.edit(editCtx.value.id, editForm.value)
    showEdit.value = false
    await Promise.all([load(), loadStocks()])
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al editar')
  }
}

const submitCancel = async () => {
  if (!cancelReason.value || cancelReason.value.trim().length < 3) {
    alert('El motivo es obligatorio (mínimo 3 caracteres)')
    return
  }
  try {
    await currencyService.cancel(cancelCtx.value.id, cancelReason.value)
    showCancel.value = false
    await Promise.all([load(), loadStocks()])
  } catch (e) {
    alert(e.response?.data?.detail || 'Error al anular')
  }
}

onMounted(async () => {
  await loadCatalogs()
  await Promise.all([loadStocks(), load()])
})
</script>
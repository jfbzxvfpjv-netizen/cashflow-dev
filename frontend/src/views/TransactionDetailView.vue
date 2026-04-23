<!--
  TransactionDetailView.vue
  Detalle de transacción + formulario de edición para importadas (admin, ventana 30 días).
  Parche fix edición importadas — solo en entorno dev.
-->
<template>
  <div class="p-4 max-w-3xl mx-auto">
    <div class="flex items-center gap-3 mb-4 flex-wrap">
      <router-link to="/transactions" class="text-blue-600 hover:underline text-sm">← Volver</router-link>
      <h1 class="text-xl font-bold">Transacción {{ txn?.reference_number }}</h1>
      <EditTimer v-if="txn && !txn.imported" :seconds-remaining="txn.seconds_remaining" @expired="txn.is_editable = false" />
      <span v-if="txn && txn.imported && txn.is_editable" class="text-xs text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
        Editable (importada — ventana 30 días)
      </span>
    </div>

    <div v-if="!txn" class="text-gray-400 py-8 text-center">Cargando...</div>

    <div v-else class="bg-white rounded shadow p-4 space-y-4">
      <!-- ========== MODO EDICIÓN ========== -->
      <div v-if="editMode" class="border-2 border-blue-400 rounded p-3 bg-blue-50 space-y-3">
        <h3 class="text-sm font-semibold text-blue-800">Edición de transacción</h3>
        <p class="text-xs text-gray-600">
          La edición queda registrada en el audit_log con valores anterior y nuevo. El hash SHA-256 se recalcula automáticamente.
        </p>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-gray-700">Tipo *</label>
            <select v-model="form.type" class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
              <option value="income">Ingreso</option>
              <option value="expense">Egreso</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700">Importe (XAF) *</label>
            <input v-model.number="form.amount" type="number" step="0.01" min="0.01"
                   class="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700">Categoría *</label>
            <select v-model="form.category_id" @change="onCategoryChange"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
              <option :value="null">— Seleccionar —</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700">Subcategoría *</label>
            <select v-model="form.subcategory_id" :disabled="!form.category_id"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm disabled:bg-gray-100">
              <option :value="null">— Seleccionar —</option>
              <option v-for="s in subcategories" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-medium text-gray-700">Proyecto *</label>
            <select v-model="form.project_id" @change="onProjectChange"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
              <option :value="null">— Seleccionar —</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700">Obra *</label>
            <select v-model="form.work_id" :disabled="!form.project_id"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm disabled:bg-gray-100">
              <option :value="null">— Seleccionar —</option>
              <option v-for="w in works" :key="w.id" :value="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-700">Concepto *</label>
          <textarea v-model="form.concept" rows="2"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm"></textarea>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-700">Contraparte *</label>
          <select v-model="form.counterparty_kind" class="w-full border border-gray-300 rounded px-2 py-1 text-sm mb-1">
            <option value="free">Texto libre</option>
            <option value="supplier">Proveedor</option>
            <option value="employee">Empleado</option>
            <option value="partner">Socio</option>
          </select>
          <input v-if="form.counterparty_kind === 'free'" v-model="form.counterparty_free"
                 placeholder="Nombre y apellido (mínimo 2 palabras)"
                 class="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
          <select v-else-if="form.counterparty_kind === 'supplier'" v-model="form.supplier_id"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
            <option :value="null">— Seleccionar —</option>
            <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
          <select v-else-if="form.counterparty_kind === 'employee'" v-model="form.employee_id"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
            <option :value="null">— Seleccionar —</option>
            <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
          </select>
          <select v-else-if="form.counterparty_kind === 'partner'" v-model="form.partner_id"
                  class="w-full border border-gray-300 rounded px-2 py-1 text-sm">
            <option :value="null">— Seleccionar —</option>
            <option v-for="p in partners" :key="p.id" :value="p.id">{{ p.full_name }}</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-medium text-gray-700">Motivo de la edición *</label>
          <textarea v-model="form.edit_reason" rows="2"
                    placeholder="Obligatorio: se registrará en el audit_log"
                    class="w-full border border-gray-300 rounded px-2 py-1 text-sm"></textarea>
        </div>

        <div v-if="editError" class="text-red-700 text-xs bg-red-50 border border-red-200 rounded p-2">
          {{ editError }}
        </div>

        <div class="flex gap-2 pt-2">
          <button @click="saveEdit" :disabled="!isFormValid || saving"
                  class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50">
            {{ saving ? 'Guardando...' : 'Guardar cambios' }}
          </button>
          <button @click="closeEdit" :disabled="saving"
                  class="px-3 py-1.5 bg-gray-200 rounded text-sm disabled:opacity-50">Cancelar</button>
        </div>
      </div>

      <!-- ========== MODO VISUALIZACIÓN ========== -->
      <template v-else>
        <div class="flex gap-2 flex-wrap">
          <span v-if="txn.cancelled" class="bg-gray-200 text-gray-700 px-2 py-1 rounded text-xs">ANULADA</span>
          <span v-if="txn.approval_status === 'pending_approval'" class="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs">PENDIENTE APROBACIÓN</span>
          <span v-if="txn.approval_status === 'authorized'" class="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs">AUTORIZADA — Pendiente de ejecución</span>
          <span v-if="txn.approval_status === 'rejected'" class="bg-red-100 text-red-700 px-2 py-1 rounded text-xs">RECHAZADA</span>
          <span v-if="txn.imported" class="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">IMPORTADA</span>
          <span :class="txn.type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
                class="px-2 py-1 rounded text-xs uppercase">{{ txn.type === 'income' ? 'Ingreso' : 'Egreso' }}</span>
        </div>

        <div class="grid grid-cols-2 gap-3 text-sm">
          <div><span class="text-gray-500">Importe:</span> <strong class="font-mono">{{ Number(txn.amount).toLocaleString() }} XAF</strong></div>
          <div><span class="text-gray-500">Delegación:</span> {{ txn.delegacion }}</div>
          <div><span class="text-gray-500">Categoría:</span> {{ txn.category_name }}</div>
          <div><span class="text-gray-500">Subcategoría:</span> {{ txn.subcategory_name }}</div>
          <div><span class="text-gray-500">Contraparte:</span> {{ txn.counterparty_name || '—' }}</div>
          <div><span class="text-gray-500">Registrado por:</span> {{ txn.user_fullname }}</div>
          <div><span class="text-gray-500">Fecha:</span> {{ formatDate(txn.created_at) }}</div>
        </div>

        <div class="text-sm">
          <span class="text-gray-500">Concepto:</span>
          <p class="mt-1">{{ txn.concept }}</p>
        </div>

        <div v-if="txn.projects && txn.projects.length" class="text-sm">
          <span class="text-gray-500">Proyectos / Obras:</span>
          <ul class="mt-1 list-disc ml-5">
            <li v-for="p in txn.projects" :key="p.project_id + '-' + p.work_id">
              {{ p.project_name }} → {{ p.work_name }}
            </li>
          </ul>
        </div>

        <div class="border-t pt-3">
          <h3 class="text-sm font-semibold mb-2">Adjuntos</h3>
          <FileUploader
            :transaction-id="txn.id"
            :can-upload="txn.is_editable && !txn.cancelled"
            @uploaded="load"
            @deleted="load"
          />
        </div>

        <div class="text-xs text-gray-400 font-mono break-all">
          SHA-256: {{ txn.integrity_hash }}
        </div>

        <div class="flex gap-2 pt-2 border-t flex-wrap">
          <button v-if="canEdit"
                  @click="openEdit"
                  class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
            ✎ Editar
          </button>
          <button v-if="isAdmin && txn.approval_status === 'pending_approval'"
                  @click="approve" class="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700">
            ✓ Aprobar
          </button>
          <button v-if="isAdmin && txn.approval_status === 'pending_approval'"
                  @click="showReject = true" class="px-3 py-1.5 bg-red-600 text-white rounded text-sm hover:bg-red-700">
            ✕ Rechazar
          </button>
          <button v-if="txn.approval_status === 'authorized' && canExecute"
                  @click="executeTxn" class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
            💰 Ejecutar pago
          </button>
          <button v-if="isAdmin && !txn.cancelled && txn.approval_status !== 'pending_approval'"
                  @click="showCancel = true" class="px-3 py-1.5 bg-gray-600 text-white rounded text-sm hover:bg-gray-700">
            Anular
          </button>
        </div>

        <div v-if="showReject" class="border rounded p-3 bg-red-50 space-y-2">
          <label class="block text-sm font-medium">Motivo del rechazo *</label>
          <textarea v-model="rejectReason" class="w-full border rounded px-3 py-2 text-sm" rows="2"></textarea>
          <div class="flex gap-2">
            <button @click="reject" :disabled="!rejectReason"
                    class="px-3 py-1.5 bg-red-600 text-white rounded text-sm disabled:opacity-50">Confirmar rechazo</button>
            <button @click="showReject = false" class="px-3 py-1.5 bg-gray-200 rounded text-sm">Cancelar</button>
          </div>
        </div>

        <div v-if="showCancel" class="border rounded p-3 bg-gray-50 space-y-2">
          <label class="block text-sm font-medium">Motivo de la anulación *</label>
          <textarea v-model="cancelReason" class="w-full border rounded px-3 py-2 text-sm" rows="2"></textarea>
          <div class="flex gap-2">
            <button @click="cancelTxn" :disabled="!cancelReason"
                    class="px-3 py-1.5 bg-gray-700 text-white rounded text-sm disabled:opacity-50">Confirmar anulación</button>
            <button @click="showCancel = false" class="px-3 py-1.5 bg-gray-200 rounded text-sm">Cancelar</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import transactionService from '@/services/transactionService'
import EditTimer from '@/components/EditTimer.vue'
import FileUploader from '@/components/FileUploader.vue'

const route = useRoute()
const auth = useAuthStore()
const isAdmin = computed(() => auth.hasRole('admin'))
const canExecute = computed(() => auth.hasRole('gestor', 'admin'))
const canEdit = computed(() => {
  if (!txn.value) return false
  if (!txn.value.is_editable || txn.value.cancelled) return false
  // Política opción 3: admin solo edita importadas, gestor solo nativas propias
  if (isAdmin.value) {
    return !!txn.value.imported
  }
  if (auth.hasRole('gestor')) {
    if (txn.value.imported) return false
    return auth.user?.id && txn.value.user_id === auth.user.id
  }
  return false
})

const txn = ref(null)
const showReject = ref(false)
const showCancel = ref(false)
const rejectReason = ref('')
const cancelReason = ref('')

// Edición importadas
const editMode = ref(false)
const saving = ref(false)
const editError = ref('')
const categories = ref([])
const subcategories = ref([])
const projects = ref([])
const works = ref([])
const suppliers = ref([])
const employees = ref([])
const partners = ref([])

const form = ref({
  type: 'expense',
  amount: 0,
  category_id: null,
  subcategory_id: null,
  project_id: null,
  work_id: null,
  concept: '',
  counterparty_kind: 'free',
  counterparty_free: '',
  supplier_id: null,
  employee_id: null,
  edit_reason: '',
})

const isFormValid = computed(() => {
  const f = form.value
  if (!f.type || !f.amount || f.amount <= 0) return false
  if (!f.category_id || !f.subcategory_id) return false
  if (!f.project_id || !f.work_id) return false
  if (!f.concept || f.concept.trim().length < 3) return false
  if (!f.edit_reason || f.edit_reason.trim().length < 3) return false
  if (f.counterparty_kind === 'free') {
    if (!f.counterparty_free || f.counterparty_free.trim().split(/\s+/).length < 2) return false
  } else if (f.counterparty_kind === 'supplier' && !f.supplier_id) {
    return false
  } else if (f.counterparty_kind === 'employee' && !f.employee_id) {
    return false
  }
  return true
})

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('es-ES')
}

async function load() {
  const { data } = await transactionService.get(route.params.id)
  txn.value = data
}

function unwrap(resp) {
  const d = resp.data
  if (Array.isArray(d)) return d
  if (d && Array.isArray(d.items)) return d.items
  if (d && Array.isArray(d.results)) return d.results
  if (d && Array.isArray(d.data)) return d.data
  console.warn('Respuesta sin array reconocible:', d)
  return []
}

async function loadCatalogs() {
  try {
    const [cats, sups, emps, projs, parts] = await Promise.all([
      transactionService.getCategories(),
      transactionService.getSuppliers(),
      transactionService.getEmployees(),
      transactionService.getProjects(),
      transactionService.getPartners(),
    ])
    categories.value = unwrap(cats)
    suppliers.value = unwrap(sups)
    employees.value = unwrap(emps)
    projects.value = unwrap(projs)
    partners.value = unwrap(parts)
    console.log('Catálogos cargados:', {
      categorias: categories.value.length,
      subcat_pendiente: 'al seleccionar categoria',
      proveedores: suppliers.value.length,
      empleados: employees.value.length,
      proyectos: projects.value.length,
    })
  } catch (err) {
    console.error('Error cargando catálogos:', err)
    editError.value = 'No se pudieron cargar los catálogos: ' + (err.response?.data?.detail || err.message)
  }
}

async function onCategoryChange() {
  form.value.subcategory_id = null
  if (form.value.category_id) {
    try {
      const res = await transactionService.getSubcategories({ category_id: form.value.category_id })
      subcategories.value = unwrap(res)
      console.log('Subcategorías cargadas:', subcategories.value.length)
    } catch (err) {
      console.error('Error cargando subcategorías:', err)
      subcategories.value = []
    }
  } else {
    subcategories.value = []
  }
}

async function onProjectChange() {
  form.value.work_id = null
  if (form.value.project_id) {
    try {
      const res = await transactionService.getWorks({ project_id: form.value.project_id })
      works.value = unwrap(res)
      console.log('Obras cargadas:', works.value.length)
    } catch (err) {
      console.error('Error cargando obras:', err)
      works.value = []
    }
  } else {
    works.value = []
  }
}

async function openEdit() {
  editError.value = ''
  await loadCatalogs()

  const t = txn.value
  form.value.type = t.type
  form.value.amount = Number(t.amount)
  form.value.category_id = t.category_id ?? null
  form.value.subcategory_id = t.subcategory_id ?? null
  form.value.concept = t.concept || ''
  form.value.edit_reason = ''

  if (t.category_id) {
    try {
      const res = await transactionService.getSubcategories({ category_id: t.category_id })
      subcategories.value = unwrap(res)
    } catch (err) { console.error('Error precargando subcategorías:', err) }
  }

  if (t.projects && t.projects.length) {
    form.value.project_id = t.projects[0].project_id
    form.value.work_id = t.projects[0].work_id
    try {
      const res = await transactionService.getWorks({ project_id: t.projects[0].project_id })
      works.value = unwrap(res)
    } catch (err) { console.error('Error precargando obras:', err) }
  }

  if (t.supplier_id) {
    form.value.counterparty_kind = 'supplier'
    form.value.supplier_id = t.supplier_id
  } else if (t.employee_id) {
    form.value.counterparty_kind = 'employee'
    form.value.employee_id = t.employee_id
  } else {
    form.value.counterparty_kind = 'free'
    form.value.counterparty_free = t.counterparty_free || ''
  }

  editMode.value = true
}

function closeEdit() {
  editMode.value = false
  editError.value = ''
}

async function saveEdit() {
  editError.value = ''
  saving.value = true
  try {
    const f = form.value
    const payload = {
      type: f.type,
      amount: f.amount,
      category_id: f.category_id,
      subcategory_id: f.subcategory_id,
      concept: f.concept.trim(),
      projects: [{ project_id: f.project_id, work_id: f.work_id }],
      edit_reason: f.edit_reason.trim(),
      supplier_id: f.counterparty_kind === 'supplier' ? f.supplier_id : null,
      employee_id: f.counterparty_kind === 'employee' ? f.employee_id : null,
      partner_id: f.counterparty_kind === 'partner' ? f.partner_id : null,
      counterparty_free: f.counterparty_kind === 'free' ? f.counterparty_free.trim() : null,
    }
    await transactionService.update(txn.value.id, payload)
    await load()
    editMode.value = false
  } catch (err) {
    editError.value = err.response?.data?.detail || err.message || 'Error al guardar los cambios'
  } finally {
    saving.value = false
  }
}

async function executeTxn() {
  await transactionService.execute(txn.value.id)
  await load()
}

async function approve() {
  await transactionService.approve(txn.value.id)
  await load()
}

async function reject() {
  await transactionService.reject(txn.value.id, rejectReason.value)
  showReject.value = false
  rejectReason.value = ''
  await load()
}

async function cancelTxn() {
  await transactionService.cancel(txn.value.id, cancelReason.value)
  showCancel.value = false
  cancelReason.value = ''
  await load()
}

onMounted(() => load())
</script>

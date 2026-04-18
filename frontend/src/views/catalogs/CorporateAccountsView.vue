<!--
  CorporateAccountsView.vue — /corporate-accounts
  Gestión de cuentas bancarias corporativas por delegación.
  Solo accesible para Administrador y Contable.
-->
<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">Cuentas Corporativas</h1>
      <button
        v-if="isAdmin"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openModal(null)"
      >
        + Nueva cuenta
      </button>
    </div>

    <!-- Filtro por delegación -->
    <div class="flex gap-2 mb-4">
      <button
        v-for="d in ['', 'Bata', 'Malabo']"
        :key="d"
        :class="[
          'px-3 py-1.5 text-sm rounded-md border',
          delegacionFilter === d ? 'bg-blue-50 border-blue-300 text-blue-700' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        ]"
        @click="delegacionFilter = d; fetchAccounts()"
      >
        {{ d || 'Todas' }}
      </button>
    </div>

    <!-- Tabla de cuentas -->
    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Banco</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número de cuenta</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Titular</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delegación</th>
            <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
            <th v-if="isAdmin" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="acc in accounts" :key="acc.id" :class="{ 'text-gray-400': !acc.active }">
            <td class="px-4 py-3 text-sm font-medium">{{ acc.bank_name }}</td>
            <td class="px-4 py-3 text-sm font-mono">{{ acc.account_number }}</td>
            <td class="px-4 py-3 text-sm">{{ acc.account_holder }}</td>
            <td class="px-4 py-3 text-sm">
              <span :class="acc.delegacion === 'Bata' ? 'text-blue-600' : 'text-green-600'">
                {{ acc.delegacion }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm text-center">
              <span :class="acc.active ? 'text-green-500' : 'text-red-400'">
                {{ acc.active ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td v-if="isAdmin" class="px-4 py-3 text-sm text-right space-x-2">
              <button class="text-blue-600 hover:text-blue-800" @click="openModal(acc)">Editar</button>
              <button
                :class="acc.active ? 'text-red-500' : 'text-green-500'"
                @click="toggleActive(acc)"
              >
                {{ acc.active ? 'Desactivar' : 'Activar' }}
              </button>
              <button class="text-red-600 hover:text-red-800" @click="confirmDelete(acc)">Eliminar</button>
            </td>
          </tr>
          <tr v-if="!accounts.length">
            <td :colspan="isAdmin ? 6 : 5" class="px-4 py-8 text-center text-gray-400 text-sm">
              No se encontraron cuentas corporativas
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">{{ editing ? 'Editar' : 'Nueva' }} cuenta corporativa</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Banco *</label>
              <input v-model="form.bank_name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Número de cuenta *</label>
              <input v-model="form.account_number" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Titular *</label>
              <input v-model="form.account_holder" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Delegación *</label>
              <select v-model="form.delegacion" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="Bata">Bata</option>
                <option value="Malabo">Malabo</option>
              </select>
            </div>
          </div>
          <p v-if="formError" class="text-sm text-red-600 mt-2">{{ formError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md" @click="save">Guardar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
    <!-- Modal confirmación eliminar -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showDeleteConfirm = false">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Confirmar eliminación</h3>
        <p class="text-sm text-gray-600 mb-4">¿Eliminar permanentemente la cuenta <strong>{{ deletingItem?.bank_name }}</strong>?</p>
        <p v-if="deleteError" class="text-sm text-red-600 mb-3 bg-red-50 p-2 rounded">{{ deleteError }}</p>
        <div class="flex justify-end gap-3">
          <button class="px-4 py-2 text-sm text-gray-600" @click="showDeleteConfirm = false">Cancelar</button>
          <button class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700" @click="executeDelete">Eliminar</button>
        </div>
      </div>
    </div>
  
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { corporateAccountsApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const accounts = ref([])
const showDeleteConfirm = ref(false)
const deletingItem = ref(null)
const deleteError = ref('')
const delegacionFilter = ref('')
const showModal = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = ref({})
const formError = ref('')

async function fetchAccounts() {
  try {
    const params = { active_only: false }
    if (delegacionFilter.value) params.delegacion = delegacionFilter.value
    const { data } = await corporateAccountsApi.list(params)
    accounts.value = data
  } catch (err) {
    console.error('Error cargando cuentas:', err)
  }
}

function openModal(acc) {
  editing.value = !!acc
  editingId.value = acc?.id || null
  form.value = acc
    ? { bank_name: acc.bank_name, account_number: acc.account_number, account_holder: acc.account_holder, delegacion: acc.delegacion }
    : { bank_name: '', account_number: '', account_holder: '', delegacion: 'Bata' }
  formError.value = ''
  showModal.value = true
}

async function save() {
  formError.value = ''
  try {
    if (editing.value) {
      await corporateAccountsApi.update(editingId.value, form.value)
    } else {
      await corporateAccountsApi.create(form.value)
    }
    showModal.value = false
    fetchAccounts()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function toggleActive(acc) {
  try {
    await corporateAccountsApi.update(acc.id, { active: !acc.active })
    fetchAccounts()
  } catch (err) {
    console.error('Error:', err)
  }
}

onMounted(fetchAccounts)


function confirmDelete(acc) {
  deletingItem.value = acc
  deleteError.value = ''
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!deletingItem.value) return
  try {
    await corporateAccountsApi.delete(deletingItem.value.id)
    showDeleteConfirm.value = false
    deletingItem.value = null
    deleteError.value = ''
    fetchAccounts()
  } catch (e) {
    deleteError.value = e.response?.data?.detail || 'Error al eliminar'
  }
}
</script>

<!--
  PartnersView.vue — /partner-accounts (vista catálogo)
  Gestión de los 4 socios. Saldos visibles solo para admin y contable.
-->
<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">Socios</h1>
      <button
        v-if="isAdmin"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openModal(null)"
      >
        + Nuevo socio
      </button>
    </div>

    <!-- Tarjetas de socios -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="p in partners"
        :key="p.id"
        class="bg-white border border-gray-200 rounded-lg p-5"
        :class="{ 'opacity-50': !p.active }"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-sm text-gray-500">{{ p.code }}</p>
            <p class="text-lg font-semibold text-gray-900">{{ p.full_name }}</p>
          </div>
          <span
            :class="p.can_contribute ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'"
            class="px-2 py-0.5 text-xs rounded-full"
          >
            {{ p.can_contribute ? 'Puede aportar' : 'Sin aportaciones' }}
          </span>
        </div>

        <div class="mt-3 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Participación</p>
            <p class="font-semibold text-lg">{{ p.participation_pct }}%</p>
          </div>
          <div v-if="canSeeSalary">
            <p class="text-gray-500">Saldo actual</p>
            <p class="font-semibold text-lg" :class="balanceColor(p.current_balance)">
              {{ formatXAF(p.current_balance) }}
            </p>
          </div>
        </div>

        <div v-if="isAdmin" class="mt-4 pt-3 border-t border-gray-100 flex gap-3">
          <button class="text-sm text-blue-600 hover:text-blue-800" @click="openModal(p)">
            Editar
          </button>
          <button
            class="text-sm"
            :class="p.active ? 'text-red-500 hover:text-red-700' : 'text-green-500'"
            @click="toggleActive(p)"
          >
            {{ p.active ? 'Desactivar' : 'Activar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal crear/editar socio -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">{{ editing ? 'Editar' : 'Nuevo' }} socio</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
              <input v-model="form.code" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre completo *</label>
              <input v-model="form.full_name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Participación (%)</label>
              <input v-model.number="form.participation_pct" type="number" min="0" max="100" step="0.01" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="form.can_contribute" type="checkbox" class="rounded border-gray-300" />
              Puede realizar aportaciones
            </label>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { partnersApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const canSeeSalary = computed(() => ['admin', 'contable'].includes(authStore.user?.role))

const partners = ref([])
const showModal = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = ref({})
const formError = ref('')

function formatXAF(amount) {
  if (amount == null) return '—'
  return new Intl.NumberFormat('es-GQ').format(amount) + ' XAF'
}

function balanceColor(amount) {
  if (amount == null) return ''
  if (amount > 0) return 'text-green-600'
  if (amount < 0) return 'text-red-600'
  return 'text-gray-900'
}

async function fetchPartners() {
  try {
    const { data } = await partnersApi.list({ active_only: false })
    partners.value = data
  } catch (err) {
    console.error('Error cargando socios:', err)
  }
}

function openModal(p) {
  editing.value = !!p
  editingId.value = p?.id || null
  form.value = p
    ? { code: p.code, full_name: p.full_name, participation_pct: p.participation_pct, can_contribute: p.can_contribute }
    : { code: '', full_name: '', participation_pct: 0, can_contribute: false }
  formError.value = ''
  showModal.value = true
}

async function save() {
  formError.value = ''
  try {
    if (editing.value) {
      await partnersApi.update(editingId.value, form.value)
    } else {
      await partnersApi.create(form.value)
    }
    showModal.value = false
    fetchPartners()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function toggleActive(p) {
  try {
    await partnersApi.update(p.id, { active: !p.active })
    fetchPartners()
  } catch (err) {
    console.error('Error:', err)
  }
}

onMounted(fetchPartners)
</script>

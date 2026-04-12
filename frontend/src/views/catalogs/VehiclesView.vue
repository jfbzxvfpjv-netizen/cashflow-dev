<!--
  VehiclesView.vue — /vehicles
  Catálogo de flota con filtro por delegación.
-->
<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">Vehículos de Flota</h1>
      <button
        v-if="isAdmin"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openModal(null)"
      >
        + Nuevo vehículo
      </button>
    </div>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input
        v-model="search"
        type="text"
        placeholder="Buscar por matrícula, marca o modelo..."
        class="flex-1 min-w-[200px] rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        @input="debouncedFetch"
      />
      <select v-model="delegacionFilter" class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" @change="fetchVehicles">
        <option value="">Todas</option>
        <option value="Bata">Bata</option>
        <option value="Malabo">Malabo</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Matrícula</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Marca</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Modelo</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Año</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delegación</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Conductor habitual</th>
            <th v-if="isAdmin" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="v in vehicles" :key="v.id" :class="{ 'text-gray-400': !v.active }">
            <td class="px-4 py-3 text-sm font-mono font-medium">{{ v.plate }}</td>
            <td class="px-4 py-3 text-sm">{{ v.brand || '—' }}</td>
            <td class="px-4 py-3 text-sm">{{ v.model || '—' }}</td>
            <td class="px-4 py-3 text-sm">{{ v.year || '—' }}</td>
            <td class="px-4 py-3 text-sm">
              <span :class="v.delegacion === 'Bata' ? 'text-blue-600' : 'text-green-600'">
                {{ v.delegacion }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm">{{ v.usual_driver_name || '—' }}</td>
            <td v-if="isAdmin" class="px-4 py-3 text-sm text-right space-x-2">
              <button class="text-blue-600 hover:text-blue-800" @click="openModal(v)">Editar</button>
              <button
                :class="v.active ? 'text-red-500 hover:text-red-700' : 'text-green-500 hover:text-green-700'"
                @click="toggleActive(v)"
              >
                {{ v.active ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
          <tr v-if="!vehicles.length">
            <td :colspan="isAdmin ? 7 : 6" class="px-4 py-8 text-center text-gray-400 text-sm">
              No se encontraron vehículos
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal crear/editar vehículo -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">{{ editing ? 'Editar' : 'Nuevo' }} vehículo</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Matrícula *</label>
              <input v-model="form.plate" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                <input v-model="form.brand" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Modelo</label>
                <input v-model="form.model" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Año</label>
                <input v-model.number="form.year" type="number" min="1990" max="2030" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Delegación *</label>
                <select v-model="form.delegacion" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="Bata">Bata</option>
                  <option value="Malabo">Malabo</option>
                </select>
              </div>
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { vehiclesApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const vehicles = ref([])
const search = ref('')
const delegacionFilter = ref('')
const showModal = ref(false)
const editing = ref(false)
const editingId = ref(null)
const form = ref({})
const formError = ref('')

let searchTimeout = null

function debouncedFetch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(fetchVehicles, 300)
}

async function fetchVehicles() {
  try {
    const params = { active_only: false, page_size: 100 }
    if (search.value) params.search = search.value
    if (delegacionFilter.value) params.delegacion = delegacionFilter.value
    const { data } = await vehiclesApi.list(params)
    vehicles.value = data.items
  } catch (err) {
    console.error('Error cargando vehículos:', err)
  }
}

function openModal(v) {
  editing.value = !!v
  editingId.value = v?.id || null
  form.value = v
    ? { plate: v.plate, brand: v.brand, model: v.model, year: v.year, delegacion: v.delegacion, usual_driver_id: v.usual_driver_id }
    : { plate: '', brand: '', model: '', year: null, delegacion: 'Bata', usual_driver_id: null }
  formError.value = ''
  showModal.value = true
}

async function save() {
  formError.value = ''
  try {
    if (editing.value) {
      await vehiclesApi.update(editingId.value, form.value)
    } else {
      await vehiclesApi.create(form.value)
    }
    showModal.value = false
    fetchVehicles()
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function toggleActive(v) {
  try {
    await vehiclesApi.update(v.id, { active: !v.active })
    fetchVehicles()
  } catch (err) {
    console.error('Error:', err)
  }
}

onMounted(fetchVehicles)
</script>

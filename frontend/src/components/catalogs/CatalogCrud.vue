<!--
  CatalogCrud.vue
  Componente genérico de CRUD para catálogos. Tabla con búsqueda,
  paginación, modal de creación/edición y botón de activar/desactivar.
  Configurable mediante props para adaptarse a cada catálogo.
-->
<template>
  <div class="max-w-6xl mx-auto">
    <!-- Cabecera -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">{{ title }}</h1>
      <button
        v-if="canCreate"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openCreate"
      >
        + Nuevo
      </button>
    </div>

    <!-- Filtros y búsqueda -->
    <div class="flex flex-wrap gap-3 mb-4">
      <input
        v-if="searchable"
        v-model="searchQuery"
        type="text"
        placeholder="Buscar..."
        class="flex-1 min-w-[200px] rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        @input="debouncedSearch"
      />
      <slot name="filters" />
      <label class="flex items-center text-sm text-gray-600 gap-1.5">
        <input v-model="showInactive" type="checkbox" class="rounded border-gray-300" />
        Mostrar inactivos
      </label>
    </div>

    <!-- Tabla -->
    <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              {{ col.label }}
            </th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr
            v-for="item in items"
            :key="item.id"
            :class="{ 'bg-gray-50 text-gray-400': !item.active }"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              class="px-4 py-3 text-sm whitespace-nowrap"
            >
              <template v-if="col.type === 'badge'">
                <span
                  :class="[
                    'px-2 py-0.5 text-xs rounded-full',
                    col.badgeColor?.(item[col.key]) || 'bg-gray-100 text-gray-700'
                  ]"
                >
                  {{ col.format ? col.format(item[col.key]) : item[col.key] }}
                </span>
              </template>
              <template v-else-if="col.type === 'boolean'">
                <span v-if="item[col.key]" class="text-green-600">✓</span>
                <span v-else class="text-gray-300">—</span>
              </template>
              <template v-else>
                {{ col.format ? col.format(item[col.key], item) : item[col.key] }}
              </template>
            </td>
            <td class="px-4 py-3 text-right text-sm space-x-2">
              <button
                v-if="canEdit"
                class="text-blue-600 hover:text-blue-800"
                @click="openEdit(item)"
              >
                Editar
              </button>
              <button
                v-if="canToggle"
                :class="item.active ? 'text-red-500 hover:text-red-700' : 'text-green-500 hover:text-green-700'"
                @click="toggleActive(item)"
              >
                {{ item.active ? 'Desactivar' : 'Activar' }}
              </button>
              <button
                v-if="canDelete"
                class="text-sm text-red-600 hover:text-red-800"
                @click="confirmDeleteItem(item)"
              >
                Eliminar
              </button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td :colspan="columns.length + 1" class="px-4 py-8 text-center text-gray-400 text-sm">
              No se encontraron registros
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Paginación -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 text-sm text-gray-600">
      <span>{{ total }} registros — Página {{ page }} de {{ totalPages }}</span>
      <div class="flex gap-2">
        <button
          :disabled="page <= 1"
          class="px-3 py-1 border rounded-md disabled:opacity-40"
          @click="changePage(page - 1)"
        >
          ← Anterior
        </button>
        <button
          :disabled="page >= totalPages"
          class="px-3 py-1 border rounded-md disabled:opacity-40"
          @click="changePage(page + 1)"
        >
          Siguiente →
        </button>
      </div>
    </div>

    <!-- Modal de creación/edición (slot) -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
        @click.self="closeModal"
      >
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">
              {{ editingItem ? 'Editar' : 'Crear' }} {{ singularTitle }}
            </h2>
          </div>
          <div class="px-6 py-4">
            <slot
              name="form"
              :item="editingItem"
              :is-editing="!!editingItem"
              :on-save="handleSave"
              :on-cancel="closeModal"
            />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
    <!-- Modal confirmación eliminar -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showDeleteConfirm = false">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-sm mx-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-2">Confirmar eliminación</h3>
        <p class="text-sm text-gray-600 mb-4">¿Eliminar permanentemente este registro? Esta acción no se puede deshacer.</p>
        <p v-if="deleteError" class="text-sm text-red-600 mb-3 bg-red-50 p-2 rounded">{{ deleteError }}</p>
        <div class="flex justify-end gap-3">
          <button class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="showDeleteConfirm = false">Cancelar</button>
          <button class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700" @click="executeDelete">Eliminar</button>
        </div>
      </div>
    </div>
  
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  singularTitle: { type: String, required: true },
  columns: { type: Array, required: true },
  fetchFn: { type: Function, required: true },
  createFn: { type: Function, default: null },
  updateFn: { type: Function, default: null },
  searchable: { type: Boolean, default: true },
  canCreate: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  canToggle: { type: Boolean, default: false },
  canDelete: { type: Boolean, default: false },
  deleteFn: { type: Function, default: null },
  pageSize: { type: Number, default: 50 },
  extraParams: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['created', 'updated'])

const items = ref([])
const total = ref(0)
const page = ref(1)
const searchQuery = ref('')
const showInactive = ref(false)
const loading = ref(false)
const showModal = ref(false)
const showDeleteConfirm = ref(false)
const deletingItem = ref(null)
const deleteError = ref('')
const editingItem = ref(null)

const totalPages = computed(() => Math.ceil(total.value / props.pageSize))

let searchTimeout = null

async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: props.pageSize,
      active_only: !showInactive.value,
      ...props.extraParams,
    }
    if (searchQuery.value) params.search = searchQuery.value

    const { data } = await props.fetchFn(params)
    // Soporta respuestas paginadas y listas simples
    if (Array.isArray(data)) {
      items.value = data
      total.value = data.length
    } else {
      items.value = data.items
      total.value = data.total
    }
  } catch (err) {
    console.error('Error cargando datos:', err)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function debouncedSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    fetchData()
  }, 300)
}

function changePage(newPage) {
  page.value = newPage
  fetchData()
}

function openCreate() {
  editingItem.value = null
  showModal.value = true
}

function openEdit(item) {
  editingItem.value = { ...item }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingItem.value = null
}

async function handleSave(data) {
  try {
    if (editingItem.value) {
      await props.updateFn(editingItem.value.id, data)
      emit('updated')
    } else {
      await props.createFn(data)
      emit('created')
    }
    closeModal()
    fetchData()
  } catch (err) {
    throw err  // Propagar al formulario para mostrar error
  }
}

async function toggleActive(item) {
  try {
    await props.updateFn(item.id, { active: !item.active })
    fetchData()
  } catch (err) {
    console.error('Error al cambiar estado:', err)
  }
}

function confirmDeleteItem(item) {
  deletingItem.value = item
  deleteError.value = ''
  showDeleteConfirm.value = true
}

async function executeDelete() {
  if (!deletingItem.value || !props.deleteFn) return
  try {
    await props.deleteFn(deletingItem.value.id)
    showDeleteConfirm.value = false
    deletingItem.value = null
    deleteError.value = ''
    fetchData()
  } catch (e) {
    deleteError.value = e.response?.data?.detail || 'Error al eliminar'
  }
}

// Recargar al cambiar filtros
watch(showInactive, fetchData)
watch(() => props.extraParams, fetchData, { deep: true })

// Carga inicial
fetchData()

// Exponer para uso externo
defineExpose({ fetchData, editingItem })
</script>

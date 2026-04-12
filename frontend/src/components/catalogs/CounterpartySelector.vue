<!--
  CounterpartySelector.vue
  Selector mixto de contraparte: búsqueda en catálogos (proveedores, empleados, socios)
  o texto libre con validación de nombre completo (mínimo dos palabras).
  Props: modelValue (objeto con supplier_id, employee_id, partner_id, counterparty_free)
  Emits: update:modelValue
-->
<template>
  <div class="space-y-3">
    <label class="block text-sm font-medium text-gray-700">Contraparte *</label>

    <!-- Selector de modo -->
    <div class="flex gap-2 text-sm">
      <button
        v-for="mode in modes"
        :key="mode.key"
        type="button"
        :class="[
          'px-3 py-1.5 rounded-md border',
          selectedMode === mode.key
            ? 'bg-blue-50 border-blue-300 text-blue-700'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        ]"
        @click="selectedMode = mode.key"
      >
        {{ mode.label }}
      </button>
    </div>

    <!-- Búsqueda en catálogo (proveedor, empleado, socio) -->
    <div v-if="selectedMode !== 'free'" class="relative">
      <input
        v-model="searchTerm"
        type="text"
        :placeholder="`Buscar ${currentModeLabel}...`"
        class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
        @input="search"
        @focus="showDropdown = true"
      />
      <ul
        v-if="showDropdown && results.length"
        class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto"
      >
        <li
          v-for="item in results"
          :key="item.id"
          class="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50"
          @click="selectItem(item)"
        >
          <span class="font-medium">{{ item.code || item.full_name || item.name }}</span>
          <span class="text-gray-500 ml-2">
            {{ item.name || item.full_name }}
          </span>
        </li>
      </ul>

      <!-- Selección actual -->
      <div
        v-if="selectedItem"
        class="mt-2 flex items-center gap-2 px-3 py-2 bg-blue-50 rounded-md text-sm"
      >
        <span class="text-blue-700 font-medium">
          {{ selectedItem.name || selectedItem.full_name }}
        </span>
        <button
          type="button"
          class="ml-auto text-blue-400 hover:text-blue-600"
          @click="clearSelection"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Texto libre -->
    <div v-else>
      <input
        v-model="freeText"
        type="text"
        placeholder="Nombre y apellido (mínimo dos palabras)"
        class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
        @input="emitFreeText"
      />
      <p v-if="freeTextError" class="mt-1 text-xs text-red-500">{{ freeTextError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { suppliersApi, employeesApi, partnersApi } from '@/api/catalogs'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue'])

const modes = [
  { key: 'supplier', label: 'Proveedor' },
  { key: 'employee', label: 'Empleado' },
  { key: 'partner', label: 'Socio' },
  { key: 'free', label: 'Texto libre' },
]

const selectedMode = ref('supplier')
const searchTerm = ref('')
const results = ref([])
const showDropdown = ref(false)
const selectedItem = ref(null)
const freeText = ref('')
const freeTextError = ref('')

const currentModeLabel = computed(() =>
  modes.find(m => m.key === selectedMode.value)?.label || ''
)

// Mapa de APIs por modo
const apiMap = {
  supplier: suppliersApi,
  employee: employeesApi,
  partner: partnersApi,
}

async function search() {
  if (searchTerm.value.length < 2) {
    results.value = []
    return
  }
  try {
    const api = apiMap[selectedMode.value]
    const { data } = await api.list({ search: searchTerm.value, active_only: true })
    results.value = data.items || data
  } catch (err) {
    results.value = []
  }
}

function selectItem(item) {
  selectedItem.value = item
  searchTerm.value = item.name || item.full_name
  showDropdown.value = false
  emitCatalogSelection()
}

function clearSelection() {
  selectedItem.value = null
  searchTerm.value = ''
  results.value = []
  emitEmpty()
}

function emitCatalogSelection() {
  const value = {
    supplier_id: null,
    employee_id: null,
    partner_id: null,
    counterparty_free: null,
  }
  if (selectedMode.value === 'supplier') value.supplier_id = selectedItem.value.id
  else if (selectedMode.value === 'employee') value.employee_id = selectedItem.value.id
  else if (selectedMode.value === 'partner') value.partner_id = selectedItem.value.id

  emit('update:modelValue', value)
}

function emitFreeText() {
  const words = freeText.value.trim().split(/\s+/)
  if (words.length < 2 && freeText.value.trim().length > 0) {
    freeTextError.value = 'Debe incluir al menos nombre y apellido'
  } else {
    freeTextError.value = ''
  }
  emit('update:modelValue', {
    supplier_id: null,
    employee_id: null,
    partner_id: null,
    counterparty_free: freeText.value.trim() || null,
  })
}

function emitEmpty() {
  emit('update:modelValue', {
    supplier_id: null,
    employee_id: null,
    partner_id: null,
    counterparty_free: null,
  })
}

// Limpiar al cambiar de modo
watch(selectedMode, () => {
  clearSelection()
  freeText.value = ''
  freeTextError.value = ''
  emitEmpty()
})

// Cerrar dropdown al hacer clic fuera
document.addEventListener('click', (e) => {
  if (!e.target.closest('.relative')) {
    showDropdown.value = false
  }
})
</script>

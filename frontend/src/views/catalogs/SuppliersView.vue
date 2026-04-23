<!--
  SuppliersView.vue — /suppliers
  Gestión de proveedores con filtro por tipo.
-->
<template>
  <div class="p-6">
    <CatalogCrud
      ref="catalogRef"
      title="Proveedores"
      singular-title="Proveedor"
      :columns="columns"
      :fetch-fn="suppliersApi.list"
      :create-fn="suppliersApi.create"
      :update-fn="suppliersApi.update"
      :can-create="isAdmin"
      :can-edit="isAdmin"
      :can-toggle="isAdmin"
      :can-delete="isAdmin"
      :delete-fn="suppliersApi.delete"
      :extra-params="extraParams"
    >
      <template #filters>
        <select
          v-model="typeFilter"
          class="rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          @change="onFilterChange"
        >
          <option value="">Todos los tipos</option>
          <option value="empresa">Empresa</option>
          <option value="organismo">Organismo</option>
          <option value="aerolinea">Aerolínea</option>
          <option value="gasolinera">Gasolinera</option>
          <option value="banco">Banco</option>
          <option value="otro">Otro</option>
        </select>
      </template>

      <template #form="{ item, isEditing, onSave, onCancel }">
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
              <input v-model="form.code" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tipo *</label>
              <select v-model="form.supplier_type" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="empresa">Empresa</option>
                <option value="organismo">Organismo</option>
                <option value="aerolinea">Aerolínea</option>
                <option value="gasolinera">Gasolinera</option>
                <option value="banco">Banco</option>
                <option value="otro">Otro</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
            <input v-model="form.name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">NIF / Tax ID</label>
              <input v-model="form.tax_id" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Contacto</label>
              <input v-model="form.contact_name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
              <input v-model="form.phone" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input v-model="form.email" type="email" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button class="px-4 py-2 text-sm text-gray-600" @click="onCancel">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md" @click="submit(onSave)">Guardar</button>
          </div>
        </div>
      </template>
    </CatalogCrud>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import CatalogCrud from '@/components/catalogs/CatalogCrud.vue'
import { suppliersApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const typeFilter = ref('')
const extraParams = ref({})

const columns = [
  { key: 'code', label: 'Código' },
  { key: 'name', label: 'Nombre' },
  { key: 'supplier_type', label: 'Tipo', type: 'badge',
    format: (v) => ({ empresa: 'Empresa', organismo: 'Organismo', aerolinea: 'Aerolínea', gasolinera: 'Gasolinera', banco: 'Banco', otro: 'Otro' }[v] || v),
    badgeColor: () => 'bg-gray-100 text-gray-700'
  },
  { key: 'contact_name', label: 'Contacto', format: (v) => v || '—' },
  { key: 'phone', label: 'Teléfono', format: (v) => v || '—' },
]

const form = ref({ supplier_type: 'empresa' })
const error = ref('')
const catalogRef = ref(null)

function onFilterChange() {
  extraParams.value = typeFilter.value ? { supplier_type: typeFilter.value } : {}
}

async function submit(onSave) {
  error.value = ''
  try { await onSave(form.value) }
  catch (err) { error.value = err.response?.data?.detail || 'Error al guardar' }
}

// H9 — Sincronizar form con el item que abre CatalogCrud
watch(() => catalogRef.value?.editingItem, (item) => {
  if (item) {
    form.value = {
      code: item.code || '',
      supplier_type: item.supplier_type || 'empresa',
      name: item.name || '',
      tax_id: item.tax_id || '',
      contact_name: item.contact_name || '',
      phone: item.phone || '',
      email: item.email || '',
    }
  } else {
    form.value = { supplier_type: 'empresa' }
  }
}, { immediate: true })
</script>

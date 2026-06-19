<!--
  WorksView.vue — /works
  Gestión del catálogo de obras (cada obra cuelga de un proyecto).
-->
<template>
  <div class="p-6">
    <CatalogCrud
      ref="catalogRef"
      title="Obras"
      singular-title="Obra"
      :columns="columns"
      :fetch-fn="worksApi.list"
      :create-fn="worksApi.create"
      :update-fn="worksApi.update"
      :can-create="isAdmin"
      :can-edit="isAdmin"
      :can-toggle="isAdmin"
    >
      <template #form="{ item, isEditing, onSave, onCancel }">
        <WorkForm :key="item ? item.id : 'new'" :item="item" :is-editing="isEditing" @save="onSave" @cancel="onCancel" />
      </template>
    </CatalogCrud>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import CatalogCrud from '@/components/catalogs/CatalogCrud.vue'
import WorkForm from '@/components/catalogs/WorkForm.vue'
import { worksApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const catalogRef = ref(null)
const columns = [
  { key: 'project_name', label: 'Proyecto' },
  { key: 'code', label: 'Código' },
  { key: 'name', label: 'Nombre' },
  { key: 'active', label: 'Estado', type: 'boolean' },
]
</script>

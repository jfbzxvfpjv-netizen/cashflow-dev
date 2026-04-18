<!--
  ProjectsView.vue — /projects
  Gestión de proyectos y obras.
-->
<template>
  <div class="p-6">
    <div class="text-xs text-red-500 mb-2">DEBUG isAdmin: {{ isAdmin }} role: {{ $store?.user?.role }}</div>
    <CatalogCrud
      ref="catalogRef"
      title="Proyectos"
      singular-title="Proyecto"
      :columns="columns"
      :fetch-fn="projectsApi.list"
      :create-fn="projectsApi.create"
      :update-fn="projectsApi.update"
      :can-create="isAdmin"
      :can-edit="isAdmin"
      :can-toggle="isAdmin"
      @created="onProjectChanged"
      @updated="onProjectChanged"
    >
      <template #form="{ item, isEditing, onSave, onCancel }">
        <ProjectForm
          :key="item ? item.id : 'new'"
          :item="item"
          :is-editing="isEditing"
          @save="onSave"
          @cancel="onCancel"
        />
      </template>
    </CatalogCrud>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import CatalogCrud from '@/components/catalogs/CatalogCrud.vue'
import ProjectForm from '@/components/catalogs/ProjectForm.vue'
import { projectsApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const catalogRef = ref(null)

const columns = [
  { key: 'code', label: 'Código' },
  { key: 'name', label: 'Nombre' },
  { key: 'active', label: 'Estado', type: 'boolean' },
]

function onProjectChanged() {}
</script>

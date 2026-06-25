<!--
  ProjectDetailView.vue — /projects/:id
  Detalle de un proyecto y gestión de sus obras (anidadas).
-->
<template>
  <div class="p-6">
    <div class="max-w-6xl mx-auto">
      <router-link to="/projects" class="text-sm text-blue-600 hover:text-blue-800">← Volver a proyectos</router-link>

      <div v-if="project" class="mt-3 mb-8 bg-white border border-gray-200 rounded-lg p-5">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold text-gray-900">{{ project.code }} — {{ project.name }}</h1>
            <p v-if="project.description" class="text-sm text-gray-500 mt-1">{{ project.description }}</p>
          </div>
          <span
            :class="project.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'"
            class="px-3 py-1 text-xs rounded-full"
          >
            {{ project.active ? 'Activo' : 'Inactivo' }}
          </span>
        </div>
      </div>
      <div v-else-if="error" class="mt-3 mb-8 text-sm text-red-600 bg-red-50 p-3 rounded">{{ error }}</div>

      <CatalogCrud
        v-if="project"
        title="Obras del proyecto"
        singular-title="Obra"
        :columns="columns"
        :fetch-fn="worksApi.list"
        :create-fn="worksApi.create"
        :update-fn="worksApi.update"
        :can-create="isAdmin"
        :can-edit="isAdmin"
        :can-toggle="isAdmin"
        :extra-params="{ project_id: projectId }"
      >
        <template #form="{ item, isEditing, onSave, onCancel }">
          <WorkForm
            :key="item ? item.id : 'new'"
            :item="item"
            :is-editing="isEditing"
            :locked-project-id="projectId"
            @save="onSave"
            @cancel="onCancel"
          />
        </template>
      </CatalogCrud>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CatalogCrud from '@/components/catalogs/CatalogCrud.vue'
import WorkForm from '@/components/catalogs/WorkForm.vue'
import { projectsApi, worksApi } from '@/api/catalogs'

const route = useRoute()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')
const projectId = Number(route.params.id)
const project = ref(null)
const error = ref('')
const columns = [
  { key: 'code', label: 'Código' },
  { key: 'name', label: 'Nombre' },
  { key: 'active', label: 'Estado', type: 'boolean' },
]
onMounted(async () => {
  try {
    const { data } = await projectsApi.get(projectId)
    project.value = data
  } catch (e) {
    error.value = 'No se pudo cargar el proyecto'
  }
})
</script>

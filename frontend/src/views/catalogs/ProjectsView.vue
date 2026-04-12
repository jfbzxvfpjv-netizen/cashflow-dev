<!--
  ProjectsView.vue — /projects
  Gestión de proyectos y obras.
-->
<template>
  <div class="p-6">
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
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Código</label>
            <input v-model="form.code" type="text" :disabled="isEditing"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
            <input v-model="form.name" type="text"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
            <textarea v-model="form.description" rows="2"
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"></textarea>
          </div>
          <p v-if="formError" class="text-sm text-red-600">{{ formError }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" class="px-4 py-2 text-sm text-gray-600" @click="onCancel">Cancelar</button>
            <button type="button" class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md"
              @click="handleSave(onSave)">Guardar</button>
          </div>
        </div>
      </template>
    </CatalogCrud>

    <!-- Panel de obras del proyecto seleccionado -->
    <div v-if="selectedProject" class="mt-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-800">
          Obras de {{ selectedProject.code }} — {{ selectedProject.name }}
        </h2>
        <button
          v-if="isAdmin"
          class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
          @click="showWorkModal = true"
        >
          + Nueva obra
        </button>
      </div>

      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nombre</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
              <th v-if="isAdmin" class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="work in projectWorks" :key="work.id" :class="{ 'text-gray-400': !work.active }">
              <td class="px-4 py-2 text-sm font-mono">{{ work.code }}</td>
              <td class="px-4 py-2 text-sm">{{ work.name }}</td>
              <td class="px-4 py-2 text-sm">
                <span :class="work.active ? 'text-green-600' : 'text-red-400'">
                  {{ work.active ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
              <td v-if="isAdmin" class="px-4 py-2 text-sm text-right">
                <button class="text-blue-600 hover:text-blue-800 mr-2" @click="editWork(work)">
                  Editar
                </button>
              </td>
            </tr>
            <tr v-if="!projectWorks.length">
              <td colspan="4" class="px-4 py-6 text-center text-gray-400 text-sm">
                Sin obras registradas
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import CatalogCrud from '@/components/catalogs/CatalogCrud.vue'
import { projectsApi, worksApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const columns = [
  { key: 'code', label: 'Código' },
  { key: 'name', label: 'Nombre' },
  { key: 'description', label: 'Descripción' },
  { key: 'active', label: 'Estado', type: 'boolean' },
]

const form = ref({ code: '', name: '', description: '' })
const formError = ref('')

const selectedProject = ref(null)
const projectWorks = ref([])
const showWorkModal = ref(false)
const catalogRef = ref(null)

// Sincronizar form con el item que abre CatalogCrud
watch(() => catalogRef.value?.editingItem, (item) => {
  if (item) {
    form.value = { code: item.code || '', name: item.name || '', description: item.description || '' }
  } else {
    form.value = { code: '', name: '', description: '' }
  }
}, { immediate: true })

async function handleSave(onSave) {
  formError.value = ''
  try {
    await onSave(form.value)
  } catch (err) {
    formError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function onProjectChanged() {
  if (selectedProject.value) {
    await loadWorks(selectedProject.value.id)
  }
}

async function loadWorks(projectId) {
  try {
    const { data } = await worksApi.list({ project_id: projectId, active_only: false, page_size: 500 })
    projectWorks.value = data.items
  } catch (err) {
    projectWorks.value = []
  }
}

function editWork(work) {
  console.log('Editar obra:', work)
}
</script>

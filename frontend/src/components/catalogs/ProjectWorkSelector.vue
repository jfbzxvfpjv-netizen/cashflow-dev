<!--
  ProjectWorkSelector.vue
  Selector de proyecto con búsqueda. Al seleccionar proyecto carga sus obras.
  Permite crear obra nueva al vuelo inline.
  Props: modelValue (objeto {project_id, work_id})
  Emits: update:modelValue
-->
<template>
  <div class="space-y-3">
    <!-- Selector de proyecto -->
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Proyecto *</label>
      <div class="relative">
        <input
          v-model="projectSearch"
          type="text"
          placeholder="Buscar proyecto..."
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          @focus="showProjectDropdown = true"
          @input="filterProjects"
        />
        <ul
          v-if="showProjectDropdown && filteredProjects.length"
          class="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto"
        >
          <li
            v-for="project in filteredProjects"
            :key="project.id"
            class="px-3 py-2 text-sm cursor-pointer hover:bg-blue-50"
            @click="selectProject(project)"
          >
            <span class="font-medium">{{ project.code }}</span>
            <span class="text-gray-500 ml-2">{{ project.name }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Selector de obra (visible tras seleccionar proyecto) -->
    <div v-if="selectedProject">
      <label class="block text-sm font-medium text-gray-700 mb-1">Obra *</label>
      <div class="flex gap-2">
        <select
          v-model="selectedWorkId"
          class="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          @change="emitValue"
        >
          <option value="">Seleccionar obra...</option>
          <option v-for="work in works" :key="work.id" :value="work.id">
            {{ work.code }} — {{ work.name }}
          </option>
        </select>
        <button
          type="button"
          class="px-3 py-2 text-sm bg-green-50 text-green-700 border border-green-300 rounded-md hover:bg-green-100"
          @click="showNewWork = true"
          title="Crear obra al vuelo"
        >
          + Nueva
        </button>
      </div>
    </div>

    <!-- Formulario inline de creación al vuelo -->
    <div
      v-if="showNewWork"
      class="p-3 bg-green-50 border border-green-200 rounded-md space-y-2"
    >
      <p class="text-sm font-medium text-green-800">
        Nueva obra en {{ selectedProject.code }}
      </p>
      <div class="flex gap-2">
        <input
          v-model="newWorkCode"
          type="text"
          placeholder="Código"
          class="w-1/3 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          v-model="newWorkName"
          type="text"
          placeholder="Nombre"
          class="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div class="flex gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
          :disabled="!newWorkCode || !newWorkName || creatingWork"
          @click="createWorkInline"
        >
          {{ creatingWork ? 'Creando...' : 'Crear' }}
        </button>
        <button
          type="button"
          class="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
          @click="cancelNewWork"
        >
          Cancelar
        </button>
      </div>
      <p v-if="workError" class="text-sm text-red-600">{{ workError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { projectsApi, worksApi } from '@/api/catalogs'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ project_id: null, work_id: null }) },
})
const emit = defineEmits(['update:modelValue'])

// Estado del selector de proyecto
const projects = ref([])
const filteredProjects = ref([])
const projectSearch = ref('')
const showProjectDropdown = ref(false)
const selectedProject = ref(null)

// Estado del selector de obra
const works = ref([])
const selectedWorkId = ref('')

// Estado de creación al vuelo
const showNewWork = ref(false)
const newWorkCode = ref('')
const newWorkName = ref('')
const creatingWork = ref(false)
const workError = ref('')

// Cargar proyectos al montar
onMounted(async () => {
  try {
    const { data } = await projectsApi.list({ active_only: true, page_size: 200 })
    projects.value = data.items
    filteredProjects.value = data.items
  } catch (err) {
    console.error('Error cargando proyectos:', err)
  }
})

function filterProjects() {
  const term = projectSearch.value.toLowerCase()
  filteredProjects.value = projects.value.filter(
    p => p.code.toLowerCase().includes(term) || p.name.toLowerCase().includes(term)
  )
}

async function selectProject(project) {
  selectedProject.value = project
  projectSearch.value = `${project.code} — ${project.name}`
  showProjectDropdown.value = false
  selectedWorkId.value = ''

  // Cargar obras del proyecto seleccionado
  try {
    const { data } = await worksApi.list({
      project_id: project.id, active_only: true, page_size: 500
    })
    works.value = data.items
  } catch (err) {
    console.error('Error cargando obras:', err)
    works.value = []
  }

  emitValue()
}

function emitValue() {
  emit('update:modelValue', {
    project_id: selectedProject.value?.id || null,
    work_id: selectedWorkId.value ? parseInt(selectedWorkId.value) : null,
  })
}

async function createWorkInline() {
  creatingWork.value = true
  workError.value = ''
  try {
    const { data } = await worksApi.createInline({
      project_id: selectedProject.value.id,
      code: newWorkCode.value,
      name: newWorkName.value,
    })
    // Añadir la nueva obra a la lista y seleccionarla
    works.value.push(data)
    selectedWorkId.value = data.id
    cancelNewWork()
    emitValue()
  } catch (err) {
    workError.value = err.response?.data?.detail || 'Error al crear la obra'
  } finally {
    creatingWork.value = false
  }
}

function cancelNewWork() {
  showNewWork.value = false
  newWorkCode.value = ''
  newWorkName.value = ''
  workError.value = ''
}

// Cerrar dropdown al hacer clic fuera
document.addEventListener('click', (e) => {
  if (!e.target.closest('.relative')) {
    showProjectDropdown.value = false
  }
})

// Pre-seleccionar si hay valores iniciales
watch(
  () => props.modelValue,
  async (val) => {
    if (val?.project_id && !selectedProject.value) {
      const proj = projects.value.find(p => p.id === val.project_id)
      if (proj) {
        await selectProject(proj)
        if (val.work_id) {
          selectedWorkId.value = val.work_id
        }
      }
    }
  },
  { immediate: true }
)
</script>

<!--
  WorkForm.vue — Formulario de creación y edición de obras.
  La obra cuelga de un proyecto; el proyecto solo se elige al crear.
-->
<template>
  <div class="space-y-4">
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Proyecto *</label>
      <select
        v-if="!isEditing && !lockedProjectId"
        v-model.number="form.project_id"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option :value="null" disabled>Selecciona un proyecto</option>
        <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.code }} — {{ p.name }}</option>
      </select>
      <input
        v-else
        type="text"
        :value="lockedLabel || projectLabel"
        disabled
        class="w-full rounded-md border bg-gray-100 border-gray-200 text-gray-500 px-3 py-2 text-sm cursor-not-allowed"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Código *</label>
      <input
        v-model="form.code"
        type="text"
        :disabled="isEditing"
        :class="[
          'w-full rounded-md border px-3 py-2 text-sm',
          isEditing ? 'bg-gray-100 border-gray-200 text-gray-500 cursor-not-allowed' : 'border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500'
        ]"
      />
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Nombre *</label>
      <input
        v-model="form.name"
        type="text"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <div class="flex justify-end gap-3 pt-2">
      <button type="button" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="$emit('cancel')">Cancelar</button>
      <button type="button" class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700" @click="save">Guardar</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { projectsApi } from '@/api/catalogs'

const props = defineProps({
  item: { type: Object, default: null },
  isEditing: { type: Boolean, default: false },
  lockedProjectId: { type: Number, default: null },
})
const emit = defineEmits(['save', 'cancel'])

const projects = ref([])
const form = ref({
  project_id: props.item?.project_id || props.lockedProjectId || null,
  code: props.item?.code || '',
  name: props.item?.name || '',
})
const error = ref('')

const projectLabel = computed(() => {
  const c = props.item?.project_code || ''
  const n = props.item?.project_name || ''
  return [c, n].filter(Boolean).join(' — ')
})
const lockedLabel = computed(() => {
  if (!props.lockedProjectId) return ''
  const p = projects.value.find(x => x.id === props.lockedProjectId)
  return p ? `${p.code} — ${p.name}` : `Proyecto #${props.lockedProjectId}`
})

onMounted(async () => {
  try {
    const res = await projectsApi.list()
    projects.value = res.data?.items || res.data || []
  } catch (e) {
    error.value = 'No se pudieron cargar los proyectos'
  }
})

async function save() {
  error.value = ''
  if (!props.isEditing && !form.value.project_id) { error.value = 'Selecciona un proyecto'; return }
  if (!form.value.code.trim()) { error.value = 'El código es obligatorio'; return }
  if (!form.value.name.trim()) { error.value = 'El nombre es obligatorio'; return }
  const payload = props.isEditing
    ? { code: form.value.code, name: form.value.name }
    : { project_id: form.value.project_id, code: form.value.code, name: form.value.name }
  try {
    await emit('save', payload)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al guardar'
  }
}
</script>

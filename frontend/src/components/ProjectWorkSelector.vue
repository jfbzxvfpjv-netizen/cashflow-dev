<!--
  Módulo 6 — ProjectWorkSelector.vue
  Selector de proyecto con búsqueda y carga dinámica de obras asociadas.
  Emite el par { project_id, work_id } al seleccionar.
-->
<template>
  <div class="space-y-2">
    <div v-for="(item, idx) in selected" :key="idx" class="flex gap-2 items-end">
      <div class="flex-1">
        <label class="block text-xs text-gray-600 mb-1">Proyecto</label>
        <select v-model="item.project_id" @change="onProjectChange(idx)"
                class="w-full border rounded px-2 py-1.5 text-sm">
          <option :value="null" disabled>Seleccionar...</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <div class="flex-1">
        <label class="block text-xs text-gray-600 mb-1">Obra</label>
        <select v-model="item.work_id" class="w-full border rounded px-2 py-1.5 text-sm">
          <option :value="null" disabled>Seleccionar...</option>
          <option v-for="w in worksFor(item.project_id)" :key="w.id" :value="w.id">{{ w.name }}</option>
        </select>
      </div>
      <button v-if="selected.length > 1" @click="removeRow(idx)"
              class="text-red-500 hover:text-red-700 text-lg pb-1">✕</button>
    </div>
    <button @click="addRow" type="button"
            class="text-sm text-blue-600 hover:text-blue-800">+ Añadir proyecto/obra</button>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'

const props = defineProps({
  modelValue: { type: Array, default: () => [{ project_id: null, work_id: null }] }
})
const emit = defineEmits(['update:modelValue'])

const projects = ref([])
const worksByProject = ref({})
const selected = ref([...props.modelValue])

async function loadProjects() {
  const { data } = await api.get('/projects')
  projects.value = Array.isArray(data) ? data : (data.items || [])
}

async function loadWorks(projectId) {
  if (!projectId || worksByProject.value[projectId]) return
  const { data } = await api.get('/works', { params: { project_id: projectId } })
  worksByProject.value[projectId] = Array.isArray(data) ? data : (data.items || [])
}

function worksFor(projectId) {
  return worksByProject.value[projectId] || []
}

function onProjectChange(idx) {
  selected.value[idx].work_id = null
  if (selected.value[idx].project_id) {
    loadWorks(selected.value[idx].project_id)
  }
  emitValue()
}

function addRow() {
  selected.value.push({ project_id: null, work_id: null })
  emitValue()
}

function removeRow(idx) {
  selected.value.splice(idx, 1)
  emitValue()
}

function emitValue() {
  emit('update:modelValue', selected.value.filter(s => s.project_id && s.work_id))
}

watch(selected, () => emitValue(), { deep: true })

onMounted(async () => {
  await loadProjects()
  for (const s of selected.value) {
    if (s.project_id) await loadWorks(s.project_id)
  }
})
</script>

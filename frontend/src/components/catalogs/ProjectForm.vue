<!--
  ProjectForm.vue — Formulario de creación y edición de proyectos.
-->
<template>
  <div class="space-y-4">
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
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
      <textarea
        v-model="form.description"
        rows="2"
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      ></textarea>
    </div>
    <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
    <div class="flex justify-end gap-3 pt-2">
      <button type="button" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800" @click="$emit('cancel')">
        Cancelar
      </button>
      <button
        type="button"
        class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
        @click="save"
      >
        Guardar
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  item: { type: Object, default: null },
  isEditing: { type: Boolean, default: false },
})

const emit = defineEmits(['save', 'cancel'])

// Inicializar directamente desde props — el item ya tiene valor cuando el componente monta
const form = ref({
  code: props.item?.code || '',
  name: props.item?.name || '',
  description: props.item?.description || '',
})

const error = ref('')

async function save() {
  error.value = ''
  if (!form.value.code.trim()) { error.value = 'El código es obligatorio'; return }
  if (!form.value.name.trim()) { error.value = 'El nombre es obligatorio'; return }
  try {
    await emit('save', { ...form.value })
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al guardar'
  }
}
</script>

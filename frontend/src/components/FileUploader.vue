<!--
  Parche M6 — FileUploader.vue
  Componente de subida de adjuntos con drag & drop, barra de progreso,
  lista de adjuntos existentes con descarga y eliminación.
-->
<template>
  <div class="space-y-3">
    <!-- Zona de subida -->
    <div v-if="canUpload"
         @dragover.prevent="dragOver = true"
         @dragleave="dragOver = false"
         @drop.prevent="onDrop"
         :class="dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'"
         class="border-2 border-dashed rounded-lg p-4 text-center transition-colors cursor-pointer"
         @click="$refs.fileInput.click()">
      <input ref="fileInput" type="file" class="hidden" multiple @change="onFileSelect" />
      <p class="text-sm text-gray-500">
        <span class="text-blue-600 font-medium">Haga clic</span> o arrastre ficheros aquí
      </p>
      <p class="text-xs text-gray-400 mt-1">Máx. {{ maxFileMB }} MB por fichero · {{ maxTxnMB }} MB por transacción</p>
    </div>

    <!-- Progreso de subida -->
    <div v-for="(u, idx) in uploading" :key="'up-'+idx" class="flex items-center gap-2 text-sm">
      <span class="truncate flex-1">{{ u.name }}</span>
      <div class="w-32 bg-gray-200 rounded h-2">
        <div class="bg-blue-600 rounded h-2 transition-all" :style="{ width: u.progress + '%' }"></div>
      </div>
      <span class="text-xs text-gray-500">{{ u.progress }}%</span>
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 p-2 rounded text-sm">{{ error }}</div>

    <!-- Lista de adjuntos -->
    <div v-if="attachments.length" class="space-y-1">
      <div v-for="att in attachments" :key="att.id"
           class="flex items-center gap-2 bg-gray-50 rounded px-3 py-2 text-sm">
        <span class="text-base">📎</span>
        <span class="flex-1 truncate">{{ att.original_filename }}</span>
        <span class="text-xs text-gray-400">{{ formatSize(att.file_size_bytes) }}</span>
        <a :href="downloadUrl(att.id)" target="_blank"
           class="text-blue-600 hover:text-blue-800 text-xs">Descargar</a>
        <button v-if="canUpload && !att.locked"
                @click="deleteAttachment(att.id)"
                class="text-red-500 hover:text-red-700 text-xs">Eliminar</button>
        <span v-if="att.locked" class="text-gray-400 text-xs">🔒</span>
      </div>
    </div>
    <p v-else-if="transactionId" class="text-xs text-gray-400">Sin adjuntos</p>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import attachmentService from '@/services/attachmentService'

const props = defineProps({
  transactionId: { type: Number, default: null },
  canUpload: { type: Boolean, default: true },
  maxFileMB: { type: Number, default: 10 },
  maxTxnMB: { type: Number, default: 50 }
})

const emit = defineEmits(['uploaded', 'deleted'])

const attachments = ref([])
const uploading = ref([])
const dragOver = ref(false)
const error = ref('')

async function loadAttachments() {
  if (!props.transactionId) return
  try {
    const { data } = await attachmentService.list(props.transactionId)
    attachments.value = data || []
  } catch (e) {
    // Silenciar si la transacción aún no tiene adjuntos
  }
}

function downloadUrl(attId) {
  return attachmentService.downloadUrl(props.transactionId, attId)
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function uploadFiles(files) {
  error.value = ''
  for (const file of files) {
    if (file.size > props.maxFileMB * 1024 * 1024) {
      error.value = `"${file.name}" supera el límite de ${props.maxFileMB} MB`
      continue
    }
    const uploadState = { name: file.name, progress: 0 }
    uploading.value.push(uploadState)
    try {
      await attachmentService.upload(props.transactionId, file, (e) => {
        if (e.total) uploadState.progress = Math.round((e.loaded / e.total) * 100)
      })
      emit('uploaded')
    } catch (e) {
      error.value = e.response?.data?.detail || `Error al subir "${file.name}"`
    } finally {
      uploading.value = uploading.value.filter(u => u !== uploadState)
    }
  }
  await loadAttachments()
}

function onFileSelect(event) {
  const files = event.target.files
  if (files.length) uploadFiles(Array.from(files))
  event.target.value = ''
}

function onDrop(event) {
  dragOver.value = false
  const files = event.dataTransfer.files
  if (files.length) uploadFiles(Array.from(files))
}

async function deleteAttachment(attId) {
  if (!confirm('¿Eliminar este adjunto?')) return
  error.value = ''
  try {
    await attachmentService.delete(props.transactionId, attId)
    emit('deleted')
    await loadAttachments()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error al eliminar'
  }
}

watch(() => props.transactionId, () => loadAttachments())
onMounted(() => loadAttachments())
</script>

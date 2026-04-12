<template>
  <div class="max-w-5xl mx-auto px-4 py-6">
    <!-- Cabecera -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Gestión de Backups</h1>
        <p class="text-sm text-gray-500 mt-1">
          Backups de la base de datos PostgreSQL — Retención automática 30 días
        </p>
      </div>
      <input
        ref="fileInput"
        type="file"
        accept=".dump"
        class="hidden"
        @change="uploadBackup"
      />
      <button
        @click="$refs.fileInput.click()"
        :disabled="uploading"
        class="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg
               hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors text-sm font-medium mr-2"
      >
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
        </svg>
        {{ uploading ? 'Subiendo...' : 'Subir Backup' }}
      </button>
      <button
        @click="createBackup"
        :disabled="creating"
        class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg
               hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors text-sm font-medium"
      >
        <svg v-if="creating" class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
        </svg>
        <svg v-else class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 4v16m8-8H4"/>
        </svg>
        {{ creating ? 'Creando backup...' : 'Crear Backup Manual' }}
      </button>
    </div>

    <!-- Mensaje de estado -->
    <div v-if="statusMessage"
         :class="[
           'mb-4 px-4 py-3 rounded-lg text-sm',
           statusType === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
           statusType === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
           'bg-blue-50 text-blue-800 border border-blue-200'
         ]">
      {{ statusMessage }}
    </div>

    <!-- Tabla de backups -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">
        <svg class="animate-spin h-8 w-8 mx-auto mb-3 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
        </svg>
        Cargando backups...
      </div>

      <div v-else-if="backups.length === 0" class="p-8 text-center text-gray-500">
        <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8"/>
        </svg>
        No hay backups disponibles. Cree uno con el botón superior.
      </div>

      <table v-else class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Fichero
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Fecha
            </th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Tamaño
            </th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="backup in backups" :key="backup.filename"
              class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3">
              <span class="text-sm font-mono text-gray-800">{{ backup.filename }}</span>
            </td>
            <td class="px-4 py-3">
              <span class="text-sm text-gray-600">{{ formatDate(backup.created_at) }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span class="text-sm text-gray-600">{{ backup.size_mb }} MB</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-2">
                <!-- Descargar -->
                <button
                  @click="downloadBackup(backup.filename)"
                  class="p-1.5 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                  title="Descargar backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                </button>
                <!-- Restaurar -->
                <button
                  @click="openRestoreModal(backup)"
                  class="p-1.5 text-amber-600 hover:bg-amber-50 rounded-md transition-colors"
                  title="Restaurar desde este backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11
                             11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                  </svg>
                </button>
                <!-- Eliminar -->
                <button
                  @click="openDeleteModal(backup)"
                  class="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                  title="Eliminar backup"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138
                             21H7.862a2 2 0 01-1.995-1.858L5 7m5
                             4v6m4-6v6m1-10V4a1 1 0
                             00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pie de tabla -->
      <div v-if="backups.length > 0" class="px-4 py-2 bg-gray-50 text-xs text-gray-500 text-right">
        {{ backups.length }} backup{{ backups.length !== 1 ? 's' : '' }} disponible{{ backups.length !== 1 ? 's' : '' }}
      </div>
    </div>

    <!-- Modal de restauración -->
    <div v-if="showRestoreModal"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="p-2 bg-amber-100 rounded-full">
            <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0
                       2.502-1.667 1.732-2.5L13.732 4c-.77-1.333-2.694-1.333-3.464
                       0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
            </svg>
          </div>
          <h3 class="text-lg font-bold text-gray-800">Confirmar restauración</h3>
        </div>

        <div class="mb-4 space-y-2 text-sm text-gray-600">
          <p>
            Está a punto de restaurar la base de datos desde el backup
            <span class="font-mono font-semibold text-gray-800">{{ selectedBackup?.filename }}</span>.
          </p>
          <p class="text-red-600 font-medium">
            Esta operación reemplazará TODOS los datos actuales de la base de datos
            y no es reversible. Asegúrese de tener un backup del estado actual antes
            de continuar.
          </p>
          <p>
            Escriba <span class="font-mono font-bold">RESTAURAR</span> para confirmar:
          </p>
        </div>

        <input
          v-model="confirmationText"
          type="text"
          placeholder="Escriba RESTAURAR"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4
                 text-sm font-mono focus:ring-2 focus:ring-amber-500
                 focus:border-amber-500 outline-none"
          @keyup.enter="confirmationText === 'RESTAURAR' && executeRestore()"
        />

        <div class="flex justify-end gap-3">
          <button
            @click="closeRestoreModal"
            class="px-4 py-2 text-sm text-gray-700 bg-gray-100
                   hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="executeRestore"
            :disabled="confirmationText !== 'RESTAURAR' || restoring"
            class="px-4 py-2 text-sm text-white bg-amber-600
                   hover:bg-amber-700 rounded-lg transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ restoring ? 'Restaurando...' : 'Restaurar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de eliminación -->
    <div v-if="showDeleteModal"
         class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-xl shadow-xl max-w-sm w-full mx-4 p-6">
        <h3 class="text-lg font-bold text-gray-800 mb-3">Eliminar backup</h3>
        <p class="text-sm text-gray-600 mb-4">
          ¿Confirma la eliminación de
          <span class="font-mono font-semibold">{{ selectedBackup?.filename }}</span>?
          Esta acción no se puede deshacer.
        </p>
        <div class="flex justify-end gap-3">
          <button
            @click="closeDeleteModal"
            class="px-4 py-2 text-sm text-gray-700 bg-gray-100
                   hover:bg-gray-200 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            @click="executeDelete"
            :disabled="deleting"
            class="px-4 py-2 text-sm text-white bg-red-600
                   hover:bg-red-700 rounded-lg transition-colors
                   disabled:opacity-50"
          >
            {{ deleting ? 'Eliminando...' : 'Eliminar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

// ── Estado reactivo ──────────────────────────────────────

const backups = ref([])
const loading = ref(true)
const creating = ref(false)
const uploading = ref(false)
const fileInput = ref(null)
const restoring = ref(false)
const deleting = ref(false)

const statusMessage = ref('')
const statusType = ref('info')

const showRestoreModal = ref(false)
const showDeleteModal = ref(false)
const selectedBackup = ref(null)
const confirmationText = ref('')

// ── API base ─────────────────────────────────────────────

const API_BASE = '/admin/backups'

// ── Subir backup ─────────────────────────────────────

async function uploadBackup(event) {
  const file = event.target.files[0]
  if (!file) return
  if (!file.name.endsWith('.dump')) {
    showStatus('Solo se permiten ficheros .dump', 'error')
    return
  }
  uploading.value = true
  clearStatus()
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post(API_BASE + '/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    showStatus(data.message, 'success')
    await loadBackups()
  } catch (err) {
    showStatus(err.response?.data?.detail || 'Error al subir el backup', 'error')
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

// ── Cargar lista de backups ──────────────────────────────

async function loadBackups() {
  loading.value = true
  try {
    const { data } = await api.get(API_BASE)
    backups.value = data.backups || []
  } catch (err) {
    showStatus('Error al cargar la lista de backups', 'error')
  } finally {
    loading.value = false
  }
}

// ── Crear backup manual ──────────────────────────────────

async function createBackup() {
  creating.value = true
  clearStatus()
  try {
    const { data } = await api.post(API_BASE)
    showStatus(
      `Backup creado: ${data.filename} (${data.size_mb} MB)`,
      'success'
    )
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error al crear el backup',
      'error'
    )
  } finally {
    creating.value = false
  }
}

// ── Descargar backup ─────────────────────────────────────

function downloadBackup(filename) {
  // Abre la descarga en una nueva pestaña con el token de auth
  const token = localStorage.getItem('token')
  const url = `${API_BASE}/${filename}/download`

  api.get(url, { responseType: 'blob' })
    .then(response => {
      const blob = new Blob([response.data])
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = filename
      link.click()
      URL.revokeObjectURL(link.href)
      showStatus(`Descarga iniciada: ${filename}`, 'success')
    })
    .catch(() => {
      showStatus('Error al descargar el backup', 'error')
    })
}

// ── Modal de restauración ────────────────────────────────

function openRestoreModal(backup) {
  selectedBackup.value = backup
  confirmationText.value = ''
  showRestoreModal.value = true
}

function closeRestoreModal() {
  showRestoreModal.value = false
  selectedBackup.value = null
  confirmationText.value = ''
}

async function executeRestore() {
  if (confirmationText.value !== 'RESTAURAR') return
  restoring.value = true
  clearStatus()
  try {
    const { data } = await api.post(
      `${API_BASE}/${selectedBackup.value.filename}/restore`,
      { confirmation: 'RESTAURAR' }
    )
    showStatus(data.message, 'success')
    closeRestoreModal()
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error durante la restauración',
      'error'
    )
  } finally {
    restoring.value = false
  }
}

// ── Modal de eliminación ─────────────────────────────────

function openDeleteModal(backup) {
  selectedBackup.value = backup
  showDeleteModal.value = true
}

function closeDeleteModal() {
  showDeleteModal.value = false
  selectedBackup.value = null
}

async function executeDelete() {
  deleting.value = true
  clearStatus()
  try {
    const { data } = await api.delete(
      `${API_BASE}/${selectedBackup.value.filename}`
    )
    showStatus(data.message, 'success')
    closeDeleteModal()
    await loadBackups()
  } catch (err) {
    showStatus(
      err.response?.data?.detail || 'Error al eliminar el backup',
      'error'
    )
  } finally {
    deleting.value = false
  }
}

// ── Utilidades ───────────────────────────────────────────

function formatDate(isoString) {
  const d = new Date(isoString)
  return d.toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function showStatus(message, type = 'info') {
  statusMessage.value = message
  statusType.value = type
  if (type === 'success') {
    setTimeout(clearStatus, 8000)
  }
}

function clearStatus() {
  statusMessage.value = ''
}

// ── Inicialización ───────────────────────────────────────

onMounted(loadBackups)
</script>

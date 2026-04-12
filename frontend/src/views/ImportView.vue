<template>
  <div class="max-w-5xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-6">📥 Importar desde Excel</h1>

    <!-- Formulario de subida -->
    <div class="bg-white rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Subir fichero Excel</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Delegación</label>
          <select v-model="delegacion" class="w-full border rounded px-3 py-2">
            <option value="">Seleccionar...</option>
            <option value="Bata">Bata</option>
            <option value="Malabo">Malabo</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Fichero .xlsx</label>
          <input type="file" accept=".xlsx,.xls" @change="onFileSelected" ref="fileInput"
                 class="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <button @click="validateFile" :disabled="!canValidate || loading"
                  class="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
            {{ loading ? 'Validando...' : 'Validar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Informe de validación -->
    <div v-if="validation" class="bg-white rounded-lg shadow p-6 mb-6">
      <h2 class="text-lg font-semibold mb-4">Resultado de la validación</h2>

      <!-- Resumen -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div class="bg-gray-50 rounded p-3 text-center">
          <div class="text-2xl font-bold">{{ validation.total_rows }}</div>
          <div class="text-sm text-gray-600">Total filas</div>
        </div>
        <div class="bg-green-50 rounded p-3 text-center">
          <div class="text-2xl font-bold text-green-700">{{ validation.valid_rows }}</div>
          <div class="text-sm text-gray-600">Válidas</div>
        </div>
        <div class="bg-red-50 rounded p-3 text-center">
          <div class="text-2xl font-bold text-red-700">{{ validation.error_rows }}</div>
          <div class="text-sm text-gray-600">Con errores</div>
        </div>
        <div class="bg-yellow-50 rounded p-3 text-center">
          <div class="text-2xl font-bold text-yellow-700">{{ validation.duplicate_rows }}</div>
          <div class="text-sm text-gray-600">Duplicadas</div>
        </div>
      </div>

      <!-- Proyectos/obras a crear -->
      <div v-if="validation.projects_to_create.length > 0" class="mb-4">
        <p class="text-sm font-medium text-blue-700 mb-1">
          Proyectos que se crearán automáticamente: {{ validation.projects_to_create.join(', ') }}
        </p>
      </div>
      <div v-if="validation.works_to_create.length > 0" class="mb-4">
        <p class="text-sm font-medium text-blue-700 mb-1">
          Obras que se crearán automáticamente: {{ validation.works_to_create.join(', ') }}
        </p>
      </div>

      <!-- Tabla de errores -->
      <div v-if="validation.errors.length > 0" class="mb-4">
        <h3 class="font-medium text-red-700 mb-2">Errores encontrados</h3>
        <div class="overflow-x-auto max-h-80 overflow-y-auto">
          <table class="w-full text-sm border">
            <thead class="bg-red-50 sticky top-0">
              <tr>
                <th class="border px-3 py-2 text-left">Fila</th>
                <th class="border px-3 py-2 text-left">Campo</th>
                <th class="border px-3 py-2 text-left">Error</th>
                <th class="border px-3 py-2 text-left">Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(err, idx) in validation.errors" :key="idx" class="hover:bg-red-25">
                <td class="border px-3 py-1">{{ err.row }}</td>
                <td class="border px-3 py-1">{{ err.field }}</td>
                <td class="border px-3 py-1">{{ err.error }}</td>
                <td class="border px-3 py-1 text-gray-500">{{ err.value || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Botón de importar -->
      <div v-if="validation.can_import" class="mt-4">
        <button @click="executeImport" :disabled="importing"
                class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:opacity-50">
          {{ importing ? 'Importando...' : 'Confirmar importación' }}
        </button>
      </div>
      <div v-else class="mt-4 text-red-600 text-sm">
        Corrija los errores antes de importar.
      </div>
    </div>

    <!-- Resultado de importación -->
    <div v-if="importResult" class="bg-green-50 border border-green-300 rounded-lg p-6 mb-6">
      <h2 class="text-lg font-semibold text-green-800 mb-3">✅ Importación completada</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div><strong>{{ importResult.rows_imported }}</strong> filas importadas</div>
        <div><strong>{{ importResult.rows_skipped }}</strong> duplicados omitidos</div>
        <div><strong>{{ importResult.projects_created }}</strong> proyectos creados</div>
        <div><strong>{{ importResult.works_created }}</strong> obras creadas</div>
      </div>
    </div>

    <!-- Historial de importaciones -->
    <div class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">Historial de importaciones</h2>
      <div v-if="history.length === 0" class="text-gray-500 text-sm">
        No se han realizado importaciones todavía.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm border">
          <thead class="bg-gray-50">
            <tr>
              <th class="border px-3 py-2 text-left">Fecha</th>
              <th class="border px-3 py-2 text-left">Fichero</th>
              <th class="border px-3 py-2 text-left">Delegación</th>
              <th class="border px-3 py-2 text-right">Importadas</th>
              <th class="border px-3 py-2 text-right">Omitidas</th>
              <th class="border px-3 py-2 text-right">Proy. creados</th>
              <th class="border px-3 py-2 text-right">Obras creadas</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in history" :key="h.id" class="hover:bg-gray-50">
              <td class="border px-3 py-1">{{ formatDate(h.imported_at) }}</td>
              <td class="border px-3 py-1">{{ h.filename }}</td>
              <td class="border px-3 py-1">{{ h.delegacion }}</td>
              <td class="border px-3 py-1 text-right">{{ h.rows_imported }}</td>
              <td class="border px-3 py-1 text-right">{{ h.rows_skipped }}</td>
              <td class="border px-3 py-1 text-right">{{ h.projects_created }}</td>
              <td class="border px-3 py-1 text-right">{{ h.works_created }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import importService from '@/services/importService'

const delegacion = ref('')
const selectedFile = ref(null)
const loading = ref(false)
const importing = ref(false)
const validation = ref(null)
const importResult = ref(null)
const history = ref([])
const fileInput = ref(null)

const canValidate = computed(() => delegacion.value && selectedFile.value)

function onFileSelected(event) {
  selectedFile.value = event.target.files[0] || null
  validation.value = null
  importResult.value = null
}

async function validateFile() {
  if (!canValidate.value) return
  loading.value = true
  validation.value = null
  importResult.value = null
  try {
    const { data } = await importService.validate(selectedFile.value, delegacion.value)
    validation.value = data
  } catch (err) {
    alert('Error al validar: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function executeImport() {
  if (!selectedFile.value || !delegacion.value) return
  importing.value = true
  try {
    const { data } = await importService.execute(selectedFile.value, delegacion.value)
    importResult.value = data
    validation.value = null
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await loadHistory()
  } catch (err) {
    alert('Error al importar: ' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}

async function loadHistory() {
  try {
    const { data } = await importService.getHistory()
    history.value = data
  } catch { /* silenciar si no hay historial */ }
}

function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleString('es-ES', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

onMounted(() => { loadHistory() })
</script>

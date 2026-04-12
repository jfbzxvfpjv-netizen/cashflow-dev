<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-semibold text-gray-900">Categorías y Subcategorías</h1>
      <button
        v-if="isAdmin"
        class="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
        @click="openCategoryModal(null)"
      >
        + Nueva categoría
      </button>
    </div>

    <div class="flex gap-2 mb-4">
      <button
        v-for="t in typeFilters"
        :key="t.value"
        :class="[
          'px-3 py-1.5 text-sm rounded-md border',
          typeFilter === t.value
            ? 'bg-blue-50 border-blue-300 text-blue-700'
            : 'border-gray-300 text-gray-600 hover:bg-gray-50'
        ]"
        @click="typeFilter = t.value; loadCategories()"
      >
        {{ t.label }}
      </button>
    </div>

    <div class="space-y-2">
      <div
        v-for="cat in categories"
        :key="cat.id"
        class="bg-white border border-gray-200 rounded-lg overflow-hidden"
      >
        <div
          class="flex items-center px-4 py-3 cursor-pointer hover:bg-gray-50"
          @click="toggleExpand(cat.id)"
        >
          <span class="text-sm mr-2 transition-transform" :class="expandedId === cat.id ? 'rotate-90' : ''">▶</span>
          <span class="font-medium text-sm flex-1">{{ cat.name }}</span>
          <span :class="typeBadgeClass(cat.type)" class="px-2 py-0.5 text-xs rounded-full mr-3">
            {{ typeLabel(cat.type) }}
          </span>
          <span v-if="!cat.requires_attachment" class="text-xs text-orange-500 mr-3">
            Sin adjunto obligatorio
          </span>
          <span :class="cat.active ? 'text-green-500' : 'text-red-400'" class="text-xs mr-3">
            {{ cat.active ? 'Activa' : 'Inactiva' }}
          </span>
          <button v-if="isAdmin" class="text-blue-600 hover:text-blue-800 text-sm mr-2" @click.stop="openCategoryModal(cat)">Editar</button>
          <button v-if="isAdmin" class="text-sm mr-2"
            :class="cat.active ? 'text-red-500 hover:text-red-700' : 'text-green-500 hover:text-green-700'"
            @click.stop="toggleCategory(cat)">
            {{ cat.active ? 'Desactivar' : 'Activar' }}
          </button>
          <button v-if="isAdmin" class="text-sm text-red-700 hover:text-red-900 font-medium" @click.stop="deleteCategory(cat)">Eliminar</button>
        </div>

        <div v-if="expandedId === cat.id" class="border-t border-gray-100 bg-gray-50 px-6 py-3">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-medium text-gray-500 uppercase">Subcategorías</span>
            <button v-if="isAdmin" class="text-xs text-green-600 hover:text-green-800" @click="openSubcategoryModal(cat.id, null)">+ Añadir</button>
          </div>
          <div v-if="subcategories[cat.id]?.length" class="space-y-1">
            <div
              v-for="sub in subcategories[cat.id]"
              :key="sub.id"
              class="flex items-center justify-between px-3 py-1.5 bg-white rounded border border-gray-100"
            >
              <span class="text-sm" :class="{ 'text-gray-400 line-through': !sub.active }">{{ sub.name }}</span>
              <div v-if="isAdmin" class="flex gap-3">
                <button class="text-xs text-blue-600 hover:text-blue-800" @click="openSubcategoryModal(cat.id, sub)">Editar</button>
                <button class="text-xs"
                  :class="sub.active ? 'text-red-500 hover:text-red-700' : 'text-green-500 hover:text-green-700'"
                  @click="toggleSubcategory(cat.id, sub)">
                  {{ sub.active ? 'Desactivar' : 'Activar' }}
                </button>
                <button class="text-xs text-red-700 hover:text-red-900 font-medium" @click="deleteSubcategory(cat.id, sub)">Eliminar</button>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-gray-400 py-2">Sin subcategorías</p>
        </div>
      </div>

      <p v-if="!categories.length" class="text-center text-gray-400 py-8">No se encontraron categorías</p>
    </div>

    <!-- Modal de categoría -->
    <Teleport to="body">
      <div v-if="showCatModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showCatModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">{{ editingCategory ? 'Editar' : 'Nueva' }} categoría</h2>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input v-model="catForm.name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select v-model="catForm.type" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="expense">Gasto</option>
                <option value="income">Ingreso</option>
                <option value="both">Ambos</option>
              </select>
            </div>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="catForm.requires_attachment" type="checkbox" class="rounded border-gray-300" />
              Adjunto obligatorio
            </label>
          </div>
          <p v-if="catError" class="text-sm text-red-600 mt-2">{{ catError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showCatModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md" @click="saveCategory">Guardar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal de subcategoría -->
    <Teleport to="body">
      <div v-if="showSubModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showSubModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
          <h2 class="text-lg font-semibold mb-4">{{ editingSubcategory ? 'Editar' : 'Nueva' }} subcategoría</h2>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
            <input v-model="subForm.name" type="text" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <p v-if="subError" class="text-sm text-red-600 mt-2">{{ subError }}</p>
          <div class="flex justify-end gap-3 mt-4">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showSubModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md" @click="saveSubcategory">Guardar</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal de confirmación de borrado -->
    <Teleport to="body">
      <div v-if="showDeleteModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="showDeleteModal = false">
        <div class="bg-white rounded-lg shadow-xl w-full max-w-sm mx-4 p-6">
          <h2 class="text-lg font-semibold text-red-700 mb-2">Confirmar eliminación</h2>
          <p class="text-sm text-gray-600 mb-1">¿Eliminar permanentemente?</p>
          <p class="text-sm font-semibold text-gray-900 mb-4">{{ deleteTarget?.name }}</p>
          <p v-if="deleteError" class="text-sm text-red-600 mb-3 bg-red-50 p-2 rounded">{{ deleteError }}</p>
          <div class="flex justify-end gap-3">
            <button class="px-4 py-2 text-sm text-gray-600" @click="showDeleteModal = false">Cancelar</button>
            <button class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700" @click="confirmDelete">Eliminar</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { categoriesApi, subcategoriesApi } from '@/api/catalogs'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const typeFilters = [
  { value: null, label: 'Todas' },
  { value: 'expense', label: 'Gasto' },
  { value: 'income', label: 'Ingreso' },
  { value: 'both', label: 'Ambos' },
]
const typeFilter = ref(null)
const categories = ref([])
const subcategories = ref({})
const expandedId = ref(null)

const showCatModal = ref(false)
const editingCategory = ref(null)
const catForm = ref({ name: '', type: 'expense', requires_attachment: true })
const catError = ref('')

const showSubModal = ref(false)
const editingSubcategory = ref(null)
const subCategoryId = ref(null)
const subForm = ref({ name: '' })
const subError = ref('')

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteType = ref('')
const deleteCategoryId = ref(null)
const deleteError = ref('')

function typeLabel(type) {
  return { expense: 'Gasto', income: 'Ingreso', both: 'Ambos' }[type] || type
}

function typeBadgeClass(type) {
  return { expense: 'bg-red-50 text-red-700', income: 'bg-green-50 text-green-700', both: 'bg-purple-50 text-purple-700' }[type] || 'bg-gray-100 text-gray-700'
}

async function loadCategories() {
  try {
    const params = { active_only: false, page_size: 100 }
    if (typeFilter.value) params.type = typeFilter.value
    const { data } = await categoriesApi.list(params)
    categories.value = data.items
  } catch (err) {
    console.error('Error:', err)
  }
}

async function toggleExpand(catId) {
  if (expandedId.value === catId) { expandedId.value = null; return }
  expandedId.value = catId
  if (!subcategories.value[catId]) await loadSubcategories(catId)
}

async function loadSubcategories(catId) {
  try {
    const { data } = await subcategoriesApi.list(catId, { active_only: false })
    subcategories.value[catId] = data
  } catch (err) {
    subcategories.value[catId] = []
  }
}

function openCategoryModal(cat) {
  editingCategory.value = cat
  catForm.value = cat
    ? { name: cat.name, type: cat.type, requires_attachment: cat.requires_attachment }
    : { name: '', type: 'expense', requires_attachment: true }
  catError.value = ''
  showCatModal.value = true
}

async function saveCategory() {
  catError.value = ''
  try {
    if (editingCategory.value) await categoriesApi.update(editingCategory.value.id, catForm.value)
    else await categoriesApi.create(catForm.value)
    showCatModal.value = false
    await loadCategories()
  } catch (err) {
    catError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function toggleCategory(cat) {
  try {
    await categoriesApi.update(cat.id, { active: !cat.active })
    await loadCategories()
  } catch (err) { console.error('Error:', err) }
}

function openSubcategoryModal(categoryId, sub) {
  subCategoryId.value = categoryId
  editingSubcategory.value = sub
  subForm.value = sub ? { name: sub.name } : { name: '' }
  subError.value = ''
  showSubModal.value = true
}

async function saveSubcategory() {
  subError.value = ''
  try {
    if (editingSubcategory.value) await subcategoriesApi.update(editingSubcategory.value.id, subForm.value)
    else await subcategoriesApi.create({ category_id: subCategoryId.value, name: subForm.value.name })
    showSubModal.value = false
    await loadSubcategories(subCategoryId.value)
  } catch (err) {
    subError.value = err.response?.data?.detail || 'Error al guardar'
  }
}

async function toggleSubcategory(categoryId, sub) {
  try {
    await subcategoriesApi.update(sub.id, { active: !sub.active })
    await loadSubcategories(categoryId)
  } catch (err) { console.error('Error:', err) }
}

function deleteCategory(cat) {
  deleteTarget.value = cat
  deleteType.value = 'category'
  deleteError.value = ''
  showDeleteModal.value = true
}

function deleteSubcategory(categoryId, sub) {
  deleteTarget.value = sub
  deleteType.value = 'subcategory'
  deleteCategoryId.value = categoryId
  deleteError.value = ''
  showDeleteModal.value = true
}

async function confirmDelete() {
  deleteError.value = ''
  try {
    if (deleteType.value === 'category') {
      await categoriesApi.delete(deleteTarget.value.id)
      showDeleteModal.value = false
      await loadCategories()
    } else {
      await subcategoriesApi.delete(deleteTarget.value.id)
      showDeleteModal.value = false
      await loadSubcategories(deleteCategoryId.value)
    }
  } catch (err) {
    deleteError.value = err.response?.data?.detail || 'No se puede eliminar'
  }
}

onMounted(loadCategories)
</script>

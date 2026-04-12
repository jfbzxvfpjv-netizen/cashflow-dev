#!/usr/bin/env python3
"""
Parche — Añade filtros de categoría, subcategoría y contraparte a TransactionsView.vue
Ejecutar desde la raíz del proyecto: python3 parche_filtros_transacciones.py
"""

import os, sys

VUE_PATH = "frontend/src/views/TransactionsView.vue"

if not os.path.exists(VUE_PATH):
    print(f"❌ No se encuentra {VUE_PATH}. Ejecuta este script desde la raíz del proyecto.")
    sys.exit(1)

content = open(VUE_PATH, "r", encoding="utf-8").read()

# ═══════════════════════════════════════════════════════════════
# 1. TEMPLATE — Sustituir bloque de filtros
# ═══════════════════════════════════════════════════════════════

OLD_FILTERS_TEMPLATE = '''    <!-- Filtros -->
    <div class="bg-white rounded shadow p-3 mb-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 text-sm">
      <input v-model="filters.date_start" type="date" class="border rounded px-2 py-1" placeholder="Desde" />
      <input v-model="filters.date_end" type="date" class="border rounded px-2 py-1" placeholder="Hasta" />
      <select v-model="filters.type" class="border rounded px-2 py-1">
        <option value="">Todos los tipos</option>
        <option value="income">Ingreso</option>
        <option value="expense">Egreso</option>
      </select>
      <select v-model="filters.approval_status" class="border rounded px-2 py-1">
        <option value="">Todas</option>
        <option value="approved">Aprobadas</option>
        <option value="pending_approval">Pendientes</option>
        <option value="rejected">Rechazadas</option>
      </select>
      <input v-model="filters.concept" type="text" class="border rounded px-2 py-1" placeholder="Buscar concepto..." />
      <button @click="loadTransactions" class="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1">Filtrar</button>
    </div>'''

NEW_FILTERS_TEMPLATE = '''    <!-- Filtros — Categoría, subcategoría y contraparte añadidos -->
    <div class="bg-white rounded shadow p-3 mb-4 text-sm">
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <input v-model="filters.date_start" type="date" class="border rounded px-2 py-1" placeholder="Desde" />
        <input v-model="filters.date_end" type="date" class="border rounded px-2 py-1" placeholder="Hasta" />
        <select v-model="filters.type" class="border rounded px-2 py-1">
          <option value="">Todos los tipos</option>
          <option value="income">Ingreso</option>
          <option value="expense">Egreso</option>
        </select>
        <select v-model="filters.category_id" class="border rounded px-2 py-1" @change="onCategoryChange">
          <option value="">Todas las categorías</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="filters.subcategory_id" class="border rounded px-2 py-1" :disabled="!filters.category_id">
          <option value="">Todas las subcategorías</option>
          <option v-for="sc in filteredSubcategories" :key="sc.id" :value="sc.id">{{ sc.name }}</option>
        </select>
        <select v-model="filters.supplier_id" class="border rounded px-2 py-1">
          <option value="">Todas las contrapartes</option>
          <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mt-2">
        <select v-model="filters.approval_status" class="border rounded px-2 py-1">
          <option value="">Todos los estados</option>
          <option value="approved">Aprobadas</option>
          <option value="pending_approval">Pendientes</option>
          <option value="rejected">Rechazadas</option>
        </select>
        <input v-model="filters.concept" type="text" class="border rounded px-2 py-1" placeholder="Buscar concepto..." />
        <div></div>
        <div></div>
        <button @click="resetFilters" class="bg-gray-100 hover:bg-gray-200 border rounded px-3 py-1 text-gray-500">Limpiar</button>
        <button @click="loadTransactions" class="bg-gray-200 hover:bg-gray-300 rounded px-3 py-1 font-medium">Filtrar</button>
      </div>
    </div>'''

if OLD_FILTERS_TEMPLATE not in content:
    print("❌ No se encontró el bloque de filtros original en el template.")
    print("   Verifica que TransactionsView.vue no haya sido modificado manualmente.")
    sys.exit(1)

content = content.replace(OLD_FILTERS_TEMPLATE, NEW_FILTERS_TEMPLATE)
print("  ✓ Template: bloque de filtros ampliado")

# ═══════════════════════════════════════════════════════════════
# 2. SCRIPT — Ampliar filters ref y añadir catálogos
# ═══════════════════════════════════════════════════════════════

OLD_SCRIPT_FILTERS = """const transactions = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const filters = ref({
  date_start: '', date_end: '', type: '', approval_status: '', concept: ''
})"""

NEW_SCRIPT_FILTERS = """const transactions = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const filters = ref({
  date_start: '', date_end: '', type: '', approval_status: '', concept: '',
  category_id: '', subcategory_id: '', supplier_id: ''
})

// --- Catálogos para selectores de filtro ---
const categories = ref([])
const subcategories = ref([])
const suppliers = ref([])

const filteredSubcategories = computed(() => {
  if (!filters.value.category_id) return []
  const catId = Number(filters.value.category_id)
  return subcategories.value.filter(sc => sc.category_id === catId)
})

function onCategoryChange() {
  filters.value.subcategory_id = ''
}

function resetFilters() {
  filters.value = {
    date_start: '', date_end: '', type: '', approval_status: '', concept: '',
    category_id: '', subcategory_id: '', supplier_id: ''
  }
  loadTransactions()
}

async function loadFilterCatalogs() {
  try {
    const axios = transactionService.axiosInstance || (await import('@/services/api')).default
    const [catRes, subRes, supRes] = await Promise.all([
      axios.get('/api/v1/categories', { params: { page_size: 500 } }),
      axios.get('/api/v1/subcategories', { params: { page_size: 500 } }),
      axios.get('/api/v1/suppliers', { params: { page_size: 500 } })
    ])
    categories.value = catRes.data.items || catRes.data || []
    subcategories.value = subRes.data.items || subRes.data || []
    suppliers.value = supRes.data.items || supRes.data || []
  } catch (e) {
    console.error('Error cargando catálogos de filtros:', e)
  }
}"""

if OLD_SCRIPT_FILTERS not in content:
    print("❌ No se encontró el bloque de filters en el script setup.")
    sys.exit(1)

content = content.replace(OLD_SCRIPT_FILTERS, NEW_SCRIPT_FILTERS)
print("  ✓ Script: filters ampliados + catálogos + cascada categoría→subcategoría")

# ═══════════════════════════════════════════════════════════════
# 3. SCRIPT — Añadir computed al import si falta
# ═══════════════════════════════════════════════════════════════

if "computed" not in content.split("<script")[1].split("from 'vue'")[0]:
    content = content.replace(
        "import { ref, onMounted",
        "import { ref, computed, onMounted"
    )
    print("  ✓ Import: añadido 'computed' al import de vue")
else:
    print("  · Import: 'computed' ya presente")

# ═══════════════════════════════════════════════════════════════
# 4. SCRIPT — Añadir loadFilterCatalogs() al onMounted
# ═══════════════════════════════════════════════════════════════

OLD_MOUNTED = "onMounted(() => loadTransactions())"
NEW_MOUNTED = """onMounted(() => {
  loadFilterCatalogs()
  loadTransactions()
})"""

if OLD_MOUNTED in content:
    content = content.replace(OLD_MOUNTED, NEW_MOUNTED)
    print("  ✓ onMounted: añadida carga de catálogos")
else:
    print("  · onMounted: ya modificado o formato diferente — verificar manualmente")

# ═══════════════════════════════════════════════════════════════
# Guardar
# ═══════════════════════════════════════════════════════════════

open(VUE_PATH, "w", encoding="utf-8").write(content)
print(f"\n✅ Parche aplicado correctamente a {VUE_PATH}")
print("   Reconstruir frontend: docker compose up -d --build frontend")

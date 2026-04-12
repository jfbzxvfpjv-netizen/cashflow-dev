#!/usr/bin/env python3
"""
Parche 3 — Selector combinado de contrapartes (proveedores + empleados).
Ejecutar desde la raíz del proyecto: python3 parche3_contrapartes.py
"""

import os, sys

# ═══════════════════════════════════════════════════════════════
# 1. transactionService.js — Añadir getEmployees si no existe
# ═══════════════════════════════════════════════════════════════

SVC_PATH = "frontend/src/services/transactionService.js"
if not os.path.exists(SVC_PATH):
    print(f"❌ No se encuentra {SVC_PATH}")
    sys.exit(1)

svc = open(SVC_PATH, "r", encoding="utf-8").read()

if "getEmployees" not in svc:
    svc = svc.replace(
        "  getSuppliers(params = {}) {\n    return api.get('/suppliers', { params })\n  },",
        "  getSuppliers(params = {}) {\n    return api.get('/suppliers', { params })\n  },\n  getEmployees(params = {}) {\n    return api.get('/employees', { params })\n  },"
    )
    open(SVC_PATH, "w", encoding="utf-8").write(svc)
    print("  ✓ transactionService.js: añadido getEmployees")
else:
    print("  · transactionService.js: getEmployees ya existe")

# ═══════════════════════════════════════════════════════════════
# 2. TransactionsView.vue — Template: selector combinado
# ═══════════════════════════════════════════════════════════════

VUE_PATH = "frontend/src/views/TransactionsView.vue"
if not os.path.exists(VUE_PATH):
    print(f"❌ No se encuentra {VUE_PATH}")
    sys.exit(1)

vue = open(VUE_PATH, "r", encoding="utf-8").read()

OLD_SELECT = """        <select v-model="filters.supplier_id" class="border rounded px-2 py-1">
          <option value="">Todas las contrapartes</option>
          <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>"""

NEW_SELECT = """        <select v-model="counterpartyFilter" class="border rounded px-2 py-1" @change="onCounterpartyChange">
          <option value="">Todas las contrapartes</option>
          <optgroup label="Proveedores">
            <option v-for="s in suppliers" :key="'s'+s.id" :value="'supplier_'+s.id">{{ s.name }}</option>
          </optgroup>
          <optgroup label="Empleados">
            <option v-for="e in employees" :key="'e'+e.id" :value="'employee_'+e.id">{{ e.full_name }}</option>
          </optgroup>
        </select>"""

if OLD_SELECT in vue:
    vue = vue.replace(OLD_SELECT, NEW_SELECT)
    print("  ✓ Template: selector combinado con optgroup")
else:
    print("  ✗ No se encontró el selector de contrapartes en el template")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# 3. Script — Añadir employees ref y lógica de contraparte
# ═══════════════════════════════════════════════════════════════

# Añadir employees ref junto a suppliers
OLD_REFS = "const suppliers = ref([])"
NEW_REFS = "const suppliers = ref([])\nconst employees = ref([])\nconst counterpartyFilter = ref('')"

if OLD_REFS in vue:
    vue = vue.replace(OLD_REFS, NEW_REFS)
    print("  ✓ Script: añadidos employees ref y counterpartyFilter")
else:
    print("  ✗ No se encontró 'const suppliers = ref([])'")

# Añadir función onCounterpartyChange después de onCategoryChange
OLD_CAT_CHANGE = """function onCategoryChange() {
  filters.value.subcategory_id = ''
  if (filters.value.category_id) {
    loadSubcategories(Number(filters.value.category_id))
  } else {
    subcategories.value = []
  }
}"""

NEW_CAT_CHANGE = """function onCategoryChange() {
  filters.value.subcategory_id = ''
  if (filters.value.category_id) {
    loadSubcategories(Number(filters.value.category_id))
  } else {
    subcategories.value = []
  }
}

function onCounterpartyChange() {
  const val = counterpartyFilter.value
  filters.value.supplier_id = ''
  filters.value.employee_id = ''
  if (val.startsWith('supplier_')) {
    filters.value.supplier_id = val.replace('supplier_', '')
  } else if (val.startsWith('employee_')) {
    filters.value.employee_id = val.replace('employee_', '')
  }
}"""

if OLD_CAT_CHANGE in vue:
    vue = vue.replace(OLD_CAT_CHANGE, NEW_CAT_CHANGE)
    print("  ✓ Script: añadida función onCounterpartyChange")
else:
    print("  ✗ No se encontró onCategoryChange")

# Añadir employee_id al objeto filters
OLD_FILTERS_OBJ = "category_id: '', subcategory_id: '', supplier_id: ''"
NEW_FILTERS_OBJ = "category_id: '', subcategory_id: '', supplier_id: '', employee_id: ''"

# Hay dos ocurrencias (declaración inicial y resetFilters), reemplazar ambas
vue = vue.replace(OLD_FILTERS_OBJ, NEW_FILTERS_OBJ)
print("  ✓ Script: employee_id añadido a filters")

# Añadir reseteo de counterpartyFilter en resetFilters
OLD_RESET = """function resetFilters() {
  filters.value = {
    date_start: '', date_end: '', type: '', approval_status: '', concept: '',
    category_id: '', subcategory_id: '', supplier_id: '', employee_id: ''
  }
  loadTransactions()
}"""

NEW_RESET = """function resetFilters() {
  filters.value = {
    date_start: '', date_end: '', type: '', approval_status: '', concept: '',
    category_id: '', subcategory_id: '', supplier_id: '', employee_id: ''
  }
  counterpartyFilter.value = ''
  subcategories.value = []
  loadTransactions()
}"""

if OLD_RESET in vue:
    vue = vue.replace(OLD_RESET, NEW_RESET)
    print("  ✓ Script: resetFilters limpia counterpartyFilter")
else:
    print("  · resetFilters: formato diferente, verificar manualmente")

# Añadir carga de empleados en loadFilterCatalogs
OLD_LOAD = """async function loadFilterCatalogs() {
  try {
    const [catRes, supRes] = await Promise.all([
      transactionService.getCategories(),
      transactionService.getSuppliers()
    ])
    categories.value = catRes.data.items || catRes.data || []
    suppliers.value = supRes.data.items || supRes.data || []
  } catch (e) {
    console.error('Error cargando catálogos de filtros:', e)
  }
}"""

NEW_LOAD = """async function loadFilterCatalogs() {
  try {
    const [catRes, supRes, empRes] = await Promise.all([
      transactionService.getCategories(),
      transactionService.getSuppliers(),
      transactionService.getEmployees()
    ])
    categories.value = catRes.data.items || catRes.data || []
    suppliers.value = supRes.data.items || supRes.data || []
    employees.value = empRes.data.items || empRes.data || []
  } catch (e) {
    console.error('Error cargando catálogos de filtros:', e)
  }
}"""

if OLD_LOAD in vue:
    vue = vue.replace(OLD_LOAD, NEW_LOAD)
    print("  ✓ Script: loadFilterCatalogs carga empleados")
else:
    print("  ✗ No se encontró loadFilterCatalogs")

# ═══════════════════════════════════════════════════════════════
# Guardar
# ═══════════════════════════════════════════════════════════════

open(VUE_PATH, "w", encoding="utf-8").write(vue)
print(f"\n✅ Parche 3 aplicado correctamente")
print("   Ejecuta: docker compose up -d --build frontend")

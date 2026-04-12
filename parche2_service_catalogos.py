#!/usr/bin/env python3
"""
Parche 2 — Añade métodos getCategories, getSubcategories y getSuppliers
a transactionService.js para alimentar los selectores de filtro.
Ejecutar desde la raíz del proyecto: python3 parche2_service_catalogos.py
"""

import os, sys

SVC_PATH = "frontend/src/services/transactionService.js"

if not os.path.exists(SVC_PATH):
    print(f"❌ No se encuentra {SVC_PATH}. Ejecuta este script desde la raíz del proyecto.")
    sys.exit(1)

content = open(SVC_PATH, "r", encoding="utf-8").read()

# ═══════════════════════════════════════════════════════════════
# Verificar que no se haya aplicado ya
# ═══════════════════════════════════════════════════════════════

if "getCategories" in content:
    print("· El parche ya fue aplicado — transactionService.js ya tiene getCategories.")
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════
# Añadir métodos de catálogos antes del cierre del export
# ═══════════════════════════════════════════════════════════════

NEW_METHODS = """
  // --- Catálogos para filtros (parche filtros M6) ---
  getCategories(params = {}) {
    return api.get('/categories', { params: { page_size: 500, ...params } })
  },
  getSubcategories(params = {}) {
    return api.get('/subcategories', { params: { page_size: 500, ...params } })
  },
  getSuppliers(params = {}) {
    return api.get('/suppliers', { params: { page_size: 500, ...params } })
  },
"""

# Buscar el cierre del objeto export default { ... }
# El patrón es: verifySingle(...) { ... }\n}
ANCHOR = "  verifySingle(id) {\n    return api.get(`/integrity/verify/${id}`)\n  }\n}"

if ANCHOR in content:
    content = content.replace(
        ANCHOR,
        "  verifySingle(id) {\n    return api.get(`/integrity/verify/${id}`)\n  },\n" + NEW_METHODS + "}"
    )
    print("  ✓ Añadidos getCategories, getSubcategories y getSuppliers")
else:
    # Alternativa: buscar el último } del fichero
    last_brace = content.rfind("}")
    if last_brace == -1:
        print("❌ No se encontró el cierre del export en transactionService.js")
        sys.exit(1)
    content = content[:last_brace] + NEW_METHODS + "}\n"
    print("  ✓ Añadidos métodos de catálogos (inserción al final del export)")

# ═══════════════════════════════════════════════════════════════
# Actualizar loadFilterCatalogs en TransactionsView.vue
# para usar transactionService en vez del import dinámico
# ═══════════════════════════════════════════════════════════════

VUE_PATH = "frontend/src/views/TransactionsView.vue"

if os.path.exists(VUE_PATH):
    vue = open(VUE_PATH, "r", encoding="utf-8").read()

    OLD_LOAD = """async function loadFilterCatalogs() {
  try {
    const axios = transactionService.axiosInstance || (await import('@/services/api')).default
    const [catRes, subRes, supRes] = await Promise.all([
      axios.get('/api/v1/categories', { params: { page_size: 500 } }),
      axios.get('/api/v1/subcategories', { params: { page_size: 500 } }),
      axios.get('/api/v1/suppliers', { params: { page_size: 500 } })
    ])"""

    NEW_LOAD = """async function loadFilterCatalogs() {
  try {
    const [catRes, subRes, supRes] = await Promise.all([
      transactionService.getCategories(),
      transactionService.getSubcategories(),
      transactionService.getSuppliers()
    ])"""

    if OLD_LOAD in vue:
        vue = vue.replace(OLD_LOAD, NEW_LOAD)
        open(VUE_PATH, "w", encoding="utf-8").write(vue)
        print(f"  ✓ {VUE_PATH}: loadFilterCatalogs simplificado con transactionService")
    else:
        print(f"  · {VUE_PATH}: loadFilterCatalogs no coincide — verificar manualmente")
else:
    print(f"  · {VUE_PATH} no encontrado — aplica el parche 1 primero")

# ═══════════════════════════════════════════════════════════════
# Guardar transactionService.js
# ═══════════════════════════════════════════════════════════════

open(SVC_PATH, "w", encoding="utf-8").write(content)
print(f"\n✅ Parche 2 aplicado correctamente")
print("   Reconstruir frontend: docker compose up -d --build frontend")

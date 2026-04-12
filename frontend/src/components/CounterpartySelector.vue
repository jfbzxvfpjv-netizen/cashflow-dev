<!--
  Módulo 6 — CounterpartySelector.vue
  Selector mixto de contraparte: permite elegir del catálogo (proveedor, empleado
  o socio) o bien introducir texto libre con validación de nombre completo.
-->
<template>
  <div class="space-y-2">
    <div class="flex gap-2">
      <label class="flex items-center gap-1 text-sm">
        <input type="radio" v-model="mode" value="catalog" /> Catálogo
      </label>
      <label class="flex items-center gap-1 text-sm">
        <input type="radio" v-model="mode" value="free" /> Texto libre
      </label>
    </div>

    <div v-if="mode === 'catalog'" class="grid grid-cols-1 sm:grid-cols-3 gap-2">
      <div>
        <label class="block text-xs text-gray-600 mb-1">Proveedor</label>
        <select v-model="supplierId" class="w-full border rounded px-2 py-1.5 text-sm">
          <option :value="null">— Ninguno —</option>
          <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-600 mb-1">Empleado</label>
        <select v-model="employeeId" class="w-full border rounded px-2 py-1.5 text-sm">
          <option :value="null">— Ninguno —</option>
          <option v-for="e in employees" :key="e.id" :value="e.id">{{ e.full_name }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs text-gray-600 mb-1">Socio</label>
        <select v-model="partnerId" class="w-full border rounded px-2 py-1.5 text-sm">
          <option :value="null">— Ninguno —</option>
          <option v-for="p in partners" :key="p.id" :value="p.id">{{ p.full_name }}</option>
        </select>
      </div>
    </div>

    <div v-else>
      <label class="block text-xs text-gray-600 mb-1">Nombre completo (mínimo nombre y apellido)</label>
      <input v-model="freeText" type="text" placeholder="Juan Pérez"
             class="w-full border rounded px-2 py-1.5 text-sm" />
      <p v-if="freeText && freeText.trim().split(/\s+/).length < 2"
         class="text-xs text-red-500 mt-1">Introduzca al menos nombre y apellido</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'

const props = defineProps({
  initialSupplierId: { type: Number, default: null },
  initialEmployeeId: { type: Number, default: null },
  initialPartnerId: { type: Number, default: null },
  initialFreeText: { type: String, default: '' }
})
const emit = defineEmits(['update'])

const mode = ref(props.initialFreeText ? 'free' : 'catalog')
const supplierId = ref(props.initialSupplierId)
const employeeId = ref(props.initialEmployeeId)
const partnerId = ref(props.initialPartnerId)
const freeText = ref(props.initialFreeText || '')

const suppliers = ref([])
const employees = ref([])
const partners = ref([])

async function loadCatalogs() {
  const [s, e, p] = await Promise.all([
    api.get('/suppliers'), api.get('/employees'), api.get('/partners')
  ])
  suppliers.value = Array.isArray(s.data) ? s.data : (s.data.items || [])
  employees.value = Array.isArray(e.data) ? e.data : (e.data.items || [])
  partners.value = Array.isArray(p.data) ? p.data : (p.data.items || [])
}

function emitValue() {
  if (mode.value === 'catalog') {
    emit('update', {
      supplier_id: supplierId.value,
      employee_id: employeeId.value,
      partner_id: partnerId.value,
      counterparty_free: null
    })
  } else {
    emit('update', {
      supplier_id: null, employee_id: null, partner_id: null,
      counterparty_free: freeText.value || null
    })
  }
}

watch([mode, supplierId, employeeId, partnerId, freeText], () => emitValue(), { deep: true })
onMounted(() => loadCatalogs())
</script>

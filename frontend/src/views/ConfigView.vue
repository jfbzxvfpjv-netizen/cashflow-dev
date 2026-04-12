<template>
  <div class="max-w-4xl mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Configuración del sistema</h1>

    <div v-if="configs.length" class="space-y-4 mb-8">
      <div v-for="c in configs" :key="c.id" class="bg-white rounded-lg shadow p-6 border-l-4"
        :class="c.delegacion === 'Bata' ? 'border-blue-500' : 'border-green-500'">
        <div class="flex justify-between items-start">
          <div><h2 class="text-lg font-semibold">{{ c.delegacion }}</h2><p class="text-gray-600 text-sm">{{ c.organization_name }}</p></div>
          <div class="text-right">
            <p class="text-2xl font-bold">{{ fmt(c.opening_balance) }} XAF</p>
            <p class="text-xs text-gray-500">Saldo inicial al {{ fmtDate(c.opening_balance_date) }}</p>
          </div>
        </div>
        <div v-if="balances[c.delegacion] !== undefined" class="mt-4 pt-4 border-t flex justify-between items-center">
          <span class="text-sm text-gray-600">Saldo actual</span>
          <span class="text-xl font-bold" :class="balances[c.delegacion] >= 0 ? 'text-green-600' : 'text-red-600'">{{ fmt(balances[c.delegacion]) }} XAF</span>
        </div>
        <button v-if="canEdit" @click="startEdit(c)" class="mt-4 text-sm text-blue-600 hover:text-blue-800">Modificar</button>
      </div>
    </div>

    <div v-if="canEdit" class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">{{ editing ? 'Modificar' : 'Nueva delegación' }}</h2>
      <form @submit.prevent="save" class="space-y-4">
        <select v-model="form.delegacion" :disabled="editing" class="w-full border rounded px-3 py-2">
          <option value="">— Delegación —</option>
          <option v-for="d in available" :key="d" :value="d">{{ d }}</option>
        </select>
        <input v-model="form.organization_name" class="w-full border rounded px-3 py-2" placeholder="Nombre de la organización" />
        <div class="grid grid-cols-2 gap-4">
          <input v-model.number="form.opening_balance" type="number" min="0" step="0.01" class="border rounded px-3 py-2" placeholder="Saldo inicial" />
          <input v-model="form.opening_balance_date" type="date" class="border rounded px-3 py-2" />
        </div>
        <div class="flex gap-3">
          <button type="submit" :disabled="saving" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
          <button v-if="editing" type="button" @click="editing=false" class="text-gray-600">Cancelar</button>
        </div>
        <p v-if="err" class="text-sm text-red-600">{{ err }}</p>
        <p v-if="ok" class="text-sm text-green-600">{{ ok }}</p>
      </form>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import configService from '@/services/configService'
const auth = useAuthStore()
const canEdit = computed(() => auth.user?.role === 'admin')
const configs = ref([]), balances = ref({}), editing = ref(false), saving = ref(false), err = ref(''), ok = ref('')
const form = ref({ delegacion: '', organization_name: '', opening_balance: 0, opening_balance_date: '' })
const available = computed(() => { const ex = configs.value.map(c => c.delegacion); return ['Bata','Malabo'].filter(d => editing.value ? d === form.value.delegacion : !ex.includes(d)) })
onMounted(load)
async function load() {
  const { data } = await configService.getAll(); configs.value = data
  for (const c of data) { try { const { data: b } = await configService.getBalance(c.delegacion); balances.value[c.delegacion] = b.current_balance } catch {} }
}
function startEdit(c) { editing.value = true; form.value = { ...c } }
async function save() {
  err.value = ''; ok.value = ''; saving.value = true
  try {
    if (editing.value) await configService.update(form.value.delegacion, form.value)
    else await configService.create(form.value)
    ok.value = 'Guardado'; editing.value = false; await load()
  } catch (e) { err.value = e.response?.data?.detail || 'Error' }
  finally { saving.value = false }
}
function fmt(n) { return new Intl.NumberFormat('es-GQ').format(n) }
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('es-GQ') : '—' }
</script>

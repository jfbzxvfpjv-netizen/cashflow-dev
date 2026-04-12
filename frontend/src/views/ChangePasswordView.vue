<template>
  <div class="max-w-sm">
    <h1 class="text-xl font-bold text-gray-800 mb-4">Cambiar Contraseña</h1>
    <div class="bg-white rounded-lg shadow p-6">
      <form @submit.prevent="handleSubmit">
        <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Contraseña actual</label>
          <input v-model="cur" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" /></div>
        <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Nueva contraseña</label>
          <input v-model="pwd" type="password" required minlength="8" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" />
          <p class="text-xs text-gray-400 mt-1">Mín 8 chars, mayúscula, número, especial.</p></div>
        <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Repetir nueva</label>
          <input v-model="pwd2" type="password" required class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" /></div>
        <div v-if="err" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{{ err }}</div>
        <div v-if="ok" class="mb-4 p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700">{{ ok }}</div>
        <button type="submit" :disabled="saving" class="w-full py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50">
          {{ saving ? 'Actualizando...' : 'Actualizar contraseña' }}</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { selfChangePassword } from '@/api/users'
const cur = ref(''); const pwd = ref(''); const pwd2 = ref('')
const saving = ref(false); const err = ref(''); const ok = ref('')
async function handleSubmit() {
  err.value = ''; ok.value = ''
  if (pwd.value !== pwd2.value) { err.value = 'Las contraseñas no coinciden.'; return }
  saving.value = true
  try { await selfChangePassword(cur.value, pwd.value); ok.value = 'Contraseña actualizada.'; cur.value=''; pwd.value=''; pwd2.value='' }
  catch (e) { err.value = e.response?.data?.detail || 'Error.' }
  finally { saving.value = false }
}
</script>

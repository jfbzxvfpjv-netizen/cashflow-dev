<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <router-link :to="{ name: 'users' }" class="text-gray-400 hover:text-gray-600">← Volver</router-link>
      <h1 class="text-xl font-bold text-gray-800">{{ isEditing ? 'Editar Usuario' : 'Nuevo Usuario' }}</h1>
    </div>
    <div class="max-w-lg">
      <div class="bg-white rounded-lg shadow p-6 mb-4">
        <form @submit.prevent="handleSubmit">
          <div v-if="!isEditing" class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Nombre de usuario</label>
            <input v-model="form.username" type="text" required minlength="3" maxlength="50" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500" /></div>
          <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Nombre completo</label>
            <input v-model="form.full_name" type="text" required class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500" /></div>
          <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Rol</label>
            <select v-model="form.role" required class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="" disabled>Seleccionar</option><option value="admin">Administrador</option><option value="contable">Contable</option>
              <option value="gestor">Gestor de Caja</option><option value="consulta">Consulta</option></select></div>
          <div class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Delegación</label>
            <select v-model="form.delegacion" required class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="" disabled>Seleccionar</option><option value="Bata">Bata</option><option value="Malabo">Malabo</option>
              <option value="Ambas" :disabled="form.role==='gestor'">Ambas</option></select>
            <p v-if="form.role==='gestor'" class="text-xs text-gray-400 mt-1">El Gestor debe asignarse a una delegación específica.</p></div>
          <div v-if="!isEditing" class="mb-4"><label class="block text-sm font-medium text-gray-600 mb-1">Contraseña</label>
            <input v-model="form.password" type="password" required minlength="8" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500" />
            <p class="text-xs text-gray-400 mt-1">Mín 8 chars, mayúscula, número, especial.</p></div>
          <div v-if="errorMsg" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{{ errorMsg }}</div>
          <div class="flex gap-3">
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50">{{ saving ? 'Guardando...' : (isEditing ? 'Guardar' : 'Crear') }}</button>
            <router-link :to="{ name: 'users' }" class="px-4 py-2 border border-gray-300 text-gray-600 text-sm rounded-md hover:bg-gray-50">Cancelar</router-link>
          </div>
        </form>
      </div>
      <div v-if="isEditing" class="bg-white rounded-lg shadow p-6">
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Cambiar contraseña</h2>
        <form @submit.prevent="handlePwd">
          <div class="mb-4"><input v-model="newPwd" type="password" required minlength="8" placeholder="Nueva contraseña" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm" /></div>
          <div v-if="pwdErr" class="mb-3 text-sm text-red-600">{{ pwdErr }}</div>
          <div v-if="pwdOk" class="mb-3 text-sm text-green-600">{{ pwdOk }}</div>
          <button type="submit" :disabled="savingPwd" class="px-4 py-2 bg-gray-700 text-white text-sm rounded-md hover:bg-gray-800 disabled:opacity-50">{{ savingPwd ? 'Cambiando...' : 'Cambiar' }}</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getUser, createUser, updateUser, adminChangePassword } from '@/api/users'
const router = useRouter(); const route = useRoute()
const isEditing = computed(() => !!route.params.id)
const saving = ref(false); const errorMsg = ref('')
const form = reactive({ username:'', full_name:'', role:'', delegacion:'', password:'' })
const newPwd = ref(''); const savingPwd = ref(false); const pwdErr = ref(''); const pwdOk = ref('')

watch(() => form.role, (r) => { if (r === 'gestor' && form.delegacion === 'Ambas') form.delegacion = '' })

onMounted(async () => {
  if (isEditing.value) {
    try { const r = await getUser(route.params.id); form.full_name=r.data.full_name; form.role=r.data.role; form.delegacion=r.data.delegacion }
    catch { errorMsg.value = 'Error al cargar usuario.' }
  }
})
async function handleSubmit() {
  saving.value = true; errorMsg.value = ''
  try {
    if (isEditing.value) await updateUser(route.params.id, { full_name:form.full_name, role:form.role, delegacion:form.delegacion })
    else await createUser({ username:form.username, password:form.password, full_name:form.full_name, role:form.role, delegacion:form.delegacion })
    router.push({ name: 'users' })
  } catch (e) { errorMsg.value = e.response?.data?.detail || 'Error.' }
  finally { saving.value = false }
}
async function handlePwd() {
  savingPwd.value = true; pwdErr.value = ''; pwdOk.value = ''
  try { await adminChangePassword(route.params.id, newPwd.value); pwdOk.value = 'Contraseña actualizada.'; newPwd.value = '' }
  catch (e) { pwdErr.value = e.response?.data?.detail || 'Error.' }
  finally { savingPwd.value = false }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-xl font-bold text-gray-800">Gestión de Usuarios</h1>
      <router-link :to="{ name: 'user-create' }" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700">Nuevo usuario</router-link>
    </div>
    <div class="bg-white rounded-lg shadow p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div><label class="block text-xs font-medium text-gray-500 mb-1">Rol</label>
          <select v-model="filters.role" @change="loadUsers" class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm">
            <option value="">Todos</option><option value="admin">Administrador</option><option value="contable">Contable</option>
            <option value="gestor">Gestor de Caja</option><option value="consulta">Consulta</option></select></div>
        <div><label class="block text-xs font-medium text-gray-500 mb-1">Delegación</label>
          <select v-model="filters.delegacion" @change="loadUsers" class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm">
            <option value="">Todas</option><option value="Bata">Bata</option><option value="Malabo">Malabo</option><option value="Ambas">Ambas</option></select></div>
        <div><label class="block text-xs font-medium text-gray-500 mb-1">Estado</label>
          <select v-model="filters.active" @change="loadUsers" class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm">
            <option value="">Todos</option><option value="true">Activos</option><option value="false">Inactivos</option></select></div>
      </div>
    </div>
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div v-if="loading" class="p-8 text-center text-gray-500">Cargando usuarios...</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50 border-b"><tr>
          <th class="px-4 py-3 text-left font-medium text-gray-600">Usuario</th>
          <th class="px-4 py-3 text-left font-medium text-gray-600">Nombre</th>
          <th class="px-4 py-3 text-left font-medium text-gray-600">Rol</th>
          <th class="px-4 py-3 text-left font-medium text-gray-600">Delegación</th>
          <th class="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
          <th class="px-4 py-3 text-center font-medium text-gray-600">Acciones</th>
        </tr></thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-mono text-gray-700">{{ u.username }}</td>
            <td class="px-4 py-3 text-gray-800">{{ u.full_name }}</td>
            <td class="px-4 py-3"><span :class="rolBadge(u.role)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ rolLabels[u.role] }}</span></td>
            <td class="px-4 py-3 text-gray-700">{{ u.delegacion }}</td>
            <td class="px-4 py-3 text-center"><span :class="u.active ? 'text-green-600':'text-red-500'" class="text-xs font-medium">{{ u.active ? 'Activo':'Inactivo' }}</span></td>
            <td class="px-4 py-3 text-center"><div class="flex items-center justify-center gap-2">
              <router-link :to="{ name: 'user-edit', params: { id: u.id } }" class="text-blue-600 hover:text-blue-800 text-xs font-medium">Editar</router-link>
              <button @click="toggleActive(u)" :class="u.active ? 'text-red-500':'text-green-600'" class="text-xs font-medium">{{ u.active ? 'Desactivar':'Activar' }}</button>
            </div></td>
          </tr>
          <tr v-if="users.length === 0"><td colspan="6" class="px-4 py-8 text-center text-gray-400">Sin resultados.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listUsers, updateUser } from '@/api/users'
const users = ref([]); const loading = ref(false)
const filters = reactive({ role: '', delegacion: '', active: '' })
const rolLabels = { admin:'Administrador', contable:'Contable', gestor:'Gestor de Caja', consulta:'Consulta' }
function rolBadge(r) { return { admin:'bg-purple-100 text-purple-700', contable:'bg-blue-100 text-blue-700', gestor:'bg-green-100 text-green-700', consulta:'bg-gray-100 text-gray-600' }[r] || '' }
async function loadUsers() {
  loading.value = true
  try {
    const p = { page: 1, page_size: 50 }
    if (filters.role) p.role = filters.role
    if (filters.delegacion) p.delegacion = filters.delegacion
    if (filters.active !== '') p.active = filters.active === 'true'
    users.value = (await listUsers(p)).data.items
  } finally { loading.value = false }
}
async function toggleActive(u) {
  if (!confirm(`¿${u.active?'Desactivar':'Activar'} a ${u.username}?`)) return
  await updateUser(u.id, { active: !u.active }); loadUsers()
}
onMounted(loadUsers)
</script>

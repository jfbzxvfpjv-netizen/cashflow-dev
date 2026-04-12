<template>
  <div class="min-h-screen bg-gray-100">
    <DevBanner />
    <div class="flex">
      <AppSidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
      <div class="flex-1 flex flex-col" :class="collapsed ? 'ml-16' : 'ml-56'">
        <header class="bg-white shadow-sm border-b px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <span class="text-sm text-gray-500">{{ auth.user?.delegacion === 'Ambas' ? 'Bata + Malabo' : auth.user?.delegacion }}</span>
          <div class="flex items-center gap-4">
            <div class="text-right">
              <p class="text-sm font-medium text-gray-700">{{ auth.user?.full_name }}</p>
              <p class="text-xs text-gray-400">{{ {admin:'Administrador',contable:'Contable',gestor:'Gestor de Caja',consulta:'Consulta'}[auth.user?.role] }}</p>
            </div>
            <button @click="handleLogout" class="text-sm text-gray-500 hover:text-red-600">Salir</button>
          </div>
        </header>
        <main class="flex-1 p-6"><router-view /></main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import DevBanner from '@/components/layout/DevBanner.vue'
const router = useRouter(); const auth = useAuthStore(); const collapsed = ref(false)
async function handleLogout() { await auth.logout(); router.push({ name: 'login' }) }
</script>

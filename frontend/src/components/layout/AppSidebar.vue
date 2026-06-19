<template>
  <aside :class="collapsed ? 'w-16' : 'w-56'" class="fixed left-0 top-0 h-screen bg-gray-800 text-gray-300 flex flex-col transition-all duration-200 z-20">
    <div class="px-4 py-4 border-b border-gray-700">
      <h2 v-if="!collapsed" class="text-sm font-bold text-white truncate">Flujo de Caja</h2>
      <span v-else class="text-white font-bold text-lg block text-center">FC</span>
    </div>
    <nav class="flex-1 overflow-y-auto py-2">
      <template v-for="item in visible" :key="item.to">
        <div v-if="item.sep && !collapsed" class="px-4 pt-4 pb-1"><span class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ item.sep }}</span></div>
        <router-link :to="item.to" class="flex items-center gap-3 px-4 py-2 text-sm hover:bg-gray-700 hover:text-white" :class="{ 'justify-center': collapsed }"
          active-class="bg-gray-700 text-white border-l-2 border-blue-400">
          <span class="text-base" :title="collapsed ? item.label : ''">{{ item.icon }}</span>
          <span v-if="!collapsed" class="flex-1">{{ item.label }}</span>
          <span v-if="!collapsed && item.badge > 0"
                @click.stop.prevent="goToProvisional"
                class="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5 ml-auto cursor-pointer hover:bg-red-600"
                :title="'Click para ver las ' + item.badge + ' provisionales pendientes'">{{ item.badge }}</span>
        </router-link>
      </template>
    </nav>
    <div class="border-t border-gray-700 p-2">
      <button @click="$emit('toggle')" class="w-full py-2 text-center text-gray-400 hover:text-white text-xs">{{ collapsed ? '→' : '← Colapsar' }}</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
defineProps({ collapsed: { type: Boolean, default: false } }); defineEmits(['toggle'])
const auth = useAuthStore()
const router = useRouter()

// F6: badge de transacciones provisionales (polling cada 60s)
const provisionalCount = ref(0)
let pollInterval = null
async function fetchProvisionalCount() {
  if (!['admin', 'contable'].includes(auth.userRole)) return
  try {
    const { data } = await api.get('/transactions/provisional/count')
    provisionalCount.value = data.count || 0
  } catch (e) {
    // silencio en sidebar; no romper la navegacion por un fallo de polling
  }
}
function goToProvisional() {
  router.push({ path: '/transactions', query: { signature_method: 'wacom_provisional' } })
}

onMounted(() => {
  fetchProvisionalCount()
  pollInterval = setInterval(fetchProvisionalCount, 60000)
})
onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})

const menu = [
  { to:'/dashboard', label:'Panel Principal', icon:'📊', roles:[] },
  { sep:'Transacciones', to:'/transactions', label:'Transacciones', icon:'💰', roles:['admin','gestor','contable','consulta'] },
  { to:'/approvals', label:'Aprobaciones', icon:'✅', roles:['admin'] },
  { to:'/payrolls', label:'Nóminas', icon:'💰', roles:['admin','gestor','contable'] },
  { to:'/integrity', label:'Integridad', icon:'🔐', roles:['admin'] },
  { sep:'Catálogos', to:'/projects', label:'Proyectos', icon:'📁', roles:['admin'] },
  { to:'/works', label:'Obras', icon:'🏗', roles:['admin'] },
  { to:'/categories', label:'Categorías', icon:'🏷️', roles:['admin'] },
  { to:'/suppliers', label:'Proveedores', icon:'🚚', roles:['admin'] },
  { to:'/employees', label:'Empleados', icon:'👥', roles:['admin','contable'] },
  { to:'/partners', label:'Socios', icon:'💼', roles:['admin','contable'] },
  { to:'/corporate-accounts', label:'Cuentas Bancarias', icon:'🏦', roles:['admin'] },
  { to:'/vehicles', label:'Vehículos', icon:'🚗', roles:['admin'] },
  { sep:'Operaciones', to:'/sessions', label:'Sesiones de Caja', icon:'💰', roles:['gestor','admin'] },
  { to:'/fingerprints/enroll', label:'Enrolar Huellas', icon:'👆', roles:['gestor'] },
  { to:'/bank-withdrawals', label:'Retiradas Bancarias', icon:'🏧', roles:['contable','admin','gestor'] },
  { to:'/config', label:'Configuración Caja', icon:'⚙️', roles:['admin'] },
    { to:'/import', label:'Importar Excel', icon:'📥', roles:['admin'] },
  { to:'/dev', label:'Desarrollo', icon:'🔧', roles:['admin'] },
    { to:'/reports', label:'Informes', icon:'📄', roles:['admin','contable','gestor','consulta'] },
        // M9: Módulos financieros especiales
  { sep: 'Módulos Financieros' },
  { to: '/advances-loans', label: 'Anticipos y Préstamos', icon: '💸', roles:['admin','contable','gestor'] },
  { to: '/retentions-deposits', label: 'Retenciones y Depósitos', icon: '🔒', roles:['admin','contable','gestor'] },
  { to: '/floats', label: 'Circulantes', icon: '💳', roles:['admin','contable','gestor'] },
  { to: '/installments', label: 'Pagos Fraccionados', icon: '📆', roles:['admin','contable','gestor'] },
  { to: '/currency-ops', label: 'Operaciones Divisa', icon: '💶', roles:['admin','contable','gestor'] },
  { to: '/partner-accounts', label: 'Cuentas de Socios', icon: '🤝', roles:['admin','contable','gestor'] },
  { to: '/reimbursable-expenses', label: 'Gastos Reembolsables', icon: '🧾', roles:['admin','contable','gestor'] },
  { to: '/money-transfers', label: 'Envíos de Dinero', icon: '📤', roles:['admin','contable','gestor'] },
  { sep:'Administración', to:'/users', label:'Usuarios', icon:'👤', roles:['admin'] },
  { to:'/admin/backups', label:'Backups', icon:'💾', roles:['admin'] },
  { to:'/admin/fingerprints', label:'Huellas Dactilares', icon:'👆', roles:['admin'] },
  { sep:'Cuenta', to:'/change-password', label:'Cambiar Contraseña', icon:'🔑', roles:[] },
]
const visible = computed(() => menu
  .filter(i => !i.roles || !i.roles.length || i.roles.includes(auth.userRole))
  .map(i => {
    // F6: inyectar badge en /transactions si el rol corresponde
    if (i.to === '/transactions' && ['admin', 'contable'].includes(auth.userRole)) {
      return { ...i, badge: provisionalCount.value }
    }
    return i
  })
)
</script>

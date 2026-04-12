import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || null)
  function hasRole(...roles) { return roles.includes(user.value?.role) }

  function setAuth(t, u) { token.value = t; user.value = u; localStorage.setItem('token', t); localStorage.setItem('user', JSON.stringify(u)) }
  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    if (data.requires_2fa) return { requires_2fa: true, temp_token: data.temp_token }
    setAuth(data.access_token, data.user); return { requires_2fa: false }
  }
  async function verify2fa(temp, code) { const { data } = await api.post('/auth/verify-2fa', { temp_token: temp, code }); setAuth(data.access_token, data.user) }
  function logout() { token.value = null; user.value = null; localStorage.removeItem('token'); localStorage.removeItem('user') }

  return { token, user, isAuthenticated, userRole, hasRole, login, verify2fa, logout }
})

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

api.interceptors.request.use((c) => {
  const auth = useAuthStore()
  if (auth.token) c.headers.Authorization = `Bearer ${auth.token}`
  return c
})

api.interceptors.response.use(r => r, err => {
  const url = err.config?.url || ''
  const isLoginAttempt = url.includes('/auth/login') || url.includes('/auth/verify-2fa')
  if (err.response?.status === 401 && !isLoginAttempt) {
    useAuthStore().logout()
    window.location.href = '/login'
  }
  return Promise.reject(err)
})

export default api

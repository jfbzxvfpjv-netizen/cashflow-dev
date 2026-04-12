import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({ baseURL: '/api/v1', timeout: 30000 })

api.interceptors.request.use((c) => {
  const auth = useAuthStore()
  if (auth.token) c.headers.Authorization = `Bearer ${auth.token}`
  return c
})

api.interceptors.response.use(r => r, err => {
  if (err.response?.status === 401) { useAuthStore().logout(); window.location.href = '/login' }
  return Promise.reject(err)
})

export default api

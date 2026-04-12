import axios from 'axios'
import router from '@/router'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, (error) => Promise.reject(error))

api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    if (router.currentRoute.value.name !== 'login') {
      router.push({ name: 'login', query: { expired: '1' } })
    }
  }
  return Promise.reject(error)
})

export default api

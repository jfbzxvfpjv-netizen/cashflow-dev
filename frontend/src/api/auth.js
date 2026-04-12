import api from '@/api/axios'

export function loginRequest(username, password) {
  return api.post('/auth/login', { username, password })
}

export function logoutRequest() {
  return api.post('/auth/logout')
}

export function getMeRequest() {
  return api.get('/auth/me')
}

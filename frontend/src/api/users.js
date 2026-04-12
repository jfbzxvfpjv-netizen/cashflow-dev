import api from '@/api/axios'

export function listUsers(params = {}) {
  return api.get('/users', { params })
}

export function getUser(userId) {
  return api.get(`/users/${userId}`)
}

export function createUser(data) {
  return api.post('/users', data)
}

export function updateUser(userId, data) {
  return api.put(`/users/${userId}`, data)
}

export function adminChangePassword(userId, newPassword) {
  return api.put(`/users/${userId}/password`, { new_password: newPassword })
}

export function selfChangePassword(currentPassword, newPassword) {
  return api.put('/users/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

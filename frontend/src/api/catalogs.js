/**
 * Módulo 4 — Servicio API de catálogos.
 */

import api from './axios'

export const projectsApi = {
  list: (params = {}) => api.get('/projects', { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
}

export const worksApi = {
  list: (params = {}) => api.get('/works', { params }),
  get: (id) => api.get(`/works/${id}`),
  create: (data) => api.post('/works', data),
  createInline: (data) => api.post('/works/inline', data),
  update: (id, data) => api.put(`/works/${id}`, data),
}

export const categoriesApi = {
  list: (params = {}) => api.get('/categories', { params }),
  get: (id) => api.get(`/categories/${id}`),
  create: (data) => api.post('/categories', data),
  update: (id, data) => api.put(`/categories/${id}`, data),
  delete: (id) => api.delete(`/categories/${id}`),
}

export const subcategoriesApi = {
  list: (categoryId, params = {}) =>
    api.get('/subcategories', { params: { category_id: categoryId, ...params } }),
  get: (id) => api.get(`/subcategories/${id}`),
  create: (data) => api.post('/subcategories', data),
  update: (id, data) => api.put(`/subcategories/${id}`, data),
  delete: (id) => api.delete(`/subcategories/${id}`),
}

export const suppliersApi = {
  list: (params = {}) => api.get('/suppliers', { params }),
  get: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
}

export const employeesApi = {
  list: (params = {}) => api.get('/employees', { params }),
  get: (id) => api.get(`/employees/${id}`),
  create: (data) => api.post('/employees', data),
  update: (id, data) => api.put(`/employees/${id}`, data),
  updateSalary: (id, data) => api.put(`/employees/${id}/salary`, data),
  getSalaryHistory: (id) => api.get(`/employees/${id}/salary-history`),
  delete: (id) => api.delete(`/employees/${id}`),
}

export const partnersApi = {
  list: (params = {}) => api.get('/partners', { params }),
  get: (id) => api.get(`/partners/${id}`),
  create: (data) => api.post('/partners', data),
  update: (id, data) => api.put(`/partners/${id}`, data),
  delete: (id) => api.delete(`/partners/${id}`),
}

export const corporateAccountsApi = {
  list: (params = {}) => api.get('/corporate-accounts', { params }),
  get: (id) => api.get(`/corporate-accounts/${id}`),
  create: (data) => api.post('/corporate-accounts', data),
  update: (id, data) => api.put(`/corporate-accounts/${id}`, data),
  delete: (id) => api.delete(`/corporate-accounts/${id}`),
}

export const vehiclesApi = {
  list: (params = {}) => api.get('/vehicles', { params }),
  get: (id) => api.get(`/vehicles/${id}`),
  create: (data) => api.post('/vehicles', data),
  update: (id, data) => api.put(`/vehicles/${id}`, data),
  delete: (id) => api.delete(`/vehicles/${id}`),
}

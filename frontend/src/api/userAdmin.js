import request from '@/utils/request'

export const userAdminApi = {
  list: (params = {}) => {
    return request.get('/v1/auth/', { params })
  },

  create: (data) => {
    return request.post('/v1/auth/register/', data)
  },

  update: (id, data) => {
    return request.patch(`/v1/auth/${id}/`, data)
  },

  delete: (id) => {
    return request.delete(`/v1/auth/${id}/`)
  },

  toggleStatus: (id, isActive) => {
    return request.patch(`/v1/auth/${id}/toggle_status/`, { is_active: isActive })
  },

  resetPassword: (id) => {
    return request.post(`/v1/auth/${id}/reset_password/`)
  }
}

export default userAdminApi

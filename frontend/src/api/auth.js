import request from '@/utils/request'

const BASE_URL = '/v1/auth'

export const authApi = {
  login(data) {
    return request.post(`${BASE_URL}/login/`, data)
  },

  register(data) {
    return request.post(`${BASE_URL}/register/`, data)
  },

  logout() {
    return request.post(`${BASE_URL}/logout/`)
  },

  getCurrentUser() {
    return request.get(`${BASE_URL}/me/`)
  },

  updateProfile(data) {
    return request.patch(`${BASE_URL}/me/`, data)
  },

  getLoginLogs(params) {
    return request.get(`${BASE_URL}/login-logs/`, { params })
  },

  refreshToken(refresh) {
    return request.post(`${BASE_URL}/token/refresh/`, { refresh })
  }
}

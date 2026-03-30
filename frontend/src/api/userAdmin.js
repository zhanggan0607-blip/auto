/**
 * 用户管理 API
 */
import request from '@/utils/request'

export const userAdminApi = {
  /**
   * 获取用户列表
   */
  list: (params = {}) => {
    return request.get('/v1/auth/', { params })
  },

  /**
   * 获取用户详情
   */
  get: (id) => {
    return request.get(`/v1/auth/${id}/`)
  },

  /**
   * 创建用户
   */
  create: (data) => {
    return request.post('/v1/auth/register/', data)
  },

  /**
   * 更新用户
   */
  update: (id, data) => {
    return request.patch(`/v1/auth/${id}/`, data)
  },

  /**
   * 删除用户(禁用)
   */
  delete: (id) => {
    return request.delete(`/v1/auth/${id}/`)
  },

  /**
   * 启用/禁用用户
   */
  toggleStatus: (id, isActive) => {
    return request.patch(`/v1/auth/${id}/toggle_status/`, { is_active: isActive })
  },

  /**
   * 修改用户角色
   */
  updateRole: (id, role) => {
    return request.patch(`/v1/auth/${id}/`, { role })
  },

  /**
   * 重置用户密码
   */
  resetPassword: (id) => {
    return request.post(`/v1/auth/${id}/reset_password/`)
  }
}

export default userAdminApi

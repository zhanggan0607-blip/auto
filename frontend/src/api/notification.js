import request from '@/utils/request'

const BASE_URL = '/v1/notifications'

export const notificationApi = {
  getList(params) {
    return request.get(`${BASE_URL}/`, params)
  },

  markRead(id) {
    return request.post(`${BASE_URL}/${id}/mark-read/`)
  },

  markAllRead() {
    return request.post(`${BASE_URL}/mark-read/`)
  },

  getUnreadCount() {
    return request.get(`${BASE_URL}/unread-count/`)
  },

  deleteNotification(id) {
    return request.delete(`${BASE_URL}/${id}/`)
  },

  batchDelete(data) {
    return request.post(`${BASE_URL}/batch-delete/`, data)
  }
}

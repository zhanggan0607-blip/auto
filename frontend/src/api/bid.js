import request from '@/utils/request'

const BASE_URL = '/v1/bids'

export const bidApi = {
  getList(params) {
    return request.get(`${BASE_URL}/records/`, { params })
  },

  getDetail(id) {
    return request.get(`${BASE_URL}/records/${id}/`)
  },

  create(data) {
    return request.post(`${BASE_URL}/records/`, data)
  },

  update(id, data) {
    return request.patch(`${BASE_URL}/records/${id}/`, data)
  },

  delete(id) {
    return request.delete(`${BASE_URL}/records/${id}/`)
  },

  getStatistics() {
    return request.get(`${BASE_URL}/statistics/`)
  },

  getResults(params) {
    return request.get(`${BASE_URL}/results/`, { params })
  },

  createResult(data) {
    return request.post(`${BASE_URL}/results/`, data)
  },

  updateResult(id, data) {
    return request.patch(`${BASE_URL}/results/${id}/`, data)
  }
}

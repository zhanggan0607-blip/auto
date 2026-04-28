import request from '@/utils/request'

const BASE_URL = '/v1/documents'

export const documentApi = {
  getTemplates(params) {
    return request.get(`${BASE_URL}/templates/`, { params })
  },
  deleteTemplate(id) {
    return request.delete(`${BASE_URL}/templates/${id}/`)
  },
  getGeneratedList(params) {
    return request.get(`${BASE_URL}/generated/`, { params })
  },
  generateDocument(data) {
    return request.post(`${BASE_URL}/generate/`, data)
  },
  reviewDocument(id) {
    return request.post(`${BASE_URL}/generated/${id}/review/`)
  },
  searchReferenceDocs(params) {
    return request.get(`${BASE_URL}/search-reference-docs/`, { params })
  }
}

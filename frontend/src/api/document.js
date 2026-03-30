import request from '@/utils/request'

const BASE_URL = '/v1/documents'

export const documentApi = {
  getTemplates(params) {
    return request.get(`${BASE_URL}/templates/`, { params })
  },

  getTemplate(id) {
    return request.get(`${BASE_URL}/templates/${id}/`)
  },

  createTemplate(data) {
    return request.post(`${BASE_URL}/templates/`, data)
  },

  updateTemplate(id, data) {
    return request.patch(`${BASE_URL}/templates/${id}/`, data)
  },

  deleteTemplate(id) {
    return request.delete(`${BASE_URL}/templates/${id}/`)
  },

  getGeneratedList(params) {
    return request.get(`${BASE_URL}/generated/`, { params })
  },

  getGeneratedDoc(id) {
    return request.get(`${BASE_URL}/generated/${id}/`)
  },

  generateDocument(data) {
    return request.post(`${BASE_URL}/generate/`, data)
  },

  reviewDocument(id) {
    return request.post(`${BASE_URL}/generated/${id}/review/`)
  },

  deleteGeneratedDoc(id) {
    return request.delete(`${BASE_URL}/generated/${id}/`)
  },

  searchReferenceDocs(params) {
    return request.get(`${BASE_URL}/search-reference-docs/`, { params })
  },

  getReferenceDocs(docId) {
    return request.get(`${BASE_URL}/generated/${docId}/reference-docs/`)
  },

  addReferenceDocs(docId, referenceDocIds) {
    return request.post(`${BASE_URL}/generated/${docId}/reference-docs/`, {
      reference_doc_ids: referenceDocIds
    })
  },

  removeReferenceDocs(docId, referenceDocIds) {
    return request.delete(`${BASE_URL}/generated/${docId}/reference-docs/`, {
      data: { reference_doc_ids: referenceDocIds }
    })
  }
}

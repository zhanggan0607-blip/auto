/**
 * 投标文档向量库 API
 */
import request from '@/utils/request'

export const vectorlibApi = {
  getDocuments(params = {}) {
    return request.get('/v1/vectorlib/documents/', params)
  },

  getDocument(id) {
    return request.get(`/v1/vectorlib/documents/${id}/`)
  },

  uploadDocument(formData, onProgress) {
    return request.post('/v1/vectorlib/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    })
  },

  deleteDocument(id) {
    return request.delete(`/v1/vectorlib/documents/${id}/`)
  },

  searchDocuments(data) {
    return request.post('/v1/vectorlib/documents/search/', data)
  },

  advancedSearch(data) {
    return request.post('/v1/vectorlib/documents/advanced_search/', data)
  },

  incrementView(id) {
    return request.post(`/v1/vectorlib/documents/${id}/increment_view/`)
  },

  incrementUse(id) {
    return request.post(`/v1/vectorlib/documents/${id}/increment_use/`)
  },

  getStatistics() {
    return request.get('/v1/vectorlib/documents/statistics/')
  },

  getAISearchTasks(params = {}) {
    return request.get('/v1/vectorlib/ai-search/', params)
  },

  createAISearchTask(data) {
    return request.post('/v1/vectorlib/ai-search/', data)
  },

  retryAISearchTask(id) {
    return request.post(`/v1/vectorlib/ai-search/${id}/retry/`)
  }
}

export default vectorlibApi
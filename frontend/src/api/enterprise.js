import request from '@/utils/request'

const BASE_URL = '/v1/enterprise'

export const enterpriseApi = {
  getEnterprises(params) {
    return request.get(`${BASE_URL}/enterprises/`, { params })
  },

  createEnterprise(data) {
    return request.post(`${BASE_URL}/enterprises/`, data)
  },

  updateEnterprise(id, data) {
    return request.patch(`${BASE_URL}/enterprises/${id}/`, data)
  },

  deleteEnterprise(id) {
    return request.delete(`${BASE_URL}/enterprises/${id}/`)
  },

  getDocuments(params) {
    return request.get(`${BASE_URL}/documents/`, { params })
  },

  createDocument(data) {
    return request.post(`${BASE_URL}/documents/`, data)
  },

  updateDocument(id, data) {
    return request.patch(`${BASE_URL}/documents/${id}/`, data)
  },

  deleteDocument(id) {
    return request.delete(`${BASE_URL}/documents/${id}/`)
  },

  getDocumentStatistics(enterpriseId) {
    return request.get(`${BASE_URL}/documents/statistics/`, { 
      params: { enterprise_id: enterpriseId } 
    })
  },

  getDocumentOptions() {
    return request.get(`${BASE_URL}/documents/options/`)
  },

  recognizeDocument(id) {
    return request.post(`${BASE_URL}/documents/${id}/recognize/`)
  },

  updateFromRecognition(id, fields = null) {
    return request.post(`${BASE_URL}/documents/${id}/update_from_recognition/`, { fields })
  },

  batchRecognizeDocuments(ids) {
    return request.post(`${BASE_URL}/documents/batch_recognize/`, { ids })
  },

  collectEnterpriseInfo(companyName, options = {}) {
    return request.post(`${BASE_URL}/enterprises/collect_info/`, {
      company_name: companyName,
      ...options
    }, {
      skipErrorMessage: true
    })
  },

  searchEnterpriseOnline(companyName, source = 'auto') {
    return request.post(`${BASE_URL}/enterprises/search_online/`, {
      company_name: companyName,
      source
    }, {
      skipErrorMessage: true
    })
  },
  
  getKeyPersonnel(params) {
    return request.get(`${BASE_URL}/key-personnel/`, { params })
  },
  
  createKeyPersonnel(data) {
    return request.post(`${BASE_URL}/key-personnel/`, data)
  },
  
  updateKeyPersonnel(id, data) {
    return request.put(`${BASE_URL}/key-personnel/${id}/`, data)
  },
  
  deleteKeyPersonnel(id) {
    return request.delete(`${BASE_URL}/key-personnel/${id}/`)
  },

  getContacts(params) {
    return request.get(`${BASE_URL}/contacts/`, { params })
  },

  createContact(data) {
    return request.post(`${BASE_URL}/contacts/`, data)
  },

  updateContact(id, data) {
    return request.patch(`${BASE_URL}/contacts/${id}/`, data)
  },

  deleteContact(id) {
    return request.delete(`${BASE_URL}/contacts/${id}/`)
  },

  getMatchRules(params) {
    return request.get(`${BASE_URL}/match-rules/`, { params })
  },

  createMatchRule(data) {
    return request.post(`${BASE_URL}/match-rules/`, data)
  },

  updateMatchRule(id, data) {
    return request.patch(`${BASE_URL}/match-rules/${id}/`, data)
  },

  deleteMatchRule(id) {
    return request.delete(`${BASE_URL}/match-rules/${id}/`)
  },

  getMatchResults(params) {
    return request.get(`${BASE_URL}/match-results/`, { params })
  },

  getMatchResultDetail(id) {
    return request.get(`${BASE_URL}/match-results/${id}/`)
  },

  markMatchResultRead(id) {
    return request.post(`${BASE_URL}/match-results/${id}/mark_read/`)
  },

  toggleMatchResultFavorite(id) {
    return request.post(`${BASE_URL}/match-results/${id}/toggle_favorite/`)
  },

  markMatchResultApplied(id) {
    return request.post(`${BASE_URL}/match-results/${id}/mark_applied/`)
  },

  batchMarkMatchResultsRead(ids) {
    return request.post(`${BASE_URL}/match-results/batch_mark_read/`, { ids })
  },

  getBidConfigs(params) {
    return request.get(`${BASE_URL}/bid-configs/`, { params })
  },

  createBidConfig(data) {
    return request.post(`${BASE_URL}/bid-configs/`, data)
  },

  updateBidConfig(id, data) {
    return request.patch(`${BASE_URL}/bid-configs/${id}/`, data)
  },

  deleteBidConfig(id) {
    return request.delete(`${BASE_URL}/bid-configs/${id}/`)
  },

  getBidConfigTemplateVariables(id) {
    return request.get(`${BASE_URL}/bid-configs/${id}/template_variables/`)
  },

  getBidConfigOptions() {
    return request.get(`${BASE_URL}/bid-configs/options/`)
  },

  matchTender(tenderData, enterpriseIds = null) {
    return request.post(`${BASE_URL}/match/`, {
      ...tenderData,
      enterprise_ids: enterpriseIds
    })
  },

  semanticMatch(tenderData, enterpriseIds = null, threshold = 0.6) {
    return request.post(`${BASE_URL}/enterprises/semantic_match/`, {
      ...tenderData,
      enterprise_ids: enterpriseIds,
      threshold
    })
  },

  getQualifications(params) {
    return request.get(`${BASE_URL}/qualifications/`, { params })
  },

  createQualification(data) {
    return request.post(`${BASE_URL}/qualifications/`, data)
  },

  updateQualification(id, data) {
    return request.patch(`${BASE_URL}/qualifications/${id}/`, data)
  },

  deleteQualification(id) {
    return request.delete(`${BASE_URL}/qualifications/${id}/`)
  },

  getPerformances(params) {
    return request.get(`${BASE_URL}/performances/`, { params })
  },

  createPerformance(data) {
    return request.post(`${BASE_URL}/performances/`, data)
  },

  updatePerformance(id, data) {
    return request.patch(`${BASE_URL}/performances/${id}/`, data)
  },

  deletePerformance(id) {
    return request.delete(`${BASE_URL}/performances/${id}/`)
  }
}

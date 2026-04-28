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

  deleteDocument(id) {
    return request.delete(`${BASE_URL}/documents/${id}/`)
  },

  getDocumentOptions() {
    return request.get(`${BASE_URL}/documents/options/`)
  },

  getKeyPersonnel(params) {
    return request.get(`${BASE_URL}/key-personnel/`, { params })
  },

  createKeyPersonnel(data) {
    return request.post(`${BASE_URL}/key-personnel/`, data)
  },

  updateKeyPersonnel(id, data) {
    return request.patch(`${BASE_URL}/key-personnel/${id}/`, data)
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

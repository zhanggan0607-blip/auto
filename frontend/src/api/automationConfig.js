import request from '@/utils/request'

const BASE_URL = '/v1/openclaw'

export const automationConfigApi = {
  list: (params) => {
    return request.get(`${BASE_URL}/automation-config/`, { params })
  },

  create: (data) => {
    return request.post(`${BASE_URL}/automation-config/`, data)
  },

  delete: (id) => {
    return request.delete(`${BASE_URL}/automation-config/${id}/`)
  },

  getDefaultConfig: () => {
    return request.get(`${BASE_URL}/automation-config/default_config/`)
  },

  setDefault: (id) => {
    return request.post(`${BASE_URL}/automation-config/${id}/set_default/`)
  },

  updateDecisionConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_decision_config/`, {
      decision_config: data
    })
  },

  updateMatchConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_match_config/`, {
      match_config: data
    })
  },

  updateReviewConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_review_config/`, {
      review_config: data
    })
  },

  updateRiskConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_risk_config/`, {
      risk_config: data
    })
  },

  updateCrawlConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_crawl_config/`, {
      crawl_config: data
    })
  },

  updateNotificationConfig: (id, data) => {
    return request.post(`${BASE_URL}/automation-config/${id}/update_notification_config/`, {
      notification_config: data
    })
  },

  createWithDefaults: (data) => {
    return request.post(`${BASE_URL}/automation-config/create_with_defaults/`, data)
  }
}

export default automationConfigApi

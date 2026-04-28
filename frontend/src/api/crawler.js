import request from '@/utils/request'

const BASE_URL = '/v1/crawler'

export const crawlerApi = {
  getWebsiteTemplates(params = {}) {
    return request.get(`${BASE_URL}/templates/`, { params })
  },

  getWebsiteTemplate(id) {
    return request.get(`${BASE_URL}/templates/${id}/`)
  },

  createWebsiteTemplate(data) {
    return request.post(`${BASE_URL}/templates/`, data)
  },

  updateWebsiteTemplate(id, data) {
    return request.put(`${BASE_URL}/templates/${id}/`, data)
  },

  deleteWebsiteTemplate(id) {
    return request.delete(`${BASE_URL}/templates/${id}/`)
  },

  toggleWebsiteTemplate(id, is_active) {
    return request.patch(`${BASE_URL}/templates/${id}/`, { is_active })
  },

  checkTemplateCodeDuplicate(code, excludeId = null) {
    const params = { code }
    if (excludeId) {
      params.exclude_id = excludeId
    }
    return request.get(`${BASE_URL}/templates/check_duplicate_code/`, { params })
  },

  testWebsiteTemplate(id) {
    return request.post(`${BASE_URL}/templates/${id}/test/`)
  },

  testWebsiteTemplateConfig(data) {
    return request.post(`${BASE_URL}/templates/test_config/`, data)
  },

  getCrawlSchedules(params) {
    return request.get(`${BASE_URL}/schedules/`, { params })
  },

  getCrawlScheduleDetail(id) {
    return request.get(`${BASE_URL}/schedules/${id}/`)
  },

  createCrawlSchedule(data) {
    return request.post(`${BASE_URL}/schedules/`, data)
  },

  updateCrawlSchedule(id, data) {
    return request.patch(`${BASE_URL}/schedules/${id}/`, data)
  },

  deleteCrawlSchedule(id) {
    return request.delete(`${BASE_URL}/schedules/${id}/`)
  },

  enableCrawlSchedule(id) {
    return request.post(`${BASE_URL}/schedules/${id}/enable/`)
  },

  pauseCrawlSchedule(id) {
    return request.post(`${BASE_URL}/schedules/${id}/pause/`)
  },

  executeCrawlScheduleNow(id) {
    return request.post(`${BASE_URL}/schedules/${id}/execute_now/`)
  },

  getCrawlScheduleLogs(id, params) {
    return request.get(`${BASE_URL}/schedules/${id}/logs/`, { params })
  },

  checkScheduleNameDuplicate(name, excludeId = null) {
    const params = { name }
    if (excludeId) {
      params.exclude_id = excludeId
    }
    return request.get(`${BASE_URL}/schedules/check_duplicate_name/`, { params })
  }
}

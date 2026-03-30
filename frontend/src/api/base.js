/**
 * API基础封装模块
 * 提供统一的API创建方式，减少样板代码
 *
 * 使用示例：
 *
 * // 方式1：使用createApi工厂函数（推荐用于标准CRUD）
 * import { createApi } from './base'
 * export const tenderApi = createApi('/v1/tenders')
 *
 * // 方式2：使用ApiClient类（用于复杂API）
 * import { ApiClient } from './base'
 * export const enterpriseApi = new ApiClient('/v1/enterprise')
 *
 * // 方式3：直接扩展（用于有自定义方法的API）
 * import { ApiClient } from './base'
 * const client = new ApiClient('/v1/enterprise')
 * export const enterpriseApi = {
 *   ...client.api,
 *   customMethod: (params) => client.get('/custom', params)
 * }
 */
import request from '@/utils/request'

/**
 * API错误类
 * 提供结构化的错误信息
 */
export class ApiError extends Error {
  constructor(error, customMessage = null) {
    super(customMessage || error.message || '请求失败')
    this.name = 'ApiError'
    this.code = error.response?.status
    this.data = error.response?.data
    this.originalError = error
  }

  isNotFound() {
    return this.code === 404
  }

  isUnauthorized() {
    return this.code === 401
  }

  isForbidden() {
    return this.code === 403
  }

  getMessage() {
    return this.data?.message || this.message
  }
}

/**
 * 创建标准CRUD API对象
 *
 * @param {string} baseUrl - API基础URL
 * @param {Object} options - 配置选项
 * @param {string} options.listEndpoint - 列表接口路径，默认 '/'
 * @param {string} options.detailEndpoint - 详情接口路径，默认 '/:id/'
 * @returns {Object} API方法对象
 *
 * @example
 * const tenderApi = createApi('/v1/tenders')
 *
 * // 生成的方法：
 * tenderApi.getList(params)     // GET /v1/tenders/
 * tenderApi.getDetail(id)         // GET /v1/tenders/{id}/
 * tenderApi.create(data)          // POST /v1/tenders/
 * tenderApi.update(id, data)      // PATCH /v1/tenders/{id}/
 * tenderApi.delete(id)            // DELETE /v1/tenders/{id}/
 */
export function createApi(baseUrl, options = {}) {
  const {
    listEndpoint = '/',
    detailEndpoint = '/:id/'
  } = options

  const api = {}

  api.getList = (params, config = {}) => {
    return request.get(`${baseUrl}${listEndpoint}`, params, config)
  }

  api.getDetail = (id, params = null, config = {}) => {
    const url = `${baseUrl}${detailEndpoint}`.replace(':id', id)
    return request.get(url, params, config)
  }

  api.create = (data, config = {}) => {
    return request.post(`${baseUrl}${listEndpoint}`, data, config)
  }

  api.update = (id, data, config = {}) => {
    const url = `${baseUrl}${detailEndpoint}`.replace(':id', id)
    return request.patch(url, data, config)
  }

  api.put = (id, data, config = {}) => {
    const url = `${baseUrl}${detailEndpoint}`.replace(':id', id)
    return request.put(url, data, config)
  }

  api.delete = (id, config = {}) => {
    const url = `${baseUrl}${detailEndpoint}`.replace(':id', id)
    return request.delete(url, {}, config)
  }

  return api
}

/**
 * API客户端类
 * 提供更灵活API创建方式
 */
export class ApiClient {
  constructor(baseUrl, options = {}) {
    this.baseUrl = baseUrl
    this.listEndpoint = options.listEndpoint || '/'
    this.detailEndpoint = options.detailEndpoint || '/:id/'
    this.request = request
  }

  get(endpoint, params = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.get(url, { params }, config)
  }

  post(endpoint, data = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.post(url, data, config)
  }

  patch(endpoint, data = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.patch(url, data, config)
  }

  put(endpoint, data = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.put(url, data, config)
  }

  delete(endpoint, params = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.delete(url, { params }, config)
  }

  paginate(endpoint, { page = 1, pageSize = 20, ...params } = {}, config = {}) {
    const url = endpoint.startsWith('/') ? endpoint : `${this.baseUrl}${endpoint}`
    return this.request.paginate(url, { page, page_size: pageSize, ...params }, config)
  }

  get api() {
    return createApi(this.baseUrl, {
      listEndpoint: this.listEndpoint,
      detailEndpoint: this.detailEndpoint
    })
  }
}

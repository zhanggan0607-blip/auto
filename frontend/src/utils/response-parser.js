/**
 * API 响应解析工具 V3
 * 统一处理后端统一响应格式
 *
 * 标准响应格式:
 * {
 *     success: true,
 *     code: 0,
 *     message: '操作成功',
 *     data: {...},
 *     timestamp: '...'
 * }
 *
 * 分页响应格式（统一后）:
 * {
 *     success: true,
 *     code: 0,
 *     message: '查询成功',
 *     data: [...],
 *     meta: {
 *         pagination: {
 *             total: 100,
 *             page: 1,
 *             page_size: 20,
 *             total_pages: 5,
 *             has_next: true,
 *             has_prev: false
 *         }
 *     },
 *     timestamp: '...'
 * }
 */

export function isSuccess(res) {
  if (!res || typeof res !== 'object') {
    return false
  }

  if (typeof res.success === 'boolean') {
    return res.success
  }

  if (typeof res.code === 'number') {
    return res.code === 0
  }

  return true
}

export function getData(res) {
  if (!res || typeof res !== 'object') {
    return res
  }

  if (res.data !== undefined) {
    return res.data
  }

  return res
}

export function parseListResponse(res) {
  if (!res || typeof res !== 'object') {
    return { list: [], total: 0 }
  }

  let list = []
  let total = 0

  if (Array.isArray(res)) {
    list = res
    total = res.length
  } else if (res.data) {
    const data = res.data
    if (Array.isArray(data)) {
      list = data
      total = res.meta?.pagination?.total || data.length
    } else if (Array.isArray(data.list)) {
      list = data.list
      total = data.pagination?.total || res.meta?.pagination?.total || 0
    } else if (Array.isArray(data.results)) {
      list = data.results
      total = data.pagination?.total || res.meta?.pagination?.total || res.count || 0
    }
  } else if (Array.isArray(res.results)) {
    list = res.results
    total = res.count || res.results.length
  } else if (Array.isArray(res.list)) {
    list = res.list
    total = res.pagination?.total || res.total || list.length
  }

  return { list, total }
}

export function parsePagination(res) {
  if (!res || typeof res !== 'object') {
    return { page: 1, pageSize: 20, total: 0, totalPages: 1 }
  }

  const pagination = res.meta?.pagination || res.data?.pagination || res.pagination || {}

  return {
    page: pagination.page || res.page || 1,
    pageSize: pagination.page_size || pagination.pageSize || res.page_size || 20,
    total: pagination.total || res.total || res.count || 0,
    totalPages: pagination.total_pages || pagination.totalPages ||
      Math.ceil((pagination.total || res.total || 0) / (pagination.page_size || 20)) || 1
  }
}

export function parseDetailResponse(res) {
  if (!res || typeof res !== 'object') {
    return res
  }

  if (res.data !== undefined) {
    if (typeof res.data === 'object' && res.data !== null) {
      return res.data
    }
    return res
  }

  if (res.results !== undefined) {
    return res.results
  }

  if (res.list !== undefined) {
    return res.list
  }

  return res
}

export function parseErrorMessage(res) {
  if (!res || typeof res !== 'object') {
    return '请求失败'
  }

  if (res.message) {
    return res.message
  }

  if (res.msg) {
    return res.msg
  }

  if (res.error) {
    if (typeof res.error === 'string') {
      return res.error
    }
    if (res.error.message) {
      return res.error.message
    }
  }

  if (res.detail) {
    return res.detail
  }

  if (res.errors && typeof res.errors === 'object') {
    const messages = []
    for (const [field, errors] of Object.entries(res.errors)) {
      if (Array.isArray(errors)) {
        messages.push(`${field}: ${errors.join(', ')}`)
      } else if (typeof errors === 'string') {
        messages.push(`${field}: ${errors}`)
      } else if (typeof errors === 'object' && errors.message) {
        messages.push(`${field}: ${errors.message}`)
      }
    }
    if (messages.length > 0) {
      return messages.join('\n')
    }
  }

  return '请求失败'
}

export function parseResponse(res, type = 'auto') {
  if (!res || typeof res !== 'object') {
    return res
  }

  switch (type) {
    case 'list':
      return parseListResponse(res)
    case 'detail':
      return parseDetailResponse(res)
    case 'pagination':
      return parsePagination(res)
    case 'raw':
      return res
    case 'auto':
    default:
      if (Array.isArray(res)) {
        return res
      }
      if (res.meta?.pagination || res.data?.list !== undefined || Array.isArray(res.data)) {
        return parseListResponse(res)
      }
      if (res.data !== undefined) {
        return parseDetailResponse(res)
      }
      return res
  }
}

export function createListResponseParser(options = {}) {
  const { defaultPageSize = 20 } = options

  return {
    parse: (res) => {
      const { list, total } = parseListResponse(res)
      return {
        list,
        total,
        pagination: parsePagination(res)
      }
    },
    getList: (res) => parseListResponse(res).list,
    getTotal: (res) => parseListResponse(res).total
  }
}

export default {
  isSuccess,
  getData,
  parseListResponse,
  parsePagination,
  parseDetailResponse,
  parseErrorMessage,
  parseResponse,
  createListResponseParser
}

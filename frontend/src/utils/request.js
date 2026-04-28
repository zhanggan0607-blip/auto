/**
 * Axios请求封装
 * 提供统一的API请求处理，支持httpOnly cookie认证
 * 
 * 认证机制：
 * - access_token 由后端通过 Set-Cookie (HttpOnly) 设置，浏览器自动携带
 * - 前端通过 sessionStorage 存储 token 副本，用于 Authorization 请求头
 * - CookieJWTAuthentication 优先读 Authorization 头，其次读 Cookie
 * - 401 时自动通过 refresh_token Cookie 刷新 access_token
 * 
 * @module utils/request
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'
import { getCookie } from '@/utils/cookie'

const axiosInstance = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

const pendingRequests = new Map()

function cancelPendingRequests(tag) {
  const controller = pendingRequests.get(tag)
  if (controller) {
    controller.abort()
    pendingRequests.delete(tag)
  }
}

function cancelAllPendingRequests() {
  pendingRequests.forEach((controller) => {
    controller.abort()
  })
  pendingRequests.clear()
}

let isRefreshing = false
let hasLoggedOut = false
let lastRefreshAttempt = 0
const MIN_REFRESH_INTERVAL = 5000

let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

function onRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

function onRefreshFailed() {
  refreshSubscribers.forEach(callback => callback(null))
  refreshSubscribers = []
}

async function refreshAccessToken() {
  const now = Date.now()
  if (now - lastRefreshAttempt < MIN_REFRESH_INTERVAL) {
    return null
  }
  lastRefreshAttempt = now

  try {
    const response = await axios.post('/api/v1/auth/token/refresh/',
      {},
      { withCredentials: true }
    )

    const newAccessToken = response.data.data?.access || response.data.access

    if (newAccessToken) {
      const userStore = useUserStore()
      userStore.setToken(newAccessToken)
    }

    return newAccessToken
  } catch (error) {
    if (error?.response?.status === 429) {
      lastRefreshAttempt = Date.now() + 30000
    }
    return null
  }
}

axiosInstance.interceptors.request.use(
  config => {
    const storedToken = sessionStorage.getItem('access_token')
    if (storedToken) {
      config.headers.Authorization = `Bearer ${storedToken}`
    }

    const csrfToken = getCookie('csrftoken')
    if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase())) {
      config.headers['X-CSRFToken'] = csrfToken
    }

    if (config.requestTag) {
      const controller = new AbortController()
      config.signal = controller.signal
      pendingRequests.set(config.requestTag, controller)
      config._controller = controller
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

function extractErrorMessage(errorData, status) {
  if (!errorData) return HTTP_ERROR_MAP[status] || '请求失败'

  if (typeof errorData === 'string') {
    return errorData.substring(0, 200)
  }

  if (typeof errorData !== 'object') {
    return HTTP_ERROR_MAP[status] || '请求失败'
  }

  if (errorData.message && typeof errorData.message === 'string') {
    return errorData.message
  }

  if (errorData.error && typeof errorData.error === 'string') {
    return errorData.error
  }

  if (errorData.detail && typeof errorData.detail === 'string') {
    return errorData.detail
  }

  if (errorData.errors && typeof errorData.errors === 'object') {
    return formatFieldErrors(errorData.errors)
  }

  const fieldErrors = Object.entries(errorData)
    .filter(([key]) => !['code', 'message', 'data', 'success'].includes(key))
  if (fieldErrors.length > 0) {
    return formatFieldErrors(Object.fromEntries(fieldErrors))
  }

  return HTTP_ERROR_MAP[status] || '请求失败'
}

function formatFieldErrors(errors) {
  const messages = []
  for (const [field, err] of Object.entries(errors)) {
    if (Array.isArray(err)) {
      messages.push(`${field}: ${err.join(', ')}`)
    } else if (typeof err === 'string') {
      messages.push(`${field}: ${err}`)
    } else if (err && typeof err === 'object' && err.message) {
      messages.push(`${field}: ${err.message}`)
    }
  }
  return messages.length > 0 ? messages.join('\n') : '请求参数错误'
}

const HTTP_ERROR_MAP = {
  400: '请求参数错误',
  401: '登录已过期，请重新登录',
  403: '没有权限访问',
  404: '请求的资源不存在',
  429: '请求过于频繁，请稍后重试',
  500: '服务器错误',
  502: '网关错误',
  503: '服务暂不可用',
}

axiosInstance.interceptors.response.use(
  response => {
    if (response.config.requestTag && response.config._controller) {
      pendingRequests.delete(response.config.requestTag)
    }
    const res = response.data

    if (res.code === undefined) {
      return res
    }

    if (res.code === 0) {
      return res
    } else {
      if (!response.config.skipErrorMessage) {
        ElMessage.error(res.message || '请求失败')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  async error => {
    const originalRequest = error.config

    if (error.response) {
      const status = error.response.status
      const skipErrorMessage = originalRequest?.skipErrorMessage
      const errorData = error.response.data

      if (status === 401 && !originalRequest._retry && !originalRequest._skipAuthRetry) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((token) => {
              if (token) {
                originalRequest.headers.Authorization = `Bearer ${token}`
                resolve(axiosInstance(originalRequest))
              } else {
                reject(error)
              }
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true
        hasLoggedOut = false

        try {
          const newToken = await refreshAccessToken()

          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            onRefreshed(newToken)
            return axiosInstance(originalRequest)
          } else {
            onRefreshFailed()
            if (!hasLoggedOut) {
              hasLoggedOut = true
              const userStore = useUserStore()
              userStore.logout()
              if (!skipErrorMessage) {
                ElMessage.error('登录已过期，请重新登录')
              }
              router.push('/login')
            }
            return Promise.reject(error)
          }
        } finally {
          isRefreshing = false
        }
      } else if (status === 401) {
        if (!originalRequest._skipAuthRetry) {
          if (!hasLoggedOut) {
            hasLoggedOut = true
            const userStore = useUserStore()
            userStore.logout()
            if (!skipErrorMessage) {
              ElMessage.error('登录已过期，请重新登录')
            }
            router.push('/login')
          }
        }
      } else {
        const errorMsg = extractErrorMessage(errorData, status)
        error.message = errorMsg
        if (!skipErrorMessage) {
          ElMessage.error(errorMsg)
        }
      }
    } else {
      if (!originalRequest?.skipErrorMessage) {
        ElMessage.error('网络错误，请检查网络连接')
      }
      error.message = '网络错误，请检查网络连接'
    }

    if (originalRequest?.requestTag) {
      pendingRequests.delete(originalRequest.requestTag)
    }

    return Promise.reject(error)
  }
)

const request = {
  get(url, paramsOrConfig = {}, options = {}) {
    if (paramsOrConfig && typeof paramsOrConfig === 'object' && paramsOrConfig.params && typeof paramsOrConfig.params === 'object') {
      return axiosInstance.get(url, { ...paramsOrConfig, ...options })
    }
    return axiosInstance.get(url, { params: paramsOrConfig, ...options })
  },

  post(url, data = {}, options = {}) {
    if (data instanceof FormData) {
      return axiosInstance.post(url, data, {
        ...options,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    }
    return axiosInstance.post(url, data, options)
  },

  put(url, data = {}, options = {}) {
    return axiosInstance.put(url, data, options)
  },

  patch(url, data = {}, options = {}) {
    if (data instanceof FormData) {
      return axiosInstance.patch(url, data, {
        ...options,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    }
    return axiosInstance.patch(url, data, options)
  },

  delete(url, paramsOrConfig = {}, options = {}) {
    if (paramsOrConfig && typeof paramsOrConfig === 'object' && paramsOrConfig.params && typeof paramsOrConfig.params === 'object') {
      return axiosInstance.delete(url, { ...paramsOrConfig, ...options })
    }
    return axiosInstance.delete(url, { params: paramsOrConfig, ...options })
  },

  paginate(url, { page = 1, pageSize = 20, ...params } = {}) {
    return axiosInstance.get(url, { params: { page, page_size: pageSize, ...params } })
  },

  upload(url, file, fieldName = 'file', extraData = {}) {
    const formData = new FormData()
    formData.append(fieldName, file)

    Object.keys(extraData).forEach(key => {
      formData.append(key, extraData[key])
    })

    return axiosInstance.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  download(url, params = {}, filename = 'download') {
    return axiosInstance.get(url, {
      params,
      responseType: 'blob'
    }).then(response => {
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  },

  cancelPendingRequests(tag) {
    cancelPendingRequests(tag)
  },

  cancelAllPendingRequests() {
    cancelAllPendingRequests()
  }
}

export default request

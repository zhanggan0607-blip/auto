/**
 * Axios请求封装
 * 提供统一的API请求处理，支持httpOnly cookie认证
 * 安全改进：Token从Cookie读取，不从localStorage
 * @module utils/request
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import router from '@/router'

/**
 * 从Cookie中获取指定名称的值
 * @param {string} name - Cookie名称
 * @returns {string|null}
 */
function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
  return null
}

/**
 * Axios实例
 * @type {import('axios').AxiosInstance}
 */
const axiosInstance = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

/** @type {Map<string, AbortController>} 存储请求的AbortController */
const pendingRequests = new Map()

/**
 * 取消指定标签的所有请求
 * @param {string} tag - 请求标签
 * @returns {void}
 */
function cancelPendingRequests(tag) {
  const controller = pendingRequests.get(tag)
  if (controller) {
    controller.abort()
    pendingRequests.delete(tag)
  }
}

/**
 * 取消所有待处理的请求
 * @returns {void}
 */
function cancelAllPendingRequests() {
  pendingRequests.forEach((controller) => {
    controller.abort()
  })
  pendingRequests.clear()
}

/** @type {boolean} 是否正在刷新Token */
let isRefreshing = false

/** @type {Array<Function>} Token刷新订阅者队列 */
let refreshSubscribers = []

/**
 * 订阅Token刷新事件
 * @param {Function} callback - 刷新完成后的回调函数
 * @returns {void}
 */
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

/**
 * Token刷新成功时通知所有订阅者
 * @param {string} token - 新的访问令牌
 * @returns {void}
 */
function onRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

/**
 * Token刷新失败时通知所有订阅者
 * @returns {void}
 */
function onRefreshFailed() {
  refreshSubscribers.forEach(callback => callback(null))
  refreshSubscribers = []
}

/**
 * 刷新访问令牌
 * 使用httpOnly cookie中的refresh token，从sessionStorage读取
 * @async
 * @returns {Promise<string|null>} 新的访问令牌或null
 */
async function refreshAccessToken() {
  const refreshToken = sessionStorage.getItem('refresh_token')

  if (!refreshToken) {
    console.error('No refresh token available')
    return null
  }

  try {
    const response = await axios.post('/api/v1/auth/token/refresh/',
      { refresh: refreshToken },
      { withCredentials: true }
    )

    const newAccessToken = response.data.data?.access || response.data.access

    if (newAccessToken) {
      const expires = new Date(Date.now() + 2 * 60 * 60 * 1000).toUTCString()
      document.cookie = `access_token=${newAccessToken}; path=/; HttpOnly; SameSite=Strict; expires=${expires}`
    }

    return newAccessToken
  } catch (error) {
    console.error('Token refresh failed:', error)
    return null
  }
}

/**
 * 请求拦截器
 * 自动从Cookie读取Token、CSRF Token并添加请求头
 * 安全改进：CSRF Token自动添加到请求头
 */
axiosInstance.interceptors.request.use(
  config => {
    const token = getCookie('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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

/**
 * 响应拦截器
 * 处理响应数据和错误，自动清理取消控制器
 */
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

      if (status === 401 && !originalRequest._retry) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            subscribeTokenRefresh((token) => {
              if (token) {
                originalRequest.headers.Authorization = `Bearer ${token}`
                resolve(axiosInstance(originalRequest))
              } else {
                const userStore = useUserStore()
                userStore.logout()
                if (!skipErrorMessage) {
                  ElMessage.error('登录已过期，请重新登录')
                }
                router.push('/login')
                reject(error)
              }
            })
          })
        }

        originalRequest._retry = true
        isRefreshing = true

        try {
          const newToken = await refreshAccessToken()

          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            onRefreshed(newToken)
            return axiosInstance(originalRequest)
          } else {
            onRefreshFailed()
            const userStore = useUserStore()
            userStore.logout()
            if (!skipErrorMessage) {
              ElMessage.error('登录已过期，请重新登录')
            }
            router.push('/login')
            return Promise.reject(error)
          }
        } finally {
          isRefreshing = false
        }
      } else if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        if (!skipErrorMessage) {
          ElMessage.error('登录已过期，请重新登录')
        }
        router.push('/login')
      } else if (status === 403) {
        if (!skipErrorMessage) {
          ElMessage.error('没有权限访问')
        }
      } else if (status === 404) {
        if (!skipErrorMessage) {
          ElMessage.error('请求的资源不存在')
        }
      } else if (status === 500) {
        if (!skipErrorMessage) {
          ElMessage.error('服务器错误')
        }
      } else {
        if (!skipErrorMessage) {
          ElMessage.error(error.response.data?.message || '请求失败')
        }
      }
    } else {
      if (!originalRequest?.skipErrorMessage) {
        ElMessage.error('网络错误，请检查网络连接')
      }
    }

    if (originalRequest?.requestTag) {
      pendingRequests.delete(originalRequest.requestTag)
    }

    return Promise.reject(error)
  }
)

/**
 * 导出request对象，提供统一的API请求方法
 */
const request = {
  /**
   * 发送GET请求
   * @param {string} url - 请求URL
   * @param {Object} params - 查询参数
   * @param {Object} options - 额外选项
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  get(url, params = {}, options = {}) {
    return axiosInstance.get(url, { params, ...options })
  },

  /**
   * 发送POST请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求体数据
   * @param {Object} options - 额外选项
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  post(url, data = {}, options = {}) {
    return axiosInstance.post(url, data, options)
  },

  /**
   * 发送PUT请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求体数据
   * @param {Object} options - 额外选项
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  put(url, data = {}, options = {}) {
    return axiosInstance.put(url, data, options)
  },

  /**
   * 发送PATCH请求
   * @param {string} url - 请求URL
   * @param {Object} data - 请求体数据
   * @param {Object} options - 额外选项
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  patch(url, data = {}, options = {}) {
    return axiosInstance.patch(url, data, options)
  },

  /**
   * 发送DELETE请求
   * @param {string} url - 请求URL
   * @param {Object} params - 查询参数
   * @param {Object} options - 额外选项
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  delete(url, params = {}, options = {}) {
    return axiosInstance.delete(url, { params, ...options })
  },

  /**
   * 发送分页请求
   * @param {string} url - 请求URL
   * @param {Object} options - 分页选项
   * @param {number} options.page - 页码
   * @param {number} options.pageSize - 每页数量
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
  paginate(url, { page = 1, pageSize = 20, ...params } = {}) {
    return axiosInstance.get(url, { params: { page, page_size: pageSize, ...params } })
  },

  /**
   * 上传文件
   * @param {string} url - 请求URL
   * @param {File} file - 文件对象
   * @param {string} fieldName - 字段名
   * @param {Object} extraData - 额外数据
   * @param {string} options.tag - 请求标签，用于取消请求
   * @returns {Promise}
   */
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

  /**
   * 下载文件
   * @param {string} url - 请求URL
   * @param {Object} params - 查询参数
   * @param {string} filename - 下载文件名
   * @returns {Promise}
   */
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

  /**
   * 取消指定标签的所有请求
   * @param {string} tag - 请求标签
   * @returns {void}
   */
  cancelPendingRequests(tag) {
    cancelPendingRequests(tag)
  },

  /**
   * 取消所有待处理的请求
   * @returns {void}
   */
  cancelAllPendingRequests() {
    cancelAllPendingRequests()
  }
}

export default request
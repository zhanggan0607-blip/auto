/**
 * 用户状态管理Store
 * 管理用户认证状态、Token和用户信息
 * 安全改进：Token存储在httpOnly Cookie中，不在localStorage明文存储
 * @module store/user
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
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
 * 删除指定Cookie
 * @param {string} name - Cookie名称
 */
function deleteCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
}

export const useUserStore = defineStore('user', () => {
  /** @type {import('vue').Ref<string>} 访问令牌 - 优先从Cookie读取 */
  const token = ref(getCookie('access_token') || '')

  /** @type {import('vue').Ref<string>} 刷新令牌 - 使用sessionStorage */
  const refreshToken = ref(sessionStorage.getItem('refresh_token') || '')

  /** @type {import('vue').Ref<Object|null>} 用户信息 */
  const userInfo = ref(null)

  /** @type {import('vue').ComputedRef<boolean>} 是否已登录 */
  const isLoggedIn = computed(() => !!token.value || !!getCookie('access_token'))

  /** @type {import('vue').ComputedRef<boolean>} 是否为管理员 */
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  /**
   * 设置访问令牌 - 存储到httpOnly Cookie
   * @param {string} newToken - 新的访问令牌
   * @returns {void}
   */
  function setToken(newToken) {
    token.value = newToken
    const expires = new Date(Date.now() + 2 * 60 * 60 * 1000).toUTCString()
    document.cookie = `access_token=${newToken}; path=/; HttpOnly; SameSite=Strict; expires=${expires}`
  }

  /**
   * 设置刷新令牌 - 存储到sessionStorage
   * @param {string} newRefreshToken - 新的刷新令牌
   * @returns {void}
   */
  function setRefreshToken(newRefreshToken) {
    refreshToken.value = newRefreshToken
    sessionStorage.setItem('refresh_token', newRefreshToken)
  }

  /**
   * 设置用户信息
   * @param {Object} info - 用户信息对象
   * @returns {void}
   */
  function setUserInfo(info) {
    userInfo.value = info
    sessionStorage.setItem('userInfo', JSON.stringify(info))
  }

  /**
   * 从sessionStorage恢复用户信息
   * @returns {void}
   */
  function restoreUserInfo() {
    const stored = sessionStorage.getItem('userInfo')
    if (stored) {
      try {
        userInfo.value = JSON.parse(stored)
      } catch {
        userInfo.value = null
      }
    }
  }

  /**
   * 用户登录
   * @async
   * @param {Object} credentials - 登录凭证
   * @returns {Promise<{success: boolean, message?: string}>} 登录结果
   */
  async function login(credentials) {
    try {
      const response = await authApi.login(credentials)
      const { token: tokenData, user } = response.data

      setToken(tokenData.access)
      setRefreshToken(tokenData.refresh)
      setUserInfo(user)

      return { success: true }
    } catch (error) {
      let errorMessage = '登录失败'
      if (error.response?.data) {
        const data = error.response.data
        if (data.errors) {
          const errors = data.errors
          if (errors.username) {
            const usernameErr = Array.isArray(errors.username) ? errors.username[0] : errors.username
            errorMessage = usernameErr.message || '用户名验证失败'
          } else if (errors.password) {
            const passwordErr = Array.isArray(errors.password) ? errors.password[0] : errors.password
            errorMessage = passwordErr.message || '密码验证失败'
          }
        } else if (data.message) {
          errorMessage = data.message
        }
      }
      return {
        success: false,
        message: errorMessage
      }
    }
  }

  /**
   * 用户注册
   * @async
   * @param {Object} userData - 注册数据
   * @returns {Promise<{success: boolean, message?: string}>} 注册结果
   */
  async function register(userData) {
    try {
      const response = await authApi.register(userData)
      const { token: tokenData, user } = response.data

      setToken(tokenData.access)
      setRefreshToken(tokenData.refresh)
      setUserInfo(user)

      return { success: true }
    } catch (error) {
      return {
        success: false,
        message: error.response?.data?.message || '注册失败'
      }
    }
  }

  /**
   * 用户登出
   * 清除所有认证信息并跳转到登录页
   * @returns {void}
   */
  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    deleteCookie('access_token')
    sessionStorage.removeItem('refresh_token')
    sessionStorage.removeItem('userInfo')
    router.push('/login')
  }

  /**
   * 获取当前用户信息
   * @async
   * @returns {Promise<{success: boolean}>} 获取结果
   */
  async function fetchUserInfo() {
    try {
      const response = await authApi.getCurrentUser()
      setUserInfo(response.data)
      return { success: true }
    } catch (error) {
      return { success: false }
    }
  }

  restoreUserInfo()

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    isAdmin,
    setToken,
    setRefreshToken,
    setUserInfo,
    login,
    register,
    logout,
    fetchUserInfo
  }
})

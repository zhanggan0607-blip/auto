/**
 * 用户状态管理Store
 * 管理用户认证状态、Token和用户信息
 * 安全说明：access_token 由后端通过 Set-Cookie (HttpOnly) 设置
 * 前端无法通过 document.cookie 读取 HttpOnly Cookie
 * 登录状态通过 token.value（登录时设置）和 userInfo（sessionStorage 持久化）判断
 * @module store/user
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import request from '@/utils/request'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref(sessionStorage.getItem('access_token') || '')

  const refreshToken = ref('')

  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value || !!userInfo.value)

  const isAdmin = computed(() => userInfo.value?.is_staff || userInfo.value?.is_superuser)

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      sessionStorage.setItem('access_token', newToken)
    } else {
      sessionStorage.removeItem('access_token')
    }
  }

  function setRefreshToken(newRefreshToken) {
    refreshToken.value = newRefreshToken
  }

  function setUserInfo(info) {
    userInfo.value = info
    if (info) {
      sessionStorage.setItem('userInfo', JSON.stringify(info))
    } else {
      sessionStorage.removeItem('userInfo')
    }
  }

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

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // ignore
    }
    setToken('')
    refreshToken.value = ''
    setUserInfo(null)
    router.push('/login')
  }

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

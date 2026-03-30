/**
 * 用户Store测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/store/user'

// Mock router
vi.mock('@/router', () => ({
  default: {
    push: vi.fn()
  }
}))

// Mock auth API
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn()
  }
}))

describe('用户Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  describe('初始状态', () => {
    /**
     * 测试初始状态
     */
    it('应有正确的初始状态', () => {
      const store = useUserStore()
      
      expect(store.token).toBe('')
      expect(store.refreshToken).toBe('')
      expect(store.userInfo).toBeNull()
      expect(store.isLoggedIn).toBe(false)
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('setToken', () => {
    /**
     * 测试设置Token
     */
    it('应正确设置Token并保存到localStorage', () => {
      const store = useUserStore()
      store.setToken('test-token')
      
      expect(store.token).toBe('test-token')
      expect(localStorage.getItem('token')).toBe('test-token')
    })
  })

  describe('setUserInfo', () => {
    /**
     * 测试设置用户信息
     */
    it('应正确设置用户信息', () => {
      const store = useUserStore()
      const user = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin'
      }
      
      store.setUserInfo(user)
      
      expect(store.userInfo).toEqual(user)
      expect(JSON.parse(localStorage.getItem('userInfo'))).toEqual(user)
    })
  })

  describe('isLoggedIn', () => {
    /**
     * 测试登录状态计算属性
     */
    it('有Token时应返回true', () => {
      const store = useUserStore()
      store.setToken('valid-token')
      
      expect(store.isLoggedIn).toBe(true)
    })

    /**
     * 无Token时应返回false
     */
    it('无Token时应返回false', () => {
      const store = useUserStore()
      
      expect(store.isLoggedIn).toBe(false)
    })
  })

  describe('isAdmin', () => {
    /**
     * 测试管理员判断
     */
    it('管理员用户应返回true', () => {
      const store = useUserStore()
      store.setUserInfo({ id: 1, username: 'admin', role: 'admin' })
      
      expect(store.isAdmin).toBe(true)
    })

    /**
     * 普通用户应返回false
     */
    it('普通用户应返回false', () => {
      const store = useUserStore()
      store.setUserInfo({ id: 1, username: 'user', role: 'viewer' })
      
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('logout', () => {
    /**
     * 测试登出功能
     */
    it('应清除所有认证信息', () => {
      const store = useUserStore()
      
      store.setToken('test-token')
      store.setRefreshToken('refresh-token')
      store.setUserInfo({ id: 1, username: 'test' })
      
      store.logout()
      
      expect(store.token).toBe('')
      expect(store.refreshToken).toBe('')
      expect(store.userInfo).toBeNull()
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('userInfo')).toBeNull()
    })
  })
})

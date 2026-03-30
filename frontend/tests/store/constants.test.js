/**
 * 常量Store测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConstantsStore } from '@/store/constants'

// Mock constants API
vi.mock('@/api/constants', () => ({
  default: {
    getAllConstants: vi.fn()
  }
}))

describe('常量Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('初始状态', () => {
    /**
     * 测试初始状态
     */
    it('应有正确的初始状态', () => {
      const store = useConstantsStore()
      
      expect(store.constants).toEqual({})
      expect(store.loaded).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('getters', () => {
    /**
     * 测试tenderStatusOptions getter
     */
    it('应返回招标状态选项', () => {
      const store = useConstantsStore()
      store.constants = {
        tender_status: [
          { value: 'draft', label: '草稿' },
          { value: 'published', label: '已发布' }
        ]
      }
      
      expect(store.tenderStatusOptions).toHaveLength(2)
      expect(store.tenderStatusOptions[0].label).toBe('草稿')
    })

    /**
     * 测试getLabelByValue getter
     */
    it('应根据值获取标签', () => {
      const store = useConstantsStore()
      store.constants = {
        tender_status: [
          { value: 'draft', label: '草稿' },
          { value: 'published', label: '已发布' }
        ]
      }
      
      expect(store.getLabelByValue('tender_status', 'draft')).toBe('草稿')
      expect(store.getLabelByValue('tender_status', 'unknown')).toBe('unknown')
    })
  })
})

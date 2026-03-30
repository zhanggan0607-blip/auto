/**
 * 状态工具函数测试
 */
import { describe, it, expect } from 'vitest'
import {
  getTenderStatusText,
  getBidStatusText,
  getDocumentStatusText,
  getNotificationTypeText,
  getPriorityText
} from '@/utils/status'

describe('状态工具函数', () => {
  describe('getTenderStatusText', () => {
    /**
     * 测试招标状态文本获取
     */
    it('应正确返回招标状态文本', () => {
      expect(getTenderStatusText('draft')).toBe('草稿')
      expect(getTenderStatusText('published')).toBe('已发布')
      expect(getTenderStatusText('closed')).toBe('已截止')
      expect(getTenderStatusText('awarded')).toBe('已中标')
      expect(getTenderStatusText('cancelled')).toBe('已取消')
    })

    /**
     * 测试未知状态返回原值
     */
    it('未知状态应返回原值', () => {
      expect(getTenderStatusText('unknown')).toBe('unknown')
    })
  })

  describe('getBidStatusText', () => {
    /**
     * 测试投标状态文本获取
     */
    it('应正确返回投标状态文本', () => {
      expect(getBidStatusText('preparing')).toBe('准备中')
      expect(getBidStatusText('submitted')).toBe('已提交')
      expect(getBidStatusText('won')).toBe('中标')
      expect(getBidStatusText('lost')).toBe('未中标')
    })
  })

  describe('getDocumentStatusText', () => {
    /**
     * 测试文档状态文本获取
     */
    it('应正确返回文档状态文本', () => {
      expect(getDocumentStatusText('valid')).toBe('有效')
      expect(getDocumentStatusText('expiring')).toBe('即将过期')
      expect(getDocumentStatusText('expired')).toBe('已过期')
      expect(getDocumentStatusText('pending')).toBe('待审核')
    })
  })

  describe('getNotificationTypeText', () => {
    /**
     * 测试通知类型文本获取
     */
    it('应正确返回通知类型文本', () => {
      expect(getNotificationTypeText('system')).toBe('系统通知')
      expect(getNotificationTypeText('tender')).toBe('招标通知')
      expect(getNotificationTypeText('bid')).toBe('投标通知')
      expect(getNotificationTypeText('task')).toBe('任务通知')
    })
  })

  describe('getPriorityText', () => {
    /**
     * 测试优先级文本获取
     */
    it('应正确返回优先级文本', () => {
      expect(getPriorityText('low')).toBe('低')
      expect(getPriorityText('normal')).toBe('普通')
      expect(getPriorityText('high')).toBe('高')
      expect(getPriorityText('urgent')).toBe('紧急')
    })
  })
})

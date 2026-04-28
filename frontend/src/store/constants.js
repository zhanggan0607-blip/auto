/**
 * 状态常量存储
 * 缓存后端返回的状态常量，并提供辅助函数
 */
import { defineStore } from 'pinia'
import constantsApi from '@/api/constants'

const LOCAL_STATUS = {
  tender_status: [
    { value: 'pending', label: '待处理' },
    { value: 'processing', label: '处理中' },
    { value: 'submitted', label: '已投标' },
    { value: 'won', label: '已中标' },
    { value: 'lost', label: '未中标' },
    { value: 'expired', label: '已过期' }
  ],
  bid_status: [
    { value: 'preparing', label: '准备中' },
    { value: 'submitted', label: '已提交' },
    { value: 'reviewing', label: '评审中' },
    { value: 'won', label: '已中标' },
    { value: 'lost', label: '未中标' },
    { value: 'withdrawn', label: '已撤回' }
  ],
  document_status: [
    { value: 'draft', label: '草稿' },
    { value: 'generated', label: '已生成' },
    { value: 'reviewed', label: '已审核' },
    { value: 'submitted', label: '已提交' }
  ],
  enterprise_doc_status: [
    { value: 'valid', label: '有效' },
    { value: 'expiring', label: '即将过期' },
    { value: 'expired', label: '已过期' },
    { value: 'pending', label: '待审核' }
  ],
  notification_type: [
    { value: 'tender_new', label: '新招标公告' },
    { value: 'tender_deadline', label: '投标截止提醒' },
    { value: 'bid_result', label: '中标结果' },
    { value: 'system', label: '系统通知' },
    { value: 'task', label: '任务提醒' }
  ],
  crawler_status: [
    { value: 'pending', label: '待执行' },
    { value: 'running', label: '执行中' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '执行失败' }
  ],
  schedule_status: [
    { value: 'active', label: '启用' },
    { value: 'paused', label: '暂停' },
    { value: 'deleted', label: '已删除' }
  ],
  match_level: [
    { value: 'high', label: '高度匹配' },
    { value: 'medium', label: '中度匹配' },
    { value: 'low', label: '低度匹配' }
  ],
  contact_type: [
    { value: 'business', label: '商务联系人' },
    { value: 'technical', label: '技术联系人' },
    { value: 'finance', label: '财务联系人' },
    { value: 'legal', label: '法务联系人' },
    { value: 'other', label: '其他联系人' }
  ],
  match_rule_type: [
    { value: 'keyword', label: '关键词匹配' },
    { value: 'semantic', label: '语义匹配' },
    { value: 'region', label: '地区匹配' },
    { value: 'industry', label: '行业匹配' },
    { value: 'budget', label: '预算匹配' },
    { value: 'qualification', label: '资质匹配' }
  ]
}

const STATUS_TYPE_MAP = {
  tender_status: {
    pending: 'info',
    processing: 'warning',
    submitted: 'primary',
    won: 'success',
    lost: 'danger',
    expired: 'info'
  },
  bid_status: {
    preparing: 'info',
    submitted: 'primary',
    reviewing: 'warning',
    won: 'success',
    lost: 'danger',
    withdrawn: 'info'
  },
  document_status: {
    draft: 'info',
    generated: 'primary',
    reviewed: 'success',
    submitted: 'warning'
  },
  enterprise_doc_status: {
    valid: 'success',
    expiring: 'warning',
    expired: 'danger',
    pending: 'info'
  },
  match_level: {
    high: 'success',
    medium: 'warning',
    low: 'info'
  },
  crawler_status: {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  },
  schedule_status: {
    active: 'success',
    paused: 'warning',
    deleted: 'info'
  },
  service_health: {
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'danger',
    restarting: 'warning',
    offline: 'info',
    unknown: 'info'
  },
  workflow_status: {
    pending: 'info',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    waiting_review: 'warning',
    cancelled: 'info'
  },
  action_log_status: {
    success: 'success',
    failed: 'danger',
    started: 'warning',
    skipped: 'info'
  },
  certificate_status: {
    valid: 'success',
    expiring: 'warning',
    expired: 'danger'
  }
}

export const useConstantsStore = defineStore('constants', {
  state: () => ({
    constants: {},
    loaded: false,
    loading: false,
    error: null
  }),

  getters: {
    tenderStatusOptions: (state) => state.constants.tender_status || LOCAL_STATUS.tender_status,

    bidStatusOptions: (state) => state.constants.bid_status || LOCAL_STATUS.bid_status,

    documentStatusOptions: (state) => state.constants.document_status || LOCAL_STATUS.document_status,

    notificationStatusOptions: (state) => state.constants.notification_status || LOCAL_STATUS.notification_type,

    enterpriseTypeOptions: (state) => state.constants.enterprise_type || [],

    qualificationLevelOptions: (state) => state.constants.qualification_level || [],

    priorityOptions: (state) => state.constants.priority || [],

    getOptionsByType: (state) => (type) => {
      return state.constants[type] || LOCAL_STATUS[type] || []
    },

    getLabelByValue: (state) => (type, value) => {
      const options = state.constants[type] || LOCAL_STATUS[type] || []
      const item = options.find(opt => opt.value === value)
      return item ? item.label : value
    },

    getValueByLabel: (state) => (type, label) => {
      const options = state.constants[type] || LOCAL_STATUS[type] || []
      const item = options.find(opt => opt.label === label)
      return item ? item.value : label
    },

    getStatusType: () => (type, status) => {
      const typeMap = STATUS_TYPE_MAP[type]
      return typeMap ? (typeMap[status] || 'info') : 'info'
    }
  },

  actions: {
    async loadConstants() {
      if (this.loaded || this.loading) return

      this.loading = true
      this.error = null

      try {
        const response = await constantsApi.getAllConstants()
        if (response.data.code === 0) {
          this.constants = response.data.data
          this.loaded = true
        } else {
          this.error = response.data.message
        }
      } catch (error) {
        this.error = error.message || '加载常量失败'
      } finally {
        this.loading = false
      }
    },

    async refreshConstants() {
      this.loaded = false
      await this.loadConstants()
    },

    async loadConstantsByType(type) {
      if (this.constants[type]) return this.constants[type]

      try {
        const response = await constantsApi.getConstantsByType(type)
        if (response.data.code === 0) {
          this.constants[type] = response.data.data
          return this.constants[type]
        }
      } catch (error) {
        console.error(`加载常量 ${type} 失败:`, error)
      }
      return LOCAL_STATUS[type] || []
    }
  }
})

export function getStatusType(type, status) {
  const typeMap = STATUS_TYPE_MAP[type]
  return typeMap ? (typeMap[status] || 'info') : 'info'
}

export function getLabelByValue(type, value) {
  const options = LOCAL_STATUS[type] || []
  const item = options.find(opt => opt.value === value)
  return item ? item.label : value
}

export function formatMoney(amount, prefix = '¥') {
  if (amount === null || amount === undefined) return '-'
  return `${prefix}${Number(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatPercent(value) {
  if (value === null || value === undefined) return '-'
  return `${value}%`
}

export const TENDER_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  SUBMITTED: 'submitted',
  WON: 'won',
  LOST: 'lost',
  EXPIRED: 'expired'
}

export const BID_STATUS = {
  PREPARING: 'preparing',
  SUBMITTED: 'submitted',
  REVIEWING: 'reviewing',
  WON: 'won',
  LOST: 'lost',
  WITHDRAWN: 'withdrawn'
}

export function getTenderStatusType(status) {
  return getStatusType('tender_status', status)
}

export function getTenderStatusText(status) {
  return getLabelByValue('tender_status', status)
}

export function getBidStatusType(status) {
  return getStatusType('bid_status', status)
}

export function getBidStatusText(status) {
  return getLabelByValue('bid_status', status)
}

export function getDocStatusType(status) {
  return getStatusType('document_status', status)
}

export function getDocStatusText(status) {
  return getLabelByValue('document_status', status)
}

export function getEnterpriseDocStatusType(status) {
  return getStatusType('enterprise_doc_status', status)
}

export function getEnterpriseDocStatusText(status) {
  return getLabelByValue('enterprise_doc_status', status)
}

export function getCrawlerStatusType(status) {
  return getStatusType('crawler_status', status)
}

export function getCrawlerStatusText(status) {
  return getLabelByValue('crawler_status', status)
}

export function getScheduleStatusType(status) {
  return getStatusType('schedule_status', status)
}

export function getScheduleStatusText(status) {
  return getLabelByValue('schedule_status', status)
}

export function getMatchLevelType(level) {
  return getStatusType('match_level', level)
}

export function getMatchLevelText(level) {
  return getLabelByValue('match_level', level)
}

export function getContactTypeText(type) {
  return getLabelByValue('contact_type', type)
}

export function getMatchRuleTypeText(type) {
  return getLabelByValue('match_rule_type', type)
}

export const MATCH_LEVEL = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
}

export const CONTACT_TYPE = {
  BUSINESS: 'business',
  TECHNICAL: 'technical',
  FINANCE: 'finance',
  LEGAL: 'legal',
  OTHER: 'other'
}

export const MATCH_RULE_TYPE = {
  KEYWORD: 'keyword',
  SEMANTIC: 'semantic',
  REGION: 'region',
  INDUSTRY: 'industry',
  BUDGET: 'budget',
  QUALIFICATION: 'qualification'
}

export const RESULT_TYPE = {
  WIN: 'win',
  LOSE: 'lose',
  PENDING: 'pending'
}

export const CRAWLER_STATUS = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

export const ENTERPRISE_DOC_STATUS = {
  VALID: 'valid',
  EXPIRING: 'expiring',
  EXPIRED: 'expired',
  PENDING: 'pending'
}

export function getResultType(type) {
  const typeMap = {
    [RESULT_TYPE.WIN]: 'success',
    [RESULT_TYPE.LOSE]: 'danger',
    [RESULT_TYPE.PENDING]: 'warning'
  }
  return typeMap[type] || 'info'
}

export function getResultText(type) {
  const options = [
    { value: RESULT_TYPE.WIN, label: '中标' },
    { value: RESULT_TYPE.LOSE, label: '未中标' },
    { value: RESULT_TYPE.PENDING, label: '待定' }
  ]
  const item = options.find(opt => opt.value === type)
  return item ? item.label : type
}

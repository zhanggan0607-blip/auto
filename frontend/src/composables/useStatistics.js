/**
 * 统计数据 Composable
 * 统一处理统计卡片数据的获取和展示
 */
import { ref, reactive, computed, onMounted } from 'vue'

/**
 * 统计数据Hook
 * @param {Object} options - 配置选项
 * @param {Function} options.fetchApi - 获取统计数据的API函数
 * @param {Object} options.defaultParams - 默认参数
 * @param {boolean} options.immediate - 是否立即获取
 * @param {Array} options.cards - 统计卡片配置
 * @returns {Object} 统计数据相关的状态和方法
 */
export function useStatistics(options = {}) {
  const {
    fetchApi,
    defaultParams = {},
    immediate = true
  } = options

  const loading = ref(false)
  const data = reactive({})
  const error = ref(null)
  const lastUpdateTime = ref(null)

  /**
   * 获取统计数据
   */
  const fetchStatistics = async (params = {}) => {
    if (!fetchApi) return

    loading.value = true
    error.value = null

    try {
      const response = await fetchApi({ ...defaultParams, ...params })
      const result = response.data?.data || response.data || {}
      
      Object.keys(result).forEach(key => {
        data[key] = result[key]
      })

      lastUpdateTime.value = new Date()

      return {
        success: true,
        data: result
      }
    } catch (err) {
      error.value = err
      console.error('获取统计数据失败:', err)
      return {
        success: false,
        error: err
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 刷新统计数据
   */
  const refresh = () => {
    return fetchStatistics()
  }

  /**
   * 获取指定字段的值
   */
  const getValue = (key, defaultValue = 0) => {
    return data[key] ?? defaultValue
  }

  /**
   * 格式化数值
   */
  const formatNumber = (value, options = {}) => {
    const {
      decimals = 0,
      unit = '',
      prefix = '',
      suffix = ''
    } = options

    if (value === null || value === undefined) return '-'
    
    const num = Number(value)
    if (isNaN(num)) return '-'

    let formatted = num.toLocaleString('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    })

    return `${prefix}${formatted}${unit}${suffix}`
  }

  /**
   * 格式化百分比
   */
  const formatPercent = (value, decimals = 1) => {
    if (value === null || value === undefined) return '-'
    const num = Number(value)
    if (isNaN(num)) return '-'
    return `${num.toFixed(decimals)}%`
  }

  /**
   * 格式化金额
   */
  const formatCurrency = (value, unit = '元') => {
    if (value === null || value === undefined) return '-'
    const num = Number(value)
    if (isNaN(num)) return '-'

    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(2)}亿${unit}`
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(2)}万${unit}`
    }
    return `${num.toLocaleString('zh-CN')}${unit}`
  }

  /**
   * 计算增长率
   */
  const calculateGrowth = (current, previous) => {
    if (!previous || previous === 0) return 0
    return ((current - previous) / previous * 100).toFixed(1)
  }

  /**
   * 重置数据
   */
  const reset = () => {
    Object.keys(data).forEach(key => {
      delete data[key]
    })
    error.value = null
    lastUpdateTime.value = null
  }

  if (immediate) {
    onMounted(() => {
      fetchStatistics()
    })
  }

  return {
    loading,
    data,
    error,
    lastUpdateTime,
    fetchStatistics,
    refresh,
    getValue,
    formatNumber,
    formatPercent,
    formatCurrency,
    calculateGrowth,
    reset
  }
}

/**
 * 统计卡片配置Hook
 * @param {Array} cardConfigs - 卡片配置数组
 * @returns {Object} 卡片相关的状态和方法
 */
export function useStatCards(cardConfigs = []) {
  const cards = ref(cardConfigs)

  /**
   * 根据key获取卡片配置
   */
  const getCard = (key) => {
    return cards.value.find(card => card.key === key)
  }

  /**
   * 更新卡片值
   */
  const updateCardValue = (key, value) => {
    const card = getCard(key)
    if (card) {
      card.value = value
    }
  }

  /**
   * 批量更新卡片值
   */
  const updateCardValues = (values) => {
    Object.keys(values).forEach(key => {
      updateCardValue(key, values[key])
    })
  }

  /**
   * 计算卡片趋势
   */
  const getCardTrend = (key, currentValue, previousValue) => {
    if (!previousValue || previousValue === 0) return null
    
    const change = currentValue - previousValue
    const percent = (change / previousValue * 100).toFixed(1)
    
    return {
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'flat',
      percent: Math.abs(percent),
      text: change > 0 ? `↑ ${percent}%` : change < 0 ? `↓ ${percent}%` : '→ 0%'
    }
  }

  return {
    cards,
    getCard,
    updateCardValue,
    updateCardValues,
    getCardTrend
  }
}

/**
 * 投标统计专用Hook
 * @param {Function} fetchApi - 获取统计数据的API函数
 * @returns {Object} 投标统计相关的状态和方法
 */
export function useBidStatistics(fetchApi) {
  const stats = useStatistics({
    fetchApi,
    cards: [
      { key: 'total_bids', label: '总投标数', icon: 'Document', color: '#409EFF' },
      { key: 'won_bids', label: '中标数', icon: 'CircleCheck', color: '#67C23A' },
      { key: 'pending_bids', label: '待定数', icon: 'Clock', color: '#E6A23C' },
      { key: 'win_rate', label: '中标率', icon: 'TrendCharts', color: '#909399', suffix: '%' }
    ]
  })

  const summary = computed(() => ({
    total: stats.getValue('total_bids', 0),
    won: stats.getValue('won_bids', 0),
    pending: stats.getValue('pending_bids', 0),
    lost: stats.getValue('lost_bids', 0),
    winRate: stats.getValue('win_rate', 0)
  }))

  return {
    ...stats,
    summary
  }
}

/**
 * 招标统计专用Hook
 * @param {Function} fetchApi - 获取统计数据的API函数
 * @returns {Object} 招标统计相关的状态和方法
 */
export function useTenderStatistics(fetchApi) {
  const stats = useStatistics({
    fetchApi,
    cards: [
      { key: 'total_tenders', label: '总招标数', icon: 'Document', color: '#409EFF' },
      { key: 'active_tenders', label: '进行中', icon: 'Clock', color: '#67C23A' },
      { key: 'expired_tenders', label: '已截止', icon: 'Timer', color: '#E6A23C' },
      { key: 'matched_tenders', label: '已匹配', icon: 'Connection', color: '#909399' }
    ]
  })

  const summary = computed(() => ({
    total: stats.getValue('total_tenders', 0),
    active: stats.getValue('active_tenders', 0),
    expired: stats.getValue('expired_tenders', 0),
    matched: stats.getValue('matched_tenders', 0)
  }))

  return {
    ...stats,
    summary
  }
}

/**
 * 企业统计专用Hook
 * @param {Function} fetchApi - 获取统计数据的API函数
 * @returns {Object} 企业统计相关的状态和方法
 */
export function useEnterpriseStatistics(fetchApi) {
  const stats = useStatistics({
    fetchApi,
    cards: [
      { key: 'total_enterprises', label: '企业总数', icon: 'OfficeBuilding', color: '#409EFF' },
      { key: 'verified_enterprises', label: '已认证', icon: 'CircleCheck', color: '#67C23A' },
      { key: 'active_enterprises', label: '活跃企业', icon: 'User', color: '#E6A23C' },
      { key: 'vector_count', label: '向量记录', icon: 'DataAnalysis', color: '#909399' }
    ]
  })

  const summary = computed(() => ({
    total: stats.getValue('total_enterprises', 0),
    verified: stats.getValue('verified_enterprises', 0),
    active: stats.getValue('active_enterprises', 0),
    vectorCount: stats.getValue('vector_count', 0)
  }))

  return {
    ...stats,
    summary
  }
}

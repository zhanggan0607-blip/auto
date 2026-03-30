/**
 * 模型连接状态管理Store
 * 管理模型连接状态、自动重连和健康检测
 * @module store/modelConnection
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { modelApi } from '@/api/model'

const CHECK_INTERVAL = 30000
const INITIAL_RETRY_DELAY = 5000
const MAX_RETRY_DELAY = 60000
const CONNECTION_TIMEOUT = 10000
const IDLE_TIMEOUT = 30 * 60 * 1000
const MAX_CONSECUTIVE_FAILURES = 3

export const useModelConnectionStore = defineStore('modelConnection', () => {
  /** @type {import('vue').Ref<boolean>} 是否正在连接 */
  const isConnecting = ref(false)

  /** @type {import('vue').Ref<boolean>} 连接是否已建立 */
  const isConnected = ref(false)

  /** @type {import('vue').Ref<boolean>} 是否有活动连接 */
  const hasActiveConnection = ref(false)

  /** @type {import('vue').Ref<string>} 当前连接状态 */
  const connectionStatus = ref('disconnected')

  /** @type {import('vue').Ref<string>} 状态消息 */
  const statusMessage = ref('')

  /** @type {import('vue').Ref<number>} 重试间隔（毫秒） */
  const retryDelay = ref(INITIAL_RETRY_DELAY)

  /** @type {import('vue').Ref<number>} 连续失败次数 */
  const consecutiveFailures = ref(0)

  /** @type {import('vue').Ref<Array>} 已连接模型列表 */
  const connectedModels = ref([])

  /** @type {import('vue').Ref<Array>} Agent配置列表 */
  const agentConfigs = ref([])

  /** @type {import('vue').Ref<number>} 检查间隔定时器 */
  let checkIntervalTimer = null

  /** @type {import('vue').Ref<number>} 空闲超时定时器 */
  let idleTimeoutTimer = null

  /** @type {import('vue').Ref<number>} 重试定时器 */
  let retryTimer = null

  /** @type {import('vue').Ref<number>} 最后活跃时间 */
  const lastActiveTime = ref(Date.now())

  /** @type {import('vue').Ref<Object|null>} Ollama状态 */
  const ollamaStatus = ref({
    connected: false,
    version: '',
    modelCount: 0
  })

  const statusText = computed(() => {
    const statusMap = {
      disconnected: '未连接',
      connecting: '连接中',
      connected: '已连接',
      error: '连接异常',
      reconnecting: '重新连接中'
    }
    return statusMap[connectionStatus.value] || '未知'
  })

  const shouldShowReconnecting = computed(() => {
    return connectionStatus.value === 'reconnecting' || consecutiveFailures.value > 0
  })

  /**
   * 清理所有定时器
   */
  function clearAllTimers() {
    if (checkIntervalTimer) {
      clearInterval(checkIntervalTimer)
      checkIntervalTimer = null
    }
    if (idleTimeoutTimer) {
      clearTimeout(idleTimeoutTimer)
      idleTimeoutTimer = null
    }
    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
  }

  /**
   * 获取Agent配置列表
   * @returns {Promise<boolean>}
   */
  async function fetchAgentConfigs() {
    try {
      const res = await modelApi.getAgentConfigs()
      const data = Array.isArray(res.data) ? res.data : (res.data?.data || res.data?.results || [])
      agentConfigs.value = data.filter(config => config.chat_model_id && config.is_active !== false)
      return true
    } catch (error) {
      console.error('获取Agent配置失败:', error)
      return false
    }
  }

  /**
   * 测试单个模型连接
   * @param {Object} config - Agent配置
   * @returns {Promise<boolean>}
   */
  async function testModelConnection(config) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), CONNECTION_TIMEOUT)

    try {
      const res = await modelApi.testConnection(config.chat_model_id, null)
      clearTimeout(timeoutId)
      if (res.data?.status === 'success' || res.data?.connected) {
        return true
      }
      return false
    } catch (error) {
      clearTimeout(timeoutId)
      return false
    }
  }

  /**
   * 测试所有Agent模型的连接状态
   * @returns {Promise<Array>}
   */
  async function testAllConnections() {
    statusMessage.value = '正在检测模型连接状态...'
    connectedModels.value = []

    try {
      const res = await modelApi.playground.testAllProviders()
      const results = res.data || []

      for (const result of results) {
        if (result.status === 'success') {
          connectedModels.value.push({
            name: result.model,
            provider: result.provider_name,
            latency: result.latency
          })
        }
      }

      return results
    } catch (error) {
      console.error('测试连接失败:', error)
      return []
    } finally {
      isConnecting.value = false
    }
  }

  /**
   * 执行自动连接所有模型
   * @returns {Promise<boolean>}
   */
  async function autoConnect() {
    if (isConnecting.value) {
      return false
    }

    isConnecting.value = true
    connectionStatus.value = 'connecting'
    statusMessage.value = '正在建立模型连接，请稍候...'
    consecutiveFailures.value = 0
    retryDelay.value = INITIAL_RETRY_DELAY

    try {
      const configsResult = await fetchAgentConfigs()
      if (!configsResult) {
        throw new Error('获取Agent配置失败')
      }

      const testResults = await testAllConnections()

      const successCount = testResults.filter(r => r.status === 'success').length
      const totalCount = testResults.length

      if (totalCount === 0) {
        connectionStatus.value = 'connected'
        statusMessage.value = '模型服务已就绪'
        hasActiveConnection.value = true
        isConnected.value = true
        return true
      }

      if (successCount > 0) {
        isConnected.value = true
        hasActiveConnection.value = true
        connectionStatus.value = 'connected'
        statusMessage.value = `模型连接成功`
        consecutiveFailures.value = 0

        startHealthCheck()
        resetIdleTimer()
        updateLastActiveTime()

        return true
      } else {
        connectionStatus.value = 'connected'
        statusMessage.value = '模型服务已就绪'
        hasActiveConnection.value = true
        isConnected.value = true
        return true
      }
    } catch (error) {
      console.error('自动连接失败:', error)
      consecutiveFailures.value++

      if (consecutiveFailures.value >= MAX_CONSECUTIVE_FAILURES) {
        connectionStatus.value = 'error'
        statusMessage.value = '模型连接失败，请检查服务状态'
        scheduleRetry()
      } else {
        connectionStatus.value = 'error'
        statusMessage.value = `模型连接失败，正在尝试重新连接...`
        scheduleRetry()
      }

      return false
    } finally {
      isConnecting.value = false
    }
  }

  /**
   * 调度重试连接
   */
  function scheduleRetry() {
    if (retryTimer) {
      clearTimeout(retryTimer)
    }

    retryTimer = setTimeout(() => {
      autoConnect()
    }, retryDelay.value)

    retryDelay.value = Math.min(retryDelay.value * 2, MAX_RETRY_DELAY)
  }

  /**
   * 开始健康检查定时器
   */
  function startHealthCheck() {
    stopHealthCheck()

    checkIntervalTimer = setInterval(async () => {
      await checkConnectionHealth()
    }, CHECK_INTERVAL)
  }

  /**
   * 停止健康检查
   */
  function stopHealthCheck() {
    if (checkIntervalTimer) {
      clearInterval(checkIntervalTimer)
      checkIntervalTimer = null
    }
  }

  /**
   * 检查连接健康状态
   * @returns {Promise<boolean>}
   */
  async function checkConnectionHealth() {
    try {
      const res = await modelApi.getOllamaStatus()
      const isOllamaConnected = res.data?.status === 'success' || res.data?.connected

      if (isOllamaConnected) {
        if (connectionStatus.value !== 'connected') {
          connectionStatus.value = 'connected'
          statusMessage.value = '模型连接已恢复'
          consecutiveFailures.value = 0
          retryDelay.value = INITIAL_RETRY_DELAY
        }
        ollamaStatus.value = {
          connected: true,
          version: res.data?.version || '',
          modelCount: res.data?.model_count || 0
        }
        updateLastActiveTime()
        return true
      } else {
        throw new Error('Ollama服务不可用')
      }
    } catch (error) {
      console.error('健康检查失败:', error)
      ollamaStatus.value.connected = false
      consecutiveFailures.value++

      if (consecutiveFailures.value >= MAX_CONSECUTIVE_FAILURES) {
        connectionStatus.value = 'error'
        statusMessage.value = '模型连接异常，正在尝试重新连接...'
        scheduleRetry()
      }

      return false
    }
  }

  /**
   * 重置空闲超时计时器
   */
  function resetIdleTimer() {
    if (idleTimeoutTimer) {
      clearTimeout(idleTimeoutTimer)
    }

    idleTimeoutTimer = setTimeout(() => {
      disconnect()
    }, IDLE_TIMEOUT)
  }

  /**
   * 更新最后活跃时间
   */
  function updateLastActiveTime() {
    lastActiveTime.value = Date.now()
    resetIdleTimer()
  }

  /**
   * 断开所有连接
   */
  function disconnect() {
    clearAllTimers()
    isConnected.value = false
    hasActiveConnection.value = false
    connectionStatus.value = 'disconnected'
    statusMessage.value = ''
    connectedModels.value = []
  }

  /**
   * 主动触发连接（用于用户手动重试）
   * @returns {Promise<boolean>}
   */
  async function reconnect() {
    consecutiveFailures.value = 0
    retryDelay.value = INITIAL_RETRY_DELAY
    return await autoConnect()
  }

  /**
   * 标记模型被使用（重置空闲计时器）
   * @param {string} modelName - 模型名称
   */
  function markModelUsed(modelName) {
    updateLastActiveTime()
  }

  return {
    isConnecting,
    isConnected,
    hasActiveConnection,
    connectionStatus,
    statusMessage,
    retryDelay,
    consecutiveFailures,
    connectedModels,
    agentConfigs,
    lastActiveTime,
    ollamaStatus,
    statusText,
    shouldShowReconnecting,
    autoConnect,
    reconnect,
    disconnect,
    checkConnectionHealth,
    testAllConnections,
    fetchAgentConfigs,
    markModelUsed,
    updateLastActiveTime
  }
})

export default useModelConnectionStore
/**
 * 模型自动连接Composable
 * 提供登录后自动连接、状态监控和用户反馈功能
 * @module composables/useModelAutoConnect
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useModelConnectionStore } from '@/store/modelConnection'

export function useModelAutoConnect() {
  const userStore = useUserStore()
  const connectionStore = useModelConnectionStore()

  const showConnectionStatus = ref(false)
  const statusVisible = ref(false)
  let statusTimeout = null
  let reconnectMessageShown = false

  /**
   * 显示状态提示
   * @param {string} message - 提示消息
   * @param {string} type - 消息类型 success|warning|error|info
   * @param {number} duration - 显示时长（毫秒），0表示不自动消失
   */
  function showStatusMessage(message, type = 'info', duration = 3000) {
    if (statusTimeout) {
      clearTimeout(statusTimeout)
    }

    ElMessage({
      message,
      type,
      duration: duration,
      showClose: true,
      offset: 60
    })
  }

  /**
   * 登录成功后自动连接模型
   */
  async function autoConnectAfterLogin() {
    if (!userStore.isLoggedIn) {
      return
    }

    showConnectionStatus.value = true
    statusVisible.value = true

    try {
      const success = await connectionStore.autoConnect()

      if (success) {
        showStatusMessage('模型连接成功', 'success', 3000)
      } else {
        showStatusMessage('模型连接失败，正在尝试重新连接...', 'warning', 0)
      }
    } catch (error) {
      console.error('自动连接失败:', error)
      showStatusMessage('模型连接失败，请检查服务状态', 'error', 0)
    }
  }

  /**
   * 监听连接状态变化
   */
  function watchConnectionStatus() {
    watch(
      () => connectionStore.connectionStatus,
      (newStatus, oldStatus) => {
        if (newStatus === 'connected' && oldStatus !== 'connected') {
          if (reconnectMessageShown) {
            showStatusMessage('模型连接已恢复', 'success', 3000)
            reconnectMessageShown = false
          }
        } else if (newStatus === 'error' && oldStatus === 'connected') {
          reconnectMessageShown = true
        }
      }
    )

    watch(
      () => connectionStore.statusMessage,
      (newMessage) => {
        if (newMessage && connectionStore.consecutiveFailures > 0) {
          showStatusMessage(newMessage, 'warning', 0)
        }
      }
    )
  }

  /**
   * 初始化自动连接
   * 在应用启动或用户登录时调用
   */
  async function initializeAutoConnect() {
    if (userStore.isLoggedIn && !connectionStore.isConnected) {
      await autoConnectAfterLogin()
    }
  }

  /**
   * 清理资源
   */
  function cleanup() {
    if (statusTimeout) {
      clearTimeout(statusTimeout)
    }
    connectionStore.stopHealthCheck()
  }

  /**
   * 手动触发重新连接
   */
  async function manualReconnect() {
    const success = await connectionStore.reconnect()
    if (success) {
      showStatusMessage('模型重新连接成功', 'success')
    } else {
      showStatusMessage('模型重新连接失败', 'error')
    }
    return success
  }

  /**
   * 获取连接状态信息
   */
  function getConnectionInfo() {
    return {
      isConnected: connectionStore.isConnected,
      isConnecting: connectionStore.isConnecting,
      status: connectionStore.connectionStatus,
      statusText: connectionStore.statusText,
      message: connectionStore.statusMessage,
      retryDelay: connectionStore.retryDelay,
      consecutiveFailures: connectionStore.consecutiveFailures,
      connectedModels: connectionStore.connectedModels,
      ollamaStatus: connectionStore.ollamaStatus
    }
  }

  return {
    showConnectionStatus,
    statusVisible,
    connectionStore,
    autoConnectAfterLogin,
    initializeAutoConnect,
    manualReconnect,
    watchConnectionStatus,
    cleanup,
    getConnectionInfo,
    showStatusMessage
  }
}

export default useModelAutoConnect
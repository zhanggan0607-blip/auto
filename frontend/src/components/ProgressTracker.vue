<template>
  <div class="progress-tracker" v-if="visible">
    <el-card class="progress-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon class="task-icon" :class="statusClass">
              <component :is="statusIcon" />
            </el-icon>
            <span class="task-title">{{ taskName }}</span>
          </div>
          <div class="header-right">
            <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
            <el-button text @click="handleClose" class="close-btn">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </template>

      <div class="progress-content">
        <div class="overall-progress">
          <div class="progress-stats">
            <div class="progress-main">
              <span class="progress-percentage">{{ overallProgress }}%</span>
              <span class="progress-message">{{ currentMessage }}</span>
            </div>
            <div class="progress-time" v-if="task">
              <span v-if="task.status === 'running' && elapsedTime">
                <el-icon><Clock /></el-icon>
                已耗时: {{ elapsedTime }}
              </span>
              <span v-if="task.status === 'completed' && totalDuration">
                <el-icon><CircleCheck /></el-icon>
                总耗时: {{ totalDuration }}
              </span>
              <span v-if="estimatedRemaining && task.status === 'running'">
                <el-icon><Timer /></el-icon>
                预计剩余: {{ estimatedRemaining }}
              </span>
            </div>
          </div>
          <el-progress
            :percentage="overallProgress"
            :status="progressStatus"
            :stroke-width="12"
            :show-text="false"
          />
        </div>

        <el-divider content-position="left">
          <span class="steps-title">执行步骤</span>
          <span class="steps-count" v-if="task?.steps?.length">
            ({{ completedStepsCount }}/{{ task.steps.length }})
          </span>
        </el-divider>

        <div class="steps-list">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{
              'step-active': step.status === 'active',
              'step-completed': step.status === 'completed',
              'step-waiting': step.status === 'waiting',
              'step-error': step.status === 'error'
            }"
          >
            <div class="step-indicator">
              <div class="step-circle">
                <el-icon v-if="step.status === 'completed'" class="step-check"><Check /></el-icon>
                <el-icon v-else-if="step.status === 'error'" class="step-error-icon"><Close /></el-icon>
                <span v-else-if="step.status === 'active'" class="step-spinner">
                  <el-icon class="is-loading"><Loading /></el-icon>
                </span>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <div class="step-line" v-if="index < steps.length - 1"></div>
            </div>
            <div class="step-content">
              <div class="step-header">
                <span class="step-title">{{ step.title || `步骤 ${index + 1}` }}</span>
                <div class="step-badges">
                  <el-tag
                    v-if="step.status === 'active'"
                    type="primary"
                    size="small"
                    class="progress-tag"
                  >
                    {{ step.progress || 0 }}%
                  </el-tag>
                  <el-tag
                    v-if="step.status === 'completed'"
                    type="success"
                    size="small"
                  >
                    完成
                  </el-tag>
                  <el-tag
                    v-if="step.status === 'error'"
                    type="danger"
                    size="small"
                  >
                    失败
                  </el-tag>
                </div>
              </div>
              <div class="step-description">
                {{ step.description || step.message || getStepDefaultMessage(step.status) }}
              </div>
              <div class="step-progress-bar" v-if="step.status === 'active' && step.progress !== undefined">
                <el-progress
                  :percentage="Math.min(100, Math.max(0, step.progress))"
                  :stroke-width="4"
                  :show-text="false"
                  :status="step.status === 'error' ? 'exception' : undefined"
                />
              </div>
              <div class="step-time-info" v-if="step.started_at || step.elapsed_seconds">
                <span class="time-item" v-if="step.started_at">
                  <el-icon><Clock /></el-icon>
                  开始: {{ formatTime(step.started_at) }}
                </span>
                <span class="time-item" v-if="step.elapsed_seconds !== null && step.elapsed_seconds !== undefined">
                  <el-icon><Timer /></el-icon>
                  耗时: {{ formatDuration(step.elapsed_seconds) }}
                </span>
                <span class="time-item error" v-if="step.status === 'error' && step.error">
                  <el-icon><WarningFilled /></el-icon>
                  {{ step.error }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <el-alert
          v-if="error"
          type="error"
          :title="errorTitle"
          :description="errorDescription"
          show-icon
          :closable="true"
          @close="handleErrorClose"
          class="error-alert"
        >
          <template #default>
            <div class="error-content">
              <p><strong>错误类型：</strong>{{ errorType }}</p>
              <p><strong>错误信息：</strong>{{ error }}</p>
              <p class="error-suggestion" v-if="errorSuggestion">
                <el-icon><InfoFilled /></el-icon>
                {{ errorSuggestion }}
              </p>
            </div>
          </template>
        </el-alert>

        <div class="action-buttons" v-if="task">
          <el-button
            v-if="task.status === 'running'"
            type="warning"
            size="small"
            @click="handleCancel"
            :loading="cancelling"
          >
            <el-icon><VideoPause /></el-icon>
            取消任务
          </el-button>
          <el-button
            v-if="task.status === 'failed'"
            type="primary"
            size="small"
            @click="handleRetry"
            :loading="retrying"
          >
            <el-icon><RefreshRight /></el-icon>
            重试
          </el-button>
          <el-button
            v-if="task.status === 'completed'"
            type="success"
            size="small"
            @click="handleClose"
          >
            <el-icon><CircleCheck /></el-icon>
            完成
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  Close,
  Check,
  Loading,
  CloseBold,
  InfoFilled,
  VideoPause,
  RefreshRight,
  CircleCheck,
  Clock,
  Checked,
  WarningFilled,
  Timer
} from '@element-plus/icons-vue'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  taskName: {
    type: String,
    default: '任务执行中'
  },
  visible: {
    type: Boolean,
    default: true
  },
  pollingInterval: {
    type: Number,
    default: 2000
  }
})

const emit = defineEmits(['close', 'cancel', 'retry', 'update:visible'])

const task = ref(null)
const cancelling = ref(false)
const retrying = ref(false)
const pollingTimer = ref(null)
const startTime = ref(null)

const steps = computed(() => {
  if (!task.value?.steps) return []
  return task.value.steps
})

const completedStepsCount = computed(() => {
  if (!task.value?.steps) return 0
  return task.value.steps.filter(s => s.status === 'completed').length
})

const currentMessage = computed(() => {
  if (!task.value) return ''
  if (task.value.status === 'failed') return '任务执行失败'
  if (task.value.status === 'completed') return '任务已完成'
  const activeStep = task.value.steps?.find(s => s.status === 'active')
  if (activeStep) {
    return activeStep.description || activeStep.title || '执行中...'
  }
  return task.value.message || '执行中...'
})

const overallProgress = computed(() => {
  if (!task.value) return 0
  if (task.value.status === 'completed') return 100
  if (task.value.status === 'failed') return task.value.progress || 0
  return Math.round(task.value.progress || 0)
})

const statusClass = computed(() => {
  if (!task.value) return ''
  return `status-${task.value.status}`
})

const statusIcon = computed(() => {
  if (!task.value) return Clock
  switch (task.value.status) {
    case 'completed': return Checked
    case 'failed': return WarningFilled
    case 'running': return Loading
    default: return Clock
  }
})

const statusTagType = computed(() => {
  if (!task.value) return 'info'
  switch (task.value.status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'running': return 'primary'
    default: return 'info'
  }
})

const statusText = computed(() => {
  if (!task.value) return '未知'
  switch (task.value.status) {
    case 'completed': return '已完成'
    case 'failed': return '失败'
    case 'running': return '执行中'
    case 'cancelled': return '已取消'
    default: return task.value.status
  }
})

const progressStatus = computed(() => {
  if (!task.value) return undefined
  switch (task.value.status) {
    case 'completed': return 'success'
    case 'failed': return 'exception'
    default: return undefined
  }
})

const error = computed(() => task.value?.error || null)

const errorTitle = computed(() => '任务执行出错')

const errorDescription = computed(() => {
  if (!error.value) return ''
  return `错误信息: ${error.value}`
})

const errorType = computed(() => {
  if (!task.value?.error_info) return 'UnknownError'
  return task.value.error_info.error_type || 'UnknownError'
})

const errorSuggestion = computed(() => {
  const err = error.value?.toLowerCase() || ''
  if (err.includes('timeout') || err.includes('超时')) {
    return '建议：网络连接超时，请检查网络状况或稍后重试'
  }
  if (err.includes('permission') || err.includes('权限')) {
    return '建议：请检查账号权限设置'
  }
  if (err.includes('not found') || err.includes('不存在')) {
    return '建议：目标资源不存在，请检查配置'
  }
  if (err.includes('connection') || err.includes('连接')) {
    return '建议：无法连接到目标服务器，请检查网络和代理设置'
  }
  return '建议：请查看错误信息并根据情况进行处理，或联系管理员'
})

const elapsedTime = computed(() => {
  if (!startTime.value || !task.value?.started_at) return null
  const start = new Date(task.value.started_at)
  const now = new Date()
  const diff = Math.floor((now - start) / 1000)
  return formatDuration(diff)
})

const totalDuration = computed(() => {
  if (!task.value?.finished_at || !task.value?.started_at) return null
  const start = new Date(task.value.started_at)
  const end = new Date(task.value.finished_at)
  const diff = Math.floor((end - start) / 1000)
  return formatDuration(diff)
})

const estimatedRemaining = computed(() => {
  if (!task.value || task.value.status !== 'running') return null
  if (!task.value.progress || task.value.progress <= 0) return null

  const start = new Date(task.value.started_at)
  const now = new Date()
  const elapsed = (now - start) / 1000
  const progress = task.value.progress / 100
  if (progress <= 0) return null

  const totalEstimated = elapsed / progress
  const remaining = totalEstimated - elapsed
  if (remaining < 0) return null
  return formatDuration(Math.floor(remaining))
})

const formatTime = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined) return ''
  seconds = Math.floor(seconds)
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}分${secs}秒`
  }
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  return `${hours}时${mins}分`
}

const getStepDefaultMessage = (status) => {
  switch (status) {
    case 'waiting': return '等待执行'
    case 'active': return '执行中...'
    case 'completed': return '已完成'
    case 'error': return '执行失败'
    default: return ''
  }
}

const fetchTaskStatus = async () => {
  try {
    const response = await fetch(`/api/v1/progress/tasks/${props.taskId}/`)
    if (response.ok) {
      const data = await response.json()
      if (data.success && data.data) {
        task.value = data.data
        if (data.data.started_at && !startTime.value) {
          startTime.value = new Date(data.data.started_at)
        }
      } else if (data.status) {
        task.value = data
      }

      if (task.value?.status === 'completed' || task.value?.status === 'failed') {
        stopPolling()
      }
    } else if (response.status === 404) {
      task.value = { status: 'not_found', error: '任务不存在或已过期' }
      stopPolling()
    }
  } catch (error) {
    console.error('获取任务状态失败:', error)
  }
}

const startPolling = () => {
  stopPolling()
  startTime.value = null
  fetchTaskStatus()
  pollingTimer.value = setInterval(fetchTaskStatus, props.pollingInterval)
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

const handleClose = () => {
  stopPolling()
  emit('close')
  emit('update:visible', false)
}

const handleErrorClose = () => {
  if (task.value) {
    task.value.error = null
  }
}

const handleCancel = async () => {
  cancelling.value = true
  try {
    const response = await fetch(`/api/v1/progress/tasks/${props.taskId}/cancel/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (response.ok) {
      emit('cancel', props.taskId)
      handleClose()
    }
  } catch (error) {
    console.error('取消任务失败:', error)
  } finally {
    cancelling.value = false
  }
}

const handleRetry = async () => {
  retrying.value = true
  try {
    const response = await fetch(`/api/v1/progress/tasks/${props.taskId}/retry/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (response.ok) {
      task.value = { status: 'running', progress: 0 }
      emit('retry', props.taskId)
      startPolling()
    }
  } catch (error) {
    console.error('重试任务失败:', error)
  } finally {
    retrying.value = false
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal && props.taskId) {
    startPolling()
  } else {
    stopPolling()
  }
})

watch(() => props.taskId, (newVal) => {
  if (newVal && props.visible) {
    startPolling()
  }
})

onMounted(() => {
  if (props.visible && props.taskId) {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.progress-tracker {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 480px;
  max-height: 90vh;
  z-index: 2000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.progress-card {
  border-radius: 12px;
  overflow: hidden;

  :deep(.el-card__header) {
    padding: 12px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom: none;
  }

  :deep(.el-card__body) {
    padding: 16px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-icon {
  font-size: 18px;

  &.status-completed { color: #67c23a; }
  &.status-failed { color: #f56c6c; }
  &.status-running { color: #409eff; animation: rotate 1s linear infinite; }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-title {
  font-size: 15px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  color: white;
  padding: 4px;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
  }
}

.progress-content {
  max-height: calc(90vh - 200px);
  overflow-y: auto;
}

.overall-progress {
  margin-bottom: 16px;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.progress-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.progress-percentage {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.progress-message {
  font-size: 13px;
  color: #606266;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-time {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  font-size: 12px;
  color: #909399;

  .time-item {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.steps-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.steps-count {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.steps-list {
  margin: 12px 0;
}

.step-item {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
}

.step-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #e4e7ed;
  color: #909399;
  flex-shrink: 0;
}

.step-waiting .step-circle {
  background: #e4e7ed;
  color: #909399;
}

.step-active .step-circle {
  background: #409eff;
  color: white;
}

.step-completed .step-circle {
  background: #67c23a;
  color: white;
}

.step-error .step-circle {
  background: #f56c6c;
  color: white;
}

.step-check, .step-error-icon {
  font-size: 14px;
}

.step-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-line {
  width: 2px;
  height: 40px;
  background: #e4e7ed;
  margin-top: 4px;
}

.step-completed .step-line {
  background: #67c23a;
}

.step-content {
  flex: 1;
  padding-bottom: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.step-waiting .step-title {
  color: #909399;
}

.step-active .step-title {
  color: #409eff;
}

.step-completed .step-title {
  color: #67c23a;
}

.step-error .step-title {
  color: #f56c6c;
}

.step-badges {
  display: flex;
  gap: 4px;
}

.progress-tag {
  font-weight: 500;
}

.step-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
  margin-bottom: 4px;
}

.step-active .step-description {
  color: #606266;
}

.step-progress-bar {
  margin-top: 6px;
}

.step-time-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 6px;
  font-size: 11px;
  color: #909399;

  .time-item {
    display: flex;
    align-items: center;
    gap: 3px;

    &.error {
      color: #f56c6c;
      font-weight: 500;
    }
  }
}

.error-alert {
  margin-top: 16px;

  :deep(.el-alert__title) {
    font-weight: 600;
  }
}

.error-content {
  p {
    margin: 4px 0;
    font-size: 13px;
  }

  .error-suggestion {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    color: #e6a23c;
  }
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}
</style>

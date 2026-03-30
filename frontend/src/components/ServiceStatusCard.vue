<template>
  <el-card class="service-status-card" shadow="never">
    <template #header>
      <div class="card-header">
        <div class="card-title-wrapper">
          <span class="card-title">系统服务状态</span>
          <el-tag :type="overallStatusType" size="small">{{ overallStatusText }}</el-tag>
        </div>
        <el-button type="primary" link @click="refreshStatus" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </template>

    <div class="services-grid">
      <div
        v-for="service in services"
        :key="service.name"
        class="service-item"
        :class="`service-${service.status}`"
      >
        <div class="service-icon">
          <el-icon :size="20">
            <component :is="getServiceIcon(service.name, service.status)" />
          </el-icon>
        </div>
        <div class="service-info">
          <div class="service-name">{{ service.name }}</div>
          <div class="service-message">{{ service.message }}</div>
        </div>
        <div class="service-status">
          <el-tag :type="getStatusType(service.status)" size="small">
            {{ getStatusText(service.status) }}
          </el-tag>
        </div>
      </div>
    </div>

    <div class="update-time">
      最后更新: {{ lastUpdateTime }}
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getSystemServices } from '@/api/system'
import {
  CircleCheck,
  CircleClose,
  Loading,
  Warning,
  QuestionFilled,
  Odometer,
  Database,
  Timer,
  Connection,
  Box,
  List,
  Clock,
  Monitor
} from '@element-plus/icons-vue'

const services = ref([])
const overallStatus = ref('unknown')
const loading = ref(false)
const lastUpdate = ref(null)

const overallStatusType = computed(() => {
  const typeMap = {
    'healthy': 'success',
    'degraded': 'warning',
    'unhealthy': 'danger',
    'unknown': 'info'
  }
  return typeMap[overallStatus.value] || 'info'
})

const overallStatusText = computed(() => {
  const textMap = {
    'healthy': '全部正常',
    'degraded': '部分异常',
    'unhealthy': '服务异常',
    'unknown': '未知状态'
  }
  return textMap[overallStatus.value] || '未知状态'
})

const lastUpdateTime = computed(() => {
  if (!lastUpdate.value) return '从未更新'
  return new Date(lastUpdate.value).toLocaleString('zh-CN')
})

const getServiceIcon = (name, status) => {
  if (status === 'running') return CircleCheck
  if (status === 'error' || status === 'stopped') return CircleClose
  if (status === 'degraded') return Warning
  return QuestionFilled
}

const getStatusType = (status) => {
  const typeMap = {
    'running': 'success',
    'error': 'danger',
    'stopped': 'warning',
    'degraded': 'warning',
    'unknown': 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    'running': '运行中',
    'error': '错误',
    'stopped': '已停止',
    'degraded': '性能下降',
    'unknown': '未知'
  }
  return textMap[status] || status
}

const fetchServicesStatus = async () => {
  try {
    loading.value = true
    const response = await getSystemServices()
    if (response.status === 200 || response.status === 201) {
      const data = response.data || response
      services.value = data.services || []
      overallStatus.value = data.status || 'unknown'
      lastUpdate.value = data.timestamp || new Date().toISOString()
    }
  } catch (error) {
    console.error('获取服务状态失败:', error)
    services.value = []
    overallStatus.value = 'unknown'
  } finally {
    loading.value = false
  }
}

const refreshStatus = () => {
  fetchServicesStatus()
}

let autoRefreshTimer = null

onMounted(() => {
  fetchServicesStatus()
  autoRefreshTimer = setInterval(fetchServicesStatus, 30000)
})

onUnmounted(() => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
  }
})
</script>

<style scoped lang="scss">
.service-status-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);

  :deep(.el-card__header) {
    padding: var(--spacing-lg) var(--spacing-xl);
    background-color: var(--color-bg-white);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-card__body) {
    padding: var(--spacing-lg);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title-wrapper {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.card-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.services-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.service-item {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  background-color: var(--color-bg-page);
  border-radius: var(--radius-md);
  gap: var(--spacing-md);
  transition: all 0.2s ease;

  &:hover {
    background-color: var(--color-bg-hover);
  }

  &.service-error {
    background-color: rgba(245, 108, 108, 0.05);
    border: 1px solid rgba(245, 108, 108, 0.2);
  }

  &.service-stopped {
    background-color: rgba(230, 162, 60, 0.05);
    border: 1px solid rgba(230, 162, 60, 0.2);
  }

  &.service-running {
    background-color: rgba(103, 194, 58, 0.05);
    border: 1px solid rgba(103, 194, 58, 0.2);
  }
}

.service-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background-color: var(--color-bg-white);

  .service-running & {
    color: var(--color-success);
  }

  .service-error & {
    color: var(--color-danger);
  }

  .service-stopped & {
    color: var(--color-warning);
  }
}

.service-info {
  flex: 1;
  min-width: 0;
}

.service-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
}

.service-message {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.service-status {
  flex-shrink: 0;
}

.update-time {
  margin-top: var(--spacing-lg);
  text-align: right;
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}
</style>

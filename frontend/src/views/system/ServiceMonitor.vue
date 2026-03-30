<template>
  <div class="service-monitor">
    <div class="monitor-header">
      <div class="header-left">
        <h2 class="page-title">服务监控中心</h2>
        <el-tag :type="overallStatusType" size="large">{{ overallStatusText }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="refreshAll" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新全部
        </el-button>
        <el-button type="success" @click="handleAutoRecovery" :loading="recovering">
          <el-icon><Lightning /></el-icon>
          自动恢复
        </el-button>
        <el-button @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加服务
        </el-button>
      </div>
    </div>

    <div class="statistics-cards">
      <el-card class="stat-card stat-healthy" shadow="never">
        <div class="stat-content">
          <div class="stat-icon healthy">
            <el-icon :size="32"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.healthy }}</div>
            <div class="stat-label">健康服务</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-degraded" shadow="never">
        <div class="stat-content">
          <div class="stat-icon degraded">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.degraded }}</div>
            <div class="stat-label">性能下降</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-unhealthy" shadow="never">
        <div class="stat-content">
          <div class="stat-icon unhealthy">
            <el-icon :size="32"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statistics.unhealthy }}</div>
            <div class="stat-label">服务异常</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card stat-alerts" shadow="never">
        <div class="stat-content">
          <div class="stat-icon alerts">
            <el-icon :size="32"><Bell /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ pendingAlerts }}</div>
            <div class="stat-label">待处理告警</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="filter-card" shadow="never">
      <div class="filters">
        <el-select v-model="filterCategory" placeholder="服务类别" clearable style="width: 150px">
          <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="服务状态" clearable style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="健康" value="healthy" />
          <el-option label="性能下降" value="degraded" />
          <el-option label="异常" value="unhealthy" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-checkbox v-model="showCriticalOnly">仅显示关键服务</el-checkbox>
      </div>
    </el-card>

    <el-card class="services-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>服务列表</span>
          <span class="service-count">共 {{ filteredServices.length }} 个服务</span>
        </div>
      </template>

      <div class="services-grid">
        <div
          v-for="service in filteredServices"
          :key="service.service_id"
          class="service-card"
          :class="`service-${service.status}`"
          @click="openServiceDetail(service)"
        >
          <div class="service-card-header">
            <div class="service-category">
              <el-tag size="small" type="info">{{ getCategoryLabel(service.category) }}</el-tag>
              <el-tag v-if="service.is_critical" size="small" type="danger">关键</el-tag>
            </div>
            <el-dropdown trigger="click" @click.stop>
              <el-button link @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click.stop="handleCheckHealth(service)">
                    <el-icon><View /></el-icon> 健康检查
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="service.auto_restart_enabled"
                    @click.stop="handleRestart(service)"
                  >
                    <el-icon><Refresh /></el-icon> 重启服务
                  </el-dropdown-item>
                  <el-dropdown-item @click.stop="openServiceDetail(service)">
                    <el-icon><Document /></el-icon> 查看详情
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="service-card-body">
            <div class="service-name">{{ service.display_name }}</div>
            <div class="service-status">
              <el-tag :type="getStatusType(service.status)" size="small">
                {{ service.status_display }}
              </el-tag>
            </div>
            <div class="service-metrics">
              <div class="metric" v-if="service.response_time_ms !== null">
                <span class="metric-label">响应</span>
                <span class="metric-value">{{ service.response_time_ms }}ms</span>
              </div>
              <div class="metric" v-if="service.cpu_usage !== null">
                <span class="metric-label">CPU</span>
                <span class="metric-value">{{ service.cpu_usage }}%</span>
              </div>
              <div class="metric" v-if="service.memory_usage !== null">
                <span class="metric-label">内存</span>
                <span class="metric-value">{{ service.memory_usage }}%</span>
              </div>
              <div class="metric" v-if="service.worker_count !== undefined && service.worker_count !== null">
                <span class="metric-label">Worker</span>
                <span class="metric-value">{{ service.worker_count }}</span>
              </div>
              <div class="metric" v-if="service.active_task_count !== undefined && service.active_task_count !== null">
                <span class="metric-label">活跃任务</span>
                <span class="metric-value">{{ service.active_task_count }}</span>
              </div>
            </div>
          </div>

          <div class="service-card-footer">
            <div class="last-check" v-if="service.last_health_check">
              <el-icon><Timer /></el-icon>
              {{ formatTime(service.last_health_check) }}
            </div>
            <div class="restart-info" v-if="service.restart_attempts_today > 0">
              今日重启: {{ service.restart_attempts_today }}
            </div>
          </div>

          <div v-if="service.consecutive_failures > 0" class="failure-indicator">
            <el-icon><WarningFilled /></el-icon>
            连续失败 {{ service.consecutive_failures }} 次
          </div>

          <div v-if="service.status === 'restarting'" class="restarting-overlay">
            <el-icon class="rotating"><Loading /></el-icon>
            重启中...
          </div>
        </div>
      </div>

      <el-empty v-if="filteredServices.length === 0" description="暂无服务数据" />
    </el-card>

    <el-dialog v-model="showAddDialog" title="添加监控服务" width="600px">
      <el-form :model="addForm" :rules="addFormRules" ref="addFormRef" label-width="120px">
        <el-form-item label="服务名称" prop="name">
          <el-input v-model="addForm.name" placeholder="如: postgresql_database" />
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="addForm.display_name" placeholder="如: PostgreSQL 数据库" />
        </el-form-item>
        <el-form-item label="服务类别" prop="category">
          <el-select v-model="addForm.category" placeholder="请选择">
            <el-option v-for="cat in categories" :key="cat.value" :label="cat.label" :value="cat.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="健康检查类型" prop="health_check_type">
          <el-radio-group v-model="addForm.health_check_type">
            <el-radio label="http">HTTP请求</el-radio>
            <el-radio label="tcp">TCP端口</el-radio>
            <el-radio label="process">进程检测</el-radio>
            <el-radio label="celery">Celery服务</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="检查URL" prop="health_check_url" v-if="addForm.health_check_type === 'http'">
          <el-input v-model="addForm.health_check_url" placeholder="如: http://localhost:5432" />
        </el-form-item>
        <el-form-item label="检查端口" prop="health_check_port" v-if="addForm.health_check_type === 'tcp'">
          <el-input-number v-model="addForm.health_check_port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="关键服务">
          <el-switch v-model="addForm.is_critical" />
        </el-form-item>
        <el-form-item label="自动重启">
          <el-switch v-model="addForm.auto_restart_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAddForm">确定</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="showDetailDrawer" :title="currentService?.display_name" size="600px">
      <div v-if="currentService" class="service-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="服务名称">{{ currentService.service_name }}</el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusType(currentService.status)">{{ currentService.status_display }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="服务类别">{{ getCategoryLabel(currentService.category) }}</el-descriptions-item>
          <el-descriptions-item label="是否关键">{{ currentService.is_critical ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="连续失败次数">{{ currentService.consecutive_failures }}</el-descriptions-item>
          <el-descriptions-item label="今日重启次数">{{ currentService.restart_attempts_today }}</el-descriptions-item>
          <el-descriptions-item label="最后检查时间" :span="2">
            {{ formatTime(currentService.last_health_check) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentService.worker_count !== undefined" label="Worker数量">
            {{ currentService.worker_count }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentService.active_task_count !== undefined" label="活跃任务">
            {{ currentService.active_task_count }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">健康记录 (最近24小时)</el-divider>
        <ServiceHealthChart :service-id="currentService.service_id" />

        <el-divider content-position="left">操作日志 (最近24小时)</el-divider>
        <ServiceActionLogList :service-id="currentService.service_id" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Plus, Lightning, CircleCheck, CircleClose,
  Warning, Bell, Timer, MoreFilled, View, Document,
  WarningFilled, Loading
} from '@element-plus/icons-vue'
import {
  getMonitorDashboard, checkServiceHealth, restartService,
  triggerAutoRecovery, createMonitoredService, getServiceCategories
} from '@/api/monitor'
import ServiceHealthChart from './components/ServiceHealthChart.vue'
import ServiceActionLogList from './components/ServiceActionLogList.vue'

const loading = ref(false)
const recovering = ref(false)
const dashboardData = ref(null)
const categories = ref([])
const filterCategory = ref('')
const filterStatus = ref('')
const showCriticalOnly = ref(false)
const showAddDialog = ref(false)
const showDetailDrawer = ref(false)
const currentService = ref(null)

const addForm = ref({
  name: '',
  display_name: '',
  category: 'other',
  health_check_type: 'http',
  health_check_url: '',
  health_check_port: null,
  is_critical: false,
  auto_restart_enabled: true
})

const addFormRules = {
  name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择服务类别', trigger: 'change' }]
}

const addFormRef = ref(null)

const statistics = computed(() => {
  return dashboardData.value?.statistics || {
    total: 0, healthy: 0, degraded: 0, unhealthy: 0, offline: 0
  }
})

const pendingAlerts = computed(() => {
  return dashboardData.value?.pending_alerts || 0
})

const overallStatus = computed(() => {
  return dashboardData.value?.overall_status || 'unknown'
})

const overallStatusType = computed(() => {
  const typeMap = {
    'healthy': 'success',
    'degraded': 'warning',
    'unhealthy': 'danger',
    'offline': 'info'
  }
  return typeMap[overallStatus.value] || 'info'
})

const overallStatusText = computed(() => {
  const textMap = {
    'healthy': '全部正常',
    'degraded': '部分异常',
    'unhealthy': '服务异常',
    'offline': '服务离线'
  }
  return textMap[overallStatus.value] || '未知状态'
})

const filteredServices = computed(() => {
  let services = dashboardData.value?.services || []

  if (filterCategory.value) {
    services = services.filter(s => s.category === filterCategory.value)
  }
  if (filterStatus.value) {
    services = services.filter(s => s.status === filterStatus.value)
  }
  if (showCriticalOnly.value) {
    services = services.filter(s => s.is_critical)
  }

  return services
})

const getStatusType = (status) => {
  const typeMap = {
    'healthy': 'success',
    'degraded': 'warning',
    'unhealthy': 'danger',
    'restarting': 'warning',
    'offline': 'info',
    'unknown': 'info'
  }
  return typeMap[status] || 'info'
}

const getCategoryLabel = (category) => {
  const cat = categories.value.find(c => c.value === category)
  return cat?.label || category
}

const formatTime = (time) => {
  if (!time) return '从未'
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

const fetchDashboard = async () => {
  try {
    loading.value = true
    const res = await getMonitorDashboard()
    dashboardData.value = res
  } catch (error) {
    console.error('获取监控数据失败:', error)
    ElMessage.error('获取监控数据失败')
  } finally {
    loading.value = false
  }
}

const fetchCategories = async () => {
  try {
    const res = await getServiceCategories()
    categories.value = res
  } catch (error) {
    console.error('获取服务类别失败:', error)
  }
}

const refreshAll = () => {
  fetchDashboard()
}

const handleAutoRecovery = async () => {
  try {
    await ElMessageBox.confirm(
      '系统将自动尝试恢复所有异常服务，是否继续？',
      '自动恢复',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    recovering.value = true
    const res = await triggerAutoRecovery()
    ElMessage.success(`自动恢复完成，已处理 ${res.processed_count} 个服务`)
    fetchDashboard()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('自动恢复失败')
    }
  } finally {
    recovering.value = false
  }
}

const handleCheckHealth = async (service) => {
  try {
    await checkServiceHealth(service.service_id)
    ElMessage.success(`已对 ${service.display_name} 执行健康检查`)
    fetchDashboard()
  } catch (error) {
    ElMessage.error('健康检查失败')
  }
}

const handleRestart = async (service) => {
  try {
    await ElMessageBox.confirm(
      `确定要重启 ${service.display_name} 吗？`,
      '重启服务',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await restartService(service.service_id)
    ElMessage.success('重启命令已发送')
    fetchDashboard()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重启失败: ' + (error.message || '未知错误'))
    }
  }
}

const openServiceDetail = (service) => {
  currentService.value = service
  showDetailDrawer.value = true
}

const submitAddForm = async () => {
  if (!addFormRef.value) return

  try {
    await addFormRef.value.validate()
    await createMonitoredService(addForm.value)
    ElMessage.success('服务添加成功')
    showAddDialog.value = false
    addFormRef.value.resetFields()
    fetchDashboard()
  } catch (error) {
    if (error !== false) {
      ElMessage.error('添加失败')
    }
  }
}

let autoRefreshTimer = null

onMounted(() => {
  fetchDashboard()
  fetchCategories()
  autoRefreshTimer = setInterval(fetchDashboard, 30000)
})

onUnmounted(() => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
  }
})
</script>

<style scoped lang="scss">
.service-monitor {
  padding: 20px;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.statistics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;

  &.healthy {
    background: rgba(103, 194, 58, 0.1);
    color: #67c23a;
  }

  &.degraded {
    background: rgba(230, 162, 60, 0.1);
    color: #e6a23c;
  }

  &.unhealthy {
    background: rgba(245, 108, 108, 0.1);
    color: #f56c6c;
  }

  &.alerts {
    background: rgba(144, 147, 153, 0.1);
    color: #909399;
  }
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.filters {
  display: flex;
  align-items: center;
  gap: 16px;
}

.services-card {
  border-radius: 12px;

  :deep(.el-card__header) {
    padding: 16px 20px;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.service-count {
  font-size: 14px;
  color: #909399;
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.service-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  &.service-healthy {
    border-left: 4px solid #67c23a;
  }

  &.service-degraded {
    border-left: 4px solid #e6a23c;
  }

  &.service-unhealthy {
    border-left: 4px solid #f56c6c;
    background: rgba(245, 108, 108, 0.02);
  }

  &.service-offline {
    border-left: 4px solid #909399;
  }

  &.service-restarting {
    border-left: 4px solid #409eff;
  }
}

.service-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.service-category {
  display: flex;
  gap: 8px;
}

.service-card-body {
  margin-bottom: 12px;
}

.service-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.service-metrics {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.metric-value {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
}

.service-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.last-check {
  display: flex;
  align-items: center;
  gap: 4px;
}

.failure-indicator {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.restarting-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #409eff;
  font-size: 14px;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.service-detail {
  padding: 0 10px;
}
</style>
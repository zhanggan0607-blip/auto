<template>
  <div class="automation-monitor">
    <div class="page-header">
      <div class="header-left">
        <h3 class="page-title">自动化监控中心</h3>
        <p class="page-subtitle">实时监控业务自动化流程运行状态</p>
      </div>
      <div class="header-actions">
        <el-tag :type="overallStatusType" size="large" class="status-tag">
          <el-icon v-if="overallStatus === 'running'" class="status-icon pulse"><Loading /></el-icon>
          <span>{{ overallStatusText }}</span>
        </el-tag>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ todayStats.crawled || 0 }}</div>
          <div class="stat-label">今日采集</div>
          <div class="stat-trend" :class="getTrendClass(todayStats.crawled_trend)">
            {{ formatTrend(todayStats.crawled_trend) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ todayStats.matched || 0 }}</div>
          <div class="stat-label">今日匹配</div>
          <div class="stat-trend" :class="getTrendClass(todayStats.matched_trend)">
            {{ formatTrend(todayStats.matched_trend) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ todayStats.bids || 0 }}</div>
          <div class="stat-label">今日投标</div>
          <div class="stat-trend" :class="getTrendClass(todayStats.bids_trend)">
            {{ formatTrend(todayStats.bids_trend) }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ todayStats.won || 0 }}</div>
          <div class="stat-label">今日中标</div>
          <div class="stat-trend" :class="getTrendClass(todayStats.won_trend)">
            {{ formatTrend(todayStats.won_trend) }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="flow-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">自动化流程</span>
          <div class="flow-legend">
            <span class="legend-item"><span class="dot success" />运行中</span>
            <span class="legend-item"><span class="dot idle" />空闲</span>
            <span class="legend-item"><span class="dot error" />异常</span>
          </div>
        </div>
      </template>

      <div class="automation-flow">
        <div
          v-for="(stage, index) in flowStages"
          :key="stage.id"
          class="flow-stage"
          :class="{ active: stage.status === 'running', error: stage.status === 'error' }"
        >
          <div class="stage-icon">
            <el-icon v-if="stage.status === 'running'" class="pulse"><Loading /></el-icon>
            <el-icon v-else-if="stage.status === 'error'"><Warning /></el-icon>
            <el-icon v-else><CircleCheck /></el-icon>
          </div>
          <div class="stage-info">
            <div class="stage-name">{{ stage.name }}</div>
            <div class="stage-count">{{ stage.count }} {{ stage.unit }}</div>
          </div>
          <div class="stage-rate">
            <el-progress
              type="circle"
              :percentage="stage.autoRate"
              :width="50"
              :stroke-width="4"
              :color="getRateColor(stage.autoRate)"
            >
              <template #default>{{ stage.autoRate }}%</template>
            </el-progress>
          </div>
          <div v-if="index < flowStages.length - 1" class="flow-arrow">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="detail-row">
      <el-col :span="12">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">异常告警</span>
              <el-badge :value="anomalies.length" :hidden="anomalies.length === 0">
                <el-button link type="primary" size="small">查看全部</el-button>
              </el-badge>
            </div>
          </template>

          <el-table :data="anomalies" style="width: 100%" size="small" max-height="300">
            <el-table-column prop="time" label="时间" width="140" />
            <el-table-column prop="stage" label="环节" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getStageTagType(row.stage)">
                  {{ getStageName(row.stage) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="message" label="异常信息" min-width="200" show-overflow-tooltip />
            <el-table-column prop="handled" label="状态" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.handled" size="small" type="success">已处理</el-tag>
                <el-tag v-else size="small" type="warning">待处理</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button
                  v-if="!row.handled"
                  type="primary"
                  link
                  size="small"
                  @click="handleAnomaly(row)"
                >
                  处理
                </el-button>
                <el-tag v-else size="small" type="info">完成</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="anomalies.length === 0" description="暂无异常" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">人工干预</span>
              <el-badge :value="pendingActions.length" :hidden="pendingActions.length === 0">
                <el-button link type="primary" size="small">查看全部</el-button>
              </el-badge>
            </div>
          </template>

          <el-table :data="pendingActions" style="width: 100%" size="small" max-height="300">
            <el-table-column prop="time" label="时间" width="140" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getActionTagType(row.type)">
                  {{ getActionName(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="success" link size="small" @click="approveAction(row)">
                  批准
                </el-button>
                <el-button type="danger" link size="small" @click="rejectAction(row)">
                  拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="pendingActions.length === 0" description="无需人工干预" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="efficiency-card" shadow="never">
      <template #header>
        <span class="card-title">自动化效率统计</span>
      </template>

      <el-row :gutter="40">
        <el-col :span="8">
          <div class="efficiency-item">
            <div class="efficiency-label">整体自动化率</div>
            <div class="efficiency-value">{{ efficiencyStats.overallRate }}%</div>
            <el-progress
              :percentage="efficiencyStats.overallRate"
              :stroke-width="10"
              :color="getRateColor(efficiencyStats.overallRate)"
              :show-text="false"
            />
            <div class="efficiency-desc">自动化处理 / 总处理量</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="efficiency-item">
            <div class="efficiency-label">平均处理时长</div>
            <div class="efficiency-value">{{ efficiencyStats.avgDuration }}</div>
            <div class="efficiency-desc">相比人工缩短 {{ efficiencyStats.timeSaved }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="efficiency-item">
            <div class="efficiency-label">异常自愈率</div>
            <div class="efficiency-value">{{ efficiencyStats.selfHealRate }}%</div>
            <el-progress
              :percentage="efficiencyStats.selfHealRate"
              :stroke-width="10"
              :color="getRateColor(efficiencyStats.selfHealRate)"
              :show-text="false"
            />
            <div class="efficiency-desc">自动恢复 / 总异常数</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading, CircleCheck, Warning, ArrowRight } from '@element-plus/icons-vue'
import request from '@/utils/request'

const refreshInterval = ref(null)

const overallStatus = ref('running')
const todayStats = ref({
  crawled: 0,
  crawled_trend: 0,
  matched: 0,
  matched_trend: 0,
  bids: 0,
  bids_trend: 0,
  won: 0,
  won_trend: 0
})

const flowStages = ref([
  { id: 'crawl', name: '招标采集', status: 'running', count: 0, unit: '条', autoRate: 0 },
  { id: 'match', name: '资质匹配', status: 'idle', count: 0, unit: '条', autoRate: 0 },
  { id: 'generate', name: '标书生成', status: 'idle', count: 0, unit: '份', autoRate: 0 },
  { id: 'review', name: '标书审核', status: 'idle', count: 0, unit: '份', autoRate: 0 },
  { id: 'upload', name: '标书上交', status: 'idle', count: 0, unit: '份', autoRate: 0 }
])

const anomalies = ref([])

const pendingActions = ref([])

const efficiencyStats = ref({
  overallRate: 0,
  avgDuration: '-',
  timeSaved: '-',
  selfHealRate: 0
})

const overallStatusType = computed(() => {
  const types = { running: 'success', idle: 'info', error: 'danger' }
  return types[overallStatus.value] || 'info'
})

const overallStatusText = computed(() => {
  const texts = { running: '自动化运行中', idle: '空闲', error: '异常' }
  return texts[overallStatus.value] || '未知'
})

const getTrendClass = (trend) => {
  if (trend > 0) return 'trend-up'
  if (trend < 0) return 'trend-down'
  return 'trend-flat'
}

const formatTrend = (trend) => {
  if (trend > 0) return `+${trend}%`
  if (trend < 0) return `${trend}%`
  return '0%'
}

const getRateColor = (rate) => {
  if (rate >= 80) return '#16A34A'
  if (rate >= 60) return '#EA580C'
  return '#DC2626'
}

const getStageTagType = (stage) => {
  const types = { crawl: 'primary', match: 'success', generate: 'warning', review: 'info', upload: 'danger' }
  return types[stage] || 'info'
}

const getStageName = (stage) => {
  const names = {
    crawl: '采集',
    match: '匹配',
    generate: '生成',
    review: '审核',
    upload: '上交'
  }
  return names[stage] || stage
}

const getActionTagType = (type) => {
  const types = { high_amount: 'warning', low_score: 'danger', missing_info: 'info' }
  return types[type] || 'info'
}

const getActionName = (type) => {
  const names = { high_amount: '金额审核', low_score: '低分审核', missing_info: '信息缺失' }
  return names[type] || type
}

const fetchAutomationStats = async () => {
  try {
    const res = await request.get('/v1/openclaw/automation/statistics/')
    if (res.success && res.data) {
      const data = res.data

      todayStats.value = {
        crawled: data.crawled_today || 0,
        crawled_trend: data.crawled_trend || 0,
        matched: data.matched_today || 0,
        matched_trend: data.matched_trend || 0,
        bids: data.bids_today || 0,
        bids_trend: data.bids_trend || 0,
        won: data.won_today || 0,
        won_trend: data.won_trend || 0
      }

      flowStages.value = flowStages.value.map(stage => ({
        ...stage,
        count: data[`${stage.id}_count`] || 0,
        autoRate: data[`${stage.id}_auto_rate`] || 0,
        status: data[`${stage.id}_status`] || 'idle'
      }))

      overallStatus.value = data.overall_status || 'idle'

      efficiencyStats.value = {
        overallRate: data.overall_auto_rate || 0,
        avgDuration: data.avg_duration || '0分钟',
        timeSaved: data.time_saved || '0%',
        selfHealRate: data.self_heal_rate || 0
      }
    }
  } catch (error) {
    console.error('获取自动化统计失败:', error)
  }
}

const fetchAnomalies = async () => {
}

const fetchPendingActions = async () => {
}

const handleAnomaly = async (row) => {
  try {
    await ElMessageBox.confirm('确定已处理此异常？', '确认', { type: 'info' })
    row.handled = true
    ElMessage.success('已标记为已处理')
  } catch {
    // cancelled
  }
}

const approveAction = async (row) => {
  try {
    await ElMessageBox.confirm('批准此操作？', '确认', { type: 'success' })
    row.handled = true
    ElMessage.success('已批准')
  } catch {
    // cancelled
  }
}

const rejectAction = async (row) => {
  try {
    await ElMessageBox.confirm('拒绝此操作？', '确认', { type: 'warning' })
    row.handled = true
    ElMessage.success('已拒绝')
  } catch {
    // cancelled
  }
}

const refreshData = () => {
  fetchAutomationStats()
  fetchAnomalies()
  fetchPendingActions()
}

onMounted(() => {
  refreshData()
  refreshInterval.value = setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})
</script>

<style scoped lang="scss">
.automation-monitor {
  padding: 20px;
  background-color: #F1F5F9;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .header-left {
    .page-title {
      margin: 0 0 4px 0;
      font-size: 20px;
      font-weight: 600;
      color: #1E293B;
    }

    .page-subtitle {
      margin: 0;
      font-size: 14px;
      color: #64748B;
    }
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;

    .status-tag {
      padding: 8px 16px;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 6px;

      .status-icon {
        font-size: 16px;
      }
    }
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 16px 0;

  .stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #1E293B;
  }

  .stat-label {
    font-size: 14px;
    color: #64748B;
    margin-top: 4px;
  }

  .stat-trend {
    font-size: 12px;
    margin-top: 4px;

    &.trend-up {
      color: #16A34A;
    }

    &.trend-down {
      color: #DC2626;
    }

    &.trend-flat {
      color: #64748B;
    }
  }
}

.flow-card {
  margin-bottom: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 14px;
      font-weight: 600;
    }

    .flow-legend {
      display: flex;
      gap: 16px;

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: #64748B;

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;

          &.success {
            background: #16A34A;
          }

          &.idle {
            background: #64748B;
          }

          &.error {
            background: #DC2626;
          }
        }
      }
    }
  }
}

.automation-flow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
}

.flow-stage {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #F1F5F9;
  border-radius: 8px;
  position: relative;
  flex: 1;
  transition: all 0.3s ease;

  &.active {
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
  }

  &.error {
    background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    border: 1px solid #fecaca;
  }

  .stage-icon {
    font-size: 24px;
    color: #64748B;

    .pulse {
      animation: rotate 2s linear infinite;
    }

    .el-icon-loading {
      color: #3B82F6;
    }
  }

  &.active .stage-icon {
    color: #3B82F6;
  }

  &.error .stage-icon {
    color: #DC2626;
  }

  .stage-info {
    flex: 1;

    .stage-name {
      font-size: 14px;
      font-weight: 600;
      color: #1E293B;
    }

    .stage-count {
      font-size: 12px;
      color: #64748B;
      margin-top: 2px;
    }
  }

  .stage-rate {
    text-align: center;
  }

  .flow-arrow {
    position: absolute;
    right: -20px;
    color: #CBD5E1;
    z-index: 1;
  }
}

.detail-row {
  margin-bottom: 20px;
}

.detail-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .card-title {
      font-size: 14px;
      font-weight: 600;
    }
  }
}

.efficiency-card {
  .card-title {
    font-size: 14px;
    font-weight: 600;
  }
}

.efficiency-item {
  text-align: center;
  padding: 16px;

  .efficiency-label {
    font-size: 14px;
    color: #334155;
    margin-bottom: 8px;
  }

  .efficiency-value {
    font-size: 32px;
    font-weight: bold;
    color: #1E293B;
    margin-bottom: 12px;
  }

  .efficiency-desc {
    font-size: 12px;
    color: #64748B;
    margin-top: 8px;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.pulse {
  animation: pulse 2s ease-in-out infinite;
}
</style>

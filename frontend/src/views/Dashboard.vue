<template>
  <div class="dashboard">
    <div class="welcome-banner">
      <div class="welcome-content">
        <h2 class="welcome-title">欢迎回来，{{ userStore.userInfo?.username || '用户' }} 👋</h2>
        <p class="welcome-desc">
          你有 <strong>{{ statistics.pending || 0 }}</strong> 个待处理招标，
          <strong>{{ urgentCount }}</strong> 个投标即将截止
        </p>
        <div class="welcome-actions">
          <el-button type="primary" @click="router.push('/tenders')" class="welcome-btn">
            查看待办 →
          </el-button>
          <el-button @click="router.push('/automation')" class="welcome-btn-secondary">
            开始投标 →
          </el-button>
        </div>
      </div>
      <div class="welcome-decoration" />
    </div>

    <div class="stats-grid">
      <div
        v-for="(stat, index) in statisticsCards"
        :key="stat.label"
        class="stat-card-new"
        :class="[`stat-${stat.type}`, { 'stat-clickable': stat.clickable }]"
        :style="{ animationDelay: `${index * 0.05}s` }"
        @click="stat.clickable && handleCardClick(stat)"
      >
        <div class="stat-decoration" />
        <div class="stat-icon-wrapper" :class="`icon-${stat.type}`">
          <el-icon :size="22"><component :is="stat.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid">
      <div class="dashboard-card chart-card">
        <div class="card-header">
          <span class="card-title">投标趋势</span>
          <div class="chart-period">
            <el-radio-group v-model="chartPeriod" size="small">
              <el-radio-button value="7d">7天</el-radio-button>
              <el-radio-button value="30d">30天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="chart-container">
          <v-chart :option="chartOption" autoresize class="chart" />
        </div>
      </div>

      <div class="dashboard-card quick-actions-card">
        <div class="card-header">
          <span class="card-title">快捷操作</span>
        </div>
        <div class="quick-actions-grid">
          <div class="quick-action" @click="router.push('/tenders')">
            <div class="action-icon action-primary">🔍</div>
            <span class="action-label">搜索招标</span>
          </div>
          <div class="quick-action" @click="router.push('/bids')">
            <div class="action-icon action-success">📝</div>
            <span class="action-label">新建投标</span>
          </div>
          <div class="quick-action" @click="router.push('/automation')">
            <div class="action-icon action-warning">🤖</div>
            <span class="action-label">自动投标</span>
          </div>
          <div class="quick-action" @click="router.push('/documents')">
            <div class="action-icon action-danger">📊</div>
            <span class="action-label">导出报告</span>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-grid two-col">
      <div class="dashboard-card">
        <div class="card-header">
          <span class="card-title">⏰ 即将截止</span>
        </div>
        <div class="deadline-list">
          <div v-if="urgentTenders.length === 0" class="empty-hint">暂无即将截止的招标</div>
          <div
            v-for="tender in urgentTenders"
            :key="tender.id"
            class="deadline-item"
            @click="viewTender(tender.id)"
          >
            <span class="deadline-name ellipsis">{{ tender.title }}</span>
            <span class="deadline-time" :class="getDeadlineClass(tender.deadline_date || tender.publish_date)">
              {{ getDeadlineText(tender.deadline_date || tender.publish_date) }}
            </span>
          </div>
        </div>
      </div>

      <div class="dashboard-card">
        <div class="card-header">
          <span class="card-title">🤖 自动化状态</span>
        </div>
        <div class="automation-status-list">
          <div class="auto-status-item">
            <div class="status-dot status-running" />
            <span class="status-label">采集服务运行中</span>
          </div>
          <div class="auto-status-item">
            <div class="status-dot" :class="connectionStore.isConnected ? 'status-running' : 'status-warning'" />
            <span class="status-label">{{ connectionStore.isConnected ? 'AI模型已连接' : 'AI模型未连接' }}</span>
          </div>
          <div class="auto-status-item">
            <div class="status-dot status-warning" />
            <span class="status-label">文档服务待配置</span>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-card tenders-card">
      <div class="card-header">
        <div class="card-title-wrapper">
          <span class="card-title">最近招标项目</span>
          <span class="card-badge">实时</span>
        </div>
        <el-button type="primary" link @click="router.push('/tenders')">
          查看全部 →
        </el-button>
      </div>
      <el-table
        :data="paginatedTenders"
        style="width: 100%"
        size="default"
      >
        <el-table-column prop="title" label="项目名称" min-width="280">
          <template #default="{ row }">
            <div class="project-cell">
              <span class="project-name">{{ row.title }}</span>
              <el-tag v-if="row.project_code" size="small" type="info" class="project-code">
                {{ row.project_code }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="地区" width="120" align="center">
          <template #default="{ row }">
            <span class="region-cell">{{ row.region || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small" class="status-tag">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewTender(row.id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
          :total="recentTenders.length"
          layout="total, sizes, prev, pager, next"
          background
          size="small"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { tenderApi } from '@/api/tender'
import { getTenderStatusType, getTenderStatusText } from '@/store/constants'
import { useUserStore } from '@/store/user'
import { useModelConnectionStore } from '@/store/modelConnection'
import { parseListResponse } from '@/utils/response-parser'

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent])

const router = useRouter()
const userStore = useUserStore()
const connectionStore = useModelConnectionStore()

const statistics = ref({})
const recentTenders = ref([])
const currentPage = ref(1)
const pageSize = ref(5)
const chartPeriod = ref('7d')
const trendData = ref({ labels: [], data: [] })

const getStatusType = getTenderStatusType
const getStatusText = getTenderStatusText

const urgentCount = computed(() => {
  return recentTenders.value.filter(t => {
    const dateStr = t.deadline_date || t.publish_date
    if (!dateStr) return false
    const d = new Date(dateStr)
    const diff = (d - new Date()) / (1000 * 60 * 60 * 24)
    return diff >= 0 && diff <= 7
  }).length
})

const urgentTenders = computed(() => {
  return recentTenders.value
    .filter(t => t.deadline_date || t.publish_date)
    .sort((a, b) => new Date(a.deadline_date || a.publish_date) - new Date(b.deadline_date || b.publish_date))
    .slice(0, 5)
})

const getDeadlineClass = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const diff = (d - new Date()) / (1000 * 60 * 60 * 24)
  if (diff < 0) return 'deadline-past'
  if (diff <= 3) return 'deadline-urgent'
  if (diff <= 7) return 'deadline-soon'
  return 'deadline-normal'
}

const getDeadlineText = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const diff = Math.ceil((d - new Date()) / (1000 * 60 * 60 * 24))
  if (diff < 0) return '已截止'
  if (diff === 0) return '今天截止'
  return `还剩 ${diff} 天`
}

const paginatedTenders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return recentTenders.value.slice(start, end)
})

const statisticsCards = computed(() => [
  { value: statistics.value.total || 0, label: '招标项目', type: 'primary', icon: 'Document', clickable: true, clickRoute: '/tenders' },
  { value: statistics.value.won || 0, label: '已中标', type: 'success', icon: 'CircleCheck', clickable: true, clickRoute: '/tenders?status=won' },
  { value: statistics.value.pending || 0, label: '待处理', type: 'warning', icon: 'Clock', clickable: true, clickRoute: '/tenders?status=pending' },
  { value: statistics.value.favorite || 0, label: '收藏项目', type: 'danger', icon: 'Star', clickable: true, clickRoute: '/tenders?is_favorite=true' }
])

const chartOption = computed(() => {
  const labels = trendData.value.labels || []
  const data = trendData.value.data || []
  if (!labels.length) {
    return {}
  }
  const days = labels.length
  return {
    tooltip: { trigger: 'axis', backgroundColor: '#1E293B', borderColor: '#1E293B', textStyle: { color: '#fff', fontSize: 12 } },
    grid: { top: 20, right: 16, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: '#E2E8F0' } }, axisLabel: { color: '#94A3B8', fontSize: 11 }, axisTick: { show: false } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#F1F5F9' } }, axisLabel: { color: '#94A3B8', fontSize: 11 }, axisLine: { show: false } },
    series: [{
      type: 'bar',
      data,
      barWidth: days <= 7 ? 24 : 8,
      itemStyle: { color: '#1A56DB', borderRadius: [4, 4, 0, 0] },
      emphasis: { itemStyle: { color: '#3B82F6' } }
    }]
  }
})

const handleCardClick = (card) => {
  if (card.clickable && card.clickRoute) {
    const [path, queryStr] = card.clickRoute.split('?')
    const query = {}
    if (queryStr) {
      queryStr.split('&').forEach(pair => {
        const [key, value] = pair.split('=')
        if (key && value) query[key] = decodeURIComponent(value)
      })
    }
    router.push({ path, query })
  }
}

const viewTender = (id) => {
  router.push(`/tenders/${id}`)
}

const handleSizeChange = () => { currentPage.value = 1 }
const handleCurrentChange = () => {}

const fetchData = async () => {
  try {
    const [statsRes, tendersRes] = await Promise.all([
      tenderApi.getStatistics(),
      tenderApi.getList({ page_size: 100 })
    ])
    statistics.value = statsRes.data || {}
    const { list: tenders } = parseListResponse(tendersRes)
    recentTenders.value = tenders
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

const fetchTrendData = async () => {
  try {
    const days = chartPeriod.value === '7d' ? 7 : 30
    const res = await tenderApi.getTrend({ days })
    if (res.data) {
      trendData.value = res.data
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

watch(chartPeriod, () => {
  fetchTrendData()
})

onMounted(() => {
  fetchData()
  fetchTrendData()
})
</script>

<style scoped lang="scss">
.dashboard {
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-banner {
  background: var(--brand-gradient);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xl) var(--spacing-2xl);
  margin-bottom: var(--spacing-lg);
  color: #fff;
  position: relative;
  overflow: hidden;

  .welcome-content {
    position: relative;
    z-index: 2;
  }

  .welcome-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    margin: 0 0 var(--spacing-xs);
  }

  .welcome-desc {
    font-size: var(--font-size-md);
    opacity: 0.85;
    margin: 0 0 var(--spacing-lg);

    strong {
      font-weight: var(--font-weight-bold);
    }
  }

  .welcome-actions {
    display: flex;
    gap: var(--spacing-sm);
  }

  .welcome-btn {
    background: rgba(255, 255, 255, 0.2) !important;
    border: none !important;
    color: #fff !important;
    border-radius: var(--radius-md) !important;

    &:hover {
      background: rgba(255, 255, 255, 0.3) !important;
    }
  }

  .welcome-btn-secondary {
    background: transparent !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    color: #fff !important;
    border-radius: var(--radius-md) !important;

    &:hover {
      background: rgba(255, 255, 255, 0.1) !important;
    }
  }

  .welcome-decoration {
    position: absolute;
    right: -30px;
    top: -30px;
    width: 160px;
    height: 160px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 50%;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.stat-card-new {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  border: 1px solid var(--color-border-lighter);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
  animation: fadeInUp 0.4s ease backwards;

  &:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  &.stat-clickable {
    cursor: pointer;
  }

  .stat-decoration {
    position: absolute;
    top: -12px;
    right: -12px;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    opacity: 0.5;
  }

  &.stat-primary .stat-decoration { background: var(--color-primary-50); }
  &.stat-success .stat-decoration { background: var(--color-success-50); }
  &.stat-warning .stat-decoration { background: var(--color-warning-50); }
  &.stat-danger .stat-decoration { background: var(--color-danger-50); }

  .stat-icon-wrapper {
    width: 44px;
    height: 44px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: var(--spacing-sm);

    &.icon-primary { background: var(--color-primary-50); color: var(--color-primary); }
    &.icon-success { background: var(--color-success-50); color: var(--color-success); }
    &.icon-warning { background: var(--color-warning-50); color: var(--color-warning); }
    &.icon-danger { background: var(--color-danger-50); color: var(--color-danger); }
  }

  .stat-value {
    font-size: 24px;
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    line-height: 1.2;
  }

  .stat-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: 2px;
  }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);

  &.two-col {
    grid-template-columns: 1fr 1fr;
  }
}

.dashboard-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);
  box-shadow: var(--shadow-card);
  overflow: hidden;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  .card-title {
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
  }

  .card-title-wrapper {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .card-badge {
    font-size: var(--font-size-xs);
    color: var(--color-primary);
    background: var(--color-primary-50);
    padding: 1px 8px;
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-medium);
  }
}

.chart-card {
  .chart-container {
    padding: var(--spacing-md);
  }

  .chart {
    height: 220px;
  }
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
}

.quick-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:hover {
    transform: translateY(-2px);
  }

  .action-icon {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-md);
    font-size: 20px;

    &.action-primary { background: var(--color-primary-50); }
    &.action-success { background: var(--color-success-50); }
    &.action-warning { background: var(--color-warning-50); }
    &.action-danger { background: var(--color-danger-50); }
  }

  .action-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    font-weight: var(--font-weight-medium);
  }
}

.deadline-list {
  padding: var(--spacing-md) var(--spacing-lg);
}

.deadline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  border-bottom: 1px solid var(--color-border-lighter);
  cursor: pointer;
  transition: all var(--transition-fast);

  &:last-child { border-bottom: none; }
  &:hover { background: var(--color-bg-hover); margin: 0 calc(-1 * var(--spacing-lg)); padding: var(--spacing-sm) var(--spacing-lg); border-radius: var(--radius-sm); }

  .deadline-name {
    font-size: var(--font-size-sm);
    color: var(--color-text-primary);
    font-weight: var(--font-weight-medium);
    flex: 1;
    margin-right: var(--spacing-md);
  }

  .deadline-time {
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    white-space: nowrap;

    &.deadline-urgent { color: var(--color-danger); }
    &.deadline-soon { color: var(--color-warning); }
    &.deadline-normal { color: var(--color-text-secondary); }
    &.deadline-past { color: var(--color-text-tertiary); }
  }
}

.empty-hint {
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  padding: var(--spacing-xl);
}

.automation-status-list {
  padding: var(--spacing-lg);
}

.auto-status-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);

  &:last-child { margin-bottom: 0; }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;

    &.status-running { background: var(--color-success); box-shadow: 0 0 6px var(--color-success); }
    &.status-warning { background: var(--color-warning); }
    &.status-error { background: var(--color-danger); }
  }

  .status-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-primary);
  }
}

.tenders-card {
  margin-bottom: var(--spacing-lg);

  :deep(.el-table) {
    th {
      background-color: var(--color-bg-base) !important;
      font-weight: var(--font-weight-medium);
      color: var(--color-text-primary);
      font-size: var(--font-size-sm);
    }

    td {
      border-bottom-color: var(--color-border-lighter);
      font-size: var(--font-size-sm);
    }

    tr:hover > td {
      background-color: var(--color-bg-hover);
    }
  }
}

.project-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-name {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.project-code {
  width: fit-content;
  font-size: var(--font-size-xs);
}

.region-cell {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.status-tag {
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-lighter);
}

@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .dashboard-grid { grid-template-columns: 1fr; }
  .dashboard-grid.two-col { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
  .welcome-banner .welcome-actions { flex-direction: column; }
}
</style>

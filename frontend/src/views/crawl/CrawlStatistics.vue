<template>
  <div class="crawl-statistics">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">采集数据统计</h2>
        <p class="page-desc">集中展示和管理各网站采集数据统计信息</p>
      </div>
      <div class="header-actions">
        <el-button @click="fetchData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="handleExport" :loading="exportLoading">
          <el-icon><Download /></el-icon>
          导出Excel
        </el-button>
      </div>
    </div>

    <div class="stats-grid">
      <div
        v-for="(stat, index) in overviewCards"
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
          <span class="card-title">采集趋势</span>
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

      <div class="dashboard-card anomaly-card">
        <div class="card-header">
          <span class="card-title">异常监控</span>
          <el-tag v-if="anomalies.length > 0" type="danger" size="small" round>
            {{ anomalies.length }}
          </el-tag>
          <el-tag v-else type="success" size="small" round>正常</el-tag>
        </div>
        <div class="anomaly-list">
          <div v-if="anomalies.length === 0" class="empty-hint">
            <el-icon :size="32" color="#16A34A"><CircleCheck /></el-icon>
            <p>所有网站采集状态正常</p>
          </div>
          <div
            v-for="(item, index) in anomalies"
            :key="index"
            class="anomaly-item"
            :class="`anomaly-${item.type}`"
          >
            <div class="anomaly-icon">
              <el-icon v-if="item.type === 'data_fluctuation'" :size="18"><TrendCharts /></el-icon>
              <el-icon v-else-if="item.type === 'crawl_error'" :size="18"><WarningFilled /></el-icon>
              <el-icon v-else :size="18"><Clock /></el-icon>
            </div>
            <div class="anomaly-content">
              <div class="anomaly-source">{{ item.source_name }}</div>
              <div class="anomaly-message">{{ item.message }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="dashboard-card">
      <div class="card-header">
        <span class="card-title">网站采集数据概览</span>
      </div>
      <div class="table-wrapper">
        <el-table
          :data="sourceStats"
          stripe
          style="width: 100%"
          :default-sort="{ prop: 'total_count', order: 'descending' }"
        >
          <el-table-column prop="name" label="网站名称" min-width="160" fixed>
            <template #default="{ row }">
              <div class="source-name">
                <el-icon :size="14" class="source-icon"><Link /></el-icon>
                <span>{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="source_type" label="类型" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getSourceTypeTag(row.source_type)" size="small">
                {{ getSourceTypeText(row.source_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="today_count" label="今日采集" width="100" align="center" sortable>
            <template #default="{ row }">
              <span :class="{ 'count-highlight': row.today_count > 0 }">{{ row.today_count }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="yesterday_count" label="昨日采集" width="100" align="center" sortable />
          <el-table-column prop="total_count" label="累计采集" width="100" align="center" sortable>
            <template #default="{ row }">
              <span class="count-total">{{ row.total_count }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="matched_count" label="已匹配" width="90" align="center" sortable />
          <el-table-column prop="ignored_count" label="已忽略" width="90" align="center" sortable>
            <template #default="{ row }">
              <span :class="{ 'count-warning': row.ignored_count > 0 }">{{ row.ignored_count }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="pending_count" label="待处理" width="90" align="center" sortable>
            <template #default="{ row }">
              <span :class="{ 'count-danger': row.pending_count > 50 }">{{ row.pending_count }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="deleted_count" label="已删除" width="90" align="center" sortable />
          <el-table-column prop="last_crawl_at" label="最后采集时间" width="170" align="center">
            <template #default="{ row }">
              <span v-if="row.last_crawl_at">{{ row.last_crawl_at }}</span>
              <span v-else class="text-muted">暂无记录</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80" align="center" fixed="right">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <div class="dashboard-card">
      <div class="card-header">
        <span class="card-title">数据处理统计</span>
      </div>
      <div class="processing-grid">
        <div class="processing-item">
          <div class="processing-label">同步待处理</div>
          <div class="processing-value" :class="{ 'count-danger': overview.sync_pending > 0 }">
            {{ overview.sync_pending || 0 }}
          </div>
          <div class="processing-desc">采集结果待同步到招标项目</div>
        </div>
        <div class="processing-item">
          <div class="processing-label">已同步</div>
          <div class="processing-value count-success">{{ overview.sync_synced || 0 }}</div>
          <div class="processing-desc">已成功同步的采集结果</div>
        </div>
        <div class="processing-item">
          <div class="processing-label">不匹配数据</div>
          <div class="processing-value" :class="{ 'count-warning': overview.total_unmatched > 0 }">
            {{ overview.total_unmatched || 0 }}
          </div>
          <div class="processing-desc">已忽略的采集结果</div>
        </div>
        <div class="processing-item">
          <div class="processing-label">已删除数据</div>
          <div class="processing-value">{{ overview.total_deleted || 0 }}</div>
          <div class="processing-desc">标记为删除的招标项目</div>
        </div>
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
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { tenderApi } from '@/api/tender'
import { ElMessage } from 'element-plus'
import {
  Refresh, Download, Link, TrendCharts, WarningFilled,
  Clock, CircleCheck, DataBoard, Collection, Delete, Warning
} from '@element-plus/icons-vue'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()

const loading = ref(false)
const exportLoading = ref(false)
const chartPeriod = ref('7d')
const overview = ref({})
const sourceStats = ref([])
const trendData = ref({ labels: [], data: [] })
const anomalies = ref([])

const overviewCards = computed(() => [
  { value: overview.value.total_sources || 0, label: '采集网站', type: 'primary', icon: 'DataBoard', clickable: true, clickRoute: '/system/templates' },
  { value: overview.value.today_crawled || 0, label: '今日采集', type: 'success', icon: 'Collection', clickable: true, clickRoute: '/tenders' },
  { value: overview.value.total_crawled || 0, label: '累计采集', type: 'warning', icon: 'TrendCharts', clickable: true, clickRoute: '/tenders' },
  { value: overview.value.total_unmatched || 0, label: '不匹配数据', type: 'danger', icon: 'Warning', clickable: true, clickRoute: '/schedules' },
])

const chartOption = computed(() => {
  const labels = trendData.value.labels || []
  const data = trendData.value.data || []
  if (!labels.length) return {}

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E293B',
      borderColor: '#1E293B',
      textStyle: { color: '#fff', fontSize: 12 }
    },
    grid: { top: 20, right: 16, bottom: 30, left: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#94A3B8', fontSize: 11 },
      axisLine: { show: false }
    },
    series: [{
      type: 'bar',
      data,
      barWidth: labels.length <= 7 ? 24 : 8,
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#3B82F6' },
            { offset: 1, color: '#1A56DB' }
          ]
        },
        borderRadius: [4, 4, 0, 0]
      },
      emphasis: { itemStyle: { color: '#60A5FA' } }
    }]
  }
})

const getSourceTypeText = (type) => {
  const map = { government: '政府', enterprise: '企业', construction: '建筑', other: '其他' }
  return map[type] || type
}

const handleCardClick = (card) => {
  if (card.clickable && card.clickRoute) {
    router.push(card.clickRoute)
  }
}

const getSourceTypeTag = (type) => {
  const map = { government: '', enterprise: 'success', construction: 'warning', other: 'info' }
  return map[type] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    const days = chartPeriod.value === '7d' ? 7 : 30
    const res = await tenderApi.getCrawlStatistics({ days })
    if (res.data) {
      overview.value = res.data.overview || {}
      sourceStats.value = res.data.source_stats || []
      trendData.value = res.data.trend || { labels: [], data: [] }
      anomalies.value = res.data.anomalies || []
    }
  } catch (error) {
    console.error('获取采集统计数据失败:', error)
    ElMessage.error('获取采集统计数据失败')
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exportLoading.value = true
  try {
    const res = await tenderApi.exportCrawlData()
    const blob = new Blob([res], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const today = new Date()
    const dateStr = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`
    link.download = `采集数据统计_${dateStr}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exportLoading.value = false
  }
}

watch(chartPeriod, () => {
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.crawl-statistics {
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-lg);

  .header-left {
    .page-title {
      font-size: var(--font-size-2xl);
      font-weight: var(--font-weight-bold);
      color: var(--color-text-primary);
      margin: 0 0 var(--spacing-xs);
    }

    .page-desc {
      font-size: var(--font-size-sm);
      color: var(--color-text-secondary);
      margin: 0;
    }
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-sm);
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
}

.dashboard-card {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  margin-bottom: var(--spacing-md);

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
}

.chart-card {
  .chart-container {
    padding: var(--spacing-md);
  }

  .chart {
    height: 260px;
  }
}

.anomaly-card {
  .anomaly-list {
    padding: var(--spacing-md) var(--spacing-lg);
    max-height: 300px;
    overflow-y: auto;
  }

  .empty-hint {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-2xl) 0;
    color: var(--color-text-secondary);

    p {
      margin-top: var(--spacing-sm);
      font-size: var(--font-size-sm);
    }
  }

  .anomaly-item {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--color-border-lighter);

    &:last-child { border-bottom: none; }

    .anomaly-icon {
      width: 32px;
      height: 32px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    &.anomaly-data_fluctuation .anomaly-icon {
      background: var(--color-warning-50);
      color: var(--color-warning);
    }

    &.anomaly-crawl_error .anomaly-icon {
      background: var(--color-danger-50);
      color: var(--color-danger);
    }

    &.anomaly-pending_backlog .anomaly-icon {
      background: var(--color-primary-50);
      color: var(--color-primary);
    }

    .anomaly-content {
      flex: 1;
      min-width: 0;
    }

    .anomaly-source {
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-medium);
      color: var(--color-text-primary);
    }

    .anomaly-message {
      font-size: var(--font-size-xs);
      color: var(--color-text-secondary);
      margin-top: 2px;
    }
  }
}

.table-wrapper {
  padding: var(--spacing-md) var(--spacing-lg);
}

.source-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);

  .source-icon {
    color: var(--color-primary);
  }
}

.count-highlight {
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.count-total {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.count-warning {
  color: var(--color-warning);
  font-weight: var(--font-weight-medium);
}

.count-danger {
  color: var(--color-danger);
  font-weight: var(--font-weight-semibold);
}

.count-success {
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.text-muted {
  color: var(--color-text-placeholder);
}

.processing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
}

.processing-item {
  text-align: center;
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  background: var(--color-bg-hover);

  .processing-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .processing-value {
    font-size: 28px;
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    line-height: 1.2;
  }

  .processing-desc {
    font-size: var(--font-size-xs);
    color: var(--color-text-placeholder);
    margin-top: var(--spacing-xs);
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .processing-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .processing-grid {
    grid-template-columns: 1fr;
  }
}
</style>

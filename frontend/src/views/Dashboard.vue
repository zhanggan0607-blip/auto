<template>
  <div class="dashboard">
    <PageHeader title="数据概览" subtitle="投标自动化系统实时数据统计" />

    <StatCards :stats="statisticsCards" class="stat-cards-wrapper" @card-click="handleCardClick" />

    <el-card class="content-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="card-title-wrapper">
            <span class="card-title">最近招标项目</span>
            <span class="card-subtitle">实时更新</span>
          </div>
          <el-button type="primary" link @click="router.push('/tenders')">
            查看全部
            <el-icon class="arrow-icon"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      <el-table
        :data="paginatedTenders"
        style="width: 100%"
        size="default"
        :row-class-name="tableRowClassName"
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
        <el-table-column prop="publish_date" label="发布日期" width="140" align="center">
          <template #default="{ row }">
            <span class="date-cell">{{ row.publish_date || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="region" label="地区" width="140" align="center">
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
        <el-table-column label="原始链接" width="120" align="center">
          <template #default="{ row }">
            <el-tooltip content="打开原始链接" placement="top">
              <el-button
                type="primary"
                link
                :disabled="!row.source_url"
                @click="openSourceUrl(row.source_url)"
                class="action-btn"
              >
                <el-icon><Link /></el-icon>
                链接
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewTender(row.id)" class="action-btn">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :total="statistics.total || 0"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Location, Link, Collection } from '@element-plus/icons-vue'
import { tenderApi } from '@/api/tender'
import { getTenderStatusType, getTenderStatusText } from '@/store/constants'
import { PageHeader, StatCards } from '@/components'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const statistics = ref({})
const recentTenders = ref([])
const currentPage = ref(1)
const pageSize = ref(5)

const getStatusType = getTenderStatusType
const getStatusText = getTenderStatusText

const paginatedTenders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return recentTenders.value.slice(start, end)
})

const statisticsCards = computed(() => [
  {
    value: statistics.value.total || 0,
    label: '招标项目',
    type: 'default',
    icon: 'Document',
    clickable: true,
    clickRoute: '/tenders'
  },
  {
    value: statistics.value.pending || 0,
    label: '待处理',
    type: 'warning',
    icon: 'Clock',
    clickable: false
  },
  {
    value: statistics.value.collected || 0,
    label: '采集数量',
    type: 'info',
    icon: 'Collection',
    clickable: false
  },
  {
    value: statistics.value.won || 0,
    label: '已中标',
    type: 'success',
    icon: 'CircleCheck',
    clickable: false
  },
  {
    value: statistics.value.favorite || 0,
    label: '收藏项目',
    type: 'danger',
    icon: 'Star',
    clickable: false
  }
])

const tableRowClassName = ({ rowIndex }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

const viewTender = (id) => {
  router.push(`/tenders/${id}`)
}

const openSourceUrl = async (url) => {
  if (!url) {
    ElMessage.warning('无原始链接')
    return
  }
  const openedWindow = window.open(url, '_blank', 'noopener,noreferrer')
  if (openedWindow) {
    setTimeout(() => {
      try {
        const doc = openedWindow.document
        const isAboutBlank = doc.domain === 'about:blank'
        const isEmptyPage = doc.readyState === 'complete' && doc.body?.innerHTML === ''
        const pageContent = doc.body?.innerText || ''
        const is404Page = pageContent.includes('不存在') || pageContent.includes('404') || pageContent.includes('无法访问')
        if (isAboutBlank || isEmptyPage || is404Page) {
          openedWindow.close()
          ElMessageBox.confirm(
            '原始链接可能已失效（网页已被删除或移动）。<br/><br/>是否跳转到中国政府采购网首页搜索相关项目？',
            '链接失效提示',
            {
              confirmButtonText: '跳转搜索',
              cancelButtonText: '关闭',
              type: 'warning',
              dangerouslyUseHTMLString: true
            }
          ).then(() => {
            window.open('http://www.ccgp.gov.cn', '_blank', 'noopener,noreferrer')
          }).catch(() => {})
        }
      } catch (e) {}
    }, 2000)
  }
}

const handleCardClick = (card) => {
  if (card.clickable && card.clickRoute) {
    router.push(card.clickRoute)
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const fetchData = async () => {
  try {
    const [statsRes, tendersRes] = await Promise.all([
      tenderApi.getStatistics(),
      tenderApi.getList({ page_size: 100 })
    ])

    statistics.value = statsRes.data || {}
    recentTenders.value = tendersRes.results || tendersRes.data?.list || []
  } catch (error) {
    console.error('获取数据失败:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 0;
  background-color: var(--color-bg-page);
  min-height: calc(100vh - var(--header-height));
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-cards-wrapper {
  margin-bottom: var(--spacing-lg);
}

.content-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);
  overflow: hidden;

  :deep(.el-card__header) {
    padding: var(--spacing-lg) var(--spacing-xl);
    background-color: var(--color-bg-white);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-card__body) {
    padding: 0;
  }

  :deep(.el-table) {
    border-radius: 0;
    table-layout: fixed;
    word-break: break-all;

    th {
      background-color: var(--color-bg-base) !important;
      font-weight: var(--font-weight-medium);
      color: var(--color-text-primary);
      font-size: var(--font-size-sm);
    }

    td {
      border-bottom-color: var(--color-border-lighter);
      padding: var(--spacing-md) var(--spacing-lg);
      white-space: nowrap;
      overflow: visible;
    }

    .cell {
      white-space: nowrap;
      overflow: visible;
    }

    tr.even-row > td {
      background-color: var(--color-bg-white);
    }

    tr.odd-row > td {
      background-color: rgba(0, 0, 0, 0.01);
    }

    tr:hover > td {
      background-color: var(--color-bg-hover) !important;
    }
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

.card-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  background: var(--color-bg-base);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.arrow-icon {
  margin-left: 4px;
  transition: transform var(--transition-fast);
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

.date-cell {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.region-cell {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
}

.status-tag {
  border-radius: var(--radius-sm);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
}

.action-btn {
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
  white-space: nowrap;

  &:hover {
    color: var(--color-primary);
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-lg);
  background: var(--color-bg-white);
  border-top: 1px solid var(--color-border-lighter);

  :deep(.el-pagination) {
    font-weight: var(--font-weight-normal);
  }
}
</style>

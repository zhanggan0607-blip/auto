<template>
  <div class="sidebar-wrapper">
    <div class="automation-status-mini" @click="goToAutomation" v-if="!isCollapse">
      <div class="status-indicator" :class="automationStatusClass" />
      <span class="status-text">{{ automationStatusText }}</span>
      <el-icon class="arrow"><ArrowRight /></el-icon>
    </div>

    <nav class="sidebar-nav" :class="{ 'is-collapse': isCollapse }">
      <div
        v-for="item in visibleMenuItems"
        :key="item.path"
        class="nav-group"
      >
        <div
          v-if="!item.children"
          class="nav-item"
          :class="{ 'is-active': isActive(item.path) }"
          @click="navigateTo(item.path)"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-title">{{ item.title }}</span>
          <el-badge v-if="item.badge && item.badge > 0" :value="item.badge" :max="99" class="nav-badge" />
        </div>

        <div
          v-else
          class="nav-item has-children"
          :class="{ 'is-active': isActive(item.path), 'is-opened': openedMenus.includes(item.path) }"
          @click="toggleMenu(item.path)"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span class="nav-title">{{ item.title }}</span>
          <el-icon class="arrow-icon" :class="{ 'is-opened': openedMenus.includes(item.path) }">
            <ArrowRight />
          </el-icon>
        </div>

        <transition name="submenu-expand">
          <div
            v-if="item.children && !isCollapse && openedMenus.includes(item.path)"
            class="nav-submenu"
          >
            <div
              v-for="child in item.children"
              :key="child.path"
              class="nav-item-child"
              :class="{ 'is-active': isActive(child.path) }"
              @click="navigateTo(child.path)"
            >
              <span class="nav-title">{{ child.title }}</span>
            </div>
          </div>
        </transition>

        <el-tooltip
          v-if="item.children && isCollapse"
          :content="item.title"
          placement="right"
          :show-after="200"
        >
          <div
            class="nav-item collapse-item"
            :class="{ 'is-active': isActive(item.path) }"
            @click="navigateTo(item.children[0]?.path)"
          >
            <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          </div>
        </el-tooltip>
      </div>

      <div class="nav-footer">
        <div class="service-status-section">
          <div class="service-status-row" v-if="!isCollapse">
            <div
              v-for="service in services"
              :key="service.name"
              class="service-dot"
              :class="`status-${service.status}`"
              :title="`${service.name}: ${service.message}`"
            >
              <el-tooltip :content="`${service.name}: ${service.message}`" placement="right">
                <el-icon :size="10"><component :is="getServiceIcon(service.status)" /></el-icon>
              </el-tooltip>
            </div>
          </div>
          <div class="service-status-summary" v-if="!isCollapse">
            <el-tag :type="overallStatusType" size="small" effect="plain">{{ overallStatusText }}</el-tag>
            <el-button link @click="refreshServices" :loading="loadingServices" :icon="Refresh" />
          </div>
          <div class="service-status-collapsed" v-else>
            <el-tooltip :content="`服务状态: ${overallStatusText}`" placement="right">
              <el-icon :size="16" :class="`status-icon-${overallStatus}`"><component :is="getOverallStatusIcon()" /></el-icon>
            </el-tooltip>
          </div>
        </div>
        <div
          class="nav-item"
          :class="{ 'is-active': isActive('/notifications') }"
          @click="navigateTo('/notifications')"
        >
          <el-icon class="nav-icon"><Bell /></el-icon>
          <span class="nav-title">消息通知</span>
          <el-badge v-if="unreadCount > 0" :value="unreadCount" :max="99" class="nav-badge" />
        </div>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Bell, CircleCheck, CircleClose, Refresh, QuestionFilled, Warning } from '@element-plus/icons-vue'
import { getSystemServices } from '@/api/system'

const props = defineProps({
  isCollapse: {
    type: Boolean,
    default: false
  },
  unreadCount: {
    type: Number,
    default: 0
  }
})

const route = useRoute()
const router = useRouter()

const services = ref([])
const loadingServices = ref(false)

const getServiceIcon = (status) => {
  if (status === 'running') return CircleCheck
  if (status === 'error' || status === 'stopped') return CircleClose
  if (status === 'degraded') return Warning
  return QuestionFilled
}

const overallStatus = computed(() => {
  const statuses = services.value.map(s => s.status)
  if (statuses.includes('error')) return 'unhealthy'
  if (statuses.includes('stopped') || statuses.includes('degraded')) return 'degraded'
  if (statuses.every(s => s === 'running')) return 'healthy'
  return 'unknown'
})

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
    'unknown': '未知'
  }
  return textMap[overallStatus.value] || '未知'
})

const getOverallStatusIcon = () => {
  if (overallStatus.value === 'healthy') return CircleCheck
  if (overallStatus.value === 'unhealthy') return CircleClose
  if (overallStatus.value === 'degraded') return Warning
  return QuestionFilled
}

const fetchServices = async () => {
  try {
    loadingServices.value = true
    const response = await getSystemServices()
    if (response.status === 200 || response.status === 201) {
      const data = response.data || response
      services.value = data.services || []
    }
  } catch (error) {
    console.error('获取服务状态失败:', error)
  } finally {
    loadingServices.value = false
  }
}

const refreshServices = () => {
  fetchServices()
}

let servicesInterval = null

onMounted(() => {
  fetchServices()
  servicesInterval = setInterval(fetchServices, 30000)
})

onUnmounted(() => {
  if (servicesInterval) {
    clearInterval(servicesInterval)
  }
})

const openedMenus = ref([])

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const navigateTo = (path) => {
  if (path) {
    router.push(path)
  }
}

const toggleMenu = (path) => {
  const index = openedMenus.value.indexOf(path)
  if (index > -1) {
    openedMenus.value.splice(index, 1)
  } else {
    openedMenus.value.push(path)
  }
}

const goToAutomation = () => {
  router.push('/automation')
}

const automationStatus = computed(() => {
  return 'running'
})

const automationStatusClass = computed(() => {
  const status = automationStatus.value
  return {
    'status-running': status === 'running',
    'status-idle': status === 'idle',
    'status-error': status === 'error'
  }
})

const automationStatusText = computed(() => {
  const status = automationStatus.value
  const texts = {
    running: '自动化运行中',
    idle: '自动化空闲',
    error: '自动化异常'
  }
  return texts[status] || '自动化空闲'
})

const visibleMenuItems = computed(() => [
  { path: '/dashboard', title: '首页', icon: 'DataBoard' },
  {
    path: '/tender',
    title: '招标采集',
    icon: 'Search',
    children: [
      { path: '/schedules', title: '定时采集' },
      { path: '/keywords', title: '关键词管理' }
    ]
  },
  {
    path: '/bid',
    title: '投标管理',
    icon: 'TrendCharts',
    children: [
      { path: '/tenders', title: '已投标项目' },
      { path: '/bids', title: '投标记录' }
    ]
  },
  {
    path: '/enterprise',
    title: '企业管理',
    icon: 'OfficeBuilding',
    children: [
      { path: '/company', title: '公司信息' },
      { path: '/documents', title: '文档管理' },
      { path: '/vectorlib', title: '文档向量库' }
    ]
  },
  { path: '/automation', title: '自动化工作台', icon: 'Monitor' },
  { path: '/automation-monitor', title: '自动化监控', icon: 'DataAnalysis' },
  {
    path: '/system',
    title: '系统管理',
    icon: 'Setting',
    children: [
      { path: '/system/users', title: '用户管理' },
      { path: '/system/models', title: '模型选择' },
      { path: '/system/monitor', title: '服务监控' },
      { path: '/system/playground', title: 'AI Playground' },
      { path: '/system/multi-view-demo', title: 'MultiViewDialog演示' },
      { path: '/system/templates', title: '网站模板管理' }
    ]
  }
])

watch(() => route.path, () => {
  visibleMenuItems.value.forEach(item => {
    if (item.children) {
      const hasActiveChild = item.children.some(child => route.path === child.path)
      if (hasActiveChild && !openedMenus.value.includes(item.path)) {
        openedMenus.value.push(item.path)
      }
    }
  })
}, { immediate: true })
</script>

<style scoped lang="scss">
.sidebar-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 2px;

    &:hover {
      background: rgba(255, 255, 255, 0.25);
    }
  }

  &.is-collapse {
    padding: 8px 4px;
  }
}

.automation-status-mini {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  margin: 8px 8px 4px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .status-indicator {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 8px;

    &.status-running {
      background: var(--color-success);
      box-shadow: 0 0 6px var(--color-success);
      animation: pulse 2s infinite;
    }

    &.status-idle {
      background: #909399;
    }

    &.status-error {
      background: var(--color-danger);
      box-shadow: 0 0 6px var(--color-danger);
    }
  }

  .status-text {
    flex: 1;
    font-size: 12px;
    color: var(--sidebar-text);
  }

  .arrow {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.3);
    transition: transform 0.2s ease;
  }

  &:hover .arrow {
    transform: translateX(2px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.nav-group {
  margin-bottom: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 12px;
  margin: 2px 0;
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;

  .nav-icon {
    font-size: 17px;
    margin-right: 10px;
    color: inherit;
    flex-shrink: 0;
  }

  .nav-title {
    font-size: var(--font-size-sm);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .nav-badge {
    position: absolute;
    right: 32px;
  }

  .arrow-icon {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.4);
    transition: transform 0.25s ease;
    margin-left: auto;

    &.is-opened {
      transform: rotate(90deg);
    }
  }

  &:hover {
    background: var(--sidebar-hover-bg);
    color: var(--sidebar-text-active);
  }

  &.is-active {
    background: var(--sidebar-active-bg);
    color: var(--sidebar-text-active);
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.25);

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 20px;
      background: var(--sidebar-text-active);
      border-radius: 0 3px 3px 0;
    }
  }

  &.is-opened {
    background: var(--sidebar-hover-bg);
    color: var(--sidebar-text-active);
  }

  &.has-children {
    padding-right: 32px;
  }
}

.nav-item-child {
  display: flex;
  align-items: center;
  height: 36px;
  padding: 0 12px 0 44px;
  margin: 1px 0;
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;

  .nav-title {
    white-space: nowrap;
  }

  &:hover {
    background: var(--sidebar-hover-bg);
    color: var(--sidebar-text-active);
  }

  &.is-active {
    background: rgba(0, 102, 204, 0.15);
    color: var(--sidebar-primary-light, #3399FF);
    font-weight: var(--font-weight-medium);

    &::before {
      content: '';
      position: absolute;
      left: 36px;
      width: 4px;
      height: 4px;
      background: var(--color-primary-light);
      border-radius: 50%;
    }
  }
}

.nav-submenu {
  overflow: hidden;
  background: rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-sm);
  margin: 2px 0;
  padding: 4px 0;
}

.submenu-expand-enter-active {
  transition: all 0.25s ease-out;
}

.submenu-expand-leave-active {
  transition: all 0.2s ease-in;
}

.submenu-expand-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.submenu-expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.is-collapse {
  .collapse-item {
    justify-content: center;
    padding: 0;

    .nav-icon {
      margin-right: 0;
    }
  }
}

.nav-footer {
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;

  .service-status-section {
    padding: 8px 12px;
    margin-bottom: 8px;

    .service-status-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 8px;
    }

    .service-dot {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.05);
      transition: all 0.2s;

      &.status-running {
        color: var(--color-success);
        background: rgba(103, 194, 58, 0.15);
      }

      &.status-error {
        color: var(--color-danger);
        background: rgba(245, 108, 108, 0.15);
      }

      &.status-stopped {
        color: var(--color-warning);
        background: rgba(230, 162, 60, 0.15);
      }

      &.status-degraded {
        color: var(--color-warning);
        background: rgba(230, 162, 60, 0.1);
      }

      &.status-unknown {
        color: var(--sidebar-text);
        background: rgba(255, 255, 255, 0.05);
      }
    }

    .service-status-summary {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .service-status-collapsed {
      display: flex;
      justify-content: center;
      padding: 8px 0;

      .status-icon-healthy {
        color: var(--color-success);
      }

      .status-icon-degraded {
        color: var(--color-warning);
      }

      .status-icon-unhealthy {
        color: var(--color-danger);
      }

      .status-icon-unknown {
        color: var(--sidebar-text);
      }
    }
  }
}
</style>

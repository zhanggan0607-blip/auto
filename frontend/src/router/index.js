import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'tenders',
        name: 'TenderList',
        component: () => import('@/views/tender/TenderList.vue'),
        meta: { title: '已投标项目管理' }
      },
      {
        path: 'tenders/:id',
        name: 'TenderDetail',
        component: () => import('@/views/tender/TenderDetail.vue'),
        meta: { title: '招标详情' }
      },
      {
        path: 'documents',
        name: 'DocumentList',
        component: () => import('@/views/document/DocumentList.vue'),
        meta: { title: '文档管理' }
      },
      {
        path: 'documents/generate',
        name: 'DocumentGenerate',
        component: () => import('@/views/document/DocumentGenerate.vue'),
        meta: { title: '生成文档' }
      },
      {
        path: 'bids',
        name: 'BidList',
        component: () => import('@/views/bid/BidList.vue'),
        meta: { title: '投标记录' }
      },
      {
        path: 'bids/:id',
        name: 'BidDetail',
        component: () => import('@/views/bid/BidDetail.vue'),
        meta: { title: '投标详情' }
      },
      {
        path: 'notifications',
        name: 'NotificationList',
        component: () => import('@/views/notification/NotificationList.vue'),
        meta: { title: '消息通知' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心' }
      },
      {
        path: 'company',
        name: 'EnterpriseInfo',
        component: () => import('@/views/CompanyInfo.vue'),
        meta: { title: '公司信息' }
      },
      {
        path: 'keywords',
        name: 'KeywordList',
        component: () => import('@/views/KeywordList.vue'),
        meta: { title: '关键词管理' }
      },
      {
        path: 'schedules',
        name: 'ScheduleList',
        component: () => import('@/views/ScheduleList.vue'),
        meta: { title: '定时采集' }
      },
      {
        path: 'schedules/create',
        name: 'CreateSchedule',
        component: () => import('@/views/schedule/CreateSchedule.vue'),
        meta: { title: '新建采集计划' }
      },
      {
        path: 'schedules/edit/:id',
        name: 'EditSchedule',
        component: () => import('@/views/schedule/EditSchedule.vue'),
        meta: { title: '编辑采集计划' }
      },
      {
        path: 'vectorlib',
        name: 'VectorLibrary',
        component: () => import('@/views/vectorlib/VectorLibrary.vue'),
        meta: { title: '文档向量库' }
      },
      {
        path: 'automation',
        name: 'AutomationDashboard',
        component: () => import('@/views/automation/AutomationDashboard.vue'),
        meta: { title: '投标自动化' }
      },
      {
        path: 'automation/launch',
        name: 'OneClickLaunch',
        component: () => import('@/views/automation/OneClickLaunch.vue'),
        meta: { title: '一键启动' }
      },
      {
        path: 'automation-config',
        name: 'AutomationConfig',
        component: () => import('@/views/AutomationConfig.vue'),
        meta: { title: '全自动化配置' }
      },
      {
        path: 'automation-monitor',
        name: 'AutomationMonitor',
        component: () => import('@/views/automation/AutomationMonitor.vue'),
        meta: { title: '自动化监控' }
      },
      {
        path: 'system/users',
        name: 'UserManagement',
        component: () => import('@/views/system/UserManagement.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'system/models',
        name: 'ModelConfig',
        component: () => import('@/views/system/ModelConfig.vue'),
        meta: { title: '模型选择' }
      },
      {
        path: 'system/playground',
        name: 'AIPlayground',
        component: () => import('@/views/system/AIPlayground.vue'),
        meta: { title: 'AI Playground' }
      },
      {
        path: 'system/knowledge',
        name: 'ProjectKnowledge',
        component: () => import('@/views/system/ProjectKnowledge.vue'),
        meta: { title: '项目知识库' }
      },
      {
        path: 'system/multi-view-demo',
        name: 'MultiViewDialogDemo',
        component: () => import('@/views/system/MultiViewDialogDemo.vue'),
        meta: { title: 'MultiViewDialog 演示' }
      },
      {
        path: 'system/templates',
        name: 'WebsiteTemplateList',
        component: () => import('@/views/system/WebsiteTemplateList.vue'),
        meta: { title: '网站模板管理' }
      },
      {
        path: 'system/monitor',
        name: 'ServiceMonitor',
        component: () => import('@/views/system/ServiceMonitor.vue'),
        meta: { title: '服务监控' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 天齐AI大模型投标平台` : '天齐AI大模型投标平台'
  
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)
  
  if (requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

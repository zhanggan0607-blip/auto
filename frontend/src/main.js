import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import {
  Upload,
  Delete,
  View,
  Download,
  Star,
  CircleCheck,
  CircleClose,
  ArrowDown,
  Document,
  Camera,
  Connection,
  Refresh,
  Edit,
  Plus,
  OfficeBuilding,
  Location,
  Select,
  Clock,
  Loading,
  Timer,
  Trophy,
  Warning,
  Check,
  DataBoard,
  Key,
  Collection,
  Folder,
  TrendCharts,
  Monitor,
  VideoPlay,
  Setting,
  Bell,
  User,
  CirclePlus,
  SwitchButton,
  Expand,
  Fold
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import StatusBadge from '@/components/StatusBadge.vue'
import '@/assets/styles/main.scss'

const app = createApp(App)

const isResizeObserverError = (err) => {
  const msg = err?.message || err?.reason?.message || ''
  return msg.includes('ResizeObserver')
}

app.config.errorHandler = (err) => {
  if (isResizeObserverError(err)) return
  console.error('Vue Error:', err)
}

window.addEventListener('error', (event) => {
  if (isResizeObserverError(event)) {
    event.preventDefault()
    return false
  }
})

window.addEventListener('unhandledrejection', (event) => {
  if (isResizeObserverError(event)) {
    event.preventDefault()
    return false
  }
})

const icons = {
  Upload,
  Delete,
  View,
  Download,
  Star,
  CircleCheck,
  CircleClose,
  ArrowDown,
  Document,
  Camera,
  Connection,
  Refresh,
  Edit,
  Plus,
  OfficeBuilding,
  Location,
  Select,
  Clock,
  Loading,
  Timer,
  Trophy,
  Warning,
  Check,
  DataBoard,
  Key,
  Collection,
  Folder,
  TrendCharts,
  Monitor,
  VideoPlay,
  Setting,
  Bell,
  User,
  CirclePlus,
  SwitchButton,
  Expand,
  Fold
}

for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.component('StatusBadge', StatusBadge)

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

app.mount('#app')

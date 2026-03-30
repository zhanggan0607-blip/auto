import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
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
  CirclePlus
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import StatusBadge from '@/components/StatusBadge.vue'
import { registerXssDirectives } from '@/directives/xss'
import '@/assets/styles/main.scss'

const app = createApp(App)

registerXssDirectives(app)

app.config.errorHandler = (err, vm, info) => {
  if (err.message && err.message.includes('ResizeObserver')) {
    return
  }
  console.error('Vue Error:', err, info)
}

window.addEventListener('error', (event) => {
  if (event.message && event.message.includes('ResizeObserver')) {
    event.preventDefault()
    return false
  }
})

window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && event.reason.message && event.reason.message.includes('ResizeObserver')) {
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
  CirclePlus
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

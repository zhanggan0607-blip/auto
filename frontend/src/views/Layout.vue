<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="layout-aside">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <transition name="fade">
          <span v-if="!isCollapse" class="logo-text">投标精灵</span>
        </transition>
      </div>
      <SidebarNav :is-collapse="isCollapse" :unread-count="unreadCount" />
    </el-aside>
    <el-container class="layout-main-container">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            :class="{ 'is-active': isCollapse }"
            @click="toggleCollapse"
          >
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <BreadcrumbNav :items="breadcrumbItems" />
        </div>
        <div class="header-right">
          <el-tooltip content="通知中心" placement="bottom">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99" class="notification-badge">
              <el-icon class="header-icon" @click="goToNotifications">
                <Bell />
              </el-icon>
            </el-badge>
          </el-tooltip>
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-info">
              <el-avatar :size="32" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.userInfo?.username }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile" :icon="User">
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings" :icon="Setting">
                  账户设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout" :icon="SwitchButton">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Bell, User, Setting, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { useModelAutoConnect } from '@/composables/useModelAutoConnect'
import { notificationApi } from '@/api/notification'
import { SidebarNav, BreadcrumbNav } from '@/components'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { autoConnectAfterLogin } = useModelAutoConnect()

const isCollapse = ref(false)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'settings') {
    router.push('/profile')
  } else if (command === 'logout') {
    userStore.logout()
  }
}

const goToNotifications = () => {
  router.push('/notifications')
}

const breadcrumbItems = computed(() => {
  const items = []
  const matched = route.matched.filter(record => record.meta && record.meta.title)

  matched.forEach((record) => {
    items.push({
      title: record.meta.title,
      path: record.path
    })
  })

  return items
})

const unreadCount = ref(0)

const fetchUnreadCount = async () => {
  try {
    const res = await notificationApi.getUnreadCount()
    unreadCount.value = res.data.unread_count
  } catch (error) {
    console.error('获取未读消息数量失败:', error)
  }
}

let unreadInterval = null

onMounted(async () => {
  if (userStore.isLoggedIn) {
    await autoConnectAfterLogin()
  }

  fetchUnreadCount()
  unreadInterval = setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  if (unreadInterval) {
    clearInterval(unreadInterval)
    unreadInterval = null
  }
})

watch(
  () => userStore.isLoggedIn,
  async (isLoggedIn) => {
    if (isLoggedIn) {
      await autoConnectAfterLogin()
    }
  }
)
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
  background-color: var(--color-bg-page);
}

.layout-aside {
  background: var(--sidebar-bg);
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;

  .logo {
    height: var(--header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 0 16px;
    background: var(--brand-gradient);
    overflow: hidden;
    flex-shrink: 0;

    .logo-icon {
      width: 28px;
      height: 28px;
      flex-shrink: 0;
      color: #fff;

      svg {
        width: 100%;
        height: 100%;
      }
    }

    .logo-text {
      font-size: var(--font-size-md);
      font-weight: var(--font-weight-semibold);
      color: #fff;
      white-space: nowrap;
      letter-spacing: 0.5px;
    }
  }
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--color-bg-white);
  box-shadow: var(--shadow-header);
  padding: 0 var(--spacing-lg);
  height: var(--header-height);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  border-bottom: 1px solid var(--color-border-lighter);

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);

    .collapse-btn {
      font-size: 18px;
      cursor: pointer;
      color: var(--color-text-secondary);
      padding: 6px;
      border-radius: var(--radius-md);
      transition: all var(--transition-fast);

      &:hover {
        color: var(--color-primary);
        background-color: var(--color-bg-hover);
      }

      &.is-active {
        color: var(--color-primary);
      }
    }

    :deep(.breadcrumb-nav) {
      font-size: var(--font-size-sm);
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);

    .notification-badge {
      cursor: pointer;

      .header-icon {
        font-size: 18px;
        color: var(--color-text-secondary);
        padding: 6px;
        border-radius: var(--radius-md);
        transition: all var(--transition-fast);

        &:hover {
          color: var(--color-primary);
          background-color: var(--color-bg-hover);
        }
      }
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: var(--spacing-sm);
      cursor: pointer;
      padding: 4px 10px;
      border-radius: var(--radius-md);
      transition: all var(--transition-fast);

      &:hover {
        background-color: var(--color-bg-base);
      }

      .user-avatar {
        background: var(--brand-gradient);
        color: #fff;
      }

      .username {
        font-size: var(--font-size-sm);
        font-weight: var(--font-weight-medium);
        color: var(--color-text-primary);
      }

      .arrow-icon {
        font-size: 12px;
        color: var(--color-text-secondary);
        transition: transform var(--transition-fast);
      }
    }
  }
}

.layout-main-container {
  flex-direction: column;
  background-color: var(--color-bg-page);
  min-height: 0;
}

.layout-main {
  background-color: var(--color-bg-page);
  padding: var(--spacing-lg);
  min-height: calc(100vh - var(--header-height));
  overflow-x: hidden;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">消息通知</h3>
      <el-button type="primary" @click="markAllRead" :disabled="unreadCount === 0">
        全部已读
      </el-button>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane :label="`未读 (${unreadCount})`" name="unread" />
    </el-tabs>

    <div class="notification-list">
      <div
        v-for="item in listPage.list"
        :key="item.id"
        class="notification-item"
        :class="{ unread: !item.is_read }"
        @click="viewNotification(item)"
      >
        <div class="notification-icon">
          <el-icon>
            <component :is="getNotificationIcon(item.notification_type)" />
          </el-icon>
        </div>
        <div class="notification-content">
          <div class="notification-title">{{ item.title }}</div>
          <div class="notification-text">{{ item.content }}</div>
          <div class="notification-time">{{ item.created_at }}</div>
        </div>
        <el-tag v-if="!item.is_read" type="danger" size="small">新</el-tag>
      </div>

      <el-empty v-if="listPage.list.length === 0 && !listPage.loading" description="暂无消息" />
    </div>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="listPage.pagination.page"
        v-model:page-size="listPage.pagination.pageSize"
        :total="listPage.pagination.total"
        layout="prev, pager, next"
        @current-change="listPage.handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Clock, TrendCharts, Bell, Flag } from '@element-plus/icons-vue'
import { notificationApi } from '@/api/notification'
import { useListPage } from '@/composables/useListPage'

const activeTab = ref('all')
const unreadCount = ref(0)

const listPage = useListPage({
  fetchApi: async (params) => {
    const searchParams = {
      page: params.page,
      page_size: params.page_size
    }
    if (activeTab.value === 'unread') {
      searchParams.is_read = false
    }
    return notificationApi.getList(searchParams)
  },
  defaultSearchParams: {
    is_read: ''
  },
  defaultPageSize: 20
})

const getNotificationIcon = (type) => {
  const icons = {
    tender_new: Document,
    tender_deadline: Clock,
    bid_result: TrendCharts,
    system: Bell,
    task: Flag
  }
  return icons[type] || Bell
}

const handleTabChange = () => {
  listPage.pagination.page = 1
  listPage.fetchData()
}

const viewNotification = async (item) => {
  if (!item.is_read) {
    try {
      await notificationApi.markRead(item.id)
      item.is_read = true
      unreadCount.value--
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
}

const markAllRead = async () => {
  try {
    await notificationApi.markAllRead()
    listPage.list.forEach(item => {
      item.is_read = true
    })
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await notificationApi.getUnreadCount()
    unreadCount.value = res.data.unread_count
  } catch (error) {
    console.error('获取未读数量失败:', error)
  }
}

onMounted(() => {
  listPage.fetchData()
  fetchUnreadCount()
})
</script>

<style lang="scss" scoped>
.notification-list {
  .notification-item {
    display: flex;
    align-items: flex-start;
    padding: 15px;
    border-bottom: 1px solid #EBEEF5;
    cursor: pointer;
    transition: background-color 0.3s;

    &:hover {
      background-color: #F5F7FA;
    }

    &.unread {
      background-color: #ECF5FF;
    }

    .notification-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background-color: #409EFF;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 15px;

      .el-icon {
        font-size: 20px;
        color: #fff;
      }
    }

    .notification-content {
      flex: 1;

      .notification-title {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 5px;
      }

      .notification-text {
        font-size: 14px;
        color: #606266;
        margin-bottom: 5px;
        line-height: 1.5;
      }

      .notification-time {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}
</style>

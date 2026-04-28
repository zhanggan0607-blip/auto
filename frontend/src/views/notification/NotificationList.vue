<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">消息通知</h3>
      <div class="header-actions">
        <el-button type="primary" @click="markAllRead" :disabled="unreadCount === 0">
          全部已读
        </el-button>
        <el-button type="danger" plain @click="handleBatchDelete" :disabled="selectedIds.length === 0">
          删除选中 ({{ selectedIds.length }})
        </el-button>
        <el-button type="warning" plain @click="showRangeDeleteDialog = true">
          范围删除
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane :label="`未读 (${unreadCount})`" name="unread" />
    </el-tabs>

    <div v-if="listPage.list.length > 0" class="select-all-bar">
      <el-checkbox
        v-model="isAllSelected"
        :indeterminate="isIndeterminate"
        @change="handleSelectAllChange"
      >
        全选当前页
      </el-checkbox>
      <span class="selected-info" v-if="selectedIds.length > 0">
        已选 {{ selectedIds.length }} 项
      </span>
    </div>

    <div class="notification-list">
      <div
        v-for="(item, index) in listPage.list"
        :key="item?.id || index"
        class="notification-item"
        :class="{ unread: !item?.is_read, selected: isSelected(item?.id) }"
      >
        <div class="notification-checkbox" @click.stop>
          <el-checkbox
            :model-value="isSelected(item?.id)"
            @change="(val) => handleItemSelect(item?.id, val)"
          />
        </div>
        <div class="notification-body" @click="viewNotification(item)">
          <div class="notification-icon">
            <el-icon>
              <component :is="getNotificationIcon(item?.notification_type)" />
            </el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ item?.title }}</div>
            <div class="notification-text">{{ item?.content }}</div>
            <div class="notification-time">{{ item?.created_at }}</div>
          </div>
          <el-tag v-if="!item?.is_read" type="danger" size="small">新</el-tag>
        </div>
        <div class="notification-actions" @click.stop>
          <el-button
            type="danger"
            :icon="Delete"
            circle
            size="small"
            @click="handleDeleteSingle(item)"
          />
        </div>
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

    <el-dialog v-model="showRangeDeleteDialog" title="范围删除" width="480px">
      <el-form label-width="80px">
        <el-form-item label="开始日期">
          <el-date-picker
            v-model="rangeDeleteForm.date_from"
            type="date"
            placeholder="选择开始日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="rangeDeleteForm.date_to"
            type="date"
            placeholder="选择结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="通知类型">
          <el-select v-model="rangeDeleteForm.notification_type" placeholder="全部类型" clearable style="width: 100%">
            <el-option label="新招标公告" value="tender_new" />
            <el-option label="投标截止提醒" value="tender_deadline" />
            <el-option label="中标结果" value="bid_result" />
            <el-option label="系统通知" value="system" />
            <el-option label="任务提醒" value="task" />
            <el-option label="采集完成" value="crawl_completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="快捷操作">
          <el-button type="warning" @click="handleDeleteRead">删除所有已读通知</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRangeDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="handleRangeDelete">确认删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Clock, TrendCharts, Bell, Flag, Download, Delete } from '@element-plus/icons-vue'
import { notificationApi } from '@/api/notification'
import { useListPage } from '@/composables/useListPage'

const activeTab = ref('all')
const unreadCount = ref(0)
const selectedIds = ref([])
const showRangeDeleteDialog = ref(false)
const rangeDeleteForm = reactive({
  date_from: '',
  date_to: '',
  notification_type: ''
})

const listPage = useListPage({
  fetchApi: async (params) => {
    const searchParams = {
      page: params.page,
      page_size: params.page_size
    }
    if (activeTab.value === 'unread') {
      searchParams.is_read = 'false'
    }
    return notificationApi.getList(searchParams)
  },
  defaultSearchParams: {
    is_read: ''
  },
  defaultPageSize: 20
})

const isAllSelected = computed(() => {
  return listPage.list.length > 0 && listPage.list.every(item => item?.id && selectedIds.value.includes(item.id))
})

const isIndeterminate = computed(() => {
  const count = listPage.list.filter(item => item?.id && selectedIds.value.includes(item.id)).length
  return count > 0 && count < listPage.list.length
})

const isSelected = (id) => {
  return id ? selectedIds.value.includes(id) : false
}

const handleItemSelect = (id, val) => {
  if (!id) return
  if (val) {
    if (!selectedIds.value.includes(id)) {
      selectedIds.value.push(id)
    }
  } else {
    selectedIds.value = selectedIds.value.filter(i => i !== id)
  }
}

const handleSelectAllChange = (val) => {
  if (val) {
    const currentPageIds = listPage.list
      .filter(item => item?.id)
      .map(item => item.id)
    const existingSet = new Set(selectedIds.value)
    currentPageIds.forEach(id => existingSet.add(id))
    selectedIds.value = Array.from(existingSet)
  } else {
    const currentPageIds = new Set(
      listPage.list.filter(item => item?.id).map(item => item.id)
    )
    selectedIds.value = selectedIds.value.filter(id => !currentPageIds.has(id))
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    tender_new: Document,
    tender_deadline: Clock,
    bid_result: TrendCharts,
    system: Bell,
    task: Flag,
    crawl_completed: Download
  }
  return icons[type] || Bell
}

const handleTabChange = () => {
  listPage.pagination.page = 1
  selectedIds.value = []
  listPage.fetchData()
}

const viewNotification = async (item) => {
  if (!item || typeof item !== 'object' || item.__v_isRef) {
    console.warn('viewNotification: 无效的通知对象', item)
    return
  }
  if (!item.is_read) {
    if (!item.id) {
      console.warn('通知ID缺失，无法标记已读', JSON.stringify(item))
      return
    }
    try {
      await notificationApi.markRead(item.id)
      item.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
}

const markAllRead = async () => {
  try {
    await notificationApi.markAllRead()
    listPage.list.forEach(item => {
      if (item && typeof item === 'object' && !item.__v_isRef) {
        item.is_read = true
      }
    })
    unreadCount.value = 0
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDeleteSingle = async (item) => {
  if (!item?.id) return
  try {
    await ElMessageBox.confirm(
      `确定要删除通知"${item.title || ''}"吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await notificationApi.deleteNotification(item.id)
    selectedIds.value = selectedIds.value.filter(id => id !== item.id)
    ElMessage.success('通知已删除')
    await listPage.fetchData()
    fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 条通知吗？`,
      '确认批量删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await notificationApi.batchDelete({ ids: selectedIds.value })
    const deletedCount = res.data?.deleted_count || selectedIds.value.length
    selectedIds.value = []
    ElMessage.success(`成功删除 ${deletedCount} 条通知`)
    await listPage.fetchData()
    fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '批量删除失败')
    }
  }
}

const handleRangeDelete = async () => {
  const { date_from, date_to, notification_type } = rangeDeleteForm
  if (!date_from && !date_to && !notification_type) {
    ElMessage.warning('请至少选择一个删除条件')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确定要删除符合条件的通知吗？此操作不可恢复。',
      '确认范围删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const data = {}
    if (date_from) data.date_from = date_from
    if (date_to) data.date_to = date_to
    if (notification_type) data.notification_type = notification_type
    const res = await notificationApi.batchDelete(data)
    const deletedCount = res.data?.deleted_count || 0
    ElMessage.success(`成功删除 ${deletedCount} 条通知`)
    showRangeDeleteDialog.value = false
    rangeDeleteForm.date_from = ''
    rangeDeleteForm.date_to = ''
    rangeDeleteForm.notification_type = ''
    selectedIds.value = []
    await listPage.fetchData()
    fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '范围删除失败')
    }
  }
}

const handleDeleteRead = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除所有已读通知吗？此操作不可恢复。',
      '确认删除已读通知',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await notificationApi.batchDelete({ delete_read: true })
    const deletedCount = res.data?.deleted_count || 0
    if (deletedCount > 0) {
      ElMessage.success(`成功删除 ${deletedCount} 条已读通知`)
    } else {
      ElMessage.info('没有已读通知可删除')
    }
    showRangeDeleteDialog.value = false
    selectedIds.value = []
    await listPage.fetchData()
    fetchUnreadCount()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const fetchUnreadCount = async () => {
  try {
    const res = await notificationApi.getUnreadCount()
    unreadCount.value = res.data?.unread_count ?? 0
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
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;

  .header-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}

.select-all-bar {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  background-color: #F8FAFC;
  border-bottom: 1px solid #E2E8F0;

  .selected-info {
    margin-left: 12px;
    font-size: 13px;
    color: #64748B;
  }
}

.notification-list {
  .notification-item {
    display: flex;
    align-items: flex-start;
    padding: 12px 15px;
    border-bottom: 1px solid #E2E8F0;
    transition: background-color 0.3s;

    &.unread {
      background-color: #EFF6FF;
    }

    &.selected {
      background-color: #F0FDF4;
    }

    &:hover {
      background-color: #F1F5F9;

      .notification-actions {
        opacity: 1;
      }
    }

    .notification-checkbox {
      display: flex;
      align-items: center;
      padding-top: 10px;
      margin-right: 8px;
    }

    .notification-body {
      display: flex;
      align-items: flex-start;
      flex: 1;
      cursor: pointer;

      .notification-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #3B82F6;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        flex-shrink: 0;

        .el-icon {
          font-size: 20px;
          color: #fff;
        }
      }

      .notification-content {
        flex: 1;
        min-width: 0;

        .notification-title {
          font-size: 16px;
          font-weight: 500;
          color: #1E293B;
          margin-bottom: 5px;
        }

        .notification-text {
          font-size: 14px;
          color: #334155;
          margin-bottom: 5px;
          line-height: 1.5;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .notification-time {
          font-size: 12px;
          color: #64748B;
        }
      }
    }

    .notification-actions {
      display: flex;
      align-items: center;
      padding-top: 8px;
      margin-left: 8px;
      opacity: 0;
      transition: opacity 0.3s;
    }
  }
}
</style>

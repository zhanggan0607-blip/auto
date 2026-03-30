<template>
  <div class="alert-list">
    <div class="alert-header">
      <h3>告警列表</h3>
      <el-button
        v-if="alerts.length > 0"
        type="success"
        size="small"
        @click="handleResolveAll"
      >
        批量解决
      </el-button>
    </div>

    <el-table :data="alerts" stripe style="width: 100%">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="service_name" label="服务" width="150" />
      <el-table-column prop="level" label="级别" width="100">
        <template #default="{ row }">
          <el-tag :type="getLevelType(row.level)" size="small">
            {{ row.level_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)" size="small">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status !== 'resolved'"
            type="primary"
            size="small"
            link
            @click="handleResolve(row)"
          >
            解决
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            type="warning"
            size="small"
            link
            @click="handleNotify(row)"
          >
            发送通知
          </el-button>
          <el-button
            size="small"
            link
            @click="openAlertDetail(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!alerts.length" class="empty-state">
      <el-empty description="暂无告警" />
    </div>

    <el-drawer v-model="showDetail" title="告警详情" size="500px">
      <div v-if="currentAlert" class="alert-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="服务">
            {{ currentAlert.service_name }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelType(currentAlert.level)">
              {{ currentAlert.level_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(currentAlert.status)">
              {{ currentAlert.status_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="标题">
            {{ currentAlert.title }}
          </el-descriptions-item>
          <el-descriptions-item label="消息">
            {{ currentAlert.message }}
          </el-descriptions-item>
          <el-descriptions-item label="连续失败次数">
            {{ currentAlert.consecutive_failures }}
          </el-descriptions-item>
          <el-descriptions-item label="触发原因">
            {{ currentAlert.triggered_by }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(currentAlert.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.notified_at" label="通知时间">
            {{ formatTime(currentAlert.notified_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="currentAlert.resolved_at" label="解决时间">
            {{ formatTime(currentAlert.resolved_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">已执行操作</el-divider>
        <el-timeline v-if="currentAlert.actions_taken?.length">
          <el-timeline-item
            v-for="(action, index) in currentAlert.actions_taken"
            :key="index"
            :timestamp="action.time"
            placement="top"
          >
            {{ action.description }}
          </el-timeline-item>
        </el-timeline>
        <div v-else class="no-actions">暂无操作记录</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlerts, resolveAlert, resolveAllAlerts, sendAlertNotification } from '@/api/monitor'

const alerts = ref([])
const showDetail = ref(false)
const currentAlert = ref(null)

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

const getLevelType = (level) => {
  const typeMap = {
    'info': 'info',
    'warning': 'warning',
    'error': 'danger',
    'critical': 'danger'
  }
  return typeMap[level] || 'info'
}

const getStatusTagType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'notified': 'info',
    'resolved': 'success',
    'ignored': 'info'
  }
  return typeMap[status] || 'info'
}

const fetchAlerts = async () => {
  try {
    const res = await getAlerts({ days: 7 })
    alerts.value = res.results || res || []
  } catch (error) {
    console.error('获取告警列表失败:', error)
  }
}

const handleResolve = async (alert) => {
  try {
    await ElMessageBox.confirm('确定要解决此告警吗？', '解决告警', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await resolveAlert(alert.id)
    ElMessage.success('告警已解决')
    fetchAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleResolveAll = async () => {
  try {
    const selectedAlerts = alerts.value.filter(a => a.status !== 'resolved')
    if (!selectedAlerts.length) {
      ElMessage.info('没有可解决的告警')
      return
    }
    await ElMessageBox.confirm(
      `确定要解决 ${selectedAlerts.length} 个告警吗？`,
      '批量解决',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await resolveAllAlerts(selectedAlerts.map(a => a.id))
    ElMessage.success('已批量解决告警')
    fetchAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleNotify = async (alert) => {
  try {
    await sendAlertNotification(alert.id)
    ElMessage.success('通知已发送')
    fetchAlerts()
  } catch (error) {
    ElMessage.error('发送通知失败')
  }
}

const openAlertDetail = (alert) => {
  currentAlert.value = alert
  showDetail.value = true
}

onMounted(() => {
  fetchAlerts()
})
</script>

<style scoped lang="scss">
.alert-list {
  .alert-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    h3 {
      margin: 0;
    }
  }

  .empty-state {
    padding: 40px 0;
  }
}

.alert-detail {
  .no-actions {
    color: #909399;
    text-align: center;
    padding: 20px;
  }
}
</style>
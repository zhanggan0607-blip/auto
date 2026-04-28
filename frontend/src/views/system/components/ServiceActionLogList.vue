<template>
  <div class="service-action-log">
    <el-table :data="logs" stripe style="width: 100%" max-height="300">
      <el-table-column prop="action_type_display" label="操作类型" width="120" />
      <el-table-column prop="status_display" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="getStatusType('action_log_status', 'action_log_status', row.status)" size="small">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="started_at" label="开始时间" width="160">
        <template #default="{ row }">
          {{ formatDateTime(row.started_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="duration_ms" label="耗时" width="80">
        <template #default="{ row }">
          {{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="result_message" label="结果" min-width="200" show-overflow-tooltip />
      <el-table-column prop="performed_by" label="执行者" width="100" />
    </el-table>
    <div v-if="!logs.length" class="empty-state">
      暂无操作日志
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { getActionLogs } from '@/api/monitor'
import { formatDateTime } from '@/utils/date'
import { getStatusType } from '@/store/constants'

const props = defineProps({
  serviceId: {
    type: Number,
    required: true
  }
})

const logs = ref([])

const fetchActionLogs = async () => {
  if (!props.serviceId) return

  try {
    const res = await getActionLogs({
      service_id: props.serviceId,
      hours: 24
    })
    const data = res?.data || res
    logs.value = Array.isArray(data) ? data :
                  Array.isArray(data?.results) ? data.results :
                  Array.isArray(data?.list) ? data.list : []
  } catch (error) {
    console.error('获取操作日志失败:', error)
    logs.value = []
  }
}

watch(() => props.serviceId, () => {
  fetchActionLogs()
})

onMounted(() => {
  fetchActionLogs()
})
</script>

<style scoped lang="scss">
.service-action-log {
  .empty-state {
    text-align: center;
    padding: 20px;
    color: #64748B;
  }
}
</style>
﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="service-health-chart">
    <div v-if="loading" class="chart-loading">
      <el-icon class="rotating"><Loading /></el-icon>
      加载中...
    </div>
    <div v-else-if="!chartData.length" class="chart-empty">
      暂无健康数据
    </div>
    <div v-else class="chart-container">
      <div class="chart-legend">
        <span class="legend-item healthy">健康</span>
        <span class="legend-item unhealthy">异常</span>
      </div>
      <div class="chart-bars">
        <div
          v-for="(item, index) in chartData"
          :key="index"
          class="chart-bar-wrapper"
        >
          <div
            class="chart-bar"
            :class="item.is_healthy ? 'healthy' : 'unhealthy'"
            :style="{ height: `${getBarHeight(item)}%` }"
            :title="`${formatDateTime(item.timestamp)}: ${item.is_healthy ? '健康' : '异常'}`"
          ></div>
          <div class="chart-time">{{ formatHour(item.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { getHealthRecords } from '@/api/monitor'
import { parseListResponse } from '@/utils/response-parser'
import { formatDateTime } from '@/utils/date'

const props = defineProps({
  serviceId: {
    type: Number,
    required: true
  }
})

const loading = ref(false)
const chartData = ref([])

const formatHour = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getHours()}:00`
}

const getBarHeight = (item) => {
  return item.is_healthy ? 100 : 60
}

const fetchHealthRecords = async () => {
  if (!props.serviceId) return

  try {
    loading.value = true
    const res = await getHealthRecords({
      service_id: props.serviceId,
      hours: 24
    })

    const { list } = parseListResponse(res)
    chartData.value = list
  } catch (error) {
    console.error('获取健康记录失败:', error)
  } finally {
    loading.value = false
  }
}

watch(() => props.serviceId, () => {
  fetchHealthRecords()
})

onMounted(() => {
  fetchHealthRecords()
})
</script>

<style scoped lang="scss">
.service-health-chart {
  height: 200px;
}

.chart-loading,
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #64748B;
  gap: 8px;
}

.chart-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  justify-content: flex-end;
}

.legend-item {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;

  &::before {
    content: '';
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }

  &.healthy::before {
    background: #16A34A;
  }

  &.unhealthy::before {
    background: #DC2626;
  }
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  padding: 8px 0;
  border-bottom: 1px solid #E2E8F0;
}

.chart-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.chart-bar {
  width: 100%;
  max-width: 20px;
  border-radius: 2px 2px 0 0;
  transition: height 0.3s;
  cursor: pointer;

  &.healthy {
    background: #16A34A;
  }

  &.unhealthy {
    background: #DC2626;
  }
}

.chart-time {
  font-size: 10px;
  color: #64748B;
  margin-top: 4px;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
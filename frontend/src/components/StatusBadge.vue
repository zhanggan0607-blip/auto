<template>
  <el-tag :type="tagType" :size="size" :effect="effect" :class="['status-badge', customClass]">
    <el-icon v-if="showIcon && iconComponent" class="status-icon">
      <component :is="iconComponent" />
    </el-icon>
    <span>{{ displayText }}</span>
  </el-tag>
</template>

<script setup>
/**
 * StatusBadge 状态徽章组件
 * 统一显示各种状态的徽章，支持多种状态类型
 */
import { computed } from 'vue'
import {
  getTenderStatusType,
  getTenderStatusText,
  getBidStatusType,
  getBidStatusText,
  getResultType,
  getResultText,
  getCrawlerStatusType,
  getCrawlerStatusText,
  getEnterpriseDocStatusType,
  getEnterpriseDocStatusText,
  TENDER_STATUS,
  BID_STATUS,
  RESULT_TYPE,
  CRAWLER_STATUS,
  ENTERPRISE_DOC_STATUS
} from '@/store/constants'
import {
  Clock,
  Loading,
  Document,
  CircleCheck,
  CircleClose,
  Warning,
  Trophy,
  Timer,
  Check
} from '@element-plus/icons-vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'tender',
    validator: (value) => ['tender', 'bid', 'result', 'crawler', 'enterpriseDoc', 'schedule', 'document'].includes(value)
  },
  size: {
    type: String,
    default: 'small',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  },
  effect: {
    type: String,
    default: 'light',
    validator: (value) => ['dark', 'light', 'plain'].includes(value)
  },
  showIcon: {
    type: Boolean,
    default: false
  },
  customText: {
    type: String,
    default: ''
  },
  customClass: {
    type: String,
    default: ''
  }
})

const tagType = computed(() => {
  const typeGetters = {
    tender: getTenderStatusType,
    bid: getBidStatusType,
    result: getResultType,
    crawler: getCrawlerStatusType,
    enterpriseDoc: getEnterpriseDocStatusType,
    schedule: (status) => {
      const typeMap = {
        'active': 'success',
        'paused': 'warning',
        'deleted': 'info'
      }
      return typeMap[status] || 'info'
    },
    document: (status) => {
      const typeMap = {
        'draft': 'info',
        'generated': 'primary',
        'reviewed': 'warning',
        'submitted': 'success'
      }
      return typeMap[status] || 'info'
    }
  }

  const getter = typeGetters[props.type]
  return getter ? getter(props.status) : 'info'
})

const displayText = computed(() => {
  if (props.customText) return props.customText

  const textGetters = {
    tender: getTenderStatusText,
    bid: getBidStatusText,
    result: getResultText,
    crawler: getCrawlerStatusText,
    enterpriseDoc: getEnterpriseDocStatusText,
    schedule: (status) => {
      const textMap = {
        'active': '启用',
        'paused': '暂停',
        'deleted': '已删除'
      }
      return textMap[status] || status
    },
    document: (status) => {
      const textMap = {
        'draft': '草稿',
        'generated': '已生成',
        'reviewed': '已审核',
        'submitted': '已提交'
      }
      return textMap[status] || status
    }
  }

  const getter = textGetters[props.type]
  return getter ? getter(props.status) : props.status
})

const iconComponent = computed(() => {
  if (!props.showIcon) return null

  const iconMaps = {
    tender: {
      [TENDER_STATUS.PENDING]: Clock,
      [TENDER_STATUS.PROCESSING]: Loading,
      [TENDER_STATUS.SUBMITTED]: Document,
      [TENDER_STATUS.WON]: Trophy,
      [TENDER_STATUS.LOST]: CircleClose,
      [TENDER_STATUS.EXPIRED]: Timer
    },
    bid: {
      [BID_STATUS.PREPARING]: Clock,
      [BID_STATUS.SUBMITTED]: Document,
      [BID_STATUS.REVIEWING]: Loading,
      [BID_STATUS.WON]: Trophy,
      [BID_STATUS.LOST]: CircleClose,
      [BID_STATUS.WITHDRAWN]: CircleClose
    },
    result: {
      [RESULT_TYPE.WIN]: Trophy,
      [RESULT_TYPE.LOSE]: CircleClose,
      [RESULT_TYPE.PENDING]: Warning
    },
    crawler: {
      [CRAWLER_STATUS.PENDING]: Clock,
      [CRAWLER_STATUS.RUNNING]: Loading,
      [CRAWLER_STATUS.COMPLETED]: CircleCheck,
      [CRAWLER_STATUS.FAILED]: CircleClose
    },
    enterpriseDoc: {
      [ENTERPRISE_DOC_STATUS.VALID]: Check,
      [ENTERPRISE_DOC_STATUS.EXPIRING]: Warning,
      [ENTERPRISE_DOC_STATUS.EXPIRED]: CircleClose,
      [ENTERPRISE_DOC_STATUS.PENDING]: Clock
    },
    schedule: {
      'active': Check,
      'paused': Timer,
      'deleted': CircleClose
    },
    document: {
      'draft': Document,
      'generated': Document,
      'reviewed': Check,
      'submitted': CircleCheck
    }
  }

  const iconMap = iconMaps[props.type]
  return iconMap ? iconMap[props.status] : null
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-icon {
  font-size: 12px;
}
</style>

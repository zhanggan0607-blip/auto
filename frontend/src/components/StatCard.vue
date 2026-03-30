<template>
  <el-card
    class="stat-card"
    :class="[`stat-card-${type}`, { 'stat-card-clickable': clickable }]"
    shadow="hover"
    @click="handleClick"
  >
    <div class="stat-content">
      <div class="stat-icon" :style="{ background: iconGradient }">
        <slot name="icon">
          <el-icon><component :is="icon" v-if="icon" /></el-icon>
        </slot>
      </div>
      <div class="stat-info">
        <div class="stat-value" :style="{ color: valueColor }">
          <span class="stat-prefix" v-if="prefix">{{ prefix }}</span>
          <span class="stat-number">{{ displayValue }}</span>
          <span class="stat-suffix" v-if="suffix">{{ suffix }}</span>
        </div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
    <div class="stat-trend" v-if="trend !== undefined">
      <el-icon :class="trend >= 0 ? 'trend-up' : 'trend-down'">
        <component :is="trend >= 0 ? 'Top' : 'Bottom'" />
      </el-icon>
      <span :class="trend >= 0 ? 'trend-up' : 'trend-down'">
        {{ Math.abs(trend) }}%
      </span>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [Number, String],
    default: 0
  },
  label: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'danger', 'info'].includes(v)
  },
  icon: {
    type: String,
    default: ''
  },
  suffix: {
    type: String,
    default: ''
  },
  prefix: {
    type: String,
    default: ''
  },
  decimals: {
    type: Number,
    default: 0
  },
  trend: {
    type: Number,
    default: undefined
  },
  clickable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const displayValue = computed(() => {
  let val = props.value
  if (typeof val === 'number' && props.decimals > 0) {
    val = val.toFixed(props.decimals)
  }
  return val
})

const iconGradient = computed(() => {
  const gradients = {
    default: 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%)',
    success: 'linear-gradient(135deg, var(--color-success) 0%, var(--color-success-light) 100%)',
    warning: 'linear-gradient(135deg, var(--color-warning) 0%, var(--color-warning-light) 100%)',
    danger: 'linear-gradient(135deg, var(--color-danger) 0%, var(--color-danger-light) 100%)',
    info: 'linear-gradient(135deg, var(--color-info) 0%, var(--color-info-light) 100%)'
  }
  return gradients[props.type] || gradients.default
})

const valueColor = computed(() => {
  const colors = {
    default: 'var(--color-primary)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
    danger: 'var(--color-danger)',
    info: 'var(--color-info)'
  }
  return colors[props.type] || colors.default
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped lang="scss">
.stat-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  background: var(--color-bg-white);
  box-shadow: var(--shadow-card);

  &.stat-card-clickable {
    cursor: pointer;
  }

  &::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 80px;
    height: 80px;
    background: radial-gradient(circle at top right, rgba(0, 102, 204, 0.04), transparent);
    border-radius: 50%;
    transform: translate(30%, -30%);
    pointer-events: none;
  }

  &:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
    border-color: var(--color-border);

    .stat-icon {
      transform: scale(1.05);
    }
  }

  :deep(.el-card__body) {
    padding: var(--spacing-lg);
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.25s ease;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.2);

  .el-icon {
    font-size: 24px;
    color: #fff;
  }
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  line-height: 1.1;
  display: flex;
  align-items: baseline;
  gap: 2px;

  .stat-prefix {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin-right: 2px;
  }

  .stat-suffix {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    margin-left: 2px;
  }
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
  font-weight: var(--font-weight-normal);
}

.stat-trend {
  position: absolute;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);

  .trend-up {
    color: var(--color-success);
  }

  .trend-down {
    color: var(--color-danger);
  }

  .el-icon {
    font-size: 12px;
  }
}
</style>

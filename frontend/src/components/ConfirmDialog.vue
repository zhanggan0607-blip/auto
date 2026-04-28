<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <div class="confirm-content">
      <div class="confirm-icon" :class="`confirm-icon-${type}`">
        <el-icon :size="32"><component :is="iconName" /></el-icon>
      </div>
      <div class="confirm-message">{{ message }}</div>
      <div v-if="description" class="confirm-description">{{ description }}</div>
    </div>
    <template #footer>
      <el-button @click="handleCancel">{{ cancelText }}</el-button>
      <el-button :type="confirmButtonType" :loading="loading" @click="handleConfirm">
        {{ confirmText }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'warning',
    validator: (v) => ['warning', 'success', 'danger', 'info'].includes(v)
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  width: {
    type: String,
    default: '460px'
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const iconName = computed(() => {
  const icons = {
    warning: 'WarningFilled',
    success: 'CircleCheckFilled',
    danger: 'CircleCloseFilled',
    info: 'InfoFilled'
  }
  return icons[props.type] || icons.warning
})

const confirmButtonType = computed(() => {
  const types = {
    warning: 'warning',
    success: 'success',
    danger: 'danger',
    info: 'primary'
  }
  return types[props.type] || 'primary'
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  visible.value = false
  emit('cancel')
}

const handleClosed = () => {
  emit('cancel')
}
</script>

<style scoped lang="scss">
.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  text-align: center;
}

.confirm-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;

  &.confirm-icon-warning {
    background-color: #fdf6ec;
    color: #EA580C;
  }

  &.confirm-icon-success {
    background-color: #F0FDF4;
    color: #16A34A;
  }

  &.confirm-icon-danger {
    background-color: #fef0f0;
    color: #DC2626;
  }

  &.confirm-icon-info {
    background-color: #f4f4f5;
    color: #64748B;
  }
}

.confirm-message {
  font-size: 16px;
  font-weight: 500;
  color: #1E293B;
  margin-bottom: 8px;
}

.confirm-description {
  font-size: 14px;
  color: #64748B;
  line-height: 1.5;
}
</style>

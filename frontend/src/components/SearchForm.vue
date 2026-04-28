<template>
  <div class="search-form">
    <el-form :model="formData" :inline="true" @submit.prevent="handleSearch" class="search-form-inner">
      <slot :form-data="formData" :handle-change="handleChange" />
      <el-form-item class="search-actions">
        <el-button type="primary" @click="handleSearch" class="search-btn">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset" class="reset-btn">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  defaultValues: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

const formData = reactive({ ...props.defaultValues, ...props.modelValue })

watch(
  () => props.modelValue,
  (val) => {
    Object.assign(formData, val)
  },
  { deep: true }
)

watch(
  formData,
  (val) => {
    emit('update:modelValue', { ...val })
  },
  { deep: true }
)

const handleSearch = () => {
  emit('search', { ...formData })
}

const handleReset = () => {
  Object.keys(props.defaultValues).forEach((key) => {
    formData[key] = props.defaultValues[key]
  })
  emit('reset')
}

const handleChange = (field, value) => {
  formData[field] = value
}
</script>

<style scoped lang="scss">
.search-form {
  :deep(.el-form-item) {
    margin-bottom: 0;
  }
}

.search-form-inner {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.search-actions {
  :deep(.el-form-item__content) {
    display: flex;
    gap: var(--spacing-sm);
  }
}

.search-btn {
  background: var(--brand-gradient);
  border: none;
  box-shadow: 0 2px 8px rgba(26, 86, 219, 0.2);
  transition: all var(--transition-base);

  &:hover {
    background: var(--brand-gradient-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(26, 86, 219, 0.3);
  }
}

.reset-btn {
  transition: all var(--transition-base);

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}
</style>

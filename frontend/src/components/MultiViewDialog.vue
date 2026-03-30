<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    :width="width"
    :close-on-click-modal="closeOnClickModal"
    :destroy-on-close="destroyOnClose"
    class="multi-view-dialog"
    @closed="onDialogClosed"
  >
    <div class="view-tabs" v-if="tabsPosition === 'top'">
      <div class="tabs-container">
        <button
          v-for="(view, index) in views"
          :key="view.name"
          :class="['view-tab', { active: currentView === view.name }]"
          @click="switchView(view.name)"
        >
          <el-icon v-if="view.icon"><component :is="view.icon" /></el-icon>
          <span>{{ view.label }}</span>
        </button>
      </div>
    </div>

    <div class="dialog-body" :class="{ 'has-tabs': showTabs }">
      <transition :name="transitionName" mode="out-in">
        <div
          v-if="currentViewData"
          :key="currentViewData.name"
          :class="['view-content', `view-${currentViewData.name}`]"
        >
          <slot :name="currentViewData.name" :view-data="getViewData(currentViewData.name)" />
        </div>
      </transition>
    </div>

    <template #footer v-if="showFooter">
      <div class="dialog-footer">
        <slot name="footer">
          <el-button @click="handleCancel">{{ cancelText }}</el-button>
          <el-button type="primary" @click="handleConfirm" :loading="confirmLoading">
            {{ confirmText }}
          </el-button>
        </slot>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '800px'
  },
  views: {
    type: Array,
    required: true,
    validator: (value) => {
      return value.every(view =>
        view.hasOwnProperty('name') &&
        view.hasOwnProperty('label')
      )
    }
  },
  defaultView: {
    type: String,
    default: ''
  },
  transition: {
    type: String,
    default: 'fade',
    validator: (value) => ['fade', 'slide', 'zoom'].includes(value)
  },
  tabsPosition: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'left'].includes(value)
  },
  showFooter: {
    type: Boolean,
    default: true
  },
  confirmText: {
    type: String,
    default: '确定'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  destroyOnClose: {
    type: Boolean,
    default: true
  },
  viewData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits([
  'update:modelValue',
  'view-change',
  'confirm',
  'cancel'
])

const dialogVisible = ref(props.modelValue)
const currentView = ref(props.defaultView || (props.views[0]?.name || ''))
const confirmLoading = ref(false)
const transitionName = ref(props.transition)

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val
})

watch(dialogVisible, (val) => {
  emit('update:modelValue', val)
})

watch(() => props.defaultView, (val) => {
  if (val && val !== currentView.value) {
    currentView.value = val
  }
})

const showTabs = computed(() => props.views.length > 1)

const currentViewData = computed(() => {
  return props.views.find(v => v.name === currentView.value) || null
})

const switchView = (viewName) => {
  if (viewName === currentView.value) return
  transitionName.value = 'slide'
  currentView.value = viewName
  emit('view-change', viewName)
}

const getViewData = (viewName) => {
  return props.viewData[viewName] || null
}

const handleConfirm = async () => {
  confirmLoading.value = true
  try {
    emit('confirm', currentView.value)
  } finally {
    confirmLoading.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
  dialogVisible.value = false
}

const onDialogClosed = () => {
  emit('closed')
}

const open = (viewName) => {
  if (viewName) {
    currentView.value = viewName
  }
  dialogVisible.value = true
}

const close = () => {
  dialogVisible.value = false
}

const setView = (viewName) => {
  switchView(viewName)
}

defineExpose({
  open,
  close,
  setView,
  currentView,
  currentViewData
})
</script>

<style scoped lang="scss">
.multi-view-dialog {
  :deep(.el-dialog__header) {
    margin-right: 0;
    padding-bottom: 0;
  }

  :deep(.el-dialog__body) {
    padding: 0;
  }
}

.view-tabs {
  padding: var(--spacing-md) var(--spacing-lg) 0;
  border-bottom: 1px solid var(--color-border-lighter);
  background: var(--color-bg-base);

  .tabs-container {
    display: flex;
    gap: var(--spacing-xs);
    overflow-x: auto;

    &::-webkit-scrollbar {
      height: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: var(--color-border);
      border-radius: 2px;
    }
  }
}

.view-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
  transition: all var(--transition-fast);
  margin-bottom: -1px;

  &:hover {
    color: var(--color-text-primary);
    background: var(--color-bg-hover);
  }

  &.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
    font-weight: var(--font-weight-medium);

    .el-icon {
      color: var(--color-primary);
    }
  }

  .el-icon {
    font-size: var(--font-size-base);
    transition: color var(--transition-fast);
  }
}

.dialog-body {
  min-height: 200px;
  max-height: 60vh;
  overflow-y: auto;

  &.has-tabs {
    padding: var(--spacing-lg);
  }

  &:not(.has-tabs) {
    padding: var(--spacing-lg);
  }
}

.view-content {
  width: 100%;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.slide-enter-from {
  transform: translateX(20px);
  opacity: 0;
}

.slide-leave-to {
  transform: translateX(-20px);
  opacity: 0;
}

.zoom-enter-active,
.zoom-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.zoom-enter-from {
  transform: scale(0.95);
  opacity: 0;
}

.zoom-leave-to {
  transform: scale(1.02);
  opacity: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-lighter);
  background: var(--color-bg-base);
}
</style>
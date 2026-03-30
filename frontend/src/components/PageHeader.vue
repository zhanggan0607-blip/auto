<template>
  <div class="page-header" :class="{ 'page-header-compact': compact }">
    <div class="page-header-left">
      <h3 class="page-title">{{ title }}</h3>
      <span v-if="subtitle" class="page-subtitle">{{ subtitle }}</span>
    </div>
    <div class="page-header-right">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
  border: 1px solid var(--color-border-lighter);
  box-shadow: var(--shadow-xs);
  transition: all var(--transition-base);

  &.page-header-compact {
    padding: var(--spacing-base) var(--spacing-lg);
    border-radius: var(--radius-md);

    .page-title {
      font-size: var(--font-size-md);
    }

    .page-subtitle {
      font-size: var(--font-size-xs);
    }
  }
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.page-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  letter-spacing: 0.3px;
}

.page-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  padding-left: var(--spacing-md);
  border-left: 1px solid var(--color-border);
}

.page-header-right {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;

  :deep(.el-button) {
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
  }
}
</style>

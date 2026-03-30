<template>
  <div class="pagination-wrapper" v-if="total > 0">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="pageSizes"
      :total="total"
      :layout="layout"
      :background="background"
      :small="small"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
    <span v-if="showTotal" class="total-text">
      共 {{ total }} 条
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: {
    type: Number,
    default: 1
  },
  limit: {
    type: Number,
    default: 10
  },
  total: {
    type: Number,
    required: true
  },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  layout: {
    type: String,
    default: 'total, sizes, prev, pager, next, jumper'
  },
  background: {
    type: Boolean,
    default: true
  },
  small: {
    type: Boolean,
    default: false
  },
  showTotal: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:page', 'update:limit', 'pagination'])

const currentPage = computed({
  get: () => props.page,
  set: (val) => emit('update:page', val)
})

const pageSize = computed({
  get: () => props.limit,
  set: (val) => emit('update:limit', val)
})

function handleSizeChange(val) {
  emit('pagination', { page: currentPage.value, limit: val })
}

function handleCurrentChange(val) {
  emit('pagination', { page: val, limit: pageSize.value })
}
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 16px 0;
  gap: 12px;
}

.total-text {
  color: #606266;
  font-size: 13px;
}

@media screen and (max-width: 768px) {
  .pagination-wrapper {
    flex-direction: column;
    align-items: flex-end;
  }
  
  .pagination-wrapper :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
}
</style>

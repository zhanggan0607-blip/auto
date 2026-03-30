<template>
  <div class="crud-table">
    <div class="crud-table-header">
      <slot name="header-actions">
        <el-button
          v-if="addButtonText"
          type="primary"
          size="small"
          @click="handleAdd"
          class="add-btn"
        >
          <el-icon v-if="showAddIcon"><Plus /></el-icon>
          {{ addButtonText }}
        </el-button>
      </slot>
    </div>

    <el-table
      :data="data"
      size="small"
      stripe
      v-loading="loading"
      @selection-change="handleSelectionChange"
      class="data-table"
    >
      <el-table-column v-if="showSelection" type="selection" width="55" />

      <slot />

      <el-table-column
        v-if="showOperations"
        :label="operationsLabel"
        :width="operationsWidth"
        fixed="right"
      >
        <template #default="{ row }">
          <slot name="operations" :row="row">
            <el-button
              v-if="showEdit"
              type="primary"
              link
              size="small"
              @click.stop="handleEdit(row)"
            >
              {{ editButtonText }}
            </el-button>
            <el-button
              v-if="showDelete"
              type="danger"
              link
              size="small"
              @click.stop="handleDelete(row)"
            >
              {{ deleteButtonText }}
            </el-button>
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <el-empty
      v-if="data.length === 0 && !loading"
      :description="emptyDescription"
    />

    <div v-if="showPagination && total > 0" class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="currentPageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        :background="true"
        small
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  addButtonText: {
    type: String,
    default: ''
  },
  showAddIcon: {
    type: Boolean,
    default: true
  },
  showOperations: {
    type: Boolean,
    default: true
  },
  operationsLabel: {
    type: String,
    default: '操作'
  },
  operationsWidth: {
    type: [Number, String],
    default: 120
  },
  showEdit: {
    type: Boolean,
    default: true
  },
  editButtonText: {
    type: String,
    default: '编辑'
  },
  showDelete: {
    type: Boolean,
    default: true
  },
  deleteButtonText: {
    type: String,
    default: '删除'
  },
  deleteConfirmTitle: {
    type: String,
    default: '确认删除'
  },
  deleteConfirmMessage: {
    type: String,
    default: '确定要删除此记录吗？删除后无法恢复。'
  },
  emptyDescription: {
    type: String,
    default: '暂无数据'
  },
  showSelection: {
    type: Boolean,
    default: false
  },
  showPagination: {
    type: Boolean,
    default: false
  },
  total: {
    type: Number,
    default: 0
  },
  page: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 20
  },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  paginationLayout: {
    type: String,
    default: 'total, sizes, prev, pager, next'
  }
})

const emit = defineEmits([
  'add',
  'edit',
  'delete',
  'selection-change',
  'page-change',
  'size-change',
  'update:page',
  'update:pageSize'
])

const currentPage = computed({
  get: () => props.page,
  set: (val) => {
    emit('update:page', val)
    emit('page-change', val)
  }
})

const currentPageSize = computed({
  get: () => props.pageSize,
  set: (val) => {
    emit('update:pageSize', val)
    emit('size-change', val)
  }
})

const handleAdd = () => {
  emit('add')
}

const handleEdit = (row) => {
  emit('edit', row)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      props.deleteConfirmMessage,
      props.deleteConfirmTitle,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('delete', row)
  } catch {
    ElMessage.info('已取消删除')
  }
}

const handleSelectionChange = (selection) => {
  emit('selection-change', selection)
}

const handlePageChange = (val) => {
  emit('page-change', val)
}

const handleSizeChange = (val) => {
  emit('size-change', val)
}
</script>

<style scoped lang="scss">
.crud-table {
  padding: 0;
}

.crud-table-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: var(--spacing-md);
  gap: var(--spacing-sm);

  .add-btn {
    background: var(--brand-gradient);
    border: none;
    box-shadow: 0 2px 6px rgba(0, 102, 204, 0.2);
    transition: all var(--transition-base);

    &:hover {
      background: var(--brand-gradient-hover);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
    }
  }
}

.data-table {
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border-lighter);
}

.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: var(--spacing-lg) 0;
  gap: var(--spacing-sm);
}
</style>

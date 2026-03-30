<template>
  <CrudTable
    :data="list"
    :loading="loading"
    add-button-text="添加匹配规则"
    empty-description="暂无匹配规则"
    operations-width="120"
    @add="handleAdd"
    @edit="handleEdit"
    @delete="handleDelete"
  >
    <el-table-column prop="name" label="规则名称" min-width="150" />
    <el-table-column prop="rule_type_display" label="规则类型" width="120">
      <template #default="{ row }">
        <el-tag size="small">{{ row.rule_type_display || getMatchRuleTypeText(row.rule_type) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="priority" label="优先级" width="80" />
    <el-table-column prop="weight" label="权重" width="80">
      <template #default="{ row }">
        <span>{{ row.weight || 1 }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="is_active" label="状态" width="80">
      <template #default="{ row }">
        <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
          {{ row.is_active ? '启用' : '禁用' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
  </CrudTable>
</template>

<script setup>
import { CrudTable } from '@/components'
import { getMatchRuleTypeText } from '@/store/constants'

defineProps({
  list: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add', 'edit', 'delete'])

const handleAdd = () => emit('add')
const handleEdit = (row) => emit('edit', row)
const handleDelete = (row) => emit('delete', row)
</script>

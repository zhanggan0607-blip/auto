<template>
  <CrudTable
    :data="list"
    :loading="loading"
    add-button-text="添加业绩信息"
    empty-description="暂无业绩记录"
    operations-width="120"
    @add="handleAdd"
    @edit="handleEdit"
    @delete="handleDelete"
  >
    <el-table-column prop="project_name" label="项目名称" min-width="200" />
    <el-table-column prop="contract_amount" label="合同金额(万元)" width="120">
      <template #default="{ row }">
        <span v-if="row.contract_amount" class="info-value capital">
          ¥{{ row.contract_amount }}
        </span>
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column prop="end_date" label="完工日期" width="120" />
    <el-table-column prop="client_name" label="业主单位" width="150" />
  </CrudTable>
</template>

<script setup>
import { CrudTable } from '@/components'

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

<style scoped>
:deep(.info-value.capital) {
  color: #16A34A;
}
</style>

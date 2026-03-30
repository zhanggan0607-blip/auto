<template>
  <CrudTable
    :data="list"
    :loading="loading"
    add-button-text="添加联系人"
    empty-description="暂无联系人"
    operations-width="120"
    @add="handleAdd"
    @edit="handleEdit"
    @delete="handleDelete"
  >
    <el-table-column prop="name" label="姓名" width="100" />
    <el-table-column prop="contact_type_display" label="联系人类型" width="120">
      <template #default="{ row }">
        <el-tag size="small">{{ row.contact_type_display || getContactTypeText(row.contact_type) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="position" label="职位" width="120" />
    <el-table-column prop="phone" label="电话" width="140" />
    <el-table-column prop="email" label="邮箱" min-width="180" />
    <el-table-column prop="is_primary" label="主要联系人" width="100">
      <template #default="{ row }">
        <el-tag :type="row.is_primary ? 'success' : 'info'" size="small">
          {{ row.is_primary ? '是' : '否' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="is_active" label="状态" width="80">
      <template #default="{ row }">
        <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
          {{ row.is_active ? '有效' : '无效' }}
        </el-tag>
      </template>
    </el-table-column>
  </CrudTable>
</template>

<script setup>
import { CrudTable } from '@/components'
import { getContactTypeText } from '@/store/constants'

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

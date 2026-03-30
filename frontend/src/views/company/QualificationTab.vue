<template>
  <CrudTable
    :data="list"
    :loading="loading"
    add-button-text="添加资质信息"
    empty-description="暂无资质信息"
    operations-width="120"
    @add="handleAdd"
    @edit="handleEdit"
    @delete="handleDelete"
  >
    <el-table-column prop="qualification_category_display" label="资质类别" width="120" />
    <el-table-column prop="qualification_name_display" label="资质名称" min-width="180" />
    <el-table-column prop="grade" label="等级" width="80" />
    <el-table-column prop="certificate_no" label="资质证书号" width="150" />
    <el-table-column prop="expiry_date" label="有效期" width="120" />
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

<template>
  <div class="documents-section">
    <div class="documents-header">
      <el-select v-model="filterType" placeholder="证书类型" clearable style="width: 150px" @change="handleFilter">
        <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width: 100px; margin-left: 12px" @change="handleFilter">
        <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" style="margin-left: auto" @click="handleUpload">
        <el-icon><Upload /></el-icon>
        上传证书
      </el-button>
    </div>

    <el-table :data="list" size="small" stripe v-loading="loading">
      <el-table-column prop="document_type_display" label="证书类型" width="100" />
      <el-table-column prop="document_name" label="证书名称" min-width="150">
        <template #default="{ row }">
          <div class="doc-name">
            <el-icon v-if="row.is_primary" class="primary-icon"><Star /></el-icon>
            {{ row.document_name }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="document_no" label="证书编号" width="130" />
      <el-table-column prop="expiry_date" label="有效期至" width="100">
        <template #default="{ row }">
          <span :class="getExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status_display" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_display }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="handlePreview(row)">
            <el-icon><View /></el-icon>预览
          </el-button>
          <el-button type="danger" link @click="handleDelete(row)">
            <el-icon><Delete /></el-icon>删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="list.length === 0 && !loading" description="暂无文档资料" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Upload, View, Delete, Star } from '@element-plus/icons-vue'

const { list, loading, typeOptions, statusOptions } = defineProps({
  list: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  typeOptions: {
    type: Array,
    default: () => []
  },
  statusOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['upload', 'preview', 'delete', 'filter'])

const filterType = ref('')
const filterStatus = ref('')

const getStatusType = (status) => {
  const types = {
    valid: 'success',
    expiring: 'warning',
    expired: 'danger',
    pending: 'info'
  }
  return types[status] || 'info'
}

const getExpiryClass = (row) => {
  if (!row.expiry_date) return ''
  if (row.status === 'expired') return 'expiry-expired'
  if (row.status === 'expiring') return 'expiry-expiring'
  return ''
}

const handleFilter = () => {
  emit('filter', { type: filterType.value, status: filterStatus.value })
}

const handleUpload = () => emit('upload')
const handlePreview = (row) => emit('preview', row)
const handleDelete = (row) => emit('delete', row)
</script>

<style scoped>
.documents-section {
  padding: 0;
}

.documents-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.doc-name {
  display: flex;
  align-items: center;
}

.primary-icon {
  color: #E6A23C;
  margin-right: 4px;
}

.expiry-expired {
  color: #F56C6C;
}

.expiry-expiring {
  color: #E6A23C;
}
</style>

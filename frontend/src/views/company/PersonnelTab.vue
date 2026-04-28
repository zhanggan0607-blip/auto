<template>
  <div class="personnel-section">
    <div class="crud-table-header">
      <el-button type="primary" size="small" @click="handleAdd">
        <el-icon><Plus /></el-icon>{{ title }}
      </el-button>
    </div>
    <el-table :data="personnelList" size="small" stripe v-loading="loading">
      <el-table-column prop="personnel_id" label="人员ID" width="150" />
      <el-table-column prop="name" label="姓名" width="80" />
      <el-table-column prop="id_number" label="身份证号" width="180" />
      <el-table-column prop="birth_date" label="出生年月" width="100" />
      <template v-if="personnelType === 'project_manager'">
        <el-table-column prop="builder_certificate" label="建造师证书" min-width="150" />
        <el-table-column prop="safety_certificate_b" label="B证" width="100" />
      </template>
      <template v-if="['technical_director', 'professional_engineer'].includes(personnelType)">
        <el-table-column prop="engineer_title_certificate" label="工程师职称证" min-width="150" />
      </template>
      <template v-if="personnelType === 'eight_officers'">
        <el-table-column prop="officer_type_display" label="员种" width="80" />
      </template>
      <el-table-column prop="certificate_number" label="证书编号" width="140" />
      <el-table-column prop="certificate_major" label="注册专业" width="100" />
      <el-table-column prop="expiry_date" label="证书有效期" width="110">
        <template #default="{ row }">
          <span :class="getExpiryClass(row)">{{ row.expiry_date || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="title_level_display" label="职称等级" width="80" v-if="personnelType !== 'eight_officers'" />
      <el-table-column prop="is_registered_locally" label="本单位注册" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_registered_locally ? 'success' : 'info'" size="small">
            {{ row.is_registered_locally ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="professional_years" label="专业年限" width="80" v-if="personnelType !== 'eight_officers'" />
      <el-table-column prop="certificate_status_display" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="getStatusType('certificate_status', 'certificate_status', row.certificate_status)" size="small">
            {{ row.certificate_status_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="personnelList.length === 0 && !loading" :description="`暂无${title}`" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { getStatusType } from '@/store/constants'

const props = defineProps({
  personnelType: {
    type: String,
    required: true
  },
  personnelList: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['add', 'edit', 'delete'])

const titleMap = {
  'project_manager': '项目经理',
  'technical_director': '技术负责人',
  'professional_engineer': '专业工程师',
  'eight_officers': '八大员'
}

const title = computed(() => titleMap[props.personnelType] || '人员')

const getExpiryClass = (row) => {
  if (!row.expiry_date) return ''
  if (row.certificate_status === 'expired') return 'expiry-expired'
  if (row.certificate_status === 'expiring') return 'expiry-expiring'
  return ''
}

const handleAdd = () => {
  emit('add', props.personnelType)
}

const handleEdit = (row) => {
  emit('edit', row)
}

const handleDelete = (row) => {
  emit('delete', row)
}
</script>

<style scoped>
.personnel-section {
  padding: 0;
}

.crud-table-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.expiry-expired {
  color: #DC2626;
}

.expiry-expiring {
  color: #EA580C;
}
</style>

<template>
  <div class="page-container">
    <PageHeader title="用户管理" subtitle="管理系统用户账户和权限">
      <template #actions>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </template>
    </PageHeader>

    <div class="toolbar">
      <el-form :inline="true" :model="searchForm" @submit.prevent="handleSearch">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="请选择角色" clearable>
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="请选择状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-card class="data-card">
      <el-table v-if="Array.isArray(userList)" :data="userList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="32" class="user-avatar">
                {{ row.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="real_name" label="真实姓名" min-width="100" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              :loading="row._loading"
              @change="handleToggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button
              v-if="row.id !== currentUserId"
              type="danger"
              link
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <el-button
              type="warning"
              link
              size="small"
              @click="handleResetPassword(row)"
            >
              重置密码
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码（至少8位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="password_confirm" v-if="!isEdit">
          <el-input
            v-model="formData.password_confirm"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="formData.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { userAdminApi } from '@/api/userAdmin'
import { PageHeader } from '@/components'

const userStore = useUserStore()

const currentUserId = computed(() => userStore.userInfo?.id)

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const searchForm = reactive({
  username: '',
  role: '',
  is_active: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const userList = ref([])

const formData = reactive({
  username: '',
  password: '',
  password_confirm: '',
  real_name: '',
  email: '',
  phone: '',
  role: 'user'
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20位', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  password_confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const fetchUserList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })

    const res = await userAdminApi.list(params)
    userList.value = res.data.results || res.data.list || []
    pagination.total = res.data.count || res.data.total || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.role = ''
  searchForm.is_active = ''
  pagination.page = 1
  fetchUserList()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchUserList()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchUserList()
}

const showCreateDialog = () => {
  isEdit.value = false
  Object.assign(formData, {
    username: '',
    password: '',
    password_confirm: '',
    real_name: '',
    email: '',
    phone: '',
    role: 'user'
  })
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    username: row.username,
    password: '',
    password_confirm: '',
    real_name: row.real_name || '',
    email: row.email || '',
    phone: row.phone || '',
    role: row.role
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (!isEdit.value && formData.password !== formData.password_confirm) {
      ElMessage.error('两次密码输入不一致')
      return
    }

    submitLoading.value = true
    try {
      const submitData = { ...formData }
      if (isEdit.value) {
        delete submitData.password
        delete submitData.password_confirm
        delete submitData.username
        await userAdminApi.update(submitData.id, submitData)
        ElMessage.success('更新成功')
      } else {
        await userAdminApi.create(submitData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchUserList()
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error(error.message || '保存失败')
    } finally {
      submitLoading.value = false
    }
  })
}

const handleToggleStatus = async (row) => {
  row._loading = true
  try {
    await userAdminApi.toggleStatus(row.id, row.is_active)
    ElMessage.success(`${row.is_active ? '启用' : '禁用'}成功`)
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  } finally {
    row._loading = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${row.username}」吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await userAdminApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleResetPassword = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置用户「${row.username}」的密码吗？`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await userAdminApi.resetPassword(row.id)
    ElMessage.success('密码已重置为默认密码')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败')
    }
  }
}

onMounted(() => {
  fetchUserList()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 0;
}

.toolbar {
  background: var(--color-bg-white);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  border: 1px solid var(--color-border-lighter);
}

.data-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-lighter);

  :deep(.el-card__body) {
    padding: 0;
  }
}

.user-cell {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  .user-avatar {
    background: var(--brand-gradient);
    color: #fff;
    font-size: 14px;
    font-weight: var(--font-weight-semibold);
  }

  .username {
    font-weight: var(--font-weight-medium);
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-lg);
}
</style>

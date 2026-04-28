<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">个人中心</h3>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>基本信息</span>
          </template>
          <el-form :model="userForm" label-width="80px">
            <el-form-item label="用户名">
              <el-input v-model="userForm.username" disabled />
            </el-form-item>
            <el-form-item label="真实姓名">
              <el-input v-model="userForm.real_name" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="userForm.phone" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="userForm.email" />
            </el-form-item>
            <el-form-item label="企业名称">
              <el-input v-model="userForm.company_name" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="updateUserInfo">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form :model="passwordForm" label-width="100px" style="max-width: 400px;">
            <el-form-item label="当前密码">
              <el-input v-model="passwordForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="passwordForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="mt-20">
          <template #header>
            <span>登录日志</span>
          </template>
          <el-table :data="loginLogs" style="width: 100%">
            <el-table-column prop="login_ip" label="登录IP" width="150" />
            <el-table-column prop="login_time" label="登录时间" width="180" />
            <el-table-column prop="login_status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.login_status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.login_status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { authApi } from '@/api/auth'
import { parseListResponse } from '@/utils/response-parser'
import { useFormDraft } from '@/composables/useFormDraft'

const userStore = useUserStore()

const userForm = reactive({
  username: '',
  real_name: '',
  phone: '',
  email: '',
  company_name: ''
})

const { clearDraft: clearUserDraft } = useFormDraft(userForm, {
  key: 'profile:user',
  promptOnRestore: false
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const loginLogs = ref([])

const initUserForm = () => {
  const user = userStore.userInfo
  if (user) {
    userForm.username = user.username
    userForm.real_name = user.real_name || ''
    userForm.phone = user.phone || ''
    userForm.email = user.email || ''
    userForm.company_name = user.company_name || ''
  }
}

const updateUserInfo = async () => {
  try {
    await authApi.updateProfile({
      real_name: userForm.real_name,
      phone: userForm.phone,
      email: userForm.email,
      company_name: userForm.company_name
    })
    ElMessage.success('保存成功')
    clearUserDraft()
    userStore.fetchUserInfo()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const changePassword = async () => {
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  
  if (passwordForm.new_password.length < 6) {
    ElMessage.error('密码长度不能少于6位')
    return
  }
  
  ElMessage.info('密码修改功能需要后端支持')
}

const fetchLoginLogs = async () => {
  try {
    const res = await authApi.getLoginLogs({ page_size: 10 })
    const { list } = parseListResponse(res)
    loginLogs.value = list
  } catch (error) {
    console.error('获取登录日志失败:', error)
  }
}

onMounted(() => {
  initUserForm()
  fetchLoginLogs()
})
</script>

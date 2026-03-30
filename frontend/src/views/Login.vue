<template>
  <div class="login-container">
    <div class="login-decoration">
      <div class="decoration-circle circle-1" />
      <div class="decoration-circle circle-2" />
      <div class="decoration-circle circle-3" />
    </div>
    <div class="login-box">
      <div class="login-header">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h2 class="login-title">投标精灵</h2>
        <p class="login-subtitle">智能投标管理解决方案</p>
      </div>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            native-type="submit"
          >
            <span v-if="!loading">登 录</span>
            <span v-else>登录中...</span>
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="rememberUsername" class="remember-checkbox">
            记住用户名
          </el-checkbox>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const rememberUsername = ref(false)

const STORAGE_KEY = 'login_remembered_username'

onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    loginForm.username = saved
    rememberUsername.value = true
  }
})

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const result = await userStore.login(loginForm)
      loading.value = false

      if (result.success) {
        if (rememberUsername.value) {
          localStorage.setItem(STORAGE_KEY, loginForm.username)
        } else {
          localStorage.removeItem(STORAGE_KEY)
        }
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    }
  })
}
</script>

<style lang="scss" scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #F7F8FA 0%, #E8ECF0 100%);
  position: relative;
  overflow: hidden;
}

.login-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;

  .decoration-circle {
    position: absolute;
    border-radius: 50%;
    opacity: 0.08;

    &.circle-1 {
      width: 600px;
      height: 600px;
      background: var(--color-primary);
      top: -200px;
      right: -200px;
      animation: float 8s ease-in-out infinite;
    }

    &.circle-2 {
      width: 400px;
      height: 400px;
      background: var(--color-success);
      bottom: -100px;
      left: -100px;
      animation: float 6s ease-in-out infinite reverse;
    }

    &.circle-3 {
      width: 200px;
      height: 200px;
      background: var(--color-primary);
      top: 50%;
      left: 10%;
      animation: float 7s ease-in-out infinite;
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(20px, -20px);
  }
}

.login-box {
  width: 420px;
  padding: var(--spacing-2xl);
  background: var(--color-bg-white);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
  position: relative;
  z-index: 1;
  animation: scaleIn 0.4s ease;
  border: 1px solid var(--color-border-lighter);
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);

  .logo-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto var(--spacing-base);
    padding: var(--spacing-sm);
    background: var(--brand-gradient);
    border-radius: var(--radius-lg);
    color: #fff;
    box-shadow: 0 4px 16px rgba(0, 102, 204, 0.25);

    svg {
      width: 100%;
      height: 100%;
    }
  }

  .login-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    margin: 0 0 var(--spacing-xs);
  }

  .login-subtitle {
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    margin: 0;
  }
}

.login-form {
  :deep(.el-form-item) {
    margin-bottom: var(--spacing-lg);
  }

  :deep(.el-input) {
    .el-input__wrapper {
      padding: 4px 16px;
      border-radius: var(--radius-md);
      box-shadow: 0 0 0 1px var(--color-border);
      transition: all var(--transition-fast);

      &:hover {
        box-shadow: 0 0 0 1px var(--color-primary);
      }

      &.is-focus {
        box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15), 0 0 0 1px var(--color-primary);
      }
    }

    .el-input__inner {
      height: 44px;
      font-size: var(--font-size-base);
    }

    .el-input__prefix {
      color: var(--color-text-secondary);
    }
  }
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-md);
  background: var(--brand-gradient);
  border: none;
  box-shadow: 0 4px 16px rgba(0, 102, 204, 0.25);
  transition: all var(--transition-base);

  &:hover {
    background: var(--brand-gradient-hover);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 102, 204, 0.35);
  }

  &:active {
    transform: translateY(0);
  }
}

.remember-checkbox {
  width: 100%;
  text-align: left;
}

.login-footer {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);

  a {
    color: var(--color-primary);
    font-weight: var(--font-weight-medium);
    margin-left: var(--spacing-xs);

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>

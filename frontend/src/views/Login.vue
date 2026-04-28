<template>
  <div class="login-container">
    <div class="login-brand">
      <div class="brand-content">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h1 class="brand-title">投标精灵</h1>
        <p class="brand-subtitle">AI驱动的智能投标管理平台</p>
        <div class="brand-features">
          <div class="feature-item">
            <div class="feature-icon">🔍</div>
            <div class="feature-text">
              <div class="feature-title">智能采集</div>
              <div class="feature-desc">自动采集全网招标信息</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🤖</div>
            <div class="feature-text">
              <div class="feature-title">AI辅助</div>
              <div class="feature-desc">大模型驱动投标决策</div>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <div class="feature-text">
              <div class="feature-title">数据分析</div>
              <div class="feature-desc">全方位投标数据洞察</div>
            </div>
          </div>
        </div>
      </div>
      <div class="brand-decoration">
        <div class="deco-circle deco-1" />
        <div class="deco-circle deco-2" />
        <div class="deco-circle deco-3" />
      </div>
    </div>
    <div class="login-form-side">
      <div class="login-box">
        <div class="login-header">
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-subtitle">登录您的账户继续使用</p>
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
  overflow: hidden;
}

.login-brand {
  width: 55%;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1A56DB 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;

  .brand-content {
    position: relative;
    z-index: 2;
    padding: var(--spacing-3xl);
    max-width: 480px;
  }

  .brand-logo {
    width: 64px;
    height: 64px;
    margin-bottom: var(--spacing-xl);
    padding: var(--spacing-md);
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    color: #fff;
    backdrop-filter: blur(10px);

    svg {
      width: 100%;
      height: 100%;
    }
  }

  .brand-title {
    font-size: 36px;
    font-weight: var(--font-weight-bold);
    color: #fff;
    margin: 0 0 var(--spacing-sm);
    letter-spacing: 1px;
  }

  .brand-subtitle {
    font-size: var(--font-size-md);
    color: #93C5FD;
    margin: 0 0 var(--spacing-3xl);
  }

  .brand-features {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all var(--transition-base);

    &:hover {
      background: rgba(255, 255, 255, 0.08);
      transform: translateX(4px);
    }
  }

  .feature-icon {
    font-size: 24px;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-md);
    flex-shrink: 0;
  }

  .feature-title {
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: #fff;
    margin-bottom: 2px;
  }

  .feature-desc {
    font-size: var(--font-size-sm);
    color: #93C5FD;
  }

  .brand-decoration {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;

    .deco-circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(59, 130, 246, 0.15);

      &.deco-1 {
        width: 400px;
        height: 400px;
        top: -100px;
        right: -100px;
      }

      &.deco-2 {
        width: 300px;
        height: 300px;
        bottom: -80px;
        left: -80px;
      }

      &.deco-3 {
        width: 150px;
        height: 150px;
        top: 40%;
        right: 20%;
        background: rgba(59, 130, 246, 0.1);
      }
    }
  }
}

.login-form-side {
  width: 45%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-white);
  padding: var(--spacing-3xl);
}

.login-box {
  width: 100%;
  max-width: 400px;
  animation: scaleIn 0.4s ease;
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
  margin-bottom: var(--spacing-2xl);

  .login-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text-primary);
    margin: 0 0 var(--spacing-xs);
  }

  .login-subtitle {
    font-size: var(--font-size-md);
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
        box-shadow: 0 0 0 2px rgba(26, 86, 219, 0.15), 0 0 0 1px var(--color-primary);
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
  box-shadow: 0 4px 16px rgba(26, 86, 219, 0.25);
  transition: all var(--transition-base);

  &:hover {
    background: var(--brand-hover-gradient);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(26, 86, 219, 0.35);
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
  margin-top: var(--spacing-lg);

  a {
    color: var(--color-primary);
    font-weight: var(--font-weight-medium);
    margin-left: var(--spacing-xs);

    &:hover {
      text-decoration: underline;
    }
  }
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
  }

  .login-brand {
    display: none;
  }

  .login-form-side {
    width: 100%;
    padding: var(--spacing-xl);
  }
}
</style>

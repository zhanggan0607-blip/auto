<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">页面不存在</h2>
      <p class="error-desc">抱歉，您访问的页面不存在或已被移除</p>
      <el-button type="primary" size="large" @click="goHome" class="home-btn">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}
</script>

<style scoped lang="scss">
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1A56DB 100%);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    width: 400px;
    height: 400px;
    border-radius: 50%;
    background: rgba(59, 130, 246, 0.1);
    top: -100px;
    right: -100px;
  }

  &::after {
    content: '';
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: rgba(59, 130, 246, 0.08);
    bottom: -80px;
    left: -80px;
  }
}

.not-found-content {
  text-align: center;
  color: #fff;
  padding: 40px;
  position: relative;
  z-index: 1;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  margin: 0;
  line-height: 1;
  background: linear-gradient(135deg, #3B82F6, #60A5FA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.error-title {
  font-size: 28px;
  font-weight: 600;
  margin: 16px 0;
  color: #fff;
}

.error-desc {
  font-size: 16px;
  margin-bottom: 32px;
  color: #94A3B8;
}

.home-btn {
  background: var(--brand-gradient) !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  padding: 12px 32px !important;
  font-weight: 600 !important;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(26, 86, 219, 0.4);
  }
}
</style>

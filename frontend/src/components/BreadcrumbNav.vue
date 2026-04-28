<template>
  <el-breadcrumb separator="/" class="breadcrumb-nav">
    <el-breadcrumb-item :to="{ path: '/' }">
      <el-icon><HomeFilled /></el-icon>
      首页
    </el-breadcrumb-item>
    <el-breadcrumb-item v-for="item in items" :key="item.path" :to="item.path || undefined">
      {{ item.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
import { HomeFilled } from '@element-plus/icons-vue'

defineProps({
  items: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped lang="scss">
.breadcrumb-nav {
  font-size: 14px;
  
  :deep(.el-breadcrumb__item) {
    .el-breadcrumb__inner {
      display: flex;
      align-items: center;
      gap: 4px;
      
      a {
        color: #334155;
        text-decoration: none;
        
        &:hover {
          color: #3B82F6;
        }
      }
    }
    
    &:last-child .el-breadcrumb__inner {
      color: #1E293B;
      font-weight: 500;
    }
  }
}
</style>

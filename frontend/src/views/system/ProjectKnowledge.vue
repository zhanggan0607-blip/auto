<template>
  <div class="page-container">
    <PageHeader title="项目知识库" subtitle="AI助手了解项目的上下文信息">
      <template #actions>
        <el-button @click="loadKnowledge" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="copyContext" :disabled="!context">
          <el-icon><DocumentCopy /></el-icon>
          复制上下文
        </el-button>
      </template>
    </PageHeader>

    <div class="knowledge-container" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card class="main-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>项目概览</span>
              </div>
            </template>
            <div class="info-section" v-if="knowledge.project_overview">
              <h3>{{ knowledge.project_overview.name }}</h3>
              <p class="version">版本: {{ knowledge.project_overview.version }}</p>
              <p class="description">{{ knowledge.project_overview.description }}</p>

              <h4>技术栈</h4>
              <div class="tech-stack">
                <el-tag v-for="(value, key) in knowledge.project_overview.tech_stack" :key="key" type="info" class="tech-tag">
                  {{ key }}: {{ value }}
                </el-tag>
              </div>

              <h4>主要功能</h4>
              <ul class="feature-list">
                <li v-for="feature in knowledge.project_overview.main_features" :key="feature">
                  {{ feature }}
                </li>
              </ul>
            </div>
          </el-card>

          <el-card class="main-card mt-20" shadow="never">
            <template #header>
              <div class="card-header">
                <span>项目模块</span>
                <span class="module-count">{{ knowledge.modules?.length || 0 }} 个模块</span>
              </div>
            </template>
            <el-table :data="knowledge.modules" stripe size="small" max-height="400">
              <el-table-column prop="verbose_name" label="模块名称" width="150" />
              <el-table-column prop="name" label="英文名" width="120" />
              <el-table-column prop="files" label="包含文件" min-width="200">
                <template #default="{ row }">
                  <el-tag v-for="file in (row.files || []).slice(0, 5)" :key="file" size="small" class="file-tag">
                    {{ file }}
                  </el-tag>
                  <span v-if="(row.files || []).length > 5">...</span>
                </template>
              </el-table-column>
              <el-table-column label="功能" width="150">
                <template #default="{ row }">
                  <el-icon v-if="row.has_views"><Connection /></el-icon>
                  <el-icon v-if="row.has_models"><Document /></el-icon>
                  <el-icon v-if="row.has_urls"><Link /></el-icon>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card class="main-card mt-20" shadow="never">
            <template #header>
              <div class="card-header">
                <span>数据库模型</span>
              </div>
            </template>
            <div class="models-section">
              <div v-for="app in knowledge.database_models" :key="app.app" class="app-models">
                <h5>{{ app.app }}</h5>
                <el-tag v-for="model in app.models" :key="model" size="small" type="success" class="model-tag">
                  {{ model }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="10">
          <el-card class="context-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span>AI 上下文</span>
              </div>
            </template>
            <div class="context-actions">
              <el-button type="primary" size="small" @click="loadContext" :loading="contextLoading">
                生成上下文
              </el-button>
              <el-button size="small" @click="copyContext" :disabled="!context">
                复制到剪贴板
              </el-button>
            </div>
            <el-input
              v-model="context"
              type="textarea"
              :rows="25"
              placeholder="点击「生成上下文」按钮获取AI可理解的项目信息"
              resize="none"
              class="context-textarea"
            />
          </el-card>

          <el-card class="main-card mt-20" shadow="never">
            <template #header>
              <div class="card-header">
                <span>API 路由</span>
                <span class="route-count">{{ knowledge.api_routes?.length || 0 }} 条</span>
              </div>
            </template>
            <div class="routes-list">
              <div v-for="route in (knowledge.api_routes || []).slice(0, 30)" :key="route.path" class="route-item">
                <el-tag size="small" type="info" class="route-method">{{ route.app }}</el-tag>
                <span class="route-path">{{ route.path }}</span>
              </div>
              <div v-if="knowledge.api_routes?.length > 30" class="more-routes">
                还有 {{ knowledge.api_routes.length - 30 }} 条路由...
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, DocumentCopy, Connection, Document, Link } from '@element-plus/icons-vue'
import { PageHeader } from '@/components'
import request from '@/utils/request'

const loading = ref(false)
const contextLoading = ref(false)
const knowledge = ref({})
const context = ref('')

const loadKnowledge = async () => {
  loading.value = true
  try {
    const res = await request.get('/v1/knowledge/')
    knowledge.value = res.data || {}
  } catch (error) {
    ElMessage.error('获取项目知识库失败')
  } finally {
    loading.value = false
  }
}

const loadContext = async () => {
  contextLoading.value = true
  try {
    const res = await request.get('/v1/knowledge/context/')
    context.value = res.data?.context || ''
    ElMessage.success('上下文已生成')
  } catch (error) {
    ElMessage.error('生成上下文失败')
  } finally {
    contextLoading.value = false
  }
}

const copyContext = async () => {
  if (!context.value) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  try {
    await navigator.clipboard.writeText(context.value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

onMounted(() => {
  loadKnowledge()
})
</script>

<style scoped lang="scss">
.knowledge-container {
  padding: 0;
}

.main-card {
  border-radius: var(--radius-lg);

  :deep(.el-card__header) {
    padding: var(--spacing-md) var(--spacing-lg);
    background-color: var(--color-bg-base);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-card__body) {
    padding: var(--spacing-lg);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  .module-count, .route-count {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }
}

.info-section {
  h3 {
    margin: 0 0 var(--spacing-xs) 0;
    color: var(--color-text-primary);
  }

  .version {
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
    margin-bottom: var(--spacing-sm);
  }

  .description {
    color: var(--color-text-regular);
    line-height: 1.6;
    margin-bottom: var(--spacing-lg);
  }

  h4 {
    margin: var(--spacing-lg) 0 var(--spacing-sm) 0;
    font-size: var(--font-size-md);
    color: var(--color-text-primary);
  }
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);

  .tech-tag {
    font-size: var(--font-size-xs);
  }
}

.feature-list {
  margin: 0;
  padding-left: var(--spacing-lg);

  li {
    margin-bottom: var(--spacing-xs);
    color: var(--color-text-regular);
  }
}

.file-tag, .model-tag {
  margin: 2px;
}

.models-section {
  .app-models {
    margin-bottom: var(--spacing-md);

    h5 {
      margin: 0 0 var(--spacing-xs) 0;
      font-size: var(--font-size-sm);
      color: var(--color-text-primary);
    }
  }
}

.context-card {
  border-radius: var(--radius-lg);

  :deep(.el-card__header) {
    padding: var(--spacing-md) var(--spacing-lg);
    background-color: var(--color-bg-base);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-card__body) {
    padding: var(--spacing-lg);
  }
}

.context-actions {
  margin-bottom: var(--spacing-md);
  display: flex;
  gap: var(--spacing-sm);
}

.context-textarea {
  :deep(.el-textarea__inner) {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
  }
}

.routes-list {
  max-height: 400px;
  overflow-y: auto;

  .route-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) 0;
    border-bottom: 1px solid var(--color-border-lighter);

    &:last-child {
      border-bottom: none;
    }
  }

  .route-method {
    flex-shrink: 0;
    font-size: 10px;
  }

  .route-path {
    font-size: var(--font-size-xs);
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    color: var(--color-text-secondary);
    word-break: break-all;
  }

  .more-routes {
    padding: var(--spacing-sm) 0;
    text-align: center;
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }
}

.mt-20 {
  margin-top: 20px;
}
</style>
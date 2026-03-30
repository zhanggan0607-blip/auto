<template>
  <div class="page-container">
    <PageHeader title="MultiViewDialog 演示" subtitle="多视图切换对话框组件测试">
      <template #actions>
        <el-button type="primary" @click="dialogVisible = true">
          <el-icon><Plus /></el-icon>
          打开对话框
        </el-button>
      </template>
    </PageHeader>

    <el-card class="demo-card" shadow="never">
      <template #header>
        <span>组件特性</span>
      </template>
      <div class="features">
        <div class="feature-item">
          <el-icon color="#409EFF"><Check /></el-icon>
          <span>Tab 样式切换 - 顶部选项卡切换视图</span>
        </div>
        <div class="feature-item">
          <el-icon color="#409EFF"><Check /></el-icon>
          <span>平滑过渡动画 - fade / slide / zoom 三种效果</span>
        </div>
        <div class="feature-item">
          <el-icon color="#409EFF"><Check /></el-icon>
          <span>Active 视觉标识 - 当前激活 Tab 有下划线和颜色标识</span>
        </div>
        <div class="feature-item">
          <el-icon color="#409EFF"><Check /></el-icon>
          <span>插槽支持 - 每个视图使用具名插槽</span>
        </div>
        <div class="feature-item">
          <el-icon color="#409EFF"><Check /></el-icon>
          <span>暴露方法 - open() / close() / setView()</span>
        </div>
      </div>
    </el-card>

    <el-card class="demo-card mt-20" shadow="never">
      <template #header>
        <span>使用代码</span>
      </template>
      <pre class="code-block"><code>&lt;template&gt;
  &lt;MultiViewDialog
    v-model="dialogVisible"
    title="多视图对话框"
    :views="[
      { name: 'chat', label: '对话', icon: Chat },
      { name: 'knowledge', label: '知识库', icon: Book },
      { name: 'settings', label: '设置', icon: Setting }
    ]"
  &gt;
    &lt;template #chat&gt;对话内容&lt;/template&gt;
    &lt;template #knowledge&gt;知识库内容&lt;/template&gt;
    &lt;template #settings&gt;设置内容&lt;/template&gt;
  &lt;/MultiViewDialog&gt;
&lt;/template&gt;</code></pre>
    </el-card>

    <MultiViewDialog
      v-model="dialogVisible"
      title="AI 助手 - 多视图切换"
      width="900px"
      :views="dialogViews"
      transition="slide"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    >
      <template #chat>
        <div class="view-panel">
          <div class="panel-header">
            <el-icon><ChatDotRound /></el-icon>
            <span>对话视图</span>
          </div>
          <div class="panel-content">
            <p>这是一个对话视图，可以在这里进行聊天交互。</p>
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="3"
              placeholder="输入对话内容..."
            />
            <el-button type="primary" class="mt-10">发送</el-button>
          </div>
        </div>
      </template>

      <template #knowledge>
        <div class="view-panel">
          <div class="panel-header">
            <el-icon><Collection /></el-icon>
            <span>知识库视图</span>
          </div>
          <div class="panel-content">
            <p>知识库视图，用于展示项目知识库内容。</p>
            <el-table :data="knowledgeData" stripe size="small">
              <el-table-column prop="name" label="模块" />
              <el-table-column prop="models" label="模型数" />
              <el-table-column prop="apis" label="API数" />
            </el-table>
          </div>
        </div>
      </template>

      <template #settings>
        <div class="view-panel">
          <div class="panel-header">
            <el-icon><Setting /></el-icon>
            <span>设置视图</span>
          </div>
          <div class="panel-content">
            <p>设置视图，用于配置各种参数。</p>
            <el-form label-position="top" size="small">
              <el-form-item label="温度">
                <el-slider v-model="temp" :min="0" :max="2" :step="0.1" show-input />
              </el-form-item>
              <el-form-item label="最大Token">
                <el-input-number v-model="maxToken" :min="256" :max="128000" :step="256" />
              </el-form-item>
              <el-form-item label="流式输出">
                <el-switch v-model="streamMode" />
              </el-form-item>
            </el-form>
          </div>
        </div>
      </template>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确认</el-button>
      </template>
    </MultiViewDialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Collection, Setting, Plus, Check } from '@element-plus/icons-vue'
import { MultiViewDialog } from '@/components'
import { PageHeader } from '@/components'

const dialogVisible = ref(false)
const chatInput = ref('')
const temp = ref(0.7)
const maxToken = ref(4096)
const streamMode = ref(true)

const dialogViews = [
  { name: 'chat', label: '对话', icon: ChatDotRound },
  { name: 'knowledge', label: '知识库', icon: Collection },
  { name: 'settings', label: '设置', icon: Setting }
]

const knowledgeData = ref([
  { name: 'tenders', models: 5, apis: 12 },
  { name: 'enterprise', models: 8, apis: 20 },
  { name: 'documents', models: 4, apis: 8 },
  { name: 'bids', models: 3, apis: 6 }
])

const handleConfirm = () => {
  ElMessage.success('确认操作，当前视图: ' + dialogViews.find(v => v.name === 'chat').label)
}

const handleCancel = () => {
  ElMessage.info('取消操作')
}
</script>

<style scoped lang="scss">
.demo-card {
  border-radius: var(--radius-lg);

  :deep(.el-card__header) {
    padding: var(--spacing-md) var(--spacing-lg);
    background-color: var(--color-bg-base);
    border-bottom: 1px solid var(--color-border-lighter);
  }
}

.features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);

  .feature-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--font-size-sm);
    color: var(--color-text-regular);
  }
}

.code-block {
  background: var(--color-bg-base);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  font-size: var(--font-size-xs);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  margin: 0;
}

.view-panel {
  .panel-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border-lighter);

    .el-icon {
      font-size: var(--font-size-lg);
      color: var(--color-primary);
    }
  }

  .panel-content {
    p {
      margin: 0 0 var(--spacing-md) 0;
      color: var(--color-text-secondary);
    }
  }
}

.mt-10 {
  margin-top: 10px;
}

.mt-20 {
  margin-top: 20px;
}
</style>
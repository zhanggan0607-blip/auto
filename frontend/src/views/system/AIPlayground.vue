<template>
  <div class="ai-playground">
    <PageHeader title="AI Playground">
      <template #actions>
        <el-button @click="testAllProviders" :loading="testing" type="success">
          <el-icon><Connection /></el-icon>
          测试所有连接
        </el-button>
        <el-button @click="showHistory = true">
          <el-icon><Clock /></el-icon>
          调用历史
        </el-button>
      </template>
    </PageHeader>

    <div class="playground-container">
      <div class="playground-main">
        <el-card class="chat-card">
          <template #header>
            <div class="chat-header">
              <div class="model-badge">
                <el-tag type="info" size="small">投标精灵</el-tag>
              </div>
            </div>
          </template>

          <div class="chat-messages" ref="messagesContainer">
            <div class="messages-container">
              <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
                <div class="message-avatar">
                  <el-avatar :size="36" :icon="ChatDotRound" />
                </div>
                <div class="message-content">
                  <div class="message-header">
                    <span class="sender-name">{{ msg.role === 'user' ? '你' : currentProviderName }}</span>
                    <span class="message-time" v-if="msg.timestamp">{{ formatDateTime(msg.timestamp) }}</span>
                  </div>
                  <div class="message-text" v-html="formatMessage(msg.content)" />
                  <div class="message-meta" v-if="msg.meta">
                    <span>Tokens: {{ msg.meta.total_tokens || 0 }}</span>
                    <span>延迟: {{ msg.meta.latency?.toFixed(2) || 0 }}s</span>
                  </div>
                </div>
              </div>
              <div v-if="loading" class="message assistant loading">
                <div class="message-avatar">
                  <el-avatar :size="36" :icon="ChatDotRound" />
                </div>
                <div class="message-content">
                  <div class="typing-indicator">
                    <span /><span /><span />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input-wrapper">
            <div class="chat-input-container">
              <el-input
                v-model="inputMessage"
                type="textarea"
                :rows="2"
                placeholder="输入消息..."
                resize="none"
                @keydown.enter.exact.prevent="handleSend"
                @keydown.enter.shift="handleShiftEnter"
              />
              <div class="input-actions">
                <el-checkbox v-model="streamMode" size="small">流式输出</el-checkbox>
                <div class="right-actions">
                  <el-button @click="clearChat" text size="small">清空对话</el-button>
                  <el-button type="primary" @click="handleSend" :loading="loading" :disabled="!inputMessage.trim()" circle>
                    <el-icon v-if="!loading"><Promotion /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="playground-sidebar">
        <el-card class="params-card">
          <template #header>
            <span>参数设置</span>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="系统提示词">
              <el-input
                v-model="systemPrompt"
                type="textarea"
                :rows="4"
                placeholder="可选的系统提示词"
              />
            </el-form-item>
            <el-form-item label="温度 (Temperature)">
              <el-slider v-model="temperature" :min="0" :max="2" :step="0.1" show-input />
              <div class="param-hint">控制随机性：0更确定性，2更有创造性</div>
            </el-form-item>
            <el-form-item label="最大Token数">
              <el-input-number v-model="maxTokens" :min="256" :max="128000" :step="256" />
            </el-form-item>
            <el-form-item>
              <el-button @click="resetParams" size="small" type="info" plain>重置参数</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="stats-card" v-if="statistics">
          <template #header>
            <span>本次会话统计</span>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ statistics.total_calls }}</div>
              <div class="stat-label">对话轮次</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ statistics.total_tokens }}</div>
              <div class="stat-label">总Tokens</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ statistics.avg_latency?.toFixed(2) || 0 }}s</div>
              <div class="stat-label">平均延迟</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ statistics.success_rate?.toFixed(1) || 100 }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="showHistory" title="调用历史" :close-on-click-modal="false" :destroy-on-close="true" class="fixed-dialog">
      <div class="history-filters">
        <el-select v-model="historyProvider" placeholder="筛选提供商" clearable size="small">
          <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-checkbox v-model="historySuccessOnly" size="small">仅显示成功</el-checkbox>
        <el-button size="small" @click="loadHistory">刷新</el-button>
      </div>
      <el-table :data="historyList" stripe size="small" max-height="400">
        <el-table-column prop="provider" label="提供商" width="120" />
        <el-table-column prop="model" label="模型" width="150" />
        <el-table-column prop="content_preview" label="内容预览" min-width="200" show-overflow-tooltip />
        <el-table-column prop="total_tokens" label="Tokens" width="100" />
        <el-table-column prop="latency" label="延迟" width="80">
          <template #default="{ row }">{{ row.latency?.toFixed(2) }}s</template>
        </el-table-column>
        <el-table-column prop="success" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="historyPage"
        v-model:page-size="historyPageSize"
        :total="historyTotal"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadHistory"
        @current-change="loadHistory"
      />
    </el-dialog>

    <el-dialog v-model="showTestResults" title="连接测试结果" :close-on-click-modal="false" :destroy-on-close="true" class="fixed-dialog">
      <el-table :data="testResults" stripe size="small">
        <el-table-column prop="provider_name" label="提供商" width="120" />
        <el-table-column prop="model" label="模型" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency" label="延迟" width="80">
          <template #default="{ row }">{{ row.latency?.toFixed(2) || 0 }}s</template>
        </el-table-column>
        <el-table-column prop="response" label="响应" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Promotion, Clock, Connection } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import { modelApi } from '@/api/model'
import { PageHeader } from '@/components'
import { useUserStore } from '@/store/user'
import { formatDateTime } from '@/utils/date'

const DEFAULT_MODEL = 'gemma3:1b'
const userStore = useUserStore()

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const streamMode = ref(true)
const systemPrompt = ref('')
const temperature = ref(0.7)
const maxTokens = ref(4096)
const messagesContainer = ref(null)
const testing = ref(false)
const showHistory = ref(false)
const showTestResults = ref(false)
const historyList = ref([])
const historyPage = ref(1)
const historyPageSize = ref(20)
const historyTotal = ref(0)
const historyProvider = ref(null)
const historySuccessOnly = ref(false)
const testResults = ref([])
const providers = ref([])
const providerModelsMap = ref({})
const selectedProvider = ref(null)
const selectedModel = ref(DEFAULT_MODEL)

const statistics = reactive({
  total_calls: 0,
  total_tokens: 0,
  avg_latency: 0,
  success_rate: 100
})

const currentProviderName = computed(() => {
  return DEFAULT_MODEL
})

const loadProviders = async () => {
  try {
    const res = await modelApi.listProviders()
    const data = Array.isArray(res.data) ? res.data : (res.data?.data || [])
    providers.value = data
      .filter(p => p.is_active)
      .map(p => ({
        id: p.id,
        name: p.name,
        provider_type: p.type || p.provider_type,
        default_model: p.default_model,
        is_default: p.is_default,
        is_active: p.is_active,
        available_models: p.available_models || []
      }))
    for (const p of providers.value) {
      providerModelsMap.value[p.id] = p.available_models || []
    }
    const defaultProvider = providers.value.find(p => p.is_default)
    if (defaultProvider) {
      selectedProvider.value = defaultProvider.id
    } else {
      const ollamaProvider = providers.value.find(p => p.provider_type === 'ollama')
      if (ollamaProvider) {
        selectedProvider.value = ollamaProvider.id
      }
    }
  } catch (error) {
    console.error('加载提供商失败:', error)
  }
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    role: 'user',
    content: userMessage,
    timestamp: new Date().toISOString()
  })

  await scrollToBottom()
  loading.value = true

  const history = messages.value
    .filter(m => m.role === 'user' || (m.role === 'assistant' && !m.loading))
    .slice(0, -1)
    .map(m => ({ role: m.role, content: m.content }))

  try {
    if (streamMode.value) {
      await streamChat(userMessage, history)
    } else {
      await normalChat(userMessage, history)
    }
  } catch (error) {
    ElMessage.error(error.message || '调用失败')
    messages.value.push({
      role: 'assistant',
      content: `错误: ${error.message || '未知错误'}`,
      timestamp: new Date().toISOString(),
      meta: { success: false }
    })
    updateStatistics(false, 0, 0)
  }

  loading.value = false
}

const streamChat = async (message, history) => {
  let fullContent = ''
  try {
    const token = userStore.token || document.cookie.match(/access_token=([^;]+)/)?.[1]
    if (!token) {
      ElMessage.error('请先登录')
      return
    }
    const response = await fetch('/api/v1/openclaw/playground/stream_chat/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        provider_id: selectedProvider.value,
        model_id: selectedModel.value,
        message: message,
        system_prompt: systemPrompt.value || undefined,
        temperature: temperature.value,
        max_tokens: maxTokens.value,
        history: history
      })
    })

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6))
            if (data.content) {
              fullContent += data.content
              updateLastMessage(fullContent)
              await nextTick()
            }
          } catch {
            // Ignore parsing errors for non-data lines
          }
        }
      }
    }

    const lastIndex = messages.value.length - 1
    if (lastIndex >= 0 && messages.value[lastIndex].role === 'assistant') {
      messages.value[lastIndex].loading = false
      messages.value[lastIndex].meta = { total_tokens: 0, latency: 0 }
    }
    updateStatistics(true, 0, 0)
  } catch (error) {
    ElMessage.error(error.message || '调用失败')
    messages.value.push({
      role: 'assistant',
      content: `错误: ${error.message || '未知错误'}`,
      timestamp: new Date().toISOString(),
      meta: { success: false }
    })
    updateStatistics(false, 0, 0)
  }
}

const normalChat = async (message, history) => {
  const res = await modelApi.playground.chat({
    provider_id: selectedProvider.value,
    model_id: selectedModel.value,
    message: message,
    system_prompt: systemPrompt.value || undefined,
    temperature: temperature.value,
    max_tokens: maxTokens.value,
    history: history
  })

  messages.value.push({
    role: 'assistant',
    content: res.data.content,
    timestamp: res.data.timestamp || new Date().toISOString(),
    meta: {
      total_tokens: res.data.total_tokens,
      latency: res.data.latency
    }
  })

  updateStatistics(true, res.data.total_tokens, res.data.latency)
}

const updateLastMessage = (content) => {
  const lastIndex = messages.value.length - 1
  if (lastIndex >= 0 && messages.value[lastIndex].role === 'assistant' && messages.value[lastIndex].loading) {
    messages.value[lastIndex].content = content
  } else if (lastIndex >= 0 && messages.value[lastIndex].role === 'user') {
    messages.value.push({
      role: 'assistant',
      content: content,
      timestamp: new Date().toISOString(),
      loading: true
    })
  } else if (lastIndex >= 0) {
    messages.value[lastIndex].content = content
  }
}

const updateStatistics = (success, tokens, latency) => {
  statistics.total_calls++
  if (success) {
    statistics.total_tokens += tokens
    if (statistics.total_calls > 1) {
      statistics.avg_latency = (statistics.avg_latency * (statistics.total_calls - 1) + latency) / statistics.total_calls
    } else {
      statistics.avg_latency = latency
    }
  } else {
    const failures = messages.value.filter(m => m.meta?.success === false).length
    statistics.success_rate = ((statistics.total_calls - failures) / statistics.total_calls) * 100
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const clearChat = () => {
  ElMessageBox.confirm('确定要清空当前对话吗？', '确认清空', {
    type: 'warning'
  }).then(() => {
    messages.value = []
    statistics.total_calls = 0
    statistics.total_tokens = 0
    statistics.avg_latency = 0
    statistics.success_rate = 100
  }).catch(() => {})
}

const resetParams = () => {
  temperature.value = 0.7
  maxTokens.value = 4096
  systemPrompt.value = ''
}

const loadHistory = async () => {
  try {
    const res = await modelApi.playground.getHistory({
      page: historyPage.value,
      page_size: historyPageSize.value,
      provider_id: historyProvider.value || undefined,
      success_only: historySuccessOnly.value || undefined
    })
    historyList.value = res.data.items || []
    historyTotal.value = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载历史记录失败')
  }
}

const testAllProviders = async () => {
  testing.value = true
  showTestResults.value = true
  try {
    const res = await modelApi.playground.testAllProviders()
    testResults.value = res.data || []
  } catch (error) {
    ElMessage.error('测试失败')
  }
  testing.value = false
}

const formatMessage = (content) => {
  if (!content) return ''
  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'code', 'pre', 'br', 'p', 'span', 'div', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'hr', 'a'],
    ALLOWED_ATTR: ['href', 'title', 'class'],
    ALLOW_DATA_ATTR: false
  })
}

const handleShiftEnter = () => {
}

onMounted(() => {
  loadProviders()
})
</script>

<style scoped lang="scss">
.ai-playground {
  padding: 0;
  height: 100%;
}

.playground-container {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: var(--spacing-lg);
  height: calc(100vh - 180px);
}

.playground-main {
  display: flex;
  flex-direction: column;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);

  :deep(.el-card__header) {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
  }
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.model-badge {
  display: flex;
  align-items: center;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
}

.messages-container {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.message {
  display: flex;
  gap: var(--spacing-md);
  width: 100%;
  max-width: 800px;
  margin: 0 auto;

  &.user {
    flex-direction: row-reverse;

    .message-avatar {
      display: none;
    }

    .message-content {
      background: var(--color-primary);
      color: white;
      border-radius: 18px 18px 4px 18px;
      max-width: 85%;
    }

    .message-header .sender-name,
    .message-meta {
      color: rgba(255, 255, 255, 0.75);
    }
  }

  &.assistant {
    flex-direction: row;

    .message-content {
      background: var(--color-bg-white);
      border-radius: 18px 18px 18px 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      max-width: 85%;
    }
  }

  &.loading .message-content {
    background: var(--color-bg-white);
    min-width: 60px;
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  padding: var(--spacing-md) var(--spacing-lg);
  line-height: 1.5;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xs);

  .sender-name {
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
  }

  .message-time {
    font-size: var(--font-size-xs);
    color: var(--color-text-placeholder);
  }
}

.message-text {
  font-size: var(--font-size-base);
  white-space: pre-wrap;
  word-break: break-word;
}

.message-meta {
  display: flex;
  gap: var(--spacing-md);
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-xs);
  color: var(--color-text-placeholder);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: var(--spacing-sm);

  span {
    width: 8px;
    height: 8px;
    background: var(--color-text-placeholder);
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;

    &:nth-child(1) { animation-delay: 0s; }
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.chat-input-wrapper {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--color-bg-page);
  border-top: 1px solid var(--color-border-lighter);
}

.chat-input-container {
  max-width: 800px;
  margin: 0 auto;

  :deep(.el-textarea__inner) {
    border-radius: 24px;
    padding: 12px 16px;
    line-height: 1.5;
  }
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-sm);
  padding: 0 var(--spacing-xs);

  .right-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }
}

.playground-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  overflow-y: auto;
}

.params-card, .stats-card {
  border-radius: var(--radius-lg);

  :deep(.el-card__header) {
    font-weight: var(--font-weight-medium);
  }
}

.param-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-xs);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-sm);
  background: var(--color-bg-page);
  border-radius: var(--radius-md);

  .stat-value {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin-top: var(--spacing-xs);
  }
}

.history-filters {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  align-items: center;
}

.fixed-dialog {
  width: 900px;
  max-width: 900px;

  :deep(.el-dialog__body) {
    max-height: 70vh;
    overflow-y: auto;
    overflow-x: hidden;
  }
}
</style>

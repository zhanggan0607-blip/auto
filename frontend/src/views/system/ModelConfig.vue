<template>
  <div class="page-container">
    <el-card class="ollama-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="card-title">投标精灵 本地模型配置</span>
            <span class="card-subtitle">支持本地部署的 Qwen、Llama 等模型</span>
          </div>
          <el-button type="primary" @click="checkOllamaStatus()" :loading="checkingOllama">
            <el-icon><Refresh /></el-icon>
            检测状态
          </el-button>
          <el-button @click="toggleSort" type="info" plain>
            <el-icon><Sort /></el-icon>
            按大小{{ sortAscending ? '↑' : '↓' }}
          </el-button>
        </div>
      </template>
      <div class="ollama-status">
        <div class="status-item">
          <span class="label">连接状态：</span>
          <el-tag :type="ollamaStatus.connected ? 'success' : 'danger'">
            {{ ollamaStatus.connected ? '已连接' : '未连接' }}
          </el-tag>
        </div>
        <div class="status-item">
          <span class="label">版本：</span>
          <span>{{ ollamaStatus.version || '未知' }}</span>
        </div>
        <div class="status-item">
          <span class="label">可用模型：</span>
          <span>{{ ollamaModels.length }} 个</span>
        </div>
      </div>

      <el-divider />

      <div class="ollama-config">
        <h4>连接配置</h4>
        <el-form :model="ollamaConfig" label-width="120px">
          <el-form-item label="投标精灵地址">
            <el-input
              v-model="ollamaConfig.base_url"
              placeholder="http://localhost:11434"
              @blur="checkOllamaStatus()"
            >
              <template #append>
                <el-button @click="checkOllamaStatus()" :loading="checkingOllama">
                  连接
                </el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="默认模型">
            <el-select v-model="ollamaConfig.default_model" placeholder="请选择模型" clearable>
              <el-option
                v-for="model in ollamaModels"
                :key="model.name"
                :label="model.name"
                :value="model.name"
              >
                <span>{{ model.name }}</span>
                <span class="model-size">{{ formatSize(model.size) }}</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>

        <div class="model-list">
          <h4>
            已安装模型
            <span class="sort-indicator" v-if="ollamaModels.length > 0">
              ({{ sortAscending ? '从小到大' : '从大到小' }})
            </span>
          </h4>
          <el-table :data="sortedOllamaModels" stripe size="small">
            <el-table-column label="模型名称" min-width="150">
              <template #default="{ row }">
                {{ formatModelName(row.name) }}
              </template>
            </el-table-column>
            <el-table-column label="模型标识" min-width="150">
              <template #default="{ row }">
                {{ formatModelSize(row.name) }}
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="120" sortable>
              <template #default="{ row }">
                {{ formatSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="modified_at" label="更新时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.modified_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="testModel(row.name)">
                  测试
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <el-card class="agent-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span class="card-title">Agent 模型配置</span>
            <span class="card-subtitle">为不同类型的 Agent 分配专用模型</span>
          </div>
          <el-button type="primary" @click="saveAgentConfigs" :loading="saving">
            保存配置
          </el-button>
        </div>
      </template>
      <el-table :data="agentConfigs" stripe>
        <el-table-column prop="agent_type" label="Agent类型" width="150">
          <template #default="{ row }">
            {{ getAgentTypeText(row.agent_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="chat_model" label="对话模型" min-width="200">
          <template #default="{ row }">
            <el-select
              v-model="row.chat_model_id"
              placeholder="请选择对话模型"
              size="small"
              style="width: 100%"
            >
              <el-option
                v-for="model in allModels"
                :key="model.model_id"
                :label="model.name"
                :value="model.model_id"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="temperature" label="温度参数" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              :precision="1"
              size="small"
              style="width: 100px"
            />
          </template>
        </el-table-column>
        <el-table-column prop="max_tokens" label="最大Token" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.max_tokens"
              :min="256"
              :max="128000"
              :step="256"
              size="small"
              style="width: 100px"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Sort } from '@element-plus/icons-vue'
import { modelApi } from '@/api/model'

const refreshing = ref(false)
const checkingOllama = ref(false)
const saving = ref(false)
const sortAscending = ref(true)

const allModels = ref([])
const agentConfigs = ref([])
const ollamaModels = ref([])

const ollamaStatus = reactive({
  connected: false,
  version: ''
})

const ollamaConfig = reactive({
  base_url: 'http://localhost:11434',
  default_model: ''
})

const getAgentTypeText = (type) => {
  const typeMap = {
    collector: '信息收集Agent',
    matcher: '企业比对Agent',
    analyst: '投标论证Agent',
    generator: '标书制作Agent',
    reviewer: '标书审核Agent',
    tracker: '结果查询Agent',
    optimizer: '质量提升Agent',
    orchestrator: '协调器Agent'
  }
  return typeMap[type] || type
}

const formatSize = (bytes) => {
  if (!bytes) return '-'
  const gb = bytes / (1024 * 1024 * 1024)
  if (gb >= 1) return `${gb.toFixed(2)} GB`
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(2)} MB`
}

const formatModelName = (name) => {
  if (!name) return '-'
  return name.replace(/:\d+(\.\d+)?b/gi, '')
}

const formatModelSize = (name) => {
  if (!name) return '-'
  const match = name.match(/:(\d+(\.\d+)?)b/i)
  if (match) {
    const size = parseFloat(match[1])
    return size % 1 === 0 ? `${size}b` : `${size}b`
  }
  return name
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const toggleSort = () => {
  sortAscending.value = !sortAscending.value
}

const sortedOllamaModels = computed(() => {
  const models = [...ollamaModels.value]
  models.sort((a, b) => {
    const sizeA = a.size || 0
    const sizeB = b.size || 0
    return sortAscending.value ? sizeA - sizeB : sizeB - sizeA
  })
  return models
})

const fetchModels = async () => {
  try {
    const res = await modelApi.listModels()
    if (Array.isArray(res.data)) {
      allModels.value = res.data
    } else if (Array.isArray(res.data?.data)) {
      allModels.value = res.data.data
    } else if (Array.isArray(res.data?.results)) {
      allModels.value = res.data.results
    } else {
      allModels.value = []
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
}

const fetchAgentConfigs = async () => {
  try {
    const res = await modelApi.getAgentConfigs()
    if (Array.isArray(res.data)) {
      agentConfigs.value = res.data
    } else if (Array.isArray(res.data?.data)) {
      agentConfigs.value = res.data.data
    } else if (Array.isArray(res.data?.results)) {
      agentConfigs.value = res.data.results
    } else {
      agentConfigs.value = []
    }
  } catch (error) {
    console.error('获取Agent配置失败:', error)
    agentConfigs.value = []
  }
}

const checkOllamaStatus = async (url = null) => {
  checkingOllama.value = true
  try {
    const targetUrl = url || ollamaConfig.base_url
    const res = await modelApi.getOllamaModels(targetUrl)
    ollamaModels.value = res.data.models || []
    ollamaStatus.connected = true
    ollamaStatus.version = res.data.version || ''
    ElMessage.success(`投标精灵连接成功，发现 ${ollamaModels.value.length} 个模型`)
  } catch (error) {
    ollamaStatus.connected = false
    ollamaModels.value = []
    ElMessage.warning('投标精灵服务未启动，请确保投标精灵已启动')
  } finally {
    checkingOllama.value = false
  }
}

const fetchData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      fetchModels(),
      fetchAgentConfigs()
    ])
  } finally {
    refreshing.value = false
  }
}

const saveAgentConfigs = async () => {
  saving.value = true
  try {
    const configs = agentConfigs.value.map(config => ({
      agent_type: config.agent_type,
      chat_model_id: config.chat_model_id,
      temperature: config.temperature,
      max_tokens: config.max_tokens
    }))
    await modelApi.batchUpdateAgentConfigs(configs)
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const testModel = async (modelName) => {
  try {
    const res = await modelApi.testConnection(1, modelName)
    ElMessage.success(`测试成功: ${res.data.response || '连接正常'}`)
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

onMounted(() => {
  fetchData()
  checkOllamaStatus()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.ollama-card {
  border-radius: var(--radius-lg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-title {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-md);
}

.card-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.ollama-status {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-md) 0;

  .status-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);

    .label {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
    }
  }
}

.ollama-config {
  h4 {
    margin: var(--spacing-lg) 0 var(--spacing-md);
    font-weight: var(--font-weight-medium);
  }
}

.model-list {
  margin-top: var(--spacing-lg);

  h4 {
    margin-bottom: var(--spacing-md);
  }

  .model-size {
    margin-left: var(--spacing-sm);
    color: var(--color-text-secondary);
    font-size: var(--font-size-xs);
  }

  .sort-indicator {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    font-weight: normal;
  }
}
</style>

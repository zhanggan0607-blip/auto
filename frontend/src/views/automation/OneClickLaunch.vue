﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="one-click-launch">
    <div class="launch-container">
      <div class="launch-header">
        <h2 class="launch-title">一键启动投标自动化</h2>
        <p class="launch-subtitle">系统自动完成采集、匹配、投标全流程</p>
      </div>

      <el-row :gutter="24">
        <el-col :span="16">
          <el-card class="main-card">
            <template #header>
              <div class="card-header">
                <span>自动化控制台</span>
                <el-tag v-if="systemStatus.overall === 'healthy'" type="success" size="small">系统正常</el-tag>
                <el-tag v-else type="warning" size="small">需要初始化</el-tag>
              </div>
            </template>

            <div class="control-panel">
              <div class="enterprise-select" v-if="!selectedEnterprise">
                <h4>选择投标企业</h4>
                <el-select
                  v-model="enterpriseId"
                  placeholder="请选择企业"
                  filterable
                  @change="onEnterpriseChange"
                  style="width: 100%"
                  size="large"
                >
                  <el-option
                    v-for="ent in enterpriseList"
                    :key="ent.id"
                    :label="ent.name"
                    :value="ent.id"
                  />
                </el-select>
                <div class="quick-create">
                  <el-button text type="primary" @click="showQuickCreate = true">
                    <el-icon><Plus /></el-icon>
                    快速创建新企业
                  </el-button>
                </div>
              </div>

              <div class="selected-enterprise" v-else>
                <el-alert
                  :title="`已选择: ${selectedEnterprise.name}`"
                  type="success"
                  :closable="false"
                  show-icon
                />
                <div class="enterprise-actions">
                  <el-button text type="primary" @click="enterpriseId = null; selectedEnterprise = null">
                    重新选择
                  </el-button>
                </div>
              </div>

              <el-divider />

              <div class="workflow-options">
                <h4>自动化选项</h4>
                <el-form label-position="top" size="default">
                  <el-form-item label="执行模式">
                    <el-radio-group v-model="executeMode">
                      <el-radio value="quick">快速模式（立即执行一次）</el-radio>
                      <el-radio value="schedule">定时模式（每天自动执行）</el-radio>
                      <el-radio value="continuous">持续模式（持续监控）</el-radio>
                    </el-radio-group>
                  </el-form-item>

                  <el-form-item label="自动投标阈值" v-if="executeMode !== 'quick'">
                    <el-slider
                      v-model="autoBidThreshold"
                      :min="0"
                      :max="100"
                      :step="5"
                      show-input
                    />
                    <div class="form-tip">匹配度达到此阈值自动投标</div>
                  </el-form-item>

                  <el-form-item label="标书自动通过阈值">
                    <el-slider
                      v-model="autoDocumentThreshold"
                      :min="50"
                      :max="100"
                      :step="5"
                      show-input
                    />
                    <div class="form-tip">标书得分达到此阈值自动上传</div>
                  </el-form-item>

                  <el-form-item>
                    <el-checkbox v-model="autoUpload">达到阈值自动上传</el-checkbox>
                    <el-checkbox v-model="sendNotification">完成后发送通知</el-checkbox>
                  </el-form-item>
                </el-form>
              </div>

              <el-divider />

              <div class="start-button-area">
                <el-button
                  type="primary"
                  size="large"
                  :loading="isRunning"
                  :disabled="!canStart"
                  @click="handleStart"
                  class="start-button"
                >
                  <el-icon v-if="!isRunning"><VideoPlay /></el-icon>
                  {{ isRunning ? '流程执行中...' : '一键启动' }}
                </el-button>
                <el-button
                  v-if="isRunning"
                  type="danger"
                  size="large"
                  @click="handleStop"
                >
                  停止
                </el-button>
              </div>
            </div>
          </el-card>

          <el-card class="progress-card" v-if="isRunning || currentWorkflow">
            <template #header>
              <div class="card-header">
                <span>执行进度</span>
                <el-tag v-if="currentWorkflow" :type="getStatusType('workflow_status', 'workflow_status', currentWorkflow.status)" size="small">
                  {{ getStatusText(currentWorkflow.status) }}
                </el-tag>
              </div>
            </template>

            <div class="workflow-progress">
              <el-steps :active="currentStepIndex" align-center finish-status="success">
                <el-step title="资质比对" :description="stepDone.collecting ? '完成' : ''" />
                <el-step title="招标采集" :description="stepDone.matching ? '完成' : ''" />
                <el-step title="标书生成" :description="stepDone.generating ? '完成' : ''" />
                <el-step title="标书审核" :description="stepDone.reviewing ? '完成' : ''" />
                <el-step title="结果通知" :description="stepDone.notifying ? '完成' : ''" />
              </el-steps>

              <div class="progress-detail">
                <div class="progress-item" v-for="(item, key) in workflowSteps" :key="key">
                  <div class="step-header">
                    <el-icon
                      :class="['step-icon', { done: stepDone[key], active: currentStep === key && isRunning }]"
                    >
                      <Check v-if="stepDone[key]" />
                      <Loading v-else-if="currentStep === key && isRunning" />
                      <Document v-else />
                    </el-icon>
                    <span class="step-title">{{ item.title }}</span>
                    <el-tag v-if="stepDone[key]" type="success" size="small">完成</el-tag>
                    <el-tag v-else-if="currentStep === key && isRunning" type="primary" size="small">执行中</el-tag>
                  </div>
                  <div class="step-desc">{{ item.desc }}</div>
                  <div class="step-result" v-if="workflowResults[key]">
                    <el-tag :type="workflowResults[key].success ? 'success' : 'danger'" size="small">
                      {{ workflowResults[key].message }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="logs-card" v-if="executionLogs.length > 0">
            <template #header>
              <div class="card-header">
                <span>执行日志</span>
                <el-button text size="small" @click="executionLogs = []">清空</el-button>
              </div>
            </template>
            <div class="logs-container">
              <div
                v-for="(log, index) in executionLogs"
                :key="index"
                :class="['log-item', `log-${log.level}`]"
              >
                <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="llm-config-card">
            <template #header>
              <div class="card-header">
                <span>大模型配置</span>
                <el-button text size="small" @click="fetchLLMConfig">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>

            <div class="llm-config-content">
              <el-form label-position="top" size="default">
                <el-form-item label="AI模型">
                  <el-select
                    v-model="llmConfig.provider_id"
                    placeholder="选择模型提供商"
                    @change="onProviderChange"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="p in llmProviders"
                      :key="p.id"
                      :label="p.name"
                      :value="p.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="模型版本" v-if="llmConfig.provider_id">
                  <el-select
                    v-model="llmConfig.model_id"
                    placeholder="选择模型"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="m in availableModels"
                      :key="m.id"
                      :label="m.name"
                      :value="m.id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="温度参数" v-if="llmConfig.model_id">
                  <el-slider
                    v-model="llmConfig.temperature"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    show-input
                  />
                  <div class="form-tip">较低值更确定性，较高值更有创造性</div>
                </el-form-item>

                <el-form-item label="Agent配置" v-if="llmConfig.model_id">
                  <el-select
                    v-model="llmConfig.agent_type"
                    placeholder="选择Agent类型"
                    style="width: 100%"
                  >
                    <el-option label="智能采集Agent" value="collector" />
                    <el-option label="标书生成Agent" value="generator" />
                    <el-option label="标书审核Agent" value="reviewer" />
                    <el-option label="决策Agent" value="decision" />
                  </el-select>
                </el-form-item>

                <div class="llm-actions">
                  <el-button
                    type="primary"
                    size="small"
                    @click="handleTestConnection"
                    :loading="testingConnection"
                  >
                    测试连接
                  </el-button>
                  <el-button
                    type="success"
                    size="small"
                    @click="handleSaveLLMConfig"
                    :loading="savingLLM"
                  >
                    保存配置
                  </el-button>
                </div>
              </el-form>

              <div class="llm-status" v-if="llmTestResult">
                <el-alert
                  :title="llmTestResult.message"
                  :type="llmTestResult.success ? 'success' : 'error'"
                  show-icon
                />
              </div>
            </div>
          </el-card>

          <el-card class="system-card">
            <template #header>
              <div class="card-header">
                <span>系统状态</span>
                <el-button text size="small" @click="checkSystemHealth">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>

            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="数据库">
                <el-tag :type="systemStatus.database === 'ok' ? 'success' : 'danger'" size="small">
                  {{ systemStatus.database === 'ok' ? '正常' : systemStatus.database }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="缓存服务">
                <el-tag :type="systemStatus.cache === 'ok' ? 'success' : 'danger'" size="small">
                  {{ systemStatus.cache === 'ok' ? '正常' : systemStatus.cache }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="向量库">
                <el-tag :type="systemStatus.vector_db === 'ok' ? 'success' : 'danger'" size="small">
                  {{ systemStatus.vector_db === 'ok' ? '正常' : systemStatus.vector_db }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="LLM服务">
                <el-tag :type="systemStatus.llm_service === 'ok' ? 'success' : 'warning'" size="small">
                  {{ systemStatus.llm_service || '未配置' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="钉钉通知">
                <el-tag :type="systemStatus.dingtalk === 'ok' ? 'success' : 'warning'" size="small">
                  {{ systemStatus.dingtalk || '未配置' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <el-card class="auto-fix-card">
            <template #header>
              <div class="card-header">
                <span>自动修复</span>
                <el-switch v-model="autoFixEnabled" />
              </div>
            </template>
            <div class="auto-fix-content">
              <p class="fix-description">
                开启后，系统检测到错误时将自动尝试修复：
              </p>
              <ul class="fix-list">
                <li>采集失败自动切换IP</li>
                <li>解析失败自动降级处理</li>
                <li>标书不达标自动优化</li>
                <li>超时自动重试</li>
              </ul>
              <div class="fix-stats" v-if="fixRecords.length > 0">
                <el-divider>修复记录</el-divider>
                <div v-for="record in fixRecords.slice(-3)" :key="record.id" class="fix-record">
                  <span class="fix-time">{{ formatDateTime(record.time) }}</span>
                  <span class="fix-result">{{ record.result }}</span>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="error-diagnosis-card">
            <template #header>
              <div class="card-header">
                <span>错误诊断</span>
                <el-button text size="small" @click="fetchErrorStatistics">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            <div class="error-diagnosis-content">
              <el-row :gutter="12" class="error-stats-row">
                <el-col :span="8">
                  <div class="stat-box">
                    <div class="stat-value">{{ errorStats.total_failures || 0 }}</div>
                    <div class="stat-label">总失败</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <div class="stat-value">{{ errorStats.solved || 0 }}</div>
                    <div class="stat-label">已解决</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="stat-box">
                    <div class="stat-value">{{ errorStats.solve_rate || 0 }}%</div>
                    <div class="stat-label">解决率</div>
                  </div>
                </el-col>
              </el-row>

              <el-divider content-position="left">高频错误</el-divider>
              <div class="frequent-errors" v-if="frequentErrors.length > 0">
                <div v-for="(err, idx) in frequentErrors.slice(0, 3)" :key="idx" class="error-item">
                  <div class="error-header">
                    <el-tag size="small" :type="getErrorTypeTag(err.error_type)">
                      {{ err.error_type }}
                    </el-tag>
                    <span class="error-count">{{ err.total_count }}次</span>
                  </div>
                  <div class="error-cause">{{ err.root_cause }}</div>
                  <div class="error-solution" v-if="err.common_solution">
                    <el-icon><InfoFilled /></el-icon>
                    {{ err.common_solution }}
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无错误记录" :image-size="40" />

              <el-divider content-position="left">最近失败</el-divider>
              <div class="recent-failures" v-if="recentFailures.length > 0">
                <div v-for="fail in recentFailures.slice(0, 3)" :key="fail.id" class="failure-item">
                  <div class="failure-info">
                    <el-tag size="small" type="danger">{{ fail.stage }}</el-tag>
                    <span class="failure-time">{{ formatDateTime(fail.created_at) }}</span>
                  </div>
                  <div class="failure-msg">{{ fail.error_message }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无失败记录" :image-size="40" />
            </div>
          </el-card>

          <el-card class="health-card">
            <template #header>
              <div class="card-header">
                <span>系统健康</span>
                <el-tag :type="healthStatus.tagType" size="small">{{ healthStatus.text }}</el-tag>
              </div>
            </template>
            <div class="health-content">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="数据库">
                  <el-icon v-if="systemHealth.database"><Check color="#16A34A"/></el-icon>
                  <el-icon v-else><Close color="#DC2626"/></el-icon>
                </el-descriptions-item>
                <el-descriptions-item label="缓存">
                  <el-icon v-if="systemHealth.cache"><Check color="#16A34A"/></el-icon>
                  <el-icon v-else><Close color="#DC2626"/></el-icon>
                </el-descriptions-item>
                <el-descriptions-item label="向量库">
                  <el-icon v-if="systemHealth.vector_db"><Check color="#16A34A"/></el-icon>
                  <el-icon v-else><Close color="#DC2626"/></el-icon>
                </el-descriptions-item>
                <el-descriptions-item label="LLM服务">
                  <el-icon v-if="systemHealth.llm"><Check color="#16A34A"/></el-icon>
                  <el-icon v-else><Close color="#DC2626"/></el-icon>
                </el-descriptions-item>
              </el-descriptions>
              <div class="health-issues" v-if="healthIssues.length > 0">
                <el-divider>问题</el-divider>
                <div v-for="(issue, idx) in healthIssues" :key="idx" class="health-issue">
                  <el-icon><Warning /></el-icon>
                  {{ issue }}
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="optimization-card">
            <template #header>
              <div class="card-header">
                <span>优化建议</span>
                <el-button text size="small" @click="fetchOptimizationSuggestions">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="optimization-content">
              <div v-if="optimizationSuggestions.length > 0">
                <div v-for="(sug, idx) in optimizationSuggestions.slice(0, 5)" :key="idx" class="suggestion-item">
                  <div class="suggestion-header">
                    <el-tag size="small" :type="sug.priority === 'high' ? 'danger' : 'warning'">
                      {{ sug.category }}
                    </el-tag>
                    <span class="suggestion-issue">{{ sug.issue }}</span>
                  </div>
                  <div class="suggestion-body">
                    <div class="suggestion-change">
                      <span class="current">{{ sug.current_value }}</span>
                      <el-icon><Right /></el-icon>
                      <span class="suggested">{{ sug.suggested_value }}</span>
                    </div>
                    <div class="suggestion-reason">{{ sug.reason }}</div>
                  </div>
                </div>
              </div>
              <el-empty v-else description="暂无优化建议" :image-size="40" />
            </div>
          </el-card>

          <el-card class="history-card">
            <template #header>
              <span>执行历史</span>
            </template>
            <div class="history-list">
              <div v-for="item in executionHistory" :key="item.id" class="history-item">
                <div class="history-info">
                  <span class="history-enterprise">{{ item.enterprise_name }}</span>
                  <el-tag :type="getStatusType('workflow_status', 'workflow_status', item.status)" size="small">
                    {{ getStatusText(item.status) }}
                  </el-tag>
                </div>
                <div class="history-meta">
                  <span>{{ formatDateTime(item.created_at) }}</span>
                  <span v-if="item.tender_count">采集 {{ item.tender_count }} 条</span>
                </div>
              </div>
              <el-empty v-if="executionHistory.length === 0" description="暂无执行历史" :image-size="60" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="showQuickCreate" title="快速创建企业" width="500px">
      <el-form :model="enterpriseForm" label-width="100px">
        <el-form-item label="企业名称" required>
          <el-input v-model="enterpriseForm.name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="统一信用代码">
          <el-input v-model="enterpriseForm.credit_code" placeholder="请输入统一社会信用代码" />
        </el-form-item>
        <el-form-item label="法人代表">
          <el-input v-model="enterpriseForm.legal_person" placeholder="请输入法人代表" />
        </el-form-item>
        <el-form-item label="经营范围">
          <el-input v-model="enterpriseForm.business_scope" type="textarea" placeholder="请输入经营范围" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuickCreate = false">取消</el-button>
        <el-button type="primary" @click="handleQuickCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showWorkflowDetail" title="工作流详情" width="700px">
      <el-descriptions :column="2" border v-if="currentWorkflow">
        <el-descriptions-item label="工作流ID">{{ currentWorkflow.workflow_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType('workflow_status', 'workflow_status', currentWorkflow.status)">
            {{ getStatusText(currentWorkflow.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前阶段">{{ getCurrentTaskName() }}</el-descriptions-item>
        <el-descriptions-item label="模拟得分">
          <span :class="getScoreClass(currentWorkflow.bid_score)">
            {{ currentWorkflow.bid_score || '-' }}分
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(currentWorkflow.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatDateTime(currentWorkflow.completed_at) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showWorkflowDetail = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Plus, Check, Loading, Document, Refresh, InfoFilled, Warning, Close, Right } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { isSuccess, parseListResponse } from '@/utils/response-parser'
import { useFormDraft } from '@/composables/useFormDraft'
import { formatDateTime } from '@/utils/date'
import { getStatusType } from '@/store/constants'

const enterpriseId = ref(null)
const selectedEnterprise = ref(null)
const enterpriseList = ref([])
const showQuickCreate = ref(false)
const creating = ref(false)
const autoFixEnabled = ref(true)

const enterpriseForm = reactive({
  name: '',
  credit_code: '',
  legal_person: '',
  business_scope: ''
})

const executeMode = ref('quick')
const autoBidThreshold = ref(60)
const autoDocumentThreshold = ref(90)
const autoUpload = ref(false)
const sendNotification = ref(true)

const isRunning = ref(false)
const currentWorkflow = ref(null)
const currentStep = ref('')
const workflowSteps = {
  collecting: { title: '资质比对', desc: '分析企业资质与招标项目匹配度' },
  matching: { title: '招标采集', desc: '从各网站采集招标公告' },
  generating: { title: '标书生成', desc: '根据招标文件生成投标标书' },
  reviewing: { title: '标书审核', desc: '审核标书内容完整性和合规性' },
  notifying: { title: '结果通知', desc: '发送中标/未中标通知' }
}
const stepDone = reactive({
  collecting: false,
  matching: false,
  generating: false,
  reviewing: false,
  notifying: false
})
const workflowResults = reactive({})
const executionLogs = ref([])

const systemStatus = reactive({
  overall: 'unknown',
  database: 'checking',
  cache: 'checking',
  vector_db: 'checking',
  llm_service: null,
  dingtalk: null
})

const systemHealth = reactive({
  database: false,
  cache: false,
  vector_db: false,
  llm: false
})

const fixRecords = ref([])
const executionHistory = ref([])

const errorStats = reactive({
  total_failures: 0,
  solved: 0,
  unsolved: 0,
  solve_rate: 0
})
const frequentErrors = ref([])
const recentFailures = ref([])

const healthStatus = computed(() => {
  const services = systemHealth
  const healthyCount = [services.database, services.cache, services.vector_db, services.llm].filter(Boolean).length
  if (healthyCount === 4) return { text: '健康', tagType: 'success' }
  if (healthyCount >= 2) return { text: '降级', tagType: 'warning' }
  return { text: '异常', tagType: 'danger' }
})
const healthIssues = ref([])
const optimizationSuggestions = ref([])

const llmProviders = ref([])
const availableModels = ref([])
const llmConfig = reactive({
  provider_id: null,
  model_id: null,
  temperature: 0.7,
  agent_type: 'collector'
})
const llmTestResult = ref(null)
const testingConnection = ref(false)
const savingLLM = ref(false)

const { clearDraft: clearEnterpriseDraft } = useFormDraft(enterpriseForm, {
  key: 'automation:launch:enterprise',
  promptMessage: '检测到您有未保存的企业信息，是否恢复？'
})

const { clearDraft: clearLLMDraft } = useFormDraft(llmConfig, {
  key: 'automation:launch:llm',
  promptOnRestore: false
})

const canStart = computed(() => {
  return selectedEnterprise.value && !isRunning.value
})

const currentStepIndex = computed(() => {
  const stepOrder = ['collecting', 'matching', 'generating', 'reviewing', 'notifying']
  const currentIdx = stepOrder.indexOf(currentStep.value)
  if (currentIdx >= 0) return currentIdx
  for (let i = stepOrder.length - 1; i >= 0; i--) {
    if (stepDone[stepOrder[i]]) return i + 1
  }
  return 0
})

const fetchEnterprises = async () => {
  try {
    const res = await request.get('/v1/enterprise/enterprises/')
    const { list } = parseListResponse(res)
    enterpriseList.value = list
  } catch (error) {
    console.error('获取企业列表失败:', error)
  }
}

const onEnterpriseChange = (val) => {
  selectedEnterprise.value = enterpriseList.value.find(e => e.id === val)
}

const fetchLLMConfig = async () => {
  try {
    const [providersRes, agentRes] = await Promise.all([
      request.get('/v1/openclaw/llm-providers/'),
      request.get('/v1/openclaw/agent-model-configs/')
    ])

    if (isSuccess(providersRes)) {
      llmProviders.value = providersRes.data || []
    }

    const { list: agents } = parseListResponse(agentRes)
    if (agents && agents.length > 0) {
      const agent = agents[0]
      llmConfig.agent_type = agent.agent_type
      llmConfig.temperature = agent.temperature || 0.7
      llmConfig.model_id = agent.chat_model || agent.reasoning_model
    }

    const defaultProviderRes = await request.get('/v1/openclaw/llm-providers/default/')
    if (isSuccess(defaultProviderRes)) {
      const provider = defaultProviderRes.data
      if (provider) {
        llmConfig.provider_id = provider.id
        await fetchModelsByProvider(provider.id)
      }
    }
  } catch (error) {
    console.error('获取LLM配置失败:', error)
  }
}

const onProviderChange = async (providerId) => {
  llmConfig.model_id = null
  availableModels.value = []
  await fetchModelsByProvider(providerId)
}

const fetchModelsByProvider = async (providerId) => {
  if (!providerId) return
  try {
    const res = await request.get(`/v1/openclaw/llm-providers/${providerId}/models/`)
    if (isSuccess(res)) {
      availableModels.value = res.data || []
    }
  } catch (error) {
    console.error('获取模型列表失败:', error)
  }
}

const handleTestConnection = async () => {
  if (!llmConfig.provider_id || !llmConfig.model_id) {
    ElMessage.warning('请先选择提供商和模型')
    return
  }

  testingConnection.value = true
  llmTestResult.value = null

  try {
    const res = await request.post('/v1/openclaw/llm-providers/test_connection/', {
      provider_id: llmConfig.provider_id,
      model_id: llmConfig.model_id
    })

    if (isSuccess(res)) {
      llmTestResult.value = {
        success: true,
        message: `连接成功: ${res.data?.response || '模型响应正常'}`
      }
      ElMessage.success('连接测试成功')
    } else {
      llmTestResult.value = {
        success: false,
        message: res.message || '连接失败'
      }
    }
  } catch (error) {
    llmTestResult.value = {
      success: false,
      message: error.response?.data?.message || '连接测试失败'
    }
  } finally {
    testingConnection.value = false
  }
}

const handleSaveLLMConfig = async () => {
  savingLLM.value = true
  try {
    const res = await request.post('/v1/openclaw/agent-model-configs/batch_update/', {
      configs: [{
        agent_type: llmConfig.agent_type,
        chat_model: llmConfig.model_id,
        temperature: llmConfig.temperature,
        is_active: true
      }]
    })

    if (isSuccess(res)) {
      ElMessage.success('LLM配置已保存')
      clearLLMDraft()
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingLLM.value = false
  }
}

const handleQuickCreate = async () => {
  if (!enterpriseForm.name) {
    ElMessage.warning('请输入企业名称')
    return
  }
  creating.value = true
  try {
    const res = await request.post('/v1/openclaw/one-click/enterprise/setup/', enterpriseForm)
    if (isSuccess(res)) {
      ElMessage.success('企业创建成功')
      clearEnterpriseDraft()
      showQuickCreate.value = false
      await fetchEnterprises()
      enterpriseId.value = res.data.enterprise_id
      selectedEnterprise.value = enterpriseList.value.find(e => e.id === res.data.enterprise_id)
    }
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

const checkSystemHealth = async () => {
  try {
    const res = await request.get('/v1/openclaw/scheduler/health/')
    if (isSuccess(res)) {
      Object.assign(systemStatus, res.data)
      systemStatus.overall = res.data.overall || 'healthy'
    }
  } catch (error) {
    console.error('检查系统状态失败:', error)
    systemStatus.overall = 'error'
  }
}

const fetchErrorStatistics = async () => {
  try {
    const res = await request.get('/v1/system/health/')
    if (isSuccess(res)) {
      const data = res.data || {}
      systemHealth.database = data.services?.database || false
      systemHealth.cache = data.services?.cache || false
      systemHealth.vector_db = data.services?.vector_db || false
      systemHealth.llm = data.services?.llm_service || false
      healthIssues.value = data.issues || []
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  }
}

const fetchOptimizationSuggestions = async () => {
}

const getErrorTypeTag = (errorType) => {
  const typeMap = {
    'network_error': 'warning',
    'llm_error': 'danger',
    'parse_error': 'info',
    'data_error': 'warning',
    'crawler_error': 'danger',
    'timeout_error': 'warning'
  }
  return typeMap[errorType] || 'info'
}

const handleStart = async () => {
  if (!selectedEnterprise.value) {
    ElMessage.warning('请先选择投标企业')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要为「${selectedEnterprise.value.name}」启动自动化投标流程吗？`,
      '确认启动',
      { type: 'info' }
    )

    const config = {
      auto_bid_threshold: autoBidThreshold.value,
      auto_document_threshold: autoDocumentThreshold.value,
      notification_enabled: sendNotification.value,
      auto_upload: autoUpload.value
    }

    const res = await request.post('/v1/openclaw/one-click/start/', {
      enterprise_id: enterpriseId.value,
      config
    })

    if (isSuccess(res)) {
      ElMessage.success('自动化流程已启动')
      isRunning.value = true
      currentWorkflow.value = res.data
      currentStep.value = 'collecting'
      addLog('info', `启动自动化流程，任务ID: ${res.data.task_id}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('启动失败')
      addLog('error', `启动失败: ${error.message}`)
    }
  }
}

const handleStop = async () => {
  try {
    await ElMessageBox.confirm('确定要停止当前流程吗？', '确认停止', { type: 'warning' })
    await request.post('/v1/openclaw/automation/resume/', {
      workflow_id: currentWorkflow.value.workflow_id,
      action: 'cancel'
    })
    ElMessage.success('流程已停止')
    isRunning.value = false
    addLog('info', '流程被用户停止')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败')
    }
  }
}

const fetchWorkflowStatus = async () => {
  if (!currentWorkflow.value?.workflow_id) return

  try {
    const res = await request.get(`/v1/openclaw/automation/status/?workflow_id=${currentWorkflow.value.workflow_id}`)
    if (isSuccess(res)) {
      const data = res.data
      currentWorkflow.value = { ...currentWorkflow.value, ...data }

      if (data.current_task) {
        currentStep.value = data.current_task
      }

      if (data.logs) {
        data.logs.forEach(log => {
          if (!executionLogs.value.find(l => l.timestamp === log.timestamp && l.message === log.message)) {
            addLog('info', log.message)
          }
        })
      }

      if (data.status === 'completed' || data.status === 'failed') {
        isRunning.value = false
        if (data.status === 'completed') {
          ElMessage.success('自动化流程已完成')
          addLog('success', '流程执行完成')
        }
      }
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const fetchExecutionHistory = async () => {
  try {
    const res = await request.get('/v1/openclaw/one-click/tasks/')
    if (isSuccess(res)) {
      executionHistory.value = res.data || []
    }
  } catch (error) {
    console.error('获取历史失败:', error)
  }
}

const addLog = (level, message) => {
  executionLogs.value.push({
    level,
    message,
    timestamp: new Date().toISOString()
  })
}

const getStatusText = (status) => {
  const texts = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    waiting_review: '待审核',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getCurrentTaskName = () => {
  const names = {
    task_1_qualification_match: '资质比对',
    task_2_download_tender: '文件下载',
    task_3_parse_tender: '文件解析',
    task_4_generate_bid: '标书生成',
    task_5_review_bid: '标书审核',
    task_6_upload_bid: '标书上传',
    task_7_optimize_bid: '标书优化',
    task_8_track_project: '项目跟踪',
    task_9_notify_result: '结果通知'
  }
  return names[currentWorkflow.value?.current_task] || currentStep.value || '-'
}

const getScoreClass = (score) => {
  if (!score) return ''
  if (score >= 90) return 'score-high'
  if (score >= 70) return 'score-medium'
  return 'score-low'
}

let statusInterval = null

onMounted(() => {
  checkSystemHealth()
  fetchEnterprises()
  fetchExecutionHistory()
  fetchLLMConfig()
  fetchErrorStatistics()
  fetchOptimizationSuggestions()
  statusInterval = setInterval(fetchWorkflowStatus, 5000)
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style lang="scss" scoped>
.one-click-launch {
  padding: 20px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 60px);
}

.launch-container {
  max-width: 1400px;
  margin: 0 auto;
}

.launch-header {
  text-align: center;
  margin-bottom: 24px;

  .launch-title {
    font-size: 28px;
    font-weight: 600;
    color: #1E293B;
    margin-bottom: 8px;
  }

  .launch-subtitle {
    font-size: 14px;
    color: #64748B;
  }
}

.main-card,
.progress-card,
.logs-card,
.system-card,
.auto-fix-card,
.history-card,
.llm-config-card,
.error-diagnosis-card,
.health-card,
.optimization-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-panel {
  padding: 10px 0;
}

.enterprise-select {
  h4 {
    margin-bottom: 12px;
    color: #1E293B;
  }
}

.quick-create {
  margin-top: 12px;
}

.selected-enterprise {
  .enterprise-actions {
    margin-top: 12px;
  }
}

.workflow-options {
  h4 {
    margin-bottom: 16px;
    color: #1E293B;
  }
}

.form-tip {
  color: #64748B;
  font-size: 12px;
  margin-top: 4px;
}

.start-button-area {
  text-align: center;
  padding: 20px 0;

  .start-button {
    width: 200px;
    height: 50px;
    font-size: 18px;
  }
}

.workflow-progress {
  padding: 20px 0;

  .progress-detail {
    margin-top: 30px;
  }

  .progress-item {
    padding: 12px 0;
    border-bottom: 1px solid #E2E8F0;

    &:last-child {
      border-bottom: none;
    }

    .step-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      .step-icon {
        font-size: 18px;

        &.done {
          color: #16A34A;
        }

        &.active {
          color: #3B82F6;
          animation: pulse 1s infinite;
        }
      }

      .step-title {
        font-weight: 500;
        color: #1E293B;
      }
    }

    .step-desc {
      color: #64748B;
      font-size: 13px;
      margin-left: 26px;
    }

    .step-result {
      margin-top: 8px;
      margin-left: 26px;
    }
  }
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;

  .log-item {
    padding: 4px 8px;
    border-radius: 4px;
    margin-bottom: 4px;

    &.log-info {
      background-color: #f4f4f5;
    }

    &.log-success {
      background-color: #F0FDF4;
      color: #16A34A;
    }

    &.log-error {
      background-color: #fef0f0;
      color: #DC2626;
    }

    .log-time {
      color: #64748B;
      margin-right: 8px;
    }
  }
}

.llm-config-content {
  .llm-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
  }

  .llm-status {
    margin-top: 16px;
  }
}

.error-stats-row {
  .stat-box {
    text-align: center;
    padding: 16px;
    background-color: #F1F5F9;
    border-radius: 8px;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: #1E293B;
    }

    .stat-label {
      font-size: 12px;
      color: #64748B;
      margin-top: 4px;
    }
  }
}

.frequent-errors,
.recent-failures {
  .error-item,
  .failure-item {
    padding: 12px;
    background-color: #F1F5F9;
    border-radius: 8px;
    margin-bottom: 8px;

    .error-header,
    .failure-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .error-cause,
    .failure-msg {
      color: #334155;
      font-size: 13px;
    }
  }
}

.health-content {
  .health-issues {
    margin-top: 16px;

    .health-issue {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px;
      background-color: #fef0f0;
      border-radius: 4px;
      color: #DC2626;
      margin-bottom: 8px;
    }
  }
}

.optimization-content {
  .suggestion-item {
    padding: 12px;
    background-color: #F1F5F9;
    border-radius: 8px;
    margin-bottom: 12px;

    .suggestion-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .suggestion-body {
      .suggestion-change {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;

        .current {
          color: #64748B;
          text-decoration: line-through;
        }

        .suggested {
          color: #16A34A;
          font-weight: 500;
        }
      }

      .suggestion-reason {
        color: #334155;
        font-size: 13px;
      }
    }
  }
}

.history-list {
  .history-item {
    padding: 12px;
    border-bottom: 1px solid #E2E8F0;

    &:last-child {
      border-bottom: none;
    }

    .history-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .history-meta {
      display: flex;
      gap: 16px;
      color: #64748B;
      font-size: 12px;
    }
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

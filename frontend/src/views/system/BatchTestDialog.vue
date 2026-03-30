<template>
  <div class="batch-test-dialog">
    <el-dialog
      v-model="dialogVisible"
      title="批量测试网站模板"
      width="900px"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <div v-if="!testStarted" class="start-section">
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <span>将测试所有<span class="highlight">{{ activeTemplateCount }}</span>个已启用的网站模板</span>
          </template>
          <template #default>
            <p>每个模板将执行实际采集测试，成功获取数据视为通过，未获取数据或发生错误将记录详细报告。</p>
            <p class="warning-text">测试过程可能需要几分钟时间，请耐心等待。</p>
          </template>
        </el-alert>
        <div class="action-bar">
          <el-button type="primary" size="large" @click="startBatchTest" :loading="starting">
            <el-icon v-if="!starting"><VideoPlay /></el-icon>
            开始批量测试
          </el-button>
        </div>
      </div>

      <div v-else class="progress-section">
        <div class="progress-header">
          <div class="progress-stats">
            <div class="stat-item">
              <span class="stat-label">总进度</span>
              <span class="stat-value">{{ currentProgress }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">成功</span>
              <span class="stat-value success">{{ successCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">失败</span>
              <span class="stat-value danger">{{ failedCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">警告</span>
              <span class="stat-value warning">{{ warningCount }}</span>
            </div>
          </div>
          <el-progress
            :percentage="currentProgress"
            :status="progressStatus"
            :stroke-width="10"
            class="main-progress"
          />
        </div>

        <el-divider content-position="left">
          <span class="steps-title">测试步骤</span>
          <span class="steps-count">({{ completedSteps }}/{{ totalSteps }})</span>
        </el-divider>

        <div class="steps-list">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{
              'step-active': step.status === 'active',
              'step-completed': step.status === 'completed',
              'step-error': step.status === 'error',
              'step-warning': step.status === 'warning'
            }"
          >
            <div class="step-indicator">
              <div class="step-circle">
                <el-icon v-if="step.status === 'completed'" class="step-icon"><CircleCheck /></el-icon>
                <el-icon v-else-if="step.status === 'error'" class="step-icon"><CircleClose /></el-icon>
                <el-icon v-else-if="step.status === 'warning'" class="step-icon"><Warning /></el-icon>
                <span v-else-if="step.status === 'active'" class="step-spinner">
                  <el-icon class="is-loading"><Loading /></el-icon>
                </span>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <div class="step-line" v-if="index < steps.length - 1"></div>
            </div>
            <div class="step-content">
              <div class="step-header">
                <span class="step-title">{{ step.title || `模板 ${index + 1}` }}</span>
                <el-tag
                  v-if="step.status === 'completed'"
                  type="success"
                  size="small"
                  class="status-tag"
                >
                  成功
                </el-tag>
                <el-tag
                  v-else-if="step.status === 'error'"
                  type="danger"
                  size="small"
                  class="status-tag"
                >
                  失败
                </el-tag>
                <el-tag
                  v-else-if="step.status === 'warning'"
                  type="warning"
                  size="small"
                  class="status-tag"
                >
                  警告
                </el-tag>
                <el-tag
                  v-else-if="step.status === 'active'"
                  type="primary"
                  size="small"
                  class="status-tag"
                >
                  测试中
                </el-tag>
              </div>
              <div class="step-description">
                {{ step.description || getStepDefaultMessage(step.status) }}
              </div>
              <div class="step-error-detail" v-if="step.status === 'error' && step.error">
                <el-icon><WarningFilled /></el-icon>
                {{ step.error }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="testCompleted" class="summary-section">
          <el-divider content-position="left">测试报告摘要</el-divider>

          <el-row :gutter="20" class="summary-stats">
            <el-col :span="6">
              <el-statistic title="测试模板总数" :value="summary.total_templates" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="成功率" :value="summary.success_rate" suffix="%" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="失败数量" :value="summary.failed_count" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="警告数量" :value="summary.warning_count" />
            </el-col>
          </el-row>

          <div v-if="summary.failed_templates && summary.failed_templates.length > 0" class="issues-section">
            <h4 class="issues-title">
              <el-icon color="#f56c6c"><CircleClose /></el-icon>
              发现的问题 ({{ summary.failed_templates.length }})
            </h4>
            <div class="issues-list">
              <el-card
                v-for="item in summary.failed_templates"
                :key="item.template_id"
                class="issue-card"
              >
                <template #header>
                  <div class="issue-header">
                    <span class="issue-name">{{ item.template_name }}</span>
                    <el-tag type="danger" size="small">{{ item.error_type }}</el-tag>
                  </div>
                </template>
                <div class="issue-content">
                  <div class="issue-row">
                    <span class="issue-label">错误信息：</span>
                    <span class="issue-value error">{{ item.error_message }}</span>
                  </div>
                  <div class="issue-row">
                    <span class="issue-label">根本原因：</span>
                    <span class="issue-value">{{ item.root_cause }}</span>
                  </div>
                  <div class="issue-row">
                    <span class="issue-label">修复建议：</span>
                    <ul class="recommendations">
                      <li v-for="(rec, idx) in item.recommendations" :key="idx">{{ rec }}</li>
                    </ul>
                  </div>
                </div>
              </el-card>
            </div>
          </div>

          <div v-if="summary.warning_templates && summary.warning_templates.length > 0" class="warnings-section">
            <h4 class="warnings-title">
              <el-icon color="#e6a23c"><Warning /></el-icon>
              需要关注的模板 ({{ summary.warning_templates.length }})
            </h4>
            <div class="warnings-list">
              <el-card
                v-for="item in summary.warning_templates"
                :key="item.template_id"
                class="warning-card"
              >
                <template #header>
                  <div class="warning-header">
                    <span class="warning-name">{{ item.template_name }}</span>
                    <el-tag type="warning" size="small">无数据</el-tag>
                  </div>
                </template>
                <div class="warning-content">
                  <div class="issue-row">
                    <span class="issue-label">详情：</span>
                    <span class="issue-value">{{ item.error_message }}</span>
                  </div>
                  <div class="issue-row">
                    <span class="issue-label">建议：</span>
                    <ul class="recommendations">
                      <li v-for="(rec, idx) in item.recommendations" :key="idx">{{ rec }}</li>
                    </ul>
                  </div>
                </div>
              </el-card>
            </div>
          </div>

          <div class="success-section" v-if="summary.success_templates && summary.success_templates.length > 0">
            <h4 class="success-title">
              <el-icon color="#67c23a"><CircleCheck /></el-icon>
              测试成功的模板 ({{ summary.success_templates.length }})
            </h4>
            <el-table :data="summary.success_templates" size="small" stripe>
              <el-table-column prop="template_name" label="模板名称" />
              <el-table-column prop="template_code" label="模板代码" width="150" />
              <el-table-column prop="data_count" label="获取数据" width="100" align="center" />
              <el-table-column prop="duration" label="耗时(秒)" width="100" align="center">
                <template #default="{ row }">
                  {{ row.duration ? row.duration.toFixed(2) : '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">
            {{ testCompleted ? '关闭' : '取消' }}
          </el-button>
          <el-button
            v-if="testStarted && !testCompleted"
            type="warning"
            @click="handleCancel"
            :loading="cancelling"
          >
            取消测试
          </el-button>
          <el-button
            v-if="testCompleted && (summary.failed_count > 0 || summary.warning_count > 0)"
            type="primary"
            @click="exportReport"
          >
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import {
  VideoPlay,
  CircleCheck,
  CircleClose,
  Warning,
  WarningFilled,
  Loading,
  Download
} from '@element-plus/icons-vue'
import { crawlerApi } from '@/api/crawler'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  activeTemplateCount: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue', 'complete'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const starting = ref(false)
const testStarted = ref(false)
const testCompleted = ref(false)
const cancelling = ref(false)

const taskId = ref(null)
const pollingTimer = ref(null)
const pollingInterval = ref(2000)

const currentProgress = ref(0)
const successCount = ref(0)
const failedCount = ref(0)
const warningCount = ref(0)
const totalSteps = ref(0)
const completedSteps = ref(0)

const steps = ref([])
const summary = ref({})
const taskStatus = ref(null)

const progressStatus = computed(() => {
  if (testCompleted.value) {
    if (failedCount.value > 0) return 'exception'
    if (warningCount.value > 0) return 'warning'
    return 'success'
  }
  return undefined
})

const getStepDefaultMessage = (status) => {
  switch (status) {
    case 'waiting': return '等待测试'
    case 'active': return '测试中...'
    case 'completed': return '测试完成'
    case 'error': return '测试失败'
    case 'warning': return '需要关注'
    default: return ''
  }
}

const startBatchTest = async () => {
  starting.value = true
  try {
    const res = await crawlerApi.batchTestTemplates()
    if (res.code === 0 || res.code === 200) {
      taskId.value = res.data.task_id
      totalSteps.value = res.data.total_templates + 1
      testStarted.value = true
      testCompleted.value = false
      startPolling()
    } else {
      ElMessage.error(res.message || '启动批量测试失败')
    }
  } catch (error) {
    console.error('启动批量测试失败:', error)
    ElMessage.error('启动批量测试失败: ' + error.message)
  } finally {
    starting.value = false
  }
}

const startPolling = () => {
  stopPolling()
  fetchProgress()
  pollingTimer.value = setInterval(fetchProgress, pollingInterval.value)
}

const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

const fetchProgress = async () => {
  if (!taskId.value) return

  try {
    const res = await crawlerApi.getBatchTestProgress(taskId.value)
    if (res.code === 0 || res.code === 200) {
      const data = res.data
      taskStatus.value = data.status

      currentProgress.value = Math.round(data.progress || 0)
      completedSteps.value = data.steps ? data.steps.filter(s => s.status === 'completed' || s.status === 'error' || s.status === 'warning').length : 0

      if (data.steps && data.steps.length > 0) {
        steps.value = data.steps

        let success = 0
        let failed = 0
        let warning = 0
        data.steps.forEach(step => {
          if (step.status === 'completed') success++
          else if (step.status === 'error') failed++
          else if (step.status === 'warning') warning++
        })
        successCount.value = success
        failedCount.value = failed
        warningCount.value = warning
      }

      if (data.result) {
        summary.value = data.result
      }

      if (data.status === 'completed' || data.status === 'failed') {
        testCompleted.value = true
        stopPolling()
        emit('complete', summary.value)
      }
    } else {
      console.warn('获取进度失败:', res.message)
    }
  } catch (error) {
    console.error('获取进度失败:', error)
  }
}

const handleCancel = async () => {
  cancelling.value = true
  try {
    stopPolling()
    testCompleted.value = true
    ElMessage.warning('测试已被取消')
  } finally {
    cancelling.value = false
  }
}

const handleClose = () => {
  stopPolling()
  dialogVisible.value = false
  emit('close')
}

const exportReport = () => {
  const report = {
    generatedAt: new Date().toLocaleString('zh-CN'),
    summary: summary.value,
    reportContent: `网站模板批量测试报告
========================================
生成时间: ${new Date().toLocaleString('zh-CN')}
测试模板总数: ${summary.value.total_templates}
成功数量: ${summary.value.success_count}
失败数量: ${summary.value.failed_count}
警告数量: ${summary.value.warning_count}
成功率: ${summary.value.success_rate}%
========================================

一、失败的模板 (${summary.value.failed_templates?.length || 0})
${(summary.value.failed_templates || []).map((item, idx) => `
${idx + 1}. ${item.template_name} (${item.template_code})
   - 错误类型: ${item.error_type}
   - 错误信息: ${item.error_message}
   - 根本原因: ${item.root_cause}
   - 修复建议:
     ${(item.recommendations || []).map(r => '     * ' + r).join('\n')}
`).join('\n')}

二、需要关注的模板 (${summary.value.warning_templates?.length || 0})
${(summary.value.warning_templates || []).map((item, idx) => `
${idx + 1}. ${item.template_name} (${item.template_code})
   - 问题: ${item.error_message}
   - 建议:
     ${(item.recommendations || []).map(r => '     * ' + r).join('\n')}
`).join('\n')}

三、成功的模板 (${summary.value.success_templates?.length || 0})
${(summary.value.success_templates || []).map((item, idx) => `
${idx + 1}. ${item.template_name} - 获取数据: ${item.data_count}条, 耗时: ${item.duration?.toFixed(2)}秒
`).join('\n')}
`
  }

  const blob = new Blob([report.reportContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `batch_test_report_${new Date().format('YYYYMMDD_HHmmss')}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('报告已导出')
}

watch(dialogVisible, (val) => {
  if (!val) {
    stopPolling()
    testStarted.value = false
    testCompleted.value = false
    taskId.value = null
    steps.value = []
    summary.value = {}
    currentProgress.value = 0
    successCount.value = 0
    failedCount.value = 0
    warningCount.value = 0
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.batch-test-dialog {
  font-size: 14px;
}

.start-section {
  padding: 10px 0;
}

.start-section .warning-text {
  color: #e6a23c;
  margin-top: 8px;
  font-size: 12px;
}

.start-section .highlight {
  color: #409eff;
  font-weight: bold;
  font-size: 16px;
}

.action-bar {
  margin-top: 24px;
  text-align: center;
}

.progress-section {
  max-height: 600px;
  overflow-y: auto;
}

.progress-header {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.danger {
  color: #f56c6c;
}

.stat-value.warning {
  color: #e6a23c;
}

.main-progress {
  margin-top: 8px;
}

.steps-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.steps-count {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.steps-list {
  margin: 16px 0;
  max-height: 300px;
  overflow-y: auto;
}

.step-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  background: #e4e7ed;
  color: #909399;
  flex-shrink: 0;
}

.step-waiting .step-circle {
  background: #e4e7ed;
  color: #909399;
}

.step-active .step-circle {
  background: #409eff;
  color: white;
}

.step-completed .step-circle {
  background: #67c23a;
  color: white;
}

.step-error .step-circle {
  background: #f56c6c;
  color: white;
}

.step-warning .step-circle {
  background: #e6a23c;
  color: white;
}

.step-icon {
  font-size: 16px;
}

.step-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-line {
  width: 2px;
  height: 30px;
  background: #e4e7ed;
  margin-top: 4px;
}

.step-completed .step-line {
  background: #67c23a;
}

.step-content {
  flex: 1;
  padding-bottom: 8px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.step-waiting .step-title {
  color: #909399;
}

.step-active .step-title {
  color: #409eff;
}

.step-completed .step-title {
  color: #67c23a;
}

.step-error .step-title {
  color: #f56c6c;
}

.step-warning .step-title {
  color: #e6a23c;
}

.step-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.step-error-detail {
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.summary-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.summary-stats {
  margin-bottom: 20px;
}

.issues-section,
.warnings-section,
.success-section {
  margin-top: 20px;
}

.issues-title,
.warnings-title,
.success-title {
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.issues-list,
.warnings-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-card,
.warning-card {
  margin-bottom: 0;
}

.issue-header,
.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.issue-name,
.warning-name {
  font-weight: 600;
  color: #303133;
}

.issue-content,
.warning-content {
  font-size: 13px;
}

.issue-row {
  margin-bottom: 8px;
}

.issue-label {
  color: #909399;
  font-weight: 500;
}

.issue-value {
  color: #606266;
}

.issue-value.error {
  color: #f56c6c;
}

.recommendations {
  margin: 4px 0 0 20px;
  padding-left: 0;
  list-style-type: disc;
}

.recommendations li {
  color: #606266;
  line-height: 1.6;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>

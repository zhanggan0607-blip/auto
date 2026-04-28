﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="automation-config-page">
    <div class="page-header">
      <div class="header-title">
        <h3 class="page-title">全自动化配置</h3>
        <p class="page-subtitle">配置AI决策参数、自动匹配阈值、模型选择等</p>
      </div>
      <div class="header-actions">
        <el-button @click="loadConfig">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="createNewConfig">
          <el-icon><Plus /></el-icon>
          新建配置
        </el-button>
      </div>
    </div>

    <div class="config-layout">
      <el-card class="config-list-card">
        <template #header>
          <span>配置列表</span>
        </template>
        <el-scrollbar height="calc(100vh - 220px)">
          <div
            v-for="config in configList"
            :key="config.id"
            class="config-item"
            :class="{ active: currentConfig?.id === config.id, default: config.is_default }"
            @click="selectConfig(config)"
          >
            <div class="config-name">
              {{ config.name }}
              <el-tag v-if="config.is_default" size="small" type="success">默认</el-tag>
            </div>
            <div class="config-desc">{{ config.description || '暂无描述' }}</div>
            <div class="config-actions">
              <el-button
                v-if="!config.is_default"
                type="primary"
                link
                size="small"
                @click.stop="setAsDefault(config)"
              >
                设为默认
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                @click.stop="deleteConfig(config)"
              >
                删除
              </el-button>
            </div>
          </div>
        </el-scrollbar>
      </el-card>

      <div class="config-detail" v-if="currentConfig">
        <el-tabs v-model="activeTab" class="config-tabs">
          <el-tab-pane label="AI决策配置" name="decision">
            <el-card>
              <template #header>AI投标决策参数</template>
              <el-form :model="decisionForm" label-width="140px">
                <el-form-item label="启用AI决策">
                  <el-switch v-model="decisionForm.USE_AI_DECISION" />
                  <span class="form-help">关闭则使用规则匹配</span>
                </el-form-item>

                <el-divider content-position="left">评分权重配置</el-divider>

                <el-form-item label="资质匹配权重">
                  <el-slider
                    v-model="decisionForm.QUALIFICATION_WEIGHT"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (decisionForm.QUALIFICATION_WEIGHT * 100).toFixed(0) }}%</span>
                </el-form-item>

                <el-form-item label="竞争对手分析权重">
                  <el-slider
                    v-model="decisionForm.COMPETITOR_WEIGHT"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (decisionForm.COMPETITOR_WEIGHT * 100).toFixed(0) }}%</span>
                </el-form-item>

                <el-form-item label="历史业绩匹配权重">
                  <el-slider
                    v-model="decisionForm.PERFORMANCE_WEIGHT"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (decisionForm.PERFORMANCE_WEIGHT * 100).toFixed(0) }}%</span>
                </el-form-item>

                <el-form-item label="风险评估权重">
                  <el-slider
                    v-model="decisionForm.RISK_WEIGHT"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (decisionForm.RISK_WEIGHT * 100).toFixed(0) }}%</span>
                </el-form-item>

                <el-divider content-position="left">决策阈值配置</el-divider>

                <el-form-item label="自动投标阈值">
                  <el-input-number
                    v-model="decisionForm.AUTO_BID_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">>=此分数自动投标</span>
                </el-form-item>

                <el-form-item label="观察阈值">
                  <el-input-number
                    v-model="decisionForm.OBSERVATION_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">>=此分数标记观察</span>
                </el-form-item>

                <el-form-item label="跳过阈值">
                  <el-input-number
                    v-model="decisionForm.SKIP_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">&lt;此分数自动跳过</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveDecisionConfig">
                    保存AI决策配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="自动匹配配置" name="match">
            <el-card>
              <template #header>招标信息自动匹配参数</template>
              <el-form :model="matchForm" label-width="160px">
                <el-form-item label="启用自动匹配">
                  <el-switch v-model="matchForm.AUTO_MATCH_ENABLED" />
                </el-form-item>

                <el-divider content-position="left">匹配阈值配置</el-divider>

                <el-form-item label="自动入库阈值">
                  <el-slider
                    v-model="matchForm.AUTO_IMPORT_THRESHOLD"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (matchForm.AUTO_IMPORT_THRESHOLD * 100).toFixed(0) }}%</span>
                  <span class="form-help">>=此相似度自动入库（无需确认）</span>
                </el-form-item>

                <el-form-item label="自动投标匹配阈值">
                  <el-slider
                    v-model="matchForm.AUTO_BID_MATCH_THRESHOLD"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (matchForm.AUTO_BID_MATCH_THRESHOLD * 100).toFixed(0) }}%</span>
                  <span class="form-help">>=此相似度进行自动投标</span>
                </el-form-item>

                <el-form-item label="排除阈值">
                  <el-slider
                    v-model="matchForm.EXCLUDE_THRESHOLD"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    show-stops
                  />
                  <span class="weight-value">{{ (matchForm.EXCLUDE_THRESHOLD * 100).toFixed(0) }}%</span>
                  <span class="form-help">&lt;此相似度自动排除</span>
                </el-form-item>

                <el-divider content-position="left">智能优化配置</el-divider>

                <el-form-item label="自适应阈值调整">
                  <el-switch v-model="matchForm.ADAPTIVE_THRESHOLD" />
                  <span class="form-help">根据匹配质量自动优化阈值</span>
                </el-form-item>

                <el-form-item label="从历史结果学习">
                  <el-switch v-model="matchForm.LEARNING_FROM_HISTORY" />
                  <span class="form-help">根据中标/失标结果自动优化匹配策略</span>
                </el-form-item>

                <el-form-item label="关键词加权">
                  <el-switch v-model="matchForm.KEYWORD_BOOST_ENABLED" />
                  <span class="form-help">匹配时对关键词命中进行加权</span>
                </el-form-item>

                <el-form-item label="地区加权">
                  <el-switch v-model="matchForm.REGION_BOOST_ENABLED" />
                  <span class="form-help">匹配时对地区进行加权</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveMatchConfig">
                    保存自动匹配配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="文档审核配置" name="review">
            <el-card>
              <template #header>标书审核与上传参数</template>
              <el-form :model="reviewForm" label-width="160px">
                <el-divider content-position="left">审核阈值配置</el-divider>

                <el-form-item label="自动上传阈值">
                  <el-input-number
                    v-model="reviewForm.AUTO_UPLOAD_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">>=此分数自动上传标书</span>
                </el-form-item>

                <el-form-item label="观察阈值">
                  <el-input-number
                    v-model="reviewForm.OBSERVATION_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">>=此分数上传后标记观察</span>
                </el-form-item>

                <el-form-item label="人工审核阈值">
                  <el-input-number
                    v-model="reviewForm.MANUAL_REVIEW_THRESHOLD"
                    :min="0"
                    :max="100"
                    :step="5"
                  />
                  <span class="form-help">&lt;此分数触发人工审核</span>
                </el-form-item>

                <el-form-item label="最大优化轮数">
                  <el-input-number
                    v-model="reviewForm.MAX_OPTIMIZATION_ROUNDS"
                    :min="1"
                    :max="10"
                    :step="1"
                  />
                  <span class="form-help">标书审核未通过时的最大自动优化次数</span>
                </el-form-item>

                <el-divider content-position="left">审核功能配置</el-divider>

                <el-form-item label="启用废标检查">
                  <el-switch v-model="reviewForm.ENABLE_ANTI_REJECTION_CHECK" />
                  <span class="form-help">自动检测可能导致废标的风险项</span>
                </el-form-item>

                <el-form-item label="启用报价分析">
                  <el-switch v-model="reviewForm.ENABLE_PRICE_ANALYSIS" />
                  <span class="form-help">分析报价合理性和竞争力</span>
                </el-form-item>

                <el-form-item label="启用模拟打分">
                  <el-switch v-model="reviewForm.USE_SIMULATED_SCORING" />
                  <span class="form-help">模拟评委视角对标书进行打分</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveReviewConfig">
                    保存文档审核配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="风险控制配置" name="risk">
            <el-card>
              <template #header>自动化风险控制参数</template>
              <el-form :model="riskForm" label-width="160px">
                <el-divider content-position="left">限制配置</el-divider>

                <el-form-item label="每日最大投标数">
                  <el-input-number
                    v-model="riskForm.MAX_DAILY_BIDS"
                    :min="1"
                    :max="500"
                    :step="10"
                  />
                  <span class="form-help">超过此数量暂停当日自动投标</span>
                </el-form-item>

                <el-form-item label="金额阈值">
                  <el-input-number
                    v-model="riskForm.AMOUNT_THRESHOLD"
                    :min="0"
                    :max="100000000"
                    :step="100000"
                  />
                  <span class="form-help">超过此金额的项目需人工确认</span>
                </el-form-item>

                <el-form-item label="连续失败上限">
                  <el-input-number
                    v-model="riskForm.CONSECUTIVE_FAILURES"
                    :min="1"
                    :max="20"
                    :step="1"
                  />
                  <span class="form-help">连续失败超过此次数自动暂停</span>
                </el-form-item>

                <el-divider content-position="left">检查开关</el-divider>

                <el-form-item label="启用金额检查">
                  <el-switch v-model="riskForm.ENABLE_AMOUNT_CHECK" />
                </el-form-item>

                <el-form-item label="启用数量检查">
                  <el-switch v-model="riskForm.ENABLE_COUNT_CHECK" />
                </el-form-item>

                <el-form-item label="启用失败检查">
                  <el-switch v-model="riskForm.ENABLE_FAILURE_CHECK" />
                </el-form-item>

                <el-form-item label="风险自动暂停">
                  <el-switch v-model="riskForm.AUTO_PAUSE_ON_RISK" />
                  <span class="form-help">检测到风险时自动暂停相关任务</span>
                </el-form-item>

                <el-form-item label="风险通知">
                  <el-switch v-model="riskForm.NOTIFY_ON_RISK" />
                  <span class="form-help">检测到风险时发送钉钉通知</span>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveRiskConfig">
                    保存风险控制配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="采集配置" name="crawl">
            <el-card>
              <template #header>定时采集任务参数</template>
              <el-form :model="crawlForm" label-width="160px">
                <el-form-item label="自动学习关键词">
                  <el-switch v-model="crawlForm.AUTO_LEARN_KEYWORDS" />
                  <span class="form-help">根据历史中标项目自动优化关键词</span>
                </el-form-item>

                <el-form-item label="自适应采集模式">
                  <el-switch v-model="crawlForm.ADAPTIVE_CRAWL_MODE" />
                  <span class="form-help">根据网站情况自动选择最优采集策略</span>
                </el-form-item>

                <el-form-item label="多源采集">
                  <el-switch v-model="crawlForm.MULTI_SOURCE_ENABLED" />
                  <span class="form-help">是否启用多网站并行采集</span>
                </el-form-item>

                <el-form-item label="默认采集间隔">
                  <el-input-number
                    v-model="crawlForm.DEFAULT_CRAWL_INTERVAL"
                    :min="5"
                    :max="1440"
                    :step="5"
                  />
                  <span class="form-help">分钟</span>
                </el-form-item>

                <el-form-item label="每次最大采集页数">
                  <el-input-number
                    v-model="crawlForm.MAX_PAGES_PER_CRAWL"
                    :min="1"
                    :max="500"
                    :step="10"
                  />
                </el-form-item>

                <el-form-item label="启用去重">
                  <el-switch v-model="crawlForm.ENABLE_DEDUP" />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveCrawlConfig">
                    保存采集配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="通知配置" name="notification">
            <el-card>
              <template #header>消息通知参数</template>
              <el-form :model="notificationForm" label-width="140px">
                <el-form-item label="启用通知">
                  <el-switch v-model="notificationForm.NOTIFICATION_ENABLED" />
                </el-form-item>

                <el-form-item label="钉钉通知">
                  <el-switch v-model="notificationForm.DINGTALK_ENABLED" />
                </el-form-item>

                <el-form-item label="仅关键事件">
                  <el-switch v-model="notificationForm.KEY_EVENTS_ONLY" />
                  <span class="form-help">开启后仅对关键事件发送通知</span>
                </el-form-item>

                <el-form-item label="发送日报">
                  <el-switch v-model="notificationForm.DAILY_REPORT_ENABLED" />
                </el-form-item>

                <el-form-item label="发送周报">
                  <el-switch v-model="notificationForm.WEEKLY_REPORT_ENABLED" />
                </el-form-item>

                <el-divider content-position="left">事件通知开关</el-divider>

                <el-form-item label="启动通知">
                  <el-switch v-model="notificationForm.NOTIFY_ON_START" />
                </el-form-item>

                <el-form-item label="成功通知">
                  <el-switch v-model="notificationForm.NOTIFY_ON_SUCCESS" />
                </el-form-item>

                <el-form-item label="失败通知">
                  <el-switch v-model="notificationForm.NOTIFY_ON_FAILURE" />
                </el-form-item>

                <el-form-item label="中标通知">
                  <el-switch v-model="notificationForm.NOTIFY_ON_WIN" />
                </el-form-item>

                <el-form-item label="失标通知">
                  <el-switch v-model="notificationForm.NOTIFY_ON_LOSS" />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="saveNotificationConfig">
                    保存通知配置
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-tab-pane>
        </el-tabs>
      </div>

      <el-empty v-else description="请选择一个配置或创建新配置" />
    </div>

    <el-dialog v-model="createDialogVisible" title="新建配置" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="配置名称" required>
          <el-input v-model="createForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="配置描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入配置描述" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="createForm.is_default">设为默认配置</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Plus } from '@element-plus/icons-vue'
import { automationConfigApi } from '@/api/automationConfig'
import { parseListResponse } from '@/utils/response-parser'
import { useFormDraft } from '@/composables/useFormDraft'

const configList = ref([])
const currentConfig = ref(null)
const activeTab = ref('decision')
const createDialogVisible = ref(false)

const decisionForm = reactive({
  USE_AI_DECISION: true,
  QUALIFICATION_WEIGHT: 0.4,
  COMPETITOR_WEIGHT: 0.2,
  PERFORMANCE_WEIGHT: 0.2,
  RISK_WEIGHT: 0.2,
  AUTO_BID_THRESHOLD: 60,
  OBSERVATION_THRESHOLD: 40,
  SKIP_THRESHOLD: 40
})

const matchForm = reactive({
  AUTO_MATCH_ENABLED: true,
  AUTO_IMPORT_THRESHOLD: 0.8,
  AUTO_BID_MATCH_THRESHOLD: 0.6,
  EXCLUDE_THRESHOLD: 0.6,
  ADAPTIVE_THRESHOLD: true,
  LEARNING_FROM_HISTORY: true,
  KEYWORD_BOOST_ENABLED: true,
  REGION_BOOST_ENABLED: true
})

const reviewForm = reactive({
  AUTO_UPLOAD_THRESHOLD: 90,
  OBSERVATION_THRESHOLD: 60,
  MANUAL_REVIEW_THRESHOLD: 60,
  MAX_OPTIMIZATION_ROUNDS: 3,
  ENABLE_ANTI_REJECTION_CHECK: true,
  ENABLE_PRICE_ANALYSIS: true,
  USE_SIMULATED_SCORING: true
})

const riskForm = reactive({
  MAX_DAILY_BIDS: 50,
  AMOUNT_THRESHOLD: 1000000,
  CONSECUTIVE_FAILURES: 3,
  ENABLE_AMOUNT_CHECK: true,
  ENABLE_COUNT_CHECK: true,
  ENABLE_FAILURE_CHECK: true,
  AUTO_PAUSE_ON_RISK: true,
  NOTIFY_ON_RISK: true
})

const crawlForm = reactive({
  AUTO_LEARN_KEYWORDS: true,
  ADAPTIVE_CRAWL_MODE: true,
  MULTI_SOURCE_ENABLED: true,
  DEFAULT_CRAWL_INTERVAL: 60,
  MAX_PAGES_PER_CRAWL: 50,
  ENABLE_DEDUP: true
})

const notificationForm = reactive({
  NOTIFICATION_ENABLED: true,
  DINGTALK_ENABLED: true,
  KEY_EVENTS_ONLY: false,
  DAILY_REPORT_ENABLED: true,
  WEEKLY_REPORT_ENABLED: false,
  NOTIFY_ON_START: false,
  NOTIFY_ON_SUCCESS: true,
  NOTIFY_ON_FAILURE: true,
  NOTIFY_ON_WIN: true,
  NOTIFY_ON_LOSS: true
})

const createForm = reactive({
  name: '',
  description: '',
  is_default: false
})

const allConfigForms = reactive({
  decision: decisionForm,
  match: matchForm,
  review: reviewForm,
  risk: riskForm,
  crawl: crawlForm,
  notification: notificationForm
})

const { clearDraft: clearConfigDraft } = useFormDraft(allConfigForms, {
  key: 'automation:config',
  context: () => ({ configId: currentConfig.value?.id, activeTab: activeTab.value })
})

const loadConfigs = async () => {
  try {
    const res = await automationConfigApi.list()
    const { list } = parseListResponse(res)
    configList.value = list
  } catch (error) {
    console.error('加载配置列表失败:', error)
  }
}

const loadConfig = async () => {
  await loadConfigs()
  if (configList.value.length > 0 && !currentConfig.value) {
    selectConfig(configList.value.find(c => c.is_default) || configList.value[0])
  }
}

const selectConfig = async (config) => {
  currentConfig.value = config

  if (config.decision_config) {
    Object.assign(decisionForm, config.decision_config)
  }
  if (config.match_config) {
    Object.assign(matchForm, config.match_config)
  }
  if (config.review_config) {
    Object.assign(reviewForm, config.review_config)
  }
  if (config.risk_config) {
    Object.assign(riskForm, config.risk_config)
  }
  if (config.crawl_config) {
    Object.assign(crawlForm, config.crawl_config)
  }
  if (config.notification_config) {
    Object.assign(notificationForm, config.notification_config)
  }
}

const createNewConfig = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.is_default = false
  createDialogVisible.value = true
}

const confirmCreate = async () => {
  if (!createForm.name) {
    ElMessage.warning('请输入配置名称')
    return
  }

  try {
    await automationConfigApi.createWithDefaults({
      name: createForm.name,
      description: createForm.description,
      is_default: createForm.is_default
    })
    ElMessage.success('配置创建成功')
    createDialogVisible.value = false
    await loadConfigs()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

const setAsDefault = async (config) => {
  try {
    await automationConfigApi.setDefault(config.id)
    ElMessage.success('已设为默认配置')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm(`确定要删除配置"${config.name}"吗？`, '提示', {
      type: 'warning'
    })
    await automationConfigApi.delete(config.id)
    ElMessage.success('删除成功')
    if (currentConfig.value?.id === config.id) {
      currentConfig.value = null
    }
    await loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveDecisionConfig = async () => {
  try {
    await automationConfigApi.updateDecisionConfig(currentConfig.value.id, decisionForm)
    clearConfigDraft()
    ElMessage.success('AI决策配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveMatchConfig = async () => {
  try {
    await automationConfigApi.updateMatchConfig(currentConfig.value.id, matchForm)
    clearConfigDraft()
    ElMessage.success('自动匹配配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveReviewConfig = async () => {
  try {
    await automationConfigApi.updateReviewConfig(currentConfig.value.id, reviewForm)
    clearConfigDraft()
    ElMessage.success('文档审核配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveRiskConfig = async () => {
  try {
    await automationConfigApi.updateRiskConfig(currentConfig.value.id, riskForm)
    clearConfigDraft()
    ElMessage.success('风险控制配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveCrawlConfig = async () => {
  try {
    await automationConfigApi.updateCrawlConfig(currentConfig.value.id, crawlForm)
    clearConfigDraft()
    ElMessage.success('采集配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const saveNotificationConfig = async () => {
  try {
    await automationConfigApi.updateNotificationConfig(currentConfig.value.id, notificationForm)
    clearConfigDraft()
    ElMessage.success('通知配置已保存')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.automation-config-page {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;

  .header-title {
    .page-title {
      margin: 0 0 8px 0;
      font-size: 20px;
      font-weight: 600;
    }

    .page-subtitle {
      margin: 0;
      color: #64748B;
      font-size: 14px;
    }
  }

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.config-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 160px);

  .config-list-card {
    width: 280px;
    flex-shrink: 0;

    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .config-detail {
    flex: 1;
    overflow: hidden;

    .config-tabs {
      height: 100%;

      :deep(.el-tabs__content) {
        height: calc(100vh - 220px);
        overflow-y: auto;
      }
    }
  }
}

.config-item {
  padding: 15px;
  border-bottom: 1px solid #E2E8F0;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background-color: #F1F5F9;
  }

  &.active {
    background-color: #EFF6FF;
    border-left: 3px solid #3B82F6;
  }

  &.default {
    .config-name {
      color: #16A34A;
    }
  }

  .config-name {
    font-weight: 600;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .config-desc {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 8px;
  }

  .config-actions {
    display: flex;
    gap: 10px;
  }
}

.form-help {
  margin-left: 10px;
  color: #64748B;
  font-size: 12px;
}

.weight-value {
  margin-left: 10px;
  color: #3B82F6;
  font-weight: 600;
}

.el-divider {
  margin: 20px 0;
}
</style>

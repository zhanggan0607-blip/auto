<template>
  <div class="automation-dashboard">
    <div class="page-header">
      <h3 class="page-title">投标自动化工作台</h3>
      <div class="header-actions">
        <el-button type="info" @click="goToConfig">
          <el-icon><Setting /></el-icon>
          全自动配置
        </el-button>
        <el-button type="primary" @click="startNewWorkflow">
          <el-icon><Plus /></el-icon>
          新建投标任务
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.total_workflows || 0 }}</div>
          <div class="stat-label">总任务数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.running_workflows || 0 }}</div>
          <div class="stat-label">执行中</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.completed_workflows || 0 }}</div>
          <div class="stat-label">已完成</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.pending_review || 0 }}</div>
          <div class="stat-label">待审核</div>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" class="main-tabs">
      <el-tab-pane label="工作流列表" name="workflows">
        <el-table :data="workflowList" v-loading="loading" style="width: 100%" />
      </el-tab-pane>

      <el-tab-pane label="采集计划" name="schedules">
        <div class="schedule-actions">
          <el-button type="primary" @click="showCreateScheduleDialog">
            <el-icon><Plus /></el-icon>
            新建采集计划
          </el-button>
        </div>
        <el-table :data="schedules" v-loading="schedulesLoading" style="width: 100%">
          <el-table-column prop="name" label="计划名称" min-width="150" />
          <el-table-column prop="website_template_name" label="网站模板" min-width="120" />
          <el-table-column prop="crontab" label="执行时间" width="120">
            <template #default="{ row }">
              <el-tooltip :content="parseCrontab(row.crontab)">
                <span>{{ row.crontab }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '已启用' : '已暂停' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="auto_match" label="自动匹配" width="100">
            <template #default="{ row }">
              <el-tag :type="row.auto_match ? 'success' : 'info'" size="small">
                {{ row.auto_match ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="last_run_at" label="上次执行" width="160">
            <template #default="{ row }">
              {{ row.last_run_at ? formatTime(row.last_run_at) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="run_count" label="执行次数" width="90" />
          <el-table-column prop="last_result_count" label="上次采集" width="90" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button size="small" @click="executeScheduleNow(row)" :loading="row.executing">
                  执行
                </el-button>
                <el-button 
                  size="small" 
                  :type="row.status === 'active' ? 'warning' : 'success'"
                  @click="toggleScheduleStatus(row)"
                >
                  {{ row.status === 'active' ? '暂停' : '启用' }}
                </el-button>
                <el-button size="small" @click="showEditScheduleDialog(row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="deleteSchedule(row)">
                  删除
                </el-button>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="schedulesPagination.page"
          v-model:page-size="schedulesPagination.pageSize"
          :total="schedulesPagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="fetchSchedules"
          @current-change="fetchSchedules"
          class="pagination"
        />
      </el-tab-pane>

      <el-tab-pane label="调度任务" name="scheduler">
        <el-table :data="schedulerTasks" v-loading="schedulerLoading" style="width: 100%">
          <el-table-column prop="name" label="任务名称" min-width="180" />
          <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
          <el-table-column prop="cron_expression" label="执行周期" width="120" />
          <el-table-column prop="enabled" label="状态" width="100">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" @change="toggleTask(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="last_run" label="上次执行" width="160">
            <template #default="{ row }">
              {{ formatTime(row.last_run) || '从未执行' }}
            </template>
          </el-table-column>
          <el-table-column prop="run_count" label="执行次数" width="100" />
          <el-table-column prop="error_count" label="错误次数" width="100">
            <template #default="{ row }">
              <span :class="{ 'error-count': row.error_count > 0 }">{{ row.error_count }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button type="primary" link @click="runTaskNow(row)">立即执行</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="系统状态" name="health">
        <el-card class="health-card">
          <template #header>
            <div class="card-header">
              <span>系统健康状态</span>
              <el-tag :type="healthStatus.overall === 'healthy' ? 'success' : 'warning'">
                {{ healthStatus.overall === 'healthy' ? '正常' : '异常' }}
              </el-tag>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据库">
              <el-tag :type="healthStatus.database === 'ok' ? 'success' : 'danger'">
                {{ healthStatus.database === 'ok' ? '正常' : healthStatus.database }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="缓存">
              <el-tag :type="healthStatus.cache === 'ok' ? 'success' : 'danger'">
                {{ healthStatus.cache === 'ok' ? '正常' : healthStatus.cache }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="向量库">
              <el-tag :type="healthStatus.vector_db === 'ok' ? 'success' : 'danger'">
                {{ healthStatus.vector_db === 'ok' ? '正常' : healthStatus.vector_db }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="向量文档数">
              {{ healthStatus.vector_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="检查时间" :span="2">
              {{ formatTime(healthStatus.timestamp) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="workflowDialogVisible" title="新建投标任务" width="600px">
      <el-form :model="workflowForm" :rules="workflowRules" ref="workflowFormRef" label-width="100px">
        <el-form-item label="招标项目" prop="tender_id">
          <el-select v-model="workflowForm.tender_id" placeholder="选择招标项目" style="width: 100%" filterable>
            <el-option
              v-for="item in tenderList"
              :key="item.id"
              :label="item.title"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="投标企业" prop="enterprise_id">
          <el-select v-model="workflowForm.enterprise_id" placeholder="选择投标企业" style="width: 100%" filterable>
            <el-option
              v-for="item in enterpriseList"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="配置选项">
          <el-checkbox v-model="workflowForm.auto_upload">达到90分自动上传</el-checkbox>
          <el-checkbox v-model="workflowForm.send_notification">完成后发送通知</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="workflowDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitWorkflow" :loading="submitting">启动任务</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="工作流详情" width="800px">
      <el-descriptions :column="2" border v-if="currentWorkflow">
        <el-descriptions-item label="工作流ID">{{ currentWorkflow.workflow_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentWorkflow.status)">{{ getStatusText(currentWorkflow.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前阶段">{{ getTaskName(currentWorkflow.current_task) }}</el-descriptions-item>
        <el-descriptions-item label="模拟得分">
          <span :class="getScoreClass(currentWorkflow.bid_score)">{{ currentWorkflow.bid_score || '-' }}分</span>
        </el-descriptions-item>
        <el-descriptions-item label="优化次数">{{ currentWorkflow.iteration_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentWorkflow.created_at) }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider>执行日志</el-divider>
      <el-timeline v-if="currentWorkflow.logs?.length">
        <el-timeline-item
          v-for="(log, index) in currentWorkflow.logs"
          :key="index"
          :timestamp="formatTime(log.timestamp)"
          placement="top"
        >
          {{ log.message }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无执行日志" />
    </el-dialog>

    <el-dialog
      v-model="scheduleDialogVisible"
      :title="isEditSchedule ? '编辑采集计划' : '新建采集计划'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="scheduleForm" :rules="scheduleRules" ref="scheduleFormRef" label-width="120px">
        <el-form-item label="计划名称" prop="name">
          <el-input v-model="scheduleForm.name" placeholder="请输入计划名称" />
        </el-form-item>
        <el-form-item label="网站模板" prop="website_template">
          <el-select v-model="scheduleForm.website_template" placeholder="请选择网站模板" style="width: 100%">
            <el-option
              v-for="template in templates"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行模式">
          <el-radio-group v-model="scheduleForm.exec_mode">
            <el-radio value="once">单次执行</el-radio>
            <el-radio value="daily">每天循环</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="执行时间">
          <el-date-picker
            v-if="scheduleForm.exec_mode === 'once'"
            v-model="scheduleForm.exec_datetime"
            type="datetime"
            placeholder="选择执行时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
          <el-time-picker
            v-else
            v-model="scheduleForm.exec_time"
            placeholder="选择时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="采集地区">
          <div class="region-select">
            <el-switch
              v-model="scheduleForm.regionsMultiple"
              active-text="多选"
              inactive-text="单选"
              style="margin-right: 10px;"
            />
            <el-cascader
              v-model="scheduleForm.regions"
              :options="regionOptions"
              :placeholder="scheduleForm.regionsMultiple ? '选择省/市/区（可多选）' : '选择省/市/区'"
              :props="{
                value: 'value',
                label: 'label',
                children: 'children',
                multiple: scheduleForm.regionsMultiple
              }"
              :clearable="true"
              :filterable="true"
              :collapse-tags="scheduleForm.regionsMultiple"
              :style="{ width: '100%' }"
            />
          </div>
        </el-form-item>
        <el-form-item label="最大采集页数">
          <el-input-number v-model="scheduleForm.max_pages" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="采集模式">
          <el-radio-group v-model="scheduleForm.crawl_mode">
            <el-radio value="full">全量采集</el-radio>
            <el-radio value="incremental">增量采集</el-radio>
          </el-radio-group>
          <div class="form-tip">全量采集：采集所有页面；增量采集：仅采集最新数据</div>
        </el-form-item>
        <el-form-item label="搜索关键词">
          <el-select
            v-model="scheduleForm.keywords"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入关键词后回车"
            style="width: 100%"
          />
        </el-form-item>
        <el-divider content-position="left">智能匹配设置</el-divider>
        <el-form-item label="自动匹配资质">
          <el-switch v-model="scheduleForm.auto_match" />
          <span class="form-tip">采集完成后自动用企业条件匹配招标公告</span>
        </el-form-item>
        <el-form-item label="选择企业" v-if="scheduleForm.auto_match">
          <el-select
            v-model="scheduleForm.enterprise_ids"
            placeholder="选择用于资质匹配的企业"
            multiple
            filterable
            clearable
            style="width: 100%"
            :loading="enterpriseLoading"
          >
            <el-option
              v-for="ent in enterpriseList"
              :key="ent.id"
              :label="ent.name"
              :value="ent.id"
            >
              <div class="enterprise-option">
                <span class="enterprise-name">{{ ent.name }}</span>
                <el-tag v-if="ent.qualification_count" size="small" type="info">
                  {{ ent.qualification_count }}个资质
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <span class="form-tip">选择参与资质匹配的企业，留空则使用所有企业</span>
        </el-form-item>
        <el-form-item label="自动删除不匹配">
          <el-switch v-model="scheduleForm.auto_delete_unmatched" />
          <span class="form-tip">不满足企业条件的项目自动删除</span>
        </el-form-item>
        <el-form-item label="匹配阈值">
          <el-slider v-model="scheduleForm.match_threshold" :min="0" :max="1" :step="0.1" show-input />
          <span class="form-tip">低于此阈值的视为不匹配</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitSchedule" :loading="scheduleSubmitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, QuestionFilled } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { crawlerApi } from '@/api/crawler'
import { enterpriseApi } from '@/api/enterprise'
import { regionData } from '@/utils/regions'

const router = useRouter()

const activeTab = ref('workflows')
const loading = ref(false)
const schedulerLoading = ref(false)
const schedulesLoading = ref(false)
const submitting = ref(false)
const scheduleSubmitting = ref(false)
const workflowDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const scheduleDialogVisible = ref(false)
const isEditSchedule = ref(false)
const regionOptions = ref(regionData)
const enterpriseLoading = ref(false)

const statistics = ref({
  total_workflows: 0,
  running_workflows: 0,
  completed_workflows: 0,
  pending_review: 0
})

const workflowList = ref([])
const schedulerTasks = ref([])
const schedules = ref([])
const templates = ref([])
const tenderList = ref([])
const enterpriseList = ref([])
const currentWorkflow = ref(null)

const schedulesPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const healthStatus = ref({
  overall: 'healthy',
  database: 'ok',
  cache: 'ok',
  vector_db: 'ok',
  vector_count: 0
})

const workflowForm = reactive({
  tender_id: null,
  enterprise_id: null,
  auto_upload: true,
  send_notification: true
})

const workflowRules = {
  tender_id: [{ required: true, message: '请选择招标项目', trigger: 'change' }],
  enterprise_id: [{ required: true, message: '请选择投标企业', trigger: 'change' }]
}

const workflowFormRef = ref(null)

const scheduleForm = reactive({
  name: '',
  website_template: null,
  crontab: '0 8 * * *',
  exec_mode: 'daily',
  exec_datetime: null,
  exec_time: '08:00:00',
  max_pages: 10,
  crawl_mode: 'full',
  keywords: [],
  regions: [],
  regionsMultiple: false,
  enterprise_ids: [],
  auto_match: true,
  auto_delete_unmatched: false,
  match_threshold: 0.6
})

const scheduleRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  website_template: [{ required: true, message: '请选择网站模板', trigger: 'change' }],
  crontab: [{ required: true, message: '请输入执行时间', trigger: 'blur' }]
}

const scheduleFormRef = ref(null)
const currentScheduleId = ref(null)

const taskNames = {
  'task_1_qualification_match': '资质比对',
  'task_2_download_tender': '文件下载',
  'task_3_parse_tender': '文件解析',
  'task_4_generate_bid': '标书生成',
  'task_5_review_bid': '标书审核',
  'task_6_upload_bid': '标书上传',
  'task_7_optimize_bid': '标书优化',
  'task_8_track_project': '项目跟踪',
  'task_9_notify_result': '结果通知'
}

const getStatusType = (status) => {
  const types = {
    'pending': 'info',
    'running': 'primary',
    'completed': 'success',
    'failed': 'danger',
    'waiting_review': 'warning',
    'cancelled': 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待执行',
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'waiting_review': '待审核',
    'cancelled': '已取消'
  }
  return texts[status] || status
}

const getTaskName = (task) => {
  return taskNames[task] || task || '-'
}

const getScoreClass = (score) => {
  if (!score) return ''
  if (score >= 90) return 'score-high'
  if (score >= 70) return 'score-medium'
  return 'score-low'
}

const formatTime = (time) => {
  if (!time) return '-'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const parseCrontab = (crontab) => {
  const parts = crontab.split(' ')
  if (parts.length !== 5) return crontab
  
  const [min, hour] = parts
  let desc = ''
  
  if (min === '0' && hour !== '*') {
    desc = `每天 ${hour} 点执行`
  } else if (min.startsWith('*/')) {
    desc = `每 ${min.slice(2)} 分钟执行`
  } else {
    desc = crontab
  }
  
  return desc
}

const fetchStatistics = async () => {
  try {
    const res = await request.get('/v1/openclaw/automation/statistics/')
    if (res.data?.success) {
      statistics.value = res.data.data || {}
    }
  } catch (error) {
    console.error('获取统计失败:', error)
  }
}

const fetchWorkflows = async () => {
  loading.value = true
  try {
    const res = await request.get('/v1/openclaw/automation/list_active/')
    if (res.data?.success) {
      workflowList.value = res.data.data?.list || []
    }
  } catch (error) {
    console.error('获取工作流列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchSchedulerStatus = async () => {
  schedulerLoading.value = true
  try {
    const res = await request.get('/v1/openclaw/scheduler/status/')
    if (res.data?.success) {
      const tasks = res.data.data?.tasks || {}
      schedulerTasks.value = Object.entries(tasks).map(([id, task]) => ({
        task_id: id,
        ...task
      }))
    }
  } catch (error) {
    console.error('获取调度状态失败:', error)
  } finally {
    schedulerLoading.value = false
  }
}

const fetchHealthStatus = async () => {
  try {
    const res = await request.get('/v1/openclaw/scheduler/health/')
    if (res.data?.success) {
      healthStatus.value = res.data.data || {}
    }
  } catch (error) {
    console.error('获取健康状态失败:', error)
  }
}

const fetchSchedules = async () => {
  schedulesLoading.value = true
  try {
    const res = await crawlerApi.getCrawlSchedules({
      page: schedulesPagination.page,
      page_size: schedulesPagination.pageSize
    })
    if (res.data && res.data.list) {
      schedules.value = res.data.list
      schedulesPagination.total = res.data.pagination?.total || 0
    } else if (res.data && res.data.results) {
      schedules.value = res.data.results
      schedulesPagination.total = res.data.count || 0
    } else if (Array.isArray(res.data)) {
      schedules.value = res.data
      schedulesPagination.total = res.data.length
    }
  } catch (error) {
    console.error('获取采集计划失败:', error)
  } finally {
    schedulesLoading.value = false
  }
}

const fetchTemplates = async () => {
  try {
    const res = await crawlerApi.getWebsiteTemplates({ page_size: 100 })
    if (res.data && res.data.list) {
      templates.value = res.data.list
    } else if (res.data && res.data.results) {
      templates.value = res.data.results
    } else if (Array.isArray(res.data)) {
      templates.value = res.data
    }
  } catch (error) {
    console.error('获取网站模板失败:', error)
  }
}

const loadEnterprises = async () => {
  enterpriseLoading.value = true
  try {
    const res = await enterpriseApi.getEnterprises({ page_size: 100 })
    enterpriseList.value = res?.data?.results || res?.results || res?.data?.list || res?.list || res?.data || []
  } catch (error) {
    console.error('获取企业列表失败:', error)
    enterpriseList.value = []
  } finally {
    enterpriseLoading.value = false
  }
}

const fetchTenders = async () => {
  try {
    const res = await request.get('/v1/tenders/', { params: { status: 'pending' } })
    if (res.data?.success) {
      tenderList.value = res.data.data?.list || res.data.data?.results || []
    }
  } catch (error) {
    console.error('获取招标列表失败:', error)
  }
}

const fetchEnterprises = async () => {
  try {
    const res = await request.get('/v1/enterprise/enterprises/')
    if (res.data?.success) {
      enterpriseList.value = res.data.data?.list || res.data.data?.results || []
    }
  } catch (error) {
    console.error('获取企业列表失败:', error)
  }
}

const refreshData = () => {
  fetchStatistics()
  fetchWorkflows()
  fetchSchedulerStatus()
  fetchHealthStatus()
  fetchSchedules()
}

const goToConfig = () => {
  router.push('/automation-config')
}

const startNewWorkflow = () => {
  fetchTenders()
  fetchEnterprises()
  workflowDialogVisible.value = true
}

const submitWorkflow = async () => {
  if (!workflowFormRef.value) return
  
  await workflowFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const res = await request.post('/v1/openclaw/automation/start/', {
        tender_id: workflowForm.tender_id,
        enterprise_id: workflowForm.enterprise_id,
        config: {
          auto_upload: workflowForm.auto_upload,
          send_notification: workflowForm.send_notification
        }
      })
      
      if (res.data?.success) {
        ElMessage.success('投标任务已启动')
        workflowDialogVisible.value = false
        refreshData()
      } else {
        ElMessage.error(res.data?.message || '启动失败')
      }
    } catch (error) {
      ElMessage.error('启动失败')
    } finally {
      submitting.value = false
    }
  })
}

const toggleTask = async (row) => {
  try {
    const action = row.enabled ? 'enable' : 'disable'
    await request.post(`/v1/openclaw/scheduler/${action}_task/`, { task_id: row.task_id })
    ElMessage.success(row.enabled ? '任务已启用' : '任务已禁用')
  } catch (error) {
    row.enabled = !row.enabled
    ElMessage.error('操作失败')
  }
}

const runTaskNow = async (row) => {
  try {
    const res = await request.post(`/v1/openclaw/scheduler/run_now/`, { task_id: row.task_id })
    if (res.data?.success) {
      ElMessage.success('任务已执行')
      fetchSchedulerStatus()
    }
  } catch (error) {
    ElMessage.error('执行失败')
  }
}

const showCreateScheduleDialog = () => {
  isEditSchedule.value = false
  currentScheduleId.value = null
  Object.assign(scheduleForm, {
    name: '',
    website_template: null,
    crontab: '0 8 * * *',
    exec_mode: 'daily',
    exec_datetime: null,
    exec_time: '08:00:00',
    max_pages: 10,
    crawl_mode: 'full',
    keywords: [],
    regions: [],
    regionsMultiple: false,
    enterprise_ids: [],
    auto_match: true,
    auto_delete_unmatched: false,
    match_threshold: 0.6
  })
  fetchTemplates()
  loadEnterprises()
  scheduleDialogVisible.value = true
}

const showEditScheduleDialog = (row) => {
  isEditSchedule.value = true
  currentScheduleId.value = row.id

  const regionsMultiple = Array.isArray(row.regions?.[0]?.[0])

  if (row.exec_datetime) {
    Object.assign(scheduleForm, {
      name: row.name,
      website_template: row.website_template,
      crontab: row.crontab || '0 8 * * *',
      exec_mode: 'once',
      exec_datetime: row.exec_datetime,
      exec_time: null,
      max_pages: row.max_pages,
      crawl_mode: row.crawl_mode || 'full',
      keywords: row.keywords || [],
      regions: row.regions || [],
      regionsMultiple: regionsMultiple,
      enterprise_ids: row.enterprise_ids || [],
      auto_match: row.auto_match,
      auto_delete_unmatched: row.auto_delete_unmatched,
      match_threshold: row.match_threshold
    })
  } else {
    const parts = (row.crontab || '0 8 * * *').split(' ')
    let exec_time = '08:00:00'
    if (parts.length >= 2) {
      const hour = parts[1].padStart(2, '0')
      const minute = parts[0].padStart(2, '0')
      exec_time = `${hour}:${minute}:00`
    }
    Object.assign(scheduleForm, {
      name: row.name,
      website_template: row.website_template,
      crontab: row.crontab || '0 8 * * *',
      exec_mode: 'daily',
      exec_datetime: null,
      exec_time: exec_time,
      max_pages: row.max_pages,
      crawl_mode: row.crawl_mode || 'full',
      keywords: row.keywords || [],
      regions: row.regions || [],
      regionsMultiple: regionsMultiple,
      enterprise_ids: row.enterprise_ids || [],
      auto_match: row.auto_match,
      auto_delete_unmatched: row.auto_delete_unmatched,
      match_threshold: row.match_threshold
    })
  }
  fetchTemplates()
  loadEnterprises()
  scheduleDialogVisible.value = true
}

const submitSchedule = async () => {
  if (!scheduleFormRef.value) return

  await scheduleFormRef.value.validate(async (valid) => {
    if (!valid) return

    scheduleSubmitting.value = true
    try {
      const submitData = { ...scheduleForm }
      delete submitData.exec_mode
      delete submitData.exec_time

      if (scheduleForm.exec_mode === 'once') {
        submitData.exec_datetime = scheduleForm.exec_datetime
        submitData.crontab = null
      } else {
        submitData.exec_datetime = null
        if (scheduleForm.exec_time) {
          const [hour, minute] = scheduleForm.exec_time.split(':')
          submitData.crontab = `${minute} ${hour} * * *`
        }
      }

      if (isEditSchedule.value) {
        await crawlerApi.updateCrawlSchedule(currentScheduleId.value, submitData)
        ElMessage.success('更新成功')
      } else {
        await crawlerApi.createCrawlSchedule(submitData)
        ElMessage.success('创建成功')
      }
      scheduleDialogVisible.value = false
      fetchSchedules()
    } catch (error) {
      console.error('保存失败:', error)
      ElMessage.error(error.response?.data?.message || '保存失败')
    } finally {
      scheduleSubmitting.value = false
    }
  })
}

const executeScheduleNow = async (row) => {
  row.executing = true
  try {
    await crawlerApi.executeCrawlScheduleNow(row.id)
    ElMessage.success('任务已提交执行')
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error('执行失败')
  } finally {
    row.executing = false
  }
}

const toggleScheduleStatus = async (row) => {
  try {
    if (row.status === 'active') {
      await crawlerApi.pauseCrawlSchedule(row.id)
      ElMessage.success('已暂停')
    } else {
      await crawlerApi.enableCrawlSchedule(row.id)
      ElMessage.success('已启用')
    }
    fetchSchedules()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const deleteSchedule = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该采集计划吗？', '提示', {
      type: 'warning'
    })
    await crawlerApi.deleteCrawlSchedule(row.id)
    ElMessage.success('删除成功')
    fetchSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

let refreshInterval = null

onMounted(() => {
  refreshData()
  refreshInterval = setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style lang="scss" scoped>
.automation-dashboard {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 10px;
  }
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 16px 0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.main-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.schedule-actions {
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.form-tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.enterprise-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.enterprise-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

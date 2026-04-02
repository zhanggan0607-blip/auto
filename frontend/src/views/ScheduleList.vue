<template>
  <div class="page-container">
    <PageHeader title="定时采集" subtitle="配置定时任务自动采集招标信息">
      <template #actions>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新建计划
        </el-button>
      </template>
    </PageHeader>

    <el-card class="content-card">
      <el-table :data="schedules" v-loading="loading" stripe>
        <el-table-column prop="name" label="计划名称" min-width="150" />
        <el-table-column prop="website_template_name" label="网站模板" min-width="120" />
        <el-table-column prop="crontab" label="执行时间" width="120">
          <template #default="{ row }">
            <el-tooltip :content="parseCrontab(row.crontab)">
              <span>{{ row.crontab }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="crawl_mode" label="采集模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.crawl_mode === 'full' ? 'primary' : 'success'" size="small">
              {{ row.crawl_mode_display || (row.crawl_mode === 'full' ? '全量采集' : '增量采集') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status_display }}
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
        <el-table-column prop="auto_delete_unmatched" label="自动删除" width="100">
          <template #default="{ row }">
            <el-tag :type="row.auto_delete_unmatched ? 'warning' : 'info'" size="small">
              {{ row.auto_delete_unmatched ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="上次执行" width="160">
          <template #default="{ row }">
            {{ row.last_run_at ? formatDate(row.last_run_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="run_count" label="执行次数" width="90" />
        <el-table-column prop="last_result_count" label="上次采集" width="90" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="executeNow(row)" :loading="row.executing">
                执行
              </el-button>
              <el-button
                size="small"
                :type="row.status === 'active' ? 'warning' : 'success'"
                @click="toggleStatus(row)"
              >
                {{ row.status === 'active' ? '暂停' : '启用' }}
              </el-button>
              <el-button size="small" @click="viewLogs(row)">
                日志
              </el-button>
              <el-button size="small" @click="showEditDialog(row)">
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchSchedules"
        @current-change="fetchSchedules"
        class="pagination"
      />
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑采集计划' : '新建采集计划'"
      width="700px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="计划名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入计划名称"
            :loading="nameChecking"
            @blur="checkNameDuplicate"
          >
            <template #suffix>
              <el-icon v-if="nameChecking"><Loading /></el-icon>
              <el-icon v-else-if="nameDuplicate === true" color="#F56C6C"><Close /></el-icon>
              <el-icon v-else-if="nameDuplicate === false && form.name" color="#67C23A"><Check /></el-icon>
            </template>
          </el-input>
          <div v-if="nameDuplicate === true" class="name-error">该计划名称已被使用</div>
        </el-form-item>

        <el-form-item label="输入方式" prop="inputMode">
          <el-radio-group v-model="inputMode" size="small">
            <el-radio-button value="select">选择模板</el-radio-button>
            <el-radio-button value="category">分类选择</el-radio-button>
            <el-radio-button value="manual">手动输入</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          label="网站模板"
          prop="website_template"
          v-if="inputMode === 'select'"
        >
          <el-select
            v-model="form.website_template"
            placeholder="请选择网站模板"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="template in templates"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            >
              <div class="template-option">
                <span>{{ template.name }}</span>
                <el-tag size="small" type="info">{{ getTypeLabel(template.website_type) }}</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          label="模板分类"
          prop="selectedCategory"
          v-if="inputMode === 'category'"
        >
          <el-select
            v-model="selectedCategory"
            placeholder="请选择分类"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="cat in templateCategories"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          label="选择模板"
          prop="website_template"
          v-if="inputMode === 'category' && selectedCategory"
        >
          <el-select
            v-model="form.website_template"
            placeholder="请选择分类后选择模板"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="template in filteredTemplatesByCategory"
              :key="template.id"
              :label="template.name"
              :value="template.id"
            >
              <div class="template-option">
                <span>{{ template.name }}</span>
                <el-tag size="small" type="info">{{ template.base_url }}</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          label="自定义URL"
          prop="customUrl"
          v-if="inputMode === 'manual'"
        >
          <el-input
            v-model="form.customUrl"
            placeholder="请输入自定义网站URL"
            clearable
          >
            <template #prepend>
              <el-select v-model="customProtocol" style="width: 100px">
                <el-option label="http://" value="http://" />
                <el-option label="https://" value="https://" />
              </el-select>
            </template>
          </el-input>
          <div class="form-tip">手动输入URL将创建自定义网站模板</div>
        </el-form-item>

        <el-form-item label="执行模式">
          <el-radio-group v-model="form.exec_mode">
            <el-radio value="once">单次执行</el-radio>
            <el-radio value="daily">每天循环</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="执行时间">
          <el-date-picker
            v-if="form.exec_mode === 'once'"
            v-model="form.exec_datetime"
            type="datetime"
            placeholder="选择执行时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
          <el-time-picker
            v-else
            v-model="form.exec_time"
            placeholder="选择时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="采集地区">
          <div class="region-select">
            <el-switch
              v-model="form.regionsMultiple"
              active-text="多选"
              inactive-text="单选"
              style="margin-right: 10px;"
            />
            <el-cascader
              v-model="form.regions"
              :options="regionOptions"
              :placeholder="form.regionsMultiple ? '选择省/市/区（可多选）' : '选择省/市/区'"
              :props="{
                value: 'value',
                label: 'label',
                children: 'children',
                multiple: form.regionsMultiple
              }"
              :clearable="true"
              :filterable="true"
              :collapse-tags="form.regionsMultiple"
              :style="{ width: '100%' }"
            />
          </div>
          <div class="form-tip">选择要采集的地区，留空则采集全国</div>
        </el-form-item>

        <el-form-item label="最大采集页数">
          <el-input-number v-model="form.max_pages" :min="1" :max="100" />
        </el-form-item>

        <el-form-item label="采集模式">
          <el-radio-group v-model="form.crawl_mode">
            <el-radio value="full">全量采集</el-radio>
            <el-radio value="incremental">增量采集</el-radio>
          </el-radio-group>
          <div class="form-tip">全量采集：采集所有页面；增量采集：仅采集最新数据</div>
        </el-form-item>

        <el-form-item label="搜索关键词">
          <el-select
            v-model="form.keywords"
            multiple
            filterable
            placeholder="请选择关键词"
            style="width: 100%"
            :loading="keywordsLoading"
            clearable
          >
            <el-option
              v-for="kw in availableKeywords"
              :key="kw.id"
              :label="kw.keyword"
              :value="kw.keyword"
            >
              <div class="keyword-option">
                <span>{{ kw.keyword }}</span>
                <el-tag size="small" type="info">{{ getKeywordCategoryLabel(kw.category) }}</el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">从关键词库中选择，支持多选</div>
        </el-form-item>

        <el-divider content-position="left">智能匹配设置</el-divider>

        <el-form-item label="自动匹配资质">
          <el-switch v-model="form.auto_match" />
          <span class="form-tip">采集完成后自动用企业条件匹配招标公告</span>
        </el-form-item>

        <el-form-item label="选择企业">
          <el-select
            v-model="form.enterprise_ids"
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
          <div class="form-tip">选择参与资质匹配的企业，留空则使用所有企业</div>
        </el-form-item>

        <el-form-item label="自动删除不匹配">
          <el-switch v-model="form.auto_delete_unmatched" />
          <span class="form-tip">不满足企业条件的项目自动删除，满足条件的进入投标报名</span>
        </el-form-item>

        <el-form-item label="匹配阈值">
          <el-slider v-model="form.match_threshold" :min="0" :max="1" :step="0.1" show-input />
          <span class="form-tip">低于此阈值的视为不匹配</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="logDialogVisible"
      :title="`执行日志 - ${currentSchedule?.name}`"
      width="900px"
    >
      <el-table :data="logs" v-loading="logsLoading" max-height="400">
        <el-table-column prop="started_at" label="执行时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="result_count" label="采集数量" width="90" />
        <el-table-column prop="matched_count" label="匹配数量" width="90" />
        <el-table-column prop="deleted_count" label="删除数量" width="90" />
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-dialog>

    <ProgressTracker
      v-if="currentTaskId && progressVisible"
      :task-id="currentTaskId"
      :task-name="`采集任务: ${currentSchedule?.name || ''}`"
      :visible="progressVisible"
      @close="onProgressClose"
      @cancel="onProgressCancel"
      @retry="onProgressRetry"
    />

    <ConfirmDialog
      v-model="deleteDialogVisible"
      title="确认删除"
      :message="`确定要删除采集计划「${deleteTarget?.name}」吗？`"
      type="danger"
      :loading="deleteLoading"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, QuestionFilled, Check, Close, Loading } from '@element-plus/icons-vue'
import { PageHeader, ConfirmDialog, ProgressTracker } from '@/components'
import { crawlerApi } from '@/api/crawler'
import { tenderApi } from '@/api/tender'
import { enterpriseApi } from '@/api/enterprise'
import { regionData } from '@/utils/regions'
import { formatDate, formatDateTime } from '@/utils/date'

const WEBSITE_TYPE_MAP = {
  'government': '政府采购网',
  'enterprise': '企业招标平台',
  'construction': '工程建设平台',
  'medical': '医疗器械采购',
  'education': '教育采购平台',
  'other': '其他平台'
}

const loading = ref(false)
const schedules = ref([])
const templates = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const keywordsLoading = ref(false)
const availableKeywords = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const currentId = ref(null)
const nameChecking = ref(false)
const nameDuplicate = ref(null)
const nameCheckTimer = ref(null)
const regionOptions = ref(regionData)
const enterpriseList = ref([])
const enterpriseLoading = ref(false)

const inputMode = ref('select')
const selectedCategory = ref(null)
const customProtocol = ref('https://')
const customUrl = ref('')

const templateCategories = [
  { label: '政府采购网', value: 'government' },
  { label: '企业招标平台', value: 'enterprise' },
  { label: '工程建设平台', value: 'construction' },
  { label: '医疗器械采购', value: 'medical' },
  { label: '教育采购平台', value: 'education' },
  { label: '其他平台', value: 'other' }
]

const form = reactive({
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
  match_threshold: 0.6,
  customUrl: ''
})

const validateNameUnique = async (rule, value, callback) => {
  if (!value || !value.trim()) {
    callback(new Error('请输入计划名称'))
    return
  }

  if (nameDuplicate.value === true) {
    callback(new Error('该计划名称已被使用'))
    return
  }

  callback()
}

const validateWebsiteTemplate = (rule, value, callback) => {
  if (inputMode.value === 'select') {
    if (!value) {
      callback(new Error('请选择网站模板'))
    } else {
      callback()
    }
  } else if (inputMode.value === 'category') {
    if (!selectedCategory.value) {
      callback(new Error('请选择模板分类'))
    } else if (!value) {
      callback(new Error('请选择网站模板'))
    } else {
      callback()
    }
  } else {
    callback()
  }
}

const validateCrontab = (rule, value, callback) => {
  if (!value || !value.trim()) {
    callback(new Error('请输入执行时间'))
    return
  }

  const parts = value.trim().split(/\s+/)
  if (parts.length !== 5) {
    callback(new Error('Cron表达式格式错误，应为5个字段：分 时 日 月 周'))
    return
  }

  callback()
}

const rules = {
  name: [
    { required: true, message: '请输入计划名称', trigger: 'blur' },
    { validator: validateNameUnique, trigger: 'blur' }
  ],
  website_template: [
    { validator: validateWebsiteTemplate, trigger: 'change' }
  ],
  crontab: [
    { required: true, message: '请输入执行时间', trigger: 'blur' },
    { validator: validateCrontab, trigger: 'blur' }
  ]
}

const filteredTemplatesByCategory = computed(() => {
  if (!selectedCategory.value) return []
  return templates.value.filter(t => t.website_type === selectedCategory.value)
})

const getTypeLabel = (type) => {
  return WEBSITE_TYPE_MAP[type] || type || '其他'
}

const getKeywordCategoryLabel = (category) => {
  const labels = {
    industry: '行业',
    region: '地区',
    product: '产品',
    exclude: '排除'
  }
  return labels[category] || category || '其他'
}

const checkNameDuplicate = async () => {
  if (!form.name || !form.name.trim()) {
    nameDuplicate.value = null
    return
  }

  if (nameCheckTimer.value) {
    clearTimeout(nameCheckTimer.value)
  }

  nameCheckTimer.value = setTimeout(async () => {
    nameChecking.value = true
    try {
      const res = await crawlerApi.checkScheduleNameDuplicate(form.name, currentId.value)
      if (res.data) {
        nameDuplicate.value = res.data.is_duplicate
      }
    } catch (error) {
      console.error('检查名称重复失败:', error)
      nameDuplicate.value = null
    } finally {
      nameChecking.value = false
    }
  }, 300)
}

watch(() => form.name, () => {
  if (nameDuplicate.value !== null) {
    nameDuplicate.value = null
  }
})

watch(inputMode, () => {
  form.website_template = null
  selectedCategory.value = null
  form.customUrl = ''
})

const logDialogVisible = ref(false)
const logsLoading = ref(false)
const logs = ref([])
const currentSchedule = ref(null)

const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)
const deleteLoading = ref(false)

const currentTaskId = ref(null)
const progressVisible = ref(false)

const executeNow = async (row) => {
  row.executing = true
  currentTaskId.value = null
  progressVisible.value = false
  try {
    const res = await crawlerApi.executeCrawlScheduleNow(row.id)
    if (res.data?.task_id) {
      currentTaskId.value = res.data.task_id
      progressVisible.value = true
      ElMessage.info('采集任务已启动，请在进度面板中查看')
    } else {
      ElMessage.success('任务已提交执行')
    }
    row.executing = false
  } catch (error) {
    console.error('执行失败:', error)
    ElMessage.error('执行失败')
    row.executing = false
  }
}

const onProgressClose = () => {
  progressVisible.value = false
  currentTaskId.value = null
  fetchSchedules()
}

const onProgressCancel = (taskId) => {
  ElMessage.warning('任务已取消')
  onProgressClose()
}

const onProgressRetry = (taskId) => {
  if (currentSchedule.value) {
    executeNow(currentSchedule.value)
  }
}

const fetchSchedules = async () => {
  loading.value = true
  try {
    const res = await crawlerApi.getCrawlSchedules({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.data && res.data.list) {
      schedules.value = res.data.list
      pagination.total = res.data.pagination?.total || 0
    } else if (res.data && res.data.results) {
      schedules.value = res.data.results
      pagination.total = res.data.count || 0
    } else if (Array.isArray(res.data)) {
      schedules.value = res.data
      pagination.total = res.data.length
    } else {
      schedules.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('获取采集计划失败:', error)
    ElMessage.error('获取采集计划失败')
  } finally {
    loading.value = false
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
    } else {
      templates.value = []
    }
  } catch (error) {
    console.error('获取网站模板失败:', error)
  }
}

const fetchKeywords = async () => {
  keywordsLoading.value = true
  try {
    const res = await tenderApi.getKeywords({})
    if (res.data && res.data.list) {
      availableKeywords.value = res.data.list
    } else if (Array.isArray(res.data)) {
      availableKeywords.value = res.data
    } else {
      availableKeywords.value = []
    }
  } catch (error) {
    console.error('获取关键词列表失败:', error)
  } finally {
    keywordsLoading.value = false
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

const showCreateDialog = () => {
  isEdit.value = false
  currentId.value = null
  inputMode.value = 'select'
  selectedCategory.value = null
  customProtocol.value = 'https://'
  customUrl.value = ''
  nameDuplicate.value = null
  resetForm()
  form.exec_mode = 'daily'
  form.exec_datetime = null
  form.exec_time = '08:00:00'
  form.regionsMultiple = false
  dialogVisible.value = true
  fetchKeywords()
  loadEnterprises()
}

const showEditDialog = async (row) => {
  isEdit.value = true
  currentId.value = row.id
  inputMode.value = 'select'
  selectedCategory.value = null
  customProtocol.value = 'https://'
  customUrl.value = ''
  nameDuplicate.value = null

  try {
    const res = await crawlerApi.getCrawlScheduleDetail(row.id)
    const data = res.data
    form.name = data.name || ''
    form.website_template = data.website_template
    form.crontab = data.crontab || '0 8 * * *'
    form.max_pages = data.max_pages || 10
    form.crawl_mode = data.crawl_mode || 'full'
    form.keywords = data.keywords || []
    form.regions = data.regions || []
    form.regionsMultiple = data.regions_multiple === true
    form.enterprise_ids = data.enterprise_ids || []
    form.auto_match = data.auto_match !== false
    form.auto_delete_unmatched = data.auto_delete_unmatched === true
    form.match_threshold = data.match_threshold || 0.6

    if (data.exec_datetime) {
      form.exec_mode = 'once'
      form.exec_datetime = data.exec_datetime
      form.exec_time = null
    } else {
      form.exec_mode = 'daily'
      form.exec_datetime = null
      const parts = (data.crontab || '0 8 * * *').split(' ')
      if (parts.length >= 2) {
        const hour = parts[1].padStart(2, '0')
        const minute = parts[0].padStart(2, '0')
        form.exec_time = `${hour}:${minute}:00`
      } else {
        form.exec_time = '08:00:00'
      }
    }
  } catch (error) {
    ElMessage.error('获取计划详情失败')
    return
  }
  dialogVisible.value = true
  fetchKeywords()
  loadEnterprises()
}

const resetForm = () => {
  form.name = ''
  form.website_template = null
  form.crontab = '0 6 * * *'
  form.max_pages = 10
  form.crawl_mode = 'full'
  form.keywords = []
  form.auto_match = true
  form.auto_delete_unmatched = false
  form.match_threshold = 0.6
  form.customUrl = ''
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (nameDuplicate.value === true) {
      ElMessage.error('该计划名称已被使用，请使用其他名称')
      return
    }

    submitting.value = true
    try {
      const submitData = { ...form }
      delete submitData.customUrl
      delete submitData.exec_mode
      delete submitData.exec_time
      submitData.regions_multiple = submitData.regionsMultiple
      delete submitData.regionsMultiple

      if (form.exec_mode === 'once') {
        submitData.exec_datetime = form.exec_datetime
        submitData.crontab = null
      } else {
        submitData.exec_datetime = null
        if (form.exec_time) {
          const [hour, minute] = form.exec_time.split(':')
          submitData.crontab = `${minute} ${hour} * * *`
        }
      }

      if (isEdit.value) {
        await crawlerApi.updateCrawlSchedule(currentId.value, submitData)
        ElMessage.success('更新成功')
      } else {
        await crawlerApi.createCrawlSchedule(submitData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchSchedules()
    } catch (error) {
      console.error('保存失败:', error)
      let errorMsg = '保存失败'
      if (error.response?.data) {
        const data = error.response.data
        if (typeof data === 'string') {
          errorMsg = data
        } else if (data.message) {
          errorMsg = data.message
        } else if (Array.isArray(data)) {
          errorMsg = data.join(', ')
        } else if (typeof data === 'object') {
          const firstError = Object.values(data).find(v => v && (Array.isArray(v) ? v.length : true))
          if (firstError) {
            errorMsg = Array.isArray(firstError) ? firstError[0] : firstError
          }
        }
      } else if (error.message) {
        errorMsg = error.message
      }
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = (row) => {
  deleteDialogVisible.value = true
  deleteTarget.value = row
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await crawlerApi.deleteCrawlSchedule(deleteTarget.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    fetchSchedules()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  } finally {
    deleteLoading.value = false
  }
}

const toggleStatus = async (row) => {
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

const parseCrontab = (crontab) => {
  const parts = crontab.split(/\s+/)
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

const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '-'
  if (seconds < 1) {
    return `${(seconds * 1000).toFixed(0)}毫秒`
  }
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  }
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(1)
  return `${mins}分${secs}秒`
}

const parseCrontabDesc = (crontab) => {
  if (!crontab) return ''
  const parts = crontab.trim().split(/\s+/)
  if (parts.length !== 5) return ''

  const [min, hour, day, month, week] = parts

  if (min === '*' && hour === '*' && day === '*' && month === '*' && week === '*') {
    return '每分钟执行'
  }
  if (min === '0' && hour === '*' && day === '*' && month === '*' && week === '*') {
    return '每小时整点执行'
  }
  if (min === '0' && hour !== '*' && day === '*' && month === '*' && week === '*') {
    return `每天 ${hour} 点执行`
  }
  if (min === '0' && hour === '0' && day === '*' && month === '*' && week === '*') {
    return '每天凌晨执行'
  }
  if (day === '*' && month === '*' && week !== '*') {
    return `每周${['日', '一', '二', '三', '四', '五', '六'][parseInt(week)]}执行`
  }
  if (min.startsWith('*/')) {
    return `每 ${min.slice(2)} 分钟执行`
  }

  return ''
}

const viewLogs = async (row) => {
  currentSchedule.value = row
  logDialogVisible.value = true
  logsLoading.value = true
  try {
    const res = await crawlerApi.getCrawlScheduleLogs(row.id)
    logs.value = res.data?.list || res.data || []
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    logsLoading.value = false
  }
}

onMounted(() => {
  fetchSchedules()
  fetchTemplates()
})
</script>

<style lang="scss" scoped>
.page-container {
  padding: 16px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.content-card {
  margin-top: 0;
  border-radius: 8px;
}

.pagination {
  margin-top: 20px;
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

.template-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.keyword-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.name-error {
  color: #F56C6C;
  font-size: 12px;
  margin-top: 4px;
  line-height: 1.4;
}
</style>

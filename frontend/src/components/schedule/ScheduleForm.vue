<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="140px"
    class="schedule-form"
  >
    <el-form-item label="计划名称" prop="name">
      <el-input
        v-model="formData.name"
        placeholder="请输入采集计划名称"
        maxlength="50"
        show-word-limit
        :disabled="readonly"
      />
    </el-form-item>

    <el-form-item label="网站模板" prop="website_template">
      <el-select
        v-model="formData.website_template"
        placeholder="请选择网站模板"
        style="width: 100%"
        filterable
        :disabled="readonly"
      >
        <el-option
          v-for="template in templates"
          :key="template.id"
          :label="template.name"
          :value="template.id"
        >
          <span>{{ template.name }}</span>
          <span class="template-code">{{ template.code }}</span>
        </el-option>
      </el-select>
    </el-form-item>

    <el-form-item label="执行时间" prop="crontab">
      <el-date-picker
        v-model="formData.exec_datetime"
        type="datetime"
        placeholder="选择执行时间"
        format="YYYY-MM-DD HH:mm"
        value-format="YYYY-MM-DD HH:mm:ss"
        :disabled="readonly"
        style="width: 100%"
      />
      <div class="form-tip">
        <el-icon><Clock /></el-icon>
        <span>选择具体时间后，系统将在该时间执行一次采集任务</span>
      </div>
    </el-form-item>

    <el-form-item label="采集地区" prop="regions">
      <el-cascader
        v-model="formData.regions"
        :options="regionOptions"
        placeholder="选择省/市/区（可多选）"
        clearable
        filterable
        multiple
        collapse-tags
        collapse-tags-tooltip
        :props="{
          value: 'value',
          label: 'label',
          children: 'children'
        }"
        style="width: 100%"
        :disabled="readonly"
      />
      <div class="form-tip">
        <el-icon><Location /></el-icon>
        <span>选择要采集的地区，留空则采集全国</span>
      </div>
    </el-form-item>

    <el-form-item label="采集模式" prop="crawl_mode">
      <el-radio-group v-model="formData.crawl_mode" :disabled="readonly">
        <el-radio value="full">
          <span class="radio-label">全量采集</span>
          <span class="radio-desc">采集所有可获取的数据</span>
        </el-radio>
        <el-radio value="incremental">
          <span class="radio-label">增量采集</span>
          <span class="radio-desc">仅采集最新数据（推荐）</span>
        </el-radio>
      </el-radio-group>
      <div class="form-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>增量采集会自动跳过已采集过的数据，仅采集新增内容</span>
      </div>
    </el-form-item>

    <el-form-item label="搜索关键词" prop="keywords">
      <div class="keyword-section">
        <div class="keyword-tabs">
          <el-radio-group v-model="keywordTab" size="small" :disabled="readonly">
            <el-radio-button value="all">全部</el-radio-button>
            <el-radio-button value="industry">行业</el-radio-button>
            <el-radio-button value="region">地区</el-radio-button>
            <el-radio-button value="product">产品</el-radio-button>
          </el-radio-group>
        </div>
        <div class="keyword-list">
          <el-checkbox-group v-model="formData.keywords">
            <el-checkbox
              v-for="kw in filteredKeywords"
              :key="kw.id"
              :value="kw.keyword"
              :disabled="readonly || kw.is_active === false"
            >
              <span class="keyword-text">{{ kw.keyword }}</span>
              <el-tag v-if="!kw.is_active" type="info" size="small">已禁用</el-tag>
            </el-checkbox>
          </el-checkbox-group>
          <el-empty v-if="filteredKeywords.length === 0" description="暂无关键词" :image-size="60" />
        </div>
        <div class="keyword-selected-info" v-if="formData.keywords.length > 0">
          <el-icon><Collection /></el-icon>
          <span>已选择 {{ formData.keywords.length }} 个关键词</span>
        </div>
      </div>
      <div class="form-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>选择要搜索的关键词，留空则使用系统默认关键词</span>
      </div>
    </el-form-item>

    <el-divider content-position="left" v-if="showMatchSettings">
      <span class="divider-title">智能匹配设置</span>
    </el-divider>

    <el-form-item label="自动匹配资质" v-if="showMatchSettings">
      <div class="switch-with-desc">
        <el-switch v-model="formData.auto_match" :disabled="readonly" />
        <span class="switch-desc">采集完成后自动用企业条件匹配招标公告</span>
      </div>
    </el-form-item>

    <el-form-item label="选择企业" v-if="showMatchSettings && formData.auto_match" prop="enterprise_ids">
      <el-select
        v-model="formData.enterprise_ids"
        placeholder="选择用于资质匹配的企业"
        multiple
        filterable
        clearable
        style="width: 100%"
        :loading="enterpriseLoading"
        :disabled="readonly"
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
      <div class="form-tip">
        <el-icon><OfficeBuilding /></el-icon>
        <span>选择参与资质匹配的企业，留空则使用所有企业</span>
      </div>
    </el-form-item>

    <el-form-item label="自动删除不匹配" v-if="showMatchSettings && formData.auto_match">
      <div class="switch-with-desc">
        <el-switch v-model="formData.auto_delete_unmatched" :disabled="readonly" />
        <span class="switch-desc">不满足企业条件的项目自动删除，满足条件的进入投标报名</span>
      </div>
    </el-form-item>

    <el-form-item label="匹配阈值" v-if="showMatchSettings && formData.auto_match">
      <div class="threshold-section">
        <el-slider
          v-model="formData.match_threshold"
          :min="0"
          :max="1"
          :step="0.1"
          :format-tooltip="formatThreshold"
          show-input
          :disabled="readonly"
        />
        <div class="threshold-labels">
          <span>宽松</span>
          <span>严格</span>
        </div>
      </div>
    </el-form-item>

    <el-alert
      v-if="showMatchSettings && formData.auto_match"
      type="info"
      :closable="false"
      class="match-info-alert"
    >
      <template #default>
        <div class="match-info-content">
          <p><strong>匹配说明：</strong></p>
          <p>• 系统将根据您的企业资质条件与招标公告进行匹配</p>
          <p>• 满足条件 → 进入投标报名流程</p>
          <p>• 不满足条件 → 自动过滤删除</p>
          <p>• <strong>自动删除不匹配数据功能默认启用</strong>，可在详情页查看已删除记录</p>
        </div>
      </template>
    </el-alert>

    <el-form-item class="form-actions" v-if="!readonly">
      <slot name="actions">
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          <el-icon v-if="!loading"><Check /></el-icon>
          {{ isEdit ? '保存修改' : '创建计划' }}
        </el-button>
      </slot>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import {
  Clock,
  InfoFilled,
  Collection,
  Check,
  Location,
  OfficeBuilding
} from '@element-plus/icons-vue'
import { regionData } from '@/utils/regions'
import { enterpriseApi } from '@/api/enterprise'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  templates: {
    type: Array,
    default: () => []
  },
  keywords: {
    type: Array,
    default: () => []
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  showMatchSettings: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

const formRef = ref(null)
const keywordTab = ref('all')
const regionOptions = ref(regionData)
const enterpriseList = ref([])
const enterpriseLoading = ref(false)

const loadEnterprises = async () => {
  enterpriseLoading.value = true
  try {
    const res = await enterpriseApi.getEnterprises({ page_size: 100 })
    enterpriseList.value = res?.results || res?.list || []
  } catch (error) {
    console.error('获取企业列表失败:', error)
    enterpriseList.value = []
  } finally {
    enterpriseLoading.value = false
  }
}

onMounted(() => {
  loadEnterprises()
})

const timeOptions = [
  { value: '0 6 * * *', label: '每天早上 6:00', description: '凌晨采集，优先推荐' },
  { value: '0 8 * * *', label: '每天早上 8:00', description: '工作日开始一天采集' },
  { value: '0 12 * * *', label: '每天中午 12:00', description: '午休时间采集' },
  { value: '0 20 * * *', label: '每天晚上 20:00', description: '晚间采集最新公告' },
  { value: '30 6 * * 1-5', label: '工作日早上 6:30', description: '仅工作日执行' },
  { value: '0 */2 * * *', label: '每 2 小时', description: '每2小时执行一次' },
  { value: '0 */4 * * *', label: '每 4 小时', description: '每4小时执行一次' },
  { value: '0 0 * * 0', label: '每周日凌晨', description: '每周执行一次' }
]

const formData = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const filteredKeywords = computed(() => {
  if (keywordTab.value === 'all') {
    return props.keywords
  }
  return props.keywords.filter(kw => kw.category === keywordTab.value)
})

const formRules = {
  name: [
    { required: true, message: '请输入计划名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  website_template: [
    { required: true, message: '请选择网站模板', trigger: 'change' }
  ],
  crontab: [
    { required: true, message: '请选择执行时间', trigger: 'change' }
  ],
  crawl_mode: [
    { required: true, message: '请选择采集模式', trigger: 'change' }
  ]
}

const formatThreshold = (val) => {
  if (val <= 0.3) return '非常宽松'
  if (val <= 0.5) return '较宽松'
  if (val <= 0.7) return '适中'
  if (val <= 0.9) return '较严格'
  return '非常严格'
}

const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    emit('submit')
  } catch (error) {
    return
  }
}

const validate = async () => {
  return await formRef.value.validate()
}

defineExpose({
  validate
})
</script>

<style scoped lang="scss">
.schedule-form {
  max-width: 700px;
  padding: 20px 0;

  :deep(.el-form-item__label) {
    font-weight: 500;
  }
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  color: #909399;
  font-size: 12px;

  .el-icon {
    font-size: 14px;
  }
}

.template-code {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.time-option {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .time-label {
    font-weight: 500;
  }

  .time-desc {
    font-size: 12px;
    color: #909399;
  }
}

.radio-label {
  font-weight: 500;
  margin-right: 8px;
}

.radio-desc {
  color: #909399;
  font-size: 12px;
}

.keyword-section {
  width: 100%;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px;
  background: var(--el-fill-color-light);
}

.keyword-tabs {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.keyword-list {
  max-height: 200px;
  overflow-y: auto;

  :deep(.el-checkbox-group) {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :deep(.el-checkbox) {
    margin-right: 0;
    height: auto;
    padding: 4px 0;

    .el-checkbox__label {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

.keyword-text {
  word-break: break-all;
}

.keyword-selected-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  color: var(--el-color-primary);
  font-size: 14px;
  font-weight: 500;
}

.switch-with-desc {
  display: flex;
  align-items: center;
  gap: 12px;

  .switch-desc {
    color: #606266;
    font-size: 14px;
  }
}

.threshold-section {
  width: 100%;
  padding-right: 120px;

  .threshold-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
    color: #909399;
    font-size: 12px;
  }
}

.divider-title {
  font-weight: 600;
  color: #303133;
}

.match-info-alert {
  margin: 16px 0;

  .match-info-content {
    line-height: 1.8;
    font-size: 14px;

    p {
      margin: 4px 0;
    }
  }
}

.form-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--el-border-color-lighter);

  :deep(.el-form-item__content) {
    justify-content: flex-end;
  }
}

:deep(.el-empty) {
  padding: 20px 0;
}

.enterprise-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;

  .enterprise-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>

<template>
  <div class="page-container">
    <PageHeader
      title="编辑采集计划"
      subtitle="修改定时任务配置"
    >
      <template #actions>
        <el-button @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </template>
    </PageHeader>

    <el-card class="content-card" v-loading="loading">
      <ScheduleForm
        ref="scheduleFormRef"
        v-model="form"
        :templates="templates"
        :keywords="keywords"
        :is-edit="true"
        :loading="submitting"
        @submit="handleSubmit"
        @cancel="handleBack"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { PageHeader } from '@/components'
import ScheduleForm from '@/components/schedule/ScheduleForm.vue'
import { crawlerApi } from '@/api/crawler'
import { tenderApi } from '@/api/tender'
import { parseListResponse } from '@/utils/response-parser'
import { useFormDraft } from '@/composables/useFormDraft'

const router = useRouter()
const route = useRoute()
const scheduleFormRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const templates = ref([])
const keywords = ref([])
const scheduleId = ref(null)

const form = reactive({
  name: '',
  website_template: null,
  crontab: '0 6 * * *',
  crawl_mode: 'incremental',
  max_pages: 10,
  keywords: [],
  regions: [],
  regionsMultiple: false,
  enterprise_ids: [],
  exec_datetime: null,
  auto_match: true,
  auto_delete_unmatched: true,
  match_threshold: 0.6
})

const { clearDraft } = useFormDraft(form, {
  key: 'schedule:edit',
  context: () => ({ scheduleId: scheduleId.value })
})

const fetchSchedule = async () => {
  loading.value = true
  try {
    const res = await crawlerApi.getCrawlScheduleDetail(scheduleId.value)
    const schedule = res.data

    if (schedule) {
      Object.assign(form, {
        name: schedule.name,
        website_template: schedule.website_template,
        crontab: schedule.crontab,
        crawl_mode: schedule.crawl_mode || 'incremental',
        max_pages: schedule.max_pages || 10,
        keywords: schedule.keywords || [],
        regions: schedule.regions || [],
        regionsMultiple: schedule.regions_multiple === true,
        enterprise_ids: schedule.enterprise_ids || [],
        exec_datetime: schedule.exec_datetime || null,
        auto_match: schedule.auto_match,
        auto_delete_unmatched: schedule.auto_delete_unmatched,
        match_threshold: schedule.match_threshold || 0.6
      })
    }
  } catch (error) {
    console.error('获取采集计划详情失败:', error)
    ElMessage.error('获取采集计划详情失败')
  } finally {
    loading.value = false
  }
}

const fetchTemplates = async () => {
  try {
    const res = await crawlerApi.getWebsiteTemplates({ page_size: 100 })
    const { list } = parseListResponse(res)
    templates.value = list
  } catch (error) {
    console.error('获取网站模板失败:', error)
  }
}

const fetchKeywords = async () => {
  try {
    const res = await tenderApi.getKeywords({})
    const { list } = parseListResponse(res)
    keywords.value = list
  } catch (error) {
    console.error('获取关键词列表失败:', error)
  }
}

const handleBack = () => {
  router.push('/schedules')
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    const submitData = {
      ...form,
      auto_delete_unmatched: true
    }
    await crawlerApi.updateCrawlSchedule(scheduleId.value, submitData)
    clearDraft()
    ElMessage.success('采集计划更新成功')
    router.push('/schedules')
  } catch (error) {
    console.error('更新失败:', error)
    let errorMsg = '更新采集计划失败'
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
}

onMounted(() => {
  scheduleId.value = parseInt(route.params.id || route.query.id || 0)
  if (scheduleId.value) {
    fetchSchedule()
  }
  fetchTemplates()
  fetchKeywords()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;
  min-height: calc(100vh - 60px);
  background-color: #F1F5F9;
}

.content-card {
  border-radius: 8px;
}
</style>

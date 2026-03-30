<template>
  <div class="page-container">
    <PageHeader
      title="新建采集计划"
      subtitle="配置定时任务自动采集招标信息"
    >
      <template #actions>
        <el-button @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </template>
    </PageHeader>

    <el-card class="content-card">
      <ScheduleForm
        ref="scheduleFormRef"
        v-model="form"
        :templates="templates"
        :keywords="keywords"
        :is-edit="false"
        :loading="submitting"
        @submit="handleSubmit"
        @cancel="handleBack"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { PageHeader } from '@/components'
import ScheduleForm from '@/components/schedule/ScheduleForm.vue'
import { crawlerApi } from '@/api/crawler'
import { tenderApi } from '@/api/tender'

const router = useRouter()
const scheduleFormRef = ref(null)
const submitting = ref(false)
const templates = ref([])
const keywords = ref([])

const form = reactive({
  name: '',
  website_template: null,
  crontab: '0 6 * * *',
  crawl_mode: 'incremental',
  keywords: [],
  regions: [],
  enterprise_ids: [],
  exec_datetime: null,
  auto_match: true,
  auto_delete_unmatched: true,
  match_threshold: 0.6
})

const fetchTemplates = async () => {
  try {
    const res = await crawlerApi.getWebsiteTemplates({ page_size: 100 })
    if (res.data) {
      templates.value = res.data.list || res.data.results || res.data || []
    }
  } catch (error) {
    console.error('获取网站模板失败:', error)
    ElMessage.error('获取网站模板失败')
  }
}

const fetchKeywords = async () => {
  try {
    const res = await tenderApi.getKeywords({})
    if (res.data) {
      keywords.value = res.data.list || res.data.results || res.data || []
    }
  } catch (error) {
    console.error('获取关键词列表失败:', error)
    ElMessage.error('获取关键词列表失败')
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
    await crawlerApi.createCrawlSchedule(submitData)
    ElMessage.success('采集计划创建成功')
    router.push('/schedules')
  } catch (error) {
    console.error('创建失败:', error)
    ElMessage.error(error.response?.data?.message || '创建采集计划失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchTemplates()
  fetchKeywords()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 16px;
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
}

.content-card {
  border-radius: 8px;
}
</style>

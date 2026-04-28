<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">招标详情</h3>
      <el-button @click="goBack">返回列表</el-button>
    </div>
    
    <el-descriptions :column="2" border>
      <el-descriptions-item label="项目名称" :span="2">
        {{ tender.title }}
      </el-descriptions-item>
      <el-descriptions-item label="项目编号">
        {{ tender.project_code || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="发布日期">
        {{ tender.publish_date || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="截止日期">
        {{ tender.deadline_date || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="开标日期">
        {{ tender.open_date || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="地区">
        {{ tender.region || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="行业">
        {{ tender.industry || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="预算金额">
        {{ tender.budget ? `¥${tender.budget}` : '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getStatusType(tender.status)">
          {{ getStatusText(tender.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="采购人">
        {{ tender.purchaser_name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="采购人电话">
        {{ tender.purchaser_phone || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="代理机构">
        {{ tender.agency_name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="代理机构电话">
        {{ tender.agency_phone || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="来源链接" v-if="tender.source_url">
        <el-button type="primary" link @click="viewSourceContent">查看原始公告</el-button>
      </el-descriptions-item>
      <el-descriptions-item label="项目描述" :span="2">
        <div v-if="tender.description" class="tender-description" v-html="sanitizeHtml(tender.description)" />
        <span v-else>-</span>
      </el-descriptions-item>
    </el-descriptions>
    
    <div class="section-title mt-20">相关文件</div>
    <el-table :data="tender.files || []" style="width: 100%">
      <el-table-column prop="file_name" label="文件名称" />
      <el-table-column prop="file_type" label="文件类型" width="120" />
      <el-table-column prop="created_at" label="上传时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="primary" link @click="downloadFile(row)">下载</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="action-buttons mt-20">
      <el-button type="primary" @click="goToGenerate">生成标书</el-button>
      <el-button type="success" @click="createBidRecord">创建投标记录</el-button>
      <el-button 
        :type="tender.is_favorite ? 'warning' : 'default'" 
        @click="toggleFavorite"
      >
        {{ tender.is_favorite ? '取消收藏' : '收藏项目' }}
      </el-button>
    </div>

    <el-dialog
      v-model="sourcePreviewVisible"
      title="查看原始公告"
      width="85%"
      top="3vh"
      :close-on-click-modal="false"
      destroy-on-close
      @close="closeSourcePreview"
    >
      <div class="source-preview-container">
        <div v-if="sourcePreviewLoading" class="source-preview-loading">
          <el-icon class="is-loading" :size="32"><Refresh /></el-icon>
          <p>正在获取公告内容，请稍候...</p>
          <p class="source-preview-tip">首次加载可能需要10-20秒</p>
        </div>
        <div v-else-if="sourcePreviewContent" class="source-preview-content" v-html="sourcePreviewContent" />
        <div v-else-if="sourcePreviewError" class="source-preview-error">
          <el-icon :size="48" color="#64748B"><WarningFilled /></el-icon>
          <p>{{ sourcePreviewError }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeSourcePreview">关闭</el-button>
        <el-button type="primary" @click="openInNewWindow">在新窗口打开</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, WarningFilled } from '@element-plus/icons-vue'
import DOMPurify from 'dompurify'
import { tenderApi } from '@/api/tender'
import { getTenderStatusType, getTenderStatusText } from '@/store/constants'

const route = useRoute()
const router = useRouter()

const tender = ref({})

const getStatusType = getTenderStatusType
const getStatusText = getTenderStatusText

const sanitizeHtml = (html) => {
  if (!html) return '-'
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code', 'a', 'span', 'div', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption', 'colgroup', 'col', 'img', 'hr', 'dl', 'dt', 'dd', 'sup', 'sub'],
    ALLOWED_ATTR: ['href', 'title', 'class', 'style', 'src', 'alt', 'colspan', 'rowspan', 'width', 'height', 'border', 'cellpadding', 'cellspacing']
  })
}

const fetchTenderDetail = async () => {
  try {
    const res = await tenderApi.getDetail(route.params.id)
    tender.value = res.data
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

const goBack = () => {
  router.back()
}

const downloadFile = (file) => {
  if (file.file_url) {
    window.open(file.file_url, '_blank')
  }
}

const goToGenerate = () => {
  router.push({
    path: '/documents/generate',
    query: { tender_id: tender.value.id }
  })
}

const createBidRecord = () => {
  ElMessage.success('请前往投标记录模块创建')
  router.push('/bids')
}

const toggleFavorite = async () => {
  try {
    await tenderApi.favorite(tender.value.id)
    tender.value.is_favorite = !tender.value.is_favorite
    ElMessage.success(tender.value.is_favorite ? '收藏成功' : '取消收藏成功')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const sourcePreviewVisible = ref(false)
const sourcePreviewLoading = ref(false)
const sourcePreviewContent = ref('')
const sourcePreviewError = ref('')

const viewSourceContent = async () => {
  if (!tender.value.source_url) return
  sourcePreviewVisible.value = true
  sourcePreviewLoading.value = true
  sourcePreviewContent.value = ''
  sourcePreviewError.value = ''

  try {
    const res = await tenderApi.getSourceContent(tender.value.id)
    const data = res.data || res
    if (data && data.content) {
      sourcePreviewContent.value = sanitizeContentHtml(data.content)
      if (data.from_cache === false) {
        tender.value.description = data.content
      }
    } else {
      sourcePreviewError.value = '未能获取到公告内容'
    }
  } catch (error) {
    console.error('获取公告内容失败:', error)
    sourcePreviewError.value = '获取公告内容失败，请尝试在新窗口打开查看'
  } finally {
    sourcePreviewLoading.value = false
  }
}

const sanitizeContentHtml = (html) => {
  if (!html) return ''
  return html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/javascript:/gi, '')
}

const openInNewWindow = () => {
  if (tender.value.source_url) {
    window.open(tender.value.source_url, '_blank', 'noopener,noreferrer')
  }
}

const closeSourcePreview = () => {
  sourcePreviewVisible.value = false
  sourcePreviewLoading.value = false
  sourcePreviewContent.value = ''
  sourcePreviewError.value = ''
}

onMounted(() => {
  fetchTenderDetail()
})
</script>

<style lang="scss" scoped>
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 15px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.tender-description {
  max-height: 500px;
  overflow-y: auto;
  line-height: 1.8;
  word-wrap: break-word;

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
  }

  :deep(td),
  :deep(th) {
    border: 1px solid #E2E8F0;
    padding: 8px 12px;
    text-align: left;
  }

  :deep(img) {
    max-width: 100%;
    height: auto;
  }
}

.source-preview-container {
  position: relative;
  width: 100%;
  min-height: 300px;
  max-height: 75vh;
  overflow-y: auto;
}

.source-preview-content {
  padding: 20px;
  line-height: 1.8;
  color: #1E293B;
  font-size: 14px;
  word-wrap: break-word;

  :deep(table) {
    border-collapse: collapse;
    width: 100%;
    margin: 10px 0;
  }

  :deep(td),
  :deep(th) {
    border: 1px solid #E2E8F0;
    padding: 8px 12px;
    text-align: left;
  }

  :deep(img) {
    max-width: 100%;
    height: auto;
  }

  :deep(a) {
    color: #3B82F6;
    text-decoration: none;
  }
}

.source-preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 8px;
  color: #64748B;
  font-size: 14px;
}

.source-preview-tip {
  font-size: 12px;
  color: #CBD5E1;
}

.source-preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
  color: #64748B;
  font-size: 14px;
}
</style>

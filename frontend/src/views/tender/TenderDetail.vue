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
      <el-descriptions-item label="项目描述" :span="2">
        <div v-html="tender.description || '-'" />
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { tenderApi } from '@/api/tender'
import { getTenderStatusType, getTenderStatusText } from '@/store/constants'

const route = useRoute()
const router = useRouter()

const tender = ref({})

const getStatusType = getTenderStatusType
const getStatusText = getTenderStatusText

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

onMounted(() => {
  fetchTenderDetail()
})
</script>

<style lang="scss" scoped>
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}
</style>

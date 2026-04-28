<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">投标详情</h3>
      <el-button @click="goBack">返回列表</el-button>
    </div>
    
    <el-descriptions :column="2" border>
      <el-descriptions-item label="项目名称" :span="2">
        {{ bidRecord.tender_title }}
      </el-descriptions-item>
      <el-descriptions-item label="投标编号">
        {{ bidRecord.bid_code || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="投标报价">
        {{ bidRecord.bid_price ? `¥${bidRecord.bid_price}` : '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="投标日期">
        {{ bidRecord.bid_date || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="getBidStatusType(bidRecord.status)">
          {{ getBidStatusText(bidRecord.status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="中标概率">
        {{ bidRecord.win_probability ? `${bidRecord.win_probability}%` : '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="竞争对手数量">
        {{ bidRecord.competitor_count || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="投标负责人">
        {{ bidRecord.bid_manager_name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="团队成员">
        {{ bidRecord.team_member_names?.join('、') || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="备注" :span="2">
        {{ bidRecord.notes || '-' }}
      </el-descriptions-item>
    </el-descriptions>
    
    <div v-if="bidRecord.result" class="mt-20">
      <h4 class="section-title">中标结果</h4>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="结果">
          <el-tag :type="bidRecord.result.result_type === 'win' ? 'success' : 'danger'">
            {{ bidRecord.result.result_type === 'win' ? '中标' : '未中标' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="中标单位">
          {{ bidRecord.result.winner_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="中标金额">
          {{ bidRecord.result.winner_price ? `¥${bidRecord.result.winner_price}` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="我方排名">
          {{ bidRecord.result.our_rank || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="公告日期">
          {{ bidRecord.result.announce_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="未中标原因" :span="2">
          {{ bidRecord.result.lose_reason || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
    
    <div v-if="bidRecord.documents?.length" class="mt-20">
      <h4 class="section-title">投标文件</h4>
      <el-table :data="bidRecord.documents">
        <el-table-column prop="name" label="文件名称" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button type="primary" link @click="downloadDoc(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { bidApi } from '@/api/bid'
import { getBidStatusType, getBidStatusText } from '@/store/constants'

const route = useRoute()
const router = useRouter()

const bidRecord = ref({})

const fetchBidDetail = async () => {
  try {
    const res = await bidApi.getDetail(route.params.id)
    bidRecord.value = res.data
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

const goBack = () => {
  router.back()
}

const downloadDoc = (doc) => {
  if (doc.file_url) {
    window.open(doc.file_url, '_blank')
  }
}

onMounted(() => {
  fetchBidDetail()
})
</script>

<style lang="scss" scoped>
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 15px;
}
</style>

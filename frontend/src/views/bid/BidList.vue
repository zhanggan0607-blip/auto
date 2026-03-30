<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">投标记录</h3>
      <el-button type="primary" @click="showCreateDialog">新建投标</el-button>
    </div>

    <el-table v-if="Array.isArray(listPage.list)" :data="listPage.list" v-loading="listPage.loading" @selection-change="listPage.handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="tender_title" label="项目名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="bid_price" label="投标报价" width="120">
        <template #default="{ row }">
          {{ row.bid_price ? `¥${row.bid_price}` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="bid_date" label="投标日期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getBidStatusType(row.status)" size="small">
            {{ getBidStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="win_probability" label="中标概率" width="100">
        <template #default="{ row }">
          {{ row.win_probability ? `${row.win_probability}%` : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" link @click="viewDetail(row.id)">详情</el-button>
          <el-button type="success" link @click="updateResult(row)">录入结果</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="listPage.pagination.page"
        v-model:page-size="listPage.pagination.pageSize"
        :total="listPage.pagination.total"
        layout="total, prev, pager, next"
        @current-change="listPage.handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { bidApi } from '@/api/bid'
import { getBidStatusType, getBidStatusText } from '@/store/constants'
import { useMessage } from '@/composables'
import { useListPage } from '@/composables/useListPage'

const router = useRouter()
const message = useMessage()

const listPage = useListPage({
  fetchApi: (params) => bidApi.getList(params),
  deleteApi: (id) => bidApi.delete(id),
  defaultSearchParams: {},
  onDeleteSuccess: () => {
    message.deleted()
  }
})

const showCreateDialog = () => {
  message.success('请从招标详情页面创建投标记录')
}

const viewDetail = (id) => {
  router.push(`/bids/${id}`)
}

const updateResult = () => {
  message.success('投标结果录入功能开发中')
}

onMounted(() => {
  listPage.fetchData()
})
</script>
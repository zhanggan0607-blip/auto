<template>
  <div class="page-container">
    <PageHeader :title="pageTitle">
      <template #actions>
        <el-button type="primary" @click="showCreateDialog" class="primary-action-btn">
          <el-icon><Plus /></el-icon>
          {{ pageMode === 'bids' ? '新建投标记录' : '添加招标' }}
        </el-button>
      </template>
    </PageHeader>

    <StatCards :stats="statisticsCards" />

    <el-card class="search-card" shadow="never">
      <SearchForm
        :default-values="searchDefaults"
        @search="handleSearch"
        @reset="handleReset"
      >
        <template #default="{ formData }">
          <el-form-item label="项目名称">
            <el-input
              v-model="formData.keyword"
              placeholder="项目名称/编号"
              clearable
              class="search-input"
            />
          </el-form-item>
          <el-form-item label="投标状态">
            <el-select v-model="formData.status" placeholder="请选择" clearable class="search-select">
              <el-option label="准备中" value="preparing" />
              <el-option label="已提交" value="submitted" />
              <el-option label="评审中" value="reviewing" />
              <el-option label="已中标" value="won" />
              <el-option label="未中标" value="lost" />
              <el-option label="已撤回" value="withdrawn" />
            </el-select>
          </el-form-item>
          <el-form-item label="投标日期">
            <el-date-picker
              v-model="formData.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              class="search-date-picker"
            />
          </el-form-item>
        </template>
      </SearchForm>
    </el-card>

    <el-card class="table-card" shadow="never">
      <el-table
        v-if="Array.isArray(listPage.list)"
        :data="listPage.list"
        v-loading="listPage.loading"
        style="width: 100%"
        @selection-change="listPage.handleSelectionChange"
        :row-class-name="tableRowClassName"
      >
        <el-table-column type="selection" width="55" />

        <template v-if="pageMode === 'tenders'">
          <el-table-column prop="title" label="项目名称" min-width="250">
            <template #default="{ row }">
              <div class="project-name-cell">
                <span class="project-title">{{ row.title }}</span>
                <el-tag v-if="row.project_code" size="small" type="info" class="project-code-tag">
                  {{ row.project_code }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="publish_date" label="发布日期" width="120" />
          <el-table-column prop="region" label="地区" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getBidStatusType(row.status)" size="small" class="status-tag">
                {{ getBidStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="原始链接" width="100" align="center">
            <template #default="{ row }">
              <el-button
                type="primary"
                link
                :disabled="!row.source_url"
                @click="openSourceUrl(row.source_url)"
              >
                链接
              </el-button>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link @click="viewDetail(row)" class="action-btn">查看</el-button>
                <el-button type="danger" link @click="handleDeleteConfirm(row)" class="action-btn">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </template>

        <template v-else>
          <el-table-column prop="tender_title" label="项目名称" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="project-name-cell">
                <span class="project-title">{{ row.tender_title }}</span>
                <el-tag v-if="row.tender_project_code" size="small" type="info" class="project-code-tag">
                  {{ row.tender_project_code }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="tender_region" label="地区" width="100">
            <template #default="{ row }">
              <div class="region-cell">
                <el-icon><Location /></el-icon>
                {{ row.tender_region || '-' }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="bid_price" label="投标报价" width="120">
            <template #default="{ row }">
              <span class="price-cell" v-if="row.bid_price">
                ¥{{ Number(row.bid_price).toLocaleString() }}
              </span>
              <span class="empty-cell" v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="bid_date" label="投标日期" width="120" />
          <el-table-column prop="tender_deadline" label="截止日期" width="120" />
          <el-table-column prop="status" label="投标状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getBidStatusType(row.status)" size="small" class="status-tag">
                {{ getBidStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="result_type" label="中标结果" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.result_type" :type="getResultType(row.result_type)" size="small">
                {{ getResultText(row.result_type) }}
              </el-tag>
              <span v-else class="empty-cell">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="win_probability" label="中标概率" width="120">
            <template #default="{ row }">
              <el-progress
                v-if="row.win_probability"
                :percentage="row.win_probability"
                :stroke-width="8"
                :color="getProbabilityColor(row.win_probability)"
              />
              <span v-else class="empty-cell">-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link @click="viewDetail(row)" class="action-btn">详情</el-button>
                <el-button type="warning" link @click="showEditDialog(row)" class="action-btn">编辑</el-button>
                <el-button type="success" link @click="showResultDialog(row)" class="action-btn">结果</el-button>
                <el-button type="danger" link @click="handleDeleteConfirm(row)" class="action-btn">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </template>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="listPage.pagination.page"
          v-model:page-size="listPage.pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="listPage.pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="listPage.handleSizeChange"
          @current-change="listPage.handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="createDialogVisible"
      :title="isEdit ? '编辑投标记录' : '新建投标记录'"
      width="700px"
      :close-on-click-modal="false"
      class="form-dialog"
    >
      <el-form
        ref="bidFormRef"
        :model="bidForm"
        :rules="bidRules"
        label-width="100px"
      >
        <el-form-item label="招标项目" prop="tender_id" v-if="!isEdit">
          <el-select
            v-model="bidForm.tender_id"
            filterable
            remote
            reserve-keyword
            placeholder="请输入关键词搜索招标项目"
            :remote-method="searchTenders"
            :loading="tenderSearchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="item in tenderOptions"
              :key="item.id"
              :label="item.title"
              :value="item.id"
            >
              <span>{{ item.title }}</span>
              <span style="float: right; color: #8492a6; font-size: 12px;">{{ item.project_code }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称" v-if="isEdit">
          <el-input :value="bidForm.tender_title" disabled />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="投标编号" prop="bid_code">
              <el-input v-model="bidForm.bid_code" placeholder="请输入投标编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="投标日期" prop="bid_date">
              <el-date-picker
                v-model="bidForm.bid_date"
                type="date"
                placeholder="选择日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="投标报价" prop="bid_price">
              <el-input-number
                v-model="bidForm.bid_price"
                :min="0"
                :precision="2"
                :controls="false"
                placeholder="请输入投标报价"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="投标状态" prop="status">
              <el-select v-model="bidForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="准备中" value="preparing" />
                <el-option label="已提交" value="submitted" />
                <el-option label="评审中" value="reviewing" />
                <el-option label="已中标" value="won" />
                <el-option label="未中标" value="lost" />
                <el-option label="已撤回" value="withdrawn" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="中标概率" prop="win_probability">
              <el-slider v-model="bidForm.win_probability" :min="0" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="竞争对手" prop="competitor_count">
              <el-input-number
                v-model="bidForm.competitor_count"
                :min="0"
                placeholder="数量"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="投标负责人" prop="bid_manager_id">
          <el-select v-model="bidForm.bid_manager_id" placeholder="请选择负责人" clearable style="width: 100%">
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="团队成员" prop="team_member_ids">
          <el-select
            v-model="bidForm.team_member_ids"
            multiple
            placeholder="请选择团队成员"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="bidForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitBidForm">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="resultDialogVisible"
      title="录入中标结果"
      width="600px"
      :close-on-click-modal="false"
      class="form-dialog"
    >
      <el-form
        ref="resultFormRef"
        :model="resultForm"
        :rules="resultRules"
        label-width="100px"
      >
        <el-form-item label="项目名称">
          <el-input :value="currentBid?.tender_title" disabled />
        </el-form-item>
        <el-form-item label="结果类型" prop="result_type">
          <el-radio-group v-model="resultForm.result_type">
            <el-radio value="win">中标</el-radio>
            <el-radio value="lose">未中标</el-radio>
            <el-radio value="pending">待定</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="中标单位" prop="winner_name">
              <el-input v-model="resultForm.winner_name" placeholder="请输入中标单位名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="中标金额" prop="winner_price">
              <el-input-number
                v-model="resultForm.winner_price"
                :min="0"
                :precision="2"
                :controls="false"
                placeholder="请输入中标金额"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="我方排名" prop="our_rank">
              <el-input-number v-model="resultForm.our_rank" :min="1" placeholder="排名" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="投标单位数" prop="total_bidders">
              <el-input-number v-model="resultForm.total_bidders" :min="1" placeholder="数量" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="公告日期" prop="announce_date">
          <el-date-picker
            v-model="resultForm.announce_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="公告链接" prop="announce_url">
          <el-input v-model="resultForm.announce_url" placeholder="请输入中标公告链接" />
        </el-form-item>
        <el-form-item label="中标原因" prop="win_reason" v-if="resultForm.result_type === 'win'">
          <el-input
            v-model="resultForm.win_reason"
            type="textarea"
            :rows="2"
            placeholder="请输入中标原因分析"
          />
        </el-form-item>
        <el-form-item label="未中标原因" prop="lose_reason" v-if="resultForm.result_type === 'lose'">
          <el-input
            v-model="resultForm.lose_reason"
            type="textarea"
            :rows="2"
            placeholder="请输入未中标原因分析"
          />
        </el-form-item>
        <el-form-item label="经验教训" prop="lessons_learned">
          <el-input
            v-model="resultForm.lessons_learned"
            type="textarea"
            :rows="2"
            placeholder="请输入经验教训总结"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resultDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingResult" @click="submitResultForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Location } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { bidApi } from '@/api/bid'
import { tenderApi } from '@/api/tender'
import { getBidStatusType, getBidStatusText } from '@/store/constants'
import { useMessage } from '@/composables'
import { useListPage } from '@/composables/useListPage'
import { PageHeader, StatCards, SearchForm } from '@/components'

const router = useRouter()
const route = useRoute()
const message = useMessage()

const pageMode = computed(() => route.query.view === 'tenders' ? 'tenders' : 'bids')

const pageTitle = computed(() => pageMode.value === 'tenders' ? '招标项目管理' : '已投标项目管理')

const bidFormRef = ref(null)
const resultFormRef = ref(null)

const searchDefaults = {
  keyword: '',
  status: '',
  dateRange: []
}

const handleSearch = (formData) => {
  Object.assign(listPage.searchForm, formData)
  listPage.pagination.page = 1
  listPage.fetchData()
}

const handleReset = () => {
  Object.assign(listPage.searchForm, searchDefaults)
  listPage.pagination.page = 1
  listPage.fetchData()
}

const statistics = reactive({
  total_bids: 0,
  won_bids: 0,
  pending_bids: 0,
  win_rate: 0
})

const tenderStatistics = reactive({
  total: 0,
  pending: 0,
  collected: 0,
  won: 0,
  favorite: 0
})

const statisticsCards = computed(() => {
  if (pageMode.value === 'tenders') {
    return [
      { value: tenderStatistics.total || 0, label: '招标总数', type: 'default', icon: 'Document' },
      { value: tenderStatistics.pending || 0, label: '待处理', type: 'warning', icon: 'Clock' },
      { value: tenderStatistics.collected || 0, label: '采集数', type: 'info', icon: 'Collection' },
      { value: tenderStatistics.won || 0, label: '已中标', type: 'success', icon: 'CircleCheck' }
    ]
  }
  return [
    { value: statistics.total_bids || 0, label: '总投标数', type: 'default', icon: 'Document' },
    { value: statistics.won_bids || 0, label: '中标数', type: 'success', icon: 'CircleCheck' },
    { value: statistics.pending_bids || 0, label: '待定数', type: 'warning', icon: 'Clock' },
    { value: statistics.win_rate || 0, label: '中标率', type: 'info', icon: 'TrendCharts', suffix: '%' }
  ]
})

const listPage = useListPage({
  fetchApi: async (params) => {
    if (pageMode.value === 'tenders') {
      const searchParams = {
        page: params.page,
        page_size: params.page_size,
        keyword: params.keyword,
        status: params.status
      }
      const res = await tenderApi.getList(searchParams)
      let list = res?.results || res?.list || []
      if (!Array.isArray(list)) {
        list = []
      }
      const total = res?.count || res?.total || list.length
      return { data: { list, total } }
    } else {
      const searchParams = {
        page: params.page,
        page_size: params.page_size,
        status: params.status,
        start_date: params.dateRange?.[0],
        end_date: params.dateRange?.[1]
      }
      const res = await bidApi.getList(searchParams)

      let list = res?.data?.list || res?.results || res?.list || []
      if (!Array.isArray(list)) {
        list = []
      }
      if (params.keyword) {
        const kw = params.keyword.toLowerCase()
        list = list.filter(item =>
          item.tender_title?.toLowerCase().includes(kw) ||
          item.tender_project_code?.toLowerCase().includes(kw) ||
          item.bid_code?.toLowerCase().includes(kw)
        )
      }
      const total = res?.data?.pagination?.total || res?.count || list.length
      return { data: { list, total } }
    }
  },
  deleteApi: (id) => pageMode.value === 'tenders' ? tenderApi.delete(id) : bidApi.delete(id),
  defaultSearchParams: {
    keyword: '',
    status: '',
    dateRange: []
  },
  onDeleteSuccess: () => {
    fetchStatistics()
  }
})

const createDialogVisible = ref(false)
const resultDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const submittingResult = ref(false)
const currentBid = ref(null)
const tenderSearchLoading = ref(false)
const tenderOptions = ref([])
const userOptions = ref([])

const bidForm = reactive({
  id: null,
  tender_id: null,
  tender_title: '',
  bid_code: '',
  bid_price: null,
  bid_date: '',
  status: 'preparing',
  win_probability: 50,
  competitor_count: null,
  bid_manager_id: null,
  team_member_ids: [],
  notes: ''
})

const resultForm = reactive({
  bid_record_id: null,
  result_type: 'pending',
  winner_name: '',
  winner_price: null,
  our_rank: null,
  total_bidders: null,
  announce_date: '',
  announce_url: '',
  win_reason: '',
  lose_reason: '',
  lessons_learned: ''
})

const bidRules = {
  tender_id: [{ required: true, message: '请选择招标项目', trigger: 'change' }],
  bid_date: [{ required: true, message: '请选择投标日期', trigger: 'change' }],
  status: [{ required: true, message: '请选择投标状态', trigger: 'change' }]
}

const resultRules = {
  result_type: [{ required: true, message: '请选择结果类型', trigger: 'change' }]
}

const tableRowClassName = ({ rowIndex }) => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

const getResultType = (type) => {
  const types = {
    win: 'success',
    lose: 'danger',
    pending: 'warning'
  }
  return types[type] || 'info'
}

const getResultText = (type) => {
  const texts = {
    win: '中标',
    lose: '未中标',
    pending: '待定'
  }
  return texts[type] || type
}

const getProbabilityColor = (probability) => {
  if (probability >= 70) return '#52A33B'
  if (probability >= 40) return '#D4862C'
  return '#C94043'
}

const handleDeleteConfirm = (row) => {
  ElMessageBox.confirm(
    `确定要删除投标记录"${row.tender_title}"吗？此操作不可撤销。`,
    '删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    }
  ).then(() => {
    listPage.handleDelete(row.id, row.tender_title)
  }).catch(() => {})
}

const fetchStatistics = async () => {
  try {
    if (pageMode.value === 'tenders') {
      const res = await tenderApi.getStatistics()
      Object.assign(tenderStatistics, res || {})
    } else {
      const res = await bidApi.getStatistics()
      Object.assign(statistics, res?.data || {})
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const searchTenders = async (query) => {
  if (!query) {
    tenderOptions.value = []
    return
  }

  tenderSearchLoading.value = true
  try {
    const res = await tenderApi.getList({ keyword: query, page_size: 20 })
    const rawList = res?.data?.list || res?.data?.results || []
    tenderOptions.value = (Array.isArray(rawList) ? rawList : []).map(item => ({
      id: item.id,
      title: item.title,
      project_code: item.project_code
    }))
  } catch (error) {
    console.error('搜索招标项目失败:', error)
    tenderOptions.value = []
  } finally {
    tenderSearchLoading.value = false
  }
}

const resetBidForm = () => {
  bidForm.id = null
  bidForm.tender_id = null
  bidForm.tender_title = ''
  bidForm.bid_code = ''
  bidForm.bid_price = null
  bidForm.bid_date = ''
  bidForm.status = 'preparing'
  bidForm.win_probability = 50
  bidForm.competitor_count = null
  bidForm.bid_manager_id = null
  bidForm.team_member_ids = []
  bidForm.notes = ''
}

const resetResultForm = () => {
  resultForm.bid_record_id = null
  resultForm.result_type = 'pending'
  resultForm.winner_name = ''
  resultForm.winner_price = null
  resultForm.our_rank = null
  resultForm.total_bidders = null
  resultForm.announce_date = ''
  resultForm.announce_url = ''
  resultForm.win_reason = ''
  resultForm.lose_reason = ''
  resultForm.lessons_learned = ''
}

const showCreateDialog = () => {
  isEdit.value = false
  resetBidForm()
  createDialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  bidForm.id = row.id
  bidForm.tender_id = row.tender_id
  bidForm.tender_title = row.tender_title
  bidForm.bid_code = row.bid_code || ''
  bidForm.bid_price = row.bid_price ? Number(row.bid_price) : null
  bidForm.bid_date = row.bid_date || ''
  bidForm.status = row.status || 'preparing'
  bidForm.win_probability = row.win_probability || 50
  bidForm.competitor_count = row.competitor_count || null
  bidForm.bid_manager_id = row.bid_manager_id || null
  bidForm.team_member_ids = row.team_member_ids || []
  bidForm.notes = row.notes || ''
  createDialogVisible.value = true
}

const showResultDialog = (row) => {
  currentBid.value = row
  resetResultForm()
  resultForm.bid_record_id = row.id

  if (row.result) {
    resultForm.result_type = row.result.result_type || 'pending'
    resultForm.winner_name = row.result.winner_name || ''
    resultForm.winner_price = row.result.winner_price ? Number(row.result.winner_price) : null
    resultForm.our_rank = row.result.our_rank || null
    resultForm.total_bidders = row.result.total_bidders || null
    resultForm.announce_date = row.result.announce_date || ''
    resultForm.announce_url = row.result.announce_url || ''
    resultForm.win_reason = row.result.win_reason || ''
    resultForm.lose_reason = row.result.lose_reason || ''
    resultForm.lessons_learned = row.result.lessons_learned || ''
  }

  resultDialogVisible.value = true
}

const submitBidForm = async () => {
  if (!bidFormRef.value) return

  await bidFormRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        tender: bidForm.tender_id,
        bid_code: bidForm.bid_code || null,
        bid_price: bidForm.bid_price,
        bid_date: bidForm.bid_date,
        status: bidForm.status,
        win_probability: bidForm.win_probability,
        competitor_count: bidForm.competitor_count,
        bid_manager: bidForm.bid_manager_id,
        team_members: bidForm.team_member_ids,
        notes: bidForm.notes || null
      }

      if (isEdit.value) {
        await bidApi.update(bidForm.id, data)
        message.success('更新成功')
      } else {
        await bidApi.create(data)
        message.success('创建成功')
      }

      createDialogVisible.value = false
      listPage.refresh()
      fetchStatistics()
    } catch (error) {
      message.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const submitResultForm = async () => {
  if (!resultFormRef.value) return

  await resultFormRef.value.validate(async (valid) => {
    if (!valid) return

    submittingResult.value = true
    try {
      const data = {
        bid_record: resultForm.bid_record_id,
        result_type: resultForm.result_type,
        winner_name: resultForm.winner_name || null,
        winner_price: resultForm.winner_price,
        our_rank: resultForm.our_rank,
        total_bidders: resultForm.total_bidders,
        announce_date: resultForm.announce_date || null,
        announce_url: resultForm.announce_url || null,
        win_reason: resultForm.win_reason || null,
        lose_reason: resultForm.lose_reason || null,
        lessons_learned: resultForm.lessons_learned || null
      }

      if (currentBid.value?.result?.id) {
        await bidApi.updateResult(currentBid.value.result.id, data)
      } else {
        await bidApi.createResult(data)
      }

      message.success('结果录入成功')
      resultDialogVisible.value = false
      listPage.refresh()
      fetchStatistics()
    } catch (error) {
      message.error(error.message || '操作失败')
    } finally {
      submittingResult.value = false
    }
  })
}

const viewDetail = (row) => {
  if (pageMode.value === 'tenders') {
    router.push(`/tenders/${row.id}`)
  } else if (row.tender_id) {
    router.push(`/tenders/${row.tender_id}`)
  } else {
    router.push(`/bids/${row.id}`)
  }
}

const openSourceUrl = async (url) => {
  if (!url) return
  const openedWindow = window.open(url, '_blank', 'noopener,noreferrer')
  if (openedWindow) {
    setTimeout(() => {
      try {
        const doc = openedWindow.document
        const isAboutBlank = doc.domain === 'about:blank'
        const isEmptyPage = doc.readyState === 'complete' && doc.body?.innerHTML === ''
        const pageContent = doc.body?.innerText || ''
        const is404Page = pageContent.includes('不存在') || pageContent.includes('404') || pageContent.includes('无法访问')
        if (isAboutBlank || isEmptyPage || is404Page) {
          openedWindow.close()
          ElMessageBox.confirm(
            '原始链接可能已失效（网页已被删除或移动）。<br/><br/>是否跳转到中国政府采购网首页搜索相关项目？',
            '链接失效提示',
            {
              confirmButtonText: '跳转搜索',
              cancelButtonText: '关闭',
              type: 'warning',
              dangerouslyUseHTMLString: true
            }
          ).then(() => {
            window.open('http://www.ccgp.gov.cn', '_blank', 'noopener,noreferrer')
          }).catch(() => {})
        }
      } catch (e) {}
    }, 2000)
  }
}

onMounted(() => {
  listPage.fetchData()
  fetchStatistics()
})
</script>

<style scoped lang="scss">
.page-container {
  padding: 0;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.primary-action-btn {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.3);
  transition: all var(--transition-base);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(var(--color-primary-rgb), 0.4);
  }
}

.search-card {
  margin: 0 var(--spacing-lg) var(--spacing-lg);
  border-radius: var(--radius-xl);
  border: none;
}

.table-card {
  margin: 0 var(--spacing-lg);
  border-radius: var(--radius-xl);
  border: none;

  :deep(.el-table) {
    border-radius: var(--radius-xl);

    th {
      background-color: var(--color-bg-base) !important;
      font-weight: var(--font-weight-semibold);
      color: var(--color-text-primary);
      font-size: var(--font-size-sm);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    td {
      border-bottom-color: var(--color-border-lighter);
    }

    tr.even-row > td {
      background-color: var(--color-bg-white);
    }

    tr.odd-row > td {
      background-color: var(--color-bg-base);
    }

    tr:hover > td {
      background-color: rgba(var(--color-primary-rgb), 0.04) !important;
    }
  }
}

.project-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-title {
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.project-code-tag {
  width: fit-content;
  font-size: var(--font-size-xs);
}

.region-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-secondary);

  .el-icon {
    font-size: 14px;
    color: var(--color-text-placeholder);
  }
}

.price-cell {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.empty-cell {
  color: var(--color-text-placeholder);
}

.status-tag {
  border-radius: var(--radius-full);
  font-weight: var(--font-weight-medium);
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
  padding: 4px 8px;

  &:hover {
    color: var(--color-primary);
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border-lighter);
}

.form-dialog {
  :deep(.el-dialog) {
    border-radius: var(--radius-xl);
  }

  :deep(.el-dialog__header) {
    padding: var(--spacing-lg) var(--spacing-xl);
    border-bottom: 1px solid var(--color-border-lighter);
  }

  :deep(.el-dialog__title) {
    font-weight: var(--font-weight-semibold);
    font-size: var(--font-size-md);
  }

  :deep(.el-dialog__body) {
    padding: var(--spacing-xl);
  }

  :deep(.el-dialog__footer) {
    padding: var(--spacing-base) var(--spacing-xl);
    border-top: 1px solid var(--color-border-lighter);
  }
}
</style>

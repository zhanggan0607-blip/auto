﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">投标文档向量库</h3>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>
        <el-button type="warning" @click="showBatchUploadDialog">
          <el-icon><Upload /></el-icon>
          批量上传
        </el-button>
        <el-button type="success" @click="showAISearchDialog">
          <el-icon><Search /></el-icon>
          AI全网搜索
        </el-button>
        <el-button type="warning" @click="showAdvancedSearchDialog">
          <el-icon><Search /></el-icon>
          高级搜索
        </el-button>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.total_count || 0 }}</div>
          <div class="stat-label">文档总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.indexed_count || 0 }}</div>
          <div class="stat-label">已索引</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.upload_count || 0 }}</div>
          <div class="stat-label">用户上传</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ statistics.ai_search_count || 0 }}</div>
          <div class="stat-label">AI搜索</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="语义搜索">
          <el-input
            v-model="searchForm.query"
            placeholder="输入搜索内容，AI将智能匹配相关文档"
            style="width: 400px"
            clearable
            @keyup.enter="handleSemanticSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="文档类型">
          <el-select v-model="searchForm.doc_type" placeholder="全部类型" clearable style="width: 150px">
            <el-option
              v-for="item in documentTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="searchForm.source_type" placeholder="全部来源" clearable style="width: 120px">
            <el-option label="用户上传" value="upload" />
            <el-option label="AI搜索" value="ai_search" />
            <el-option label="系统内置" value="system" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSemanticSearch">
            <el-icon><Search /></el-icon>
            智能搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="list-card">
      <el-table :data="documentList" v-loading="loading" style="width: 100%" size="small">
        <el-table-column prop="title" label="文档标题" min-width="300">
          <template #default="{ row }">
            <div class="doc-title">{{ row.title }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="document_type_display" label="类型" width="120" />
        <el-table-column prop="source_type_display" label="来源" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDocument(row)">查看</el-button>
            <el-button type="danger" link @click="deleteDocument(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="uploadDialogVisible"
      title="上传投标文档"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
        </el-form-item>

        <el-form-item label="文档类型" prop="document_type">
          <el-select v-model="uploadForm.document_type" placeholder="请选择文档类型" style="width: 100%">
            <el-option
              v-for="item in documentTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="所属行业">
          <el-input v-model="uploadForm.industry" placeholder="请输入所属行业" />
        </el-form-item>

        <el-form-item label="项目类型">
          <el-input v-model="uploadForm.project_type" placeholder="请输入适用的项目类型" />
        </el-form-item>

        <el-form-item label="文档文件" prop="file">
          <el-upload
            ref="uploadRef"
            class="upload-area"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :file-list="fileList"
            accept=".doc,.docx,.pdf,.txt,.md"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 .doc/.docx/.pdf/.txt/.md 格式文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="内容摘要">
          <el-input
            v-model="uploadForm.content_summary"
            type="textarea"
            :rows="3"
            placeholder="请输入文档内容摘要（可选）"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="uploadForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入标签后回车添加"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          确定上传
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="aiSearchDialogVisible"
      title="AI全网搜索投标文档"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="aiSearchFormRef"
        :model="aiSearchForm"
        :rules="aiSearchRules"
        label-width="100px"
      >
        <el-form-item label="搜索关键词" required>
          <div class="keyword-input-group">
            <el-input
              v-model="currentAiKeyword"
              placeholder="输入关键词后按回车添加"
              @keyup.enter="addAiKeyword"
              style="width: 280px"
            >
              <template #append>
                <el-button @click="addAiKeyword">添加</el-button>
              </template>
            </el-input>
          </div>
          <div class="keyword-tags" v-if="aiSearchForm.keywords.length > 0">
            <el-tag
              v-for="(kw, idx) in aiSearchForm.keywords"
              :key="idx"
              closable
              @close="removeAiKeyword(idx)"
              class="keyword-tag"
            >
              {{ kw }}
            </el-tag>
          </div>
          <div class="form-tip" v-else>
            提示：多个关键词将组合搜索
          </div>
        </el-form-item>

        <el-form-item label="文档类型">
          <el-select
            v-model="aiSearchForm.document_types"
            multiple
            placeholder="选择文档类型（可多选）"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in documentTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="目标行业">
          <el-select
            v-model="aiSearchForm.industries"
            multiple
            placeholder="选择行业（可多选）"
            style="width: 100%"
            clearable
            filterable
          >
            <el-option
              v-for="item in industryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="最大结果数">
          <el-input-number v-model="aiSearchForm.max_results" :min="5" :max="100" :step="5" />
        </el-form-item>
      </el-form>

      <div v-if="aiSearchTasks.length > 0" class="ai-search-tasks">
        <h4>最近搜索任务</h4>
        <el-table :data="aiSearchTasks" size="small">
          <el-table-column prop="keyword" label="关键词" width="150" />
          <el-table-column prop="status_display" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getTaskStatusType(row.status)" size="small">
                {{ row.status_display }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="saved_count" label="保存数" width="80" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'failed'"
                type="primary"
                link
                size="small"
                @click="retryAISearchTask(row)"
              >
                重试
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="aiSearchDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="aiSearching" @click="startAISearch">
          开始搜索
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="batchUploadDialogVisible"
      title="批量上传投标文档"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="batchUploadFormRef"
        :model="batchUploadForm"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="文档类型">
              <el-select v-model="batchUploadForm.document_type" placeholder="选择文档类型" style="width: 100%">
                <el-option
                  v-for="item in documentTypeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="所属行业">
              <el-input v-model="batchUploadForm.industry" placeholder="输入所属行业" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目类型">
              <el-input v-model="batchUploadForm.project_type" placeholder="输入项目类型" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="质量阈值">
              <el-input-number v-model="batchUploadForm.min_quality_score" :min="0" :max="100" :step="5" />
              <span class="form-tip" style="margin-left: 8px">低于此分数将被跳过</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="选择文件">
          <el-upload
            ref="batchUploadRef"
            class="batch-upload-area"
            :auto-upload="false"
            :limit="100"
            :multiple="true"
            :on-change="handleBatchFileChange"
            :on-remove="handleBatchFileRemove"
            :file-list="batchFileList"
            accept=".doc,.docx,.pdf,.txt,.md"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择多个文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 .doc/.docx/.pdf/.txt/.md 格式，支持批量选择（最多100个文件）
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="batchFileList.length > 0">
          <div class="batch-file-info">
            <span>已选择 {{ batchFileList.length }} 个文件</span>
            <el-button type="text" @click="batchFileList = []">清空</el-button>
          </div>
        </el-form-item>
      </el-form>

      <div v-if="batchUploadProgress.total > 0" class="upload-progress">
        <el-progress
          :percentage="Math.round(batchUploadProgress.current / batchUploadProgress.total * 100)"
          :status="batchUploadProgress.status"
        />
        <div class="progress-info">
          已处理: {{ batchUploadProgress.current }} / {{ batchUploadProgress.total }}
          <span v-if="batchUploadProgress.success > 0" class="success-count">成功: {{ batchUploadProgress.success }}</span>
          <span v-if="batchUploadProgress.failed > 0" class="failed-count">失败: {{ batchUploadProgress.failed }}</span>
          <span v-if="batchUploadProgress.skipped > 0" class="skipped-count">跳过: {{ batchUploadProgress.skipped }}</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="batchUploadDialogVisible = false" :disabled="batchUploading">取消</el-button>
        <el-button type="primary" :loading="batchUploading" :disabled="batchFileList.length === 0" @click="submitBatchUpload">
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="documentDetailVisible"
      :title="currentDocument?.title"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="文档类型">
          {{ currentDocument?.document_type_display }}
        </el-descriptions-item>
        <el-descriptions-item label="来源">
          {{ currentDocument?.source_type_display }}
        </el-descriptions-item>
        <el-descriptions-item label="所属行业">
          {{ currentDocument?.industry_display || currentDocument?.industry || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="项目类型">
          {{ currentDocument?.project_type || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="查看次数">
          {{ currentDocument?.view_count }}
        </el-descriptions-item>
        <el-descriptions-item label="引用次数">
          {{ currentDocument?.use_count }}
        </el-descriptions-item>
        <el-descriptions-item label="相似度">
          {{ currentDocument?.similarity ? (currentDocument.similarity * 100).toFixed(1) + '%' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="质量评分">
          {{ currentDocument?.quality_score || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="内容摘要" :span="2">
          {{ currentDocument?.content_summary || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="来源链接" :span="2" v-if="currentDocument?.source_url">
          <el-link :href="currentDocument.source_url" target="_blank" type="primary">
            {{ currentDocument.source_url }}
          </el-link>
        </el-descriptions-item>
      </el-descriptions>

      <div class="doc-actions">
        <el-button type="primary" @click="downloadDocument">
          <el-icon><Download /></el-icon>
          下载文档
        </el-button>
      </div>
    </el-dialog>

    <el-dialog
      v-model="advancedSearchDialogVisible"
      title="高级搜索"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="advancedSearchFormRef"
        :model="advancedSearchForm"
        label-width="120px"
      >
        <el-form-item label="关键词" required>
          <div class="keyword-input-group">
            <el-input
              v-model="currentKeyword"
              placeholder="输入关键词后按回车添加"
              @keyup.enter="addKeyword"
              style="width: 300px"
            >
              <template #append>
                <el-button @click="addKeyword">添加</el-button>
              </template>
            </el-input>
            <el-select
              v-model="advancedSearchForm.keyword_operator"
              style="width: 120px; margin-left: 10px"
            >
              <el-option label="且 (AND)" value="AND" />
              <el-option label="或 (OR)" value="OR" />
              <el-option label="非 (NOT)" value="NOT" />
            </el-select>
          </div>
          <div class="keyword-tags" v-if="advancedSearchForm.keywords.length > 0">
            <el-tag
              v-for="(kw, idx) in advancedSearchForm.keywords"
              :key="idx"
              closable
              @close="removeKeyword(idx)"
              class="keyword-tag"
            >
              {{ kw }}
            </el-tag>
          </div>
          <div class="form-tip" v-else>
            提示：关键词之间使用 {{ advancedSearchForm.keyword_operator }} 逻辑运算
          </div>
        </el-form-item>

        <el-form-item label="排除关键词" v-if="advancedSearchForm.include_excluded_keywords">
          <div class="keyword-input-group">
            <el-input
              v-model="currentExcludedKeyword"
              placeholder="输入要排除的关键词"
              @keyup.enter="addExcludedKeyword"
              style="width: 300px"
            >
              <template #append>
                <el-button @click="addExcludedKeyword">添加</el-button>
              </template>
            </el-input>
          </div>
          <div class="keyword-tags" v-if="advancedSearchForm.excluded_keywords.length > 0">
            <el-tag
              v-for="(kw, idx) in advancedSearchForm.excluded_keywords"
              :key="idx"
              type="danger"
              closable
              @close="removeExcludedKeyword(idx)"
              class="keyword-tag"
            >
              {{ kw }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="启用排除">
          <el-switch v-model="advancedSearchForm.include_excluded_keywords" />
        </el-form-item>

        <el-form-item label="文档类型">
          <el-select
            v-model="advancedSearchForm.doc_types"
            multiple
            placeholder="选择文档类型（可多选）"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in documentTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="目标行业">
          <el-select
            v-model="advancedSearchForm.industries"
            multiple
            placeholder="选择行业（可多选）"
            style="width: 100%"
            clearable
            filterable
          >
            <el-option
              v-for="item in industryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="项目类型">
          <el-select
            v-model="advancedSearchForm.project_types"
            multiple
            placeholder="选择项目类型（可多选）"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="item in projectTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="最小相似度">
          <el-slider
            v-model="advancedSearchForm.min_similarity"
            :min="0"
            :max="100"
            :step="5"
            show-stops
            :marks="similarityMarks"
            style="width: 400px"
          />
          <span class="similarity-value">{{ advancedSearchForm.min_similarity }}%</span>
        </el-form-item>

        <el-form-item label="返回数量">
          <el-input-number
            v-model="advancedSearchForm.limit"
            :min="1"
            :max="100"
            :step="5"
          />
        </el-form-item>
      </el-form>

      <div v-if="advancedSearchResults.length > 0" class="advanced-search-results">
        <div class="results-header">
          <span>搜索结果: {{ advancedSearchTotal }} 个相关文档</span>
          <el-button link type="primary" @click="advancedSearchResults = []">清除结果</el-button>
        </div>
        <el-table :data="advancedSearchResults" size="small" max-height="300">
          <el-table-column prop="title" label="文档标题" min-width="200" show-overflow-tooltip />
          <el-table-column prop="document_type_display" label="类型" width="100" />
          <el-table-column prop="industry_display" label="行业" width="100" show-overflow-tooltip />
          <el-table-column label="相似度" width="80">
            <template #default="{ row }">
              <el-tag type="success" size="small">
                {{ row.similarity ? (row.similarity * 100).toFixed(1) + '%' : '-' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewAdvancedSearchDocument(row)">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button @click="advancedSearchDialogVisible = false">取消</el-button>
        <el-button @click="resetAdvancedSearch">重置</el-button>
        <el-button type="primary" :loading="advancedSearching" @click="executeAdvancedSearch">
          开始搜索
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Upload, Download } from '@element-plus/icons-vue'
import { vectorlibApi } from '@/api/vectorlib'
import { formatDate } from '@/utils/date'
import { parseListResponse } from '@/utils/response-parser'

const loading = ref(false)
const documentList = ref([])
const statistics = ref({})

const searchForm = reactive({
  query: '',
  doc_type: '',
  source_type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const documentTypeOptions = [
  { value: 'bid_template', label: '标书范本' },
  { value: 'technical_plan', label: '技术方案' },
  { value: 'construction_plan', label: '施工组织设计' },
  { value: 'qualification_doc', label: '资质文件' },
  { value: 'business_doc', label: '商务文件' },
  { value: 'price_analysis', label: '报价分析' },
  { value: 'contract_template', label: '合同范本' },
  { value: 'case_study', label: '案例资料' },
  { value: 'other', label: '其他文档' }
]

const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const fileList = ref([])

const uploadForm = reactive({
  title: '',
  document_type: 'other',
  industry: '',
  project_type: '',
  content_summary: '',
  tags: [],
  file: null
})

const uploadRules = {
  title: [
    { required: true, message: '请输入文档标题', trigger: 'blur' }
  ],
  document_type: [
    { required: true, message: '请选择文档类型', trigger: 'change' }
  ],
  file: [
    { required: true, message: '请选择文档文件', trigger: 'change' }
  ]
}

const batchUploadDialogVisible = ref(false)
const batchUploading = ref(false)
const batchUploadFormRef = ref(null)
const batchUploadRef = ref(null)
const batchFileList = ref([])

const batchUploadForm = reactive({
  document_type: 'bid_document',
  industry: '',
  project_type: '',
  min_quality_score: 90
})

const batchUploadProgress = reactive({
  total: 0,
  current: 0,
  success: 0,
  failed: 0,
  skipped: 0,
  status: ''
})

const showBatchUploadDialog = () => {
  batchUploadForm.document_type = 'bid_document'
  batchUploadForm.industry = ''
  batchUploadForm.project_type = ''
  batchUploadForm.min_quality_score = 90
  batchFileList.value = []
  batchUploadProgress.total = 0
  batchUploadProgress.current = 0
  batchUploadProgress.success = 0
  batchUploadProgress.failed = 0
  batchUploadProgress.skipped = 0
  batchUploadProgress.status = ''
  batchUploadDialogVisible.value = true
}

const handleBatchFileChange = (file, files) => {
  batchFileList.value = files
}

const handleBatchFileRemove = (file, files) => {
  batchFileList.value = files
}

const submitBatchUpload = async () => {
  if (!batchUploadFormRef.value) return

  if (batchFileList.value.length === 0) {
    ElMessage.error('请选择要上传的文件')
    return
  }

  batchUploading.value = true
  batchUploadProgress.total = batchFileList.value.length
  batchUploadProgress.current = 0
  batchUploadProgress.success = 0
  batchUploadProgress.failed = 0
  batchUploadProgress.skipped = 0

  try {
    const formData = new FormData()
    batchFileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    formData.append('document_type', batchUploadForm.document_type)
    if (batchUploadForm.industry) formData.append('industry', batchUploadForm.industry)
    if (batchUploadForm.project_type) formData.append('project_type', batchUploadForm.project_type)
    formData.append('min_quality_score', batchUploadForm.min_quality_score.toString())

    const res = await vectorlibApi.batchUpload(formData)
    if (res.code === 0 || res.success) {
      const result = res.data || res
      batchUploadProgress.current = result.total_files || batchFileList.value.length
      batchUploadProgress.success = result.success_count || 0
      batchUploadProgress.failed = result.failed_count || 0
      batchUploadProgress.skipped = result.skipped_count || 0
      batchUploadProgress.status = 'success'

      ElMessage.success({
        message: `批量上传完成: 成功${batchUploadProgress.success}个, 跳过${batchUploadProgress.skipped}个, 失败${batchUploadProgress.failed}个`,
        duration: 5000
      })

      if (batchUploadProgress.success > 0) {
        batchUploadDialogVisible.value = false
        fetchDocuments()
        fetchStatistics()
      }
    } else {
      ElMessage.error(res.message || '批量上传失败')
      batchUploadProgress.status = 'exception'
    }
  } catch (error) {
    console.error('批量上传失败:', error)
    ElMessage.error('批量上传失败，请重试')
    batchUploadProgress.status = 'exception'
  } finally {
    batchUploading.value = false
  }
}

const aiSearchDialogVisible = ref(false)
const aiSearching = ref(false)
const aiSearchFormRef = ref(null)
const aiSearchTasks = ref([])
const currentAiKeyword = ref('')

const aiSearchForm = reactive({
  keywords: [],
  document_types: [],
  industries: [],
  max_results: 20
})

const aiSearchRules = {
  keywords: [
    { required: true, message: '请至少添加一个搜索关键词', trigger: 'blur' }
  ]
}

const advancedSearchDialogVisible = ref(false)
const advancedSearching = ref(false)
const advancedSearchFormRef = ref(null)
const advancedSearchResults = ref([])
const advancedSearchTotal = ref(0)
const currentKeyword = ref('')
const currentExcludedKeyword = ref('')

const advancedSearchForm = reactive({
  keywords: [],
  keyword_operator: 'AND',
  doc_types: [],
  industries: [],
  project_types: [],
  min_similarity: 0,
  limit: 20,
  include_excluded_keywords: false,
  excluded_keywords: []
})

const industryOptions = [
  { value: 'building', label: '房屋建筑' },
  { value: 'municipal', label: '市政公用' },
  { value: 'transportation', label: '交通运输' },
  { value: 'water_conservancy', label: '水利水电' },
  { value: 'power', label: '电力能源' },
  { value: 'telecommunication', label: '通信信息' },
  { value: 'mechanical_electrical', label: '机电安装' },
  { value: 'petrochemical', label: '石油化工' },
  { value: 'mining', label: '矿山工程' },
  { value: 'metallurgy', label: '冶金工程' },
  { value: 'textile', label: '纺织轻工' },
  { value: 'environmental', label: '生态环境' },
  { value: 'agriculture_forestry', label: '农林牧渔' },
  { value: 'medical', label: '医疗卫生' },
  { value: 'education', label: '教育文化' },
  { value: 'finance', label: '金融服务' },
  { value: 'it', label: '信息技术' },
  { value: 'commerce', label: '商业服务' },
  { value: 'culture_tourism', label: '文化旅游' },
  { value: 'other', label: '其他行业' }
]

const projectTypeOptions = [
  { value: 'new', label: '新建项目' },
  { value: 'renovation', label: '改建项目' },
  { value: 'expansion', label: '扩建项目' },
  { value: 'maintenance', label: '维保项目' }
]

const similarityMarks = {
  0: '0%',
  25: '25%',
  50: '50%',
  75: '75%',
  100: '100%'
}

const addKeyword = () => {
  if (currentKeyword.value.trim() && !advancedSearchForm.keywords.includes(currentKeyword.value.trim())) {
    advancedSearchForm.keywords.push(currentKeyword.value.trim())
    currentKeyword.value = ''
  }
}

const removeKeyword = (index) => {
  advancedSearchForm.keywords.splice(index, 1)
}

const addAiKeyword = () => {
  if (currentAiKeyword.value.trim() && !aiSearchForm.keywords.includes(currentAiKeyword.value.trim())) {
    aiSearchForm.keywords.push(currentAiKeyword.value.trim())
    currentAiKeyword.value = ''
  }
}

const removeAiKeyword = (index) => {
  aiSearchForm.keywords.splice(index, 1)
}

const addExcludedKeyword = () => {
  if (currentExcludedKeyword.value.trim() && !advancedSearchForm.excluded_keywords.includes(currentExcludedKeyword.value.trim())) {
    advancedSearchForm.excluded_keywords.push(currentExcludedKeyword.value.trim())
    currentExcludedKeyword.value = ''
  }
}

const removeExcludedKeyword = (index) => {
  advancedSearchForm.excluded_keywords.splice(index, 1)
}

const showAdvancedSearchDialog = () => {
  resetAdvancedSearch()
  advancedSearchDialogVisible.value = true
}

const resetAdvancedSearch = () => {
  advancedSearchForm.keywords = []
  advancedSearchForm.keyword_operator = 'AND'
  advancedSearchForm.doc_types = []
  advancedSearchForm.industries = []
  advancedSearchForm.project_types = []
  advancedSearchForm.min_similarity = 0
  advancedSearchForm.limit = 20
  advancedSearchForm.include_excluded_keywords = false
  advancedSearchForm.excluded_keywords = []
  advancedSearchResults.value = []
  advancedSearchTotal.value = 0
  currentKeyword.value = ''
  currentExcludedKeyword.value = ''
}

const executeAdvancedSearch = async () => {
  if (advancedSearchForm.keywords.length === 0) {
    ElMessage.warning('请至少添加一个关键词')
    return
  }

  advancedSearching.value = true
  try {
    const res = await vectorlibApi.advancedSearch({
      keywords: advancedSearchForm.keywords,
      keyword_operator: advancedSearchForm.keyword_operator,
      doc_types: advancedSearchForm.doc_types,
      industries: advancedSearchForm.industries,
      project_types: advancedSearchForm.project_types,
      min_similarity: advancedSearchForm.min_similarity / 100,
      limit: advancedSearchForm.limit,
      include_excluded_keywords: advancedSearchForm.include_excluded_keywords,
      excluded_keywords: advancedSearchForm.excluded_keywords
    })
    if (res.code === 0) {
      const { list, total } = parseListResponse(res)
      advancedSearchResults.value = list
      advancedSearchTotal.value = total
      ElMessage.success(`找到 ${advancedSearchTotal.value} 个相关文档`)
    } else {
      ElMessage.error(res.message || '搜索失败')
    }
  } catch (error) {
    console.error('高级搜索失败:', error)
    ElMessage.error('搜索失败，请重试')
  } finally {
    advancedSearching.value = false
  }
}

const viewAdvancedSearchDocument = (row) => {
  currentDocument.value = row
  documentDetailVisible.value = true
}

const documentDetailVisible = ref(false)
const currentDocument = ref(null)

const getTaskStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const fetchStatistics = async () => {
  try {
    const res = await vectorlibApi.getStatistics()
    if (res.code === 0) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const fetchDocuments = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (searchForm.doc_type) params.document_type = searchForm.doc_type
    if (searchForm.source_type) params.source_type = searchForm.source_type

    const res = await vectorlibApi.getDocuments(params)
    if (res.code === 0) {
      const { list, total } = parseListResponse(res)
      documentList.value = list
      pagination.total = total
    }
  } catch (error) {
    console.error('获取文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSemanticSearch = async () => {
  if (!searchForm.query.trim()) {
    fetchDocuments()
    return
  }

  loading.value = true
  try {
    const res = await vectorlibApi.searchDocuments({
      query: searchForm.query,
      doc_types: searchForm.doc_type ? [searchForm.doc_type] : [],
      limit: pagination.pageSize
    })
    if (res.code === 0) {
      const { list, total } = parseListResponse(res)
      documentList.value = list
      pagination.total = total
      ElMessage.success(`找到 ${res.data?.total || 0} 个相关文档`)
    }
  } catch (error) {
    console.error('语义搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.query = ''
  searchForm.doc_type = ''
  searchForm.source_type = ''
  pagination.page = 1
  fetchDocuments()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  fetchDocuments()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  fetchDocuments()
}

const showUploadDialog = () => {
  uploadForm.title = ''
  uploadForm.document_type = 'other'
  uploadForm.industry = ''
  uploadForm.project_type = ''
  uploadForm.content_summary = ''
  uploadForm.tags = []
  uploadForm.file = null
  fileList.value = []
  uploadDialogVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
  if (!uploadForm.title && file.name) {
    uploadForm.title = file.name.replace(/\.[^/.]+$/, '')
  }
  fileList.value = [file]
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return

  try {
    await uploadFormRef.value.validate()
  } catch {
    return
  }

  if (!uploadForm.file) {
    ElMessage.error('请选择文档文件')
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('title', uploadForm.title)
    formData.append('document_type', uploadForm.document_type)
    formData.append('source_type', 'upload')
    if (uploadForm.industry) formData.append('industry', uploadForm.industry)
    if (uploadForm.project_type) formData.append('project_type', uploadForm.project_type)
    if (uploadForm.content_summary) formData.append('content_summary', uploadForm.content_summary)
    if (uploadForm.tags.length > 0) formData.append('tags', JSON.stringify(uploadForm.tags))
    formData.append('file_path', uploadForm.file)

    const res = await vectorlibApi.uploadDocument(formData)
    if (res.code === 0) {
      ElMessage.success('文档上传成功，正在处理中...')
      uploadDialogVisible.value = false
      fetchDocuments()
      fetchStatistics()
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

const showAISearchDialog = async () => {
  aiSearchForm.keywords = []
  aiSearchForm.document_types = []
  aiSearchForm.industries = []
  aiSearchForm.max_results = 20
  currentAiKeyword.value = ''
  aiSearchDialogVisible.value = true

  try {
    const res = await vectorlibApi.getAISearchTasks({ page_size: 5 })
    if (res.code === 0) {
      const { list } = parseListResponse(res)
      aiSearchTasks.value = list
    }
  } catch (error) {
    console.error('获取AI搜索任务失败:', error)
  }
}

const startAISearch = async () => {
  if (!aiSearchFormRef.value) return

  try {
    await aiSearchFormRef.value.validate()
  } catch {
    return
  }

  aiSearching.value = true

  try {
    const res = await vectorlibApi.createAISearchTask({
      keywords: aiSearchForm.keywords.join(','),
      document_types: aiSearchForm.document_types.join(','),
      industries: aiSearchForm.industries.join(','),
      max_results: aiSearchForm.max_results
    })
    if (res.code === 0) {
      if (res.data?.status === 'failed' && res.data?.error_message) {
        ElMessage.error(res.data.error_message.replace(/\n/g, ' '))
      } else {
        ElMessage.success('AI搜索任务已创建，正在执行中...')
        aiSearchDialogVisible.value = false
        fetchDocuments()
        fetchStatistics()
      }
    } else {
      const errorMsg = res.message || '创建任务失败'
      if (errorMsg.includes('LLM') || errorMsg.includes('Ollama') || errorMsg.includes('API')) {
        ElMessage({
          type: 'error',
          message: errorMsg,
          duration: 5000,
          showClose: true
        })
      } else {
        ElMessage.error(errorMsg)
      }
    }
  } catch (error) {
    console.error('创建AI搜索任务失败:', error)
    const errorMsg = error.response?.data?.message || error.message || '创建任务失败'
    ElMessage({
      type: 'error',
      message: errorMsg,
      duration: 5000,
      showClose: true
    })
  } finally {
    aiSearching.value = false
  }
}

const retryAISearchTask = async (task) => {
  try {
    const res = await vectorlibApi.retryAISearchTask(task.id)
    if (res.code === 0) {
      ElMessage.success('任务已重新启动')
      showAISearchDialog()
    } else {
      ElMessage.error(res.message || '重试失败')
    }
  } catch (error) {
    ElMessage.error('重试失败')
  }
}

const viewDocument = async (row) => {
  try {
    const res = await vectorlibApi.getDocument(row.id)
    if (res.code === 0) {
      currentDocument.value = res.data
      documentDetailVisible.value = true
      vectorlibApi.incrementView(row.id)
    }
  } catch (error) {
    console.error('获取文档详情失败:', error)
  }
}

const deleteDocument = async (row) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除此文档吗？删除后将无法恢复。',
      '删除确认',
      { type: 'warning' }
    )
    const res = await vectorlibApi.deleteDocument(row.id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      fetchDocuments()
      fetchStatistics()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const downloadDocument = () => {
  if (currentDocument.value?.file_url) {
    window.open(currentDocument.value.file_url, '_blank')
  } else {
    ElMessage.warning('该文档暂无可下载的文件')
  }
}

onMounted(() => {
  fetchStatistics()
  fetchDocuments()
})
</script>

<style scoped>
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
  color: #1E293B;
}

.stat-label {
  font-size: 14px;
  color: #64748B;
  margin-top: 8px;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.list-card {
  margin-bottom: 20px;
}

.doc-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-area {
  width: 100%;
}

.ai-search-tasks {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #E2E8F0;
}

.ai-search-tasks h4 {
  margin-bottom: 10px;
  color: #334155;
}

.doc-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.keyword-input-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.keyword-tag {
  font-size: 14px;
}

.form-tip {
  margin-top: 10px;
  color: #64748B;
  font-size: 12px;
}

.similarity-value {
  margin-left: 15px;
  color: #3B82F6;
  font-weight: bold;
}

.advanced-search-results {
  margin-top: 20px;
  padding: 15px;
  background: #F1F5F9;
  border-radius: 4px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: #334155;
  font-size: 14px;
}
</style>

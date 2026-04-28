﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">生成标书</h3>
    </div>
    
    <el-steps :active="activeStep" finish-status="success" class="steps">
      <el-step title="选择模板" />
      <el-step title="选择参考资料" />
      <el-step title="填写信息" />
      <el-step title="生成文档" />
    </el-steps>
    
    <div class="step-content">
      <div v-show="activeStep === 0" class="step-panel">
        <el-table :data="templateList" @row-click="selectTemplate" highlight-current-row>
          <el-table-column prop="name" label="模板名称" />
          <el-table-column prop="template_type" label="模板类型" width="120" />
          <el-table-column prop="variables" label="变量" width="200">
            <template #default="{ row }">
              {{ row.variables?.join(', ') || '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <div v-show="activeStep === 1" class="step-panel reference-panel">
        <div class="reference-header">
          <el-input
            v-model="referenceSearch"
            placeholder="搜索参考文档"
            style="width: 300px"
            clearable
            @keyup.enter="searchReferenceDocs"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" @click="searchReferenceDocs">搜索</el-button>
        </div>
        
        <el-row :gutter="20">
          <el-col :span="14">
            <div class="reference-list">
              <h4>向量库文档</h4>
              <el-table 
                :data="referenceDocList" 
                @selection-change="handleReferenceSelect"
                v-loading="referenceLoading"
                max-height="400"
              >
                <el-table-column type="selection" width="50" />
                <el-table-column prop="title" label="文档标题" min-width="200" show-overflow-tooltip />
                <el-table-column prop="document_type" label="类型" width="100" />
                <el-table-column prop="quality_score" label="质量分" width="80">
                  <template #default="{ row }">
                    <el-tag :type="getQualityTagType(row.quality_score)" size="small">
                      {{ row.quality_score }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="use_count" label="引用次数" width="80" />
              </el-table>
            </div>
          </el-col>
          <el-col :span="10">
            <div class="selected-reference">
              <h4>已选择 ({{ selectedReferenceDocs.length }})</h4>
              <el-scrollbar max-height="400">
                <div v-if="selectedReferenceDocs.length === 0" class="empty-tip">
                  请从左侧选择参考文档
                </div>
                <div v-else class="selected-list">
                  <div 
                    v-for="doc in selectedReferenceDocs" 
                    :key="doc.id" 
                    class="selected-item"
                  >
                    <div class="doc-info">
                      <span class="doc-title">{{ doc.title }}</span>
                      <el-tag size="small" type="info">{{ doc.document_type }}</el-tag>
                    </div>
                    <el-button 
                      type="danger" 
                      link 
                      size="small"
                      @click="removeReferenceDoc(doc)"
                    >
                      移除
                    </el-button>
                  </div>
                </div>
              </el-scrollbar>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <div v-show="activeStep === 2" class="step-panel">
        <el-form :model="formData" label-width="120px">
          <el-form-item label="文档名称">
            <el-input v-model="formData.name" placeholder="请输入文档名称" />
          </el-form-item>
          <el-form-item label="关联项目">
            <el-input v-model="tenderTitle" disabled />
          </el-form-item>
          <el-form-item label="参考资料">
            <div class="reference-summary">
              已选择 {{ selectedReferenceDocs.length }} 篇参考文档
              <el-button type="primary" link @click="activeStep = 1">修改</el-button>
            </div>
          </el-form-item>
          <el-divider>变量填写</el-divider>
          <el-form-item
            v-for="variable in templateVariables"
            :key="variable"
            :label="variable"
          >
            <el-input 
              v-model="formData.variables[variable]" 
              :placeholder="`请输入${variable}`" 
            />
          </el-form-item>
        </el-form>
      </div>
      
      <div v-show="activeStep === 3" class="step-panel">
        <el-result
          v-if="generateResult.success"
          icon="success"
          title="文档生成成功"
          sub-title="您可以下载或继续编辑"
        >
          <template #extra>
            <el-button type="primary" @click="downloadResult">下载文档</el-button>
            <el-button @click="resetForm">继续生成</el-button>
          </template>
        </el-result>
        <el-result
          v-else-if="generateResult.error"
          icon="error"
          title="生成失败"
          :sub-title="generateResult.error"
        >
          <template #extra>
            <el-button type="primary" @click="activeStep = 2">返回修改</el-button>
          </template>
        </el-result>
        <div v-else class="generating">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在生成文档，请稍候...</span>
        </div>
      </div>
    </div>
    
    <div class="step-actions">
      <el-button v-if="activeStep > 0" @click="prevStep">上一步</el-button>
      <el-button v-if="activeStep < 3" type="primary" @click="nextStep" :disabled="!canNext">
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { documentApi } from '@/api/document'
import { parseListResponse } from '@/utils/response-parser'
import { useFormDraft } from '@/composables/useFormDraft'

const route = useRoute()

const activeStep = ref(0)
const templateList = ref([])
const selectedTemplate = ref(null)
const tenderTitle = ref('')
const tenderId = ref(null)

const referenceSearch = ref('')
const referenceDocList = ref([])
const selectedReferenceDocs = ref([])
const referenceLoading = ref(false)

const formData = reactive({
  name: '',
  variables: {}
})

const { clearDraft } = useFormDraft(formData, {
  key: 'document:generate',
  context: () => ({ tenderId: tenderId.value, templateId: selectedTemplate.value?.id }),
  onRestored: (data) => {
    if (data.templateId) {
      const tmpl = templateList.value.find(t => t.id === data.templateId)
      if (tmpl) selectedTemplate.value = tmpl
    }
  }
})

const generateResult = ref({
  success: false,
  error: '',
  data: null
})

const templateVariables = computed(() => {
  return selectedTemplate.value?.variables || []
})

const canNext = computed(() => {
  if (activeStep.value === 0) {
    return !!selectedTemplate.value
  }
  if (activeStep.value === 2) {
    return !!formData.name
  }
  return true
})

const fetchTemplates = async () => {
  try {
    const res = await documentApi.getTemplates()
    const { list } = parseListResponse(res)
    templateList.value = list
  } catch (error) {
    console.error('获取模板列表失败:', error)
  }
}

const selectTemplate = (row) => {
  selectedTemplate.value = row
  formData.name = `${tenderTitle.value || '标书'}_${row.name}`
}

const searchReferenceDocs = async () => {
  referenceLoading.value = true
  try {
    const res = await documentApi.searchReferenceDocs({
      query: referenceSearch.value,
      limit: 20
    })
    const { list } = parseListResponse(res)
    referenceDocList.value = list
  } catch (error) {
    console.error('搜索参考文档失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    referenceLoading.value = false
  }
}

const handleReferenceSelect = (selection) => {
  const existingIds = new Set(selectedReferenceDocs.value.map(d => d.id))
  selection.forEach(doc => {
    if (!existingIds.has(doc.id)) {
      selectedReferenceDocs.value.push(doc)
    }
  })
}

const removeReferenceDoc = (doc) => {
  const index = selectedReferenceDocs.value.findIndex(d => d.id === doc.id)
  if (index > -1) {
    selectedReferenceDocs.value.splice(index, 1)
  }
}

const getQualityTagType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'info'
}

const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--
  }
}

const nextStep = async () => {
  if (activeStep.value === 0 && !selectedTemplate.value) {
    ElMessage.warning('请选择一个模板')
    return
  }
  
  if (activeStep.value === 1) {
    searchReferenceDocs()
  }
  
  if (activeStep.value === 2) {
    await generateDocument()
  }
  
  if (activeStep.value < 3) {
    activeStep.value++
  }
}

const generateDocument = async () => {
  generateResult.value = { success: false, error: '', data: null }
  
  try {
    const res = await documentApi.generateDocument({
      template_id: selectedTemplate.value.id,
      tender_id: tenderId.value,
      document_name: formData.name,
      variables: formData.variables,
      generate_pdf: true,
      reference_doc_ids: selectedReferenceDocs.value.map(d => d.id)
    })
    
    generateResult.value = {
      success: true,
      data: res.data
    }
    clearDraft()
  } catch (error) {
    generateResult.value = {
      success: false,
      error: error.response?.data?.message || '生成失败'
    }
  }
}

const downloadResult = () => {
  if (generateResult.value.data?.file_url) {
    window.open(generateResult.value.data.file_url, '_blank')
  }
}

const resetForm = () => {
  activeStep.value = 0
  selectedTemplate.value = null
  formData.name = ''
  formData.variables = {}
  selectedReferenceDocs.value = []
  generateResult.value = { success: false, error: '', data: null }
}

onMounted(() => {
  tenderId.value = route.query.tender_id
  tenderTitle.value = route.query.tender_title || ''
  fetchTemplates()
  searchReferenceDocs()
})
</script>

<style lang="scss" scoped>
.steps {
  margin-bottom: 30px;
}

.step-panel {
  min-height: 300px;
  padding: 20px;
  background-color: #F1F5F9;
  border-radius: 4px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.generating {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  
  .el-icon {
    font-size: 40px;
    margin-bottom: 15px;
  }
}

.reference-panel {
  .reference-header {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .reference-list,
  .selected-reference {
    h4 {
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid #E2E8F0;
    }
  }
  
  .empty-tip {
    color: #64748B;
    text-align: center;
    padding: 40px 0;
  }
  
  .selected-list {
    .selected-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px;
      margin-bottom: 8px;
      background: #fff;
      border-radius: 4px;
      border: 1px solid #E2E8F0;
      
      .doc-info {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .doc-title {
          max-width: 200px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }
}

.reference-summary {
  color: #334155;
}
</style>

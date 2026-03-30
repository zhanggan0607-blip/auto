<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">文档管理</h3>
      <el-button type="primary" @click="showUploadDialog">
        <el-icon><Upload /></el-icon>
        上传模板
      </el-button>
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="文档模板" name="templates">
        <el-table :data="templateList" v-loading="loading">
          <el-table-column prop="name" label="模板名称" />
          <el-table-column prop="template_type" label="模板类型" width="120">
            <template #default="{ row }">
              {{ getTemplateTypeText(row.template_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="variables" label="变量数量" width="100">
            <template #default="{ row }">
              {{ row.variables?.length || 0 }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button type="primary" link @click="previewTemplate(row)">预览</el-button>
              <el-button type="danger" link @click="deleteTemplate(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="生成的文档" name="generated">
        <el-table :data="generatedList" v-loading="loading">
          <el-table-column prop="name" label="文档名称" />
          <el-table-column prop="tender_title" label="关联项目" width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getDocStatusType(row.status)" size="small">
                {{ getDocStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button type="primary" link @click="downloadDoc(row)">下载</el-button>
              <el-button type="success" link @click="reviewDoc(row)">审核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="uploadDialogVisible"
      title="上传模板"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        
        <el-form-item label="模板类型" prop="template_type">
          <el-select v-model="uploadForm.template_type" placeholder="请选择模板类型" style="width: 100%">
            <el-option
              v-for="item in templateTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模板描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <el-form-item label="模板文件" prop="file">
          <el-upload
            ref="uploadRef"
            class="upload-area"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            :file-list="fileList"
            accept=".doc,.docx,.dotx"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 .doc/.docx/.dotx 格式的Word模板文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">
          确定上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { documentApi } from '@/api/document'
import { getDocStatusType, getDocStatusText } from '@/store/constants'

const activeTab = ref('templates')
const loading = ref(false)
const templateList = ref([])
const generatedList = ref([])

const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const fileList = ref([])

const uploadForm = ref({
  name: '',
  template_type: 'bid_document',
  description: '',
  file: null
})

const uploadRules = {
  name: [
    { required: true, message: '请输入模板名称', trigger: 'blur' }
  ],
  template_type: [
    { required: true, message: '请选择模板类型', trigger: 'change' }
  ],
  file: [
    { required: true, message: '请选择模板文件', trigger: 'change' }
  ]
}

const templateTypeOptions = [
  { value: 'bid_document', label: '投标文件' },
  { value: 'business_license', label: '营业执照' },
  { value: 'qualification', label: '资质证书' },
  { value: 'authorization', label: '授权书' },
  { value: 'proposal', label: '投标方案' },
  { value: 'other', label: '其他' }
]

const getTemplateTypeText = (type) => {
  const item = templateTypeOptions.find(opt => opt.value === type)
  return item ? item.label : type
}

const fetchTemplates = async () => {
  loading.value = true
  try {
    const res = await documentApi.getTemplates()
    templateList.value = res.data?.list || []
  } catch (error) {
    console.error('获取模板列表失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchGeneratedDocs = async () => {
  loading.value = true
  try {
    const res = await documentApi.getGeneratedList()
    generatedList.value = res.data?.list || []
  } catch (error) {
    console.error('获取文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

const showUploadDialog = () => {
  uploadForm.value = {
    name: '',
    template_type: 'bid_document',
    description: '',
    file: null
  }
  fileList.value = []
  uploadDialogVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
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
  
  if (!uploadForm.value.file) {
    ElMessage.error('请选择模板文件')
    return
  }
  
  uploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.value.name)
    formData.append('template_type', uploadForm.value.template_type)
    formData.append('description', uploadForm.value.description || '')
    formData.append('file_path', uploadForm.value.file)
    formData.append('is_active', 'true')
    
    const userStore = (await import('@/store/user')).useUserStore()

    const response = await fetch('/api/v1/documents/templates/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })
    
    const result = await response.json()
    
    if (result.code === 0) {
      ElMessage.success('模板上传成功')
      uploadDialogVisible.value = false
      fetchTemplates()
    } else {
      ElMessage.error(result.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败，请重试')
  } finally {
    uploading.value = false
  }
}

const previewTemplate = (row) => {
  if (row.file_url) {
    window.open(row.file_url, '_blank')
  } else {
    ElMessage.info(`预览模板: ${row.name}`)
  }
}

const deleteTemplate = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该模板吗？', '提示', {
      type: 'warning'
    })
    await documentApi.deleteTemplate(row.id)
    ElMessage.success('删除成功')
    fetchTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const downloadDoc = (row) => {
  if (row.file_url) {
    window.open(row.file_url, '_blank')
  }
}

const reviewDoc = async (row) => {
  try {
    await documentApi.reviewDocument(row.id)
    ElMessage.success('审核成功')
    fetchGeneratedDocs()
  } catch (error) {
    ElMessage.error('审核失败')
  }
}

onMounted(() => {
  fetchTemplates()
  fetchGeneratedDocs()
})
</script>

<style scoped>
.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-list) {
  margin-top: 10px;
}
</style>

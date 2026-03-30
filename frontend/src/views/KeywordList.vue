<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">关键词管理</h3>
      <el-button type="primary" @click="showCreateDialog">新增关键词</el-button>
    </div>
    
    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="行业关键词" name="industry" />
      <el-tab-pane label="地区关键词" name="region" />
      <el-tab-pane label="产品关键词" name="product" />
      <el-tab-pane label="排除关键词" name="exclude" />
    </el-tabs>
    
    <el-table :data="keywordList" v-loading="loading">
      <el-table-column prop="keyword" label="关键词" />
      <el-table-column prop="category" label="类别" width="120">
        <template #default="{ row }">
          {{ getCategoryText(row.category) }}
        </template>
      </el-table-column>
      <el-table-column prop="weight" label="权重" width="80" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" link @click="editKeyword(row)">编辑</el-button>
          <el-button type="danger" link @click="deleteKeyword(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑关键词' : '新增关键词'" width="400px">
      <el-form :model="keywordForm" label-width="80px">
        <el-form-item label="关键词" required>
          <el-input v-model="keywordForm.keyword" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="keywordForm.category">
            <el-option label="行业关键词" value="industry" />
            <el-option label="地区关键词" value="region" />
            <el-option label="产品关键词" value="product" />
            <el-option label="排除关键词" value="exclude" />
          </el-select>
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="keywordForm.weight" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="keywordForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKeyword">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tenderApi } from '@/api/tender'

const activeTab = ref('all')
const loading = ref(false)
const keywordList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)

const keywordForm = reactive({
  id: null,
  keyword: '',
  category: 'industry',
  weight: 1,
  is_active: true
})

const getCategoryText = (category) => {
  const texts = {
    industry: '行业关键词',
    region: '地区关键词',
    product: '产品关键词',
    exclude: '排除关键词'
  }
  return texts[category] || category
}

const fetchKeywords = async () => {
  loading.value = true
  try {
    const params = {}
    if (activeTab.value !== 'all') {
      params.category = activeTab.value
    }
    const res = await tenderApi.getKeywords(params)
    keywordList.value = res.data?.list || []
  } catch (error) {
    console.error('获取关键词列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTabChange = () => {
  fetchKeywords()
}

const showCreateDialog = () => {
  isEdit.value = false
  keywordForm.id = null
  keywordForm.keyword = ''
  keywordForm.category = activeTab.value !== 'all' ? activeTab.value : 'industry'
  keywordForm.weight = 1
  keywordForm.is_active = true
  dialogVisible.value = true
}

const editKeyword = (row) => {
  isEdit.value = true
  keywordForm.id = row.id
  keywordForm.keyword = row.keyword
  keywordForm.category = row.category
  keywordForm.weight = row.weight
  keywordForm.is_active = row.is_active
  dialogVisible.value = true
}

const saveKeyword = async () => {
  if (!keywordForm.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }

  const keywordValue = keywordForm.keyword.trim()
  if (keywordList.value.some(k => k.keyword === keywordValue && k.id !== keywordForm.id)) {
    ElMessage.error('该关键词已存在，请使用其他关键词')
    return
  }

  try {
    await tenderApi.createKeyword({ ...keywordForm, keyword: keywordValue })
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchKeywords()
  } catch (error) {
    if (error.response?.data) {
      const errorData = error.response.data
      let errorMessage = '保存失败'
      if (errorData.keyword) {
        const keywordErrors = Array.isArray(errorData.keyword)
          ? errorData.keyword.join('；')
          : errorData.keyword
        errorMessage = `关键词错误：${keywordErrors}`
      } else if (errorData.message) {
        errorMessage = errorData.message
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      }
      ElMessage.error(errorMessage)
    } else {
      ElMessage.error('保存失败')
    }
  }
}

const deleteKeyword = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该关键词吗？', '提示', {
      type: 'warning'
    })
    await tenderApi.deleteKeyword(row.id)
    ElMessage.success('删除成功')
    fetchKeywords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchKeywords()
})
</script>

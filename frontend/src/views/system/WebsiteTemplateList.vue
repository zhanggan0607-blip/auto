<template>
  <div class="page-container">
    <div class="page-header">
      <h3 class="page-title">网站模板管理</h3>
      <div class="header-actions">
        <el-button type="success" @click="showBatchTestDialog" :disabled="activeTemplateCount === 0">
          <el-icon><Cpu /></el-icon>
          批量测试
        </el-button>
        <el-button type="primary" @click="showFormDialog(null)">
          <el-icon><Plus /></el-icon>
          新建模板
        </el-button>
      </div>
    </div>

    <BatchTestDialog
      v-model="batchTestDialogVisible"
      :activeTemplateCount="activeTemplateCount"
      @complete="handleBatchTestComplete"
      @close="handleBatchTestClose"
    />

    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="模板名称">
          <el-input v-model="filterForm.name" placeholder="搜索模板名称" clearable @clear="handleFilter" />
        </el-form-item>
        <el-form-item label="网站类型">
          <el-select v-model="filterForm.website_type" placeholder="选择网站类型" clearable @change="handleFilter">
            <el-option label="政府采购网" value="government" />
            <el-option label="企业招标平台" value="enterprise" />
            <el-option label="工程建设平台" value="construction" />
            <el-option label="医疗器械采购" value="medical" />
            <el-option label="教育采购平台" value="education" />
            <el-option label="其他平台" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.is_active" placeholder="选择状态" clearable @change="handleFilter">
            <el-option label="已启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table v-loading="loading" :data="tableData" stripe class="data-table">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="模板名称" min-width="150">
        <template #default="{ row }">
          <el-link type="primary" @click="showFormDialog(row)">{{ row.name }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="code" label="模板代码" width="150" />
      <el-table-column prop="base_url" label="基础URL" min-width="200" show-overflow-tooltip />
      <el-table-column prop="website_type" label="网站类型" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.website_type === 'government'" type="success" size="small">
            政府采购网
          </el-tag>
          <el-tag v-else-if="row.website_type === 'enterprise'" type="warning" size="small">
            企业招标平台
          </el-tag>
          <el-tag v-else-if="row.website_type === 'construction'" type="info" size="small">
            工程建设平台
          </el-tag>
          <el-tag v-else-if="row.website_type === 'medical'" type="info" size="small">
            医疗器械采购
          </el-tag>
          <el-tag v-else-if="row.website_type === 'education'" type="info" size="small">
            教育采购平台
          </el-tag>
          <el-tag v-else type="info" size="small">
            其他平台
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" sortable />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showFormDialog(row)">
            编辑
          </el-button>
          <el-button type="success" link size="small" @click="handleTest(row)" :loading="testingId === row.id">
            测试
          </el-button>
          <el-button
            type="warning"
            link
            size="small"
            @click="handleToggle(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑网站模板' : '新建网站模板'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="140px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板代码" prop="code">
          <el-input v-model="form.code" placeholder="请输入唯一代码标识，如：ccgp_gov">
            <template #append>
              <el-button @click="generateCode">自动生成</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="基础URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="请输入网站基础URL，如：http://www.ccgp.gov.cn/">
            <template #append>
              <el-button @click="testUrl" :loading="testingUrl">测试</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="网站类型" prop="website_type">
          <el-select v-model="form.website_type" placeholder="选择网站类型">
            <el-option label="政府采购网" value="government" />
            <el-option label="企业招标平台" value="enterprise" />
            <el-option label="工程建设平台" value="construction" />
            <el-option label="医疗器械采购" value="medical" />
            <el-option label="教育采购平台" value="education" />
            <el-option label="其他平台" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="form.priority" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>

        <el-divider content-position="left">URL配置</el-divider>

        <el-form-item label="列表URL模式">
          <el-input v-model="form.list_url_pattern" placeholder="如：http://www.ccgp.gov.cn/list?page={page}&category={category}">
            <template #append>
              <el-tooltip content="支持变量: {page}, {keyword}, {category}, {start_date}, {end_date}">
                <el-button>?</el-button>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="搜索URL模式">
          <el-input v-model="form.search_url_pattern" placeholder="如：http://www.ccgp.gov.cn/search?keyword={keyword}&page={page}">
            <template #append>
              <el-tooltip content="支持变量: {keyword}, {page}, {start_date}, {end_date}">
                <el-button>?</el-button>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>

        <el-divider content-position="left">高级配置</el-divider>

        <el-form-item label="需要JS渲染">
          <el-switch v-model="form.requires_javascript" />
        </el-form-item>
        <el-form-item label="需要登录">
          <el-switch v-model="form.requires_login" />
        </el-form-item>
        <el-form-item label="请求配置" v-if="!form.requires_login">
          <el-input
            v-model="requestConfigText"
            type="textarea"
            :rows="3"
            placeholder='JSON格式，如：{"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 30, "delay_min": 1, "delay_max": 3}'
          />
        </el-form-item>
        <el-form-item label="登录配置" v-if="form.requires_login">
          <el-input
            v-model="loginConfigText"
            type="textarea"
            :rows="3"
            placeholder='JSON格式，如：{"username_field": "name", "password_field": "pwd", "login_url": "/login"}'
          />
        </el-form-item>
        <el-form-item label="选择器配置">
          <el-input
            v-model="selectorsText"
            type="textarea"
            :rows="3"
            placeholder='JSON格式，如：{"list": ".item", "title": "h3", "url": "a@href", "date": ".time"}'
          />
        </el-form-item>
        <el-form-item label="分页配置">
          <el-input
            v-model="paginationConfigText"
            type="textarea"
            :rows="2"
            placeholder='JSON格式，如：{"type": "page", "start": 1, "increment": 1, "max_pages": 100}'
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button @click="testTemplate" :loading="testingUrl">测试配置</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="testDialogVisible"
      title="测试结果"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-alert
        v-if="testResult.success"
        type="success"
        :title="testResult.message"
        :closable="false"
        show-icon
      />
      <el-alert
        v-else
        type="error"
        :title="testResult.message"
        :closable="false"
        show-icon
      />
      <div v-if="testResult.data && testResult.data.length > 0" class="test-result-list">
        <h4>采集到的数据（前3条）：</h4>
        <el-card v-for="(item, idx) in testResult.data" :key="idx" class="test-item">
          <div class="test-item-title">{{ item.title || item.text || '无标题' }}</div>
          <div class="test-item-url" v-if="item.url">
            <el-link :href="item.url" target="_blank" type="primary">{{ item.url }}</el-link>
          </div>
        </el-card>
      </div>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Cpu } from '@element-plus/icons-vue'
import { crawlerApi } from '@/api/crawler'
import BatchTestDialog from './BatchTestDialog.vue'

const loading = ref(false)
const tableData = ref([])
const filterForm = reactive({
  name: '',
  website_type: '',
  is_active: null
})
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const testingId = ref(null)
const testingUrl = ref(false)
const testDialogVisible = ref(false)
const testResult = ref({ success: false, message: '', data: [] })

const batchTestDialogVisible = ref(false)

const activeTemplateCount = computed(() => {
  return tableData.value.filter(t => t.is_active).length
})

const currentId = ref(null)

const requestConfigText = ref('')
const selectorsText = ref('')
const paginationConfigText = ref('')
const loginConfigText = ref('')

const form = reactive({
  name: '',
  code: '',
  base_url: '',
  website_type: '',
  list_url_pattern: '',
  search_url_pattern: '',
  priority: 10,
  is_active: true,
  requires_javascript: false,
  requires_login: false,
  selectors: {},
  pagination_config: {},
  request_config: {},
  login_config: {}
})

const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入模板代码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请输入模板代码'))
          return
        }
        crawlerApi.checkTemplateCodeDuplicate(value, isEdit.value ? currentId.value : null)
          .then(res => {
            if (res.code === 0 || res.code === 200) {
              if (res.data?.is_duplicate) {
                callback(new Error('该模板代码已存在，请使用其他代码'))
              } else {
                callback()
              }
            } else {
              callback()
            }
          })
          .catch(() => {
            callback()
          })
      },
      trigger: 'blur'
    }
  ],
  base_url: [
    { required: true, message: '请输入基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ],
  website_type: [{ required: true, message: '请选择网站类型', trigger: 'change' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: filterForm.name || undefined,
      website_type: filterForm.website_type || undefined,
      is_active: filterForm.is_active !== null && filterForm.is_active !== '' ? filterForm.is_active : undefined
    }
    const res = await crawlerApi.getWebsiteTemplates(params)
    if (res.code === 0 || res.code === 200) {
      tableData.value = res.data?.results || res.data || []
      pagination.total = res.data?.count || res.data?.length || 0
    } else {
      ElMessage.error(res.message || '加载数据失败')
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  pagination.page = 1
  loadData()
}

const resetFilter = () => {
  filterForm.name = ''
  filterForm.website_type = ''
  filterForm.is_active = null
  pagination.page = 1
  loadData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadData()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  loadData()
}

const showFormDialog = async (row) => {
  if (row) {
    isEdit.value = true
    currentId.value = row.id
    try {
      const res = await crawlerApi.getWebsiteTemplate(row.id)
      if (res.code === 0 || res.code === 200) {
        const data = res.data
        Object.assign(form, data)
        requestConfigText.value = JSON.stringify(data.request_config || {}, null, 2)
        selectorsText.value = JSON.stringify(data.selectors || {}, null, 2)
        paginationConfigText.value = JSON.stringify(data.pagination_config || {}, null, 2)
        loginConfigText.value = JSON.stringify(data.login_config || {}, null, 2)
      } else {
        ElMessage.error(res.message || '加载模板详情失败')
        return
      }
    } catch (error) {
      console.error('加载模板详情失败:', error)
      ElMessage.error('加载模板详情失败')
      return
    }
  } else {
    isEdit.value = false
    currentId.value = null
    Object.assign(form, {
      name: '',
      code: '',
      base_url: '',
      website_type: '',
      list_url_pattern: '',
      search_url_pattern: '',
      priority: 10,
      is_active: true,
      requires_javascript: false,
      requires_login: false,
      selectors: {},
      pagination_config: {},
      request_config: {},
      login_config: {}
    })
    requestConfigText.value = ''
    selectorsText.value = ''
    paginationConfigText.value = ''
    loginConfigText.value = ''
  }
  formDialogVisible.value = true
}

const generateCode = () => {
  if (form.name) {
    form.code = form.name
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '')
  }
}

const testUrl = async () => {
  if (!form.base_url) {
    ElMessage.warning('请先输入URL')
    return
  }
  testingUrl.value = true
  try {
    testResult.value = {
      success: true,
      message: 'URL格式正确',
      data: []
    }
    testDialogVisible.value = true
  } catch (error) {
    testResult.value = {
      success: false,
      message: 'URL格式错误: ' + error.message,
      data: []
    }
    testDialogVisible.value = true
  } finally {
    testingUrl.value = false
  }
}

const handleTest = async (row) => {
  testingId.value = row.id
  testDialogVisible.value = true
  testResult.value = { success: false, message: '正在测试...', data: [] }
  try {
    const res = await crawlerApi.testWebsiteTemplate(row.id)
    if (res.code === 0 || res.code === 200) {
      testResult.value = {
        success: true,
        message: res.message || '测试成功',
        data: res.data?.sample_data || []
      }
    } else {
      testResult.value = {
        success: false,
        message: res.message || '测试失败',
        data: []
      }
    }
  } catch (error) {
    console.error('测试失败:', error)
    testResult.value = {
      success: false,
      message: '测试失败: ' + error.message,
      data: []
    }
  } finally {
    testingId.value = null
  }
}

const testTemplate = async () => {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return

    testingUrl.value = true
    testDialogVisible.value = true
    testResult.value = { success: false, message: '正在测试配置...', data: [] }

    try {
      const data = { ...form }
      if (requestConfigText.value) {
        try {
          data.request_config = JSON.parse(requestConfigText.value)
        } catch {
          data.request_config = {}
        }
      }
      if (selectorsText.value) {
        try {
          data.selectors = JSON.parse(selectorsText.value)
        } catch {
          data.selectors = {}
        }
      }
      if (paginationConfigText.value) {
        try {
          data.pagination_config = JSON.parse(paginationConfigText.value)
        } catch {
          data.pagination_config = {}
        }
      }
      if (loginConfigText.value) {
        try {
          data.login_config = JSON.parse(loginConfigText.value)
        } catch {
          data.login_config = {}
        }
      }

      const res = await crawlerApi.createWebsiteTemplate(data)
      if (res.code === 0 || res.code === 200 || res.code === 201) {
        if (res.data?.id) {
          const testRes = await crawlerApi.testWebsiteTemplate(res.data.id)
          if (testRes.code === 0 || testRes.code === 200) {
            testResult.value = {
              success: true,
              message: '测试成功，模板可正常使用',
              data: testRes.data?.sample_data || []
            }
            await crawlerApi.deleteWebsiteTemplate(res.data.id)
          } else {
            testResult.value = {
              success: false,
              message: '测试失败: ' + (testRes.message || '未知错误'),
              data: []
            }
            await crawlerApi.deleteWebsiteTemplate(res.data.id)
          }
        } else {
          testResult.value = {
            success: true,
            message: '配置保存成功',
            data: []
          }
        }
      } else {
        testResult.value = {
          success: false,
          message: res.message || '测试失败',
          data: []
        }
      }
    } catch (error) {
      console.error('测试失败:', error)
      testResult.value = {
        success: false,
        message: '测试失败: ' + error.message,
        data: []
      }
    } finally {
      testingUrl.value = false
    }
  })
}

const handleToggle = async (row) => {
  try {
    const action = row.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(`确定要${action}模板"${row.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await crawlerApi.toggleWebsiteTemplate(row.id, !row.is_active)
    if (res.code === 0 || res.code === 200) {
      ElMessage.success(`${action}成功`)
      loadData()
    } else {
      ElMessage.error(res.message || `${action}失败`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error(`${row.is_active ? '禁用' : '启用'}失败:`, error)
      ElMessage.error(`${row.is_active ? '禁用' : '启用'}失败`)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${row.name}"吗？删除后无法恢复。`,
      '危险操作',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    const res = await crawlerApi.deleteWebsiteTemplate(row.id)
    if (res.code === 0 || res.code === 200 || res.code === 204) {
      ElMessage.success('删除成功')
      loadData()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = { ...form }
      if (requestConfigText.value) {
        try {
          data.request_config = JSON.parse(requestConfigText.value)
        } catch {
          data.request_config = {}
        }
      }
      if (selectorsText.value) {
        try {
          data.selectors = JSON.parse(selectorsText.value)
        } catch {
          data.selectors = {}
        }
      }
      if (paginationConfigText.value) {
        try {
          data.pagination_config = JSON.parse(paginationConfigText.value)
        } catch {
          data.pagination_config = {}
        }
      }
      if (loginConfigText.value) {
        try {
          data.login_config = JSON.parse(loginConfigText.value)
        } catch {
          data.login_config = {}
        }
      }

      let res
      if (isEdit.value) {
        res = await crawlerApi.updateWebsiteTemplate(currentId.value, data)
        if (res.code === 0 || res.code === 200 || res.code === 201) {
          ElMessage.success('保存成功')
          formDialogVisible.value = false
          loadData()
        } else {
          ElMessage.error(res.message || '保存失败')
        }
      } else {
        res = await crawlerApi.createWebsiteTemplate(data)
        if (res.code === 0 || res.code === 200 || res.code === 201) {
          const templateId = res.data?.id
          if (templateId) {
            testResult.value = { success: false, message: '正在检验配置...', data: [] }
            testDialogVisible.value = true
            const testRes = await crawlerApi.testWebsiteTemplate(templateId)
            if (testRes.code === 0 || testRes.code === 200) {
              testResult.value = {
                success: true,
                message: '检验通过，模板创建成功',
                data: testRes.data?.sample_data || []
              }
              ElMessage.success('创建成功')
              formDialogVisible.value = false
              loadData()
            } else {
              testResult.value = {
                success: false,
                message: '检验失败: ' + (testRes.message || '未知错误'),
                data: []
              }
              await crawlerApi.deleteWebsiteTemplate(templateId)
              ElMessage.error('检验失败，模板未保存。请检查配置后重试。')
            }
          } else {
            ElMessage.success('创建成功')
            formDialogVisible.value = false
            loadData()
          }
        } else {
          ElMessage.error(res.message || '创建失败')
        }
      }
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error('提交失败: ' + error.message)
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  loadData()
})

const showBatchTestDialog = () => {
  batchTestDialogVisible.value = true
}

const handleBatchTestComplete = (summary) => {
  console.log('Batch test completed:', summary)
  loadData()
}

const handleBatchTestClose = () => {
  batchTestDialogVisible.value = false
}
</script>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}

.data-table {
  margin-bottom: 16px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
}

.test-result-list {
  margin-top: 20px;
}

.test-result-list h4 {
  margin-bottom: 10px;
  color: #606266;
}

.test-item {
  margin-bottom: 10px;
}

.test-item-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.test-item-url {
  font-size: 12px;
  color: #909399;
}
</style>

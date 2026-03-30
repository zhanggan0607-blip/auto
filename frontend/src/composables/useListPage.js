/**
 * 列表页面通用 Composable
 * 整合搜索、分页、选择、批量操作等常见列表页功能
 */
import { ref, reactive, computed } from 'vue'
import { useMessage } from './usePagination'

/**
 * 列表页面通用Hook
 * @param {Object} options - 配置选项
 * @param {Function} options.fetchApi - 获取列表数据的API函数
 * @param {Function} options.deleteApi - 删除数据的API函数
 * @param {Object} options.defaultSearchParams - 默认搜索参数
 * @param {number} options.defaultPageSize - 默认每页数量
 * @param {Function} options.onFetchSuccess - 获取数据成功回调
 * @param {Function} options.onDeleteSuccess - 删除成功回调
 * @param {Function} options.formatItem - 格式化每条数据的函数
 * @returns {Object} 列表页面相关的状态和方法
 */
export function useListPage(options = {}) {
  const {
    fetchApi,
    deleteApi,
    defaultSearchParams = {},
    defaultPageSize = 20,
    onFetchSuccess = null,
    onDeleteSuccess = null,
    formatItem = null
  } = options

  const message = useMessage()

  const loading = ref(false)
  const list = ref([])
  const selectedIds = ref([])
  const selectAll = ref(false)

  const pagination = reactive({
    page: 1,
    pageSize: defaultPageSize,
    total: 0
  })

  const searchForm = reactive({
    ...defaultSearchParams
  })

  const searchParams = computed(() => {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    Object.keys(searchForm).forEach(key => {
      const value = searchForm[key]
      if (value !== null && value !== undefined && value !== '') {
        if (Array.isArray(value) && value.length > 0) {
          params[key] = value.join(',')
        } else if (!Array.isArray(value)) {
          params[key] = value
        }
      }
    })
    
    return params
  })

  const totalPages = computed(() => {
    return Math.ceil(pagination.total / pagination.pageSize) || 1
  })

  const hasSelection = computed(() => selectedIds.value.length > 0)

  const selectionCount = computed(() => selectedIds.value.length)

  /**
   * 获取列表数据
   */
  const fetchData = async () => {
    if (!fetchApi) return

    loading.value = true
    try {
      const response = await fetchApi(searchParams.value)
      let result = response?.data?.data
      if (result === undefined) {
        result = response?.data
      }
      if (result === undefined) {
        result = response
      }
      if (typeof result !== 'object' || result === null) {
        result = {}
      }

      let items = result.list || result.results || []
      if (!Array.isArray(items)) {
        items = []
      }
      if (formatItem) {
        items = items.map(formatItem)
      }

      list.value = items
      pagination.total = result.total || result.count || result.pagination?.total || 0

      if (onFetchSuccess) {
        await onFetchSuccess(result)
      }

      return {
        success: true,
        data: result
      }
    } catch (error) {
      console.error('获取列表数据失败:', error)
      message.error(error.response?.data?.message || '获取数据失败')
      list.value = []
      return {
        success: false,
        error
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 搜索
   */
  const handleSearch = () => {
    pagination.page = 1
    fetchData()
  }

  /**
   * 重置搜索
   */
  const resetSearch = () => {
    Object.keys(defaultSearchParams).forEach(key => {
      searchForm[key] = defaultSearchParams[key]
    })
    pagination.page = 1
    fetchData()
  }

  /**
   * 刷新数据
   */
  const refresh = () => {
    fetchData()
  }

  /**
   * 页码变化
   */
  const handlePageChange = (page) => {
    pagination.page = page
    fetchData()
  }

  /**
   * 每页数量变化
   */
  const handleSizeChange = (size) => {
    pagination.pageSize = size
    pagination.page = 1
    fetchData()
  }

  /**
   * 选择变化
   */
  const handleSelectionChange = (selection) => {
    selectedIds.value = selection.map(item => item.id)
    selectAll.value = selection.length === list.value.length && list.value.length > 0
  }

  /**
   * 全选/取消全选
   */
  const toggleSelectAll = () => {
    if (selectAll.value) {
      selectedIds.value = list.value.map(item => item.id)
    } else {
      selectedIds.value = []
    }
  }

  /**
   * 清空选择
   */
  const clearSelection = () => {
    selectedIds.value = []
    selectAll.value = false
  }

  /**
   * 删除单条记录
   */
  const handleDelete = async (id, itemName = '') => {
    if (!deleteApi) return { success: false }

    try {
      const { ElMessageBox } = await import('element-plus')
      await ElMessageBox.confirm(
        itemName ? `确定要删除"${itemName}"吗？` : '确定要删除该记录吗？',
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      await deleteApi(id)
      message.deleted()

      if (onDeleteSuccess) {
        await onDeleteSuccess(id)
      }

      await fetchData()
      return { success: true }
    } catch (error) {
      if (error === 'cancel') {
        return { success: false, cancelled: true }
      }
      message.error(error.response?.data?.message || '删除失败')
      return { success: false, error }
    }
  }

  /**
   * 批量删除
   */
  const handleBatchDelete = async () => {
    if (!deleteApi || !hasSelection.value) return { success: false }

    try {
      const { ElMessageBox } = await import('element-plus')
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedIds.value.length} 条记录吗？`,
        '确认批量删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      await Promise.all(selectedIds.value.map(id => deleteApi(id)))
      message.success(`成功删除 ${selectedIds.value.length} 条记录`)
      clearSelection()

      if (onDeleteSuccess) {
        await onDeleteSuccess(selectedIds.value)
      }

      await fetchData()
      return { success: true }
    } catch (error) {
      if (error === 'cancel') {
        return { success: false, cancelled: true }
      }
      message.error(error.response?.data?.message || '批量删除失败')
      return { success: false, error }
    }
  }

  /**
   * 导出数据
   */
  const handleExport = async (exportApi, filename = 'export') => {
    if (!exportApi) return

    try {
      const response = await exportApi(searchParams.value)
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}_${new Date().toISOString().slice(0, 10)}.xlsx`
      link.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
    }
  }

  /**
   * 重置所有状态
   */
  const reset = () => {
    pagination.page = 1
    pagination.total = 0
    list.value = []
    selectedIds.value = []
    selectAll.value = false
    Object.keys(defaultSearchParams).forEach(key => {
      searchForm[key] = defaultSearchParams[key]
    })
  }

  return {
    loading,
    list,
    pagination,
    searchForm,
    searchParams,
    selectedIds,
    selectAll,
    hasSelection,
    selectionCount,
    totalPages,
    fetchData,
    handleSearch,
    resetSearch,
    refresh,
    handlePageChange,
    handleSizeChange,
    handleSelectionChange,
    toggleSelectAll,
    clearSelection,
    handleDelete,
    handleBatchDelete,
    handleExport,
    reset
  }
}

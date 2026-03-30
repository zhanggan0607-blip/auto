/**
 * 删除确认组合式函数
 * 统一处理删除确认弹窗，避免重复代码
 */
import { ElMessageBox } from 'element-plus'

/**
 * 删除确认Hook
 * @param {Object} options - 配置选项
 * @returns {Object} 删除确认相关的方法
 */
export function useDeleteConfirm(options = {}) {
  const {
    confirmTitle = '确认删除',
    confirmMessage = '确定要删除此记录吗？删除后无法恢复。',
    confirmButtonText = '确定',
    cancelButtonText = '取消',
    confirmButtonType = 'danger',
    onConfirmed = null,
    onCancelled = null
  } = options

  /**
   * 执行带确认的删除操作
   * @param {Function} deleteFunction - 删除API函数
   * @param {*} item - 要删除的项（会传递给deleteFunction）
   * @param {string} itemName - 项名称（用于提示信息）
   * @returns {Promise<{success: boolean, error?: Error}>} 删除结果
   */
  const deleteWithConfirm = async (deleteFunction, item, itemName = '') => {
    const customizedMessage = itemName
      ? `确定要删除「${itemName}」吗？删除后无法恢复。`
      : confirmMessage

    try {
      await ElMessageBox.confirm(
        customizedMessage,
        confirmTitle,
        {
          confirmButtonText,
          cancelButtonText,
          type: 'warning',
          confirmButtonType
        }
      )

      if (deleteFunction) {
        await deleteFunction(item)
      }

      if (onConfirmed) {
        onConfirmed(item)
      }

      return { success: true }
    } catch (error) {
      if (error !== 'cancel' && error !== 'close') {
        console.error('删除失败:', error)
        return { success: false, error }
      }

      if (onCancelled) {
        onCancelled(item)
      }

      return { success: false, cancelled: true }
    }
  }

  /**
   * 批量删除确认
   * @param {Function} deleteFunction - 批量删除API函数
   * @param {Array} items - 要删除的项列表
   * @param {number} count - 删除数量（用于提示）
   * @returns {Promise<{success: boolean, error?: Error}>} 删除结果
   */
  const batchDeleteWithConfirm = async (deleteFunction, items, count = null) => {
    const deleteCount = count ?? items.length
    const customizedMessage = `确定要删除选中的 ${deleteCount} 条记录吗？删除后无法恢复。`

    try {
      await ElMessageBox.confirm(
        customizedMessage,
        confirmTitle,
        {
          confirmButtonText: '批量删除',
          cancelButtonText,
          type: 'warning',
          confirmButtonType: 'danger'
        }
      )

      if (deleteFunction) {
        await deleteFunction(items)
      }

      if (onConfirmed) {
        onConfirmed(items)
      }

      return { success: true }
    } catch (error) {
      if (error !== 'cancel' && error !== 'close') {
        console.error('批量删除失败:', error)
        return { success: false, error }
      }

      if (onCancelled) {
        onCancelled(items)
      }

      return { success: false, cancelled: true }
    }
  }

  return {
    deleteWithConfirm,
    batchDeleteWithConfirm
  }
}

/**
 * 使用 CrudTable 的删除确认（快捷方式）
 * 用于在组件中快速集成删除确认
 *
 * 使用示例：
 * ```vue
 * <template>
 *   <el-button @click="handleDelete(row)">删除</el-button>
 * </template>
 *
 * <script setup>
 * import { useDeleteConfirm } from '@/composables/useDeleteConfirm'
 *
 * const { deleteWithConfirm } = useDeleteConfirm({
 *   onConfirmed: () => {
 *     ElMessage.success('删除成功')
 *     fetchData()
 *   }
 * })
 *
 * const handleDelete = (row) => {
 *   deleteWithConfirm(() => enterpriseApi.delete(row.id), row, row.name)
 * }
 * </script>
 * ```
 */
export function useCrudDelete(options = {}) {
  const { deleteConfirm } = useDeleteConfirm(options)

  return {
    handleDelete: (deleteFn, item, name) => deleteConfirm(deleteFn, item, name),
    handleBatchDelete: (deleteFn, items, count) => deleteConfirm(deleteFn, items, count)
  }
}

export default useDeleteConfirm

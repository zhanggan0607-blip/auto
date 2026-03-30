/**
 * 分页和消息提示 Composable
 * 提供 Element Plus ElMessage 的封装
 */
import { ElMessage } from 'element-plus'

export function usePagination() {
  const message = {
    success: (msg = '操作成功') => {
      ElMessage.success(msg)
    },
    error: (msg = '操作失败') => {
      ElMessage.error(msg)
    },
    warning: (msg = '警告') => {
      ElMessage.warning(msg)
    },
    info: (msg = '信息') => {
      ElMessage.info(msg)
    },
    deleted: () => {
      ElMessage.success('删除成功')
    },
    created: () => {
      ElMessage.success('创建成功')
    },
    updated: () => {
      ElMessage.success('更新成功')
    }
  }

  return {
    message
  }
}

export function useMessage() {
  return usePagination().message
}

export default usePagination

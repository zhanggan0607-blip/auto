/**
 * 进度追踪 API
 */
import request from '@/utils/request'

const progressApi = {
  /**
   * 创建进度任务
   */
  createTask(data) {
    return request.post('/v1/progress/tasks/', data)
  },

  /**
   * 获取任务状态
   */
  getTaskStatus(taskId) {
    return request.get(`/v1/progress/tasks/${taskId}/`)
  },

  /**
   * 开始任务
   */
  startTask(taskId) {
    return request.post(`/v1/progress/tasks/${taskId}/start/`)
  },

  /**
   * 更新进度
   */
  updateProgress(taskId, data) {
    return request.post(`/v1/progress/tasks/${taskId}/progress/`, data)
  },

  /**
   * 完成任务
   */
  completeTask(taskId, data) {
    return request.post(`/v1/progress/tasks/${taskId}/complete/`, data || {})
  },

  /**
   * 手动结束任务
   */
  manuallyEndTask(taskId, data) {
    return request.post(`/v1/progress/tasks/${taskId}/end/`, data || {})
  },

  /**
   * 取消任务
   */
  cancelTask(taskId) {
    return request.post(`/v1/progress/tasks/${taskId}/cancel/`)
  },

  /**
   * 标记失败
   */
  failTask(taskId, error) {
    return request.post(`/v1/progress/tasks/${taskId}/fail/`, { error })
  },

  /**
   * 获取所有任务
   */
  listTasks() {
    return request.get('/v1/progress/tasks/')
  },

  /**
   * 删除任务
   */
  deleteTask(taskId) {
    return request.delete(`/v1/progress/tasks/${taskId}/`)
  }
}

export default progressApi
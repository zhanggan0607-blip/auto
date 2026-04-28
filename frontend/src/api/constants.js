/**
 * 状态常量API
 * 从后端获取状态常量定义
 */
import request from '@/utils/request'

const BASE_URL = '/v1/constants'

const constantsApi = {
  /**
   * 获取所有状态常量
   */
  getAllConstants() {
    return request.get(BASE_URL + '/')
  },

  /**
   * 获取指定类型的状态常量
   * @param {string} constantType - 常量类型
   */
  getConstantsByType(constantType) {
    return request.get(`${BASE_URL}/${constantType}/`)
  },

  /**
   * 获取招标状态
   */
  getTenderStatus() {
    return this.getConstantsByType('tender_status')
  },

  /**
   * 获取投标状态
   */
  getBidStatus() {
    return this.getConstantsByType('bid_status')
  },

  /**
   * 获取文档状态
   */
  getDocumentStatus() {
    return this.getConstantsByType('document_status')
  },

  /**
   * 获取通知状态
   */
  getNotificationStatus() {
    return this.getConstantsByType('notification_status')
  },

  /**
   * 获取企业类型
   */
  getEnterpriseType() {
    return this.getConstantsByType('enterprise_type')
  },

  /**
   * 获取资质等级
   */
  getQualificationLevel() {
    return this.getConstantsByType('qualification_level')
  },

  /**
   * 获取优先级
   */
  getPriority() {
    return this.getConstantsByType('priority')
  }
}

export { constantsApi }
export default constantsApi

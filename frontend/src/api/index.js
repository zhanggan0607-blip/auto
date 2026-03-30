/**
 * API统一导出模块
 *
 * 提供统一的API导入方式，简化各页面的import语句
 *
 * 使用示例：
 * // 旧写法
 * import { authApi } from '@/api/auth'
 * import { enterpriseApi } from '@/api/enterprise'
 * import { tenderApi } from '@/api/tender'
 *
 * // 新写法（推荐）
 * import { authApi, enterpriseApi, tenderApi } from '@/api'
 *
 * // 或者直接导入所有
 * import api from '@/api'
 * api.auth.login(...)
 * api.enterprise.getList(...)
 */

// 基础工具导出
export { createApi, ApiClient, ApiError } from './base'

export { authApi } from './auth'
export { enterpriseApi } from './enterprise'
export { tenderApi } from './tender'
export { bidApi } from './bid'
export { documentApi } from './document'
export { crawlerApi } from './crawler'
export { notificationApi } from './notification'
export { vectorlibApi } from './vectorlib'
export { constantsApi } from './constants'
export { automationConfigApi } from './automationConfig'
export { userAdminApi } from './userAdmin'
export { modelApi } from './model'

import { authApi } from './auth'
import { enterpriseApi } from './enterprise'
import { tenderApi } from './tender'
import { bidApi } from './bid'
import { documentApi } from './document'
import { crawlerApi } from './crawler'
import { notificationApi } from './notification'
import { vectorlibApi } from './vectorlib'
import { constantsApi } from './constants'
import { automationConfigApi } from './automationConfig'
import { userAdminApi } from './userAdmin'
import { modelApi } from './model'

const api = {
  auth: authApi,
  enterprise: enterpriseApi,
  tender: tenderApi,
  bid: bidApi,
  document: documentApi,
  crawler: crawlerApi,
  notification: notificationApi,
  vectorlib: vectorlibApi,
  constants: constantsApi,
  automationConfig: automationConfigApi,
  userAdmin: userAdminApi,
  model: modelApi
}

export default api

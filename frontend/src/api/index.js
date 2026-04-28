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
export { modelApi } from './model'
export { userAdminApi } from './userAdmin'

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
import { modelApi } from './model'
import { userAdminApi } from './userAdmin'

export default {
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
  model: modelApi,
  userAdmin: userAdminApi,
}

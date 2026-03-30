/**
 * 状态常量和工具函数（已废弃，请使用 @/store/constants）
 *
 * 此文件仅用于向后兼容，新代码请直接从 @/store/constants 导入
 *
 * 已迁移到 @/store/constants 的功能：
 * - getStatusType, getLabelByValue
 * - getTenderStatusType, getTenderStatusText
 * - getBidStatusType, getBidStatusText
 * - getDocStatusType, getDocStatusText
 * - getEnterpriseDocStatusType, getEnterpriseDocStatusText
 * - getCrawlerStatusType, getCrawlerStatusText
 * - getScheduleStatusType, getScheduleStatusText
 * - getMatchLevelType, getMatchLevelText
 * - getContactTypeText, getMatchRuleTypeText
 * - TENDER_STATUS, BID_STATUS, MATCH_LEVEL, CONTACT_TYPE, MATCH_RULE_TYPE, RESULT_TYPE
 * - getResultType, getResultText, formatMoney, formatPercent
 *
 * 仍在 @/utils/date 中的功能：
 * - formatDate, formatDateTime (请使用 @/utils/date)
 *
 * 使用示例：
 * // 旧写法（仍可用，但推荐使用新写法）
 * import { getTenderStatusText } from '@/utils/status'
 *
 * // 新写法
 * import { getTenderStatusText } from '@/store/constants'
 */

export {
  getStatusType,
  getLabelByValue,
  formatMoney,
  formatPercent,
  getTenderStatusType,
  getTenderStatusText,
  getBidStatusType,
  getBidStatusText,
  getDocStatusType,
  getDocStatusText,
  getEnterpriseDocStatusType,
  getEnterpriseDocStatusText,
  getCrawlerStatusType,
  getCrawlerStatusText,
  getScheduleStatusType,
  getScheduleStatusText,
  getMatchLevelType,
  getMatchLevelText,
  getContactTypeText,
  getMatchRuleTypeText,
  getResultType,
  getResultText,
  TENDER_STATUS,
  BID_STATUS,
  MATCH_LEVEL,
  CONTACT_TYPE,
  MATCH_RULE_TYPE,
  RESULT_TYPE,
  CRAWLER_STATUS,
  ENTERPRISE_DOC_STATUS
} from '@/store/constants'

export { formatDate, formatDateTime } from '@/utils/date'

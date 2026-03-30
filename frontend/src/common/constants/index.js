/**
 * 统一错误码和状态码定义
 * 与后端 ErrorCode 枚举保持一致
 */

export const ErrorCode = {
  // 通用错误 (1xxx)
  SUCCESS: '0',
  INTERNAL_ERROR: '1000',
  INVALID_PARAMETER: '1001',
  MISSING_PARAMETER: '1002',
  INVALID_FORMAT: '1003',
  NOT_FOUND: '1004',
  ALREADY_EXISTS: '1005',
  OPERATION_FAILED: '1006',
  TIMEOUT: '1007',
  PERMISSION_DENIED: '1008',
  RATE_LIMITED: '1009',
  SERVICE_UNAVAILABLE: '1010',

  // 认证授权错误 (2xxx)
  AUTH_TOKEN_EXPIRED: '2001',
  AUTH_TOKEN_INVALID: '2002',
  AUTH_TOKEN_MISSING: '2003',
  AUTH_CREDENTIALS_INVALID: '2004',
  AUTH_REFRESH_TOKEN_EXPIRED: '2005',
  AUTH_REFRESH_TOKEN_INVALID: '2006',

  // 用户相关错误 (3xxx)
  USER_NOT_FOUND: '3001',
  USER_DISABLED: '3002',
  USER_ALREADY_EXISTS: '3003',
  USER_PASSWORD_INVALID: '3004',
  USER_PASSWORD_WRONG: '3005',

  // 企业相关错误 (4xxx)
  ENTERPRISE_NOT_FOUND: '4001',
  ENTERPRISE_DISABLED: '4002',
  ENTERPRISE_ALREADY_EXISTS: '4003',
  ENTERPRISE_CREDIT_CODE_INVALID: '4004',
  QUALIFICATION_EXPIRED: '4006',

  // 招标相关错误 (5xxx)
  TENDER_NOT_FOUND: '5001',
  TENDER_DEADLINE_PASSED: '5002',
  TENDER_ALREADY_FAVORITED: '5004',

  // 投标相关错误 (6xxx)
  BID_NOT_FOUND: '6001',
  BID_ALREADY_SUBMITTED: '6002',
  BID_ALREADY_WITHDRAWN: '6003',

  // 文档相关错误 (7xxx)
  DOCUMENT_NOT_FOUND: '7001',
  DOCUMENT_UPLOAD_FAILED: '7002',
  DOCUMENT_FORMAT_NOT_SUPPORTED: '7003',
  DOCUMENT_TOO_LARGE: '7004',

  // 爬虫相关错误 (8xxx)
  CRAWLER_NOT_FOUND: '8001',
  CRAWLER_RUNNING: '8002',
  CRAWLER_FAILED: '8003',
  CRAWLER_TIMEOUT: '8005',

  // 向量库相关错误 (9xxx)
  VECTOR_NOT_FOUND: '9001',
  VECTOR_SYNC_FAILED: '9002',
  VECTOR_SEARCH_FAILED: '9003',

  // LLM相关错误 (11xx)
  LLM_PROVIDER_NOT_FOUND: '11001',
  LLM_MODEL_NOT_FOUND: '11002',
  LLM_API_ERROR: '11003',
  LLM_TIMEOUT: '11005',
}

export const ErrorMessage = {
  [ErrorCode.SUCCESS]: '操作成功',
  [ErrorCode.INTERNAL_ERROR]: '服务器内部错误',
  [ErrorCode.INVALID_PARAMETER]: '参数无效',
  [ErrorCode.MISSING_PARAMETER]: '缺少必要参数',
  [ErrorCode.NOT_FOUND]: '资源不存在',
  [ErrorCode.ALREADY_EXISTS]: '资源已存在',
  [ErrorCode.PERMISSION_DENIED]: '权限不足',
  [ErrorCode.RATE_LIMITED]: '请求过于频繁',
  [ErrorCode.AUTH_TOKEN_EXPIRED]: 'Token已过期，请重新登录',
  [ErrorCode.AUTH_TOKEN_INVALID]: 'Token无效',
  [ErrorCode.AUTH_TOKEN_MISSING]: '请先登录',
  [ErrorCode.AUTH_CREDENTIALS_INVALID]: '用户名或密码错误',
  [ErrorCode.USER_NOT_FOUND]: '用户不存在',
  [ErrorCode.USER_DISABLED]: '用户已被禁用',
  [ErrorCode.ENTERPRISE_NOT_FOUND]: '企业不存在',
  [ErrorCode.TENDER_NOT_FOUND]: '招标信息不存在',
  [ErrorCode.TENDER_DEADLINE_PASSED]: '招标已截止',
  [ErrorCode.BID_NOT_FOUND]: '投标记录不存在',
  [ErrorCode.DOCUMENT_NOT_FOUND]: '文档不存在',
  [ErrorCode.CRAWLER_FAILED]: '采集任务执行失败',
}

export const HttpStatus = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
}

export function getErrorMessage(code, fallbackMessage) {
  return ErrorMessage[code] || fallbackMessage || '操作失败'
}

export function isSuccessCode(code) {
  return code === 0 || code === ErrorCode.SUCCESS
}

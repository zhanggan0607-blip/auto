/**
 * API响应类型定义
 * @module types/index
 */

/**
 * 通用API响应
 * @template T - 响应数据类型
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/**
 * 分页响应
 * @template T - 列表项类型
 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * 分页参数
 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/**
 * 排序参数
 */
export interface SortParams {
  ordering?: string
}

/**
 * 搜索参数
 */
export interface SearchParams {
  search?: string
}

/**
 * 通用查询参数
 */
export interface QueryParams extends PaginationParams, SortParams, SearchParams {
  [key: string]: any
}

/**
 * 企业信息
 */
export interface Enterprise {
  id: number
  name: string
  short_name?: string
  credit_code?: string
  legal_person?: string
  registered_capital?: number
  establishment_date?: string
  province?: string
  city?: string
  district?: string
  address?: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  bank_name?: string
  bank_account?: string
  enterprise_type?: EnterpriseType
  enterprise_scale?: EnterpriseScale
  staff_count?: number
  insured_count?: number
  business_scope?: string
  auto_bid_enabled: boolean
  auto_bid_threshold: number
  auto_upload_enabled: boolean
  auto_bid_keywords?: string[]
  notification_channels?: NotificationChannel[]
  tags?: string[]
  extra_info?: Record<string, any>
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

/**
 * 企业类型
 */
export type EnterpriseType = 'limited' | 'joint_stock' | 'sole_proprietorship' | 'partnership' | 'other'

/**
 * 企业规模
 */
export type EnterpriseScale = '大型' | '中型' | '小型' | '微型'

/**
 * 企业资质
 */
export interface EnterpriseQualification {
  id: number
  enterprise: number
  qualification_name: string
  qualification_type: QualificationType
  qualification_type_display?: string
  grade: string
  certificate_number?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
  scope?: string
  is_valid: boolean
  status?: string
  status_display?: string
  created_at: string
  updated_at: string
}

/**
 * 资质类型
 */
export type QualificationType = 'general_contractor' | 'professional_contractor' | 'labor_subcontractor' | 'design' | 'supervision' | 'other'

/**
 * 企业业绩
 */
export interface EnterprisePerformance {
  id: number
  enterprise: number
  project_name: string
  project_location?: string
  contract_amount?: number
  start_date?: string
  end_date?: string
  project_type?: PerformanceType
  client_name?: string
  client_contact?: string
  client_phone?: string
  description?: string
  is_verified?: boolean
  created_at: string
  updated_at: string
}

/**
 * 业绩类型
 */
export type PerformanceType = 'construction' | 'decoration' | 'installation' | 'municipal' | 'other'

/**
 * 企业关键人员
 */
export interface EnterpriseKeyPersonnel {
  id: number
  enterprise: number
  personnel_type: PersonnelType
  personnel_type_display?: string
  personnel_id?: string
  name: string
  id_number?: string
  birth_date?: string
  gender?: 'male' | 'female'
  phone?: string
  email?: string
  education?: string
  major?: string
  builder_certificate?: string
  builder_certificate_file?: string
  builder_certificate_file_url?: string
  builder_level?: BuilderLevel
  builder_major?: string
  safety_certificate_b?: string
  safety_certificate_b_file?: string
  safety_certificate_b_file_url?: string
  engineer_title_certificate?: string
  engineer_certificate_file?: string
  engineer_certificate_file_url?: string
  title_level?: string
  certificate_number?: string
  certificate_major?: string
  certificate_valid_from?: string
  certificate_valid_to?: string
  expiry_date?: string
  issuing_authority?: string
  issuing_unit?: string
  social_security_proof?: string
  social_security_proof_url?: string
  no_project_commitment?: string
  no_project_commitment_url?: string
  labor_contract?: string
  labor_contract_url?: string
  similar_performance_proof?: string
  similar_performance_proof_url?: string
  is_registered_locally?: boolean
  social_security_code?: string
  professional_years?: number
  officer_type?: string
  officer_type_display?: string
  certificate_status?: CertificateStatus
  certificate_status_display?: string
  remark?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 人员类型
 */
export type PersonnelType = 'project_manager' | 'technical_director' | 'professional_engineer' | 'eight_officers'

/**
 * 建造师等级
 */
export type BuilderLevel = 'first' | 'second' | 'third'

/**
 * 证书状态
 */
export type CertificateStatus = 'valid' | 'expiring' | 'expired'

/**
 * 企业文档
 */
export interface EnterpriseDocument {
  id: number
  enterprise: number
  document_type: DocumentType
  document_type_display?: string
  document_name: string
  document_no?: string
  file_path?: string
  file_url?: string
  issue_date?: string
  expiry_date?: string
  issuing_authority?: string
  is_primary?: boolean
  status?: DocumentStatus
  status_display?: string
  remark?: string
  created_at: string
  updated_at: string
}

/**
 * 文档类型
 */
export type DocumentType = 'business_license' | 'qualification' | 'safety_license' | 'iso_certificate' | 'other'

/**
 * 文档状态
 */
export type DocumentStatus = 'valid' | 'expiring' | 'expired' | 'pending'

/**
 * 企业联系人
 */
export interface EnterpriseContact {
  id: number
  enterprise: number
  name: string
  contact_type: ContactType
  contact_type_display?: string
  position?: string
  phone?: string
  mobile?: string
  email?: string
  wechat?: string
  is_primary: boolean
  is_active: boolean
  remark?: string
  created_at: string
  updated_at: string
}

/**
 * 联系人类型
 */
export type ContactType = 'business' | 'technical' | 'finance' | 'hr' | 'other'

/**
 * 匹配规则
 */
export interface EnterpriseMatchRule {
  id: number
  enterprise: number
  name: string
  rule_type: MatchRuleType
  rule_type_display?: string
  keywords?: string[]
  exclude_keywords?: string[]
  regions?: string[]
  industries?: string[]
  min_budget?: number
  max_budget?: number
  priority: number
  weight: number
  is_active: boolean
  description?: string
  created_at: string
  updated_at: string
}

/**
 * 匹配规则类型
 */
export type MatchRuleType = 'keyword' | 'region' | 'industry' | 'budget' | 'custom'

/**
 * 招标项目
 */
export interface TenderProject {
  id: number
  title: string
  tender_no?: string
  tender_type?: string
  tender_method?: string
  budget?: number
  deposit?: number
  description?: string
  requirements?: string
  region?: string
  province?: string
  city?: string
  district?: string
  industry?: string
  source_url?: string
  source_website?: string
  publish_date?: string
  deadline?: string
  open_date?: string
  contact_person?: string
  contact_phone?: string
  status: TenderStatus
  keywords_matched?: Record<string, any>
  match_score?: number
  is_favorited?: boolean
  created_at: string
  updated_at: string
}

/**
 * 招标状态
 */
export type TenderStatus = 'draft' | 'published' | 'closed' | 'awarded' | 'cancelled'

/**
 * 投标记录
 */
export interface BidRecord {
  id: number
  tender: number
  tender_title?: string
  enterprise: number
  enterprise_name?: string
  bid_amount?: number
  bid_date?: string
  bid_status: BidStatus
  bid_status_display?: string
  result_type?: ResultType
  result_type_display?: string
  win_amount?: number
  win_date?: string
  contract_no?: string
  contract_amount?: number
  contract_date?: string
  remark?: string
  created_by_name?: string
  created_at: string
  updated_at: string
}

/**
 * 投标状态
 */
export type BidStatus = 'preparing' | 'submitted' | 'opened' | 'pending' | 'won' | 'lost' | 'withdrawn'

/**
 * 中标结果类型
 */
export type ResultType = 'won' | 'lost' | 'pending'

/**
 * 文档模板
 */
export interface DocumentTemplate {
  id: number
  name: string
  template_type: string
  description?: string
  file_path?: string
  file_url?: string
  variables?: Record<string, any>
  is_active: boolean
  created_by_name?: string
  created_at: string
  updated_at: string
}

/**
 * 生成的文档
 */
export interface GeneratedDocument {
  id: number
  name: string
  template: number
  template_name?: string
  tender: number
  tender_title?: string
  file_path?: string
  file_url?: string
  pdf_path?: string
  pdf_url?: string
  variables_data?: Record<string, any>
  status: string
  version: number
  notes?: string
  created_by_name?: string
  reviewed_by_name?: string
  reviewed_at?: string
  created_at: string
  updated_at: string
}

/**
 * 用户信息
 */
export interface User {
  id: number
  username: string
  email?: string
  first_name?: string
  last_name?: string
  role?: UserRole
  is_active: boolean
  is_staff: boolean
  date_joined: string
  last_login?: string
}

/**
 * 用户角色
 */
export type UserRole = 'admin' | 'manager' | 'operator' | 'viewer'

/**
 * 用户详情
 */
export interface UserProfile {
  id: number
  user: number
  avatar?: string
  phone?: string
  department?: string
  position?: string
  notification_enabled: boolean
  email_notification: boolean
  sms_notification: boolean
  created_at: string
  updated_at: string
}

/**
 * 登录请求
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  user: User
  token: {
    access: string
    refresh: string
  }
}

/**
 * Token刷新响应
 */
export interface TokenRefreshResponse {
  access: string
  refresh?: string
}

/**
 * 通知消息
 */
export interface Notification {
  id: number
  title: string
  content: string
  notification_type: NotificationType
  notification_type_display?: string
  priority: NotificationPriority
  priority_display?: string
  is_read: boolean
  read_at?: string
  link?: string
  extra_data?: Record<string, any>
  created_at: string
}

/**
 * 通知类型
 */
export type NotificationType = 'system' | 'tender' | 'bid' | 'task' | 'alert'

/**
 * 通知优先级
 */
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

/**
 * 通知渠道
 */
export type NotificationChannel = 'email' | 'sms' | 'wechat' | 'dingtalk'

/**
 * 向量库文档
 */
export interface VectorDocument {
  id: number
  title: string
  document_type: string
  document_type_display?: string
  file_path?: string
  file_url?: string
  content?: string
  chunk_count?: number
  vector_status: VectorStatus
  vector_status_display?: string
  is_indexed: boolean
  indexed_at?: string
  tags?: string[]
  metadata?: Record<string, any>
  created_by_name?: string
  created_at: string
  updated_at: string
}

/**
 * 向量状态
 */
export type VectorStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * 采集计划
 */
export interface CrawlSchedule {
  id: number
  name: string
  description?: string
  website: string
  website_display?: string
  crawl_type: CrawlType
  crawl_type_display?: string
  crontab: string
  is_active: boolean
  last_run?: string
  next_run?: string
  run_count: number
  success_count: number
  fail_count: number
  config?: Record<string, any>
  created_by_name?: string
  created_at: string
  updated_at: string
}

/**
 * 采集类型
 */
export type CrawlType = 'tender' | 'enterprise' | 'result' | 'other'

/**
 * 表格查询参数
 */
export interface TableQueryParams extends QueryParams {
  status?: string
  is_active?: boolean
  start_date?: string
  end_date?: string
}

/**
 * 文件上传响应
 */
export interface FileUploadResponse {
  id: number
  name: string
  file_path: string
  file_url: string
  file_size: number
  file_type: string
  created_at: string
}

/**
 * 统计数据
 */
export interface Statistics {
  total: number
  active: number
  inactive: number
  today: number
  this_week: number
  this_month: number
}

/**
 * 仪表盘统计数据
 */
export interface DashboardStatistics {
  tenders: Statistics
  bids: Statistics
  enterprises: Statistics
  notifications: Statistics
}

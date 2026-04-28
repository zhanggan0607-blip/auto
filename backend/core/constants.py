"""
通用状态常量和选项定义

此模块定义了系统中多个模块共用的状态常量和选项，
避免在各模型中重复定义。
"""
from enum import Enum


# ==================== Agent相关枚举 ====================

class AgentStatus(Enum):
    """
    Agent状态枚举
    """
    IDLE = 'idle'
    RUNNING = 'running'
    PAUSED = 'paused'
    ERROR = 'error'
    STOPPED = 'stopped'
    WAITING = 'waiting'


class AgentType(Enum):
    """
    Agent类型枚举
    """
    COLLECTOR = 'collector'
    PARSER = 'parser'
    MATCHER = 'matcher'
    ANALYST = 'analyst'
    GENERATOR = 'generator'
    REVIEWER = 'reviewer'
    OPTIMIZER = 'optimizer'
    UPLOADER = 'uploader'
    TRACKER = 'tracker'
    ORCHESTRATOR = 'orchestrator'
    SUPERVISOR = 'supervisor'


class AgentCapability(Enum):
    """
    Agent能力枚举
    """
    CRAWLING = 'crawling'
    PARSING = 'parsing'
    MATCHING = 'matching'
    ANALYZING = 'analyzing'
    GENERATING = 'generating'
    REVIEWING = 'reviewing'
    OPTIMIZING = 'optimizing'
    UPLOADING = 'uploading'
    TRACKING = 'tracking'
    ORCHESTRATING = 'orchestrating'
    CHATTING = 'chatting'
    CODING = 'coding'


# ==================== 爬虫相关枚举 ====================

class CrawlStrategy(Enum):
    """
    采集策略枚举
    """
    API = 'api'
    HEADLESS = 'headless'
    STEALTH = 'stealth'
    HUMAN = 'human'


class CrawlStatus(Enum):
    """
    采集状态枚举
    """
    SUCCESS = 'success'
    FAILED = 'failed'
    RETRY = 'retry'
    FALLBACK = 'fallback'


# ==================== 工作流相关枚举 ====================

class WorkflowStatus(Enum):
    """
    工作流状态枚举
    """
    PENDING = 'pending'
    RUNNING = 'running'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class StageStatus(Enum):
    """
    工作流阶段状态枚举
    """
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


class ExecutionStatus(Enum):
    """
    执行状态枚举
    """
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'


class MessageRole(Enum):
    """
    Agent消息角色枚举 - 标准消息格式
    """
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    AGENT = 'agent'
    TOOL = 'tool'


class MessageType(Enum):
    """
    Agent消息类型枚举
    """
    TEXT = 'text'
    CODE = 'code'
    TOOL_CALL = 'tool_call'
    TOOL_RESULT = 'tool_result'
    ERROR = 'error'
    STATUS = 'status'
    HEARTBEAT = 'heartbeat'


# ==================== 通用状态 ====================

STATUS_PENDING = 'pending'
STATUS_PROCESSING = 'processing'
STATUS_SUBMITTED = 'submitted'
STATUS_COMPLETED = 'completed'
STATUS_FAILED = 'failed'
STATUS_CANCELLED = 'cancelled'

STATUS_CHOICES_COMMON = [
    (STATUS_PENDING, '待处理'),
    (STATUS_PROCESSING, '处理中'),
    (STATUS_SUBMITTED, '已提交'),
    (STATUS_COMPLETED, '已完成'),
    (STATUS_FAILED, '失败'),
    (STATUS_CANCELLED, '已取消'),
]

# ==================== 招标项目状态 ====================

TENDER_STATUS_PENDING = 'pending'
TENDER_STATUS_PROCESSING = 'processing'
TENDER_STATUS_SUBMITTED = 'submitted'
TENDER_STATUS_WON = 'won'
TENDER_STATUS_LOST = 'lost'
TENDER_STATUS_EXPIRED = 'expired'

TENDER_STATUS_CHOICES = [
    (TENDER_STATUS_PENDING, '待处理'),
    (TENDER_STATUS_PROCESSING, '处理中'),
    (TENDER_STATUS_SUBMITTED, '已投标'),
    (TENDER_STATUS_WON, '已中标'),
    (TENDER_STATUS_LOST, '未中标'),
    (TENDER_STATUS_EXPIRED, '已过期'),
]

# ==================== 投标记录状态 ====================

BID_STATUS_PREPARING = 'preparing'
BID_STATUS_SUBMITTED = 'submitted'
BID_STATUS_REVIEWING = 'reviewing'
BID_STATUS_WON = 'won'
BID_STATUS_LOST = 'lost'
BID_STATUS_WITHDRAWN = 'withdrawn'

BID_STATUS_CHOICES = [
    (BID_STATUS_PREPARING, '准备中'),
    (BID_STATUS_SUBMITTED, '已提交'),
    (BID_STATUS_REVIEWING, '评审中'),
    (BID_STATUS_WON, '已中标'),
    (BID_STATUS_LOST, '未中标'),
    (BID_STATUS_WITHDRAWN, '已撤回'),
]

# ==================== 中标结果类型 ====================

RESULT_TYPE_WIN = 'win'
RESULT_TYPE_LOSE = 'lose'
RESULT_TYPE_PENDING = 'pending'

RESULT_TYPE_CHOICES = [
    (RESULT_TYPE_WIN, '中标'),
    (RESULT_TYPE_LOSE, '未中标'),
    (RESULT_TYPE_PENDING, '待定'),
]

# ==================== 爬虫任务状态 ====================

CRAWLER_STATUS_PENDING = 'pending'
CRAWLER_STATUS_RUNNING = 'running'
CRAWLER_STATUS_COMPLETED = 'completed'
CRAWLER_STATUS_FAILED = 'failed'

CRAWLER_STATUS_CHOICES = [
    (CRAWLER_STATUS_PENDING, '待执行'),
    (CRAWLER_STATUS_RUNNING, '执行中'),
    (CRAWLER_STATUS_COMPLETED, '已完成'),
    (CRAWLER_STATUS_FAILED, '执行失败'),
]

# ==================== 定时任务状态 ====================

SCHEDULE_STATUS_ACTIVE = 'active'
SCHEDULE_STATUS_PAUSED = 'paused'
SCHEDULE_STATUS_DELETED = 'deleted'

SCHEDULE_STATUS_CHOICES = [
    (SCHEDULE_STATUS_ACTIVE, '启用'),
    (SCHEDULE_STATUS_PAUSED, '暂停'),
    (SCHEDULE_STATUS_DELETED, '已删除'),
]

# ==================== 通知状态 ====================

NOTIFICATION_STATUS_PENDING = 'pending'
NOTIFICATION_STATUS_SENT = 'sent'
NOTIFICATION_STATUS_FAILED = 'failed'

NOTIFICATION_STATUS_CHOICES = [
    (NOTIFICATION_STATUS_PENDING, '待发送'),
    (NOTIFICATION_STATUS_SENT, '已发送'),
    (NOTIFICATION_STATUS_FAILED, '发送失败'),
]

# ==================== 文档状态 ====================

DOCUMENT_STATUS_DRAFT = 'draft'
DOCUMENT_STATUS_GENERATED = 'generated'
DOCUMENT_STATUS_REVIEWED = 'reviewed'
DOCUMENT_STATUS_SUBMITTED = 'submitted'

DOCUMENT_STATUS_CHOICES = [
    (DOCUMENT_STATUS_DRAFT, '草稿'),
    (DOCUMENT_STATUS_GENERATED, '已生成'),
    (DOCUMENT_STATUS_REVIEWED, '已审核'),
    (DOCUMENT_STATUS_SUBMITTED, '已提交'),
]

# ==================== 向量库状态 ====================

VECTOR_STATUS_PENDING = 'pending'
VECTOR_STATUS_PROCESSING = 'processing'
VECTOR_STATUS_INDEXED = 'indexed'
VECTOR_STATUS_FAILED = 'failed'

VECTOR_STATUS_CHOICES = [
    (VECTOR_STATUS_PENDING, '待处理'),
    (VECTOR_STATUS_PROCESSING, '处理中'),
    (VECTOR_STATUS_INDEXED, '已索引'),
    (VECTOR_STATUS_FAILED, '失败'),
]

# ==================== 建造师等级 ====================

BUILDER_LEVEL_FIRST = 'first'
BUILDER_LEVEL_SECOND = 'second'
BUILDER_LEVEL_NONE = 'none'

BUILDER_LEVEL_CHOICES = [
    (BUILDER_LEVEL_FIRST, '一级注册建造师'),
    (BUILDER_LEVEL_SECOND, '二级注册建造师'),
    (BUILDER_LEVEL_NONE, '不作要求'),
]

# ==================== 建造师专业 ====================

BUILDER_MAJOR_CHOICES = [
    ('architecture', '建筑工程'),
    ('municipal', '市政公用工程'),
    ('mechanical_electrical', '机电工程'),
    ('highway', '公路工程'),
    ('water_conservancy', '水利水电工程'),
    ('communication', '通信与广电工程'),
    ('mining', '矿业工程'),
    ('railway', '铁路工程'),
    ('aviation', '民航机场工程'),
    ('port', '港口与航道工程'),
]

# ==================== 资质等级 ====================

QUALIFICATION_LEVEL_SPECIAL = 'special'
QUALIFICATION_LEVEL_FIRST = 'first'
QUALIFICATION_LEVEL_SECOND = 'second'
QUALIFICATION_LEVEL_THIRD = 'third'
QUALIFICATION_LEVEL_FOURTH = 'fourth'

QUALIFICATION_LEVEL_CHOICES = [
    (QUALIFICATION_LEVEL_SPECIAL, '特级'),
    (QUALIFICATION_LEVEL_FIRST, '一级'),
    (QUALIFICATION_LEVEL_SECOND, '二级'),
    (QUALIFICATION_LEVEL_THIRD, '三级'),
    (QUALIFICATION_LEVEL_FOURTH, '四级'),
]

# ==================== 工程勘察资质等级 ====================
# 综合资质：只设甲级
# 专业资质（岩土工程、水文地质勘察、工程测量）：甲级、乙级、丙级；岩土工程（分项）：甲、乙两级
# 劳务资质：不分等级

QUALIFICATION_LEVEL_SURVEY_COMPREHENSIVE_CHOICES = [
    ('survey_first', '甲级'),
]

QUALIFICATION_LEVEL_SURVEY_PROFESSIONAL_CHOICES = [
    ('survey_first', '甲级'),
    ('survey_second', '乙级'),
    ('survey_third', '丙级'),
]

QUALIFICATION_LEVEL_SURVEY_GEOTECHNICAL_SUB_CHOICES = [
    ('survey_first', '甲级'),
    ('survey_second', '乙级'),
]

# ==================== 工程勘察资质名称（详细分类） ====================

QUALIFICATION_SURVEY_CHOICES = [
    # 综合资质
    ('survey_comprehensive', '综合资质（工程勘察）'),
    # 岩土工程专业
    ('survey_geotechnical', '岩土工程专业'),
    ('survey_geotechnical_survey', '岩土工程勘察'),
    ('survey_geotechnical_design', '岩土工程设计'),
    ('survey_geotechnical_testing', '岩土工程物探测试检测监测'),
    # 水文地质勘察专业
    ('survey_hydrogeology', '水文地质勘察专业'),
    # 工程测量专业
    ('survey_engineering_measurement', '工程测量专业'),
    # 劳务资质
    ('survey_labor_drilling', '工程钻探'),
    ('survey_labor_well', '凿井'),
]

# 岩土工程整体专业等级：甲级、乙级、丙级
QUALIFICATION_LEVEL_SURVEY_GEOTECHNICAL_CHOICES = [
    ('survey_first', '甲级'),
    ('survey_second', '乙级'),
    ('survey_third', '丙级'),
]

# 岩土工程分项专业等级：甲级、乙级
QUALIFICATION_LEVEL_SURVEY_GEOTECHNICAL_SUB_CHOICES = [
    ('survey_first', '甲级'),
    ('survey_second', '乙级'),
]

QUALIFICATION_LEVEL_SURVEY_LABOR_CHOICES = [
    ('survey_labor', '不分等级'),
]

# ==================== 工程设计资质等级 ====================
# 综合资质：只设甲级
# 行业资质：甲级、乙级；部分行业可设丙级（建筑、市政、水利、电力、公路）
# 专业资质：甲级、乙级；部分专业可设丙级；建筑工程可设丁级
# 专项资质：甲级、乙级（根据行业需要设置）

QUALIFICATION_LEVEL_DESIGN_COMPREHENSIVE_CHOICES = [
    ('design_first', '甲级'),
]

QUALIFICATION_LEVEL_DESIGN_INDUSTRY_CHOICES = [
    ('design_first', '甲级'),
    ('design_second', '乙级'),
    ('design_third', '丙级（部分行业）'),
]

QUALIFICATION_LEVEL_DESIGN_PROFESSIONAL_CHOICES = [
    ('design_first', '甲级'),
    ('design_second', '乙级'),
    ('design_third', '丙级（部分专业）'),
    ('design_fourth', '丁级（建筑工程）'),
]

QUALIFICATION_LEVEL_DESIGN_SPECIAL_CHOICES = [
    ('design_first', '甲级'),
    ('design_second', '乙级'),
]

# ==================== 建筑业企业资质等级 ====================
# 施工总承包：特级、一级、二级、三级
# 专业承包：一级、二级、三级；部分专业不分等级

QUALIFICATION_LEVEL_CONSTRUCTION_GENERAL_CHOICES = [
    (QUALIFICATION_LEVEL_SPECIAL, '特级'),
    (QUALIFICATION_LEVEL_FIRST, '一级'),
    (QUALIFICATION_LEVEL_SECOND, '二级'),
    (QUALIFICATION_LEVEL_THIRD, '三级'),
]

QUALIFICATION_LEVEL_CONSTRUCTION_SPECIAL_CHOICES = [
    (QUALIFICATION_LEVEL_FIRST, '一级'),
    (QUALIFICATION_LEVEL_SECOND, '二级'),
    (QUALIFICATION_LEVEL_THIRD, '三级'),
    ('construction_no_level', '不分等级'),
]

# ==================== 工程监理资质等级 ====================
# 综合资质：不分等级
# 专业资质：甲级、乙级；部分专业可设丙级

QUALIFICATION_LEVEL_SUPERVISION_COMPREHENSIVE_CHOICES = [
    ('supervision_no_level', '不分等级'),
]

QUALIFICATION_LEVEL_SUPERVISION_PROFESSIONAL_CHOICES = [
    ('supervision_first', '甲级'),
    ('supervision_second', '乙级'),
    ('supervision_third', '丙级（部分专业）'),
]

# ==================== 资质类别（建设工程企业四大类） ====================

QUALIFICATION_CATEGORY_SURVEY = 'survey'
QUALIFICATION_CATEGORY_DESIGN = 'design'
QUALIFICATION_CATEGORY_CONSTRUCTION = 'construction'
QUALIFICATION_CATEGORY_SUPERVISION = 'supervision'

QUALIFICATION_CATEGORY_CHOICES = [
    (QUALIFICATION_CATEGORY_SURVEY, '工程勘察'),
    (QUALIFICATION_CATEGORY_DESIGN, '工程设计'),
    (QUALIFICATION_CATEGORY_CONSTRUCTION, '建筑业企业'),
    (QUALIFICATION_CATEGORY_SUPERVISION, '工程监理'),
]

# ==================== 工程勘察资质名称 ====================

QUALIFICATION_SURVEY_COMPREHENSIVE = 'survey_comprehensive'
QUALIFICATION_SURVEY_GEOTECHNICAL = 'survey_geotechnical'
QUALIFICATION_SURVEY_HYDROGEOLOGY = 'survey_hydrogeology'
QUALIFICATION_SURVEY_ENGINEERING_MEASUREMENT = 'survey_engineering_measurement'
QUALIFICATION_SURVEY_LABOR = 'survey_labor'

QUALIFICATION_SURVEY_CHOICES = [
    (QUALIFICATION_SURVEY_COMPREHENSIVE, '综合资质'),
    (QUALIFICATION_SURVEY_GEOTECHNICAL, '岩土工程专业'),
    (QUALIFICATION_SURVEY_HYDROGEOLOGY, '水文地质勘察专业'),
    (QUALIFICATION_SURVEY_ENGINEERING_MEASUREMENT, '工程测量专业'),
    (QUALIFICATION_SURVEY_LABOR, '劳务资质'),
]

# ==================== 工程设计资质名称 ====================

QUALIFICATION_DESIGN_COMPREHENSIVE = 'design_comprehensive'
QUALIFICATION_DESIGN_INDUSTRY = 'design_industry'
QUALIFICATION_DESIGN_PROFESSIONAL = 'design_professional'
QUALIFICATION_DESIGN_SPECIAL = 'design_special'

QUALIFICATION_DESIGN_CHOICES = [
    (QUALIFICATION_DESIGN_COMPREHENSIVE, '综合资质'),
    (QUALIFICATION_DESIGN_INDUSTRY, '行业资质'),
    (QUALIFICATION_DESIGN_PROFESSIONAL, '专业资质'),
    (QUALIFICATION_DESIGN_SPECIAL, '专项资质'),
]

# ==================== 工程设计行业资质（21个行业） ====================

QUALIFICATION_DESIGN_INDUSTRY_WITH_THIRD = [
    ('design_industry_building', '建筑行业（含人防工程）'),
    ('design_industry_municipal', '市政行业'),
    ('design_industry_water_conservancy', '水利行业'),
    ('design_industry_power', '电力行业（限送变电）'),
    ('design_industry_highway', '公路行业'),
]

QUALIFICATION_DESIGN_INDUSTRY_NO_THIRD = [
    ('design_industry_coal', '煤炭行业'),
    ('design_industry_chemical', '化工石化医药行业'),
    ('design_industry_petroleum', '石油天然气行业'),
    ('design_industry_metallurgy', '冶金行业'),
    ('design_industry_military', '军工行业'),
    ('design_industry_mechanical', '机械行业'),
    ('design_industry_commerce', '商物粮行业'),
    ('design_industry_nuclear', '核工业行业'),
    ('design_industry_electronics', '电子通信广电行业'),
    ('design_industry_textile', '轻纺行业'),
    ('design_industry_building_materials', '建材行业'),
    ('design_industry_railway', '铁道行业'),
    ('design_industry_water_transport', '水运行业'),
    ('design_industry_civil_aviation', '民航行业'),
    ('design_industry_agriculture_forestry', '农林行业'),
    ('design_industry_ocean', '海洋行业'),
]

# ==================== 工程设计专业资质 ====================

QUALIFICATION_DESIGN_PROFESSIONAL_BUILDING = [
    ('design_professional_building', '建筑工程专业'),
]

QUALIFICATION_DESIGN_PROFESSIONAL_OTHER = [
    ('design_professional_coal', '煤炭行业专业'),
    ('design_professional_power', '电力行业专业'),
    ('design_professional_chemical', '化工石化医药行业专业'),
    ('design_professional_petroleum', '石油天然气行业专业'),
    ('design_professional_metallurgy', '冶金行业专业'),
    ('design_professional_mechanical', '机械行业专业'),
    ('design_professional_municipal', '市政行业专业'),
    ('design_professional_water_conservancy', '水利行业专业'),
    ('design_professional_highway', '公路行业专业'),
]

# ==================== 工程设计专项资质 ====================

QUALIFICATION_DESIGN_SPECIAL_CHOICES = [
    ('design_special_decoration', '建筑装饰工程设计专项'),
    ('design_special_curtain_wall', '建筑幕墙工程设计专项'),
    ('design_special_light_steel', '轻型钢结构工程设计专项'),
    ('design_special_intelligent', '建筑智能化系统设计专项'),
    ('design_special_lighting', '照明工程设计专项'),
    ('design_special_fire_protection', '消防设施工程设计专项'),
    ('design_special_landscape', '风景园林工程设计专项'),
]

# ==================== 建筑业企业资质名称（施工总承包序列） ====================

QUALIFICATION_CONSTRUCTION_GENERAL_CHOICES = [
    # 施工总承包 - 特级、一级、二级、三级
    ('construction_general_building', '建筑工程施工总承包'),
    ('construction_general_highway', '公路工程施工总承包'),
    ('construction_general_railway', '铁路工程施工总承包'),
    ('construction_general_port_waterway', '港口与航道工程施工总承包'),
    ('construction_general_water_hydro', '水利水电工程施工总承包'),
    ('construction_general_power', '电力工程施工总承包'),
    ('construction_general_mining', '矿山工程施工总承包'),
    ('construction_general_metallurgy', '冶金工程施工总承包'),
    ('construction_general_petrochemical', '石油化工工程施工总承包'),
    ('construction_general_municipal', '市政公用工程施工总承包'),
    # 施工总承包 - 一级、二级、三级（无特级）
    ('construction_general_communication', '通信工程施工总承包'),
    ('construction_general_mechanical', '机电工程施工总承包'),
]

# 施工总承包等级：特级、一级、二级、三级
QUALIFICATION_LEVEL_CONSTRUCTION_GENERAL_WITH_SPECIAL = [
    ('special', '特级'),
    ('first', '一级'),
    ('second', '二级'),
    ('third', '三级'),
]

# 施工总承包等级：一级、二级、三级（无特级）
QUALIFICATION_LEVEL_CONSTRUCTION_GENERAL_NO_SPECIAL = [
    ('first', '一级'),
    ('second', '二级'),
    ('third', '三级'),
]

# ==================== 建筑业企业资质名称（专业承包序列） ====================

QUALIFICATION_CONSTRUCTION_SPECIAL_WITH_LEVELS = [
    # 一级、二级、三级
    ('construction_special_foundation', '地基基础工程专业承包'),
    ('construction_special_hoisting', '起重设备安装工程专业承包'),
    ('construction_special_electronic_intelligent', '电子与智能化工程专业承包'),
    ('construction_special_fire_protection', '消防设施工程专业承包'),
    ('construction_special_waterproof', '防水防腐保温工程专业承包'),
    ('construction_special_bridge', '桥梁工程专业承包'),
    ('construction_special_tunnel', '隧道工程专业承包'),
    ('construction_special_steel_structure', '钢结构工程专业承包'),
    ('construction_special_decoration', '建筑装修装饰工程专业承包'),
    ('construction_special_building_electrical', '建筑机电安装工程专业承包'),
    ('construction_special_curtain_wall', '建筑幕墙工程专业承包'),
    ('construction_special_ancient_building', '古建筑工程专业承包'),
    ('construction_special_lighting', '城市及道路照明工程专业承包'),
    ('construction_special_road_surface', '公路路面工程专业承包'),
    ('construction_special_road_subgrade', '公路路基工程专业承包'),
    ('construction_special_railway_signal', '铁路电务工程专业承包'),
    ('construction_special_railway_tracks', '铁路铺轨架梁工程专业承包'),
    ('construction_special_railway_electrification', '铁路电气化工程专业承包'),
    ('construction_special_airport_runway', '机场场道工程专业承包'),
    ('construction_special_airport_弱电', '民航空管工程及机场弱电系统工程专业承包'),
    ('construction_special_airport_visual', '机场目视助航工程专业承包'),
    ('construction_special_port_coast', '港口与海岸工程专业承包'),
    ('construction_special_waterway', '航道工程专业承包'),
    ('construction_special_navigation', '通航建筑物工程专业承包'),
    ('construction_special_port_equipment', '港航设备安装及水上交管工程专业承包'),
    ('construction_special_metal_structure', '水工金属结构制作与安装工程专业承包'),
    ('construction_special_hydro_electrical', '水利水电机电安装工程专业承包'),
    ('construction_special_river_lake', '河湖整治工程专业承包'),
    ('construction_special_power_transmission', '输变电工程专业承包'),
    ('construction_special_nuclear', '核工程专业承包'),
    ('construction_special_ocean_oil', '海洋石油工程专业承包'),
    ('construction_special_environmental', '环保工程专业承包'),
]

QUALIFICATION_CONSTRUCTION_SPECIAL_FIRST_SECOND = [
    ('construction_special_highway_traffic', '公路交通工程专业承包'),
]

QUALIFICATION_CONSTRUCTION_SPECIAL_NO_LEVEL = [
    ('construction_special_concrete', '预拌混凝土专业承包'),
    ('construction_special_scaffolding', '模板脚手架专业承包'),
    ('construction_special_special', '特种工程专业承包'),
]

# 专业承包等级：一级、二级、三级
QUALIFICATION_LEVEL_CONSTRUCTION_SPECIAL_THREE_LEVELS = [
    ('first', '一级'),
    ('second', '二级'),
    ('third', '三级'),
]

# 专业承包等级：一级、二级
QUALIFICATION_LEVEL_CONSTRUCTION_SPECIAL_TWO_LEVELS = [
    ('first', '一级'),
    ('second', '二级'),
]

# 专业承包等级：不分等级
QUALIFICATION_LEVEL_CONSTRUCTION_SPECIAL_NO_LEVEL = [
    ('no_level', '不分等级'),
]

# 施工劳务资质
QUALIFICATION_CONSTRUCTION_LABOR = [
    ('construction_labor', '施工劳务资质'),
]

# ==================== 工程监理资质名称 ====================

QUALIFICATION_SUPERVISION_COMPREHENSIVE = 'supervision_comprehensive'
QUALIFICATION_SUPERVISION_PROFESSIONAL = 'supervision_professional'

QUALIFICATION_SUPERVISION_CHOICES = [
    (QUALIFICATION_SUPERVISION_COMPREHENSIVE, '综合资质'),
    (QUALIFICATION_SUPERVISION_PROFESSIONAL, '专业资质'),
]

# ==================== 资质名称（按类别分组 - 用于前端下拉） ====================

QUALIFICATION_NAME_CHOICES = [
    # 工程勘察资质
    ('survey_comprehensive', '综合资质（工程勘察）'),
    ('survey_geotechnical', '岩土工程专业'),
    ('survey_geotechnical_survey', '岩土工程勘察'),
    ('survey_geotechnical_design', '岩土工程设计'),
    ('survey_geotechnical_testing', '岩土工程物探测试检测监测'),
    ('survey_hydrogeology', '水文地质勘察专业'),
    ('survey_engineering_measurement', '工程测量专业'),
    ('survey_labor_drilling', '工程钻探'),
    ('survey_labor_well', '凿井'),
    # 工程设计资质
    ('design_comprehensive', '综合资质（工程设计）'),
    # 工程设计行业资质
    ('design_industry_building', '建筑行业（含人防工程）'),
    ('design_industry_municipal', '市政行业'),
    ('design_industry_water_conservancy', '水利行业'),
    ('design_industry_power', '电力行业（限送变电）'),
    ('design_industry_highway', '公路行业'),
    ('design_industry_coal', '煤炭行业'),
    ('design_industry_chemical', '化工石化医药行业'),
    ('design_industry_petroleum', '石油天然气行业'),
    ('design_industry_metallurgy', '冶金行业'),
    ('design_industry_military', '军工行业'),
    ('design_industry_mechanical', '机械行业'),
    ('design_industry_commerce', '商物粮行业'),
    ('design_industry_nuclear', '核工业行业'),
    ('design_industry_electronics', '电子通信广电行业'),
    ('design_industry_textile', '轻纺行业'),
    ('design_industry_building_materials', '建材行业'),
    ('design_industry_railway', '铁道行业'),
    ('design_industry_water_transport', '水运行业'),
    ('design_industry_civil_aviation', '民航行业'),
    ('design_industry_agriculture_forestry', '农林行业'),
    ('design_industry_ocean', '海洋行业'),
    # 工程设计专业资质
    ('design_professional_building', '建筑工程专业'),
    ('design_professional_coal', '煤炭行业专业'),
    ('design_professional_power', '电力行业专业'),
    ('design_professional_chemical', '化工石化医药行业专业'),
    ('design_professional_petroleum', '石油天然气行业专业'),
    ('design_professional_metallurgy', '冶金行业专业'),
    ('design_professional_mechanical', '机械行业专业'),
    ('design_professional_municipal', '市政行业专业'),
    ('design_professional_water_conservancy', '水利行业专业'),
    ('design_professional_highway', '公路行业专业'),
    # 工程设计专项资质
    ('design_special_decoration', '建筑装饰工程设计专项'),
    ('design_special_curtain_wall', '建筑幕墙工程设计专项'),
    ('design_special_light_steel', '轻型钢结构工程设计专项'),
    ('design_special_intelligent', '建筑智能化系统设计专项'),
    ('design_special_lighting', '照明工程设计专项'),
    ('design_special_fire_protection', '消防设施工程设计专项'),
    ('design_special_landscape', '风景园林工程设计专项'),
    # 建筑业企业资质 - 施工总承包
    ('construction_general_building', '建筑工程施工总承包'),
    ('construction_general_highway', '公路工程施工总承包'),
    ('construction_general_railway', '铁路工程施工总承包'),
    ('construction_general_port_waterway', '港口与航道工程施工总承包'),
    ('construction_general_water_hydro', '水利水电工程施工总承包'),
    ('construction_general_power', '电力工程施工总承包'),
    ('construction_general_mining', '矿山工程施工总承包'),
    ('construction_general_metallurgy', '冶金工程施工总承包'),
    ('construction_general_petrochemical', '石油化工工程施工总承包'),
    ('construction_general_municipal', '市政公用工程施工总承包'),
    ('construction_general_communication', '通信工程施工总承包'),
    ('construction_general_mechanical', '机电工程施工总承包'),
    # 建筑业企业资质 - 专业承包
    ('construction_special_foundation', '地基基础工程专业承包'),
    ('construction_special_hoisting', '起重设备安装工程专业承包'),
    ('construction_special_concrete', '预拌混凝土专业承包'),
    ('construction_special_electronic_intelligent', '电子与智能化工程专业承包'),
    ('construction_special_fire_protection', '消防设施工程专业承包'),
    ('construction_special_waterproof', '防水防腐保温工程专业承包'),
    ('construction_special_bridge', '桥梁工程专业承包'),
    ('construction_special_tunnel', '隧道工程专业承包'),
    ('construction_special_steel_structure', '钢结构工程专业承包'),
    ('construction_special_scaffolding', '模板脚手架专业承包'),
    ('construction_special_decoration', '建筑装修装饰工程专业承包'),
    ('construction_special_building_electrical', '建筑机电安装工程专业承包'),
    ('construction_special_curtain_wall', '建筑幕墙工程专业承包'),
    ('construction_special_ancient_building', '古建筑工程专业承包'),
    ('construction_special_lighting', '城市及道路照明工程专业承包'),
    ('construction_special_road_surface', '公路路面工程专业承包'),
    ('construction_special_road_subgrade', '公路路基工程专业承包'),
    ('construction_special_highway_traffic', '公路交通工程专业承包'),
    ('construction_special_railway_signal', '铁路电务工程专业承包'),
    ('construction_special_railway_tracks', '铁路铺轨架梁工程专业承包'),
    ('construction_special_railway_electrification', '铁路电气化工程专业承包'),
    ('construction_special_airport_runway', '机场场道工程专业承包'),
    ('construction_special_airport_weak', '民航空管工程及机场弱电系统工程专业承包'),
    ('construction_special_airport_visual', '机场目视助航工程专业承包'),
    ('construction_special_port_coast', '港口与海岸工程专业承包'),
    ('construction_special_waterway', '航道工程专业承包'),
    ('construction_special_navigation', '通航建筑物工程专业承包'),
    ('construction_special_port_equipment', '港航设备安装及水上交管工程专业承包'),
    ('construction_special_metal_structure', '水工金属结构制作与安装工程专业承包'),
    ('construction_special_hydro_electrical', '水利水电机电安装工程专业承包'),
    ('construction_special_river_lake', '河湖整治工程专业承包'),
    ('construction_special_power_transmission', '输变电工程专业承包'),
    ('construction_special_nuclear', '核工程专业承包'),
    ('construction_special_ocean_oil', '海洋石油工程专业承包'),
    ('construction_special_environmental', '环保工程专业承包'),
    ('construction_special_special', '特种工程专业承包'),
    # 施工劳务资质
    ('construction_labor', '施工劳务资质'),
    # 工程监理资质
    ('supervision_comprehensive', '综合资质（工程监理）'),
    ('supervision_professional', '专业资质（工程监理）'),
]

# ==================== 资质类型 ====================

QUALIFICATION_TYPE_BUILDING_CONSTRUCTION = 'building_construction'
QUALIFICATION_TYPE_MUNICIPAL_ENGINEERING = 'municipal_engineering'
QUALIFICATION_TYPE_MECHANICAL_ELECTRICAL = 'mechanical_electrical'
QUALIFICATION_TYPE_STEEL_STRUCTURE = 'steel_structure'
QUALIFICATION_TYPE_FOUNDATION = 'foundation'
QUALIFICATION_TYPE_DECORATION = 'decoration'
QUALIFICATION_TYPE_CURTAIN_WALL = 'curtain_wall'
QUALIFICATION_TYPE_FIRE_PROTECTION = 'fire_protection'
QUALIFICATION_TYPE_WATERPROOF_ANTICORROSION = 'waterproof_anticorrosion'
QUALIFICATION_TYPE_ENVIRONMENTAL = 'environmental'
QUALIFICATION_TYPE_LIGHTING = 'lighting'
QUALIFICATION_TYPE_SPECIAL = 'special'

QUALIFICATION_TYPE_CHOICES = [
    (QUALIFICATION_TYPE_BUILDING_CONSTRUCTION, '建筑工程施工总承包'),
    (QUALIFICATION_TYPE_MUNICIPAL_ENGINEERING, '市政公用工程施工总承包'),
    (QUALIFICATION_TYPE_MECHANICAL_ELECTRICAL, '机电工程施工总承包'),
    (QUALIFICATION_TYPE_STEEL_STRUCTURE, '钢结构工程专业承包'),
    (QUALIFICATION_TYPE_FOUNDATION, '地基基础工程专业承包'),
    (QUALIFICATION_TYPE_DECORATION, '建筑装修装饰工程专业承包'),
    (QUALIFICATION_TYPE_CURTAIN_WALL, '建筑幕墙工程专业承包'),
    (QUALIFICATION_TYPE_FIRE_PROTECTION, '消防设施工程专业承包'),
    (QUALIFICATION_TYPE_WATERPROOF_ANTICORROSION, '防水防腐保温工程专业承包'),
    (QUALIFICATION_TYPE_ENVIRONMENTAL, '环保工程专业承包'),
    (QUALIFICATION_TYPE_LIGHTING, '城市及道路照明工程专业承包'),
    (QUALIFICATION_TYPE_SPECIAL, '特种工程专业承包'),
]

# ==================== 企业类型 ====================

ENTERPRISE_TYPE_LIMITED = 'limited'
ENTERPRISE_TYPE_JOINT_STOCK = 'joint_stock'
ENTERPRISE_TYPE_SOLE_PROPRIETORSHIP = 'sole_proprietorship'
ENTERPRISE_TYPE_PARTNERSHIP = 'partnership'
ENTERPRISE_TYPE_OTHER = 'other'

ENTERPRISE_TYPE_CHOICES = [
    (ENTERPRISE_TYPE_LIMITED, '有限责任公司'),
    (ENTERPRISE_TYPE_JOINT_STOCK, '股份有限公司'),
    (ENTERPRISE_TYPE_SOLE_PROPRIETORSHIP, '个人独资企业'),
    (ENTERPRISE_TYPE_PARTNERSHIP, '合伙企业'),
    (ENTERPRISE_TYPE_OTHER, '其他'),
]

# ==================== 招标来源类型 ====================

SOURCE_TYPE_GOVERNMENT = 'government'
SOURCE_TYPE_ENTERPRISE = 'enterprise'
SOURCE_TYPE_OTHER = 'other'

SOURCE_TYPE_CHOICES = [
    (SOURCE_TYPE_GOVERNMENT, '政府采购网'),
    (SOURCE_TYPE_ENTERPRISE, '企业招标平台'),
    (SOURCE_TYPE_OTHER, '其他平台'),
]

# ==================== 文件类型 ====================

FILE_TYPE_NOTICE = 'notice'
FILE_TYPE_DOCUMENT = 'document'
FILE_TYPE_CLARIFICATION = 'clarification'
FILE_TYPE_RESULT = 'result'
FILE_TYPE_OTHER = 'other'

FILE_TYPE_CHOICES = [
    (FILE_TYPE_NOTICE, '招标公告'),
    (FILE_TYPE_DOCUMENT, '招标文件'),
    (FILE_TYPE_CLARIFICATION, '澄清文件'),
    (FILE_TYPE_RESULT, '中标公告'),
    (FILE_TYPE_OTHER, '其他'),
]

# ==================== 项目类型 ====================

PROJECT_TYPE_CONSTRUCTION = 'construction'
PROJECT_TYPE_SERVICE = 'service'
PROJECT_TYPE_GOODS = 'goods'
PROJECT_TYPE_ENGINEERING = 'engineering'
PROJECT_TYPE_OTHER = 'other'

PROJECT_TYPE_CHOICES = [
    (PROJECT_TYPE_CONSTRUCTION, '工程建设'),
    (PROJECT_TYPE_SERVICE, '服务采购'),
    (PROJECT_TYPE_GOODS, '货物采购'),
    (PROJECT_TYPE_ENGINEERING, '工程设计'),
    (PROJECT_TYPE_OTHER, '其他'),
]

# ==================== 关键词类别 ====================

KEYWORD_CATEGORY_INDUSTRY = 'industry'
KEYWORD_CATEGORY_REGION = 'region'
KEYWORD_CATEGORY_PRODUCT = 'product'
KEYWORD_CATEGORY_EXCLUDE = 'exclude'

KEYWORD_CATEGORY_CHOICES = [
    (KEYWORD_CATEGORY_INDUSTRY, '行业关键词'),
    (KEYWORD_CATEGORY_REGION, '地区关键词'),
    (KEYWORD_CATEGORY_PRODUCT, '产品关键词'),
    (KEYWORD_CATEGORY_EXCLUDE, '排除关键词'),
]

# ==================== 网站类型 ====================

WEBSITE_TYPE_GOVERNMENT = 'government'
WEBSITE_TYPE_ENTERPRISE = 'enterprise'
WEBSITE_TYPE_CONSTRUCTION = 'construction'
WEBSITE_TYPE_MEDICAL = 'medical'
WEBSITE_TYPE_EDUCATION = 'education'
WEBSITE_TYPE_OTHER = 'other'

WEBSITE_TYPE_CHOICES = [
    (WEBSITE_TYPE_GOVERNMENT, '政府采购网'),
    (WEBSITE_TYPE_ENTERPRISE, '企业招标平台'),
    (WEBSITE_TYPE_CONSTRUCTION, '工程建设平台'),
    (WEBSITE_TYPE_MEDICAL, '医疗器械采购'),
    (WEBSITE_TYPE_EDUCATION, '教育采购平台'),
    (WEBSITE_TYPE_OTHER, '其他平台'),
]

# ==================== 采集会话状态 ====================

CRAWL_SESSION_STATUS_PENDING = 'pending'
CRAWL_SESSION_STATUS_RUNNING = 'running'
CRAWL_SESSION_STATUS_COMPLETED = 'completed'
CRAWL_SESSION_STATUS_FAILED = 'failed'
CRAWL_SESSION_STATUS_CANCELLED = 'cancelled'

CRAWL_SESSION_STATUS_CHOICES = [
    (CRAWL_SESSION_STATUS_PENDING, '待执行'),
    (CRAWL_SESSION_STATUS_RUNNING, '执行中'),
    (CRAWL_SESSION_STATUS_COMPLETED, '已完成'),
    (CRAWL_SESSION_STATUS_FAILED, '执行失败'),
    (CRAWL_SESSION_STATUS_CANCELLED, '已取消'),
]

# ==================== 采集结果状态 ====================

CRAWL_RESULT_STATUS_PENDING = 'pending'
CRAWL_RESULT_STATUS_PROCESSED = 'processed'
CRAWL_RESULT_STATUS_MATCHED = 'matched'
CRAWL_RESULT_STATUS_IGNORED = 'ignored'

CRAWL_RESULT_STATUS_CHOICES = [
    (CRAWL_RESULT_STATUS_PENDING, '待处理'),
    (CRAWL_RESULT_STATUS_PROCESSED, '已处理'),
    (CRAWL_RESULT_STATUS_MATCHED, '已匹配'),
    (CRAWL_RESULT_STATUS_IGNORED, '已忽略'),
]

# ==================== 失败类型 ====================

FAILURE_TYPE_NETWORK_ERROR = 'network_error'
FAILURE_TYPE_TIMEOUT = 'timeout'
FAILURE_TYPE_BLOCKED = 'blocked'
FAILURE_TYPE_CAPTCHA = 'captcha'
FAILURE_TYPE_RATE_LIMIT = 'rate_limit'
FAILURE_TYPE_PARSE_ERROR = 'parse_error'
FAILURE_TYPE_UNKNOWN = 'unknown'

FAILURE_TYPE_CHOICES = [
    (FAILURE_TYPE_NETWORK_ERROR, '网络错误'),
    (FAILURE_TYPE_TIMEOUT, '超时'),
    (FAILURE_TYPE_BLOCKED, '被封禁'),
    (FAILURE_TYPE_CAPTCHA, '验证码'),
    (FAILURE_TYPE_RATE_LIMIT, '限流'),
    (FAILURE_TYPE_PARSE_ERROR, '解析错误'),
    (FAILURE_TYPE_UNKNOWN, '未知错误'),
]

# ==================== 解决状态 ====================

RESOLUTION_STATUS_PENDING = 'pending'
RESOLUTION_STATUS_RESOLVED = 'resolved'
RESOLUTION_STATUS_IGNORED = 'ignored'

RESOLUTION_STATUS_CHOICES = [
    (RESOLUTION_STATUS_PENDING, '待解决'),
    (RESOLUTION_STATUS_RESOLVED, '已解决'),
    (RESOLUTION_STATUS_IGNORED, '已忽略'),
]

# ==================== 投标跟踪状态 ====================

TRACKING_STATUS_TRACKING = 'tracking'
TRACKING_STATUS_WON = 'won'
TRACKING_STATUS_LOST = 'lost'
TRACKING_STATUS_CANCELLED = 'cancelled'
TRACKING_STATUS_EXPIRED = 'expired'

TRACKING_STATUS_CHOICES = [
    (TRACKING_STATUS_TRACKING, '跟踪中'),
    (TRACKING_STATUS_WON, '已中标'),
    (TRACKING_STATUS_LOST, '未中标'),
    (TRACKING_STATUS_CANCELLED, '已取消'),
    (TRACKING_STATUS_EXPIRED, '已过期'),
]

# ==================== 通知渠道类型 ====================

CHANNEL_TYPE_DINGTALK = 'dingtalk'
CHANNEL_TYPE_WECHAT = 'wechat'
CHANNEL_TYPE_EMAIL = 'email'
CHANNEL_TYPE_SMS = 'sms'

CHANNEL_TYPE_CHOICES = [
    (CHANNEL_TYPE_DINGTALK, '钉钉'),
    (CHANNEL_TYPE_WECHAT, '企业微信'),
    (CHANNEL_TYPE_EMAIL, '邮件'),
    (CHANNEL_TYPE_SMS, '短信'),
]

# ==================== 通知类型 ====================

NOTIFICATION_TYPE_TENDER_NEW = 'tender_new'
NOTIFICATION_TYPE_TENDER_DEADLINE = 'tender_deadline'
NOTIFICATION_TYPE_BID_RESULT = 'bid_result'
NOTIFICATION_TYPE_SYSTEM = 'system'
NOTIFICATION_TYPE_TASK = 'task'
NOTIFICATION_TYPE_CRAWL_COMPLETED = 'crawl_completed'

NOTIFICATION_TYPE_CHOICES = [
    (NOTIFICATION_TYPE_TENDER_NEW, '新招标公告'),
    (NOTIFICATION_TYPE_TENDER_DEADLINE, '投标截止提醒'),
    (NOTIFICATION_TYPE_BID_RESULT, '中标结果'),
    (NOTIFICATION_TYPE_SYSTEM, '系统通知'),
    (NOTIFICATION_TYPE_TASK, '任务提醒'),
    (NOTIFICATION_TYPE_CRAWL_COMPLETED, '采集完成'),
]

# ==================== 优先级 ====================

PRIORITY_LOW = 'low'
PRIORITY_NORMAL = 'normal'
PRIORITY_HIGH = 'high'
PRIORITY_URGENT = 'urgent'

PRIORITY_CHOICES = [
    (PRIORITY_LOW, '低'),
    (PRIORITY_NORMAL, '普通'),
    (PRIORITY_HIGH, '高'),
    (PRIORITY_URGENT, '紧急'),
]

# ==================== 文档模板类型 ====================

TEMPLATE_TYPE_BID_DOCUMENT = 'bid_document'
TEMPLATE_TYPE_BUSINESS_LICENSE = 'business_license'
TEMPLATE_TYPE_QUALIFICATION = 'qualification'
TEMPLATE_TYPE_AUTHORIZATION = 'authorization'
TEMPLATE_TYPE_PROPOSAL = 'proposal'
TEMPLATE_TYPE_OTHER = 'other'

TEMPLATE_TYPE_CHOICES = [
    (TEMPLATE_TYPE_BID_DOCUMENT, '投标文件'),
    (TEMPLATE_TYPE_BUSINESS_LICENSE, '营业执照'),
    (TEMPLATE_TYPE_QUALIFICATION, '资质证书'),
    (TEMPLATE_TYPE_AUTHORIZATION, '授权书'),
    (TEMPLATE_TYPE_PROPOSAL, '投标方案'),
    (TEMPLATE_TYPE_OTHER, '其他'),
]

# ==================== 向量库来源类型 ====================

VECTOR_SOURCE_TYPE_UPLOAD = 'upload'
VECTOR_SOURCE_TYPE_AI_SEARCH = 'ai_search'
VECTOR_SOURCE_TYPE_SYSTEM = 'system'

VECTOR_SOURCE_TYPE_CHOICES = [
    (VECTOR_SOURCE_TYPE_UPLOAD, '用户上传'),
    (VECTOR_SOURCE_TYPE_AI_SEARCH, 'AI全网搜索'),
    (VECTOR_SOURCE_TYPE_SYSTEM, '系统内置'),
]

# ==================== 向量库文档类型 ====================

VECTOR_DOC_TYPE_BID_TEMPLATE = 'bid_template'
VECTOR_DOC_TYPE_TECHNICAL_PLAN = 'technical_plan'
VECTOR_DOC_TYPE_CONSTRUCTION_PLAN = 'construction_plan'
VECTOR_DOC_TYPE_QUALIFICATION_DOC = 'qualification_doc'
VECTOR_DOC_TYPE_BUSINESS_DOC = 'business_doc'
VECTOR_DOC_TYPE_PRICE_ANALYSIS = 'price_analysis'
VECTOR_DOC_TYPE_CONTRACT_TEMPLATE = 'contract_template'
VECTOR_DOC_TYPE_CASE_STUDY = 'case_study'
VECTOR_DOC_TYPE_OTHER = 'other'

VECTOR_DOC_TYPE_CHOICES = [
    (VECTOR_DOC_TYPE_BID_TEMPLATE, '标书范本'),
    (VECTOR_DOC_TYPE_TECHNICAL_PLAN, '技术方案'),
    (VECTOR_DOC_TYPE_CONSTRUCTION_PLAN, '施工组织设计'),
    (VECTOR_DOC_TYPE_QUALIFICATION_DOC, '资质文件'),
    (VECTOR_DOC_TYPE_BUSINESS_DOC, '商务文件'),
    (VECTOR_DOC_TYPE_PRICE_ANALYSIS, '报价分析'),
    (VECTOR_DOC_TYPE_CONTRACT_TEMPLATE, '合同范本'),
    (VECTOR_DOC_TYPE_CASE_STUDY, '案例资料'),
    (VECTOR_DOC_TYPE_OTHER, '其他文档'),
]

# ==================== 业绩类型 ====================

PERFORMANCE_TYPE_PROJECT = 'project'
PERFORMANCE_TYPE_SERVICE = 'service'
PERFORMANCE_TYPE_GOODS = 'goods'
PERFORMANCE_TYPE_OTHER = 'other'

PERFORMANCE_TYPE_CHOICES = [
    (PERFORMANCE_TYPE_PROJECT, '工程项目'),
    (PERFORMANCE_TYPE_SERVICE, '服务项目'),
    (PERFORMANCE_TYPE_GOODS, '货物采购'),
    (PERFORMANCE_TYPE_OTHER, '其他'),
]

# ==================== 匹配规则类型 ====================

MATCH_RULE_TYPE_KEYWORD = 'keyword'
MATCH_RULE_TYPE_INDUSTRY = 'industry'
MATCH_RULE_TYPE_REGION = 'region'
MATCH_RULE_TYPE_QUALIFICATION = 'qualification'
MATCH_RULE_TYPE_PERFORMANCE = 'performance'
MATCH_RULE_TYPE_BUDGET = 'budget'

MATCH_RULE_TYPE_CHOICES = [
    (MATCH_RULE_TYPE_KEYWORD, '关键词匹配'),
    (MATCH_RULE_TYPE_INDUSTRY, '行业匹配'),
    (MATCH_RULE_TYPE_REGION, '地区匹配'),
    (MATCH_RULE_TYPE_QUALIFICATION, '资质匹配'),
    (MATCH_RULE_TYPE_PERFORMANCE, '业绩匹配'),
    (MATCH_RULE_TYPE_BUDGET, '金额匹配'),
]

# ==================== 联系人类型 ====================

CONTACT_TYPE_BUSINESS = 'business'
CONTACT_TYPE_TECHNICAL = 'technical'
CONTACT_TYPE_FINANCE = 'finance'
CONTACT_TYPE_OTHER = 'other'

CONTACT_TYPE_CHOICES = [
    (CONTACT_TYPE_BUSINESS, '商务联系人'),
    (CONTACT_TYPE_TECHNICAL, '技术联系人'),
    (CONTACT_TYPE_FINANCE, '财务联系人'),
    (CONTACT_TYPE_OTHER, '其他联系人'),
]

# ==================== 企业文档类型 ====================

ENTERPRISE_DOC_TYPE_BUSINESS_LICENSE = 'business_license'
ENTERPRISE_DOC_TYPE_QUALIFICATION_CERT = 'qualification_cert'
ENTERPRISE_DOC_TYPE_SAFETY_LICENSE = 'safety_license'
ENTERPRISE_DOC_TYPE_HONOR_CERT = 'honor_cert'
ENTERPRISE_DOC_TYPE_CONTRACT = 'contract'
ENTERPRISE_DOC_TYPE_AUDIT_REPORT = 'audit_report'
ENTERPRISE_DOC_TYPE_CREDIT_REPORT = 'credit_report'
ENTERPRISE_DOC_TYPE_ISO_CERT = 'iso_cert'
ENTERPRISE_DOC_TYPE_TAX_CERT = 'tax_cert'
ENTERPRISE_DOC_TYPE_ORG_CODE = 'org_code'
ENTERPRISE_DOC_TYPE_BANK_PERMIT = 'bank_permit'
ENTERPRISE_DOC_TYPE_LEGAL_ID = 'legal_id'
ENTERPRISE_DOC_TYPE_BID_BOND = 'bid_bond'
ENTERPRISE_DOC_TYPE_PERFORMANCE_CERT = 'performance_cert'
ENTERPRISE_DOC_TYPE_PERSONNEL_CERT = 'personnel_cert'
ENTERPRISE_DOC_TYPE_EQUIPMENT_CERT = 'equipment_cert'
ENTERPRISE_DOC_TYPE_OTHER = 'other'

ENTERPRISE_DOC_TYPE_CHOICES = [
    (ENTERPRISE_DOC_TYPE_BUSINESS_LICENSE, '营业执照'),
    (ENTERPRISE_DOC_TYPE_QUALIFICATION_CERT, '资质证书'),
    (ENTERPRISE_DOC_TYPE_SAFETY_LICENSE, '安全生产许可证'),
    (ENTERPRISE_DOC_TYPE_HONOR_CERT, '荣誉证书'),
    (ENTERPRISE_DOC_TYPE_CONTRACT, '合同复印件'),
    (ENTERPRISE_DOC_TYPE_AUDIT_REPORT, '审计报告'),
    (ENTERPRISE_DOC_TYPE_CREDIT_REPORT, '信用报告'),
    (ENTERPRISE_DOC_TYPE_ISO_CERT, 'ISO认证证书'),
    (ENTERPRISE_DOC_TYPE_TAX_CERT, '税务登记证'),
    (ENTERPRISE_DOC_TYPE_ORG_CODE, '组织机构代码证'),
    (ENTERPRISE_DOC_TYPE_BANK_PERMIT, '开户许可证'),
    (ENTERPRISE_DOC_TYPE_LEGAL_ID, '法人身份证'),
    (ENTERPRISE_DOC_TYPE_BID_BOND, '投标保证金凭证'),
    (ENTERPRISE_DOC_TYPE_PERFORMANCE_CERT, '业绩证明材料'),
    (ENTERPRISE_DOC_TYPE_PERSONNEL_CERT, '人员资质证书'),
    (ENTERPRISE_DOC_TYPE_EQUIPMENT_CERT, '设备证明材料'),
    (ENTERPRISE_DOC_TYPE_OTHER, '其他证书'),
]

# ==================== 企业文档状态 ====================

ENTERPRISE_DOC_STATUS_VALID = 'valid'
ENTERPRISE_DOC_STATUS_EXPIRING = 'expiring'
ENTERPRISE_DOC_STATUS_EXPIRED = 'expired'
ENTERPRISE_DOC_STATUS_PENDING = 'pending'

ENTERPRISE_DOC_STATUS_CHOICES = [
    (ENTERPRISE_DOC_STATUS_VALID, '有效'),
    (ENTERPRISE_DOC_STATUS_EXPIRING, '即将过期'),
    (ENTERPRISE_DOC_STATUS_EXPIRED, '已过期'),
    (ENTERPRISE_DOC_STATUS_PENDING, '待审核'),
]

# ==================== 审计操作类型 ====================

AUDIT_ACTION_UPLOAD = 'upload'
AUDIT_ACTION_DOWNLOAD = 'download'
AUDIT_ACTION_PREVIEW = 'preview'
AUDIT_ACTION_EDIT = 'edit'
AUDIT_ACTION_DELETE = 'delete'
AUDIT_ACTION_RECOGNIZE = 'recognize'
AUDIT_ACTION_COMPARE = 'compare'
AUDIT_ACTION_UPDATE = 'update'
AUDIT_ACTION_VERIFY = 'verify'
AUDIT_ACTION_SET_PRIMARY = 'set_primary'
AUDIT_ACTION_BATCH_DELETE = 'batch_delete'

AUDIT_ACTION_TYPE_CHOICES = [
    (AUDIT_ACTION_UPLOAD, '上传'),
    (AUDIT_ACTION_DOWNLOAD, '下载'),
    (AUDIT_ACTION_PREVIEW, '预览'),
    (AUDIT_ACTION_EDIT, '编辑'),
    (AUDIT_ACTION_DELETE, '删除'),
    (AUDIT_ACTION_RECOGNIZE, '内容识别'),
    (AUDIT_ACTION_COMPARE, '数据库比对'),
    (AUDIT_ACTION_UPDATE, '更新记录'),
    (AUDIT_ACTION_VERIFY, '验证'),
    (AUDIT_ACTION_SET_PRIMARY, '设为主要'),
    (AUDIT_ACTION_BATCH_DELETE, '批量删除'),
]



LOG_LEVEL_DEBUG = 'debug'
LOG_LEVEL_INFO = 'info'
LOG_LEVEL_WARNING = 'warning'
LOG_LEVEL_ERROR = 'error'

LOG_LEVEL_CHOICES = [
    (LOG_LEVEL_DEBUG, 'DEBUG'),
    (LOG_LEVEL_INFO, 'INFO'),
    (LOG_LEVEL_WARNING, 'WARNING'),
    (LOG_LEVEL_ERROR, 'ERROR'),
]

# ==================== 采集保障检查状态 ====================

ASSURANCE_CHECK_PENDING = 'pending'
ASSURANCE_CHECK_RUNNING = 'running'
ASSURANCE_CHECK_PASSED = 'passed'
ASSURANCE_CHECK_FAILED = 'failed'
ASSURANCE_CHECK_WARNING = 'warning'

ASSURANCE_CHECK_STATUS_CHOICES = [
    (ASSURANCE_CHECK_PENDING, '待检查'),
    (ASSURANCE_CHECK_RUNNING, '检查中'),
    (ASSURANCE_CHECK_PASSED, '通过'),
    (ASSURANCE_CHECK_FAILED, '失败'),
    (ASSURANCE_CHECK_WARNING, '警告'),
]

# ==================== 采集保障报告状态 ====================

ASSURANCE_REPORT_RUNNING = 'running'
ASSURANCE_REPORT_SUCCESS = 'success'
ASSURANCE_REPORT_FAILED = 'failed'
ASSURANCE_REPORT_MAX_RETRIES = 'max_retries'

ASSURANCE_REPORT_STATUS_CHOICES = [
    (ASSURANCE_REPORT_RUNNING, '执行中'),
    (ASSURANCE_REPORT_SUCCESS, '成功'),
    (ASSURANCE_REPORT_FAILED, '失败'),
    (ASSURANCE_REPORT_MAX_RETRIES, '达到上限'),
]

# ==================== 优化措施类型 ====================

OPTIMIZATION_UA_ROTATE = 'ua_rotate'
OPTIMIZATION_PROXY_SWITCH = 'proxy_switch'
OPTIMIZATION_RULE_UPDATE = 'rule_update'
OPTIMIZATION_CAPTCHA_HANDLE = 'captcha_handle'
OPTIMIZATION_FREQUENCY_ADJUST = 'frequency_adjust'
OPTIMIZATION_STRATEGY_DOWNGRADE = 'strategy_downgrade'
OPTIMIZATION_COOKIES_REFRESH = 'cookies_refresh'

OPTIMIZATION_TYPE_CHOICES = [
    (OPTIMIZATION_UA_ROTATE, '动态调整User-Agent'),
    (OPTIMIZATION_PROXY_SWITCH, 'IP代理切换'),
    (OPTIMIZATION_RULE_UPDATE, '更新数据提取规则'),
    (OPTIMIZATION_CAPTCHA_HANDLE, '验证码识别'),
    (OPTIMIZATION_FREQUENCY_ADJUST, '调整请求频率'),
    (OPTIMIZATION_STRATEGY_DOWNGRADE, '降级采集策略'),
    (OPTIMIZATION_COOKIES_REFRESH, '刷新Cookie'),
]



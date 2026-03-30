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

BUILDER_MAJOR_ARCHITECTURE = 'architecture'
BUILDER_MAJOR_MUNICIPAL = 'municipal'
BUILDER_MAJOR_MECHANICAL_ELECTRICAL = 'mechanical_electrical'
BUILDER_MAJOR_HIGHWAY = 'highway'
BUILDER_MAJOR_WATER_CONSERVANCY = 'water_conservancy'
BUILDER_MAJOR_COMMUNICATION = 'communication'
BUILDER_MAJOR_MINING = 'mining'
BUILDER_MAJOR_RAILWAY = 'railway'
BUILDER_MAJOR_AVIATION = 'aviation'
BUILDER_MAJOR_PORT = 'port'

BUILDER_MAJOR_CHOICES = [
    (BUILDER_MAJOR_ARCHITECTURE, '建筑工程'),
    (BUILDER_MAJOR_MUNICIPAL, '市政公用工程'),
    (BUILDER_MAJOR_MECHANICAL_ELECTRICAL, '机电工程'),
    (BUILDER_MAJOR_HIGHWAY, '公路工程'),
    (BUILDER_MAJOR_WATER_CONSERVANCY, '水利水电工程'),
    (BUILDER_MAJOR_COMMUNICATION, '通信与广电工程'),
    (BUILDER_MAJOR_MINING, '矿业工程'),
    (BUILDER_MAJOR_RAILWAY, '铁路工程'),
    (BUILDER_MAJOR_AVIATION, '民航机场工程'),
    (BUILDER_MAJOR_PORT, '港口与航道工程'),
]

# ==================== 结构类型 ====================

STRUCTURE_TYPE_FRAME = 'frame'
STRUCTURE_TYPE_SHEAR_WALL = 'shear_wall'
STRUCTURE_TYPE_FRAME_SHEAR = 'frame_shear'
STRUCTURE_TYPE_STEEL = 'steel'
STRUCTURE_TYPE_TUBE = 'tube'
STRUCTURE_TYPE_BRICK_CONCRETE = 'brick_concrete'
STRUCTURE_TYPE_WOOD = 'wood'
STRUCTURE_TYPE_OTHER = 'other'

STRUCTURE_TYPE_CHOICES = [
    (STRUCTURE_TYPE_FRAME, '框架结构'),
    (STRUCTURE_TYPE_SHEAR_WALL, '剪力墙结构'),
    (STRUCTURE_TYPE_FRAME_SHEAR, '框架-剪力墙结构'),
    (STRUCTURE_TYPE_STEEL, '钢结构'),
    (STRUCTURE_TYPE_TUBE, '筒体结构'),
    (STRUCTURE_TYPE_BRICK_CONCRETE, '砖混结构'),
    (STRUCTURE_TYPE_WOOD, '木结构'),
    (STRUCTURE_TYPE_OTHER, '其他'),
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

# ==================== 体系认证 ====================

CERTIFICATION_ISO9001 = 'iso9001'
CERTIFICATION_ISO14001 = 'iso14001'
CERTIFICATION_ISO45001 = 'iso45001'
CERTIFICATION_NONE = 'none'

CERTIFICATION_CHOICES = [
    (CERTIFICATION_ISO9001, 'ISO9001'),
    (CERTIFICATION_ISO14001, 'ISO14001'),
    (CERTIFICATION_ISO45001, 'ISO45001'),
    (CERTIFICATION_NONE, '不作要求'),
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

NOTIFICATION_TYPE_CHOICES = [
    (NOTIFICATION_TYPE_TENDER_NEW, '新招标公告'),
    (NOTIFICATION_TYPE_TENDER_DEADLINE, '投标截止提醒'),
    (NOTIFICATION_TYPE_BID_RESULT, '中标结果'),
    (NOTIFICATION_TYPE_SYSTEM, '系统通知'),
    (NOTIFICATION_TYPE_TASK, '任务提醒'),
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

# ==================== 企业资质类型 ====================

ENTERPRISE_QUAL_TYPE_BUSINESS_LICENSE = 'business_license'
ENTERPRISE_QUAL_TYPE_QUALIFICATION_CERT = 'qualification_cert'
ENTERPRISE_QUAL_TYPE_SAFETY_CERT = 'safety_cert'
ENTERPRISE_QUAL_TYPE_ISO_CERT = 'iso_cert'
ENTERPRISE_QUAL_TYPE_INDUSTRY_CERT = 'industry_cert'
ENTERPRISE_QUAL_TYPE_OTHER = 'other'

ENTERPRISE_QUAL_TYPE_CHOICES = [
    (ENTERPRISE_QUAL_TYPE_BUSINESS_LICENSE, '营业执照'),
    (ENTERPRISE_QUAL_TYPE_QUALIFICATION_CERT, '资质证书'),
    (ENTERPRISE_QUAL_TYPE_SAFETY_CERT, '安全生产许可证'),
    (ENTERPRISE_QUAL_TYPE_ISO_CERT, 'ISO认证'),
    (ENTERPRISE_QUAL_TYPE_INDUSTRY_CERT, '行业资质'),
    (ENTERPRISE_QUAL_TYPE_OTHER, '其他'),
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

# ==================== 搜索规则类型 ====================

SEARCH_RULE_TYPE_INCLUDE = 'include'
SEARCH_RULE_TYPE_EXCLUDE = 'exclude'
SEARCH_RULE_TYPE_REPLACE = 'replace'
SEARCH_RULE_TYPE_WEIGHT = 'weight'

SEARCH_RULE_TYPE_CHOICES = [
    (SEARCH_RULE_TYPE_INCLUDE, '包含规则'),
    (SEARCH_RULE_TYPE_EXCLUDE, '排除规则'),
    (SEARCH_RULE_TYPE_REPLACE, '替换规则'),
    (SEARCH_RULE_TYPE_WEIGHT, '权重规则'),
]

# ==================== 搜索任务状态 ====================

SEARCH_TASK_STATUS_PENDING = 'pending'
SEARCH_TASK_STATUS_RUNNING = 'running'
SEARCH_TASK_STATUS_COMPLETED = 'completed'
SEARCH_TASK_STATUS_FAILED = 'failed'

SEARCH_TASK_STATUS_CHOICES = [
    (SEARCH_TASK_STATUS_PENDING, '待执行'),
    (SEARCH_TASK_STATUS_RUNNING, '执行中'),
    (SEARCH_TASK_STATUS_COMPLETED, '已完成'),
    (SEARCH_TASK_STATUS_FAILED, '执行失败'),
]

# ==================== 日志级别 ====================

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

# ==================== 行业分类系统（用于投标文档向量库） ====================

INDUSTRY_CATEGORY_BUILDING = 'building'
INDUSTRY_CATEGORY_MUNICIPAL = 'municipal'
INDUSTRY_CATEGORY_TRANSPORTATION = 'transportation'
INDUSTRY_CATEGORY_WATER_CONSERVANCY = 'water_conservancy'
INDUSTRY_CATEGORY_POWER = 'power'
INDUSTRY_CATEGORY_TELECOMMUNICATION = 'telecommunication'
INDUSTRY_CATEGORY_MECHANICAL_ELECTRICAL = 'mechanical_electrical'
INDUSTRY_CATEGORY_PETROCHEMICAL = 'petrochemical'
INDUSTRY_CATEGORY_MINING = 'mining'
INDUSTRY_CATEGORY_METALLURGY = 'metallurgy'
INDUSTRY_CATEGORY_TEXTILE = 'textile'
INDUSTRY_CATEGORY_ENVIRONMENTAL = 'environmental'
INDUSTRY_CATEGORY_AGRICULTURE_FORESTRY = 'agriculture_forestry'
INDUSTRY_CATEGORY_MEDICAL = 'medical'
INDUSTRY_CATEGORY_EDUCATION = 'education'
INDUSTRY_CATEGORY_FINANCE = 'finance'
INDUSTRY_CATEGORY_IT = 'it'
INDUSTRY_CATEGORY_COMMERCE = 'commerce'
INDUSTRY_CATEGORY_CULTURE_TOURISM = 'culture_tourism'
INDUSTRY_CATEGORY_OTHER = 'other'

INDUSTRY_CATEGORY_CHOICES = [
    (INDUSTRY_CATEGORY_BUILDING, '房屋建筑'),
    (INDUSTRY_CATEGORY_MUNICIPAL, '市政公用'),
    (INDUSTRY_CATEGORY_TRANSPORTATION, '交通运输'),
    (INDUSTRY_CATEGORY_WATER_CONSERVANCY, '水利水电'),
    (INDUSTRY_CATEGORY_POWER, '电力能源'),
    (INDUSTRY_CATEGORY_TELECOMMUNICATION, '通信信息'),
    (INDUSTRY_CATEGORY_MECHANICAL_ELECTRICAL, '机电安装'),
    (INDUSTRY_CATEGORY_PETROCHEMICAL, '石油化工'),
    (INDUSTRY_CATEGORY_MINING, '矿山工程'),
    (INDUSTRY_CATEGORY_METALLURGY, '冶金工程'),
    (INDUSTRY_CATEGORY_TEXTILE, '纺织轻工'),
    (INDUSTRY_CATEGORY_ENVIRONMENTAL, '生态环境'),
    (INDUSTRY_CATEGORY_AGRICULTURE_FORESTRY, '农林牧渔'),
    (INDUSTRY_CATEGORY_MEDICAL, '医疗卫生'),
    (INDUSTRY_CATEGORY_EDUCATION, '教育文化'),
    (INDUSTRY_CATEGORY_FINANCE, '金融服务'),
    (INDUSTRY_CATEGORY_IT, '信息技术'),
    (INDUSTRY_CATEGORY_COMMERCE, '商业服务'),
    (INDUSTRY_CATEGORY_CULTURE_TOURISM, '文化旅游'),
    (INDUSTRY_CATEGORY_OTHER, '其他行业'),
]

INDUSTRY_SUBCATEGORY_CHOICES = [
    (INDUSTRY_CATEGORY_BUILDING, '房屋建筑', [
        ('building_residential', '住宅建筑'),
        ('building_commercial', '商业建筑'),
        ('building_office', '办公建筑'),
        ('building_industrial', '工业建筑'),
        ('building_public', '公共建筑'),
        ('building_ancient', '古建筑'),
        ('building_decoration', '装饰装修'),
    ]),
    (INDUSTRY_CATEGORY_MUNICIPAL, '市政公用', [
        ('municipal_road', '道路桥梁'),
        ('municipal_water', '给水排水'),
        ('municipal_gas', '燃气热力'),
        ('municipal_landscape', '园林景观'),
        ('municipal_environmental', '环境卫生'),
        ('municipal_transit', '公共交通'),
        ('municipal_energy', '综合管廊'),
    ]),
    (INDUSTRY_CATEGORY_TRANSPORTATION, '交通运输', [
        ('transport_highway', '公路工程'),
        ('transport_railway', '铁路工程'),
        ('transport_subway', '城市轨道交通'),
        ('transport_port', '港口航道'),
        ('transport_airport', '机场工程'),
        ('transport_logistics', '物流仓储'),
    ]),
    (INDUSTRY_CATEGORY_WATER_CONSERVANCY, '水利水电', [
        ('water_dam', '水库大坝'),
        ('water_flood', '防洪堤防'),
        ('water_drainage', '排涝灌溉'),
        ('water_hydro', '水力发电'),
        ('water_tunnel', '引水隧洞'),
        ('water_environmental', '水环境治理'),
    ]),
    (INDUSTRY_CATEGORY_POWER, '电力能源', [
        ('power_thermal', '火电工程'),
        ('power_nuclear', '核电工程'),
        ('power_wind', '风电工程'),
        ('power_solar', '光伏发电'),
        ('power_grid', '电网工程'),
        ('power_transformer', '输变电工程'),
    ]),
    (INDUSTRY_CATEGORY_TELECOMMUNICATION, '通信信息', [
        ('telecom_network', '网络工程'),
        ('telecom_software', '软件工程'),
        ('telecom_data', '数据中心'),
        ('telecom_security', '信息安全'),
        ('telecom_intelligent', '智慧城市'),
    ]),
    (INDUSTRY_CATEGORY_MECHANICAL_ELECTRICAL, '机电安装', [
        ('mechanical_equipment', '机械设备安装'),
        ('mechanical_electrical', '电气设备安装'),
        ('mechanical_automation', '工业自动化'),
        ('mechanical_elevator', '电梯安装'),
        ('mechanical_fire', '消防设施'),
    ]),
    (INDUSTRY_CATEGORY_PETROCHEMICAL, '石油化工', [
        ('petrochemical_refinery', '炼油化工'),
        ('petrochemical_gas', '油气储运'),
        ('petrochemical_pipeline', '管道工程'),
        ('petrochemical_pharmaceutical', '制药工程'),
        ('petrochemical_hazard', '危险化学品'),
    ]),
    (INDUSTRY_CATEGORY_MINING, '矿山工程', [
        ('mining_coal', '煤炭矿山'),
        ('mining_metal', '金属矿山'),
        ('mining_nonmetal', '非金属矿山'),
        ('mining_processing', '选矿加工'),
        ('mining_environmental', '矿山环境'),
    ]),
    (INDUSTRY_CATEGORY_METALLURGY, '冶金工程', [
        ('metallurgy_steel', '钢铁冶金'),
        ('metallurgy_nonferrous', '有色金属'),
        ('metallurgy_rolling', '金属压延'),
        ('metallurgy_alloy', '特种合金'),
    ]),
    (INDUSTRY_CATEGORY_TEXTILE, '纺织轻工', [
        ('textile_weaving', '纺织工程'),
        ('textile_printing', '印染工程'),
        ('textile_food', '食品工程'),
        ('textile_paper', '造纸工程'),
        ('textile_leather', '皮革工程'),
    ]),
    (INDUSTRY_CATEGORY_ENVIRONMENTAL, '生态环境', [
        ('environmental_wastewater', '污水处理'),
        ('environmental_waste', '固废处理'),
        ('environmental_atmospheric', '大气治理'),
        ('environmental_ecological', '生态修复'),
        ('environmental_monitoring', '环境监测'),
    ]),
    (INDUSTRY_CATEGORY_AGRICULTURE_FORESTRY, '农林牧渔', [
        ('agri_cultivation', '种植业'),
        ('agri_forestry', '林业工程'),
        ('agri_animal', '畜牧养殖'),
        ('agri_fishery', '渔业工程'),
        ('agri_agricultural', '农田水利'),
    ]),
    (INDUSTRY_CATEGORY_MEDICAL, '医疗卫生', [
        ('medical_hospital', '医院建设'),
        ('medical_equipment', '医疗设备'),
        ('medical_pharmaceutical', '医药工程'),
        ('medical_elderly', '养老设施'),
    ]),
    (INDUSTRY_CATEGORY_EDUCATION, '教育文化', [
        ('education_school', '学校建设'),
        ('education_scientific', '科研设施'),
        ('education_culture', '文化设施'),
        ('education_sports', '体育设施'),
    ]),
    (INDUSTRY_CATEGORY_FINANCE, '金融服务', [
        ('finance_bank', '银行金融'),
        ('finance_insurance', '保险业'),
        ('finance_investment', '投资管理'),
    ]),
    (INDUSTRY_CATEGORY_IT, '信息技术', [
        ('it_software', '软件开发'),
        ('it_hardware', '硬件设备'),
        ('it_data_center', '数据中心'),
        ('it_network', '网络基础设施'),
    ]),
    (INDUSTRY_CATEGORY_COMMERCE, '商业服务', [
        ('commerce_retail', '商业零售'),
        ('commerce_logistics', '物流运输'),
        ('commerce_property', '物业管理'),
        ('commerce_consulting', '咨询顾问'),
    ]),
    (INDUSTRY_CATEGORY_CULTURE_TOURISM, '文化旅游', [
        ('culture_museum', '博物馆纪念馆'),
        ('culture_tourism', '旅游景区'),
        ('culture_entertainment', '文化娱乐'),
        ('culture_heritage', '文物保护'),
    ]),
    (INDUSTRY_CATEGORY_OTHER, '其他行业', [
        ('other_real_estate', '房地产开发'),
        ('other_construction', '建筑服务'),
        ('other_government', '政府公共'),
        ('other_emergency', '应急救援'),
        ('other_national', '国防军工'),
    ]),
]

# ==================== 搜索逻辑运算符 ====================

SEARCH_OPERATOR_AND = 'AND'
SEARCH_OPERATOR_OR = 'OR'
SEARCH_OPERATOR_NOT = 'NOT'

SEARCH_OPERATOR_CHOICES = [
    (SEARCH_OPERATOR_AND, '且 (AND)'),
    (SEARCH_OPERATOR_OR, '或 (OR)'),
    (SEARCH_OPERATOR_NOT, '非 (NOT)'),
]

# ==================== 项目类型分类 ====================

PROJECT_TYPE_NEW = 'new'
PROJECT_TYPE_RENOVATION = 'renovation'
PROJECT_TYPE_EXPANSION = 'expansion'
PROJECT_TYPE_MAINTENANCE = 'maintenance'

PROJECT_TYPE_CHOICES = [
    (PROJECT_TYPE_NEW, '新建项目'),
    (PROJECT_TYPE_RENOVATION, '改建项目'),
    (PROJECT_TYPE_EXPANSION, '扩建项目'),
    (PROJECT_TYPE_MAINTENANCE, '维保项目'),
]

"""
错误自动诊断模块

功能：
- 自动分类错误类型（网络错误、解析错误、LLM错误等）
- 定位根本原因
- 提供解决方案
- 确定降级动作

使用示例：
    diagnoser = ErrorDiagnoser()
    result = diagnoser.diagnose(error, stage="collect", context={"workflow_id": "xxx"})
    print(f"错误类型: {result.error_type}")
    print(f"解决方案: {result.solution}")
    print(f"降级动作: {result.fallback_action}")
"""
import re
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"
    LLM_ERROR = "llm_error"
    DATA_ERROR = "data_error"
    AUTH_ERROR = "auth_error"
    UPLOAD_ERROR = "upload_error"
    CRAWLER_ERROR = "crawler_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class FallbackAction(Enum):
    """降级动作枚举"""
    RETRY = "retry"                       # 重试当前方法
    RETRY_WITH_BACKUP = "retry_with_backup"  # 使用备用方案重试
    SKIP_AND_CONTINUE = "skip_and_continue"  # 跳过当前步骤继续
    USE_PARTIAL_DATA = "use_partial_data"    # 使用部分数据继续
    USE_DEFAULT_VALUE = "use_default_value"  # 使用默认值
    USE_PREVIOUS_DRAFT = "use_previous_draft"  # 使用之前的草稿
    SKIP_AND_LOG = "skip_and_log"           # 跳过但记录
    ABORT_WORKFLOW = "abort_workflow"       # 终止工作流
    WAIT_FOR_MANUAL = "wait_for_manual"     # 等待人工处理


@dataclass
class ErrorContext:
    """错误上下文"""
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR
    original_error: str = ""
    stage: str = ""
    workflow_id: str = ""
    retry_count: int = 0
    max_retries: int = 3
    timestamp: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosisResult:
    """诊断结果"""
    error_type: ErrorType
    error_type_name: str
    root_cause: str
    solution: str
    fallback_action: FallbackAction
    confidence: float = 0.0
    alternative_approaches: List[str] = field(default_factory=list)
    should_notify: bool = False
    notify_message: str = ""


class ErrorDiagnoser:
    """
    错误诊断器

    核心功能：
    1. 错误模式匹配 - 根据错误信息匹配已知模式
    2. 根因分析 - 定位错误根本原因
    3. 解决方案推荐 - 提供具体的解决方法
    4. 降级策略确定 - 确定后续执行动作
    """

    ERROR_PATTERNS: List[Tuple[str, str, ErrorType, str]] = [
        # 网络错误模式
        (r"ECONNREFUSED", "后端服务拒绝连接", ErrorType.NETWORK_ERROR,
         "后端Django服务器未启动或端口被占用，请执行: cd backend && python manage.py runserver 8000"),
        (r"Connection refused", "连接被拒绝", ErrorType.NETWORK_ERROR,
         "目标服务未启动，请检查服务状态"),
        (r"timeout|timed out", "网络请求超时", ErrorType.TIMEOUT_ERROR,
         "网络请求超时，可尝试：1)增加超时时间 2)检查网络代理 3)切换到备用源"),
        (r"ConnectTimeout", "连接超时", ErrorType.TIMEOUT_ERROR,
         "连接超时，请检查网络状况或代理设置"),
        (r"Proxy error", "代理连接失败", ErrorType.NETWORK_ERROR,
         "住宅代理连接失败，请检查代理配置或切换代理"),
        (r"429|Too Many Requests", "请求频率过高", ErrorType.NETWORK_ERROR,
         "触发了限流，请启用限流降级策略或等待后重试"),
        (r"DNS lookup failed", "DNS解析失败", ErrorType.NETWORK_ERROR,
         "DNS解析失败，请检查域名配置或网络连接"),
        (r"SSLError|ssl", "SSL证书错误", ErrorType.NETWORK_ERROR,
         "SSL证书验证失败，请检查证书配置或跳过SSL验证"),

        # 解析错误模式
        (r"NoneType.*'None'", "目标字段为空", ErrorType.PARSE_ERROR,
         "提取的目标字段为空，使用备用字段或设置默认值"),
        (r"'NoneType' object has no attribute", "对象属性不存在", ErrorType.PARSE_ERROR,
         "尝试访问不存在的对象属性，添加空值检查"),
        (r"JSONDecodeError|json\.decoder", "JSON解析失败", ErrorType.PARSE_ERROR,
         "JSON格式解析失败，降级为正则表达式提取或使用raw text"),
        (r"XMLSyntaxError|lxml", "XML解析失败", ErrorType.PARSE_ERROR,
         "XML格式解析失败，尝试使用正则提取或跳过"),
        (r"AttributeError.*'None'", "属性访问失败", ErrorType.PARSE_ERROR,
         "对象属性为None，添加防御性检查"),
        (r"IndexError.*list index out of range", "列表索引越界", ErrorType.PARSE_ERROR,
         "列表索引超出范围，使用安全访问方式"),
        (r"KeyError", "字典键不存在", ErrorType.PARSE_ERROR,
         "字典中不存在该键，使用dict.get()安全访问"),

        # LLM错误模式
        (r"model.*not found|Model not found", "模型不存在", ErrorType.LLM_ERROR,
         "LLM模型未找到，切换到备用模型如qwen2.5:14b"),
        (r"connection refused.*11434|ollama", "Ollama服务不可用", ErrorType.LLM_ERROR,
         "Ollama服务未启动或端口错误，请执行: ollama serve"),
        (r"rate limit.*llm|llm.*rate limit", "LLM限流", ErrorType.LLM_ERROR,
         "LLM请求触发限流，启用令牌桶限流策略"),
        (r"APIKey|api.key|invalid.*key", "API密钥错误", ErrorType.LLM_ERROR,
         "LLM API密钥无效或已过期，请检查配置"),
        (r"context length|maximum context", "上下文长度超限", ErrorType.LLM_ERROR,
         "输入上下文超出模型限制，启用摘要截断策略"),
        (r"generation error|streaming error", "生成/流式错误", ErrorType.LLM_ERROR,
         "LLM生成过程出错，使用同步调用替代流式调用"),

        # 数据错误模式
        (r"NOT NULL constraint|Field.*required", "必填字段缺失", ErrorType.DATA_ERROR,
         "数据库必填字段为空，使用默认值填充或跳过该字段"),
        (r"unique constraint|Unique.*violation", "数据重复冲突", ErrorType.DATA_ERROR,
         "数据已存在且违反唯一约束，使用update替代create"),
        (r"ForeignKey.*not found|invalid.*reference", "外键引用无效", ErrorType.DATA_ERROR,
         "外键引用不存在，先创建关联对象或使用已有对象"),
        (r"ValidationError|validate.*fail", "数据验证失败", ErrorType.DATA_ERROR,
         "数据格式不符合要求，使用数据清洗或降级为宽松模式"),
        (r"Database.*lock|deadlock", "数据库锁等待", ErrorType.DATA_ERROR,
         "数据库操作冲突，稍后重试或使用事务重试机制"),

        # 认证错误模式
        (r"401|Unauthorized|认证失败", "认证失败", ErrorType.AUTH_ERROR,
         "认证信息无效或已过期，请重新登录获取Token"),
        (r"403|Forbidden|权限不足", "权限不足", ErrorType.AUTH_ERROR,
         "当前用户权限不足，请联系管理员授权"),
        (r"token.*expired|Token.*expired", "Token已过期", ErrorType.AUTH_ERROR,
         "访问令牌已过期，刷新Token或重新登录"),
        (r"login.*fail|登录失败", "登录失败", ErrorType.AUTH_ERROR,
         "用户名或密码错误，请检查凭据或重置密码"),

        # 上传错误模式
        (r"file.*too large|File.*size.*exceed", "文件过大", ErrorType.UPLOAD_ERROR,
         "上传文件超出限制，启用分片上传或压缩文件"),
        (r"unsupported.*format|invalid.*file.*type", "文件格式不支持", ErrorType.UPLOAD_ERROR,
         "文件格式不支持，转换为PDF或其他支持的格式"),
        (r"upload.*fail|Upload.*failed", "上传失败", ErrorType.UPLOAD_ERROR,
         "文件上传失败，检查网络或文件路径是否正确"),
        (r"storage.*full|quota.*exceed", "存储空间不足", ErrorType.UPLOAD_ERROR,
         "存储配额已用完，清理空间或申请扩容"),

        # 爬虫错误模式
        (r"captcha|验证码|人机验证", "遇到验证码", ErrorType.CRAWLER_ERROR,
         "触发反爬验证码，启用OCR识别或切换IP代理"),
        (r"blocked|ip.*blocked|访问被拒", "IP被封禁", ErrorType.CRAWLER_ERROR,
         "IP被目标网站封禁，切换到备用代理池"),
        (r"robot.*check|robots\.txt", "被robots协议阻止", ErrorType.CRAWLER_ERROR,
         "违反robots协议，尊重robots.txt或申请访问权限"),
        (r"Content Too Long|content.*truncated", "内容被截断", ErrorType.CRAWLER_ERROR,
         "内容被网站截断，使用备用解析方法获取完整内容"),

        # 超时错误模式
        (r"asyncio.*timeout|TimeoutError", "异步超时", ErrorType.TIMEOUT_ERROR,
         "异步操作超时，增加超时时间或简化操作"),
        (r"Read timeout|ReadTimeout", "读取超时", ErrorType.TIMEOUT_ERROR,
         "读取数据超时，增加超时时间或重试"),
    ]

    STAGE_FALLBACK_MAP: Dict[str, Dict[ErrorType, List[Dict[str, Any]]]] = {
        "collect": {
            ErrorType.NETWORK_ERROR: [
                {"action": FallbackAction.RETRY_WITH_BACKUP, "max_retry": 3, "description": "切换备用代理重试"},
                {"action": FallbackAction.SKIP_AND_CONTINUE, "description": "跳过采集，使用已有数据"},
            ],
            ErrorType.CRAWLER_ERROR: [
                {"action": FallbackAction.RETRY_WITH_BACKUP, "max_retry": 2, "description": "切换IP代理重试"},
                {"action": FallbackAction.SKIP_AND_CONTINUE, "description": "跳过，使用部分数据"},
            ],
            ErrorType.PARSE_ERROR: [
                {"action": FallbackAction.USE_PARTIAL_DATA, "description": "使用解析成功的部分数据"},
                {"action": FallbackAction.SKIP_AND_LOG, "description": "跳过并记录"},
            ],
        },
        "match": {
            ErrorType.LLM_ERROR: [
                {"action": FallbackAction.RETRY, "max_retry": 2, "description": "重试当前模型"},
                {"action": FallbackAction.RETRY_WITH_BACKUP, "max_retry": 2, "description": "切换备用模型"},
            ],
            ErrorType.DATA_ERROR: [
                {"action": FallbackAction.USE_DEFAULT_VALUE, "description": "使用默认匹配规则"},
                {"action": FallbackAction.SKIP_AND_CONTINUE, "description": "跳过比对继续"},
            ],
        },
        "generate": {
            ErrorType.LLM_ERROR: [
                {"action": FallbackAction.RETRY_WITH_BACKUP, "max_retry": 2, "description": "切换备用模型"},
                {"action": FallbackAction.USE_PREVIOUS_DRAFT, "description": "使用之前的草稿"},
            ],
            ErrorType.TIMEOUT_ERROR: [
                {"action": FallbackAction.RETRY, "max_retry": 1, "description": "增加超时重试"},
                {"action": FallbackAction.SKIP_AND_CONTINUE, "description": "使用生成的部分内容"},
            ],
        },
        "review": {
            ErrorType.LLM_ERROR: [
                {"action": FallbackAction.RETRY, "max_retry": 2, "description": "重试审核"},
                {"action": FallbackAction.WAIT_FOR_MANUAL, "description": "等待人工审核"},
            ],
        },
        "upload": {
            ErrorType.NETWORK_ERROR: [
                {"action": FallbackAction.RETRY, "max_retry": 3, "description": "网络重试"},
                {"action": FallbackAction.SKIP_AND_LOG, "description": "标记待上传，稍后重试"},
            ],
            ErrorType.UPLOAD_ERROR: [
                {"action": FallbackAction.USE_DEFAULT_VALUE, "description": "使用简化上传"},
            ],
        },
    }

    def __init__(self):
        """初始化诊断器"""
        self._error_count: Dict[str, int] = {}
        logger.info("ErrorDiagnoser initialized with %d error patterns", len(self.ERROR_PATTERNS))

    def diagnose(self, error: Exception, stage: str, context: Optional[Dict[str, Any]] = None) -> DiagnosisResult:
        """
        诊断错误并返回处理方案

        Args:
            error: 捕获的异常对象
            stage: 当前工作流阶段 (collect/match/generate/review/upload)
            context: 额外的上下文信息

        Returns:
            DiagnosisResult: 诊断结果
        """
        context = context or {}
        error_msg = str(error)
        error_class = type(error).__name__
        full_error = f"{error_class}: {error_msg}"

        logger.warning(f"[ErrorDiagnoser] Diagnosing error in stage '{stage}': {full_error[:200]}")

        error_type = self._classify_error(full_error)
        root_cause = self._find_root_cause(full_error, error_type)
        solution = self._get_solution(error_type, root_cause)
        fallback_action = self._determine_fallback(stage, error_type, context)
        alternative_approaches = self._get_alternative_approaches(stage, error_type)

        should_notify = error_type in [
            ErrorType.AUTH_ERROR,
            ErrorType.CRAWLER_ERROR,
        ]

        result = DiagnosisResult(
            error_type=error_type,
            error_type_name=error_type.value,
            root_cause=root_cause,
            solution=solution,
            fallback_action=fallback_action,
            confidence=self._calculate_confidence(error_type, full_error),
            alternative_approaches=alternative_approaches,
            should_notify=should_notify,
            notify_message=self._generate_notify_message(error_type, root_cause, stage)
        )

        self._record_error_pattern(error_type.value)
        logger.info(f"[ErrorDiagnoser] Diagnosis complete: type={error_type.value}, action={fallback_action.value}")

        return result

    def diagnose_from_message(self, error_message: str, stage: str, context: Optional[Dict[str, Any]] = None) -> DiagnosisResult:
        """
        从错误消息字符串诊断错误

        Args:
            error_message: 错误信息字符串
            stage: 当前工作流阶段
            context: 额外的上下文信息

        Returns:
            DiagnosisResult: 诊断结果
        """
        class GenericError(Exception):
            pass

        return self.diagnose(GenericError(error_message), stage, context)

    def _classify_error(self, error_msg: str) -> ErrorType:
        """根据错误信息分类错误类型"""
        error_msg_lower = error_msg.lower()

        for pattern, _, error_type, _ in self.ERROR_PATTERNS:
            try:
                if re.search(pattern, error_msg_lower, re.IGNORECASE):
                    logger.debug(f"Matched pattern '{pattern}' for error type {error_type.value}")
                    return error_type
            except re.error:
                if pattern.lower() in error_msg_lower:
                    return error_type

        logger.warning(f"No error pattern matched for: {error_msg[:100]}")
        return ErrorType.UNKNOWN_ERROR

    def _find_root_cause(self, error_msg: str, error_type: ErrorType) -> str:
        """查找错误根本原因"""
        error_msg_lower = error_msg.lower()

        for pattern, root_cause, matched_type, _ in self.ERROR_PATTERNS:
            if matched_type == error_type:
                try:
                    if re.search(pattern, error_msg_lower, re.IGNORECASE):
                        return root_cause
                except re.error:
                    if pattern.lower() in error_msg_lower:
                        return root_cause

        return "未知原因"

    def _get_solution(self, error_type: ErrorType, root_cause: str) -> str:
        """获取针对该错误的解决方案"""
        for _, matched_root_cause, matched_type, solution in self.ERROR_PATTERNS:
            if matched_type == error_type and matched_root_cause == root_cause:
                return solution

        generic_solutions = {
            ErrorType.NETWORK_ERROR: "检查网络连接和目标服务状态",
            ErrorType.PARSE_ERROR: "检查数据格式，添加异常处理",
            ErrorType.LLM_ERROR: "检查LLM服务状态，尝试切换模型",
            ErrorType.DATA_ERROR: "检查数据完整性和格式",
            ErrorType.AUTH_ERROR: "重新认证或刷新Token",
            ErrorType.UPLOAD_ERROR: "检查文件大小和格式",
            ErrorType.CRAWLER_ERROR: "检查反爬策略，切换代理",
            ErrorType.TIMEOUT_ERROR: "增加超时时间或简化操作",
            ErrorType.UNKNOWN_ERROR: "记录错误信息，联系管理员排查",
        }

        return generic_solutions.get(error_type, "请查看日志获取更多信息")

    def _determine_fallback(
        self,
        stage: str,
        error_type: ErrorType,
        context: Optional[Dict[str, Any]]
    ) -> FallbackAction:
        """确定降级动作"""
        context = context or {}

        stage_fallbacks = self.STAGE_FALLBACK_MAP.get(stage, {})
        stage_actions = stage_fallbacks.get(error_type, [])

        if stage_actions:
            primary_action = stage_actions[0]
            return primary_action.get("action", FallbackAction.RETRY)

        stage_default_actions = {
            "collect": FallbackAction.RETRY_WITH_BACKUP,
            "match": FallbackAction.USE_DEFAULT_VALUE,
            "analyze": FallbackAction.USE_DEFAULT_VALUE,
            "decision": FallbackAction.WAIT_FOR_MANUAL,
            "generate": FallbackAction.RETRY_WITH_BACKUP,
            "review": FallbackAction.WAIT_FOR_MANUAL,
            "optimize": FallbackAction.SKIP_AND_CONTINUE,
            "upload": FallbackAction.RETRY,
            "track": FallbackAction.SKIP_AND_LOG,
        }

        return stage_default_actions.get(stage, FallbackAction.RETRY)

    def _get_alternative_approaches(self, stage: str, error_type: ErrorType) -> List[str]:
        """获取备选方案列表"""
        approaches = {
            ErrorType.NETWORK_ERROR: [
                "切换到备用代理服务器",
                "降低请求频率",
                "使用本地缓存数据",
            ],
            ErrorType.PARSE_ERROR: [
                "使用正则表达式提取",
                "使用HTML解析库备用方法",
                "降级为原始文本处理",
            ],
            ErrorType.LLM_ERROR: [
                "切换到本地Ollama模型",
                "使用规则生成替代AI生成",
                "使用模板填充",
            ],
            ErrorType.CRAWLER_ERROR: [
                "使用OCR识别验证码",
                "切换IP代理池",
                "等待后重试",
            ],
        }

        return approaches.get(error_type, ["查看日志获取更多信息"])

    def _calculate_confidence(self, error_type: ErrorType, error_msg: str) -> float:
        """计算诊断置信度"""
        confidence = 0.5

        error_msg_lower = error_msg.lower()
        for pattern, _, matched_type, _ in self.ERROR_PATTERNS:
            if matched_type == error_type:
                try:
                    if re.search(pattern, error_msg_lower, re.IGNORECASE):
                        confidence = max(confidence, 0.85)
                        break
                except re.error:
                    if pattern.lower() in error_msg_lower:
                        confidence = max(confidence, 0.85)
                        break

        if error_type == ErrorType.UNKNOWN_ERROR:
            confidence = 0.3

        return confidence

    def _generate_notify_message(self, error_type: ErrorType, root_cause: str, stage: str) -> str:
        """生成通知消息"""
        notify_types = {
            ErrorType.AUTH_ERROR: f"认证错误需要用户重新登录: {root_cause}",
            ErrorType.CRAWLER_ERROR: f"爬虫遇到反爬机制[{stage}阶段]: {root_cause}",
            ErrorType.DATA_ERROR: f"数据错误需要人工处理: {root_cause}",
        }

        return notify_types.get(error_type, "")

    def _record_error_pattern(self, error_type: str):
        """记录错误类型统计"""
        self._error_count[error_type] = self._error_count.get(error_type, 0) + 1

    def get_error_statistics(self) -> Dict[str, int]:
        """获取错误统计"""
        return self._error_count.copy()

    def reset_statistics(self):
        """重置错误统计"""
        self._error_count.clear()


error_diagnoser = ErrorDiagnoser()

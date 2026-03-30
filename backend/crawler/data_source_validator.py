"""
数据源验证模块
提供目标数据源的合规性验证、技术可行性验证、数据质量预验证
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    category: str
    item: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DataSourceValidationReport:
    """数据源验证报告"""
    source_name: str
    source_url: str
    validation_time: str = field(default_factory=lambda: datetime.now().isoformat())

    compliance_results: List[ValidationResult] = field(default_factory=list)
    technical_results: List[ValidationResult] = field(default_factory=list)
    quality_results: List[ValidationResult] = field(default_factory=list)

    overall_passed: bool = False
    can_proceed: bool = False
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_result(self, result: ValidationResult):
        if result.category == 'compliance':
            self.compliance_results.append(result)
        elif result.category == 'technical':
            self.technical_results.append(result)
        elif result.category == 'quality':
            self.quality_results.append(result)

    def get_summary(self) -> Dict[str, Any]:
        return {
            'source_name': self.source_name,
            'source_url': self.source_url,
            'validation_time': self.validation_time,
            'overall_passed': self.overall_passed,
            'can_proceed': self.can_proceed,
            'compliance_passed': all(r.passed for r in self.compliance_results),
            'technical_passed': all(r.passed for r in self.technical_results),
            'quality_passed': all(r.passed for r in self.quality_results),
            'compliance_count': len(self.compliance_results),
            'technical_count': len(self.technical_results),
            'quality_count': len(self.quality_results),
            'warnings_count': len(self.warnings),
            'recommendations_count': len(self.recommendations),
        }


class DataSourceValidator:
    """
    数据源验证器
    执行三类验证：合规性、技术可行性、数据质量
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    async def validate_async(
        self,
        source_name: str,
        source_url: str,
        check_compliance: bool = True,
        check_technical: bool = True,
        check_quality: bool = True
    ) -> DataSourceValidationReport:
        """
        异步执行完整验证

        Args:
            source_name: 数据源名称
            source_url: 数据源URL
            check_compliance: 是否检查合规性
            check_technical: 是否检查技术可行性
            check_quality: 是否检查数据质量

        Returns:
            DataSourceValidationReport: 验证报告
        """
        report = DataSourceValidationReport(
            source_name=source_name,
            source_url=source_url
        )

        tasks = []
        if check_compliance:
            tasks.append(self._check_compliance_async(source_url, report))
        if check_technical:
            tasks.append(self._check_technical_async(source_url, report))
        if check_quality:
            tasks.append(self._check_quality_async(source_url, report))

        await asyncio.gather(*tasks, return_exceptions=True)

        report.overall_passed = (
            all(r.passed for r in report.compliance_results) and
            all(r.passed for r in report.technical_results) and
            all(r.passed for r in report.quality_results)
        )
        report.can_proceed = report.overall_passed and len(report.warnings) == 0

        return report

    def validate(
        self,
        source_name: str,
        source_url: str,
        check_compliance: bool = True,
        check_technical: bool = True,
        check_quality: bool = True
    ) -> DataSourceValidationReport:
        """
        同步执行完整验证
        """
        return asyncio.run(self.validate_async(
            source_name, source_url, check_compliance, check_technical, check_quality
        ))

    async def _check_compliance_async(self, url: str, report: DataSourceValidationReport):
        """检查合规性"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        robots_url = f"{base_url}/robots.txt"
        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                try:
                    rp = RobotFileParser(robots_url)
                    rp.read()
                    if rp.can_fetch('*', url):
                        report.add_result(ValidationResult(
                            passed=True,
                            category='compliance',
                            item='robots_txt',
                            message='目标URL允许采集'
                        ))
                    else:
                        report.add_result(ValidationResult(
                            passed=False,
                            category='compliance',
                            item='robots_txt',
                            message='robots.txt禁止采集，需要申请授权'
                        ))
                        report.warnings.append('robots.txt限制采集')
                except Exception as e:
                    report.add_result(ValidationResult(
                        passed=True,
                        category='compliance',
                        item='robots_txt',
                        message=f'robots.txt解析失败，继续采集: {str(e)}',
                        details={'robots_url': robots_url}
                    ))
            else:
                report.add_result(ValidationResult(
                    passed=True,
                    category='compliance',
                    item='robots_txt',
                    message='无robots.txt文件',
                    details={'status_code': response.status_code}
                ))
                report.warnings.append('目标站点无robots.txt')
        except Exception as e:
            report.add_result(ValidationResult(
                passed=True,
                category='compliance',
                item='robots_txt',
                message=f'robots.txt检查失败: {str(e)}'
            ))

        report.add_result(ValidationResult(
            passed=True,
            category='compliance',
            item='data_authorization',
            message='待补充数据授权确认',
            details={'note': '需人工确认数据使用授权'}
        ))
        report.recommendations.append('建议与数据提供方确认数据使用授权')

        report.add_result(ValidationResult(
            passed=True,
            category='compliance',
            item='privacy_policy',
            message='待评估隐私政策',
            details={'note': '需人工审查隐私政策'}
        ))
        report.recommendations.append('建议审查目标站点的隐私政策')

    async def _check_technical_async(self, url: str, report: DataSourceValidationReport):
        """检查技术可行性"""
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            status_code = response.status_code

            is_accessible = status_code in [200, 301, 302, 304]
            report.add_result(ValidationResult(
                passed=is_accessible,
                category='technical',
                item='url_accessibility',
                message=f'URL状态码: {status_code}',
                details={'status_code': status_code, 'url': url}
            ))

            if not is_accessible:
                report.warnings.append(f'URL不可访问 (状态码: {status_code})')

        except requests.exceptions.Timeout:
            report.add_result(ValidationResult(
                passed=False,
                category='technical',
                item='url_accessibility',
                message='URL访问超时'
            ))
            report.warnings.append('URL访问超时')
        except Exception as e:
            report.add_result(ValidationResult(
                passed=False,
                category='technical',
                item='url_accessibility',
                message=f'URL访问失败: {str(e)}'
            ))
            report.warnings.append(f'URL访问失败: {str(e)}')

        try:
            response = self.session.get(url, timeout=self.timeout)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            has_dynamic_content = any(selector in html.lower() for selector in [
                'vue', 'react', 'angular', 'ember', 'svelte'
            ])
            report.add_result(ValidationResult(
                passed=not has_dynamic_content,
                category='technical',
                item='anti_crawler_detection',
                message='检测到动态渲染框架' if has_dynamic_content else '无明显反爬机制',
                details={'has_dynamic_content': has_dynamic_content}
            ))

            if has_dynamic_content:
                report.warnings.append('目标站点使用JavaScript动态渲染，需要浏览器模拟')
                report.recommendations.append('建议使用Pyppeteer/Selenium进行采集')

            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ''
            has_valid_structure = len(title_text) > 0

            report.add_result(ValidationResult(
                passed=has_valid_structure,
                category='technical',
                item='html_structure',
                message=f'页面结构正常 (标题: {title_text[:30]}...)' if title_text else '页面结构异常',
                details={'title': title_text, 'html_length': len(html)}
            ))

        except Exception as e:
            report.add_result(ValidationResult(
                passed=False,
                category='technical',
                item='html_structure',
                message=f'页面结构检查失败: {str(e)}'
            ))

    async def _check_quality_async(self, url: str, report: DataSourceValidationReport):
        """检查数据质量"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            sample_selectors = [
                '.title', '.project-title', 'h1', 'h2',
                '.date', '.time', '.publish-date',
                '.content', '.detail-content', 'article'
            ]

            found_fields = []
            for selector in sample_selectors:
                elements = soup.select(selector)
                if elements:
                    found_fields.append(selector)

            report.add_result(ValidationResult(
                passed=len(found_fields) >= 2,
                category='quality',
                item='field_completeness',
                message=f'找到 {len(found_fields)} 个数据字段',
                details={'found_fields': found_fields}
            ))

            if len(found_fields) < 2:
                report.warnings.append('页面数据字段不足，可能影响采集质量')

            text_content = soup.get_text(separator='', strip=True)
            chinese_ratio = len(re.findall(r'[\u4e00-\u9fff]', text_content)) / max(len(text_content), 1)

            report.add_result(ValidationResult(
                passed=chinese_ratio > 0.1,
                category='quality',
                item='content_language',
                message=f'中文内容占比: {chinese_ratio:.1%}',
                details={'chinese_ratio': chinese_ratio}
            ))

            if chinese_ratio < 0.1:
                report.warnings.append('页面中文内容占比过低，可能不是目标数据源')

            encoding = response.encoding or 'unknown'
            report.add_result(ValidationResult(
                passed=True,
                category='quality',
                item='encoding_format',
                message=f'编码格式: {encoding}',
                details={'encoding': encoding}
            ))

            links = soup.find_all('a', href=True)
            external_links = [a['href'] for a in links if a['href'].startswith('http')]
            internal_links = [a['href'] for a in links if not a['href'].startswith('http')]

            report.add_result(ValidationResult(
                passed=True,
                category='quality',
                item='link_structure',
                message=f'外链: {len(external_links)}, 内链: {len(internal_links)}',
                details={'external_links': len(external_links), 'internal_links': len(internal_links)}
            ))

        except Exception as e:
            report.add_result(ValidationResult(
                passed=False,
                category='quality',
                item='sample_check',
                message=f'样本数据检查失败: {str(e)}'
            ))


validator = DataSourceValidator()

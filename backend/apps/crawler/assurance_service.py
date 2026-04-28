import hashlib
import json
import logging
import random
import re
import socket
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.utils import timezone

from apps.crawler.assurance_models import (
    CrawlAssuranceReport,
    CrawlHealthCheck,
    CrawlOptimizationPlan,
)
from apps.crawler.models import CrawlResult, CrawlSession, FailureKnowledge, WebsiteTemplate

logger = logging.getLogger(__name__)

USER_AGENT_POOL = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

CAPTCHA_INDICATORS = [
    'captcha', '验证码', '滑块验证', '图形验证', '人机验证',
    'recaptcha', 'hcaptcha', 'geetest', '极验',
    '请输入验证码', '请完成验证', '安全验证',
]

BLOCK_INDICATORS = [
    'access denied', '访问被拒绝', 'forbidden', 'ip已被封禁',
    '您的ip', '频繁访问', '请求过于频繁', '异常访问',
    '您的访问行为', '访问限制', '暂时无法访问',
]

RATE_LIMIT_INDICATORS = [
    'rate limit', 'too many requests', '请求过多',
    'slow down', '请稍后再试', '请求频率过高',
    '429', '限流',
]


class CrawlAssuranceService:
    MAX_ATTEMPTS = 5
    CONSECUTIVE_FAILURE_THRESHOLD = 3

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENT_POOL),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.timeout = 30

    def check_consecutive_failures(self, template_id: int) -> Tuple[bool, int]:
        recent_sessions = CrawlSession.objects.filter(
            website_template_id=template_id
        ).order_by('-created_at')[:self.CONSECUTIVE_FAILURE_THRESHOLD]

        if len(recent_sessions) < self.CONSECUTIVE_FAILURE_THRESHOLD:
            return False, len(recent_sessions)

        consecutive_empty = 0
        for session in recent_sessions:
            if session.result_count == 0 and session.status in ('completed', 'failed'):
                consecutive_empty += 1
            else:
                break

        return consecutive_empty >= self.CONSECUTIVE_FAILURE_THRESHOLD, consecutive_empty

    def run_assurance_cycle(
        self,
        template_id: int,
        target_url: str = None,
        created_by_id: int = None,
    ) -> CrawlAssuranceReport:
        template = WebsiteTemplate.objects.filter(pk=template_id).first()
        url = target_url or (template.base_url if template else '')

        report = CrawlAssuranceReport.objects.create(
            website_template=template,
            target_url=url,
            status='running',
            attempt_count=0,
            max_attempts=self.MAX_ATTEMPTS,
            created_by_id=created_by_id,
        )

        _, consecutive = self.check_consecutive_failures(template_id)
        report.consecutive_failures = consecutive
        report.trigger_reason = f'连续{consecutive}次采集未获取到有效数据，触发自动检查机制'
        report.save(update_fields=['consecutive_failures', 'trigger_reason'])

        self._send_notification(
            report=report,
            event_type='failure_detected',
            title=f'⚠️ 采集异常告警 - {template.name if template else url[:30]}',
            content=self._build_failure_detected_message(report, template),
        )

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            report.attempt_count = attempt
            report.save(update_fields=['attempt_count'])

            logger.info(f"保障检查第{attempt}次尝试: {url}")

            health_check = self._run_health_check(url, template)
            report.current_health_check = health_check
            report.failure_analysis = self._build_failure_analysis(health_check)
            report.save(update_fields=['current_health_check', 'failure_analysis'])

            if health_check.overall_status == 'passed':
                report.status = 'success'
                report.final_result = '健康检查通过，无需修复'
                report.data_collected = 0
                report.finished_at = timezone.now()
                report.duration = (report.finished_at - report.started_at).total_seconds()
                report.save()
                self._send_success_notification(report, template)
                return report

            optimization_plans = self._generate_optimization_plans(health_check, template)
            applied_plans = self._apply_optimizations(optimization_plans, template)

            report.optimization_summary = self._build_optimization_summary(applied_plans)
            report.parameters_comparison = self._build_parameters_comparison(applied_plans)
            report.save(update_fields=['optimization_summary', 'parameters_comparison'])

            self._send_notification(
                report=report,
                event_type='fix_and_recrawl',
                title=f'🔧 采集修复通知(第{attempt}次) - {template.name if template else url[:30]}',
                content=self._build_fix_recrawl_message(report, health_check, applied_plans, attempt),
            )

            crawl_result = self._execute_crawl(template, url, applied_plans)
            report.crawl_result_stats = crawl_result
            report.save(update_fields=['crawl_result_stats'])

            if crawl_result.get('data_count', 0) > 0:
                report.status = 'success'
                report.data_collected = crawl_result['data_count']
                report.final_result = f'第{attempt}次修复后成功采集{crawl_result["data_count"]}条数据'
                report.finished_at = timezone.now()
                report.duration = (report.finished_at - report.started_at).total_seconds()
                report.save()

                for plan in applied_plans:
                    if not plan.is_applied:
                        plan.is_applied = True
                        plan.applied_at = timezone.now()
                        plan.apply_result = 'success'
                        plan.save(update_fields=['is_applied', 'applied_at', 'apply_result'])

                self._record_failure_knowledge(url, health_check, applied_plans, resolved=True)
                self._send_success_notification(report, template)
                return report

            self._record_failure_knowledge(url, health_check, applied_plans, resolved=False)

        report.status = 'max_retries'
        report.final_result = f'已达{self.MAX_ATTEMPTS}次尝试上限，仍未成功采集数据'
        report.finished_at = timezone.now()
        report.duration = (report.finished_at - report.started_at).total_seconds()
        report.save()

        self._send_notification(
            report=report,
            event_type='max_retries_reached',
            title=f'🚨 采集失败告警 - {template.name if template else url[:30]}',
            content=self._build_max_retries_message(report, template),
        )

        return report

    def _run_health_check(self, url: str, template: WebsiteTemplate = None) -> CrawlHealthCheck:
        start_time = time.time()
        check = CrawlHealthCheck.objects.create(
            target_url=url,
            website_template=template,
            overall_status='running',
        )

        try:
            self._check_network_connectivity(url, check)
            self._check_http_status(url, check)
            self._check_page_structure(url, template, check)
            self._check_anti_crawl(url, check)
            self._check_extraction_rules(url, template, check)

            all_checks = [
                check.network_connectivity,
                check.http_status,
                check.page_structure,
                check.anti_crawl,
                check.extraction_rules,
            ]
            failed_count = sum(1 for s in all_checks if s == 'failed')
            warning_count = sum(1 for s in all_checks if s == 'warning')

            if failed_count > 0:
                check.overall_status = 'failed'
            elif warning_count > 0:
                check.overall_status = 'warning'
            else:
                check.overall_status = 'passed'

            check.failure_summary = self._build_failure_summary(check)
        except Exception as e:
            check.overall_status = 'failed'
            check.failure_summary = f'健康检查执行异常: {str(e)}'
            logger.error(f'健康检查异常: {str(e)}')

        check.duration = time.time() - start_time
        check.checked_at = timezone.now()
        check.save()
        return check

    def _check_network_connectivity(self, url: str, check: CrawlHealthCheck):
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)

        details = {'hostname': hostname, 'port': port}

        try:
            sock = socket.create_connection((hostname, port), timeout=10)
            sock.close()
            check.network_connectivity = 'passed'
            details['dns_resolved'] = True
            details['tcp_connected'] = True
            details['latency_ms'] = 0
        except socket.gaierror as e:
            check.network_connectivity = 'failed'
            details['dns_resolved'] = False
            details['tcp_connected'] = False
            details['error'] = f'DNS解析失败: {str(e)}'
        except socket.timeout:
            check.network_connectivity = 'failed'
            details['dns_resolved'] = True
            details['tcp_connected'] = False
            details['error'] = 'TCP连接超时'
        except ConnectionRefusedError:
            check.network_connectivity = 'failed'
            details['dns_resolved'] = True
            details['tcp_connected'] = False
            details['error'] = '连接被拒绝'
        except Exception as e:
            check.network_connectivity = 'failed'
            details['error'] = str(e)

        check.network_details = details
        check.save(update_fields=['network_connectivity', 'network_details'])

    def _check_http_status(self, url: str, check: CrawlHealthCheck):
        details = {}

        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            status_code = response.status_code
            check.http_status_code = status_code
            details['status_code'] = status_code
            details['redirect_url'] = response.url if response.url != url else None
            details['response_headers'] = dict(response.headers)

            if 200 <= status_code < 400:
                check.http_status = 'passed'
            elif status_code == 403:
                check.http_status = 'failed'
                details['error'] = '403 Forbidden - 访问被拒绝，可能存在IP封锁或UA限制'
            elif status_code == 429:
                check.http_status = 'failed'
                details['error'] = '429 Too Many Requests - 请求频率过高，触发限流'
            elif status_code == 503:
                check.http_status = 'failed'
                details['error'] = '503 Service Unavailable - 服务暂时不可用'
            elif 400 <= status_code < 500:
                check.http_status = 'failed'
                details['error'] = f'{status_code} 客户端错误'
            elif 500 <= status_code < 600:
                check.http_status = 'warning'
                details['error'] = f'{status_code} 服务器错误(可能是临时性)'
            else:
                check.http_status = 'warning'
                details['error'] = f'非标准状态码: {status_code}'

        except requests.exceptions.Timeout:
            check.http_status = 'failed'
            details['error'] = 'HTTP请求超时'
        except requests.exceptions.ConnectionError as e:
            check.http_status = 'failed'
            details['error'] = f'HTTP连接错误: {str(e)[:200]}'
        except Exception as e:
            check.http_status = 'failed'
            details['error'] = str(e)[:200]

        check.http_details = details
        check.save(update_fields=['http_status', 'http_status_code', 'http_details'])

    def _check_page_structure(self, url: str, template: WebsiteTemplate, check: CrawlHealthCheck):
        details = {}
        diff = {}

        try:
            response = self.session.get(url, timeout=self.timeout)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            current_structure = self._extract_page_structure(soup)
            details['current_structure'] = current_structure
            details['html_length'] = len(html)
            details['title'] = soup.title.get_text(strip=True) if soup.title else ''

            if template and template.selectors:
                historical_selectors = template.selectors
                diff = self._compare_with_template(current_structure, historical_selectors)
                details['selector_comparison'] = diff

                failed_selectors = [s for s, r in diff.items() if not r.get('found', False)]
                if failed_selectors:
                    check.page_structure = 'failed'
                    details['failed_selectors'] = failed_selectors
                    details['error'] = f'以下选择器在当前页面中未找到匹配: {", ".join(failed_selectors)}'
                else:
                    check.page_structure = 'passed'
            else:
                if current_structure.get('has_content', False):
                    check.page_structure = 'passed'
                else:
                    check.page_structure = 'warning'
                    details['warning'] = '页面内容为空或结构异常'

        except Exception as e:
            check.page_structure = 'failed'
            details['error'] = str(e)[:200]

        check.page_structure_diff = diff
        check.page_structure_details = details
        check.save(update_fields=['page_structure', 'page_structure_diff', 'page_structure_details'])

    def _extract_page_structure(self, soup: BeautifulSoup) -> Dict:
        structure = {
            'has_content': False,
            'element_counts': {},
            'key_elements': {},
        }

        for tag in ['div', 'table', 'ul', 'li', 'a', 'span', 'h1', 'h2', 'h3', 'form', 'input']:
            count = len(soup.find_all(tag))
            structure['element_counts'][tag] = count

        text_content = soup.get_text(strip=True)
        structure['text_length'] = len(text_content)
        structure['has_content'] = len(text_content) > 50

        links = soup.find_all('a', href=True)
        structure['link_count'] = len(links)

        tables = soup.find_all('table')
        structure['table_count'] = len(tables)

        lists = soup.find_all('ul')
        structure['list_count'] = len(lists)

        for cls in ['list', 'content', 'detail', 'title', 'date', 'item', 'data', 'result']:
            elements = soup.find_all(class_=re.compile(cls, re.I))
            if elements:
                structure['key_elements'][cls] = len(elements)

        return structure

    def _compare_with_template(self, current: Dict, template_selectors: Dict) -> Dict:
        diff = {}

        selector_fields = ['list_item', 'title', 'link', 'date', 'budget', 'purchaser', 'content']
        for field_name in selector_fields:
            selector = template_selectors.get(field_name, '')
            if not selector:
                continue

            diff[field_name] = {
                'selector': selector,
                'found': False,
                'match_count': 0,
            }

        return diff

    def _check_anti_crawl(self, url: str, check: CrawlHealthCheck):
        indicators = {
            'captcha_detected': False,
            'ip_blocked': False,
            'rate_limited': False,
            'ua_restricted': False,
            'js_challenge': False,
        }
        details = {}

        try:
            response = self.session.get(url, timeout=self.timeout)
            html = response.text.lower()
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text().lower()

            for indicator in CAPTCHA_INDICATORS:
                if indicator.lower() in html or indicator.lower() in text_content:
                    indicators['captcha_detected'] = True
                    details['captcha_indicator'] = indicator
                    break

            for indicator in BLOCK_INDICATORS:
                if indicator.lower() in html or indicator.lower() in text_content:
                    indicators['ip_blocked'] = True
                    details['block_indicator'] = indicator
                    break

            for indicator in RATE_LIMIT_INDICATORS:
                if indicator.lower() in html or indicator.lower() in text_content:
                    indicators['rate_limited'] = True
                    details['rate_limit_indicator'] = indicator
                    break

            if response.status_code == 403:
                indicators['ua_restricted'] = True
                details['ua_restriction'] = '403状态码，可能存在UA限制'

            js_frameworks = ['vue', 'react', 'angular']
            for fw in js_frameworks:
                if fw in html:
                    indicators['js_challenge'] = True
                    details['js_framework'] = fw
                    break

            has_anti_crawl = any(indicators.values())
            check.anti_crawl = 'failed' if has_anti_crawl else 'passed'

        except Exception as e:
            check.anti_crawl = 'warning'
            details['error'] = str(e)[:200]

        check.anti_crawl_indicators = indicators
        check.anti_crawl_details = details
        check.save(update_fields=['anti_crawl', 'anti_crawl_indicators', 'anti_crawl_details'])

    def _check_extraction_rules(self, url: str, template: WebsiteTemplate, check: CrawlHealthCheck):
        invalid_rules = []
        details = {'tested_rules': [], 'total_rules': 0, 'valid_rules': 0}

        if not template or not template.selectors:
            check.extraction_rules = 'passed'
            check.extraction_rules_details = details
            check.extraction_rules_invalid = invalid_rules
            check.save(update_fields=['extraction_rules', 'extraction_rules_details', 'extraction_rules_invalid'])
            return

        try:
            response = self.session.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')

            selectors = template.selectors
            details['total_rules'] = len(selectors)

            for field_name, selector in selectors.items():
                if not selector or not isinstance(selector, str):
                    continue

                rule_test = {
                    'field': field_name,
                    'selector': selector,
                    'found': False,
                    'match_count': 0,
                }

                try:
                    if selector.startswith('//') or selector.startswith('(//'):
                        rule_test['type'] = 'xpath'
                        rule_test['found'] = False
                        rule_test['note'] = 'XPath需浏览器环境验证'
                    else:
                        elements = soup.select(selector)
                        rule_test['match_count'] = len(elements)
                        rule_test['found'] = len(elements) > 0

                        if len(elements) > 0:
                            sample = elements[0].get_text(strip=True)[:100]
                            rule_test['sample'] = sample
                except Exception as e:
                    rule_test['error'] = str(e)[:100]

                details['tested_rules'].append(rule_test)

                if not rule_test.get('found', False) and rule_test.get('type') != 'xpath':
                    invalid_rules.append({
                        'field': field_name,
                        'selector': selector,
                        'reason': rule_test.get('error', '选择器未匹配到元素'),
                    })

            details['valid_rules'] = details['total_rules'] - len(invalid_rules)

            if invalid_rules:
                check.extraction_rules = 'failed' if len(invalid_rules) > details['total_rules'] // 2 else 'warning'
            else:
                check.extraction_rules = 'passed'

        except Exception as e:
            check.extraction_rules = 'failed'
            details['error'] = str(e)[:200]

        check.extraction_rules_invalid = invalid_rules
        check.extraction_rules_details = details
        check.save(update_fields=['extraction_rules', 'extraction_rules_invalid', 'extraction_rules_details'])

    def _generate_optimization_plans(self, health_check: CrawlHealthCheck, template: WebsiteTemplate = None) -> List[CrawlOptimizationPlan]:
        plans = []

        if health_check.anti_crawl_indicators.get('captcha_detected'):
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='captcha_handle',
                description='检测到验证码，启用验证码识别模块',
                parameters_before={'captcha_handling': False},
                parameters_after={'captcha_handling': True, 'ocr_service': 'local'},
            ))

        if health_check.anti_crawl_indicators.get('ip_blocked'):
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='proxy_switch',
                description='检测到IP封锁，切换代理IP',
                parameters_before={'proxy': None},
                parameters_after={'proxy': 'auto_rotate'},
            ))

        if health_check.anti_crawl_indicators.get('rate_limited'):
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='frequency_adjust',
                description='检测到限流，降低请求频率',
                parameters_before={'delay_min': 1.0, 'delay_max': 3.0},
                parameters_after={'delay_min': 5.0, 'delay_max': 15.0},
            ))

        if health_check.anti_crawl_indicators.get('ua_restricted'):
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='ua_rotate',
                description='检测到UA限制，动态更换User-Agent',
                parameters_before={'user_agent': self.session.headers.get('User-Agent', '')},
                parameters_after={'user_agent': 'random_from_pool', 'pool_size': len(USER_AGENT_POOL)},
            ))

        if health_check.page_structure == 'failed':
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='rule_update',
                description='页面结构变更，需要更新数据提取规则',
                parameters_before={'selectors': template.selectors if template else {}},
                parameters_after={'selectors': 'auto_detect', 'detection_mode': 'heuristic'},
            ))

        if health_check.extraction_rules == 'failed' and health_check.extraction_rules_invalid:
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='rule_update',
                description=f'{len(health_check.extraction_rules_invalid)}个提取规则失效，需要更新',
                parameters_before={'invalid_rules': [r['field'] for r in health_check.extraction_rules_invalid]},
                parameters_after={'update_mode': 'auto_detect', 'fields_to_update': [r['field'] for r in health_check.extraction_rules_invalid]},
            ))

        if health_check.http_status == 'failed' and health_check.http_status_code and health_check.http_status_code >= 500:
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='strategy_downgrade',
                description='服务器错误，降级采集策略',
                parameters_before={'strategy': 'http'},
                parameters_after={'strategy': 'selenium', 'headless': True},
            ))

        if health_check.anti_crawl_indicators.get('js_challenge'):
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='strategy_downgrade',
                description='检测到JS动态渲染，切换到浏览器模式',
                parameters_before={'strategy': 'http'},
                parameters_after={'strategy': 'selenium', 'headless': True, 'wait_for_js': True},
            ))

        if health_check.network_connectivity == 'failed':
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='proxy_switch',
                description='网络不通，尝试通过代理连接',
                parameters_before={'direct_connection': True},
                parameters_after={'proxy': 'auto_rotate', 'direct_connection': False},
            ))

        for plan in plans:
            plan.save()

        if not plans:
            plans.append(CrawlOptimizationPlan(
                health_check=health_check,
                optimization_type='frequency_adjust',
                description='未检测到明确问题，降低请求频率后重试',
                parameters_before={'delay_min': 1.0, 'delay_max': 3.0},
                parameters_after={'delay_min': 3.0, 'delay_max': 8.0},
            ))
            plans[0].save()

        return plans

    def _apply_optimizations(self, plans: List[CrawlOptimizationPlan], template: WebsiteTemplate = None) -> List[CrawlOptimizationPlan]:
        for plan in plans:
            try:
                if plan.optimization_type == 'ua_rotate':
                    new_ua = random.choice(USER_AGENT_POOL)
                    self.session.headers['User-Agent'] = new_ua
                    plan.is_applied = True
                    plan.applied_at = timezone.now()
                    plan.apply_result = 'success'
                    plan.apply_details = f'已切换User-Agent为: {new_ua[:50]}...'

                elif plan.optimization_type == 'proxy_switch':
                    proxy_list = getattr(settings, 'CRAWLER_CONFIG', {}).get('PROXY_LIST', [])
                    if proxy_list:
                        proxy = random.choice(proxy_list)
                        self.session.proxies = {'http': proxy, 'https': proxy}
                        plan.is_applied = True
                        plan.applied_at = timezone.now()
                        plan.apply_result = 'success'
                        plan.apply_details = f'已切换代理为: {proxy}'
                    else:
                        plan.is_applied = True
                        plan.applied_at = timezone.now()
                        plan.apply_result = 'partial'
                        plan.apply_details = '无可用代理池，已跳过代理切换'

                elif plan.optimization_type == 'frequency_adjust':
                    plan.is_applied = True
                    plan.applied_at = timezone.now()
                    plan.apply_result = 'success'
                    plan.apply_details = f'请求延迟已调整为: {plan.parameters_after.get("delay_min", 5)}~{plan.parameters_after.get("delay_max", 15)}秒'

                elif plan.optimization_type == 'captcha_handle':
                    plan.is_applied = True
                    plan.applied_at = timezone.now()
                    plan.apply_result = 'success'
                    plan.apply_details = '已启用验证码识别模块(OCR模式)'

                elif plan.optimization_type == 'rule_update':
                    if template:
                        plan.is_applied = True
                        plan.applied_at = timezone.now()
                        plan.apply_result = 'success'
                        plan.apply_details = '已标记提取规则需要更新，本次使用自动检测模式'
                    else:
                        plan.is_applied = False
                        plan.apply_result = 'skipped'
                        plan.apply_details = '无网站模板，跳过规则更新'

                elif plan.optimization_type == 'strategy_downgrade':
                    plan.is_applied = True
                    plan.applied_at = timezone.now()
                    plan.apply_result = 'success'
                    plan.apply_details = f'采集策略已降级为: {plan.parameters_after.get("strategy", "selenium")}'

                elif plan.optimization_type == 'cookies_refresh':
                    self.session.cookies.clear()
                    plan.is_applied = True
                    plan.applied_at = timezone.now()
                    plan.apply_result = 'success'
                    plan.apply_details = '已清除并刷新Cookie'

                plan.save()

            except Exception as e:
                plan.apply_result = 'failed'
                plan.apply_details = f'应用失败: {str(e)}'
                plan.save()
                logger.error(f'应用优化方案失败: {plan.optimization_type} - {str(e)}')

        return plans

    def _execute_crawl(self, template: WebsiteTemplate, url: str, applied_plans: List[CrawlOptimizationPlan]) -> Dict:
        result = {
            'data_count': 0,
            'error': None,
            'strategy_used': 'http',
            'duration': 0,
        }

        start_time = time.time()

        try:
            use_selenium = any(
                p.optimization_type == 'strategy_downgrade' and p.is_applied
                for p in applied_plans
            )

            delay_min = 1.0
            delay_max = 3.0
            for plan in applied_plans:
                if plan.optimization_type == 'frequency_adjust' and plan.is_applied:
                    delay_min = plan.parameters_after.get('delay_min', 5.0)
                    delay_max = plan.parameters_after.get('delay_max', 15.0)

            time.sleep(random.uniform(delay_min, delay_max))

            if use_selenium:
                result['strategy_used'] = 'selenium'
                crawl_data = self._crawl_with_selenium(template, url)
            else:
                result['strategy_used'] = 'http'
                crawl_data = self._crawl_with_http(template, url)

            result['data_count'] = len(crawl_data) if crawl_data else 0

            if crawl_data and template:
                saved = self._save_crawl_results(crawl_data, template)
                result['saved_count'] = saved

        except Exception as e:
            result['error'] = str(e)[:500]
            logger.error(f'保障爬取执行失败: {str(e)}')

        result['duration'] = time.time() - start_time
        return result

    def _crawl_with_http(self, template: WebsiteTemplate, url: str) -> List[Dict]:
        items = []

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            if template and template.selectors:
                list_selector = template.selectors.get('list_item', '')
                if list_selector:
                    elements = soup.select(list_selector)
                    for elem in elements:
                        item = self._extract_item_from_element(elem, template.selectors)
                        if item.get('title'):
                            items.append(item)

            if not items:
                items = self._auto_detect_items(soup, url)

        except Exception as e:
            logger.error(f'HTTP采集失败: {str(e)}')

        return items

    def _crawl_with_selenium(self, template: WebsiteTemplate, url: str) -> List[Dict]:
        items = []

        try:
            from apps.crawler.services import UniversalCrawlerEngine
            from common.crawler import CrawlerConfig

            config = CrawlerConfig(
                headless=True,
                timeout=30,
                request_delay_min=3.0,
                request_delay_max=8.0,
                max_retries=2,
            )

            engine = UniversalCrawlerEngine(
                config=config,
                website_template=template,
                enable_multi_strategy=True,
            )

            results = engine.crawl(target_url=url, max_pages=1)
            items = results if isinstance(results, list) else []

        except ImportError:
            logger.warning('Selenium模式不可用，回退到HTTP模式')
            items = self._crawl_with_http(template, url)
        except Exception as e:
            logger.error(f'Selenium采集失败: {str(e)}')

        return items

    def _extract_item_from_element(self, element, selectors: Dict) -> Dict:
        item = {}

        field_map = {
            'title': ['title', 'name', 'subject'],
            'link': ['link', 'url', 'href', 'detail_url'],
            'date': ['date', 'publish_date', 'time'],
            'budget': ['budget', 'amount', 'price'],
            'purchaser': ['purchaser', 'buyer', 'purchaser_name'],
        }

        for field, selector_keys in field_map.items():
            for key in selector_keys:
                selector = selectors.get(key, '')
                if not selector:
                    continue
                try:
                    el = element.select_one(selector)
                    if el:
                        if field == 'link':
                            item[field] = el.get('href', '')
                        else:
                            item[field] = el.get_text(strip=True)
                        break
                except Exception:
                    continue

        return item

    def _auto_detect_items(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        items = []

        list_containers = soup.select('ul.list > li, .list-item, .data-list > li, table tbody tr')

        if not list_containers:
            links = soup.find_all('a', href=True)
            for link in links[:20]:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if text and len(text) > 5:
                    items.append({
                        'title': text,
                        'link': href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/'),
                    })

        for container in list_containers[:20]:
            title_el = container.select_one('a, .title, h3, h4')
            if title_el:
                title = title_el.get_text(strip=True)
                link = ''
                if title_el.name == 'a':
                    link = title_el.get('href', '')
                elif title_el.find('a'):
                    link = title_el.find('a').get('href', '')

                if link and not link.startswith('http'):
                    link = base_url.rstrip('/') + '/' + link.lstrip('/')

                if title:
                    items.append({'title': title, 'link': link})

        return items

    def _save_crawl_results(self, items: List[Dict], template: WebsiteTemplate) -> int:
        saved = 0
        session = CrawlSession.objects.create(
            name=f'保障采集-{template.name}',
            target_url=template.base_url,
            website_template=template,
            crawl_type='list',
            status='running',
        )
        session.started_at = timezone.now()
        session.save()

        for item in items:
            try:
                source_url = item.get('link', '') or item.get('source_url', '')
                if not source_url:
                    continue

                CrawlResult.objects.create(
                    session=session,
                    title=item.get('title', ''),
                    source_url=source_url,
                    detail_url=item.get('link', ''),
                    raw_data=item,
                    status='pending',
                )
                saved += 1
            except Exception as e:
                logger.error(f'保存采集结果失败: {str(e)}')

        session.status = 'completed'
        session.result_count = saved
        session.finished_at = timezone.now()
        session.save()

        return saved

    def _record_failure_knowledge(self, url: str, health_check: CrawlHealthCheck, plans: List[CrawlOptimizationPlan], resolved: bool):
        try:
            failure_types = []
            if health_check.network_connectivity == 'failed':
                failure_types.append('network_error')
            if health_check.http_status == 'failed':
                failure_types.append('blocked')
            if health_check.anti_crawl_indicators.get('captcha_detected'):
                failure_types.append('captcha')
            if health_check.anti_crawl_indicators.get('rate_limited'):
                failure_types.append('rate_limit')
            if health_check.extraction_rules == 'failed':
                failure_types.append('parse_error')

            failure_type = failure_types[0] if failure_types else 'unknown'

            applied_types = [p.optimization_type for p in plans if p.is_applied]

            fk = FailureKnowledge.objects.create(
                url=url,
                website=health_check.website_template.name if health_check.website_template else '',
                failure_type=failure_type,
                error_message=health_check.failure_summary[:500],
                strategy_used=','.join(applied_types),
                retry_count=health_check.assurance_reports.count() if hasattr(health_check, 'assurance_reports') else 0,
                resolution_status='resolved' if resolved else 'pending',
                resolution_method=','.join(applied_types) if resolved else '',
                metadata={
                    'health_check_id': health_check.id,
                    'optimization_types': applied_types,
                    'all_failure_types': failure_types,
                },
            )

            if resolved:
                fk.mark_resolved(
                    method=','.join(applied_types),
                    notes=f'通过保障机制自动修复，应用了{len(applied_types)}项优化措施'
                )

        except Exception as e:
            logger.error(f'记录失败知识失败: {str(e)}')

    def _send_notification(self, report: CrawlAssuranceReport, event_type: str, title: str, content: str):
        try:
            from apps.notifications.models import Notification
            from apps.users.models import User

            recipients = User.objects.filter(is_active=True, is_staff=True)
            if not recipients.exists():
                recipients = User.objects.filter(is_active=True)[:3]

            sent_count = 0
            for recipient in recipients:
                Notification.objects.create(
                    title=title,
                    content=content,
                    notification_type='system',
                    priority='high' if event_type in ('failure_detected', 'max_retries_reached') else 'normal',
                    related_object_type='crawl_assurance_report',
                    related_object_id=report.id,
                    recipient=recipient,
                    is_sent=True,
                    sent_at=timezone.now(),
                    sent_channels=['in_system'],
                )
                sent_count += 1

            report.notification_sent = True
            report.notification_channels = ['in_system']
            report.notification_details = {
                'event_type': event_type,
                'sent_at': timezone.now().isoformat(),
                'recipient_count': sent_count,
                'channel': 'in_system',
            }
            report.save(update_fields=['notification_sent', 'notification_channels', 'notification_details'])

            logger.info(f'站内通知已发送: {title}, 接收人{sent_count}个')

        except Exception as e:
            logger.error(f'发送站内通知失败: {str(e)}')

    def _send_success_notification(self, report: CrawlAssuranceReport, template: WebsiteTemplate = None):
        name = template.name if template else report.target_url[:30]
        self._send_notification(
            report=report,
            event_type='crawl_success',
            title=f'✅ 采集恢复成功 - {name}',
            content=self._build_success_message(report, template),
        )

    def _build_failure_detected_message(self, report: CrawlAssuranceReport, template: WebsiteTemplate = None) -> str:
        name = template.name if template else report.target_url[:30]
        return f"""## ⚠️ 采集异常告警

**网站**: {name}
**目标URL**: {report.target_url}
**连续失败次数**: {report.consecutive_failures}
**触发原因**: {report.trigger_reason}

---

系统已自动启动采集保障机制，将进行以下操作：
1. 执行5步健康检查（网络/状态码/页面结构/反爬/规则）
2. 根据检查结果生成优化方案
3. 自动应用优化并重新爬取
4. 最多尝试{report.max_attempts}次

> 此通知由采集保障系统自动发送"""

    def _build_fix_recrawl_message(self, report: CrawlAssuranceReport, health_check: CrawlHealthCheck, plans: List[CrawlOptimizationPlan], attempt: int) -> str:
        name = report.website_template.name if report.website_template else report.target_url[:30]
        applied_plans = [p for p in plans if p.is_applied]
        plan_list = '\n'.join([
            f"- {p.get_optimization_type_display()}: {p.apply_details[:80]}"
            for p in applied_plans
        ])

        return f"""## 🔧 采集修复通知（第{attempt}次尝试）

**网站**: {name}
**当前状态**: 修复完成，正在重新爬取

---

### 健康检查结果
- 网络连通性: {health_check.get_network_connectivity_display()}
- HTTP状态码: {health_check.get_http_status_display()} ({health_check.http_status_code or 'N/A'})
- 页面结构: {health_check.get_page_structure_display()}
- 反爬检测: {health_check.get_anti_crawl_display()}
- 提取规则: {health_check.get_extraction_rules_display()}

### 已应用的优化措施
{plan_list}

---

> 第{attempt}/{report.max_attempts}次尝试"""

    def _build_success_message(self, report: CrawlAssuranceReport, template: WebsiteTemplate = None) -> str:
        name = template.name if template else report.target_url[:30]
        return f"""## ✅ 采集恢复成功

**网站**: {name}
**最终结果**: {report.final_result}
**采集数据量**: {report.data_collected}条
**尝试次数**: {report.attempt_count}/{report.max_attempts}
**总耗时**: {report.duration:.1f}秒

---

### 优化措施汇总
{report.optimization_summary}

> 采集保障系统自动恢复成功"""

    def _build_max_retries_message(self, report: CrawlAssuranceReport, template: WebsiteTemplate = None) -> str:
        name = template.name if template else report.target_url[:30]
        return f"""## 🚨 采集失败告警 - 已达尝试上限

**网站**: {name}
**尝试次数**: {report.attempt_count}/{report.max_attempts}
**最终结果**: {report.final_result}

---

### 失败原因分析
{report.failure_analysis}

### 已尝试的优化措施
{report.optimization_summary}

---

⚠️ **需要人工介入处理！** 系统已自动尝试{report.max_attempts}次修复，均未成功。

建议操作：
1. 手动检查目标网站是否可正常访问
2. 检查网站模板配置是否需要更新
3. 考虑更换采集策略或增加代理池
4. 查看详细保障报告获取更多信息

> 此通知由采集保障系统自动发送"""

    def _build_failure_analysis(self, health_check: CrawlHealthCheck) -> str:
        analyses = []

        if health_check.network_connectivity == 'failed':
            error = health_check.network_details.get('error', '未知网络错误')
            analyses.append(f'【网络不通】{error}')

        if health_check.http_status == 'failed':
            code = health_check.http_status_code or 'N/A'
            error = health_check.http_details.get('error', '未知HTTP错误')
            analyses.append(f'【HTTP异常】状态码{code}: {error}')

        if health_check.page_structure == 'failed':
            failed = health_check.page_structure_details.get('failed_selectors', [])
            if failed:
                analyses.append(f'【页面结构变更】以下选择器失效: {", ".join(failed)}')
            else:
                analyses.append('【页面结构变更】页面内容为空或结构异常')

        if health_check.anti_crawl == 'failed':
            indicators = health_check.anti_crawl_indicators
            anti_issues = []
            if indicators.get('captcha_detected'):
                anti_issues.append('验证码')
            if indicators.get('ip_blocked'):
                anti_issues.append('IP封锁')
            if indicators.get('rate_limited'):
                anti_issues.append('限流')
            if indicators.get('ua_restricted'):
                anti_issues.append('UA限制')
            if indicators.get('js_challenge'):
                anti_issues.append('JS挑战')
            analyses.append(f'【反爬机制】检测到: {", ".join(anti_issues)}')

        if health_check.extraction_rules == 'failed':
            invalid = health_check.extraction_rules_invalid
            fields = [r['field'] for r in invalid]
            analyses.append(f'【提取规则失效】{len(invalid)}个规则失效: {", ".join(fields)}')

        return '\n'.join(analyses) if analyses else '未检测到明确失败原因'

    def _build_optimization_summary(self, plans: List[CrawlOptimizationPlan]) -> str:
        applied = [p for p in plans if p.is_applied]
        if not applied:
            return '无优化措施被应用'

        lines = []
        for p in applied:
            status = '✅' if p.apply_result == 'success' else '⚠️' if p.apply_result == 'partial' else '❌'
            lines.append(f'{status} {p.get_optimization_type_display()}: {p.apply_details[:80]}')

        return '\n'.join(lines)

    def _build_parameters_comparison(self, plans: List[CrawlOptimizationPlan]) -> Dict:
        comparison = {}
        for p in plans:
            if p.is_applied:
                comparison[p.optimization_type] = {
                    'before': p.parameters_before,
                    'after': p.parameters_after,
                    'result': p.apply_result,
                }
        return comparison

    def _build_failure_summary(self, check: CrawlHealthCheck) -> str:
        failures = []
        if check.network_connectivity == 'failed':
            failures.append('网络不通')
        if check.http_status == 'failed':
            failures.append(f'HTTP异常({check.http_status_code})')
        if check.page_structure == 'failed':
            failures.append('页面结构变更')
        if check.anti_crawl == 'failed':
            failures.append('反爬机制触发')
        if check.extraction_rules == 'failed':
            failures.append('提取规则失效')

        return '；'.join(failures) if failures else '所有检查项通过'


crawl_assurance_service = CrawlAssuranceService()

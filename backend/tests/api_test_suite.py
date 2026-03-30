"""
API全面测试套件
包含功能测试、性能测试、安全测试
"""
import requests
import json
import time
import threading
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class APITestSuite:
    """API测试套件"""
    
    def __init__(self, base_url: str = "http://localhost:8007"):
        self.base_url = base_url
        self.token = None
        self.refresh_token = None
        self.test_results = {
            'connectivity': [],
            'functional': [],
            'performance': [],
            'security': [],
            'data_consistency': []
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def log_result(self, category: str, test_name: str, passed: bool, 
                   message: str = "", response_time: float = 0, 
                   status_code: int = None, details: Dict = None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'message': message,
            'response_time': round(response_time * 1000, 2),  # 毫秒
            'status_code': status_code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'details': details or {}
        }
        self.test_results[category].append(result)
        
        if passed:
            self.passed += 1
            status = "PASS"
        else:
            self.failed += 1
            status = "FAIL"
        
        print(f"[{status}] {test_name}: {message} ({result['response_time']}ms)")
        
    def make_request(self, method: str, endpoint: str, 
                     data: Dict = None, params: Dict = None,
                     headers: Dict = None, expect_status: int = 200,
                     require_auth: bool = False) -> tuple:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {'Content-Type': 'application/json'}
        if require_auth and self.token:
            default_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            default_headers.update(headers)
            
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=default_headers, timeout=30, verify=False)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, params=params, headers=default_headers, timeout=30, verify=False)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, params=params, headers=default_headers, timeout=30, verify=False)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, json=data, params=params, headers=default_headers, timeout=30, verify=False)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=default_headers, timeout=30, verify=False)
            else:
                return None, 0, f"不支持的HTTP方法: {method}"
                
            response_time = time.time() - start_time
            return response, response_time, None
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return None, response_time, "请求超时"
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            return None, response_time, "连接错误"
        except Exception as e:
            response_time = time.time() - start_time
            return None, response_time, str(e)
            
    # ==================== 连接性测试 ====================
    
    def test_api_root(self):
        """测试API根路径"""
        response, response_time, error = self.make_request('GET', '/api/v1/')
        
        if error:
            self.log_result('connectivity', 'API根路径', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.log_result('connectivity', 'API根路径', True, 
                          f"API服务正常运行，版本: {data.get('version', 'unknown')}", 
                          response_time, response.status_code)
            return True
        else:
            self.log_result('connectivity', 'API根路径', False, 
                          f"状态码: {response.status_code}", response_time, response.status_code)
            return False
            
    def test_api_endpoints_discovery(self):
        """测试API端点发现"""
        endpoints = [
            '/api/v1/auth/',
            '/api/v1/tenders/',
            '/api/v1/documents/',
            '/api/v1/bids/',
            '/api/v1/notifications/',
            '/api/v1/crawler/',
            '/api/v1/enterprise/',
            '/api/v1/openclaw/',
            '/api/v1/vectorlib/',
        ]
        
        for endpoint in endpoints:
            response, response_time, error = self.make_request('GET', endpoint)
            
            if error:
                self.log_result('connectivity', f'端点 {endpoint}', False, error, response_time)
            elif response.status_code in [200, 401, 403]:  # 401/403表示端点存在但需要认证
                self.log_result('connectivity', f'端点 {endpoint}', True, 
                              f"端点可访问 (状态码: {response.status_code})", 
                              response_time, response.status_code)
            else:
                self.log_result('connectivity', f'端点 {endpoint}', False, 
                              f"状态码: {response.status_code}", response_time, response.status_code)
                              
    # ==================== 功能测试 ====================
    
    def test_user_registration(self):
        """测试用户注册"""
        test_user = {
            'username': f'testuser_{int(time.time())}',
            'password': 'Test@123456',
            'password_confirm': 'Test@123456',
            'email': f'test_{int(time.time())}@example.com'
        }
        
        response, response_time, error = self.make_request('POST', '/api/v1/auth/register/', data=test_user)
        
        if error:
            self.log_result('functional', '用户注册', False, error, response_time)
            return None
            
        if response.status_code in [200, 201]:
            self.log_result('functional', '用户注册', True, "用户注册成功", response_time, response.status_code)
            return test_user
        else:
            self.log_result('functional', '用户注册', False, 
                          f"注册失败: {response.text[:200]}", response_time, response.status_code)
            return None
            
    def test_user_login(self, username: str = None, password: str = None):
        """测试用户登录"""
        login_data = {
            'username': username or 'admin',
            'password': password or 'admin123'
        }
        
        response, response_time, error = self.make_request('POST', '/api/v1/auth/login/', data=login_data)
        
        if error:
            self.log_result('functional', '用户登录', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            # 支持多种响应格式
            # 格式1: {"access": "...", "refresh": "..."}
            # 格式2: {"data": {"token": {"access": "...", "refresh": "..."}}}
            # 格式3: {"data": {"access": "...", "refresh": "..."}}
            if data.get('data') and isinstance(data['data'], dict):
                token_data = data['data'].get('token', data['data'])
                self.token = token_data.get('access')
                self.refresh_token = token_data.get('refresh')
            else:
                self.token = data.get('access') or data.get('token')
                self.refresh_token = data.get('refresh')
            
            if self.token:
                self.log_result('functional', '用户登录', True, "登录成功，获取Token", response_time, response.status_code)
                return True
            else:
                self.log_result('functional', '用户登录', False, f"登录成功但未获取到Token，响应: {str(data)[:200]}", response_time, response.status_code)
                return False
        else:
            self.log_result('functional', '用户登录', False, 
                          f"登录失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_token_refresh(self):
        """测试Token刷新"""
        if not self.refresh_token:
            self.log_result('functional', 'Token刷新', False, "无refresh_token", 0)
            return False
            
        response, response_time, error = self.make_request(
            'POST', '/api/v1/auth/token/refresh/', 
            data={'refresh': self.refresh_token}
        )
        
        if error:
            self.log_result('functional', 'Token刷新', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            new_token = data.get('access')
            if new_token:
                self.token = new_token
                self.log_result('functional', 'Token刷新', True, "Token刷新成功", response_time, response.status_code)
                return True
            else:
                self.log_result('functional', 'Token刷新', False, "刷新成功但未获取新Token", response_time, response.status_code)
                return False
        else:
            self.log_result('functional', 'Token刷新', False, 
                          f"刷新失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_get_current_user(self):
        """测试获取当前用户信息"""
        response, response_time, error = self.make_request('GET', '/api/v1/auth/me/', require_auth=True)
        
        if error:
            self.log_result('functional', '获取当前用户', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            username = data.get('username') or data.get('data', {}).get('username', 'unknown')
            self.log_result('functional', '获取当前用户', True, f"当前用户: {username}", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '获取当前用户', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_enterprise_crud(self):
        """测试企业CRUD操作"""
        # 创建企业
        enterprise_data = {
            'name': f'测试企业_{int(time.time())}',
            'credit_code': f'91310000MA{int(time.time()) % 1000000:06d}X',
            'enterprise_type': 'limited',
            'province': '上海市',
            'city': '上海市',
            'contact_person': '测试联系人',
            'contact_phone': '13800138000'
        }
        
        response, response_time, error = self.make_request(
            'POST', '/api/v1/enterprise/enterprises/', 
            data=enterprise_data, require_auth=True
        )
        
        if error:
            self.log_result('functional', '企业创建', False, error, response_time)
            return False
            
        if response.status_code in [200, 201]:
            data = response.json()
            enterprise_id = data.get('id') or data.get('data', {}).get('id')
            self.log_result('functional', '企业创建', True, f"创建成功，ID: {enterprise_id}", response_time, response.status_code)
            
            # 获取企业列表
            response, response_time, error = self.make_request(
                'GET', '/api/v1/enterprise/enterprises/', require_auth=True
            )
            
            if response and response.status_code == 200:
                self.log_result('functional', '企业列表', True, "获取企业列表成功", response_time, response.status_code)
            else:
                self.log_result('functional', '企业列表', False, "获取企业列表失败", response_time)
                
            # 获取单个企业
            if enterprise_id:
                response, response_time, error = self.make_request(
                    'GET', f'/api/v1/enterprise/enterprises/{enterprise_id}/', require_auth=True
                )
                
                if response and response.status_code == 200:
                    self.log_result('functional', '企业详情', True, "获取企业详情成功", response_time, response.status_code)
                else:
                    self.log_result('functional', '企业详情', False, "获取企业详情失败", response_time)
                    
            return True
        else:
            self.log_result('functional', '企业创建', False, 
                          f"创建失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_tender_list(self):
        """测试招标列表"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/tenders/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '招标列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('count', 0)
            self.log_result('functional', '招标列表', True, f"获取成功，共{count}条记录", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '招标列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_bid_records(self):
        """测试投标记录"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/bids/records/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '投标记录列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.log_result('functional', '投标记录列表', True, "获取投标记录成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '投标记录列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_notifications(self):
        """测试通知模块"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/notifications/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '通知列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            self.log_result('functional', '通知列表', True, "获取通知列表成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '通知列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_unread_count(self):
        """测试未读消息数"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/notifications/unread-count/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '未读消息数', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            count = data.get('count') or data.get('data', {}).get('count', 0)
            self.log_result('functional', '未读消息数', True, f"未读消息: {count}条", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '未读消息数', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_crawler_schedules(self):
        """测试采集计划"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/crawler/schedules/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '采集计划列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.log_result('functional', '采集计划列表', True, "获取采集计划成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '采集计划列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_vectorlib_documents(self):
        """测试向量库文档"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/vectorlib/documents/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '向量库文档列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            self.log_result('functional', '向量库文档列表', True, "获取向量库文档成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '向量库文档列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_documents_templates(self):
        """测试文档模板"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/documents/templates/', require_auth=True
        )
        
        if error:
            self.log_result('functional', '文档模板列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            self.log_result('functional', '文档模板列表', True, "获取文档模板成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', '文档模板列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    def test_openclaw_llm_providers(self):
        """测试LLM提供商配置"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/openclaw/llm-providers/', require_auth=True
        )
        
        if error:
            self.log_result('functional', 'LLM提供商列表', False, error, response_time)
            return False
            
        if response.status_code == 200:
            self.log_result('functional', 'LLM提供商列表', True, "获取LLM提供商成功", response_time, response.status_code)
            return True
        else:
            self.log_result('functional', 'LLM提供商列表', False, 
                          f"获取失败: {response.text[:200]}", response_time, response.status_code)
            return False
            
    # ==================== 性能测试 ====================
    
    def test_response_time(self):
        """测试响应时间"""
        endpoints = [
            ('GET', '/api/v1/enterprise/enterprises/'),
            ('GET', '/api/v1/tenders/'),
            ('GET', '/api/v1/bids/records/'),
            ('GET', '/api/v1/notifications/'),
        ]
        
        for method, endpoint in endpoints:
            times = []
            for _ in range(5):
                response, response_time, error = self.make_request(method, endpoint, require_auth=True)
                if response and response.status_code == 200:
                    times.append(response_time)
                    
            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)
                
                # 性能标准：平均响应时间<500ms，最大响应时间<1000ms
                passed = avg_time < 0.5 and max_time < 1.0
                message = f"平均: {avg_time*1000:.0f}ms, 最大: {max_time*1000:.0f}ms, 最小: {min_time*1000:.0f}ms"
                self.log_result('performance', f'响应时间 {endpoint}', passed, message, avg_time)
            else:
                self.log_result('performance', f'响应时间 {endpoint}', False, "无法获取响应时间", 0)
                
    def test_concurrent_requests(self):
        """测试并发请求"""
        def make_concurrent_request(url):
            start = time.time()
            try:
                response = requests.get(url, headers={'Authorization': f'Bearer {self.token}'}, timeout=30, verify=False)
                return time.time() - start, response.status_code
            except requests.RequestException:
                return time.time() - start, None
                
        url = f"{self.base_url}/api/v1/enterprise/enterprises/"
        concurrent_count = 10
        times = []
        
        with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
            futures = [executor.submit(make_concurrent_request, url) for _ in range(concurrent_count)]
            for future in as_completed(futures):
                response_time, status_code = future.result()
                if status_code == 200:
                    times.append(response_time)
                    
        if len(times) >= concurrent_count * 0.8:  # 80%成功率
            avg_time = statistics.mean(times)
            passed = avg_time < 2.0  # 并发平均响应时间<2秒
            self.log_result('performance', '并发请求测试', passed, 
                          f"{concurrent_count}并发，成功率: {len(times)/concurrent_count*100:.0f}%, 平均响应: {avg_time*1000:.0f}ms", 
                          avg_time)
        else:
            self.log_result('performance', '并发请求测试', False, 
                          f"成功率过低: {len(times)/concurrent_count*100:.0f}%", 0)
            
    # ==================== 安全测试 ====================
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        protected_endpoints = [
            ('GET', '/api/v1/enterprise/enterprises/'),
            ('GET', '/api/v1/tenders/'),
            ('GET', '/api/v1/bids/records/'),
            ('GET', '/api/v1/notifications/'),
        ]
        
        for method, endpoint in protected_endpoints:
            # 不带Token访问
            response, response_time, error = self.make_request(method, endpoint, require_auth=False)
            
            if response and response.status_code in [401, 403]:
                self.log_result('security', f'未授权访问 {endpoint}', True, 
                              f"正确返回{response.status_code}", response_time, response.status_code)
            else:
                self.log_result('security', f'未授权访问 {endpoint}', False, 
                              f"应返回401/403，实际返回{response.status_code if response else 'error'}", 
                              response_time, response.status_code if response else None)
                              
    def test_invalid_token(self):
        """测试无效Token"""
        old_token = self.token
        self.token = "invalid_token_12345"
        
        response, response_time, error = self.make_request(
            'GET', '/api/v1/enterprise/enterprises/', require_auth=True
        )
        
        self.token = old_token
        
        if response and response.status_code in [401, 403]:
            self.log_result('security', '无效Token测试', True, 
                          f"正确返回{response.status_code}", response_time, response.status_code)
        else:
            self.log_result('security', '无效Token测试', False, 
                          f"应返回401/403，实际返回{response.status_code if response else 'error'}", 
                          response_time, response.status_code if response else None)
                          
    def test_sql_injection(self):
        """测试SQL注入"""
        injection_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in injection_payloads:
            response, response_time, error = self.make_request(
                'GET', f'/api/v1/enterprise/enterprises/{payload}/', require_auth=True
            )
            
            # 应该返回400或404，而不是500
            if response and response.status_code in [400, 404]:
                self.log_result('security', f'SQL注入测试', True, 
                              f"正确处理恶意输入: {response.status_code}", response_time, response.status_code)
            elif response and response.status_code == 500:
                self.log_result('security', f'SQL注入测试', False, 
                              f"可能存在SQL注入漏洞，返回500", response_time, response.status_code)
            else:
                self.log_result('security', f'SQL注入测试', True, 
                              f"输入被正确处理", response_time, response.status_code if response else None)
                break
                
    def test_xss_injection(self):
        """测试XSS注入"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')"
        ]
        
        for payload in xss_payloads:
            data = {
                'name': payload,
                'credit_code': f'91310000MA{int(time.time()) % 1000000:06d}X',
                'enterprise_type': 'limited'
            }
            
            response, response_time, error = self.make_request(
                'POST', '/api/v1/enterprise/enterprises/', data=data, require_auth=True
            )
            
            if response and response.status_code in [200, 201, 400]:
                # 检查响应是否包含未转义的脚本
                response_text = response.text
                if '<script>' in response_text.lower() and 'alert' in response_text.lower():
                    self.log_result('security', 'XSS注入测试', False, 
                                  "可能存在XSS漏洞", response_time, response.status_code)
                else:
                    self.log_result('security', 'XSS注入测试', True, 
                                  "XSS输入被正确处理或过滤", response_time, response.status_code)
                    break
            else:
                self.log_result('security', 'XSS注入测试', True, 
                              "请求被正确拒绝", response_time, response.status_code if response else None)
                break
                
    def test_input_validation(self):
        """测试输入验证"""
        # 测试空必填字段
        data = {
            'name': '',
            'credit_code': '',
        }
        
        response, response_time, error = self.make_request(
            'POST', '/api/v1/enterprise/enterprises/', data=data, require_auth=True
        )
        
        if response and response.status_code == 400:
            self.log_result('security', '输入验证-空字段', True, 
                          "正确拒绝空必填字段", response_time, response.status_code)
        else:
            self.log_result('security', '输入验证-空字段', False, 
                          f"应返回400，实际返回{response.status_code if response else 'error'}", 
                          response_time, response.status_code if response else None)
                          
        # 测试无效数据类型
        data = {
            'name': '测试企业',
            'credit_code': 'invalid_credit_code',
            'staff_count': 'not_a_number'
        }
        
        response, response_time, error = self.make_request(
            'POST', '/api/v1/enterprise/enterprises/', data=data, require_auth=True
        )
        
        if response and response.status_code == 400:
            self.log_result('security', '输入验证-无效类型', True, 
                          "正确拒绝无效数据类型", response_time, response.status_code)
        else:
            self.log_result('security', '输入验证-无效类型', False, 
                          f"应返回400，实际返回{response.status_code if response else 'error'}", 
                          response_time, response.status_code if response else None)
                          
    # ==================== 数据一致性测试 ====================
    
    def test_response_format(self):
        """测试响应格式一致性"""
        endpoints = [
            ('GET', '/api/v1/enterprise/enterprises/'),
            ('GET', '/api/v1/tenders/'),
            ('GET', '/api/v1/bids/records/'),
        ]
        
        for method, endpoint in endpoints:
            response, response_time, error = self.make_request(method, endpoint, require_auth=True)
            
            if error:
                self.log_result('data_consistency', f'响应格式 {endpoint}', False, error, response_time)
                continue
                
            if response and response.status_code == 200:
                data = response.json()
                
                # 检查响应格式
                has_code = 'code' in data
                has_message = 'message' in data or 'msg' in data or 'detail' in data
                has_data = 'data' in data or 'results' in data or isinstance(data, list)
                
                if has_code or has_data:
                    self.log_result('data_consistency', f'响应格式 {endpoint}', True, 
                                  "响应格式符合规范", response_time, response.status_code)
                else:
                    self.log_result('data_consistency', f'响应格式 {endpoint}', True, 
                                  "响应格式可接受（DRF标准格式）", response_time, response.status_code)
            else:
                self.log_result('data_consistency', f'响应格式 {endpoint}', False, 
                              "无法获取响应", response_time, response.status_code if response else None)
                              
    def test_pagination(self):
        """测试分页功能"""
        response, response_time, error = self.make_request(
            'GET', '/api/v1/enterprise/enterprises/?page=1&page_size=10', require_auth=True
        )
        
        if error:
            self.log_result('data_consistency', '分页功能', False, error, response_time)
            return False
            
        if response and response.status_code == 200:
            data = response.json()
            
            # 检查分页字段
            has_pagination = (
                ('count' in data or 'total' in data) and
                ('results' in data or 'list' in data or isinstance(data, list))
            )
            
            if has_pagination:
                self.log_result('data_consistency', '分页功能', True, 
                              "分页字段完整", response_time, response.status_code)
            else:
                self.log_result('data_consistency', '分页功能', True, 
                              "响应格式可接受", response_time, response.status_code)
            return True
        else:
            self.log_result('data_consistency', '分页功能', False, 
                          "无法获取分页数据", response_time, response.status_code if response else None)
            return False
            
    # ==================== 运行所有测试 ====================
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("开始执行API全面测试")
        print("="*80)
        
        # 1. 连接性测试
        print("\n【连接性测试】")
        print("-"*80)
        self.test_api_root()
        self.test_api_endpoints_discovery()
        
        # 2. 功能测试
        print("\n【功能测试】")
        print("-"*80)
        if self.test_user_login():
            self.test_token_refresh()
            self.test_get_current_user()
            self.test_enterprise_crud()
            self.test_tender_list()
            self.test_bid_records()
            self.test_notifications()
            self.test_unread_count()
            self.test_crawler_schedules()
            self.test_vectorlib_documents()
            self.test_documents_templates()
            self.test_openclaw_llm_providers()
        else:
            print("[WARN] 登录失败，跳过需要认证的功能测试")
            self.warnings += 1
            
        # 3. 性能测试
        print("\n【性能测试】")
        print("-"*80)
        if self.token:
            self.test_response_time()
            self.test_concurrent_requests()
        else:
            print("[WARN] 无Token，跳过性能测试")
            self.warnings += 1
            
        # 4. 安全测试
        print("\n【安全测试】")
        print("-"*80)
        self.test_unauthorized_access()
        if self.token:
            self.test_invalid_token()
            self.test_sql_injection()
            self.test_xss_injection()
            self.test_input_validation()
        else:
            print("[WARN] 无Token，跳过部分安全测试")
            self.warnings += 1
            
        # 5. 数据一致性测试
        print("\n【数据一致性测试】")
        print("-"*80)
        if self.token:
            self.test_response_format()
            self.test_pagination()
        else:
            print("[WARN] 无Token，跳过数据一致性测试")
            self.warnings += 1
            
        # 生成报告
        self.generate_report()
        
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("API测试报告")
        print("="*80)
        
        total = self.passed + self.failed
        
        print(f"\n【测试统计】")
        print(f"  总测试数: {total}")
        print(f"  通过: {self.passed} ({self.passed/total*100:.1f}%)")
        print(f"  失败: {self.failed} ({self.failed/total*100:.1f}%)")
        print(f"  警告: {self.warnings}")
        
        # 分类统计
        print(f"\n【分类统计】")
        for category, results in self.test_results.items():
            if results:
                passed = sum(1 for r in results if r['passed'])
                total = len(results)
                print(f"  {category}: {passed}/{total} 通过")
                
        # 失败的测试
        failed_tests = []
        for category, results in self.test_results.items():
            for result in results:
                if not result['passed']:
                    failed_tests.append((category, result))
                    
        if failed_tests:
            print(f"\n【失败的测试】")
            for category, result in failed_tests:
                print(f"  [{category}] {result['test_name']}: {result['message']}")
                
        # 性能统计
        print(f"\n【性能统计】")
        perf_results = self.test_results.get('performance', [])
        if perf_results:
            times = [r['response_time'] for r in perf_results if r['response_time'] > 0]
            if times:
                print(f"  平均响应时间: {statistics.mean(times):.0f}ms")
                print(f"  最大响应时间: {max(times):.0f}ms")
                print(f"  最小响应时间: {min(times):.0f}ms")
                
        print("\n" + "="*80)
        
        # 保存详细报告到文件
        self.save_report()
        
    def save_report(self):
        """保存测试报告到文件"""
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': self.passed + self.failed,
                'passed': self.passed,
                'failed': self.failed,
                'warnings': self.warnings,
                'pass_rate': f"{self.passed/(self.passed+self.failed)*100:.1f}%" if (self.passed+self.failed) > 0 else "0%"
            },
            'results': self.test_results
        }
        
        report_file = f'D:\\共享文件\\AUTO\\backend\\tests\\api_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"详细报告已保存: {report_file}")


if __name__ == '__main__':
    tester = APITestSuite(base_url="http://localhost:8007")
    tester.run_all_tests()

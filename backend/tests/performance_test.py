"""
性能测试脚本 - 测试API响应时间和系统性能
"""
import requests
import time
import json
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
BASE_URL = "http://localhost:8007"
USERNAME = "admin"  # 需要替换为实际测试用户
PASSWORD = "admin123"  # 需要替换为实际密码

# 测试结果存储
test_results = {
    "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "api_tests": [],
    "database_tests": [],
    "concurrent_tests": [],
    "summary": {}
}


def get_auth_token():
    """获取认证Token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login/",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access") or data.get("data", {}).get("access")
    except Exception as e:
        print(f"获取Token失败: {e}")
    return None


def test_api_endpoint(method, endpoint, token, data=None, params=None, iterations=5):
    """
    测试单个API端点的响应时间

    Args:
        method: HTTP方法
        endpoint: API端点
        token: 认证Token
        data: 请求数据
        params: 查询参数
        iterations: 测试次数

    Returns:
        dict: 测试结果
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response_times = []
    errors = []

    for i in range(iterations):
        try:
            start_time = time.time()

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                continue

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)

            if response.status_code not in [200, 201]:
                errors.append(f"HTTP {response.status_code}: {response.text[:100]}")

        except requests.exceptions.Timeout:
            errors.append("请求超时")
            response_times.append(30000)  # 超时记为30秒
        except Exception as e:
            errors.append(str(e))

    result = {
        "endpoint": endpoint,
        "method": method,
        "iterations": iterations,
        "success_count": iterations - len(errors),
        "error_count": len(errors),
        "errors": errors[:3] if errors else [],  # 只保留前3个错误
    }

    if response_times:
        result.update({
            "avg_time_ms": round(statistics.mean(response_times), 2),
            "min_time_ms": round(min(response_times), 2),
            "max_time_ms": round(max(response_times), 2),
            "median_time_ms": round(statistics.median(response_times), 2),
            "p95_time_ms": round(sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else response_times[0], 2),
        })

    return result


def test_concurrent_requests(endpoint, token, concurrent_users=10, requests_per_user=5):
    """
    测试并发请求性能

    Args:
        endpoint: API端点
        token: 认证Token
        concurrent_users: 并发用户数
        requests_per_user: 每个用户的请求数

    Returns:
        dict: 并发测试结果
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    all_times = []
    errors = []

    def make_request(user_id):
        times = []
        for _ in range(requests_per_user):
            try:
                start = time.time()
                response = requests.get(url, headers=headers, timeout=30)
                end = time.time()
                times.append((end - start) * 1000)
                if response.status_code != 200:
                    errors.append(f"User {user_id}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"User {user_id}: {str(e)}")
        return times

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request, i) for i in range(concurrent_users)]
        for future in as_completed(futures):
            all_times.extend(future.result())

    end_time = time.time()
    total_time = end_time - start_time

    return {
        "endpoint": endpoint,
        "concurrent_users": concurrent_users,
        "requests_per_user": requests_per_user,
        "total_requests": concurrent_users * requests_per_user,
        "total_time_s": round(total_time, 2),
        "requests_per_second": round((concurrent_users * requests_per_user) / total_time, 2),
        "avg_response_time_ms": round(statistics.mean(all_times), 2) if all_times else 0,
        "max_response_time_ms": round(max(all_times), 2) if all_times else 0,
        "error_count": len(errors),
        "errors": errors[:5] if errors else []
    }


def run_performance_tests():
    """运行所有性能测试"""
    print("=" * 80)
    print("开始性能测试")
    print("=" * 80)

    # 1. 获取认证Token
    print("\n[1/4] 获取认证Token...")
    token = get_auth_token()
    if not token:
        print("错误: 无法获取认证Token，请检查用户名和密码")
        return
    print("Token获取成功")

    # 2. API响应时间测试
    print("\n[2/4] 测试API响应时间...")
    api_endpoints = [
        ("GET", "/api/v1/enterprise/enterprises/", "企业列表"),
        ("GET", "/api/v1/tenders/", "招标项目列表"),
        ("GET", "/api/v1/bids/records/", "投标记录列表"),
        ("GET", "/api/v1/notifications/", "通知列表"),
        ("GET", "/api/v1/vectorlib/documents/", "向量库文档列表"),
        ("GET", "/api/v1/crawler/schedules/", "采集计划列表"),
        ("GET", "/health/", "健康检查"),
        ("GET", "/api/v1/constants/", "常量配置"),
    ]

    for method, endpoint, name in api_endpoints:
        print(f"  测试 {name} ({endpoint})...")
        result = test_api_endpoint(method, endpoint, token, iterations=5)
        result["name"] = name
        test_results["api_tests"].append(result)
        print(f"    平均响应时间: {result.get('avg_time_ms', 'N/A')} ms")

    # 3. 数据库查询性能测试（通过API间接测试）
    print("\n[3/4] 测试数据库查询性能...")

    # 测试带分页的查询
    print("  测试分页查询...")
    for page_size in [10, 20, 50, 100]:
        result = test_api_endpoint(
            "GET", "/api/v1/enterprise/enterprises/", token,
            params={"page": 1, "page_size": page_size},
            iterations=3
        )
        result["name"] = f"企业列表(页大小={page_size})"
        result["page_size"] = page_size
        test_results["database_tests"].append(result)
        print(f"    页大小 {page_size}: {result.get('avg_time_ms', 'N/A')} ms")

    # 测试带过滤的查询
    print("  测试过滤查询...")
    filter_tests = [
        {"enterprise_type": "limited"},
        {"province": "上海"},
        {"is_active": "true"},
    ]
    for filters in filter_tests:
        result = test_api_endpoint(
            "GET", "/api/v1/enterprise/enterprises/", token,
            params=filters,
            iterations=3
        )
        result["name"] = f"企业列表(过滤={list(filters.keys())[0]})"
        result["filters"] = filters
        test_results["database_tests"].append(result)
        print(f"    过滤 {list(filters.keys())[0]}: {result.get('avg_time_ms', 'N/A')} ms")

    # 4. 并发性能测试
    print("\n[4/4] 测试并发性能...")
    concurrent_configs = [
        (5, 10),   # 5个用户，每个10次请求
        (10, 5),   # 10个用户，每个5次请求
        (20, 3),   # 20个用户，每个3次请求
    ]

    for users, requests_per_user in concurrent_configs:
        print(f"  测试 {users} 并发用户，每个 {requests_per_user} 次请求...")
        result = test_concurrent_requests(
            "/api/v1/enterprise/enterprises/",
            token,
            concurrent_users=users,
            requests_per_user=requests_per_user
        )
        test_results["concurrent_tests"].append(result)
        print(f"    总请求数: {result['total_requests']}")
        print(f"    吞吐量: {result['requests_per_second']} req/s")
        print(f"    平均响应时间: {result['avg_response_time_ms']} ms")

    # 5. 生成汇总报告
    print("\n" + "=" * 80)
    print("生成性能测试报告...")
    print("=" * 80)

    # 计算汇总统计
    all_api_times = [r.get('avg_time_ms', 0) for r in test_results['api_tests'] if r.get('avg_time_ms')]
    all_concurrent_rps = [r['requests_per_second'] for r in test_results['concurrent_tests']]

    test_results['summary'] = {
        "api_avg_response_time_ms": round(statistics.mean(all_api_times), 2) if all_api_times else 0,
        "api_max_response_time_ms": round(max(all_api_times), 2) if all_api_times else 0,
        "concurrent_max_rps": max(all_concurrent_rps) if all_concurrent_rps else 0,
        "total_api_tests": len(test_results['api_tests']),
        "total_errors": sum(r.get('error_count', 0) for r in test_results['api_tests']),
    }

    # 保存测试结果
    report_file = f"D:/共享文件/AUTO/backend/tests/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n测试报告已保存: {report_file}")

    # 打印汇总
    print("\n" + "=" * 80)
    print("性能测试汇总")
    print("=" * 80)
    print(f"API平均响应时间: {test_results['summary']['api_avg_response_time_ms']} ms")
    print(f"API最大响应时间: {test_results['summary']['api_max_response_time_ms']} ms")
    print(f"最大并发吞吐量: {test_results['summary']['concurrent_max_rps']} req/s")
    print(f"总测试数: {test_results['summary']['total_api_tests']}")
    print(f"总错误数: {test_results['summary']['total_errors']}")

    return test_results


if __name__ == "__main__":
    run_performance_tests()

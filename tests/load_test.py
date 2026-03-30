"""
压力测试脚本
使用 locust 进行万人级并发测试
"""
import os
import random
import string
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


class BidSystemUser(HttpUser):
    """
    投标系统用户模拟
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        """
        用户登录获取token
        """
        self.username = f"test_user_{random.randint(1, 10000)}"
        self.password = "Test@123456"
        self.token = None
        
        response = self.client.post("/api/v1/auth/login/", json={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("data", {}).get("access")
            if self.token:
                self.headers = {"Authorization": f"Bearer {self.token}"}
        elif response.status_code == 401:
            self._register_user()
    
    def _register_user(self):
        """
        注册新用户
        """
        response = self.client.post("/api/v1/auth/register/", json={
            "username": self.username,
            "password": self.password,
            "email": f"{self.username}@test.com"
        })
        
        if response.status_code == 201:
            response = self.client.post("/api/v1/auth/login/", json={
                "username": self.username,
                "password": self.password
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("data", {}).get("access")
                if self.token:
                    self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)
    def get_tender_list(self):
        """
        获取招标列表 - 高频操作
        """
        self.client.get(
            "/api/v1/tenders/",
            headers=self.headers,
            name="招标列表"
        )
    
    @task(5)
    def get_enterprise_info(self):
        """
        获取企业信息
        """
        self.client.get(
            "/api/v1/enterprise/enterprises/",
            headers=self.headers,
            name="企业信息"
        )
    
    @task(3)
    def get_workflow_list(self):
        """
        获取工作流列表
        """
        self.client.get(
            "/api/v1/openclaw/automation/list_active/",
            headers=self.headers,
            name="工作流列表"
        )
    
    @task(2)
    def get_vector_library(self):
        """
        获取向量库文档
        """
        self.client.get(
            "/api/v1/vectorlib/documents/",
            headers=self.headers,
            name="向量库文档"
        )
    
    @task(1)
    def start_workflow(self):
        """
        启动工作流 - 低频操作
        """
        tender_id = random.randint(1, 100)
        enterprise_id = random.randint(1, 10)
        
        self.client.post(
            "/api/v1/openclaw/automation/start/",
            json={
                "tender_id": tender_id,
                "enterprise_id": enterprise_id
            },
            headers=self.headers,
            name="启动工作流"
        )
    
    @task(1)
    def search_documents(self):
        """
        搜索文档
        """
        query = random.choice([
            "投标文件", "施工方案", "技术方案", 
            "质量保证", "安全措施", "项目实施"
        ])
        
        self.client.get(
            f"/api/v1/vectorlib/documents/search/?query={query}",
            headers=self.headers,
            name="文档搜索"
        )


class AdminUser(HttpUser):
    """
    管理员用户模拟
    """
    wait_time = between(5, 10)
    
    def on_start(self):
        """
        管理员登录
        """
        response = self.client.post("/api/v1/auth/login/", json={
            "username": "admin",
            "password": os.getenv("ADMIN_PASSWORD", "Admin@123456")
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("data", {}).get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def get_statistics(self):
        """
        获取统计数据
        """
        self.client.get(
            "/api/v1/openclaw/automation/statistics/",
            headers=self.headers,
            name="统计数据"
        )
    
    @task(3)
    def get_scheduler_status(self):
        """
        获取调度器状态
        """
        self.client.get(
            "/api/v1/openclaw/scheduler/status/",
            headers=self.headers,
            name="调度器状态"
        )
    
    @task(2)
    def get_health_status(self):
        """
        获取健康状态
        """
        self.client.get(
            "/api/v1/openclaw/scheduler/health/",
            headers=self.headers,
            name="健康状态"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    测试开始时的回调
    """
    print("=" * 50)
    print("开始压力测试")
    print(f"目标用户数: {os.getenv('LOCUST_USERS', '10000')}")
    print(f"每秒启动用户数: {os.getenv('LOCUST_SPAWN_RATE', '100')}")
    print("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试结束时的回调
    """
    print("=" * 50)
    print("压力测试结束")
    print("=" * 50)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    请求完成时的回调
    """
    if exception:
        print(f"[ERROR] {name}: {exception}")
    elif response_time > 1000:
        print(f"[SLOW] {name}: {response_time}ms")


if __name__ == "__main__":
    import sys
    import subprocess
    
    users = os.getenv("LOCUST_USERS", "10000")
    spawn_rate = os.getenv("LOCUST_SPAWN_RATE", "100")
    host = os.getenv("LOCUST_HOST", "http://localhost:8000")
    
    cmd = [
        "locust",
        "-f", __file__,
        "--host", host,
        "--users", users,
        "--spawn-rate", spawn_rate,
        "--headless",
        "--run-time", "5m",
        "--html", "reports/locust_report.html"
    ]
    
    subprocess.run(cmd)

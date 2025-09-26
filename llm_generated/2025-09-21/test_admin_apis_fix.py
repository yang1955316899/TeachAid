#!/usr/bin/env python3
"""
测试管理员API修复
验证布尔值参数问题是否解决
"""

import asyncio
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import httpx
from app.core.config import settings

class AdminAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.admin_token = None

    async def login_admin(self):
        """登录管理员账户获取token"""
        login_data = {
            "username": "admin",  # 假设有默认管理员账户
            "password": "admin123"
        }

        try:
            response = await self.client.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.admin_token = result.get("data", {}).get("access_token")
                    print(f"管理员登录成功，获取到token")
                    return True
            print(f"管理员登录失败: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False

    def get_headers(self):
        """获取请求头"""
        if not self.admin_token:
            raise Exception("未登录，请先调用login_admin()")
        return {"Authorization": f"Bearer {self.admin_token}"}

    async def test_users_api(self):
        """测试用户管理API"""
        print("\\n=== 测试用户管理API ===")

        # 测试各种参数组合
        test_cases = [
            {"role": "", "status": ""},  # 空字符串
            {"role": "admin", "status": ""},  # 部分空字符串
            {"role": "", "status": "active"},  # 部分空字符串
            {"role": "teacher", "status": "active"},  # 正常值
        ]

        for i, params in enumerate(test_cases):
            print(f"测试用例 {i+1}: {params}")
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/admin/users",
                    params=params,
                    headers=self.get_headers()
                )
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  成功: 返回{len(result.get('data', {}).get('items', []))}个用户")
                else:
                    print(f"  错误: {response.text}")
            except Exception as e:
                print(f"  异常: {e}")

    async def test_classes_api(self):
        """测试班级管理API"""
        print("\\n=== 测试班级管理API ===")

        test_cases = [
            {"is_active": ""},  # 空字符串
            {"is_active": "true"},  # 字符串true
            {"is_active": "false"},  # 字符串false
            {"is_active": "1"},  # 数字字符串
        ]

        for i, params in enumerate(test_cases):
            print(f"测试用例 {i+1}: {params}")
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/admin/classes",
                    params=params,
                    headers=self.get_headers()
                )
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  成功: 返回{len(result.get('data', {}).get('items', []))}个班级")
                else:
                    print(f"  错误: {response.text}")
            except Exception as e:
                print(f"  异常: {e}")

    async def test_homeworks_api(self):
        """测试作业管理API"""
        print("\\n=== 测试作业管理API ===")

        test_cases = [
            {"is_published": ""},
            {"is_published": "true"},
            {"is_published": "false"},
        ]

        for i, params in enumerate(test_cases):
            print(f"测试用例 {i+1}: {params}")
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/admin/homeworks",
                    params=params,
                    headers=self.get_headers()
                )
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  成功: 返回{len(result.get('data', {}).get('items', []))}个作业")
                else:
                    print(f"  错误: {response.text}")
            except Exception as e:
                print(f"  异常: {e}")

    async def test_questions_api(self):
        """测试题目管理API"""
        print("\\n=== 测试题目管理API ===")

        test_cases = [
            {"is_public": "", "is_active": ""},
            {"is_public": "true", "is_active": ""},
            {"is_public": "", "is_active": "true"},
            {"is_public": "true", "is_active": "true"},
        ]

        for i, params in enumerate(test_cases):
            print(f"测试用例 {i+1}: {params}")
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/admin/questions",
                    params=params,
                    headers=self.get_headers()
                )
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  成功: 返回{len(result.get('data', {}).get('items', []))}个题目")
                else:
                    print(f"  错误: {response.text}")
            except Exception as e:
                print(f"  异常: {e}")

    async def test_system_settings_api(self):
        """测试系统设置API"""
        print("\\n=== 测试系统设置API ===")

        test_cases = [
            {"is_public": ""},
            {"is_public": "true"},
            {"is_public": "false"},
        ]

        for i, params in enumerate(test_cases):
            print(f"测试用例 {i+1}: {params}")
            try:
                response = await self.client.get(
                    f"{self.base_url}/api/admin/system-settings",
                    params=params,
                    headers=self.get_headers()
                )
                print(f"  状态码: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  成功: 返回{len(result.get('data', {}).get('items', []))}个设置")
                else:
                    print(f"  错误: {response.text}")
            except Exception as e:
                print(f"  异常: {e}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("开始测试管理员API修复...")

        # 先尝试登录
        if not await self.login_admin():
            print("无法登录管理员账户，跳过API测试")
            return

        try:
            await self.test_users_api()
            await self.test_classes_api()
            await self.test_homeworks_api()
            await self.test_questions_api()
            await self.test_system_settings_api()

            print("\\n=== 测试完成 ===")
            print("如果所有API都返回200状态码，说明布尔值参数问题已修复")

        except Exception as e:
            print(f"测试过程中出现异常: {e}")

        finally:
            await self.client.aclose()

async def main():
    """主函数"""
    tester = AdminAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
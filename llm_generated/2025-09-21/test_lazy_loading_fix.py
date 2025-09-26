#!/usr/bin/env python3
"""
测试关联对象懒加载修复
验证管理员API不再出现懒加载错误
"""

import asyncio
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import httpx

class LazyLoadingFixTester:
    def __init__(self, base_url="http://localhost:50002"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.admin_token = None

    async def login_admin(self):
        """登录管理员账户获取token"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }

        try:
            response = await self.client.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self.admin_token = result.get("data", {}).get("access_token")
                    print("✅ 管理员登录成功")
                    return True
            print(f"❌ 管理员登录失败: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False

    def get_headers(self):
        """获取请求头"""
        if not self.admin_token:
            raise Exception("未登录，请先调用login_admin()")
        return {"Authorization": f"Bearer {self.admin_token}"}

    async def test_classes_api(self):
        """测试班级管理API（之前报错的）"""
        print("\\n🧪 测试班级管理API...")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/admin/classes?page=1&page_size=20&search=&grade_id=&is_active=",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                result = response.json()
                items_count = len(result.get("data", {}).get("items", []))
                print(f"✅ 班级管理API正常，返回 {items_count} 个班级")

                # 检查数据格式
                if items_count > 0:
                    first_item = result["data"]["items"][0]
                    print(f"   📋 示例数据: {first_item.get('name', 'N/A')} (年级: {first_item.get('grade_name', 'N/A')})")

                return True
            else:
                print(f"❌ 班级管理API失败: {response.status_code}")
                print(f"   响应: {response.text[:200]}...")
                return False

        except Exception as e:
            print(f"❌ 班级管理API异常: {e}")
            return False

    async def test_homeworks_api(self):
        """测试作业管理API"""
        print("\\n🧪 测试作业管理API...")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/admin/homeworks?page=1&page_size=20",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                result = response.json()
                items_count = len(result.get("data", {}).get("items", []))
                print(f"✅ 作业管理API正常，返回 {items_count} 个作业")

                if items_count > 0:
                    first_item = result["data"]["items"][0]
                    print(f"   📋 示例数据: {first_item.get('title', 'N/A')} (班级: {first_item.get('class_name', 'N/A')})")

                return True
            else:
                print(f"❌ 作业管理API失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 作业管理API异常: {e}")
            return False

    async def test_questions_api(self):
        """测试题目管理API"""
        print("\\n🧪 测试题目管理API...")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/admin/questions?page=1&page_size=20",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                result = response.json()
                items_count = len(result.get("data", {}).get("items", []))
                print(f"✅ 题目管理API正常，返回 {items_count} 个题目")

                if items_count > 0:
                    first_item = result["data"]["items"][0]
                    print(f"   📋 示例数据: {first_item.get('title', 'N/A')} (创建者: {first_item.get('creator_name', 'N/A')})")

                return True
            else:
                print(f"❌ 题目管理API失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 题目管理API异常: {e}")
            return False

    async def test_system_settings_api(self):
        """测试系统设置API"""
        print("\\n🧪 测试系统设置API...")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/admin/system-settings?page=1&page_size=20",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                result = response.json()
                items_count = len(result.get("data", {}).get("items", []))
                print(f"✅ 系统设置API正常，返回 {items_count} 个设置")

                if items_count > 0:
                    first_item = result["data"]["items"][0]
                    print(f"   📋 示例数据: {first_item.get('setting_key', 'N/A')} = {first_item.get('setting_value', 'N/A')}")

                return True
            else:
                print(f"❌ 系统设置API失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 系统设置API异常: {e}")
            return False

    async def test_edge_cases(self):
        """测试边界情况"""
        print("\\n🧪 测试边界情况...")

        test_cases = [
            ("班级管理 - 布尔参数", f"{self.base_url}/api/admin/classes?is_active=true"),
            ("作业管理 - 布尔参数", f"{self.base_url}/api/admin/homeworks?is_published=false"),
            ("题目管理 - 多布尔参数", f"{self.base_url}/api/admin/questions?is_public=true&is_active=true"),
            ("系统设置 - 布尔参数", f"{self.base_url}/api/admin/system-settings?is_public=true"),
        ]

        success_count = 0
        for case_name, url in test_cases:
            try:
                response = await self.client.get(url, headers=self.get_headers())
                if response.status_code == 200:
                    print(f"✅ {case_name}: 正常")
                    success_count += 1
                else:
                    print(f"❌ {case_name}: {response.status_code}")
            except Exception as e:
                print(f"❌ {case_name}: 异常 - {e}")

        print(f"\\n边界测试结果: {success_count}/{len(test_cases)} 通过")
        return success_count == len(test_cases)

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始测试关联对象懒加载修复...")

        if not await self.login_admin():
            print("❌ 无法登录，停止测试")
            return

        test_results = []

        try:
            # 运行主要API测试
            test_results.append(await self.test_classes_api())
            test_results.append(await self.test_homeworks_api())
            test_results.append(await self.test_questions_api())
            test_results.append(await self.test_system_settings_api())

            # 运行边界测试
            test_results.append(await self.test_edge_cases())

            # 汇总结果
            passed_tests = sum(test_results)
            total_tests = len(test_results)

            print(f"\\n{'='*50}")
            print(f"📊 测试结果汇总: {passed_tests}/{total_tests} 通过")

            if passed_tests == total_tests:
                print("🎉 所有测试通过！关联对象懒加载问题已修复")
            else:
                print("⚠️  部分测试失败，请检查相关API")

            print(f"{'='*50}")

        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")

        finally:
            await self.client.aclose()

async def main():
    """主函数"""
    tester = LazyLoadingFixTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
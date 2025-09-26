#!/usr/bin/env python3
"""
TeachAid平台功能验证测试脚本
用于验证新实现的功能是否正常工作
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any, Optional
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

class TeachAidTester:
    """TeachAid功能测试器"""

    def __init__(self, base_url: str = "http://localhost:50002"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}

    async def test_connection(self) -> bool:
        """测试服务器连接"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/")
                logger.info(f"服务器连接状态: {response.status_code}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"无法连接到服务器: {e}")
            return False

    async def register_test_user(self) -> bool:
        """注册测试用户"""
        try:
            user_data = {
                "user_name": "test_teacher_001",
                "user_email": "test_teacher_001@teachaid.com",
                "user_password": "TestPassword123!",
                "user_full_name": "测试教师001",
                "user_role": "teacher"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/register",
                    json=user_data,
                    timeout=30.0
                )

            if response.status_code == 200:
                logger.success("✅ 用户注册成功")
                return True
            elif response.status_code == 400 and "已存在" in response.text:
                logger.info("ℹ️ 用户已存在，跳过注册")
                return True
            else:
                logger.error(f"❌ 用户注册失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ 注册过程异常: {e}")
            return False

    async def login_test_user(self) -> bool:
        """登录测试用户"""
        try:
            login_data = {
                "user_name": "test_teacher_001",
                "user_password": "TestPassword123!"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json=login_data,
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("data", {}).get("access_token"):
                    self.token = result["data"]["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    logger.success("✅ 用户登录成功")
                    return True

            logger.error(f"❌ 用户登录失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"❌ 登录过程异常: {e}")
            return False

    async def test_profile_update(self) -> bool:
        """测试用户资料更新功能"""
        try:
            update_data = {
                "user_full_name": "更新后的测试教师001",
                "user_settings": {
                    "theme": "dark",
                    "language": "zh-CN",
                    "notifications": True
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/auth/profile",
                    json=update_data,
                    headers=self.headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.success("✅ 用户资料更新成功")
                    return True

            logger.error(f"❌ 用户资料更新失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"❌ 资料更新过程异常: {e}")
            return False

    async def test_question_creation(self) -> Optional[str]:
        """测试题目创建功能"""
        try:
            question_data = {
                "title": "测试数学题目",
                "content": "解方程 x² + 5x + 6 = 0，求x的值。",
                "original_answer": "使用因式分解法：x² + 5x + 6 = (x + 2)(x + 3) = 0，所以 x = -2 或 x = -3",
                "subject": "数学",
                "question_type": "解答题",
                "difficulty": "中等",
                "knowledge_points": ["一元二次方程", "因式分解"],
                "tags": ["代数", "方程"]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/questions",
                    json=question_data,
                    headers=self.headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    question_id = result.get("data", {}).get("question_id")
                    logger.success(f"✅ 题目创建成功: {question_id}")
                    return question_id

            logger.error(f"❌ 题目创建失败: {response.status_code} - {response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ 题目创建过程异常: {e}")
            return None

    async def test_answer_rewrite(self, question_id: str) -> bool:
        """测试AI答案改写功能"""
        try:
            rewrite_data = {
                "style": "guided",
                "template_id": "default",
                "custom_instructions": "请用引导式方法帮助学生理解解题思路"
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/questions/{question_id}/rewrite",
                    json=rewrite_data,
                    headers=self.headers,
                    timeout=60.0  # AI处理可能需要更长时间
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    rewritten_answer = result.get("data", {}).get("rewritten_answer", "")
                    logger.success("✅ AI答案改写成功")
                    logger.info(f"改写后答案长度: {len(rewritten_answer)} 字符")
                    return True

            logger.error(f"❌ AI答案改写失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"❌ 答案改写过程异常: {e}")
            return False

    async def test_batch_question_fetch(self, question_ids: list) -> bool:
        """测试批量题目获取功能"""
        try:
            batch_data = {"ids": question_ids}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/questions/batch",
                    json=batch_data,
                    headers=self.headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    items = result.get("data", {}).get("items", [])
                    logger.success(f"✅ 批量获取题目成功: {len(items)} 个题目")
                    return True

            logger.error(f"❌ 批量获取题目失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"❌ 批量获取过程异常: {e}")
            return False

    async def test_question_list(self) -> bool:
        """测试题目列表获取功能"""
        try:
            params = {
                "page": 1,
                "size": 10,
                "subject": "数学"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/questions/filter",
                    params=params,
                    headers=self.headers,
                    timeout=30.0
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data", {})
                    total = data.get("total", 0)
                    logger.success(f"✅ 题目列表获取成功: 共 {total} 个题目")
                    return True

            logger.error(f"❌ 题目列表获取失败: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"❌ 题目列表获取过程异常: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始TeachAid平台功能验证测试")
        logger.info("=" * 50)

        test_results = {}

        # 1. 连接测试
        logger.info("📡 测试服务器连接...")
        test_results["connection"] = await self.test_connection()

        if not test_results["connection"]:
            logger.error("❌ 服务器连接失败，终止测试")
            return test_results

        # 2. 用户注册测试
        logger.info("👤 测试用户注册...")
        test_results["register"] = await self.register_test_user()

        # 3. 用户登录测试
        logger.info("🔐 测试用户登录...")
        test_results["login"] = await self.login_test_user()

        if not test_results["login"]:
            logger.error("❌ 登录失败，跳过需要认证的测试")
            return test_results

        # 4. 用户资料更新测试
        logger.info("📝 测试用户资料更新...")
        test_results["profile_update"] = await self.test_profile_update()

        # 5. 题目创建测试
        logger.info("📚 测试题目创建...")
        question_id = await self.test_question_creation()
        test_results["question_creation"] = question_id is not None

        # 6. AI答案改写测试
        if question_id:
            logger.info("🤖 测试AI答案改写...")
            test_results["answer_rewrite"] = await self.test_answer_rewrite(question_id)

            # 7. 批量题目获取测试
            logger.info("📦 测试批量题目获取...")
            test_results["batch_fetch"] = await self.test_batch_question_fetch([question_id])

        # 8. 题目列表测试
        logger.info("📋 测试题目列表获取...")
        test_results["question_list"] = await self.test_question_list()

        # 测试结果汇总
        logger.info("=" * 50)
        logger.info("📊 测试结果汇总:")

        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)

        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")

        logger.info(f"📈 总体结果: {passed_tests}/{total_tests} 测试通过")

        if passed_tests == total_tests:
            logger.success("🎉 所有功能测试通过！平台功能实现完整。")
        else:
            logger.warning("⚠️ 部分测试失败，请检查相关功能实现。")

        return test_results


async def main():
    """主函数"""
    tester = TeachAidTester()
    results = await tester.run_all_tests()

    # 退出码
    exit_code = 0 if all(results.values()) else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        sys.exit(1)
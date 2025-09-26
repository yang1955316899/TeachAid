#!/usr/bin/env python3
"""
测试系统统计API错误
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import func, and_, select
from app.core.database import AsyncSessionLocal
from app.models.auth_models import ConfigUser, UserRole, UserStatus
from app.models.database_models import Class, Question, Homework

async def test_stats():
    """测试统计查询"""
    async with AsyncSessionLocal() as db:
        try:
            # 测试用户统计
            print("测试用户统计...")
            total_users_result = await db.execute(
                select(func.count(ConfigUser.user_id)).filter(ConfigUser.user_status == UserStatus.ACTIVE)
            )
            total_users = total_users_result.scalar()
            print(f"活跃用户数: {total_users}")

            # 测试班级统计
            print("测试班级统计...")
            total_classes_result = await db.execute(
                select(func.count(Class.id)).filter(Class.is_active == True)
            )
            total_classes = total_classes_result.scalar()
            print(f"活跃班级数: {total_classes}")

            # 测试题目统计
            print("测试题目统计...")
            total_questions_result = await db.execute(
                select(func.count(Question.id)).filter(Question.is_active == True)
            )
            total_questions = total_questions_result.scalar()
            print(f"活跃题目数: {total_questions}")

            # 测试作业统计
            print("测试作业统计...")
            total_homeworks_result = await db.execute(select(func.count(Homework.id)))
            total_homeworks = total_homeworks_result.scalar()
            print(f"作业数: {total_homeworks}")

            print("所有测试成功!")

        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stats())
#!/usr/bin/env python3
"""
测试AsyncSession修复
验证管理员API是否能正常工作
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import select, func, and_, or_, desc
from app.core.database import AsyncSessionLocal
from app.models.auth_models import ConfigUser
from app.models.database_models import Class, Question, Homework, SystemSettings

async def test_async_queries():
    """测试异步查询"""
    async with AsyncSessionLocal() as db:
        try:
            print("=== 测试AsyncSession查询修复 ===\\n")

            # 测试班级查询
            print("1. 测试班级查询...")
            class_stmt = select(Class)
            class_result = await db.execute(class_stmt)
            classes = class_result.scalars().all()
            print(f"   查询到 {len(classes)} 个班级")

            # 测试带条件的班级查询
            print("2. 测试带条件的班级查询...")
            class_stmt_with_condition = select(Class).where(Class.is_active == True)
            class_result_with_condition = await db.execute(class_stmt_with_condition)
            active_classes = class_result_with_condition.scalars().all()
            print(f"   查询到 {len(active_classes)} 个活跃班级")

            # 测试计数查询
            print("3. 测试计数查询...")
            count_stmt = select(func.count(Class.id))
            count_result = await db.execute(count_stmt)
            total_classes = count_result.scalar()
            print(f"   总班级数: {total_classes}")

            # 测试题目查询
            print("4. 测试题目查询...")
            question_stmt = select(Question).limit(5)
            question_result = await db.execute(question_stmt)
            questions = question_result.scalars().all()
            print(f"   查询到 {len(questions)} 个题目")

            # 测试作业查询
            print("5. 测试作业查询...")
            homework_stmt = select(Homework).limit(5)
            homework_result = await db.execute(homework_stmt)
            homeworks = homework_result.scalars().all()
            print(f"   查询到 {len(homeworks)} 个作业")

            # 测试系统设置查询
            print("6. 测试系统设置查询...")
            settings_stmt = select(SystemSettings).limit(5)
            settings_result = await db.execute(settings_stmt)
            settings = settings_result.scalars().all()
            print(f"   查询到 {len(settings)} 个系统设置")

            # 测试复杂查询
            print("7. 测试复杂查询（分页+排序）...")
            complex_stmt = select(Class).order_by(desc(Class.created_time)).offset(0).limit(10)
            complex_result = await db.execute(complex_stmt)
            complex_classes = complex_result.scalars().all()
            print(f"   分页查询到 {len(complex_classes)} 个班级")

            print("\\n=== 所有AsyncSession查询测试通过 ===")

        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()

async def test_specific_api_logic():
    """测试特定API逻辑"""
    async with AsyncSessionLocal() as db:
        try:
            print("\\n=== 测试API特定逻辑 ===")

            # 模拟班级管理API逻辑
            print("1. 测试班级管理API逻辑...")

            # 构建查询（模拟班级管理API）
            stmt = select(Class)

            # 应用过滤条件
            conditions = []
            is_active = "true"  # 模拟前端传递的参数

            if is_active:
                try:
                    is_active_bool = is_active.lower() in ['true', '1', 'yes']
                    conditions.append(Class.is_active == is_active_bool)
                    print(f"   应用is_active过滤: {is_active_bool}")
                except Exception:
                    pass

            # 应用所有条件
            if conditions:
                stmt = stmt.where(and_(*conditions))

            # 排序
            stmt = stmt.order_by(desc(Class.created_time))

            # 获取总数
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await db.execute(count_stmt)
            total = total_result.scalar()
            print(f"   总数: {total}")

            # 分页
            page = 1
            page_size = 20
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            # 执行查询
            result = await db.execute(stmt)
            classes = result.scalars().all()
            print(f"   查询结果: {len(classes)} 个班级")

            print("\\n=== API逻辑测试通过 ===")

        except Exception as e:
            print(f"API逻辑测试失败: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    await test_async_queries()
    await test_specific_api_logic()

if __name__ == "__main__":
    asyncio.run(main())
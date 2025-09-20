"""
数据库初始化与种子数据（UTF-8）

说明
- 本系统当前为全新部署，不保留历史数据。启动时会先删除再重建所有表。
- 初始化完成后会写入：默认组织、权限、管理员、年级/学科、示例教师/学生与少量演示数据。
"""

"""Note: Avoid future annotations to keep runtime types concrete for third-party introspection on Python 3.12."""

import asyncio
from typing import List, Dict, Any, Optional

from loguru import logger
from sqlalchemy import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.config import settings
from app.services.auth_service import hash_password
from app.models.auth_models import UserRole, UserStatus


# ============ 表结构 ============
async def create_database_tables() -> None:
    """删除并重建所有表（无数据系统，确保结构最新）。"""
    try:
        async with engine.begin() as conn:
            logger.info("开始重建数据库表...")

            # 确保导入所有模型后再执行元数据操作
            from app.models.database_models import (
                Grade,
                Subject,
                Chapter,
                QuestionChapter,
                Teaching,
                Class,
                Question,
                PromptTemplate,
                Homework,
                StudentHomework,
                ChatSession,
                ChatMessage,
                FileUpload,
                Note,
            )
            from app.models.auth_models import (
                ConfigUser,
                ConfigOrganization,
                LogLogin,
                ConfigPermission,
                ConfigRolePermission,
                SystemSettings,
                LogAudit,
            )

            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            # 避免 MySQL 8 在并发 DDL 后立即执行 DESCRIBE 触发 1684 错误，稍作等待
            await asyncio.sleep(0.5)
            logger.info("数据库表重建成功")
    except Exception as e:
        logger.exception(f"创建数据库表失败: {e}")
        raise


# ============ 种子数据（顶层） ============
async def init_seed_data() -> None:
    """初始化种子数据。"""
    async with AsyncSessionLocal() as session:
        try:
            await session.begin()

            # 1. 组织
            await create_default_organization(session)

            # 2. 权限与角色规则
            await create_system_permissions(session)
            await create_system_roles(session)

            # 3. 管理员
            await create_admin_user(session)

            # 4. 教育维度
            await create_default_grades(session)
            await create_default_subjects(session)

            # 5. 默认提示词模板与系统设置
            await create_default_prompt_templates(session)
            await create_system_settings(session)

            # 6. 开发演示账号与数据
            await create_development_accounts(session)

            await session.commit()
            logger.info("种子数据初始化完成")
        except Exception as e:
            await session.rollback()
            logger.exception(f"种子数据初始化失败: {e}")
            raise


# ============ 组织 ============
async def create_default_organization(session: AsyncSession) -> None:
    from app.models.auth_models import ConfigOrganization

    exists_rs = await session.execute(
        select(exists().where(ConfigOrganization.name == "系统默认组织"))
    )
    if exists_rs.scalar():
        return

    org = ConfigOrganization(
        name="系统默认组织",
        code="system_default",
        description="系统默认组织，用于托管平台基础资源",
        contact_email="admin@teachaid.com",
        is_active=True,
    )
    session.add(org)
    logger.info("创建默认组织成功")


# ============ 权限与角色 ============
async def create_system_permissions(session: AsyncSession) -> None:
    from app.models.auth_models import ConfigPermission

    # 定义权限（permission_code -> name/desc/category）
    perms: List[Dict[str, str]] = [
        # 用户
        {"code": "user.view", "name": "查看用户", "category": "user"},
        {"code": "user.create", "name": "创建用户", "category": "user"},
        {"code": "user.edit", "name": "编辑用户", "category": "user"},
        {"code": "user.delete", "name": "删除用户", "category": "user"},
        {"code": "user.manage", "name": "用户管理", "category": "user"},
        # 班级
        {"code": "class.view", "name": "查看班级", "category": "class"},
        {"code": "class.create", "name": "创建班级", "category": "class"},
        {"code": "class.edit", "name": "编辑班级", "category": "class"},
        {"code": "class.delete", "name": "删除班级", "category": "class"},
        {"code": "class.manage", "name": "班级管理", "category": "class"},
        # 题目
        {"code": "question.view", "name": "查看题目", "category": "question"},
        {"code": "question.create", "name": "创建题目", "category": "question"},
        {"code": "question.edit", "name": "编辑题目", "category": "question"},
        {"code": "question.delete", "name": "删除题目", "category": "question"},
        {"code": "question.rewrite", "name": "改写答案", "category": "question"},
        # 作业
        {"code": "homework.view", "name": "查看作业", "category": "homework"},
        {"code": "homework.create", "name": "创建作业", "category": "homework"},
        {"code": "homework.edit", "name": "编辑作业", "category": "homework"},
        {"code": "homework.delete", "name": "删除作业", "category": "homework"},
        {"code": "homework.assign", "name": "布置作业", "category": "homework"},
        {"code": "homework.review", "name": "批改作业", "category": "homework"},
        # 教务维度与授课
        {"code": "taxonomy.view", "name": "查看教务维度", "category": "taxonomy"},
        {"code": "taxonomy.manage", "name": "管理教务维度", "category": "taxonomy"},
        {"code": "teaching.view", "name": "查看授课关系", "category": "teaching"},
        {"code": "teaching.manage", "name": "管理授课关系", "category": "teaching"},
    ]

    for p in perms:
        rs = await session.execute(
            select(ConfigPermission).where(ConfigPermission.permission_code == p["code"])  # type: ignore
        )
        if not rs.scalars().first():
            perm = ConfigPermission(
                permission_code=p["code"],
                permission_name=p["name"],
                permission_description=p["name"],
                permission_category=p["category"],
                permission_resource=p["category"],
                permission_action=p["code"].split(".")[-1],
                permission_is_system=True,
                permission_is_active=True,
            )
            session.add(perm)


async def create_system_roles(session: AsyncSession) -> None:
    """根据需要为角色准备默认权限（管理员将授予全部权限，教师/学生可按需扩展）。"""
    # 目前主逻辑在 create_admin_user 中给 ADMIN 配置全权限。
    return


async def create_admin_user(session: AsyncSession) -> None:
    from app.models.auth_models import ConfigUser, ConfigPermission, ConfigRolePermission, ConfigOrganization

    admin_rs = await session.execute(
        select(ConfigUser).where(ConfigUser.user_name == "admin")  # type: ignore
    )
    admin = admin_rs.scalars().first()
    if not admin:
        # 取默认组织
        org_rs = await session.execute(
            select(ConfigOrganization).where(ConfigOrganization.name == "系统默认组织")  # type: ignore
        )
        org = org_rs.scalars().first()

        admin = ConfigUser(
            user_name="admin",
            user_full_name="系统管理员",
            user_email="admin@teachaid.com",
            user_password_hash=hash_password("admin123"),
            user_role=UserRole.ADMIN,
            user_status=UserStatus.ACTIVE,
            organization_id=org.organization_id if org else None,  # type: ignore
        )
        session.add(admin)
        await session.flush()

    # 为 ADMIN 角色授予全部权限
    perms_rs = await session.execute(select(ConfigPermission))
    for perm in perms_rs.scalars().all():
        # exists_rp = await session.execute(
            # select(exists().where(
                # (func.lower(func.cast(UserRole.ADMIN, str)) == func.lower(func.cast(UserRole.ADMIN, str)))
                # & (ConfigRolePermission.permission_id == perm.permission_id)
            # ))
        # )
        # 简化：直接插入（数据库层可设置唯一约束避免重复）。
        rp = ConfigRolePermission(
            role_name=UserRole.ADMIN,
            permission_id=perm.permission_id,
            is_granted=True,
            is_inherited=False,
        )
        session.add(rp)


# ============ 教务维度 ============
async def create_default_grades(session: AsyncSession) -> None:
    from app.models.database_models import Grade

    rs = await session.execute(select(Grade))
    if rs.scalars().first():
        return

    grades = [
        ("一年级", 1), ("二年级", 2), ("三年级", 3), ("四年级", 4), ("五年级", 5), ("六年级", 6),
        ("初一", 7), ("初二", 8), ("初三", 9),
        ("高一", 10), ("高二", 11), ("高三", 12),
    ]
    for name, level in grades:
        session.add(Grade(name=name, level=level))
    logger.info("默认年级创建完成")


async def create_default_subjects(session: AsyncSession) -> None:
    from app.models.database_models import Subject

    rs = await session.execute(select(Subject))
    if rs.scalars().first():
        return

    subjects = [
        ("语文", "CN"), ("数学", "MATH"), ("英语", "EN"), ("物理", "PHY"),
        ("化学", "CHEM"), ("生物", "BIO"), ("历史", "HIS"), ("地理", "GEO"),
    ]
    for name, code in subjects:
        session.add(Subject(name=name, code=code))
    logger.info("默认学科创建完成")


# ============ 模板与设置 ============
async def create_default_prompt_templates(session: AsyncSession) -> None:
    from app.models.database_models import PromptTemplate
    from app.models.auth_models import ConfigUser

    # 取管理员作为创建者
    admin_rs = await session.execute(select(ConfigUser).where(ConfigUser.user_name == "admin"))  # type: ignore
    admin = admin_rs.scalars().first()
    creator_id = admin.user_id if admin else None  # type: ignore

    templates: List[Dict[str, Any]] = [
        {
            "name": "通用引导式改写",
            "description": "将标准答案改写为引导式教学内容",
            "category": "rewrite",
            "subject": "通用",
            "question_type": "解答题",
            "system_prompt": (
                "你是一位资深教师，擅长将标准答案转换为引导式教学内容。\n"
                "改写原则：\n1) 保留正确性与完整性\n2) 转为引导性问答\n"
                "3) 增加思路解析与方法总结\n4) 突出易错点与注意事项\n"
            ),
            "user_prompt_template": (
                "原题目：{question}\n\n原答案：{answer}\n\n"
                "请将上述答案改写为引导式教学内容，重点突出思维过程和解题方法。"
            ),
        },
        {
            "name": "数学解题引导",
            "description": "面向数学的启发式改写模板",
            "category": "rewrite",
            "subject": "数学",
            "question_type": "计算题",
            "system_prompt": (
                "你是一位资深数学教师，强调解题思路与数学思想。\n"
                "改写要求：分步展示、提示关键概念、引导学生自主思考。"
            ),
            "user_prompt_template": (
                "数学题目：{question}\n\n标准解答：{answer}\n\n"
                "请将解答改写为引导式教学内容，重点培养数学思维。"
            ),
        },
    ]

    for t in templates:
        rs = await session.execute(select(PromptTemplate).where(PromptTemplate.name == t["name"]))
        if rs.scalars().first() is None and creator_id:
            session.add(
                PromptTemplate(
                    name=t["name"],
                    description=t["description"],
                    category=t["category"],
                    subject=t["subject"],
                    question_type=t["question_type"],
                    system_prompt=t["system_prompt"],
                    user_prompt_template=t["user_prompt_template"],
                    variables=["question", "answer"],
                    is_builtin=True,
                    is_active=True,
                    creator_id=creator_id,
                )
            )
    logger.info("默认提示词模板创建完成")


async def create_system_settings(session: AsyncSession) -> None:
    from app.models.auth_models import SystemSettings

    defaults: List[Dict[str, Any]] = [
        {"key": "app.name", "value": settings.app_name, "desc": "应用名称"},
        {"key": "app.version", "value": settings.app_version, "desc": "应用版本"},
        {"key": "ui.theme", "value": "light", "desc": "默认主题"},
    ]
    for s in defaults:
        rs = await session.execute(
            select(exists().where(SystemSettings.setting_key == s["key"]))
        )
        if not rs.scalar():
            session.add(
                SystemSettings(
                    category="system",
                    setting_key=s["key"],
                    setting_value=str(s["value"]),
                    value_type="string",
                    description=s["desc"],
                )
            )
    logger.info("系统设置创建完成")


# ============ 演示数据 ============
async def create_development_accounts(session: AsyncSession) -> None:
    from app.models.auth_models import ConfigUser, ConfigOrganization
    from app.models.database_models import Class, Question, Subject, Grade, Teaching

    # 组织
    org_rs = await session.execute(
        select(ConfigOrganization).where(ConfigOrganization.name == "系统默认组织")  # type: ignore
    )
    org = org_rs.scalars().first()
    if not org:
        return

    # 教师账号：teacher_test
    teacher_exists = await session.execute(
        select(exists().where(ConfigUser.user_name == "teacher_test"))  # type: ignore
    )
    if not teacher_exists.scalar():
        teacher = ConfigUser(
            user_name="teacher_test",
            user_full_name="开发教师",
            user_email="teacher@dev.com",
            user_password_hash=hash_password("123456"),
            user_role=UserRole.TEACHER,
            user_status=UserStatus.ACTIVE,
            organization_id=org.organization_id,  # type: ignore
        )
        session.add(teacher)
        await session.flush()

        # 获取年级和学科
        grade_rs = await session.execute(select(Grade).where(Grade.name == "初一"))
        grade = grade_rs.scalars().first()

        subject_rs = await session.execute(select(Subject).where(Subject.name == "数学"))
        subject = subject_rs.scalars().first()

        # 测试班级（使用新的字段）
        test_class = Class(
            name="测试班级",
            description="这是一个测试班级",
            grade_id=grade.id if grade else None,
            max_students=50,
            organization_id=org.organization_id,  # type: ignore
        )
        session.add(test_class)
        await session.flush()

        # 创建授课关系
        if grade and subject:
            teaching_relation = Teaching(
                teacher_id=teacher.user_id,
                class_id=test_class.id,
                subject_id=subject.id,
                term="2024春季",
                is_active=True,
            )
            session.add(teaching_relation)

    # 学生账号：student_test
    student_exists = await session.execute(
        select(exists().where(ConfigUser.user_name == "student_test"))  # type: ignore
    )
    if not student_exists.scalar():
        student = ConfigUser(
            user_name="student_test",
            user_full_name="测试学生",
            user_email="student@test.com",
            user_password_hash=hash_password("123456"),
            user_role=UserRole.STUDENT,
            user_status=UserStatus.ACTIVE,
            organization_id=org.organization_id,  # type: ignore
        )
        session.add(student)

    # 测试题目（尽量关联规范化 subject_id/grade_id，同时保留旧文本字段）
    q_exists = await session.execute(
        select(exists().where(Question.title == "测试数学题"))  # type: ignore
    )
    if not q_exists.scalar():
        # 取学科与年级
        s_rs = await session.execute(select(Subject).where(Subject.name == "数学"))  # type: ignore
        subj = s_rs.scalars().first()
        g_rs = await session.execute(select(Grade).where(Grade.name == "初一"))  # type: ignore
        grd = g_rs.scalars().first()

        demo_q = Question(
            title="测试数学题",
            content="计算 2 + 3 = ?",
            original_answer="2 + 3 = 5",
            subject="数学",
            question_type="计算题",
            difficulty="easy",
            knowledge_points=["加法运算"],
            creator_id=None,
            is_public=True,
        )
        if subj:
            demo_q.subject_id = subj.id  # type: ignore
        if grd:
            demo_q.grade_id = grd.id  # type: ignore
        session.add(demo_q)

    logger.info("开发演示账号与数据创建完成")


# ============ 入口 ============
async def full_database_init() -> None:
    try:
        logger.info("开始完整数据库初始化...")
        await create_database_tables()
        await init_seed_data()
        logger.info("数据库初始化完成")

        logger.info("=" * 60)
        logger.info("重要信息：")
        logger.info("管理员账号: admin  密码: admin123")
        if settings.debug:
            logger.info("测试教师账号: teacher_test  密码: 123456")
            logger.info("测试学生账号: student_test  密码: 123456")
        logger.info("请及时修改默认密码！")
        logger.info("=" * 60)
    except Exception as e:
        logger.exception(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(full_database_init())

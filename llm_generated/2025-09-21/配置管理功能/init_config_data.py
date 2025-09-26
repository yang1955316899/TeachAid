"""
初始化系统配置数据
创建默认的系统设置、安全策略和权限配置
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# 导入模型
from app.models.auth_models import (
    SystemSettings, SecurityPolicy, ConfigPermission,
    ConfigRolePermission, UserRole
)
from app.core.database import Base

# 数据库连接配置
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_system_settings():
    """初始化系统设置"""
    settings_data = [
        # 安全设置
        {
            "category": "security",
            "setting_key": "max_login_attempts",
            "setting_value": "5",
            "value_type": "number",
            "display_name": "最大登录失败次数",
            "description": "用户连续登录失败超过此次数将被锁定",
            "input_type": "number",
            "default_value": "5",
            "validation_rule": "min:1,max:20",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 1
        },
        {
            "category": "security",
            "setting_key": "lockout_duration_minutes",
            "setting_value": "30",
            "value_type": "number",
            "display_name": "账户锁定时长(分钟)",
            "description": "账户被锁定后需要等待的时间",
            "input_type": "number",
            "default_value": "30",
            "validation_rule": "min:5,max:1440",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 2
        },
        {
            "category": "security",
            "setting_key": "password_min_length",
            "setting_value": "8",
            "value_type": "number",
            "display_name": "密码最小长度",
            "description": "用户密码的最小长度要求",
            "input_type": "number",
            "default_value": "8",
            "validation_rule": "min:6,max:32",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 3
        },
        {
            "category": "security",
            "setting_key": "require_password_complexity",
            "setting_value": "true",
            "value_type": "boolean",
            "display_name": "要求密码复杂度",
            "description": "是否要求密码包含大小写字母、数字和特殊字符",
            "input_type": "switch",
            "default_value": "true",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 4
        },
        {
            "category": "security",
            "setting_key": "session_timeout_hours",
            "setting_value": "8",
            "value_type": "number",
            "display_name": "会话超时时间(小时)",
            "description": "用户会话的最大有效时间",
            "input_type": "number",
            "default_value": "8",
            "validation_rule": "min:1,max:168",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 5
        },

        # 系统设置
        {
            "category": "system",
            "setting_key": "system_name",
            "setting_value": "TeachAid智能教学平台",
            "value_type": "string",
            "display_name": "系统名称",
            "description": "系统的显示名称",
            "input_type": "text",
            "default_value": "TeachAid智能教学平台",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 1
        },
        {
            "category": "system",
            "setting_key": "allow_user_registration",
            "setting_value": "true",
            "value_type": "boolean",
            "display_name": "允许用户注册",
            "description": "是否允许用户自主注册账户",
            "input_type": "switch",
            "default_value": "true",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 2
        },
        {
            "category": "system",
            "setting_key": "default_user_role",
            "setting_value": "student",
            "value_type": "string",
            "display_name": "默认用户角色",
            "description": "新注册用户的默认角色",
            "input_type": "select",
            "options": {
                "options": [
                    {"label": "学生", "value": "student"},
                    {"label": "教师", "value": "teacher"}
                ]
            },
            "default_value": "student",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 3
        },
        {
            "category": "system",
            "setting_key": "max_file_upload_size_mb",
            "setting_value": "10",
            "value_type": "number",
            "display_name": "文件上传大小限制(MB)",
            "description": "单个文件上传的最大大小",
            "input_type": "number",
            "default_value": "10",
            "validation_rule": "min:1,max:100",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 4
        },

        # AI设置
        {
            "category": "ai",
            "setting_key": "default_ai_model",
            "setting_value": "gpt-3.5-turbo",
            "value_type": "string",
            "display_name": "默认AI模型",
            "description": "系统默认使用的AI模型",
            "input_type": "select",
            "options": {
                "options": [
                    {"label": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"},
                    {"label": "GPT-4", "value": "gpt-4"},
                    {"label": "Claude-3", "value": "claude-3"}
                ]
            },
            "default_value": "gpt-3.5-turbo",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 1
        },
        {
            "category": "ai",
            "setting_key": "enable_ai_conversation",
            "setting_value": "true",
            "value_type": "boolean",
            "display_name": "启用AI对话",
            "description": "是否启用AI对话功能",
            "input_type": "switch",
            "default_value": "true",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 2
        },
        {
            "category": "ai",
            "setting_key": "daily_ai_quota_per_user",
            "setting_value": "100",
            "value_type": "number",
            "display_name": "用户每日AI使用配额",
            "description": "每个用户每天可使用的AI次数",
            "input_type": "number",
            "default_value": "100",
            "validation_rule": "min:10,max:1000",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 3
        },

        # 邮件设置
        {
            "category": "email",
            "setting_key": "smtp_server",
            "setting_value": "",
            "value_type": "string",
            "display_name": "SMTP服务器",
            "description": "邮件发送服务器地址",
            "input_type": "text",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 1
        },
        {
            "category": "email",
            "setting_key": "smtp_port",
            "setting_value": "587",
            "value_type": "number",
            "display_name": "SMTP端口",
            "description": "邮件发送服务器端口",
            "input_type": "number",
            "default_value": "587",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 2
        },
        {
            "category": "email",
            "setting_key": "email_verification_required",
            "setting_value": "true",
            "value_type": "boolean",
            "display_name": "要求邮箱验证",
            "description": "新用户是否需要验证邮箱",
            "input_type": "switch",
            "default_value": "true",
            "required_role": "admin",
            "is_readonly": False,
            "sort_order": 3
        }
    ]

    async with AsyncSessionLocal() as session:
        for setting_data in settings_data:
            # 检查设置是否已存在
            result = await session.execute(
                select(SystemSettings).where(
                    SystemSettings.category == setting_data["category"],
                    SystemSettings.setting_key == setting_data["setting_key"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                setting = SystemSettings(**setting_data)
                session.add(setting)
                print(f"添加系统设置: {setting_data['category']}.{setting_data['setting_key']}")

        await session.commit()
        print("系统设置初始化完成")


async def init_security_policies():
    """初始化安全策略"""
    policies_data = [
        {
            "policy_name": "登录安全策略",
            "policy_type": "login_security",
            "config": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 30,
                "require_captcha_after_failures": 3,
                "track_ip_addresses": True,
                "suspicious_activity_threshold": 10
            },
            "description": "控制用户登录安全的策略，包括失败次数限制、账户锁定等",
            "applies_to_roles": ["admin", "teacher", "student"],
            "applies_to_organizations": [],
            "is_active": True,
            "is_system": True,
            "priority": 10
        },
        {
            "policy_name": "密码安全策略",
            "policy_type": "password_policy",
            "config": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True,
                "password_history_count": 5,
                "password_expiry_days": 90,
                "prevent_common_passwords": True
            },
            "description": "控制用户密码安全要求的策略",
            "applies_to_roles": ["admin", "teacher", "student"],
            "applies_to_organizations": [],
            "is_active": True,
            "is_system": True,
            "priority": 9
        },
        {
            "policy_name": "会话管理策略",
            "policy_type": "session_management",
            "config": {
                "max_concurrent_sessions": 3,
                "session_timeout_hours": 8,
                "idle_timeout_minutes": 30,
                "force_logout_on_password_change": True,
                "remember_me_duration_days": 30
            },
            "description": "管理用户会话的策略，包括超时、并发限制等",
            "applies_to_roles": ["admin", "teacher", "student"],
            "applies_to_organizations": [],
            "is_active": True,
            "is_system": True,
            "priority": 8
        },
        {
            "policy_name": "访问控制策略",
            "policy_type": "access_control",
            "config": {
                "ip_whitelist": [],
                "ip_blacklist": [],
                "country_restrictions": [],
                "time_based_access": {
                    "enabled": False,
                    "allowed_hours": {
                        "start": "08:00",
                        "end": "22:00"
                    },
                    "allowed_days": [1, 2, 3, 4, 5, 6, 7]
                },
                "device_restrictions": {
                    "max_devices_per_user": 5,
                    "require_device_approval": False
                }
            },
            "description": "控制用户访问权限的策略，包括IP限制、时间限制等",
            "applies_to_roles": ["admin", "teacher", "student"],
            "applies_to_organizations": [],
            "is_active": False,
            "is_system": True,
            "priority": 7
        }
    ]

    async with AsyncSessionLocal() as session:
        for policy_data in policies_data:
            # 检查策略是否已存在
            result = await session.execute(
                select(SecurityPolicy).where(
                    SecurityPolicy.policy_name == policy_data["policy_name"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                policy = SecurityPolicy(**policy_data, created_by="system")
                session.add(policy)
                print(f"添加安全策略: {policy_data['policy_name']}")

        await session.commit()
        print("安全策略初始化完成")


async def init_permissions():
    """初始化权限配置"""
    permissions_data = [
        # 用户管理权限
        {"permission_code": "user:create", "permission_name": "创建用户", "permission_category": "user", "permission_resource": "user", "permission_action": "create"},
        {"permission_code": "user:read", "permission_name": "查看用户", "permission_category": "user", "permission_resource": "user", "permission_action": "read"},
        {"permission_code": "user:update", "permission_name": "更新用户", "permission_category": "user", "permission_resource": "user", "permission_action": "update"},
        {"permission_code": "user:delete", "permission_name": "删除用户", "permission_category": "user", "permission_resource": "user", "permission_action": "delete"},

        # 系统管理权限
        {"permission_code": "system:settings", "permission_name": "系统设置", "permission_category": "system", "permission_resource": "system", "permission_action": "manage"},
        {"permission_code": "system:logs", "permission_name": "查看日志", "permission_category": "system", "permission_resource": "logs", "permission_action": "read"},
        {"permission_code": "system:audit", "permission_name": "审计管理", "permission_category": "system", "permission_resource": "audit", "permission_action": "manage"},

        # 配置管理权限
        {"permission_code": "CREATE_SETTING", "permission_name": "创建系统设置", "permission_category": "config", "permission_resource": "settings", "permission_action": "create"},
        {"permission_code": "UPDATE_SETTING", "permission_name": "更新系统设置", "permission_category": "config", "permission_resource": "settings", "permission_action": "update"},
        {"permission_code": "DELETE_SETTING", "permission_name": "删除系统设置", "permission_category": "config", "permission_resource": "settings", "permission_action": "delete"},
        {"permission_code": "CREATE_POLICY", "permission_name": "创建安全策略", "permission_category": "config", "permission_resource": "policies", "permission_action": "create"},
        {"permission_code": "UPDATE_POLICY", "permission_name": "更新安全策略", "permission_category": "config", "permission_resource": "policies", "permission_action": "update"},
        {"permission_code": "DELETE_POLICY", "permission_name": "删除安全策略", "permission_category": "config", "permission_resource": "policies", "permission_action": "delete"},
    ]

    async with AsyncSessionLocal() as session:
        for perm_data in permissions_data:
            # 检查权限是否已存在
            result = await session.execute(
                select(ConfigPermission).where(
                    ConfigPermission.permission_code == perm_data["permission_code"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                permission = ConfigPermission(**perm_data)
                session.add(permission)
                print(f"添加权限: {perm_data['permission_code']}")

        await session.commit()

        # 为管理员角色分配所有权限
        permissions = await session.execute(select(ConfigPermission))
        all_permissions = permissions.scalars().all()

        for permission in all_permissions:
            # 检查角色权限是否已存在
            result = await session.execute(
                select(ConfigRolePermission).where(
                    ConfigRolePermission.role_name == UserRole.ADMIN,
                    ConfigRolePermission.permission_id == permission.permission_id
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                role_permission = ConfigRolePermission(
                    role_name=UserRole.ADMIN,
                    permission_id=permission.permission_id,
                    is_granted=True
                )
                session.add(role_permission)

        await session.commit()
        print("权限配置初始化完成")


async def main():
    """主函数"""
    try:
        # 创建数据库表（如果不存在）
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("开始初始化配置数据...")

        # 初始化系统设置
        await init_system_settings()

        # 初始化安全策略
        await init_security_policies()

        # 初始化权限配置
        await init_permissions()

        print("配置数据初始化完成！")

    except Exception as e:
        print(f"初始化失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
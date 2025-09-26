"""
数据库更新脚本
为配置管理功能添加新的数据库表和初始数据
"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect

# 数据库连接配置
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": table_name}
        )
        return result.fetchone() is not None


async def create_system_settings_table():
    """创建或更新 system_settings 表"""
    table_name = "system_settings"

    if await check_table_exists(table_name):
        print(f"表 {table_name} 已存在，检查是否需要更新字段...")

        # 检查并添加新字段
        async with engine.begin() as conn:
            # 获取表结构
            result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]

            new_columns = [
                ("display_name", "VARCHAR(200) NOT NULL DEFAULT ''"),
                ("input_type", "VARCHAR(20) DEFAULT 'text'"),
                ("options", "TEXT"),  # JSON
                ("default_value", "TEXT"),
                ("sort_order", "INTEGER DEFAULT 0"),
                ("required_role", "VARCHAR(20) DEFAULT 'admin'"),
                ("is_readonly", "BOOLEAN DEFAULT 0"),
                ("is_active", "BOOLEAN DEFAULT 1")
            ]

            for column_name, column_def in new_columns:
                if column_name not in columns:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
                    print(f"  ✅ 添加字段: {column_name}")
    else:
        print(f"创建表 {table_name}...")
        async with engine.begin() as conn:
            create_sql = """
            CREATE TABLE system_settings (
                system_id VARCHAR(36) PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                setting_key VARCHAR(100) NOT NULL,
                setting_value TEXT,
                value_type VARCHAR(20) DEFAULT 'string',
                display_name VARCHAR(200) NOT NULL,
                description TEXT,
                is_public BOOLEAN DEFAULT 0,
                is_encrypted BOOLEAN DEFAULT 0,
                validation_rule TEXT,
                input_type VARCHAR(20) DEFAULT 'text',
                options TEXT,
                default_value TEXT,
                sort_order INTEGER DEFAULT 0,
                required_role VARCHAR(20) DEFAULT 'admin',
                is_readonly BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, setting_key)
            )
            """
            await conn.execute(text(create_sql))
            print(f"  ✅ 表 {table_name} 创建成功")


async def create_security_policies_table():
    """创建安全策略表"""
    table_name = "config_security_policies"

    if not await check_table_exists(table_name):
        print(f"创建表 {table_name}...")
        async with engine.begin() as conn:
            create_sql = """
            CREATE TABLE config_security_policies (
                policy_id VARCHAR(36) PRIMARY KEY,
                policy_name VARCHAR(100) NOT NULL,
                policy_type VARCHAR(50) NOT NULL,
                config TEXT NOT NULL,
                description TEXT,
                applies_to_roles TEXT DEFAULT '[]',
                applies_to_organizations TEXT DEFAULT '[]',
                is_active BOOLEAN DEFAULT 1,
                is_system BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 0,
                created_by VARCHAR(36),
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES config_users(user_id)
            )
            """
            await conn.execute(text(create_sql))
            print(f"  ✅ 表 {table_name} 创建成功")
    else:
        print(f"表 {table_name} 已存在")


async def create_notification_config_table():
    """创建通知配置表"""
    table_name = "config_notifications"

    if not await check_table_exists(table_name):
        print(f"创建表 {table_name}...")
        async with engine.begin() as conn:
            create_sql = """
            CREATE TABLE config_notifications (
                notification_id VARCHAR(36) PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                notification_title VARCHAR(200) NOT NULL,
                notification_content TEXT NOT NULL,
                notification_methods TEXT DEFAULT '[]',
                target_roles TEXT DEFAULT '[]',
                target_users TEXT DEFAULT '[]',
                trigger_conditions TEXT DEFAULT '{}',
                frequency_limit TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_system BOOLEAN DEFAULT 0,
                created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(text(create_sql))
            print(f"  ✅ 表 {table_name} 创建成功")
    else:
        print(f"表 {table_name} 已存在")


async def update_config_users_table():
    """更新用户表，添加安全相关字段"""
    table_name = "config_users"

    if await check_table_exists(table_name):
        print(f"更新表 {table_name}，添加安全字段...")

        async with engine.begin() as conn:
            # 获取表结构
            result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]

            new_columns = [
                ("user_failed_login_attempts", "INTEGER DEFAULT 0"),
                ("user_locked_until", "DATETIME"),
                ("user_last_password_change", "DATETIME"),
                ("user_password_reset_token", "VARCHAR(255)"),
                ("user_password_reset_expires", "DATETIME"),
                ("user_last_login_time", "DATETIME"),
                ("user_last_login_ip", "VARCHAR(45)"),
                ("user_last_login_device", "VARCHAR(200)"),
                ("user_active_sessions", "TEXT"),  # JSON
                ("user_max_sessions", "INTEGER DEFAULT 3"),
                ("user_login_count", "INTEGER DEFAULT 0"),
                ("user_last_activity", "DATETIME")
            ]

            for column_name, column_def in new_columns:
                if column_name not in columns:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
                    print(f"  ✅ 添加字段: {column_name}")
    else:
        print(f"⚠️ 表 {table_name} 不存在，请先运行基础初始化脚本")


async def update_log_login_table():
    """更新登录日志表"""
    table_name = "log_login"

    if await check_table_exists(table_name):
        print(f"更新表 {table_name}，添加新字段...")

        async with engine.begin() as conn:
            # 获取表结构
            result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]

            new_columns = [
                ("device_fingerprint", "VARCHAR(255)"),
                ("geolocation", "TEXT"),  # JSON
                ("risk_score", "REAL"),
                ("requires_2fa", "BOOLEAN DEFAULT 0"),
                ("two_fa_method", "VARCHAR(50)"),
                ("session_duration", "INTEGER")
            ]

            for column_name, column_def in new_columns:
                if column_name not in columns:
                    await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"))
                    print(f"  ✅ 添加字段: {column_name}")
    else:
        print(f"⚠️ 表 {table_name} 不存在，请先运行基础初始化脚本")


async def create_audit_log_table():
    """创建或更新审计日志表"""
    table_name = "log_audit"

    if not await check_table_exists(table_name):
        print(f"创建表 {table_name}...")
        async with engine.begin() as conn:
            create_sql = """
            CREATE TABLE log_audit (
                log_id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                action_type VARCHAR(50) NOT NULL,
                resource VARCHAR(100) NOT NULL,
                resource_id VARCHAR(36),
                description TEXT NOT NULL,
                request_method VARCHAR(10),
                request_url VARCHAR(500),
                ip_address VARCHAR(45),
                user_agent TEXT,
                status VARCHAR(20) NOT NULL,
                result TEXT,
                error_message TEXT,
                action_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            await conn.execute(text(create_sql))
            print(f"  ✅ 表 {table_name} 创建成功")
    else:
        print(f"表 {table_name} 已存在")


async def create_indexes():
    """创建索引以提高查询性能"""
    print("创建索引...")

    indexes = [
        # 系统设置索引
        "CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category)",
        "CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key)",
        "CREATE INDEX IF NOT EXISTS idx_system_settings_active ON system_settings(is_active)",

        # 安全策略索引
        "CREATE INDEX IF NOT EXISTS idx_security_policies_type ON config_security_policies(policy_type)",
        "CREATE INDEX IF NOT EXISTS idx_security_policies_active ON config_security_policies(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_security_policies_priority ON config_security_policies(priority)",

        # 登录日志索引
        "CREATE INDEX IF NOT EXISTS idx_login_log_user_id ON log_login(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_login_log_time ON log_login(logged_in_at)",
        "CREATE INDEX IF NOT EXISTS idx_login_log_success ON log_login(is_success)",
        "CREATE INDEX IF NOT EXISTS idx_login_log_ip ON log_login(ip_address)",

        # 审计日志索引
        "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON log_audit(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON log_audit(action_type)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_time ON log_audit(action_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON log_audit(resource)",

        # 用户表索引
        "CREATE INDEX IF NOT EXISTS idx_config_users_email ON config_users(user_email)",
        "CREATE INDEX IF NOT EXISTS idx_config_users_status ON config_users(user_status)",
        "CREATE INDEX IF NOT EXISTS idx_config_users_role ON config_users(user_role)",
        "CREATE INDEX IF NOT EXISTS idx_config_users_failed_attempts ON config_users(user_failed_login_attempts)",
        "CREATE INDEX IF NOT EXISTS idx_config_users_locked_until ON config_users(user_locked_until)"
    ]

    async with engine.begin() as conn:
        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
                print(f"  ✅ 索引创建成功: {index_sql.split(' ')[-1]}")
            except Exception as e:
                print(f"  ⚠️ 索引创建失败: {e}")


async def insert_default_data():
    """插入默认配置数据"""
    print("插入默认配置数据...")

    # 导入初始化数据脚本的函数
    try:
        from init_config_data import init_system_settings, init_security_policies, init_permissions

        # 初始化系统设置
        await init_system_settings()

        # 初始化安全策略
        await init_security_policies()

        # 初始化权限配置
        await init_permissions()

        print("  ✅ 默认数据插入成功")

    except Exception as e:
        print(f"  ⚠️ 默认数据插入失败: {e}")
        print("     请手动运行 init_config_data.py 脚本")


async def verify_update():
    """验证更新是否成功"""
    print("\n验证数据库更新...")

    tables_to_check = [
        "system_settings",
        "config_security_policies",
        "config_notifications",
        "log_audit",
        "config_users",
        "log_login"
    ]

    async with engine.begin() as conn:
        for table in tables_to_check:
            try:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} 条记录")
            except Exception as e:
                print(f"  ❌ {table}: 验证失败 - {e}")


async def main():
    """主函数"""
    print("🚀 开始更新数据库以支持配置管理功能...")
    print("=" * 60)

    try:
        # 1. 创建/更新系统设置表
        await create_system_settings_table()

        # 2. 创建安全策略表
        await create_security_policies_table()

        # 3. 创建通知配置表
        await create_notification_config_table()

        # 4. 更新用户表
        await update_config_users_table()

        # 5. 更新登录日志表
        await update_log_login_table()

        # 6. 创建审计日志表
        await create_audit_log_table()

        # 7. 创建索引
        await create_indexes()

        # 8. 插入默认数据
        await insert_default_data()

        # 9. 验证更新
        await verify_update()

        print("\n" + "=" * 60)
        print("✅ 数据库更新完成！")
        print("\n📋 更新摘要:")
        print("   🗃️ 系统设置表 - 创建/更新")
        print("   🔒 安全策略表 - 创建")
        print("   📢 通知配置表 - 创建")
        print("   👥 用户表 - 添加安全字段")
        print("   📝 登录日志表 - 添加字段")
        print("   📊 审计日志表 - 创建")
        print("   🔍 数据库索引 - 创建")
        print("   📦 默认数据 - 插入")

        print("\n💡 下一步:")
        print("   1. 重启应用服务器")
        print("   2. 访问管理员配置界面")
        print("   3. 运行测试脚本验证功能")

    except Exception as e:
        print(f"\n❌ 数据库更新失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
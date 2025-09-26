#!/usr/bin/env python3
"""
TeachAid服务器启动脚本
包含数据库初始化、服务健康检查等功能
"""

import asyncio
import sys
import time
from pathlib import Path

import uvicorn
from loguru import logger

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import engine
from app.core.redis_client import init_redis, close_redis


async def check_dependencies():
    """检查依赖服务状态"""
    logger.info("🔍 检查系统依赖...")

    # 检查数据库连接
    try:
        # 简单测试数据库连接
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.success("✅ 数据库连接正常")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

    # 检查Redis连接
    try:
        await init_redis()
        logger.success("✅ Redis连接正常")
    except Exception as e:
        logger.warning(f"⚠️ Redis连接失败，将使用内存缓存: {e}")

    return True


async def initialize_database():
    """初始化数据库"""
    try:
        from app.core.db_init import create_database_tables, create_seed_data

        logger.info("🗄️ 初始化数据库...")
        await create_database_tables()
        logger.success("✅ 数据库表创建完成")

        logger.info("🌱 创建种子数据...")
        await create_seed_data()
        logger.success("✅ 种子数据创建完成")

        return True

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False


async def setup_application():
    """应用程序设置"""
    logger.info("⚙️ 设置应用程序...")

    # 检查依赖
    if not await check_dependencies():
        logger.error("❌ 依赖检查失败")
        return False

    # 初始化数据库（可选）
    if "--init-db" in sys.argv:
        if not await initialize_database():
            logger.error("❌ 数据库初始化失败")
            return False

    logger.success("✅ 应用程序设置完成")
    return True


def create_app():
    """创建FastAPI应用"""
    from app.main import app
    return app


def start_development_server():
    """启动开发服务器"""
    logger.info("🚀 启动TeachAid开发服务器...")
    logger.info(f"📍 服务地址: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API文档: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔧 调试模式: {settings.debug}")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_dirs=["app"] if settings.debug else None,
        log_level="info",
        access_log=True,
        use_colors=True,
    )


def start_production_server():
    """启动生产服务器"""
    logger.info("🏭 启动TeachAid生产服务器...")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        workers=4,  # 根据CPU核心数调整
        log_level="info",
        access_log=True,
        use_colors=False,
    )


async def health_check():
    """健康检查"""
    try:
        # 检查数据库
        await test_connection()

        # 检查Redis
        from app.core.redis_client import redis_client
        if redis_client.connected:
            await redis_client.ping()

        logger.success("✅ 系统健康检查通过")
        return True

    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return False


def show_help():
    """显示帮助信息"""
    help_text = """
TeachAid平台启动脚本

用法:
    python start_server.py [选项]

选项:
    --dev           启动开发服务器（默认）
    --prod          启动生产服务器
    --init-db       初始化数据库和种子数据
    --health        执行健康检查
    --help          显示此帮助信息

示例:
    python start_server.py --dev --init-db    # 开发模式并初始化数据库
    python start_server.py --prod             # 生产模式
    python start_server.py --health           # 健康检查
"""
    print(help_text)


async def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    )

    # 解析命令行参数
    if "--help" in sys.argv:
        show_help()
        return

    if "--health" in sys.argv:
        logger.info("🏥 执行系统健康检查...")
        success = await health_check()
        sys.exit(0 if success else 1)

    # 应用程序设置
    if not await setup_application():
        sys.exit(1)

    # 启动服务器
    try:
        if "--prod" in sys.argv:
            start_production_server()
        else:
            start_development_server()

    except KeyboardInterrupt:
        logger.info("👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
    finally:
        # 清理资源
        try:
            await close_redis()
            if engine:
                await engine.dispose()
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 程序被用户中断")
    except Exception as e:
        logger.error(f"❌ 程序执行异常: {e}")
        sys.exit(1)
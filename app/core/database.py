"""
数据库连接和会话管理
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine.url import make_url

from app.core.config import settings


# 创建异步数据库引擎（仅在内存 SQLite 使用 StaticPool）
_engine_kwargs = {"echo": settings.database.echo, "pool_pre_ping": True, "pool_recycle": 1800}
try:
    _url = make_url(settings.database.url)
    if _url.get_backend_name().startswith("sqlite") and ("memory" in str(_url.database)):
        _engine_kwargs["poolclass"] = StaticPool
except Exception:
    # 忽略URL解析异常，使用默认参数
    pass

engine = create_async_engine(settings.database.url, **_engine_kwargs)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 数据库Base：所有模型需要使用同一个Base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：提供异步数据库会话（自动提交/回滚）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """初始化数据库表和种子数据"""
    from app.core.db_init import (
        full_database_init,
        create_default_grades,
        create_default_subjects,
    )

    await full_database_init()

    # 确保基础教务维度存在（兼容首次运行场景）
    async with AsyncSessionLocal() as session:
        try:
            await session.begin()
            await create_default_grades(session)
            await create_default_subjects(session)
            await session.commit()
        except Exception:
            await session.rollback()
            # 初始化失败不阻断应用启动


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()

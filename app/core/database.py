"""
数据库连接和会话管理
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import settings


# 创建异步数据库引擎
engine = create_async_engine(
    settings.database.url,
    echo=settings.database.echo,
    poolclass=StaticPool,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 数据库基类 注意：需要保证所有模型使用相同的Base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        # 导入所有数据模型
        from app.models.database_models import (
            Class, Question, PromptTemplate,
            Homework, StudentHomework, ChatSession, ChatMessage, FileUpload
        )
        
        # 导入认证系统数据模型
        from app.models.auth_models import (
            ConfigUser, ConfigOrganization, LogLogin,
            ConfigPermission, ConfigRolePermission, SystemSettings, LogAudit
        )
        
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
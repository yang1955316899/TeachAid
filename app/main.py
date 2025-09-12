"""
FastAPI主应用入口
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api import auth, questions
from app.models.pydantic_models import BaseResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("TeachAid应用启动中...")
    
    try:
        # 初始化数据库
        await init_db()
        logger.info("数据库初始化成功")
        
        # 其他初始化操作
        # await init_redis()
        # await init_ai_models()
        
        logger.info("TeachAid应用启动完成")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("TeachAid应用关闭中...")
    
    try:
        await close_db()
        logger.info("数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"应用关闭时出错: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## TeachAid AI辅助教学平台

    ### 核心功能
    - 🤖 **多模态AI理解**：智能解析题目图片、PDF等多种格式
    - ✨ **智能答案改写**：将标准答案转换为引导式教学内容  
    - 💬 **智能学习对话**：为学生提供个性化AI答疑和学习引导
    - 📚 **作业管理系统**：创建、分发和跟踪学生作业完成情况
    - 🎯 **学习分析报告**：生成详细的学习进度和薄弱点分析

    ### 技术特色
    - **统一多模型接口**：LiteLLM整合100+大语言模型
    - **智能工作流编排**：LangGraph处理复杂教学流程
    - **智能缓存优化**：显著降低AI调用成本
    - **企业级权限管理**：支持多角色、多机构的细粒度权限控制

    ### API版本
    当前版本：v1.0.0
    """,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.teachaid.com"]
)


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "服务器内部错误，请稍后重试",
            "error_code": 500
        }
    )


# 注册路由
app.include_router(auth.router, prefix="/api")
app.include_router(questions.router, prefix="/api")


# 根路径
@app.get("/", response_model=BaseResponse, summary="系统信息")
async def root():
    """
    获取系统基本信息
    """
    return BaseResponse(
        success=True,
        message="TeachAid AI辅助教学平台运行正常",
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs_url": "/docs" if settings.debug else None
        }
    )


# 健康检查
@app.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查接口
    """
    try:
        # 可以添加数据库、Redis等健康检查
        # db_status = await check_database_health()
        # redis_status = await check_redis_health()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "ai_models": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# 运行应用
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
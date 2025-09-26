"""
FastAPI主应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis_client import init_redis, close_redis
# from app.core.security import security_middleware  # 临时屏蔽
from app.core.error_handler import error_handler
from app.api import auth, questions, chat, public, classes, homework, prompts, files, rewriter, analytics, profile, taxonomy, teaching, notes, admin, intelligent_tutor, admin_config
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
        
        # 初始化Redis
        await init_redis()
        logger.info("Redis初始化成功")
        
        # 其他初始化操作
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
        
        await close_redis()
        logger.info("Redis连接已关闭")
        
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
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:50001", 
        "http://127.0.0.1:50001",
        "http://localhost:50005", 
        "http://127.0.0.1:50005",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

@app.middleware("http")
async def options_middleware(request: Request, call_next):
    """处理OPTIONS预检请求"""
    if request.method == "OPTIONS":
        return JSONResponse(
            content={"success": True},
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",
            }
        )
    
    response = await call_next(request)
    return response

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.teachaid.com"]
)

# 临时屏蔽安全中间件
# @app.middleware("http")
# async def security_middleware_handler(request: Request, call_next):
#     """安全中间件"""
#     try:
#         # 安全检查
#         security_info = await security_middleware.check_request_security(request)

#         # 处理请求
#         response = await call_next(request)

#         # 添加安全响应头
#         security_headers = security_middleware.get_security_headers()
#         for header, value in security_headers.items():
#             response.headers[header] = value

#         # 添加安全评分头（仅在调试模式）
#         if settings.debug:
#             response.headers['X-Security-Score'] = str(security_info['security_score'])

#         return response

#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"安全中间件错误: {e}")
#         return JSONResponse(
#             status_code=500,
#             content={"success": False, "message": "服务器内部错误"}
#         )


@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    """错误日志中间件"""
    import time
    import uuid

    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    try:
        response = await call_next(request)

        # 记录响应时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # 记录慢请求
        if process_time > 2.0:  # 超过2秒的请求
            logger.warning(
                f"慢请求 - ID: {request_id}, URL: {request.url}, "
                f"方法: {request.method}, 耗时: {process_time:.2f}s"
            )

        return response

    except Exception as e:
        # 记录错误请求
        process_time = time.time() - start_time
        logger.error(
            f"请求错误 - ID: {request_id}, URL: {request.url}, "
            f"方法: {request.method}, 错误: {str(e)}, 耗时: {process_time:.2f}s"
        )
        raise


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return await error_handler.handle_exception(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    return await error_handler.handle_exception(request, exc)


# 注册路由 - 按功能模块分组，统一使用/api前缀

# 基础认证模块
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(public.router, prefix="/api")

# 核心业务模块
app.include_router(questions.router, prefix="/api")
app.include_router(homework.router, prefix="/api")
app.include_router(homework.router_student, prefix="/api")  # 学生作业视图
app.include_router(classes.router, prefix="/api")
app.include_router(notes.router, prefix="/api")

# AI功能模块
app.include_router(chat.router, prefix="/api")
app.include_router(intelligent_tutor.router, prefix="/api")
app.include_router(rewriter.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")

# 数据分析模块
app.include_router(analytics.router, prefix="/api")

# 管理配置模块
app.include_router(teaching.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")
app.include_router(files.router, prefix="/api")

# 管理员模块
app.include_router(admin.router, prefix="/api")
app.include_router(admin_config.router, prefix="/api")


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

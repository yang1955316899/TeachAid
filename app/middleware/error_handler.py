"""
统一错误处理中间件
"""
import traceback
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.models.pydantic_models import BaseResponse


class ErrorHandlerMiddleware:
    """统一错误处理中间件"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            response = await self.handle_error(request, exc)
            await response(scope, receive, send)

    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """处理各种类型的异常"""

        # HTTP异常
        if isinstance(exc, HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content=BaseResponse(
                    success=False,
                    message=exc.detail,
                    error_code=f"HTTP_{exc.status_code}"
                ).dict()
            )

        # 数据库相关异常
        elif isinstance(exc, IntegrityError):
            logger.error(f"数据库完整性错误: {exc}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=BaseResponse(
                    success=False,
                    message="数据完整性约束失败，请检查输入数据",
                    error_code="DB_INTEGRITY_ERROR"
                ).dict()
            )

        elif isinstance(exc, SQLAlchemyError):
            logger.error(f"数据库操作异常: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=BaseResponse(
                    success=False,
                    message="数据库操作失败，请稍后重试",
                    error_code="DB_ERROR"
                ).dict()
            )

        # 数据验证异常
        elif isinstance(exc, ValidationError):
            logger.warning(f"数据验证错误: {exc}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=BaseResponse(
                    success=False,
                    message=f"数据验证失败: {str(exc)}",
                    error_code="VALIDATION_ERROR"
                ).dict()
            )

        # 其他未捕获的异常
        else:
            logger.error(f"未处理的异常: {type(exc).__name__}: {exc}")
            logger.error(f"请求路径: {request.url}")
            logger.error(f"异常堆栈: {traceback.format_exc()}")

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=BaseResponse(
                    success=False,
                    message="服务器内部错误，请稍后重试",
                    error_code="INTERNAL_ERROR"
                ).dict()
            )


def setup_error_handlers(app):
    """设置全局异常处理器"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器"""
        logger.warning(f"HTTP异常 {exc.status_code}: {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseResponse(
                success=False,
                message=exc.detail,
                error_code=f"HTTP_{exc.status_code}"
            ).dict()
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """数据验证异常处理器"""
        logger.warning(f"数据验证错误: {exc} - {request.url}")

        # 提取更友好的错误信息
        error_messages = []
        for error in exc.errors():
            field = " -> ".join([str(loc) for loc in error["loc"]])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=BaseResponse(
                success=False,
                message=f"数据验证失败: {'; '.join(error_messages)}",
                error_code="VALIDATION_ERROR",
                data={"validation_errors": exc.errors()}
            ).dict()
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """数据库异常处理器"""
        if isinstance(exc, IntegrityError):
            logger.warning(f"数据库完整性错误: {exc} - {request.url}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=BaseResponse(
                    success=False,
                    message="数据完整性约束失败，请检查输入数据",
                    error_code="DB_INTEGRITY_ERROR"
                ).dict()
            )
        else:
            logger.error(f"数据库操作异常: {exc} - {request.url}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=BaseResponse(
                    success=False,
                    message="数据库操作失败，请稍后重试",
                    error_code="DB_ERROR"
                ).dict()
            )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理器"""
        logger.error(f"未处理的异常: {type(exc).__name__}: {exc}")
        logger.error(f"请求路径: {request.url}")
        logger.error(f"异常堆栈: {traceback.format_exc()}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=BaseResponse(
                success=False,
                message="服务器内部错误，请稍后重试",
                error_code="INTERNAL_ERROR"
            ).dict()
        )

    logger.info("全局异常处理器设置完成")
"""
错误处理和用户体验工具
"""
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class ErrorCode:
    """错误代码定义"""
    # 认证相关错误 (1000-1999)
    AUTH_INVALID_CREDENTIALS = 1001
    AUTH_TOKEN_EXPIRED = 1002
    AUTH_TOKEN_INVALID = 1003
    AUTH_PERMISSION_DENIED = 1004
    AUTH_USER_NOT_FOUND = 1005
    AUTH_USER_DISABLED = 1006
    AUTH_PASSWORD_INVALID = 1007
    AUTH_EMAIL_EXISTS = 1008
    AUTH_USERNAME_EXISTS = 1009
    
    # 验证相关错误 (2000-2999)
    VALIDATION_REQUIRED_FIELD = 2001
    VALIDATION_INVALID_FORMAT = 2002
    VALIDATION_INVALID_LENGTH = 2003
    VALIDATION_INVALID_RANGE = 2004
    VALIDATION_FILE_TYPE = 2005
    VALIDATION_FILE_SIZE = 2006
    
    # 业务逻辑错误 (3000-3999)
    BUSINESS_NOT_FOUND = 3001
    BUSINESS_ALREADY_EXISTS = 3002
    BUSINESS_INVALID_STATE = 3003
    BUSINESS_QUOTA_EXCEEDED = 3004
    BUSINESS_OPERATION_FAILED = 3005
    
    # 系统错误 (4000-4999)
    SYSTEM_INTERNAL_ERROR = 4001
    SYSTEM_DATABASE_ERROR = 4002
    SYSTEM_NETWORK_ERROR = 4003
    SYSTEM_EXTERNAL_SERVICE_ERROR = 4004
    
    # 安全错误 (5000-5999)
    SECURITY_RATE_LIMITED = 5001
    SECURITY_SUSPICIOUS_REQUEST = 5002
    SECURITY_IP_BLOCKED = 5003
    SECURITY_CSRF_FAILED = 5004


class ErrorDetails:
    """错误详情"""
    
    def __init__(self, code: int, message: str, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class ErrorResponse:
    """统一错误响应格式"""
    
    @staticmethod
    def create(
        error: ErrorDetails,
        status_code: int = 400,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """创建错误响应"""
        response_data = {
            'success': False,
            'error': error.to_dict()
        }
        
        if request_id:
            response_data['request_id'] = request_id
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def from_exception(
        exception: Exception,
        request_id: Optional[str] = None
    ) -> JSONResponse:
        """从异常创建错误响应"""
        if isinstance(exception, HTTPException):
            error_details = ErrorDetails(
                code=exception.status_code,
                message=exception.detail
            )
            return ErrorResponse.create(
                error_details,
                status_code=exception.status_code,
                request_id=request_id
            )
        
        # 处理其他异常
        error_details = ErrorDetails(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message=str(exception) or "服务器内部错误"
        )
        
        return ErrorResponse.create(
            error_details,
            status_code=500,
            request_id=request_id
        )


class UserExperienceHandler:
    """用户体验处理器"""
    
    def __init__(self):
        self.error_messages = {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "用户名或密码错误，请重新输入",
            ErrorCode.AUTH_TOKEN_EXPIRED: "登录已过期，请重新登录",
            ErrorCode.AUTH_TOKEN_INVALID: "登录信息无效，请重新登录",
            ErrorCode.AUTH_PERMISSION_DENIED: "您没有权限执行此操作",
            ErrorCode.AUTH_USER_NOT_FOUND: "用户不存在",
            ErrorCode.AUTH_USER_DISABLED: "账户已被禁用，请联系管理员",
            ErrorCode.AUTH_PASSWORD_INVALID: "密码格式不正确",
            ErrorCode.AUTH_EMAIL_EXISTS: "邮箱已被注册",
            ErrorCode.AUTH_USERNAME_EXISTS: "用户名已被使用",
            
            ErrorCode.VALIDATION_REQUIRED_FIELD: "请填写所有必填字段",
            ErrorCode.VALIDATION_INVALID_FORMAT: "格式不正确",
            ErrorCode.VALIDATION_INVALID_LENGTH: "长度不符合要求",
            ErrorCode.VALIDATION_INVALID_RANGE: "数值超出范围",
            ErrorCode.VALIDATION_FILE_TYPE: "文件类型不支持",
            ErrorCode.VALIDATION_FILE_SIZE: "文件大小超出限制",
            
            ErrorCode.BUSINESS_NOT_FOUND: "资源不存在",
            ErrorCode.BUSINESS_ALREADY_EXISTS: "资源已存在",
            ErrorCode.BUSINESS_INVALID_STATE: "当前状态不允许此操作",
            ErrorCode.BUSINESS_QUOTA_EXCEEDED: "配额已用完",
            ErrorCode.BUSINESS_OPERATION_FAILED: "操作失败，请重试",
            
            ErrorCode.SYSTEM_INTERNAL_ERROR: "系统繁忙，请稍后重试",
            ErrorCode.SYSTEM_DATABASE_ERROR: "数据库连接失败",
            ErrorCode.SYSTEM_NETWORK_ERROR: "网络连接失败",
            ErrorCode.SYSTEM_EXTERNAL_SERVICE_ERROR: "外部服务暂时不可用",
            
            ErrorCode.SECURITY_RATE_LIMITED: "请求过于频繁，请稍后重试",
            ErrorCode.SECURITY_SUSPICIOUS_REQUEST: "请求被系统拦截",
            ErrorCode.SECURITY_IP_BLOCKED: "IP地址被临时封禁",
            ErrorCode.SECURITY_CSRF_FAILED: "安全验证失败",
        }
        
        self.suggestions = {
            ErrorCode.AUTH_INVALID_CREDENTIALS: "检查用户名和密码是否正确",
            ErrorCode.AUTH_TOKEN_EXPIRED: "请重新登录系统",
            ErrorCode.AUTH_PERMISSION_DENIED: "联系管理员申请相应权限",
            ErrorCode.VALIDATION_REQUIRED_FIELD: "请检查表单中标记为必填的字段",
            ErrorCode.VALIDATION_INVALID_FORMAT: "请按照正确格式填写",
            ErrorCode.BUSINESS_QUOTA_EXCEEDED: "升级账户或等待配额重置",
            ErrorCode.SYSTEM_INTERNAL_ERROR: "稍后重试或联系技术支持",
            ErrorCode.SECURITY_RATE_LIMITED: "等待1分钟后再试",
        }
    
    def get_user_message(self, error_code: int) -> str:
        """获取用户友好的错误消息"""
        return self.error_messages.get(error_code, "操作失败，请重试")
    
    def get_suggestion(self, error_code: int) -> Optional[str]:
        """获取错误解决建议"""
        return self.suggestions.get(error_code)
    
    def format_error_response(self, error_code: int, details: Optional[Dict] = None) -> Dict[str, Any]:
        """格式化用户友好的错误响应"""
        user_message = self.get_user_message(error_code)
        suggestion = self.get_suggestion(error_code)
        
        response = {
            'success': False,
            'message': user_message,
            'code': error_code,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if suggestion:
            response['suggestion'] = suggestion
        
        if details:
            response['details'] = details
        
        return response


class ErrorHandler:
    """全局错误处理器"""
    
    def __init__(self):
        self.ux_handler = UserExperienceHandler()
        self.error_count = {}
        self.error_threshold = 10  # 10次错误后报警
    
    async def handle_exception(
        self, 
        request: Request, 
        exception: Exception
    ) -> JSONResponse:
        """处理异常"""
        request_id = self.get_request_id(request)
        
        # 记录错误
        await self.log_error(request, exception, request_id)
        
        # 统计错误频率
        self.track_error(exception)
        
        # 创建错误响应
        if isinstance(exception, HTTPException):
            return self.handle_http_exception(exception, request_id)
        
        return self.handle_generic_exception(exception, request_id)
    
    def get_request_id(self, request: Request) -> str:
        """获取请求ID"""
        return request.headers.get('X-Request-ID', 'unknown')
    
    async def log_error(
        self, 
        request: Request, 
        exception: Exception, 
        request_id: str
    ) -> None:
        """记录错误日志"""
        try:
            error_info = {
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'client_ip': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', ''),
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'timestamp': datetime.utcnow().isoformat(),
                'traceback': traceback.format_exc()
            }
            
            logger.error(f"错误发生: {error_info}")
            
        except Exception as log_error:
            logger.error(f"记录错误日志失败: {log_error}")
    
    def track_error(self, exception: Exception) -> None:
        """统计错误频率"""
        error_key = type(exception).__name__
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        # 检查是否需要报警
        if self.error_count[error_key] >= self.error_threshold:
            logger.warning(f"错误频率过高: {error_key} 发生了 {self.error_count[error_key]} 次")
            # 这里可以添加报警逻辑
    
    def handle_http_exception(
        self, 
        exception: HTTPException, 
        request_id: str
    ) -> JSONResponse:
        """处理HTTP异常"""
        error_details = ErrorDetails(
            code=exception.status_code,
            message=exception.detail
        )
        
        return ErrorResponse.create(
            error_details,
            status_code=exception.status_code,
            request_id=request_id
        )
    
    def handle_generic_exception(
        self, 
        exception: Exception, 
        request_id: str
    ) -> JSONResponse:
        """处理通用异常"""
        error_details = ErrorDetails(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message="服务器内部错误"
        )
        
        return ErrorResponse.create(
            error_details,
            status_code=500,
            request_id=request_id
        )


# 全局错误处理器实例
error_handler = ErrorHandler()
ux_handler = UserExperienceHandler()


def create_error_response(
    error_code: int, 
    details: Optional[Dict] = None,
    status_code: int = 400
) -> JSONResponse:
    """创建标准错误响应"""
    error_details = ErrorDetails(
        code=error_code,
        message=ux_handler.get_user_message(error_code),
        details=details
    )
    
    return ErrorResponse.create(error_details, status_code)


def raise_http_error(
    error_code: int, 
    details: Optional[Dict] = None,
    status_code: int = 400
) -> HTTPException:
    """抛出HTTP异常"""
    message = ux_handler.get_user_message(error_code)
    raise HTTPException(
        status_code=status_code,
        detail=message
    )
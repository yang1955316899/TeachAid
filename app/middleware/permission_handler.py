"""
权限验证中间件和装饰器
"""
from functools import wraps
from typing import List, Optional, Callable, Any
from datetime import datetime
from fastapi import HTTPException, status, Depends
from loguru import logger

from app.models.auth_models import ConfigUser, UserRole
from app.services.auth_service import get_current_user


class PermissionRequired:
    """权限验证装饰器"""

    def __init__(
        self,
        roles: Optional[List[UserRole]] = None,
        permissions: Optional[List[str]] = None,
        resource_check: Optional[Callable] = None,
        allow_self: bool = False
    ):
        """
        初始化权限验证装饰器

        Args:
            roles: 允许的用户角色列表
            permissions: 需要的权限代码列表
            resource_check: 资源级权限检查函数
            allow_self: 是否允许访问自己的资源
        """
        self.roles = roles or []
        self.permissions = permissions or []
        self.resource_check = resource_check
        self.allow_self = allow_self

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从依赖注入中获取当前用户
            current_user = None
            for arg in args:
                if isinstance(arg, ConfigUser):
                    current_user = arg
                    break

            if not current_user:
                # 如果没有找到，尝试从kwargs中获取
                current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户未认证"
                )

            # 验证用户角色
            if self.roles and current_user.user_role not in self.roles:
                logger.warning(
                    f"用户 {current_user.user_id} 权限不足，需要角色: {self.roles}，"
                    f"当前角色: {current_user.user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join([role.value for role in self.roles])}"
                )

            # 验证具体权限（如果有权限系统）
            if self.permissions:
                # TODO: 实现具体的权限验证逻辑
                pass

            # 资源级权限检查
            if self.resource_check:
                resource_allowed = await self.resource_check(current_user, *args, **kwargs)
                if not resource_allowed:
                    logger.warning(
                        f"用户 {current_user.user_id} 尝试访问无权限的资源"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权访问该资源"
                    )

            return await func(*args, **kwargs)

        return wrapper


def require_roles(*roles: UserRole):
    """要求特定角色的装饰器"""
    return PermissionRequired(roles=list(roles))


def require_teacher_or_admin():
    """要求教师或管理员权限"""
    return PermissionRequired(roles=[UserRole.TEACHER, UserRole.ADMIN])


def require_admin():
    """要求管理员权限"""
    return PermissionRequired(roles=[UserRole.ADMIN])


def require_student():
    """要求学生权限"""
    return PermissionRequired(roles=[UserRole.STUDENT, UserRole.ADMIN])


class ResourceOwnershipCheck:
    """资源所有权检查"""

    @staticmethod
    async def check_question_ownership(user: ConfigUser, question_id: str, **kwargs) -> bool:
        """检查题目所有权"""
        # 管理员可以访问所有资源
        if user.user_role == UserRole.ADMIN:
            return True

        # TODO: 实现具体的题目所有权检查逻辑
        # 这里需要查询数据库验证用户是否是题目的创建者
        return True

    @staticmethod
    async def check_homework_access(user: ConfigUser, homework_id: str, **kwargs) -> bool:
        """检查作业访问权限"""
        # 管理员可以访问所有资源
        if user.user_role == UserRole.ADMIN:
            return True

        # 教师可以访问自己创建的作业
        if user.user_role == UserRole.TEACHER:
            # TODO: 检查是否是作业创建者
            return True

        # 学生只能访问分配给自己的作业
        if user.user_role == UserRole.STUDENT:
            # TODO: 检查学生是否被分配了该作业
            return True

        return False

    @staticmethod
    async def check_class_access(user: ConfigUser, class_id: str, **kwargs) -> bool:
        """检查班级访问权限"""
        # 管理员可以访问所有资源
        if user.user_role == UserRole.ADMIN:
            return True

        # 教师可以访问自己教授的班级
        if user.user_role == UserRole.TEACHER:
            # TODO: 检查教师是否教授该班级
            return True

        # 学生只能访问自己所在的班级
        if user.user_role == UserRole.STUDENT:
            # TODO: 检查学生是否在该班级
            return True

        return False


def check_resource_ownership(check_func: Callable):
    """资源所有权检查装饰器"""
    return PermissionRequired(resource_check=check_func)


# 常用的权限检查装饰器
question_ownership_required = check_resource_ownership(
    ResourceOwnershipCheck.check_question_ownership
)

homework_access_required = check_resource_ownership(
    ResourceOwnershipCheck.check_homework_access
)

class_access_required = check_resource_ownership(
    ResourceOwnershipCheck.check_class_access
)


class PermissionLevel:
    """权限级别常量"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


def log_permission_check(user_id: str, resource: str, action: str, result: bool):
    """记录权限检查日志"""
    if result:
        logger.info(f"权限验证通过: 用户 {user_id} 对资源 {resource} 执行 {action}")
    else:
        logger.warning(f"权限验证失败: 用户 {user_id} 尝试对资源 {resource} 执行 {action}")


def rate_limit_check(user: ConfigUser, action: str) -> bool:
    """速率限制检查"""
    # TODO: 实现基于Redis的速率限制
    # 例如：限制用户每分钟只能创建10个题目
    return True


def security_audit_log(user: ConfigUser, action: str, resource: str, details: dict = None):
    """安全审计日志"""
    audit_data = {
        "user_id": user.user_id,
        "user_role": user.user_role.value,
        "action": action,
        "resource": resource,
        "timestamp": str(datetime.utcnow()),
        "ip_address": getattr(user, "last_login_ip", "unknown"),
        "details": details or {}
    }

    logger.info(f"安全审计: {audit_data}")
    # TODO: 写入审计日志数据库表
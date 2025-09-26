"""
中间件模块
"""
from .error_handler import ErrorHandlerMiddleware, setup_error_handlers
from .permission_handler import (
    PermissionRequired,
    require_roles,
    require_teacher_or_admin,
    require_admin,
    require_student,
    ResourceOwnershipCheck,
    check_resource_ownership,
    question_ownership_required,
    homework_access_required,
    class_access_required,
    PermissionLevel,
    log_permission_check,
    rate_limit_check,
    security_audit_log
)

__all__ = [
    "ErrorHandlerMiddleware",
    "setup_error_handlers",
    "PermissionRequired",
    "require_roles",
    "require_teacher_or_admin",
    "require_admin",
    "require_student",
    "ResourceOwnershipCheck",
    "check_resource_ownership",
    "question_ownership_required",
    "homework_access_required",
    "class_access_required",
    "PermissionLevel",
    "log_permission_check",
    "rate_limit_check",
    "security_audit_log"
]
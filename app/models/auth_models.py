"""
认证系统数据库模型定义
使用config_前缀，标准字段命名规范
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, DateTime, JSON, Text, Boolean, Integer,
    ForeignKey, Float, func, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid4())


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"


# =============================================================================
# 配置相关表（config_前缀）
# =============================================================================

class ConfigUser(Base):
    """用户配置表 - 统一的用户管理"""
    __tablename__ = "config_users"
    
    user_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    user_name: Mapped[str] = Column(String(50), unique=True, nullable=False, comment="用户名")
    user_email: Mapped[str] = Column(String(255), unique=True, nullable=False, comment="邮箱")
    user_password_hash: Mapped[str] = Column(String(255), nullable=False, comment="密码哈希")
    user_password_salt: Mapped[Optional[str]] = Column(String(32), comment="密码盐值")
    user_full_name: Mapped[Optional[str]] = Column(String(100), comment="真实姓名")
    
    # 角色和状态
    user_role: Mapped[UserRole] = Column(SQLEnum(UserRole), default=UserRole.STUDENT, comment="用户角色")
    user_status: Mapped[UserStatus] = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, comment="用户状态")
    
    # 机构关联
    organization_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_organizations.organization_id"), comment="所属机构ID")
    
    # 认证相关
    user_is_verified: Mapped[bool] = Column(Boolean, default=False, comment="邮箱是否已验证")
    user_verification_token: Mapped[Optional[str]] = Column(String(255), comment="验证令牌")
    user_verification_expires: Mapped[Optional[datetime]] = Column(DateTime, comment="验证令牌过期时间")
    
    # 安全相关
    user_failed_login_attempts: Mapped[int] = Column(Integer, default=0, comment="失败登录次数")
    user_locked_until: Mapped[Optional[datetime]] = Column(DateTime, comment="锁定到期时间")
    user_last_password_change: Mapped[Optional[datetime]] = Column(DateTime, comment="上次密码修改时间")
    user_password_reset_token: Mapped[Optional[str]] = Column(String(255), comment="密码重置令牌")
    user_password_reset_expires: Mapped[Optional[datetime]] = Column(DateTime, comment="密码重置令牌过期时间")
    
    # 登录追踪
    user_last_login_time: Mapped[Optional[datetime]] = Column(DateTime, comment="最后登录时间")
    user_last_login_ip: Mapped[Optional[str]] = Column(String(45), comment="最后登录IP")
    user_last_login_device: Mapped[Optional[str]] = Column(String(200), comment="最后登录设备信息")
    
    # 会话管理
    user_active_sessions: Mapped[Optional[dict]] = Column(JSON, comment="活跃会话列表")
    user_max_sessions: Mapped[int] = Column(Integer, default=3, comment="最大并发会话数")
    
    # 个人设置
    user_settings: Mapped[Optional[dict]] = Column(JSON, comment="用户个人设置")
    user_preferences: Mapped[Optional[dict]] = Column(JSON, comment="用户偏好配置")
    
    # 统计信息
    user_login_count: Mapped[int] = Column(Integer, default=0, comment="总登录次数")
    user_last_activity: Mapped[Optional[datetime]] = Column(DateTime, comment="最后活跃时间")
    
    # 时间字段 - 保持与API兼容
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_time: Mapped[Optional[datetime]] = Column(DateTime, comment="软删除时间")
    
    # 关系
    organization = relationship("ConfigOrganization", back_populates="users")
    login_logs = relationship("LogLogin", back_populates="user")

    # 业务关联关系暂时注释掉，避免循环导入
    created_questions = relationship("Question", back_populates="creator")
    student_homeworks = relationship("StudentHomework", back_populates="student")
    chat_sessions = relationship("ChatSession", back_populates="student")
    file_uploads = relationship("FileUpload", back_populates="uploader")
    notes = relationship("Note", back_populates="student")


# ConfigOrganization已在database_models.py中定义，此处删除重复定义



class LogLogin(Base):
    """登录日志表"""
    __tablename__ = "log_login"
    
    log_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_users.user_id"))
    
    # 登录信息
    username: Mapped[str] = Column(String(50), nullable=False, comment="登录用户名")
    email: Mapped[Optional[str]] = Column(String(255), comment="登录邮箱")
    is_success: Mapped[bool] = Column(Boolean, nullable=False, comment="登录是否成功")
    failure_reason: Mapped[Optional[str]] = Column(String(200), comment="失败原因")
    
    # 设备和网络信息
    ip_address: Mapped[str] = Column(String(45), nullable=False, comment="登录IP")
    user_agent: Mapped[Optional[str]] = Column(Text, comment="用户代理")
    device_fingerprint: Mapped[Optional[str]] = Column(String(255), comment="设备指纹")
    geolocation: Mapped[Optional[dict]] = Column(JSON, comment="地理位置信息")
    
    # 安全相关
    risk_score: Mapped[Optional[float]] = Column(Float, comment="风险评分")
    requires_2fa: Mapped[bool] = Column(Boolean, default=False, comment="是否需要双因子认证")
    two_fa_method: Mapped[Optional[str]] = Column(String(50), comment="双因子认证方法")
    
    # 统一时间字段命名
    logged_in_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="登录时间")
    session_duration: Mapped[Optional[int]] = Column(Integer, comment="会话持续时间(秒)")
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="记录创建时间")
    
    # 关系
    user = relationship("ConfigUser", back_populates="login_logs")


class ConfigPermission(Base):
    """权限配置表"""
    __tablename__ = "config_permissions"
    
    permission_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    permission_code: Mapped[str] = Column(String(50), unique=True, nullable=False, comment="权限代码")
    permission_name: Mapped[str] = Column(String(100), nullable=False, comment="权限名称")
    permission_description: Mapped[Optional[str]] = Column(Text, comment="权限描述")
    
    # 权限分组
    permission_category: Mapped[str] = Column(String(50), nullable=False, comment="权限分类")
    permission_resource: Mapped[str] = Column(String(50), nullable=False, comment="资源类型")
    permission_action: Mapped[str] = Column(String(20), nullable=False, comment="操作类型")
    
    # 权限属性
    permission_is_system: Mapped[bool] = Column(Boolean, default=False, comment="是否为系统权限")
    permission_is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否激活")
    
    # 时间字段 - 保持与API兼容
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class ConfigRolePermission(Base):
    """角色权限关联表"""
    __tablename__ = "config_role_permissions"
    
    role_permission_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    role_name: Mapped[UserRole] = Column(SQLEnum(UserRole), nullable=False, comment="角色名称")
    permission_id: Mapped[str] = Column(String(36), ForeignKey("config_permissions.permission_id"), nullable=False)
    
    # 权限设置
    is_granted: Mapped[bool] = Column(Boolean, default=True, comment="是否授予")
    is_inherited: Mapped[bool] = Column(Boolean, default=False, comment="是否继承")
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关系
    permission = relationship("ConfigPermission")


class SystemSettings(Base):
    """系统设置表 - 动态配置管理"""
    __tablename__ = "system_settings"

    system_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    category: Mapped[str] = Column(String(50), nullable=False, comment="设置分类")
    setting_key: Mapped[str] = Column(String(100), nullable=False, comment="设置键名")
    setting_value: Mapped[str] = Column(Text, comment="设置值")
    value_type: Mapped[str] = Column(String(20), default="string", comment="值类型")

    # 设置属性
    display_name: Mapped[str] = Column(String(200), nullable=False, comment="显示名称")
    description: Mapped[Optional[str]] = Column(Text, comment="设置描述")
    is_public: Mapped[bool] = Column(Boolean, default=False, comment="是否为公开设置")
    is_encrypted: Mapped[bool] = Column(Boolean, default=False, comment="是否加密存储")
    validation_rule: Mapped[Optional[str]] = Column(Text, comment="验证规则")

    # 配置界面相关
    input_type: Mapped[str] = Column(String(20), default="text", comment="输入控件类型")
    options: Mapped[Optional[dict]] = Column(JSON, comment="选项配置")
    default_value: Mapped[Optional[str]] = Column(Text, comment="默认值")
    sort_order: Mapped[int] = Column(Integer, default=0, comment="排序")

    # 权限控制
    required_role: Mapped[str] = Column(String(20), default="admin", comment="所需角色")
    is_readonly: Mapped[bool] = Column(Boolean, default=False, comment="是否只读")
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否启用")

    # 时间字段 - 保持与API兼容
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 唯一约束
    __table_args__ = (UniqueConstraint('category', 'setting_key', name='uq_setting_key'),)


class LogAudit(Base):
    """操作审计日志表"""
    __tablename__ = "log_audit"

    log_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = Column(String(36), comment="操作用户ID")

    # 操作信息
    action_type: Mapped[str] = Column(String(50), nullable=False, comment="操作类型")
    resource: Mapped[str] = Column(String(100), nullable=False, comment="操作资源")
    resource_id: Mapped[Optional[str]] = Column(String(36), comment="资源ID")
    description: Mapped[str] = Column(Text, nullable=False, comment="操作描述")

    # 请求信息
    request_method: Mapped[str] = Column(String(10), comment="HTTP方法")
    request_url: Mapped[str] = Column(String(500), comment="请求URL")
    ip_address: Mapped[str] = Column(String(45), comment="请求IP")
    user_agent: Mapped[Optional[str]] = Column(Text, comment="用户代理")

    # 操作详情
    status: Mapped[str] = Column(String(20), nullable=False, comment="操作状态")
    result: Mapped[Optional[dict]] = Column(JSON, comment="操作结果")
    error_message: Mapped[Optional[str]] = Column(Text, comment="错误信息")

    # 统一时间字段命名
    action_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="操作时间")
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="记录创建时间")


class SecurityPolicy(Base):
    """安全策略配置表"""
    __tablename__ = "config_security_policies"

    policy_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    policy_name: Mapped[str] = Column(String(100), nullable=False, comment="策略名称")
    policy_type: Mapped[str] = Column(String(50), nullable=False, comment="策略类型")

    # 策略配置
    config: Mapped[dict] = Column(JSON, nullable=False, comment="策略配置")
    description: Mapped[Optional[str]] = Column(Text, comment="策略描述")

    # 应用范围
    applies_to_roles: Mapped[List] = Column(JSON, default=list, comment="适用角色")
    applies_to_organizations: Mapped[List] = Column(JSON, default=list, comment="适用机构")

    # 策略状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否启用")
    is_system: Mapped[bool] = Column(Boolean, default=False, comment="是否系统策略")
    priority: Mapped[int] = Column(Integer, default=0, comment="优先级")

    # 创建者
    created_by: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"), comment="创建者")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    creator = relationship("ConfigUser")


class ConfigNotification(Base):
    """系统通知配置表"""
    __tablename__ = "config_notifications"

    notification_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = Column(String(50), nullable=False, comment="事件类型")
    notification_title: Mapped[str] = Column(String(200), nullable=False, comment="通知标题")
    notification_content: Mapped[str] = Column(Text, nullable=False, comment="通知内容")

    # 通知设置
    notification_methods: Mapped[List] = Column(JSON, default=list, comment="通知方式")
    target_roles: Mapped[List] = Column(JSON, default=list, comment="目标角色")
    target_users: Mapped[List] = Column(JSON, default=list, comment="目标用户")

    # 触发条件
    trigger_conditions: Mapped[dict] = Column(JSON, default=dict, comment="触发条件")
    frequency_limit: Mapped[Optional[dict]] = Column(JSON, comment="频率限制")

    # 状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否启用")
    is_system: Mapped[bool] = Column(Boolean, default=False, comment="是否系统通知")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
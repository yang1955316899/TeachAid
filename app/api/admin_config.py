"""
管理员配置管理API
提供系统设置、安全策略、权限管理等功能
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.auth_models import (
    ConfigUser, SystemSettings, SecurityPolicy, ConfigNotification,
    LogAudit, LogLogin, ConfigPermission, ConfigRolePermission, UserRole
)
from app.services.auth_service import get_current_user, require_admin
from app.core.unified_ai_framework import UnifiedAIFramework


router = APIRouter(prefix="/api/admin", tags=["管理员配置"])

# ============================================================================
# Pydantic模型定义
# ============================================================================

class SystemSettingCreate(BaseModel):
    category: str = Field(..., description="设置分类")
    setting_key: str = Field(..., description="设置键名")
    setting_value: str = Field(..., description="设置值")
    value_type: str = Field(default="string", description="值类型")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="设置描述")
    input_type: str = Field(default="text", description="输入控件类型")
    options: Optional[Dict] = Field(None, description="选项配置")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    required_role: str = Field(default="admin", description="所需角色")
    is_readonly: bool = Field(default=False, description="是否只读")

class SystemSettingUpdate(BaseModel):
    setting_value: Optional[str] = Field(None, description="设置值")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="设置描述")
    input_type: Optional[str] = Field(None, description="输入控件类型")
    options: Optional[Dict] = Field(None, description="选项配置")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    is_readonly: Optional[bool] = Field(None, description="是否只读")
    is_active: Optional[bool] = Field(None, description="是否启用")

class SecurityPolicyCreate(BaseModel):
    policy_name: str = Field(..., description="策略名称")
    policy_type: str = Field(..., description="策略类型")
    config: Dict = Field(..., description="策略配置")
    description: Optional[str] = Field(None, description="策略描述")
    applies_to_roles: List[str] = Field(default=[], description="适用角色")
    applies_to_organizations: List[str] = Field(default=[], description="适用机构")
    priority: int = Field(default=0, description="优先级")

class SecurityPolicyUpdate(BaseModel):
    policy_name: Optional[str] = Field(None, description="策略名称")
    config: Optional[Dict] = Field(None, description="策略配置")
    description: Optional[str] = Field(None, description="策略描述")
    applies_to_roles: Optional[List[str]] = Field(None, description="适用角色")
    applies_to_organizations: Optional[List[str]] = Field(None, description="适用机构")
    priority: Optional[int] = Field(None, description="优先级")
    is_active: Optional[bool] = Field(None, description="是否启用")

class LoginStatsResponse(BaseModel):
    total_logins: int
    successful_logins: int
    failed_logins: int
    unique_users: int
    recent_activities: List[Dict]

class SecurityStatsResponse(BaseModel):
    locked_users: int
    failed_attempts_today: int
    suspicious_ips: List[str]
    recent_security_events: List[Dict]

# ============================================================================
# 系统设置管理
# ============================================================================

@router.get("/settings", summary="获取系统设置列表")
async def get_system_settings(
    category: Optional[str] = Query(None, description="设置分类"),
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取系统设置列表，支持按分类筛选"""
    query = db.query(SystemSettings)

    if category:
        query = query.filter(SystemSettings.category == category)

    settings = query.filter(SystemSettings.is_active == True).order_by(
        SystemSettings.category, SystemSettings.sort_order
    ).all()

    # 按分类组织数据
    result = {}
    for setting in settings:
        if setting.category not in result:
            result[setting.category] = []

        setting_data = {
            "system_id": setting.system_id,
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value,
            "value_type": setting.value_type,
            "display_name": setting.display_name,
            "description": setting.description,
            "input_type": setting.input_type,
            "options": setting.options,
            "default_value": setting.default_value,
            "validation_rule": setting.validation_rule,
            "is_readonly": setting.is_readonly,
            "required_role": setting.required_role,
            "updated_time": setting.updated_time
        }
        result[setting.category].append(setting_data)

    return {"settings": result}

@router.post("/settings", summary="创建系统设置")
async def create_system_setting(
    setting_data: SystemSettingCreate,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建新的系统设置"""
    # 检查设置是否已存在
    existing = db.query(SystemSettings).filter(
        and_(
            SystemSettings.category == setting_data.category,
            SystemSettings.setting_key == setting_data.setting_key
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"设置 {setting_data.category}.{setting_data.setting_key} 已存在"
        )

    new_setting = SystemSettings(
        category=setting_data.category,
        setting_key=setting_data.setting_key,
        setting_value=setting_data.setting_value,
        value_type=setting_data.value_type,
        display_name=setting_data.display_name,
        description=setting_data.description,
        input_type=setting_data.input_type,
        options=setting_data.options,
        default_value=setting_data.default_value,
        validation_rule=setting_data.validation_rule,
        required_role=setting_data.required_role,
        is_readonly=setting_data.is_readonly
    )

    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_SETTING",
        resource="system_settings",
        resource_id=new_setting.system_id,
        description=f"创建系统设置: {setting_data.category}.{setting_data.setting_key}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "系统设置创建成功", "setting_id": new_setting.system_id}

@router.put("/settings/{setting_id}", summary="更新系统设置")
async def update_system_setting(
    setting_id: str,
    setting_data: SystemSettingUpdate,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新系统设置"""
    setting = db.query(SystemSettings).filter(SystemSettings.system_id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")

    # 检查是否只读
    if setting.is_readonly and not setting_data.is_readonly:
        raise HTTPException(status_code=403, detail="只读设置无法修改")

    # 更新字段
    update_data = setting_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_SETTING",
        resource="system_settings",
        resource_id=setting_id,
        description=f"更新系统设置: {setting.category}.{setting.setting_key}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "系统设置更新成功"}

# ============================================================================
# 安全策略管理
# ============================================================================

@router.get("/security-policies", summary="获取安全策略列表")
async def get_security_policies(
    policy_type: Optional[str] = Query(None, description="策略类型"),
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取安全策略列表"""
    query = db.query(SecurityPolicy)

    if policy_type:
        query = query.filter(SecurityPolicy.policy_type == policy_type)

    policies = query.filter(SecurityPolicy.is_active == True).order_by(
        SecurityPolicy.priority.desc(), SecurityPolicy.created_time
    ).all()

    result = []
    for policy in policies:
        policy_data = {
            "policy_id": policy.policy_id,
            "policy_name": policy.policy_name,
            "policy_type": policy.policy_type,
            "config": policy.config,
            "description": policy.description,
            "applies_to_roles": policy.applies_to_roles,
            "applies_to_organizations": policy.applies_to_organizations,
            "priority": policy.priority,
            "is_system": policy.is_system,
            "created_time": policy.created_time,
            "updated_time": policy.updated_time
        }
        result.append(policy_data)

    return {"policies": result}

@router.post("/security-policies", summary="创建安全策略")
async def create_security_policy(
    policy_data: SecurityPolicyCreate,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建新的安全策略"""
    new_policy = SecurityPolicy(
        policy_name=policy_data.policy_name,
        policy_type=policy_data.policy_type,
        config=policy_data.config,
        description=policy_data.description,
        applies_to_roles=policy_data.applies_to_roles,
        applies_to_organizations=policy_data.applies_to_organizations,
        priority=policy_data.priority,
        created_by=current_user.user_id
    )

    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_POLICY",
        resource="security_policies",
        resource_id=new_policy.policy_id,
        description=f"创建安全策略: {policy_data.policy_name}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "安全策略创建成功", "policy_id": new_policy.policy_id}

@router.put("/security-policies/{policy_id}", summary="更新安全策略")
async def update_security_policy(
    policy_id: str,
    policy_data: SecurityPolicyUpdate,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新安全策略"""
    policy = db.query(SecurityPolicy).filter(SecurityPolicy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")

    # 检查是否为系统策略
    if policy.is_system:
        raise HTTPException(status_code=403, detail="系统策略无法修改")

    # 更新字段
    update_data = policy_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_POLICY",
        resource="security_policies",
        resource_id=policy_id,
        description=f"更新安全策略: {policy.policy_name}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "安全策略更新成功"}

# ============================================================================
# 登录日志和统计
# ============================================================================

@router.get("/login-logs", summary="获取登录日志")
async def get_login_logs(
    user_id: Optional[str] = Query(None, description="用户ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    is_success: Optional[bool] = Query(None, description="是否成功"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取登录日志，支持筛选和分页"""
    query = db.query(LogLogin)

    # 筛选条件
    if user_id:
        query = query.filter(LogLogin.user_id == user_id)
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(LogLogin.logged_in_at >= start_dt)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(LogLogin.logged_in_at <= end_dt)
    if is_success is not None:
        query = query.filter(LogLogin.is_success == is_success)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    logs = query.order_by(LogLogin.logged_in_at.desc()).offset(offset).limit(page_size).all()

    result = []
    for log in logs:
        log_data = {
            "log_id": log.log_id,
            "user_id": log.user_id,
            "username": log.username,
            "email": log.email,
            "is_success": log.is_success,
            "failure_reason": log.failure_reason,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "risk_score": log.risk_score,
            "logged_in_at": log.logged_in_at,
            "session_duration": log.session_duration
        }
        result.append(log_data)

    return {
        "logs": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/login-stats", summary="获取登录统计")
async def get_login_stats(
    days: int = Query(7, description="统计天数"),
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
) -> LoginStatsResponse:
    """获取登录统计数据"""
    start_date = datetime.now() - timedelta(days=days)

    # 基础统计
    total_logins = db.query(LogLogin).filter(LogLogin.logged_in_at >= start_date).count()
    successful_logins = db.query(LogLogin).filter(
        and_(LogLogin.logged_in_at >= start_date, LogLogin.is_success == True)
    ).count()
    failed_logins = total_logins - successful_logins

    unique_users = db.query(LogLogin.user_id).filter(
        and_(LogLogin.logged_in_at >= start_date, LogLogin.is_success == True)
    ).distinct().count()

    # 最近活动
    recent_activities = db.query(LogLogin).filter(
        LogLogin.logged_in_at >= start_date
    ).order_by(LogLogin.logged_in_at.desc()).limit(10).all()

    activities = []
    for activity in recent_activities:
        activities.append({
            "username": activity.username,
            "is_success": activity.is_success,
            "ip_address": activity.ip_address,
            "logged_in_at": activity.logged_in_at,
            "failure_reason": activity.failure_reason
        })

    return LoginStatsResponse(
        total_logins=total_logins,
        successful_logins=successful_logins,
        failed_logins=failed_logins,
        unique_users=unique_users,
        recent_activities=activities
    )

@router.get("/security-stats", summary="获取安全统计")
async def get_security_stats(
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
) -> SecurityStatsResponse:
    """获取安全统计数据"""
    # 锁定用户数
    locked_users = db.query(ConfigUser).filter(
        or_(
            ConfigUser.user_status == "locked",
            ConfigUser.user_locked_until > datetime.now()
        )
    ).count()

    # 今日失败尝试次数
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    failed_attempts_today = db.query(LogLogin).filter(
        and_(
            LogLogin.logged_in_at >= today,
            LogLogin.is_success == False
        )
    ).count()

    # 可疑IP（多次失败登录的IP）
    suspicious_ips_query = db.query(
        LogLogin.ip_address,
        func.count(LogLogin.log_id).label('fail_count')
    ).filter(
        and_(
            LogLogin.logged_in_at >= today,
            LogLogin.is_success == False
        )
    ).group_by(LogLogin.ip_address).having(
        func.count(LogLogin.log_id) >= 5
    ).all()

    suspicious_ips = [ip.ip_address for ip in suspicious_ips_query]

    # 最近安全事件
    recent_events = db.query(LogAudit).filter(
        LogAudit.action_type.in_(['LOGIN_FAILED', 'ACCOUNT_LOCKED', 'SUSPICIOUS_ACTIVITY'])
    ).order_by(LogAudit.action_at.desc()).limit(10).all()

    events = []
    for event in recent_events:
        events.append({
            "action_type": event.action_type,
            "description": event.description,
            "ip_address": event.ip_address,
            "action_at": event.action_at,
            "status": event.status
        })

    return SecurityStatsResponse(
        locked_users=locked_users,
        failed_attempts_today=failed_attempts_today,
        suspicious_ips=suspicious_ips,
        recent_security_events=events
    )

# ============================================================================
# 用户管理
# ============================================================================

@router.get("/users", summary="获取用户列表")
async def get_users(
    role: Optional[str] = Query(None, description="用户角色"),
    status: Optional[str] = Query(None, description="用户状态"),
    organization_id: Optional[str] = Query(None, description="机构ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表，支持筛选和搜索"""
    query = db.query(ConfigUser)

    # 筛选条件
    if role:
        query = query.filter(ConfigUser.user_role == role)
    if status:
        query = query.filter(ConfigUser.user_status == status)
    if organization_id:
        query = query.filter(ConfigUser.organization_id == organization_id)
    if search:
        query = query.filter(
            or_(
                ConfigUser.user_name.contains(search),
                ConfigUser.user_email.contains(search),
                ConfigUser.user_full_name.contains(search)
            )
        )

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    users = query.order_by(ConfigUser.created_time.desc()).offset(offset).limit(page_size).all()

    result = []
    for user in users:
        user_data = {
            "user_id": user.user_id,
            "user_name": user.user_name,
            "user_email": user.user_email,
            "user_full_name": user.user_full_name,
            "user_role": user.user_role,
            "user_status": user.user_status,
            "organization_id": user.organization_id,
            "user_is_verified": user.user_is_verified,
            "user_failed_login_attempts": user.user_failed_login_attempts,
            "user_last_login_time": user.user_last_login_time,
            "user_login_count": user.user_login_count,
            "created_time": user.created_time
        }
        result.append(user_data)

    return {
        "users": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.put("/users/{user_id}/status", summary="更新用户状态")
async def update_user_status(
    user_id: str,
    status: str,
    reason: Optional[str] = None,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户状态（激活、停用、锁定等）"""
    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_status = user.user_status
    user.user_status = status

    # 如果解锁用户，清除失败次数和锁定时间
    if status == "active":
        user.user_failed_login_attempts = 0
        user.user_locked_until = None

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_USER_STATUS",
        resource="config_users",
        resource_id=user_id,
        description=f"用户状态变更: {old_status} -> {status}, 原因: {reason or '无'}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "用户状态更新成功"}

@router.post("/users/{user_id}/unlock", summary="解锁用户")
async def unlock_user(
    user_id: str,
    current_user: ConfigUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """解锁被锁定的用户"""
    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.user_failed_login_attempts = 0
    user.user_locked_until = None
    if user.user_status == "locked":
        user.user_status = "active"

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UNLOCK_USER",
        resource="config_users",
        resource_id=user_id,
        description=f"管理员解锁用户: {user.user_name}",
        status="success"
    )
    db.add(audit_log)
    db.commit()

    return {"message": "用户解锁成功"}
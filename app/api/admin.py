"""
管理员API接口
提供用户管理、系统管理等功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from app.core.database import get_db
from app.core.unified_ai_framework import UnifiedAIFramework
from app.models.auth_models import (
    ConfigUser, UserRole, UserStatus, ConfigOrganization, LogLogin, LogAudit,
    SystemSettings, ConfigPermission, ConfigRolePermission
)
from app.models.database_models import (
    Class, Teaching, Question, Homework, StudentHomework, ClassStudent,
    Grade, Subject, Chapter, ChatSession, ChatMessage, FileUpload
)
from app.models.pydantic_models import BaseResponse
from app.services.auth_service import get_current_user, get_current_admin
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/admin", tags=["管理员"])
security = HTTPBearer()


# 响应模型
class ResponseModel(BaseModel):
    """通用响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class PageResponseModel(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# =============================================================================
# Pydantic 模型定义
# =============================================================================

class UserListQuery(BaseModel):
    """用户列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    role: Optional[UserRole] = Field(None, description="用户角色过滤")
    status: Optional[UserStatus] = Field(None, description="用户状态过滤")
    search: Optional[str] = Field(None, description="搜索关键词")
    organization_id: Optional[str] = Field(None, description="机构ID过滤")
    sort_by: str = Field("created_time", description="排序字段")
    sort_order: str = Field("desc", description="排序方式")


class UserCreateRequest(BaseModel):
    """创建用户请求"""
    user_name: str = Field(..., min_length=3, max_length=50, description="用户名")
    user_email: str = Field(..., description="邮箱")
    user_password: str = Field(..., min_length=6, description="密码")
    user_full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    user_role: UserRole = Field(..., description="用户角色")
    organization_id: Optional[str] = Field(None, description="机构ID")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    user_email: Optional[str] = Field(None, description="邮箱")
    user_full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    user_role: Optional[UserRole] = Field(None, description="用户角色")
    user_status: Optional[UserStatus] = Field(None, description="用户状态")
    organization_id: Optional[str] = Field(None, description="机构ID")


class PasswordResetRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6, description="新密码")


class UserResponseModel(BaseModel):
    """用户响应模型"""
    user_id: str
    user_name: str
    user_email: str
    user_full_name: Optional[str]
    user_role: UserRole
    user_status: UserStatus
    organization_id: Optional[str]
    organization_name: Optional[str]
    user_is_verified: bool
    user_login_count: int
    user_last_login_time: Optional[datetime]
    user_last_activity: Optional[datetime]
    created_time: datetime
    updated_time: datetime

    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    """系统统计响应"""
    total_users: int
    total_teachers: int
    total_students: int
    total_admins: int
    total_classes: int
    total_questions: int
    total_homeworks: int
    active_users_today: int
    active_users_week: int
    recent_logins: List[Dict[str, Any]]


class ClassListQuery(BaseModel):
    """班级列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    grade_id: Optional[str] = Field(None, description="年级过滤")
    organization_id: Optional[str] = Field(None, description="机构过滤")
    is_active: Optional[bool] = Field(None, description="状态过滤")


class ClassCreateRequest(BaseModel):
    """创建班级请求"""
    name: str = Field(..., max_length=100, description="班级名称")
    description: Optional[str] = Field(None, description="班级描述")
    grade_id: Optional[str] = Field(None, description="年级ID")
    organization_id: Optional[str] = Field(None, description="机构ID")
    max_students: int = Field(50, ge=1, le=200, description="最大学生数")


class TeachingAssignmentRequest(BaseModel):
    """授课分配请求"""
    teacher_id: str = Field(..., description="教师ID")
    class_id: str = Field(..., description="班级ID")
    subject_id: str = Field(..., description="学科ID")
    term: Optional[str] = Field(None, description="学期")


# =============================================================================
# 用户管理接口
# =============================================================================

@router.get("/users", response_model=PageResponseModel)
async def get_users(
    query: UserListQuery = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    # 构建查询
    base_query = db.query(ConfigUser).join(
        ConfigOrganization, ConfigUser.organization_id == ConfigOrganization.organization_id, isouter=True
    )

    # 应用过滤条件
    if query.role:
        base_query = base_query.filter(ConfigUser.user_role == query.role)

    if query.status:
        base_query = base_query.filter(ConfigUser.user_status == query.status)

    if query.organization_id:
        base_query = base_query.filter(ConfigUser.organization_id == query.organization_id)

    if query.search:
        search_pattern = f"%{query.search}%"
        base_query = base_query.filter(
            or_(
                ConfigUser.user_name.like(search_pattern),
                ConfigUser.user_email.like(search_pattern),
                ConfigUser.user_full_name.like(search_pattern)
            )
        )

    # 排序
    sort_column = getattr(ConfigUser, query.sort_by, ConfigUser.created_time)
    if query.sort_order == "asc":
        base_query = base_query.order_by(asc(sort_column))
    else:
        base_query = base_query.order_by(desc(sort_column))

    # 分页
    total = base_query.count()
    offset = (query.page - 1) * query.page_size
    users = base_query.offset(offset).limit(query.page_size).all()

    # 组装响应数据
    items = []
    for user in users:
        user_data = UserResponseModel.model_validate(user)
        if user.organization:
            user_data.organization_name = user.organization.name
        items.append(user_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size
    )


@router.post("/users", response_model=ResponseModel)
async def create_user(
    request: UserCreateRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建用户"""
    from app.services.auth_service import hash_password

    # 检查用户名和邮箱是否已存在
    existing_user = db.query(ConfigUser).filter(
        or_(
            ConfigUser.user_name == request.user_name,
            ConfigUser.user_email == request.user_email
        )
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已存在"
        )

    # 验证机构存在性
    if request.organization_id:
        org = db.query(ConfigOrganization).filter(
            ConfigOrganization.organization_id == request.organization_id
        ).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的机构不存在"
            )

    # 创建用户
    password_hash, salt = hash_password(request.user_password)
    new_user = ConfigUser(
        user_name=request.user_name,
        user_email=request.user_email,
        user_password_hash=password_hash,
        user_password_salt=salt,
        user_full_name=request.user_full_name,
        user_role=request.user_role,
        organization_id=request.organization_id,
        user_is_verified=True  # 管理员创建的用户默认已验证
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_USER",
        resource="USER",
        resource_id=new_user.user_id,
        description=f"管理员创建用户: {new_user.user_name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="用户创建成功", data={"user_id": new_user.user_id})


@router.put("/users/{user_id}", response_model=ResponseModel)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 检查邮箱重复
    if request.user_email and request.user_email != user.user_email:
        existing = db.query(ConfigUser).filter(
            and_(
                ConfigUser.user_email == request.user_email,
                ConfigUser.user_id != user_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )

    # 验证机构存在性
    if request.organization_id:
        org = db.query(ConfigOrganization).filter(
            ConfigOrganization.organization_id == request.organization_id
        ).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的机构不存在"
            )

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_USER",
        resource="USER",
        resource_id=user_id,
        description=f"管理员更新用户信息: {user.user_name}",
        status="SUCCESS",
        result=update_data
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="用户更新成功")


@router.post("/users/{user_id}/reset-password", response_model=ResponseModel)
async def reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """重置用户密码"""
    from app.services.auth_service import hash_password

    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 重置密码
    password_hash, salt = hash_password(request.new_password)
    user.user_password_hash = password_hash
    user.user_password_salt = salt
    user.user_last_password_change = datetime.now()
    user.user_failed_login_attempts = 0
    user.user_locked_until = None
    user.updated_time = datetime.now()

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="RESET_PASSWORD",
        resource="USER",
        resource_id=user_id,
        description=f"管理员重置用户密码: {user.user_name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="密码重置成功")


@router.delete("/users/{user_id}", response_model=ResponseModel)
async def delete_user(
    user_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除用户（软删除）"""
    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 不能删除自己
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )

    # 软删除
    user.user_status = UserStatus.INACTIVE
    user.deleted_time = datetime.now()
    user.updated_time = datetime.now()

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="DELETE_USER",
        resource="USER",
        resource_id=user_id,
        description=f"管理员删除用户: {user.user_name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="用户删除成功")


@router.get("/users/{user_id}/login-logs")
async def get_user_login_logs(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取用户登录日志"""
    # 验证用户存在
    user = db.query(ConfigUser).filter(ConfigUser.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 查询登录日志
    query = db.query(LogLogin).filter(LogLogin.user_id == user_id).order_by(desc(LogLogin.logged_in_at))

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()

    return PageResponseModel(
        items=[{
            "log_id": log.log_id,
            "username": log.username,
            "is_success": log.is_success,
            "failure_reason": log.failure_reason,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "logged_in_at": log.logged_in_at,
            "session_duration": log.session_duration
        } for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


# =============================================================================
# 系统统计接口
# =============================================================================

@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    # 用户统计
    total_users = db.query(ConfigUser).filter(ConfigUser.user_status == UserStatus.ACTIVE).count()
    total_teachers = db.query(ConfigUser).filter(
        and_(ConfigUser.user_role == UserRole.TEACHER, ConfigUser.user_status == UserStatus.ACTIVE)
    ).count()
    total_students = db.query(ConfigUser).filter(
        and_(ConfigUser.user_role == UserRole.STUDENT, ConfigUser.user_status == UserStatus.ACTIVE)
    ).count()
    total_admins = db.query(ConfigUser).filter(
        and_(ConfigUser.user_role == UserRole.ADMIN, ConfigUser.user_status == UserStatus.ACTIVE)
    ).count()

    # 其他统计
    total_classes = db.query(Class).filter(Class.is_active == True).count()
    total_questions = db.query(Question).filter(Question.is_active == True).count()
    total_homeworks = db.query(Homework).count()

    # 活跃用户统计
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    active_users_today = db.query(ConfigUser).filter(
        and_(
            ConfigUser.user_last_activity >= today,
            ConfigUser.user_status == UserStatus.ACTIVE
        )
    ).count()

    active_users_week = db.query(ConfigUser).filter(
        and_(
            ConfigUser.user_last_activity >= week_ago,
            ConfigUser.user_status == UserStatus.ACTIVE
        )
    ).count()

    # 最近登录记录
    recent_logins = db.query(LogLogin).filter(
        LogLogin.is_success == True
    ).order_by(desc(LogLogin.logged_in_at)).limit(10).all()

    recent_login_data = [{
        "username": log.username,
        "ip_address": log.ip_address,
        "logged_in_at": log.logged_in_at,
        "user_agent": log.user_agent[:100] if log.user_agent else None
    } for log in recent_logins]

    return SystemStatsResponse(
        total_users=total_users,
        total_teachers=total_teachers,
        total_students=total_students,
        total_admins=total_admins,
        total_classes=total_classes,
        total_questions=total_questions,
        total_homeworks=total_homeworks,
        active_users_today=active_users_today,
        active_users_week=active_users_week,
        recent_logins=recent_login_data
    )


# =============================================================================
# 班级管理接口
# =============================================================================

@router.get("/classes", response_model=PageResponseModel)
async def get_classes(
    query: ClassListQuery = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取班级列表"""
    # 构建查询
    base_query = db.query(Class).join(
        Grade, Class.grade_id == Grade.id, isouter=True
    ).join(
        ConfigOrganization, Class.organization_id == ConfigOrganization.organization_id, isouter=True
    )

    # 应用过滤条件
    if query.grade_id:
        base_query = base_query.filter(Class.grade_id == query.grade_id)

    if query.organization_id:
        base_query = base_query.filter(Class.organization_id == query.organization_id)

    if query.is_active is not None:
        base_query = base_query.filter(Class.is_active == query.is_active)

    if query.search:
        search_pattern = f"%{query.search}%"
        base_query = base_query.filter(
            or_(
                Class.name.like(search_pattern),
                Class.description.like(search_pattern)
            )
        )

    # 排序
    base_query = base_query.order_by(desc(Class.created_time))

    # 分页
    total = base_query.count()
    offset = (query.page - 1) * query.page_size
    classes = base_query.offset(offset).limit(query.page_size).all()

    # 组装响应数据
    items = []
    for class_obj in classes:
        # 统计学生数量
        student_count = db.query(ClassStudent).filter(
            ClassStudent.class_id == class_obj.id
        ).count()

        # 统计教师数量
        teacher_count = db.query(Teaching).filter(
            and_(
                Teaching.class_id == class_obj.id,
                Teaching.is_active == True
            )
        ).count()

        class_data = {
            "id": class_obj.id,
            "name": class_obj.name,
            "description": class_obj.description,
            "grade_id": class_obj.grade_id,
            "grade_name": class_obj.grade.name if class_obj.grade else None,
            "organization_id": class_obj.organization_id,
            "organization_name": class_obj.organization.name if class_obj.organization else None,
            "max_students": class_obj.max_students,
            "student_count": student_count,
            "teacher_count": teacher_count,
            "is_active": class_obj.is_active,
            "created_time": class_obj.created_time,
            "updated_time": class_obj.updated_time
        }
        items.append(class_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size
    )


@router.post("/classes", response_model=ResponseModel)
async def create_class(
    request: ClassCreateRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建班级"""
    # 验证年级存在性
    if request.grade_id:
        grade = db.query(Grade).filter(Grade.id == request.grade_id).first()
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的年级不存在"
            )

    # 验证机构存在性
    if request.organization_id:
        org = db.query(ConfigOrganization).filter(
            ConfigOrganization.organization_id == request.organization_id
        ).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的机构不存在"
            )

    # 创建班级
    new_class = Class(
        name=request.name,
        description=request.description,
        grade_id=request.grade_id,
        organization_id=request.organization_id,
        max_students=request.max_students
    )

    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_CLASS",
        resource="CLASS",
        resource_id=new_class.id,
        description=f"管理员创建班级: {new_class.name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="班级创建成功", data={"class_id": new_class.id})


@router.put("/classes/{class_id}", response_model=ResponseModel)
async def update_class(
    class_id: str,
    request: ClassCreateRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新班级信息"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 验证年级和机构
    if request.grade_id and request.grade_id != class_obj.grade_id:
        grade = db.query(Grade).filter(Grade.id == request.grade_id).first()
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的年级不存在"
            )

    if request.organization_id and request.organization_id != class_obj.organization_id:
        org = db.query(ConfigOrganization).filter(
            ConfigOrganization.organization_id == request.organization_id
        ).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的机构不存在"
            )

    # 更新班级信息
    class_obj.name = request.name
    class_obj.description = request.description
    class_obj.grade_id = request.grade_id
    class_obj.organization_id = request.organization_id
    class_obj.max_students = request.max_students
    class_obj.updated_time = datetime.now()

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_CLASS",
        resource="CLASS",
        resource_id=class_id,
        description=f"管理员更新班级: {class_obj.name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="班级更新成功")


@router.delete("/classes/{class_id}", response_model=ResponseModel)
async def delete_class(
    class_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除班级（软删除）"""
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 检查是否有学生或作业
    student_count = db.query(ClassStudent).filter(ClassStudent.class_id == class_id).count()
    homework_count = db.query(Homework).filter(Homework.class_id == class_id).count()

    if student_count > 0 or homework_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="班级下还有学生或作业，无法删除"
        )

    # 软删除
    class_obj.is_active = False
    class_obj.updated_time = datetime.now()

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="DELETE_CLASS",
        resource="CLASS",
        resource_id=class_id,
        description=f"管理员删除班级: {class_obj.name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="班级删除成功")


@router.get("/classes/{class_id}/students")
async def get_class_students(
    class_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取班级学生列表"""
    # 验证班级存在
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 查询班级学生
    query = db.query(ClassStudent).join(
        ConfigUser, ClassStudent.student_id == ConfigUser.user_id
    ).filter(ClassStudent.class_id == class_id)

    total = query.count()
    offset = (page - 1) * page_size
    students = query.offset(offset).limit(page_size).all()

    items = []
    for cs in students:
        student_data = {
            "student_id": cs.student_id,
            "student_name": cs.student.user_name if cs.student else None,
            "student_full_name": cs.student.user_full_name if cs.student else None,
            "student_email": cs.student.user_email if cs.student else None,
            "joined_at": cs.joined_at,
            "created_time": cs.created_time
        }
        items.append(student_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/classes/{class_id}/students/{student_id}", response_model=ResponseModel)
async def add_student_to_class(
    class_id: str,
    student_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """添加学生到班级"""
    # 验证班级存在
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 验证学生存在且为学生角色
    student = db.query(ConfigUser).filter(
        and_(
            ConfigUser.user_id == student_id,
            ConfigUser.user_role == UserRole.STUDENT,
            ConfigUser.user_status == UserStatus.ACTIVE
        )
    ).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在或状态异常"
        )

    # 检查是否已在班级中
    existing = db.query(ClassStudent).filter(
        and_(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == student_id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生已在该班级中"
        )

    # 检查班级是否已满
    current_count = db.query(ClassStudent).filter(ClassStudent.class_id == class_id).count()
    if current_count >= class_obj.max_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="班级人数已满"
        )

    # 添加学生到班级
    class_student = ClassStudent(
        class_id=class_id,
        student_id=student_id
    )

    db.add(class_student)
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="ADD_STUDENT_TO_CLASS",
        resource="CLASS_STUDENT",
        resource_id=class_student.id,
        description=f"管理员添加学生 {student.user_name} 到班级 {class_obj.name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="学生添加成功")


@router.delete("/classes/{class_id}/students/{student_id}", response_model=ResponseModel)
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """从班级移除学生"""
    # 查找班级学生关系
    class_student = db.query(ClassStudent).filter(
        and_(
            ClassStudent.class_id == class_id,
            ClassStudent.student_id == student_id
        )
    ).first()

    if not class_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不在该班级中"
        )

    # 获取学生和班级信息用于日志
    student = db.query(ConfigUser).filter(ConfigUser.user_id == student_id).first()
    class_obj = db.query(Class).filter(Class.id == class_id).first()

    # 删除关系
    db.delete(class_student)
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="REMOVE_STUDENT_FROM_CLASS",
        resource="CLASS_STUDENT",
        resource_id=class_student.id,
        description=f"管理员从班级 {class_obj.name if class_obj else '未知'} 移除学生 {student.user_name if student else '未知'}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="学生移除成功")


@router.post("/teaching-assignments", response_model=ResponseModel)
async def create_teaching_assignment(
    request: TeachingAssignmentRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建教师授课安排"""
    # 验证教师存在且为教师角色
    teacher = db.query(ConfigUser).filter(
        and_(
            ConfigUser.user_id == request.teacher_id,
            ConfigUser.user_role == UserRole.TEACHER,
            ConfigUser.user_status == UserStatus.ACTIVE
        )
    ).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教师不存在或状态异常"
        )

    # 验证班级存在
    class_obj = db.query(Class).filter(Class.id == request.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 验证学科存在
    subject = db.query(Subject).filter(Subject.id == request.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学科不存在"
        )

    # 检查是否已存在相同的授课安排
    existing = db.query(Teaching).filter(
        and_(
            Teaching.teacher_id == request.teacher_id,
            Teaching.class_id == request.class_id,
            Teaching.subject_id == request.subject_id,
            Teaching.term == request.term,
            Teaching.is_active == True
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该教师已在该班级教授该学科"
        )

    # 创建授课安排
    teaching = Teaching(
        teacher_id=request.teacher_id,
        class_id=request.class_id,
        subject_id=request.subject_id,
        term=request.term
    )

    db.add(teaching)
    db.commit()
    db.refresh(teaching)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_TEACHING_ASSIGNMENT",
        resource="TEACHING",
        resource_id=teaching.id,
        description=f"管理员安排教师 {teacher.user_name} 在班级 {class_obj.name} 教授 {subject.name}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="授课安排创建成功", data={"teaching_id": teaching.id})


# =============================================================================
# 作业管理接口
# =============================================================================

class HomeworkListQuery(BaseModel):
    """作业列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    class_id: Optional[str] = Field(None, description="班级过滤")
    subject_id: Optional[str] = Field(None, description="学科过滤")
    is_published: Optional[bool] = Field(None, description="发布状态过滤")
    creator_id: Optional[str] = Field(None, description="创建者过滤")


@router.get("/homeworks", response_model=PageResponseModel)
async def get_homeworks(
    query: HomeworkListQuery = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取作业列表"""
    # 构建查询
    base_query = db.query(Homework).join(
        Class, Homework.class_id == Class.id, isouter=True
    ).join(
        Subject, Homework.subject_id == Subject.id, isouter=True
    ).join(
        ConfigUser, Homework.creator_teacher_id == ConfigUser.user_id, isouter=True
    )

    # 应用过滤条件
    if query.class_id:
        base_query = base_query.filter(Homework.class_id == query.class_id)

    if query.subject_id:
        base_query = base_query.filter(Homework.subject_id == query.subject_id)

    if query.is_published is not None:
        base_query = base_query.filter(Homework.is_published == query.is_published)

    if query.creator_id:
        base_query = base_query.filter(Homework.creator_teacher_id == query.creator_id)

    if query.search:
        search_pattern = f"%{query.search}%"
        base_query = base_query.filter(
            or_(
                Homework.title.like(search_pattern),
                Homework.description.like(search_pattern)
            )
        )

    # 排序
    base_query = base_query.order_by(desc(Homework.created_time))

    # 分页
    total = base_query.count()
    offset = (query.page - 1) * query.page_size
    homeworks = base_query.offset(offset).limit(query.page_size).all()

    # 组装响应数据
    items = []
    for homework in homeworks:
        # 统计学生完成情况
        total_students = db.query(StudentHomework).filter(
            StudentHomework.homework_id == homework.id
        ).count()

        completed_students = db.query(StudentHomework).filter(
            and_(
                StudentHomework.homework_id == homework.id,
                StudentHomework.status == "completed"
            )
        ).count()

        homework_data = {
            "id": homework.id,
            "title": homework.title,
            "description": homework.description,
            "class_id": homework.class_id,
            "class_name": homework.class_obj.name if homework.class_obj else None,
            "subject_id": homework.subject_id,
            "subject_name": homework.subject.name if homework.subject else None,
            "creator_teacher_id": homework.creator_teacher_id,
            "creator_name": homework.creator_teacher.user_full_name if homework.creator_teacher else None,
            "question_count": len(homework.question_ids) if homework.question_ids else 0,
            "total_students": total_students,
            "completed_students": completed_students,
            "completion_rate": round(completed_students / total_students * 100, 2) if total_students > 0 else 0,
            "is_published": homework.is_published,
            "due_at": homework.due_at,
            "started_at": homework.started_at,
            "created_time": homework.created_time,
            "updated_time": homework.updated_time
        }
        items.append(homework_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size
    )


@router.get("/homeworks/{homework_id}/students")
async def get_homework_students(
    homework_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取作业学生完成情况"""
    # 验证作业存在
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作业不存在"
        )

    # 查询学生作业
    query = db.query(StudentHomework).join(
        ConfigUser, StudentHomework.student_id == ConfigUser.user_id
    ).filter(StudentHomework.homework_id == homework_id)

    total = query.count()
    offset = (page - 1) * page_size
    student_homeworks = query.offset(offset).limit(page_size).all()

    items = []
    for sh in student_homeworks:
        student_data = {
            "student_homework_id": sh.id,
            "student_id": sh.student_id,
            "student_name": sh.student.user_name if sh.student else None,
            "student_full_name": sh.student.user_full_name if sh.student else None,
            "status": sh.status,
            "completion_percentage": sh.completion_percentage,
            "total_chat_sessions": sh.total_chat_sessions,
            "total_messages": sh.total_messages,
            "assigned_at": sh.assigned_at,
            "started_at": sh.started_at,
            "completed_at": sh.completed_at,
            "submitted_at": sh.submitted_at
        }
        items.append(student_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/homeworks/{homework_id}/publish", response_model=ResponseModel)
async def publish_homework(
    homework_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """发布作业"""
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作业不存在"
        )

    if homework.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="作业已发布"
        )

    # 发布作业
    homework.is_published = True
    homework.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="PUBLISH_HOMEWORK",
        resource="HOMEWORK",
        resource_id=homework_id,
        description=f"管理员发布作业: {homework.title}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="作业发布成功")


@router.post("/homeworks/{homework_id}/unpublish", response_model=ResponseModel)
async def unpublish_homework(
    homework_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """撤回作业"""
    homework = db.query(Homework).filter(Homework.id == homework_id).first()
    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作业不存在"
        )

    if not homework.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="作业未发布"
        )

    # 撤回作业
    homework.is_published = False
    homework.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UNPUBLISH_HOMEWORK",
        resource="HOMEWORK",
        resource_id=homework_id,
        description=f"管理员撤回作业: {homework.title}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="作业撤回成功")


# =============================================================================
# 题目管理接口
# =============================================================================

class QuestionListQuery(BaseModel):
    """题目列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    subject: Optional[str] = Field(None, description="学科过滤")
    question_type: Optional[str] = Field(None, description="题目类型过滤")
    difficulty: Optional[str] = Field(None, description="难度过滤")
    grade_level: Optional[str] = Field(None, description="年级过滤")
    creator_id: Optional[str] = Field(None, description="创建者过滤")
    is_public: Optional[bool] = Field(None, description="公开状态过滤")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
    min_quality_score: Optional[int] = Field(None, ge=1, le=10, description="最低质量评分")


@router.get("/questions", response_model=PageResponseModel)
async def get_questions(
    query: QuestionListQuery = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    # 构建查询
    base_query = db.query(Question).join(
        ConfigUser, Question.creator_id == ConfigUser.user_id, isouter=True
    )

    # 应用过滤条件
    if query.subject:
        base_query = base_query.filter(Question.subject == query.subject)

    if query.question_type:
        base_query = base_query.filter(Question.question_type == query.question_type)

    if query.difficulty:
        base_query = base_query.filter(Question.difficulty == query.difficulty)

    if query.grade_level:
        base_query = base_query.filter(Question.grade_level == query.grade_level)

    if query.creator_id:
        base_query = base_query.filter(Question.creator_id == query.creator_id)

    if query.is_public is not None:
        base_query = base_query.filter(Question.is_public == query.is_public)

    if query.is_active is not None:
        base_query = base_query.filter(Question.is_active == query.is_active)

    if query.min_quality_score:
        base_query = base_query.filter(Question.quality_score >= query.min_quality_score)

    if query.search:
        search_pattern = f"%{query.search}%"
        base_query = base_query.filter(
            or_(
                Question.title.like(search_pattern),
                Question.content.like(search_pattern)
            )
        )

    # 排序
    base_query = base_query.order_by(desc(Question.created_time))

    # 分页
    total = base_query.count()
    offset = (query.page - 1) * query.page_size
    questions = base_query.offset(offset).limit(query.page_size).all()

    # 组装响应数据
    items = []
    for question in questions:
        question_data = {
            "id": question.id,
            "title": question.title,
            "content": question.content[:200] + "..." if question.content and len(question.content) > 200 else question.content,
            "subject": question.subject,
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "grade_level": question.grade_level,
            "creator_id": question.creator_id,
            "creator_name": question.creator.user_full_name if question.creator else None,
            "quality_score": question.quality_score,
            "processing_cost": question.processing_cost,
            "has_image": question.has_image,
            "has_formula": question.has_formula,
            "is_public": question.is_public,
            "is_active": question.is_active,
            "knowledge_points": question.knowledge_points,
            "tags": question.tags,
            "created_time": question.created_time,
            "updated_time": question.updated_time
        }
        items.append(question_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size
    )


@router.get("/questions/{question_id}", response_model=ResponseModel)
async def get_question_detail(
    question_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取题目详情"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )

    # 构建详细信息
    question_data = {
        "id": question.id,
        "title": question.title,
        "content": question.content,
        "original_answer": question.original_answer,
        "rewritten_answer": question.rewritten_answer,
        "subject": question.subject,
        "question_type": question.question_type,
        "difficulty": question.difficulty,
        "grade_level": question.grade_level,
        "subject_id": question.subject_id,
        "grade_id": question.grade_id,
        "creator_id": question.creator_id,
        "creator_name": question.creator.user_full_name if question.creator else None,
        "quality_score": question.quality_score,
        "processing_cost": question.processing_cost,
        "extraction_model": question.extraction_model,
        "rewrite_template_id": question.rewrite_template_id,
        "source_file_path": question.source_file_path,
        "has_image": question.has_image,
        "has_formula": question.has_formula,
        "is_public": question.is_public,
        "is_active": question.is_active,
        "knowledge_points": question.knowledge_points,
        "tags": question.tags,
        "created_time": question.created_time,
        "updated_time": question.updated_time
    }

    return ResponseModel(data=question_data)


@router.put("/questions/{question_id}/status", response_model=ResponseModel)
async def update_question_status(
    question_id: str,
    is_active: bool = Query(..., description="激活状态"),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新题目状态"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )

    # 更新状态
    question.is_active = is_active
    question.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    action = "ACTIVATE_QUESTION" if is_active else "DEACTIVATE_QUESTION"
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type=action,
        resource="QUESTION",
        resource_id=question_id,
        description=f"管理员{'激活' if is_active else '停用'}题目: {question.title or '无标题'}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message=f"题目{'激活' if is_active else '停用'}成功")


@router.put("/questions/{question_id}/publicity", response_model=ResponseModel)
async def update_question_publicity(
    question_id: str,
    is_public: bool = Query(..., description="公开状态"),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新题目公开状态"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )

    # 更新公开状态
    question.is_public = is_public
    question.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    action = "MAKE_QUESTION_PUBLIC" if is_public else "MAKE_QUESTION_PRIVATE"
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type=action,
        resource="QUESTION",
        resource_id=question_id,
        description=f"管理员设置题目为{'公开' if is_public else '私有'}: {question.title or '无标题'}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message=f"题目设置为{'公开' if is_public else '私有'}成功")


@router.delete("/questions/{question_id}", response_model=ResponseModel)
async def delete_question(
    question_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除题目（软删除）"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="题目不存在"
        )

    # 检查是否有作业使用该题目
    homeworks_using = db.query(Homework).filter(
        Homework.question_ids.contains([question_id])
    ).count()

    if homeworks_using > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该题目被 {homeworks_using} 个作业使用，无法删除"
        )

    # 软删除
    question.is_active = False
    question.updated_time = datetime.now()
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="DELETE_QUESTION",
        resource="QUESTION",
        resource_id=question_id,
        description=f"管理员删除题目: {question.title or '无标题'}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="题目删除成功")


# =============================================================================
# 系统配置管理接口
# =============================================================================

class SystemSettingRequest(BaseModel):
    """系统设置请求"""
    category: str = Field(..., description="设置分类")
    setting_key: str = Field(..., description="设置键名")
    setting_value: str = Field(..., description="设置值")
    value_type: str = Field("string", description="值类型")
    description: Optional[str] = Field(None, description="设置描述")
    is_public: bool = Field(False, description="是否为公开设置")
    is_encrypted: bool = Field(False, description="是否加密存储")
    validation_rule: Optional[str] = Field(None, description="验证规则")


class SystemSettingListQuery(BaseModel):
    """系统设置列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    category: Optional[str] = Field(None, description="分类过滤")
    search: Optional[str] = Field(None, description="搜索关键词")
    is_public: Optional[bool] = Field(None, description="公开状态过滤")


@router.get("/system-settings", response_model=PageResponseModel)
async def get_system_settings(
    query: SystemSettingListQuery = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取系统设置列表"""
    # 构建查询
    base_query = db.query(SystemSettings)

    # 应用过滤条件
    if query.category:
        base_query = base_query.filter(SystemSettings.category == query.category)

    if query.is_public is not None:
        base_query = base_query.filter(SystemSettings.is_public == query.is_public)

    if query.search:
        search_pattern = f"%{query.search}%"
        base_query = base_query.filter(
            or_(
                SystemSettings.setting_key.like(search_pattern),
                SystemSettings.description.like(search_pattern)
            )
        )

    # 排序
    base_query = base_query.order_by(SystemSettings.category, SystemSettings.setting_key)

    # 分页
    total = base_query.count()
    offset = (query.page - 1) * query.page_size
    settings = base_query.offset(offset).limit(query.page_size).all()

    # 组装响应数据
    items = []
    for setting in settings:
        setting_data = {
            "system_id": setting.system_id,
            "category": setting.category,
            "setting_key": setting.setting_key,
            "setting_value": setting.setting_value if not setting.is_encrypted else "******",
            "value_type": setting.value_type,
            "description": setting.description,
            "is_public": setting.is_public,
            "is_encrypted": setting.is_encrypted,
            "validation_rule": setting.validation_rule,
            "created_time": setting.created_time,
            "updated_time": setting.updated_time
        }
        items.append(setting_data)

    return PageResponseModel(
        items=items,
        total=total,
        page=query.page,
        page_size=query.page_size,
        total_pages=(total + query.page_size - 1) // query.page_size
    )


@router.get("/system-settings/categories")
async def get_setting_categories(
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取设置分类列表"""
    categories = db.query(SystemSettings.category).distinct().all()
    return ResponseModel(data=[cat[0] for cat in categories])


@router.post("/system-settings", response_model=ResponseModel)
async def create_system_setting(
    request: SystemSettingRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建系统设置"""
    # 检查是否已存在相同的设置
    existing = db.query(SystemSettings).filter(
        and_(
            SystemSettings.category == request.category,
            SystemSettings.setting_key == request.setting_key
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该设置已存在"
        )

    # 加密处理
    setting_value = request.setting_value
    if request.is_encrypted:
        # 这里可以添加实际的加密逻辑
        pass

    # 创建设置
    new_setting = SystemSettings(
        category=request.category,
        setting_key=request.setting_key,
        setting_value=setting_value,
        value_type=request.value_type,
        description=request.description,
        is_public=request.is_public,
        is_encrypted=request.is_encrypted,
        validation_rule=request.validation_rule
    )

    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_SYSTEM_SETTING",
        resource="SYSTEM_SETTING",
        resource_id=new_setting.system_id,
        description=f"管理员创建系统设置: {request.category}.{request.setting_key}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="系统设置创建成功", data={"system_id": new_setting.system_id})


@router.put("/system-settings/{system_id}", response_model=ResponseModel)
async def update_system_setting(
    system_id: str,
    request: SystemSettingRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新系统设置"""
    setting = db.query(SystemSettings).filter(SystemSettings.system_id == system_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统设置不存在"
        )

    # 检查键名冲突
    if (request.category != setting.category or request.setting_key != setting.setting_key):
        existing = db.query(SystemSettings).filter(
            and_(
                SystemSettings.category == request.category,
                SystemSettings.setting_key == request.setting_key,
                SystemSettings.system_id != system_id
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该设置键名已存在"
            )

    # 加密处理
    setting_value = request.setting_value
    if request.is_encrypted:
        # 这里可以添加实际的加密逻辑
        pass

    # 更新设置
    setting.category = request.category
    setting.setting_key = request.setting_key
    setting.setting_value = setting_value
    setting.value_type = request.value_type
    setting.description = request.description
    setting.is_public = request.is_public
    setting.is_encrypted = request.is_encrypted
    setting.validation_rule = request.validation_rule
    setting.updated_time = datetime.now()

    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="UPDATE_SYSTEM_SETTING",
        resource="SYSTEM_SETTING",
        resource_id=system_id,
        description=f"管理员更新系统设置: {request.category}.{request.setting_key}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="系统设置更新成功")


@router.delete("/system-settings/{system_id}", response_model=ResponseModel)
async def delete_system_setting(
    system_id: str,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除系统设置"""
    setting = db.query(SystemSettings).filter(SystemSettings.system_id == system_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="系统设置不存在"
        )

    # 删除设置
    db.delete(setting)
    db.commit()

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="DELETE_SYSTEM_SETTING",
        resource="SYSTEM_SETTING",
        resource_id=system_id,
        description=f"管理员删除系统设置: {setting.category}.{setting.setting_key}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="系统设置删除成功")


# =============================================================================
# 权限管理接口
# =============================================================================

class PermissionRequest(BaseModel):
    """权限请求"""
    permission_code: str = Field(..., description="权限代码")
    permission_name: str = Field(..., description="权限名称")
    permission_description: Optional[str] = Field(None, description="权限描述")
    permission_category: str = Field(..., description="权限分类")
    permission_resource: str = Field(..., description="资源类型")
    permission_action: str = Field(..., description="操作类型")


@router.get("/permissions", response_model=PageResponseModel)
async def get_permissions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="分类过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取权限列表"""
    # 构建查询
    base_query = db.query(ConfigPermission)

    # 应用过滤条件
    if category:
        base_query = base_query.filter(ConfigPermission.permission_category == category)

    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.filter(
            or_(
                ConfigPermission.permission_code.like(search_pattern),
                ConfigPermission.permission_name.like(search_pattern),
                ConfigPermission.permission_description.like(search_pattern)
            )
        )

    # 排序
    base_query = base_query.order_by(
        ConfigPermission.permission_category,
        ConfigPermission.permission_resource,
        ConfigPermission.permission_action
    )

    # 分页
    total = base_query.count()
    offset = (page - 1) * page_size
    permissions = base_query.offset(offset).limit(page_size).all()

    items = [{
        "permission_id": perm.permission_id,
        "permission_code": perm.permission_code,
        "permission_name": perm.permission_name,
        "permission_description": perm.permission_description,
        "permission_category": perm.permission_category,
        "permission_resource": perm.permission_resource,
        "permission_action": perm.permission_action,
        "permission_is_system": perm.permission_is_system,
        "permission_is_active": perm.permission_is_active,
        "created_time": perm.created_time,
        "updated_time": perm.updated_time
    } for perm in permissions]

    return PageResponseModel(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.post("/permissions", response_model=ResponseModel)
async def create_permission(
    request: PermissionRequest,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建权限"""
    # 检查权限代码是否已存在
    existing = db.query(ConfigPermission).filter(
        ConfigPermission.permission_code == request.permission_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限代码已存在"
        )

    # 创建权限
    new_permission = ConfigPermission(
        permission_code=request.permission_code,
        permission_name=request.permission_name,
        permission_description=request.permission_description,
        permission_category=request.permission_category,
        permission_resource=request.permission_resource,
        permission_action=request.permission_action
    )

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="CREATE_PERMISSION",
        resource="PERMISSION",
        resource_id=new_permission.permission_id,
        description=f"管理员创建权限: {request.permission_code}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="权限创建成功", data={"permission_id": new_permission.permission_id})


@router.get("/roles/{role}/permissions")
async def get_role_permissions(
    role: UserRole,
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取角色权限"""
    role_permissions = db.query(ConfigRolePermission).join(
        ConfigPermission, ConfigRolePermission.permission_id == ConfigPermission.permission_id
    ).filter(ConfigRolePermission.role_name == role).all()

    permissions = [{
        "permission_id": rp.permission.permission_id,
        "permission_code": rp.permission.permission_code,
        "permission_name": rp.permission.permission_name,
        "permission_category": rp.permission.permission_category,
        "permission_resource": rp.permission.permission_resource,
        "permission_action": rp.permission.permission_action,
        "is_granted": rp.is_granted,
        "is_inherited": rp.is_inherited
    } for rp in role_permissions]

    return ResponseModel(data=permissions)


@router.post("/roles/{role}/permissions/{permission_id}", response_model=ResponseModel)
async def assign_permission_to_role(
    role: UserRole,
    permission_id: str,
    is_granted: bool = Query(True, description="是否授予权限"),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """为角色分配权限"""
    # 验证权限存在
    permission = db.query(ConfigPermission).filter(
        ConfigPermission.permission_id == permission_id
    ).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )

    # 检查是否已存在
    existing = db.query(ConfigRolePermission).filter(
        and_(
            ConfigRolePermission.role_name == role,
            ConfigRolePermission.permission_id == permission_id
        )
    ).first()

    if existing:
        # 更新现有权限
        existing.is_granted = is_granted
        db.commit()
        action = "UPDATE_ROLE_PERMISSION"
    else:
        # 创建新的角色权限
        role_permission = ConfigRolePermission(
            role_name=role,
            permission_id=permission_id,
            is_granted=is_granted
        )
        db.add(role_permission)
        db.commit()
        action = "ASSIGN_ROLE_PERMISSION"

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type=action,
        resource="ROLE_PERMISSION",
        description=f"管理员为角色 {role.value} {'授予' if is_granted else '撤销'}权限: {permission.permission_code}",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message=f"权限{'授予' if is_granted else '撤销'}成功")


# =============================================================================
# 数据统计分析接口
# =============================================================================

class AnalyticsTimeRange(BaseModel):
    """分析时间范围"""
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    period: str = Field("week", description="时间周期", pattern="^(day|week|month|year)$")


class LearningAnalyticsResponse(BaseModel):
    """学习数据分析响应"""
    total_study_sessions: int
    total_messages: int
    average_session_duration: float
    active_students: int
    popular_subjects: List[Dict[str, Any]]
    learning_trends: List[Dict[str, Any]]
    completion_rates: Dict[str, float]


@router.get("/analytics/overview")
async def get_analytics_overview(
    time_range: AnalyticsTimeRange = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取数据分析概览"""
    # 设置默认时间范围
    if not time_range.start_date:
        if time_range.period == "day":
            time_range.start_date = datetime.now() - timedelta(days=1)
        elif time_range.period == "week":
            time_range.start_date = datetime.now() - timedelta(weeks=1)
        elif time_range.period == "month":
            time_range.start_date = datetime.now() - timedelta(days=30)
        else:  # year
            time_range.start_date = datetime.now() - timedelta(days=365)

    if not time_range.end_date:
        time_range.end_date = datetime.now()

    # 学习会话统计
    session_query = db.query(ChatSession).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date
        )
    )

    total_study_sessions = session_query.count()

    # 消息统计
    message_count = db.query(func.sum(ChatSession.message_count)).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date
        )
    ).scalar() or 0

    # 平均会话时长（分钟）
    avg_duration_result = db.query(
        func.avg(
            func.extract('epoch', ChatSession.last_interaction_at - ChatSession.started_at) / 60
        )
    ).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date,
            ChatSession.last_interaction_at.isnot(None)
        )
    ).scalar()

    average_session_duration = round(float(avg_duration_result or 0), 2)

    # 活跃学生数
    active_students = db.query(ChatSession.student_id).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date
        )
    ).distinct().count()

    # 热门学科统计
    popular_subjects_query = db.query(
        Question.subject,
        func.count(ChatSession.id).label('session_count')
    ).join(
        ChatSession, Question.id == ChatSession.question_id
    ).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date,
            Question.subject.isnot(None)
        )
    ).group_by(Question.subject).order_by(desc('session_count')).limit(10).all()

    popular_subjects = [
        {"subject": subject, "session_count": count}
        for subject, count in popular_subjects_query
    ]

    # 学习趋势（按天统计）
    if time_range.period in ["day", "week"]:
        date_format = "%Y-%m-%d"
        date_trunc = func.date(ChatSession.started_at)
    elif time_range.period == "month":
        date_format = "%Y-%m-%d"
        date_trunc = func.date(ChatSession.started_at)
    else:  # year
        date_format = "%Y-%m"
        date_trunc = func.date_trunc('month', ChatSession.started_at)

    trends_query = db.query(
        date_trunc.label('date'),
        func.count(ChatSession.id).label('session_count'),
        func.count(ChatSession.student_id.distinct()).label('student_count')
    ).filter(
        and_(
            ChatSession.started_at >= time_range.start_date,
            ChatSession.started_at <= time_range.end_date
        )
    ).group_by('date').order_by('date').all()

    learning_trends = [
        {
            "date": trend.date.strftime(date_format) if hasattr(trend.date, 'strftime') else str(trend.date),
            "session_count": trend.session_count,
            "student_count": trend.student_count
        }
        for trend in trends_query
    ]

    # 作业完成率统计
    homework_stats = db.query(
        func.count(StudentHomework.id).label('total'),
        func.sum(func.case([(StudentHomework.status == 'completed', 1)], else_=0)).label('completed')
    ).join(
        Homework, StudentHomework.homework_id == Homework.id
    ).filter(
        and_(
            Homework.created_time >= time_range.start_date,
            Homework.created_time <= time_range.end_date
        )
    ).first()

    completion_rates = {
        "homework_completion": round(
            (homework_stats.completed or 0) / max(homework_stats.total or 1, 1) * 100, 2
        )
    }

    return ResponseModel(data=LearningAnalyticsResponse(
        total_study_sessions=total_study_sessions,
        total_messages=int(message_count),
        average_session_duration=average_session_duration,
        active_students=active_students,
        popular_subjects=popular_subjects,
        learning_trends=learning_trends,
        completion_rates=completion_rates
    ))


@router.get("/analytics/users")
async def get_user_analytics(
    time_range: AnalyticsTimeRange = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取用户数据分析"""
    # 设置默认时间范围
    if not time_range.start_date:
        time_range.start_date = datetime.now() - timedelta(days=30)
    if not time_range.end_date:
        time_range.end_date = datetime.now()

    # 用户注册趋势
    registration_trends = db.query(
        func.date(ConfigUser.created_time).label('date'),
        func.count(ConfigUser.user_id).label('registrations'),
        ConfigUser.user_role
    ).filter(
        and_(
            ConfigUser.created_time >= time_range.start_date,
            ConfigUser.created_time <= time_range.end_date
        )
    ).group_by('date', ConfigUser.user_role).order_by('date').all()

    # 用户活跃度分析
    user_activity = db.query(
        ConfigUser.user_role,
        func.count(ConfigUser.user_id).label('total_users'),
        func.sum(
            func.case([
                (ConfigUser.user_last_activity >= datetime.now() - timedelta(days=1), 1)
            ], else_=0)
        ).label('active_today'),
        func.sum(
            func.case([
                (ConfigUser.user_last_activity >= datetime.now() - timedelta(days=7), 1)
            ], else_=0)
        ).label('active_week'),
        func.sum(
            func.case([
                (ConfigUser.user_last_activity >= datetime.now() - timedelta(days=30), 1)
            ], else_=0)
        ).label('active_month')
    ).filter(
        ConfigUser.user_status == UserStatus.ACTIVE
    ).group_by(ConfigUser.user_role).all()

    # 登录分析
    login_stats = db.query(
        func.date(LogLogin.logged_in_at).label('date'),
        func.count(LogLogin.log_id).label('total_logins'),
        func.count(func.distinct(LogLogin.user_id)).label('unique_users'),
        func.sum(func.case([(LogLogin.is_success == True, 1)], else_=0)).label('successful_logins'),
        func.sum(func.case([(LogLogin.is_success == False, 1)], else_=0)).label('failed_logins')
    ).filter(
        and_(
            LogLogin.logged_in_at >= time_range.start_date,
            LogLogin.logged_in_at <= time_range.end_date
        )
    ).group_by('date').order_by('date').all()

    return ResponseModel(data={
        "registration_trends": [
            {
                "date": trend.date.strftime("%Y-%m-%d"),
                "registrations": trend.registrations,
                "role": trend.user_role.value
            }
            for trend in registration_trends
        ],
        "user_activity": [
            {
                "role": activity.user_role.value,
                "total_users": activity.total_users,
                "active_today": activity.active_today or 0,
                "active_week": activity.active_week or 0,
                "active_month": activity.active_month or 0,
                "activity_rate_today": round((activity.active_today or 0) / max(activity.total_users, 1) * 100, 2),
                "activity_rate_week": round((activity.active_week or 0) / max(activity.total_users, 1) * 100, 2),
                "activity_rate_month": round((activity.active_month or 0) / max(activity.total_users, 1) * 100, 2)
            }
            for activity in user_activity
        ],
        "login_stats": [
            {
                "date": stat.date.strftime("%Y-%m-%d"),
                "total_logins": stat.total_logins,
                "unique_users": stat.unique_users,
                "successful_logins": stat.successful_logins,
                "failed_logins": stat.failed_logins,
                "success_rate": round(stat.successful_logins / max(stat.total_logins, 1) * 100, 2)
            }
            for stat in login_stats
        ]
    })


@router.get("/analytics/content")
async def get_content_analytics(
    time_range: AnalyticsTimeRange = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取内容数据分析"""
    # 设置默认时间范围
    if not time_range.start_date:
        time_range.start_date = datetime.now() - timedelta(days=30)
    if not time_range.end_date:
        time_range.end_date = datetime.now()

    # 题目统计
    question_stats = db.query(
        Question.subject,
        Question.difficulty,
        func.count(Question.id).label('question_count'),
        func.avg(Question.quality_score).label('avg_quality'),
        func.sum(Question.processing_cost).label('total_cost')
    ).filter(
        and_(
            Question.created_time >= time_range.start_date,
            Question.created_time <= time_range.end_date,
            Question.is_active == True
        )
    ).group_by(Question.subject, Question.difficulty).all()

    # 作业统计
    homework_stats = db.query(
        Homework.subject_id,
        Subject.name.label('subject_name'),
        func.count(Homework.id).label('homework_count'),
        func.avg(
            func.case([
                (StudentHomework.status == 'completed', 100)
            ], else_=StudentHomework.completion_percentage)
        ).label('avg_completion'),
        func.count(StudentHomework.id).label('total_assignments')
    ).join(
        Subject, Homework.subject_id == Subject.id, isouter=True
    ).join(
        StudentHomework, Homework.id == StudentHomework.homework_id, isouter=True
    ).filter(
        and_(
            Homework.created_time >= time_range.start_date,
            Homework.created_time <= time_range.end_date
        )
    ).group_by(Homework.subject_id, Subject.name).all()

    # 文件上传统计
    file_stats = db.query(
        func.date(FileUpload.created_time).label('date'),
        func.count(FileUpload.id).label('upload_count'),
        func.sum(FileUpload.file_size).label('total_size'),
        func.avg(FileUpload.processing_time).label('avg_processing_time'),
        func.sum(FileUpload.processing_cost).label('total_processing_cost')
    ).filter(
        and_(
            FileUpload.created_time >= time_range.start_date,
            FileUpload.created_time <= time_range.end_date
        )
    ).group_by('date').order_by('date').all()

    # AI 使用统计
    ai_stats = db.query(
        ChatMessage.model_used,
        func.count(ChatMessage.id).label('usage_count'),
        func.avg(ChatMessage.token_count).label('avg_tokens'),
        func.sum(ChatMessage.cost).label('total_cost'),
        func.avg(ChatMessage.response_time).label('avg_response_time')
    ).filter(
        and_(
            ChatMessage.created_at >= time_range.start_date,
            ChatMessage.created_at <= time_range.end_date,
            ChatMessage.model_used.isnot(None)
        )
    ).group_by(ChatMessage.model_used).all()

    return ResponseModel(data={
        "question_stats": [
            {
                "subject": stat.subject,
                "difficulty": stat.difficulty,
                "question_count": stat.question_count,
                "avg_quality": round(float(stat.avg_quality or 0), 2),
                "total_cost": round(float(stat.total_cost or 0), 4)
            }
            for stat in question_stats
        ],
        "homework_stats": [
            {
                "subject_id": stat.subject_id,
                "subject_name": stat.subject_name,
                "homework_count": stat.homework_count,
                "avg_completion": round(float(stat.avg_completion or 0), 2),
                "total_assignments": stat.total_assignments
            }
            for stat in homework_stats
        ],
        "file_stats": [
            {
                "date": stat.date.strftime("%Y-%m-%d"),
                "upload_count": stat.upload_count,
                "total_size_mb": round((stat.total_size or 0) / (1024 * 1024), 2),
                "avg_processing_time": round(float(stat.avg_processing_time or 0), 2),
                "total_processing_cost": round(float(stat.total_processing_cost or 0), 4)
            }
            for stat in file_stats
        ],
        "ai_stats": [
            {
                "model": stat.model_used,
                "usage_count": stat.usage_count,
                "avg_tokens": round(float(stat.avg_tokens or 0), 0),
                "total_cost": round(float(stat.total_cost or 0), 4),
                "avg_response_time": round(float(stat.avg_response_time or 0), 0)
            }
            for stat in ai_stats
        ]
    })


@router.get("/analytics/export")
async def export_analytics_data(
    format: str = Query("csv", pattern="^(csv|excel|json)$", description="导出格式"),
    time_range: AnalyticsTimeRange = Depends(),
    current_user: ConfigUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """导出分析数据"""
    from io import StringIO, BytesIO
    import csv
    import json

    # 获取综合数据
    overview_data = await get_analytics_overview(time_range, current_user, db)
    user_data = await get_user_analytics(time_range, current_user, db)
    content_data = await get_content_analytics(time_range, current_user, db)

    export_data = {
        "overview": overview_data.data,
        "users": user_data.data,
        "content": content_data.data,
        "export_time": datetime.now().isoformat(),
        "time_range": {
            "start_date": time_range.start_date.isoformat() if time_range.start_date else None,
            "end_date": time_range.end_date.isoformat() if time_range.end_date else None,
            "period": time_range.period
        }
    }

    if format == "json":
        from fastapi.responses import Response
        return Response(
            content=json.dumps(export_data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )

    elif format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        # 写入概览数据
        writer.writerow(["=== 概览数据 ==="])
        writer.writerow(["指标", "数值"])
        writer.writerow(["总学习会话", export_data["overview"]["total_study_sessions"]])
        writer.writerow(["总消息数", export_data["overview"]["total_messages"]])
        writer.writerow(["平均会话时长(分钟)", export_data["overview"]["average_session_duration"]])
        writer.writerow(["活跃学生数", export_data["overview"]["active_students"]])
        writer.writerow([])

        # 写入热门学科
        writer.writerow(["=== 热门学科 ==="])
        writer.writerow(["学科", "会话数"])
        for subject in export_data["overview"]["popular_subjects"]:
            writer.writerow([subject["subject"], subject["session_count"]])
        writer.writerow([])

        # 写入学习趋势
        writer.writerow(["=== 学习趋势 ==="])
        writer.writerow(["日期", "会话数", "学生数"])
        for trend in export_data["overview"]["learning_trends"]:
            writer.writerow([trend["date"], trend["session_count"], trend["student_count"]])

        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    # 记录审计日志
    audit_log = LogAudit(
        user_id=current_user.user_id,
        action_type="EXPORT_ANALYTICS",
        resource="ANALYTICS",
        description=f"管理员导出分析数据 (格式: {format})",
        status="SUCCESS"
    )
    db.add(audit_log)
    db.commit()

    return ResponseModel(message="数据导出功能开发中")
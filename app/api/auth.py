"""
认证API路由 - 完整的用户认证、授权和会话管理
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.services.auth_service import (
    auth_service, 
    get_current_user, 
    get_current_admin, 
    get_current_teacher, 
    get_current_student
)
from app.models.auth_models import ConfigUser, UserRole, UserStatus
from app.models.pydantic_models import BaseResponse, UserProfileUpdateRequest


# =============================================================================
# 请求/响应模型
# =============================================================================

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    user_name: str = Field(..., min_length=3, max_length=50, description="用户名")
    user_email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    user_full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    user_role: UserRole = Field(UserRole.STUDENT, description="用户角色")
    organization_code: Optional[str] = Field(None, description="机构代码")
    invitation_code: Optional[str] = Field(None, description="邀请码")


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住登录状态")
    device_name: Optional[str] = Field(None, description="设备名称")


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]


# BaseResponse已在app.models.pydantic_models中定义，删除重复定义

class UserProfileResponse(BaseModel):
    """用户资料响应"""
    user_id: str
    user_name: str
    user_email: str
    user_full_name: Optional[str]
    user_role: str
    user_status: str
    organization_id: Optional[str]
    user_is_verified: bool
    created_time: datetime
    last_login_time: Optional[datetime]


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


# =============================================================================
# 路由定义
# =============================================================================

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register_user(
    user_data: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    - **user_name**: 用户名（3-50字符，唯一）
    - **user_email**: 邮箱地址（唯一）
    - **password**: 密码（至少6位，支持复杂度检查）
    - **user_full_name**: 真实姓名（可选）
    - **user_role**: 用户角色（admin/teacher/student，默认student）
    - **organization_code**: 机构代码（可选）
    - **invitation_code**: 邀请码（可选，暂未实现）
    """
    try:
        result = await auth_service.register_user(
            user_data.model_dump(),
            db,
            request
        )
        
        return BaseResponse(
            success=True,
            message="注册成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败：{str(e)}"
        )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login_user(
    credentials: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    - **remember_me**: 是否记住登录（暂未实现）
    - **device_name**: 设备名称（可选，用于会话管理）
    
    返回访问令牌、刷新令牌和用户信息
    """
    try:
        # 设置设备名称到请求头中
        if credentials.device_name:
            request.headers.__dict__.setdefault("_list", [])
            request.headers._list.append((b"x-device-name", credentials.device_name.encode()))
        
        result = await auth_service.authenticate_user(
            credentials.username,
            credentials.password,
            request,
            db
        )
        
        return TokenResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败：{str(e)}"
        )


@router.post("/refresh", response_model=BaseResponse, summary="刷新访问令牌")
async def refresh_access_token(
    request_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    
    返回新的访问令牌
    """
    try:
        # 解码刷新令牌
        payload = auth_service.decode_token(request_data.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌类型"
            )
        
        user_id = payload.get("sub")
        
        # 验证刷新令牌在Redis中是否存在且有效
        from app.services.token_service import token_service
        
        refresh_jti = payload.get("jti")
        if not refresh_jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌格式无效"
            )
        
        if not await token_service.validate_token(refresh_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已失效或不存在"
            )
        
        # 创建新的访问令牌
        token_data = {
            "sub": user_id,
            "username": payload.get("username"),
            "role": payload.get("role")
        }
        
        new_access_token = auth_service.create_access_token(
            token_data,
            payload.get("device_id"),
            payload.get("ip")
        )
        
        # 获取新访问令牌的JTI并存储到Redis
        new_payload = auth_service.decode_token(new_access_token)
        new_jti = new_payload["jti"]
        
        await token_service.store_token(
            user_id=user_id,
            token_id=new_jti,
            token_data={
                "type": "access",
                "device_id": payload.get("device_id"),
                "username": payload.get("username"),
                "role": payload.get("role"),
                "ip_address": payload.get("ip")
            },
            expires_in=auth_service.access_token_expire * 60
        )
        
        return BaseResponse(
            success=True,
            message="令牌刷新成功",
            data={
                "access_token": new_access_token,
                "token_type": "Bearer", 
                "expires_in": auth_service.access_token_expire * 60
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败：{str(e)}"
        )


@router.get("/profile", response_model=UserProfileResponse, summary="获取用户资料")
async def get_user_profile(
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    获取当前登录用户的详细资料

    需要有效的访问令牌
    """
    try:
        return UserProfileResponse(
            user_id=current_user.user_id,
            user_name=current_user.user_name,
            user_email=current_user.user_email,
            user_full_name=current_user.user_full_name,
            user_role=current_user.user_role.value,
            user_status=current_user.user_status.value if hasattr(current_user.user_status, 'value') else 'active',
            organization_id=current_user.organization_id,
            user_is_verified=current_user.user_is_verified,
            created_time=current_user.created_time,
            last_login_time=current_user.user_last_login_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户资料失败：{str(e)}"
        )


# UserProfileUpdateRequest已移到app.models.pydantic_models中

@router.put("/profile", response_model=BaseResponse, summary="更新用户资料")
async def update_user_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: ConfigUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户资料

    - **user_full_name**: 真实姓名（可选）
    - **user_email**: 邮箱地址（可选，需要重新验证）
    - **user_settings**: 用户设置（可选）
    - **user_preferences**: 用户偏好（可选）
    """
    try:
        # 构建更新数据
        update_data = profile_data.dict(exclude_unset=True)

        # 如果要更新邮箱，需要检查是否已被使用
        if "user_email" in update_data and update_data["user_email"] != current_user.user_email:
            from sqlalchemy import select

            existing_user = await db.execute(
                select(ConfigUser).where(
                    ConfigUser.user_email == update_data["user_email"],
                    ConfigUser.user_id != current_user.user_id
                )
            )

            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱地址已被其他用户使用"
                )

            # 邮箱变更后需要重新验证
            current_user.user_is_verified = False
            current_user.user_verification_token = None  # 可以在这里生成新的验证令牌

        # 更新用户资料
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        # 更新时间戳
        current_user.updated_time = datetime.utcnow()

        await db.commit()
        await db.refresh(current_user)

        # 返回更新后的用户资料
        updated_profile = UserProfileResponse(
            user_id=current_user.user_id,
            user_name=current_user.user_name,
            user_email=current_user.user_email,
            user_full_name=current_user.user_full_name,
            user_role=current_user.user_role.value,
            user_status=current_user.user_status.value if hasattr(current_user.user_status, 'value') else 'active',
            organization_id=current_user.organization_id,
            user_is_verified=current_user.user_is_verified,
            created_time=current_user.created_time,
            last_login_time=current_user.user_last_login_time
        )

        return BaseResponse(
            success=True,
            message="用户资料更新成功",
            data=updated_profile.dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户资料失败：{str(e)}"
        )


@router.get("/permissions", response_model=BaseResponse, summary="获取用户权限")
async def get_user_permissions(
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    获取当前用户的权限列表
    """
    try:
        permissions = await auth_service.get_user_permissions(current_user)
        
        return BaseResponse(
            success=True,
            message="获取权限成功",
            data={
                "user_id": current_user.user_id,
                "user_role": current_user.user_role.value,
                "permissions": permissions,
                "permission_count": len(permissions)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限失败：{str(e)}"
        )


@router.post("/change-password", response_model=BaseResponse, summary="修改密码")
async def change_user_password(
    request_data: ChangePasswordRequest,
    current_user: ConfigUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改用户密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码（至少6位，支持复杂度检查）
    
    注意：用户密码修改后会强制重新登录
    """
    try:
        success = await auth_service.change_password(
            current_user,
            request_data.old_password,
            request_data.new_password,
            db
        )
        
        if success:
            return BaseResponse(
                success=True,
                message="密码修改成功，请重新登录"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败：{str(e)}"
        )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout_user(
    current_user: ConfigUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出 - 撤销当前会话
    
    登出操作会撤销服务端会话
    """
    try:
        # 撤销用户会话
        await auth_service.revoke_user_session(
            current_user.user_id,
            db=db
        )
        
        return BaseResponse(
            success=True,
            message="登出成功"
        )
        
    except Exception as e:
        return BaseResponse(
            success=True,
            message="登出成功"  # 即使撤销会话失败，也认为登出成功
        )


@router.get("/check", response_model=BaseResponse, summary="检查认证状态")
async def check_auth_status(
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    检查用户认证状态
    
    用于前端验证令牌有效性
    """
    try:
        return BaseResponse(
            success=True,
            message="认证状态有效",
            data={
                "authenticated": True,
                "user_id": current_user.user_id,
                "user_name": current_user.user_name,
                "user_role": current_user.user_role.value,
                "user_status": current_user.user_status.value if hasattr(current_user.user_status, 'value') else 'active'
            }
        )
        
    except HTTPException:
        return BaseResponse(
            success=False,
            message="认证状态无效",
            data={
                "authenticated": False
            }
        )


# =============================================================================
# 管理员专用接口
# =============================================================================

@router.get("/admin/users", response_model=BaseResponse, summary="获取用户列表（管理员）")
async def get_users_list(
    page: int = 1,
    size: int = 20,
    role: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: ConfigUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表（管理员权限）
    
    - **page**: 页码（从1开始）
    - **size**: 每页大小
    - **role**: 筛选角色
    - **status**: 筛选状态
    - **search**: 搜索关键词（用户名、邮箱、姓名）
    """
    try:
        from sqlalchemy import select, func, or_
        
        # 构建查询
        query = select(ConfigUser).where(ConfigUser.deleted_time.is_(None))
        
        # 添加筛选条件
        if role:
            try:
                role_enum = UserRole(role)
                query = query.where(ConfigUser.user_role == role_enum)
            except ValueError:
                pass  # 忽略无效的角色值
        
        if status:
            try:
                status_enum = UserStatus(status)
                query = query.where(ConfigUser.user_status == status_enum)
            except ValueError:
                pass  # 忽略无效的状态值
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    ConfigUser.user_name.ilike(search_pattern),
                    ConfigUser.user_email.ilike(search_pattern),
                    ConfigUser.user_full_name.ilike(search_pattern)
                )
            )
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(ConfigUser.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        users = result.scalars().all()
        
        # 格式化用户数据
        user_list = []
        for user in users:
            user_list.append({
                "user_id": user.user_id,
                "user_name": user.user_name,
                "user_email": user.user_email,
                "user_full_name": user.user_full_name,
                "user_role": user.user_role.value,
                "user_status": user.user_status.value,
                "user_is_verified": user.user_is_verified,
                "organization_id": user.organization_id,
                "user_login_count": user.user_login_count,
                "user_last_login_time": user.user_last_login_time,
                "user_last_login_ip": user.user_last_login_ip,
                "created_time": user.created_time,
                "updated_time": user.updated_time
            })
        
        return BaseResponse(
            success=True,
            message="获取用户列表成功",
            data={
                "users": user_list,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                },
                "filters": {
                    "role": role,
                    "status": status,
                    "search": search
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败：{str(e)}"
        )


@router.put("/admin/users/{user_id}/status", response_model=BaseResponse, summary="更新用户状态（管理员）")
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: ConfigUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户状态（管理员权限）
    
    - **user_id**: 用户ID
    - **new_status**: 新状态（active/inactive/locked/suspended）
    """
    try:
        from sqlalchemy import select
        
        # 查找用户
        result = await db.execute(
            select(ConfigUser).where(ConfigUser.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 不能修改自己的状态
        if user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改自己的状态"
            )
        
        old_status = user.user_status
        user.user_status = new_status
        user.updated_time = datetime.utcnow()
        
        # 如果是锁定状态，撤销用户会话
        if new_status == UserStatus.LOCKED:
            await auth_service.revoke_user_session(user_id, db=db)
        
        await db.commit()
        
        return BaseResponse(
            success=True,
            message=f"用户状态已从 {old_status.value} 更新为 {new_status.value}",
            data={
                "user_id": user_id,
                "old_status": old_status.value,
                "new_status": new_status.value
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户状态失败：{str(e)}"
        )


# =============================================================================
# 健康检查和元信息
# =============================================================================

@router.get("/health", summary="认证服务健康检查")
async def auth_health_check():
    """
    认证服务健康检查
    """
    return {
        "service": "认证服务",
        "status": "健康",
        "version": "2.0.0",
        "features": [
            "用户注册登录",
            "JWT令牌管理", 
            "会话管理",
            "权限控制",
            "密码安全",
            "登录审计"
        ],
        "timestamp": datetime.utcnow()
    }
"""
认证相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import auth_service, get_current_user
from app.models.pydantic_models import (
    UserCreate, UserLogin, TokenResponse, UserResponse,
    BaseResponse
)
from app.models.database_models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少8位）
    - **full_name**: 真实姓名（可选）
    - **role**: 用户角色（默认为student）
    - **organization_code**: 机构代码（可选）
    - **invitation_code**: 邀请码（可选）
    """
    try:
        result = await auth_service.register_user(user_data, db)
        
        return BaseResponse(
            success=True,
            message="注册成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回访问令牌和用户信息
    """
    try:
        return await auth_service.authenticate_user(credentials, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.post("/refresh", response_model=BaseResponse, summary="刷新令牌")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    try:
        result = await auth_service.refresh_access_token(refresh_token, db)
        
        return BaseResponse(
            success=True,
            message="令牌刷新成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.get("/profile", response_model=UserResponse, summary="获取用户信息")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的详细信息
    
    需要有效的访问令牌
    """
    return UserResponse.from_orm(current_user)


@router.get("/permissions", response_model=BaseResponse, summary="获取用户权限")
async def get_permissions(
    current_user: User = Depends(get_current_user)
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
                "user_id": current_user.id,
                "role": current_user.role,
                "permissions": permissions
            }
        )
        
    except Exception as e:
        logger.error(f"获取权限失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取权限失败"
        )


@router.post("/change-password", response_model=BaseResponse, summary="修改密码")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码
    """
    try:
        await auth_service.change_password(current_user, old_password, new_password, db)
        
        return BaseResponse(
            success=True,
            message="密码修改成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"密码修改失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )


@router.post("/logout", response_model=BaseResponse, summary="用户登出")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    用户登出
    
    注意：由于使用JWT，服务端无法主动使令牌失效。
    客户端应该删除本地保存的令牌。
    """
    logger.info(f"用户登出: {current_user.username}")
    
    return BaseResponse(
        success=True,
        message="登出成功"
    )
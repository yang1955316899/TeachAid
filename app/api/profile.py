"""
用户资料相关API（拆分自认证模块）
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.auth_models import ConfigUser
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/auth", tags=["认证"])


class UpdateProfileRequest(BaseModel):
    """更新个人资料请求"""
    user_email: Optional[EmailStr] = Field(None, description="邮箱地址")
    user_full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


@router.put("/profile", summary="更新用户资料")
async def update_user_profile(
    request_data: UpdateProfileRequest,
    current_user: ConfigUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前登录用户的基本资料（邮箱、真实姓名）。
    返回与 GET /auth/profile 相同结构的数据以便前端直接使用。
    """
    try:
        updated = False

        # 更新邮箱（若提供且未被占用）
        if request_data.user_email and request_data.user_email != current_user.user_email:
            dup = await db.execute(
                select(ConfigUser).where(
                    ConfigUser.user_email == str(request_data.user_email),
                    ConfigUser.user_id != current_user.user_id
                )
            )
            if dup.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被占用"
                )
            current_user.user_email = str(request_data.user_email)
            updated = True

        # 更新真实姓名
        if request_data.user_full_name is not None and request_data.user_full_name != current_user.user_full_name:
            current_user.user_full_name = request_data.user_full_name
            updated = True

        if updated:
            current_user.updated_time = datetime.utcnow()
            await db.commit()

        # 返回最新资料（与 /auth/profile 一致的结构）
        return {
            "user_id": current_user.user_id,
            "user_name": current_user.user_name,
            "user_email": current_user.user_email,
            "user_full_name": current_user.user_full_name,
            "user_role": getattr(current_user.user_role, "value", str(current_user.user_role)),
            "user_status": getattr(current_user.user_status, "value", "active"),
            "organization_id": current_user.organization_id,
            "user_is_verified": current_user.user_is_verified,
            "created_time": current_user.created_time,
            "last_login_time": current_user.user_last_login_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        # 回滚并抛错
        try:
            await db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新资料失败：{str(e)}"
        )


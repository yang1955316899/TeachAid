"""
班级管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_teacher, get_current_user
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Class
from app.models.pydantic_models import (
    BaseResponse, PaginationQuery, PaginationResponse
)
from pydantic import BaseModel

router = APIRouter(prefix="/classes", tags=["班级管理"])


# 简化的请求/响应模型
class ClassCreate(BaseModel):
    """创建班级请求"""
    name: str
    description: str = None
    grade_level: str = None
    subject: str = None
    max_students: int = 50


class ClassUpdate(BaseModel):
    """更新班级请求"""
    name: str = None
    description: str = None
    grade_level: str = None
    subject: str = None
    max_students: int = None
    is_active: bool = None


class ClassResponse(BaseModel):
    """班级响应"""
    id: int
    name: str
    description: str = None
    grade_level: str = None
    subject: str = None
    teacher_id: int
    organization_id: int = None
    max_students: int
    is_active: bool
    created_at: str = None
    updated_at: str = None
    teacher_name: str = None
    organization_name: str = None
    
    @classmethod
    def from_orm(cls, class_obj):
        data = {
            "id": class_obj.id,
            "name": class_obj.name,
            "description": class_obj.description,
            "grade_level": class_obj.grade_level,
            "subject": class_obj.subject,
            "teacher_id": class_obj.teacher_id,
            "organization_id": class_obj.organization_id,
            "max_students": class_obj.max_students,
            "is_active": class_obj.is_active,
            "created_at": class_obj.created_at.isoformat() if class_obj.created_at else None,
            "updated_at": class_obj.updated_at.isoformat() if class_obj.updated_at else None,
            "teacher_name": None,
            "organization_name": None
        }
        
        # 关联信息
        if hasattr(class_obj, 'teacher') and class_obj.teacher:
            data["teacher_name"] = class_obj.teacher.user_full_name
        if hasattr(class_obj, 'organization') and class_obj.organization:
            data["organization_name"] = class_obj.organization.organization_name
            
        return cls(**data)


@router.get("", response_model=PaginationResponse, summary="获取班级列表")
async def list_classes(
    pagination: PaginationQuery = Depends(),
    subject: Optional[str] = Query(None, description="学科筛选"),
    grade_level: Optional[str] = Query(None, description="年级筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取班级列表（分页）
    
    - 支持按学科、年级筛选
    - 支持关键词搜索
    - 教师只能看到自己教授的班级
    """
    try:
        # 构建查询条件
        conditions = [Class.is_active == True]
        
        # 权限过滤
        if current_user.user_role == "teacher":
            conditions.append(Class.teacher_id == current_user.user_id)
        elif current_user.user_role == "student":
            # 学生只能看到自己所属的班级（这里简化处理，实际应该通过学生班级关联表）
            pass
        
        # 添加筛选条件
        if subject:
            conditions.append(Class.subject == subject)
        if grade_level:
            conditions.append(Class.grade_level == grade_level)
        if keyword:
            conditions.append(
                or_(
                    Class.name.contains(keyword),
                    Class.description.contains(keyword)
                )
            )
        
        # 查询总数
        count_query = select(func.count(Class.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = (
            select(Class)
            .where(and_(*conditions))
            .order_by(Class.created_at.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        
        result = await db.execute(query)
        classes = result.scalars().all()
        
        # 转换为响应模型
        class_responses = [ClassResponse(cls) for cls in classes]
        
        return PaginationResponse(
            items=class_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取班级列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取班级列表失败"
        )


@router.get("/{class_id}", response_model=BaseResponse, summary="获取班级详情")
async def get_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取班级详情
    """
    try:
        result = await db.execute(
            select(Class).where(Class.id == class_id)
        )
        class_obj = result.scalar_one_or_none()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在"
            )
        
        # 权限检查
        if (current_user.user_role == "teacher" and class_obj.teacher_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此班级"
            )
        
        return BaseResponse(
            success=True,
            message="获取班级详情成功",
            data=ClassResponse(class_obj).__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取班级详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取班级详情失败"
        )


@router.post("", response_model=BaseResponse, summary="创建班级")
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    创建班级（仅教师）
    """
    try:
        new_class = Class(
            name=class_data.name,
            description=class_data.description,
            grade_level=class_data.grade_level,
            subject=class_data.subject,
            max_students=class_data.max_students,
            teacher_id=current_user.user_id,
            organization_id=current_user.organization_id
        )
        
        db.add(new_class)
        await db.commit()
        await db.refresh(new_class)
        
        logger.info(f"班级创建成功: {new_class.id}")
        
        return BaseResponse(
            success=True,
            message="班级创建成功",
            data={"class_id": new_class.id}
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"班级创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="班级创建失败"
        )


@router.put("/{class_id}", response_model=BaseResponse, summary="更新班级")
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    更新班级信息（仅班级教师）
    """
    try:
        result = await db.execute(
            select(Class).where(Class.id == class_id)
        )
        class_obj = result.scalar_one_or_none()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在"
            )
        
        # 权限检查
        if class_obj.teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此班级"
            )
        
        # 更新字段
        update_data = class_data.__dict__
        for field, value in update_data.items():
            if value is not None:
                setattr(class_obj, field, value)
        
        await db.commit()
        
        logger.info(f"班级更新成功: {class_id}")
        
        return BaseResponse(
            success=True,
            message="班级更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"班级更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="班级更新失败"
        )


@router.delete("/{class_id}", response_model=BaseResponse, summary="删除班级")
async def delete_class(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    删除班级（软删除，仅班级教师）
    """
    try:
        result = await db.execute(
            select(Class).where(Class.id == class_id)
        )
        class_obj = result.scalar_one_or_none()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在"
            )
        
        # 权限检查
        if class_obj.teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此班级"
            )
        
        # 软删除
        class_obj.is_active = False
        await db.commit()
        
        logger.info(f"班级删除成功: {class_id}")
        
        return BaseResponse(
            success=True,
            message="班级删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"班级删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="班级删除失败"
        )


@router.get("/{class_id}/students", response_model=BaseResponse, summary="获取班级学生列表")
async def get_class_students(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取班级学生列表
    """
    try:
        result = await db.execute(
            select(Class).where(Class.id == class_id)
        )
        class_obj = result.scalar_one_or_none()
        
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="班级不存在"
            )
        
        # 权限检查
        if (current_user.user_role == "teacher" and class_obj.teacher_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此班级"
            )
        
        # TODO: 实现学生关联逻辑
        # 这里需要查询学生班级关联表，当前简化处理
        
        return BaseResponse(
            success=True,
            message="获取班级学生列表成功",
            data={"students": [], "total": 0}  # 临时返回空列表
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取班级学生列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取班级学生列表失败"
        )
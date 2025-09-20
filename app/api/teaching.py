"""
教师授课关系 API - 增强版
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_teacher, get_current_user
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Teaching, Class, Subject, Grade
from app.models.pydantic_models import BaseResponse, PaginationQuery
from pydantic import BaseModel

router = APIRouter(prefix="/teaching", tags=["授课关系管理"])


class TeachingCreate(BaseModel):
    class_id: str
    subject_id: str
    term: Optional[str] = None


class TeachingUpdate(BaseModel):
    term: Optional[str] = None
    is_active: Optional[bool] = None


class TeachingResponse(BaseModel):
    id: str
    teacher_id: str
    class_id: str
    subject_id: str
    term: Optional[str] = None
    is_active: bool
    created_time: Optional[str] = None
    updated_time: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    grade_name: Optional[str] = None
    teacher_name: Optional[str] = None

    @classmethod
    def from_orm(cls, teaching_obj: Teaching, **kwargs):
        return cls(
            id=teaching_obj.id,
            teacher_id=teaching_obj.teacher_id,
            class_id=teaching_obj.class_id,
            subject_id=teaching_obj.subject_id,
            term=teaching_obj.term,
            is_active=teaching_obj.is_active,
            created_time=teaching_obj.created_time.isoformat() if teaching_obj.created_time else None,
            updated_time=teaching_obj.updated_time.isoformat() if teaching_obj.updated_time else None,
            class_name=kwargs.get("class_name"),
            subject_name=kwargs.get("subject_name"),
            grade_name=kwargs.get("grade_name"),
            teacher_name=kwargs.get("teacher_name"),
        )


@router.get("/my", response_model=BaseResponse, summary="获取我的授课关系")
async def list_my_teaching(
    pagination: PaginationQuery = Depends(),
    class_id: Optional[str] = Query(None, description="班级筛选"),
    subject_id: Optional[str] = Query(None, description="学科筛选"),
    term: Optional[str] = Query(None, description="学期筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教师的授课关系列表"""
    try:
        conditions = [Teaching.teacher_id == current_user.user_id]

        if class_id:
            conditions.append(Teaching.class_id == class_id)
        if subject_id:
            conditions.append(Teaching.subject_id == subject_id)
        if term:
            conditions.append(Teaching.term == term)
        if is_active is not None:
            conditions.append(Teaching.is_active == is_active)

        # 统计总数
        count_q = select(func.count(Teaching.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = (
            select(Teaching, Class.name, Subject.name, Grade.name, User.user_full_name, User.user_name)
            .outerjoin(Class, Teaching.class_id == Class.id)
            .outerjoin(Subject, Teaching.subject_id == Subject.id)
            .outerjoin(Grade, Class.grade_id == Grade.id)
            .outerjoin(User, Teaching.teacher_id == User.user_id)
            .where(and_(*conditions))
            .order_by(Teaching.created_time.desc())
            .offset(offset)
            .limit(pagination.size)
        )

        result = await db.execute(query)
        items = []
        for teaching, class_name, subject_name, grade_name, teacher_full_name, teacher_username in result.all():
            teaching_data = TeachingResponse.from_orm(
                teaching,
                class_name=class_name,
                subject_name=subject_name,
                grade_name=grade_name,
                teacher_name=teacher_full_name or teacher_username,
            )
            items.append(teaching_data.dict())

        return BaseResponse(
            success=True,
            message="获取授课关系列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except Exception as e:
        logger.error(f"获取授课关系列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取授课关系列表失败")


@router.get("/all", response_model=BaseResponse, summary="获取所有授课关系（管理员）")
async def list_all_teaching(
    pagination: PaginationQuery = Depends(),
    teacher_id: Optional[str] = Query(None, description="教师筛选"),
    class_id: Optional[str] = Query(None, description="班级筛选"),
    subject_id: Optional[str] = Query(None, description="学科筛选"),
    term: Optional[str] = Query(None, description="学期筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有授课关系列表（仅管理员）"""
    try:
        if current_user.user_role.value != "admin":
            raise HTTPException(status_code=403, detail="仅管理员可访问")

        conditions = []
        if teacher_id:
            conditions.append(Teaching.teacher_id == teacher_id)
        if class_id:
            conditions.append(Teaching.class_id == class_id)
        if subject_id:
            conditions.append(Teaching.subject_id == subject_id)
        if term:
            conditions.append(Teaching.term == term)
        if is_active is not None:
            conditions.append(Teaching.is_active == is_active)

        # 统计总数
        count_q = select(func.count(Teaching.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = (
            select(Teaching, Class.name, Subject.name, Grade.name, User.user_full_name, User.user_name)
            .outerjoin(Class, Teaching.class_id == Class.id)
            .outerjoin(Subject, Teaching.subject_id == Subject.id)
            .outerjoin(Grade, Class.grade_id == Grade.id)
            .outerjoin(User, Teaching.teacher_id == User.user_id)
            .order_by(Teaching.created_time.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        items = []
        for teaching, class_name, subject_name, grade_name, teacher_full_name, teacher_username in result.all():
            teaching_data = TeachingResponse.from_orm(
                teaching,
                class_name=class_name,
                subject_name=subject_name,
                grade_name=grade_name,
                teacher_name=teacher_full_name or teacher_username,
            )
            items.append(teaching_data.dict())

        return BaseResponse(
            success=True,
            message="获取授课关系列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取授课关系列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取授课关系列表失败")


@router.post("", response_model=BaseResponse, summary="创建授课关系")
async def create_teaching(
    payload: TeachingCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """创建新的授课关系"""
    try:
        # 验证班级是否存在
        class_check = await db.execute(select(Class).where(Class.id == payload.class_id, Class.is_active == True))
        if not class_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="指定的班级不存在或已禁用")

        # 验证学科是否存在
        subject_check = await db.execute(select(Subject).where(Subject.id == payload.subject_id))
        if not subject_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="指定的学科不存在")

        # 检查是否已存在相同的授课关系
        exists_q = await db.execute(
            select(Teaching).where(
                and_(
                    Teaching.teacher_id == current_user.user_id,
                    Teaching.class_id == payload.class_id,
                    Teaching.subject_id == payload.subject_id,
                    Teaching.term == payload.term,
                )
            )
        )
        existing_teaching = exists_q.scalar_one_or_none()
        if existing_teaching:
            if existing_teaching.is_active:
                raise HTTPException(status_code=400, detail="授课关系已存在")
            else:
                # 重新激活已存在但被禁用的授课关系
                existing_teaching.is_active = True
                await db.commit()
                return BaseResponse(success=True, message="授课关系已重新激活", data={"id": existing_teaching.id})

        # 创建新的授课关系
        new_teaching = Teaching(
            teacher_id=current_user.user_id,
            class_id=payload.class_id,
            subject_id=payload.subject_id,
            term=payload.term,
        )
        db.add(new_teaching)
        await db.commit()
        await db.refresh(new_teaching)

        return BaseResponse(success=True, message="授课关系创建成功", data={"id": new_teaching.id})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建授课关系失败: {e}")
        raise HTTPException(status_code=500, detail="创建授课关系失败")


@router.put("/{teaching_id}", response_model=BaseResponse, summary="更新授课关系")
async def update_teaching(
    teaching_id: str,
    payload: TeachingUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """更新授课关系信息"""
    try:
        # 查找授课关系
        teaching_obj = await db.execute(select(Teaching).where(Teaching.id == teaching_id))
        teaching = teaching_obj.scalar_one_or_none()
        if not teaching:
            raise HTTPException(status_code=404, detail="授课关系不存在")

        # 权限检查
        if teaching.teacher_id != current_user.user_id and current_user.user_role.value != "admin":
            raise HTTPException(status_code=403, detail="无权修改此授课关系")

        # 更新字段
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(teaching, field, value)

        await db.commit()
        return BaseResponse(success=True, message="授课关系更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新授课关系失败: {e}")
        raise HTTPException(status_code=500, detail="更新授课关系失败")


@router.delete("/{teaching_id}", response_model=BaseResponse, summary="删除授课关系")
async def delete_teaching(
    teaching_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """删除授课关系（软删除）"""
    try:
        # 查找授课关系
        teaching_obj = await db.execute(select(Teaching).where(Teaching.id == teaching_id))
        teaching = teaching_obj.scalar_one_or_none()
        if not teaching:
            raise HTTPException(status_code=404, detail="授课关系不存在")

        # 权限检查
        if teaching.teacher_id != current_user.user_id and current_user.user_role.value != "admin":
            raise HTTPException(status_code=403, detail="无权删除此授课关系")

        # 软删除
        teaching.is_active = False
        await db.commit()

        return BaseResponse(success=True, message="授课关系已删除")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除授课关系失败: {e}")
        raise HTTPException(status_code=500, detail="删除授课关系失败")


@router.get("/classes-by-subject", response_model=BaseResponse, summary="按学科获取授课班级")
async def get_classes_by_subject(
    subject_id: Optional[str] = Query(None, description="学科ID"),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教师某学科的授课班级列表"""
    try:
        conditions = [
            Teaching.teacher_id == current_user.user_id,
            Teaching.is_active == True,
        ]
        if subject_id:
            conditions.append(Teaching.subject_id == subject_id)

        result = await db.execute(
            select(Teaching, Class.name, Subject.name)
            .join(Class, Teaching.class_id == Class.id)
            .join(Subject, Teaching.subject_id == Subject.id)
            .where(and_(*conditions))
            .order_by(Class.name)
        )

        items = []
        for teaching, class_name, subject_name in result.all():
            items.append({
                "teaching_id": teaching.id,
                "class_id": teaching.class_id,
                "class_name": class_name,
                "subject_id": teaching.subject_id,
                "subject_name": subject_name,
                "term": teaching.term,
            })

        return BaseResponse(success=True, message="获取授课班级列表成功", data={"items": items})
    except Exception as e:
        logger.error(f"获取授课班级列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取授课班级列表失败")


@router.get("/subjects-by-class", response_model=BaseResponse, summary="按班级获取授课学科")
async def get_subjects_by_class(
    class_id: Optional[str] = Query(None, description="班级ID"),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """获取当前教师某班级的授课学科列表"""
    try:
        conditions = [
            Teaching.teacher_id == current_user.user_id,
            Teaching.is_active == True,
        ]
        if class_id:
            conditions.append(Teaching.class_id == class_id)

        result = await db.execute(
            select(Teaching, Class.name, Subject.name)
            .join(Class, Teaching.class_id == Class.id)
            .join(Subject, Teaching.subject_id == Subject.id)
            .where(and_(*conditions))
            .order_by(Subject.name)
        )

        items = []
        for teaching, class_name, subject_name in result.all():
            items.append({
                "teaching_id": teaching.id,
                "class_id": teaching.class_id,
                "class_name": class_name,
                "subject_id": teaching.subject_id,
                "subject_name": subject_name,
                "term": teaching.term,
            })

        return BaseResponse(success=True, message="获取授课学科列表成功", data={"items": items})
    except Exception as e:
        logger.error(f"获取授课学科列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取授课学科列表失败")


"""
班级管理API路由（重构修复编码问题并补全学生管理）
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_user, get_current_teacher
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Class, ClassStudent, Teaching, Grade
from app.models.pydantic_models import BaseResponse, PaginationQuery, PaginationResponse
from pydantic import BaseModel


router = APIRouter(prefix="/classes", tags=["班级管理"])


class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    grade_id: Optional[str] = None
    max_students: int = 50


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    grade_id: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None


class ClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    grade_id: Optional[str] = None
    grade_name: Optional[str] = None
    organization_id: Optional[str] = None
    max_students: Optional[int] = 0
    is_active: Optional[bool] = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    organization_name: Optional[str] = None
    teachers: Optional[List[dict]] = []  # 授课老师列表

    @classmethod
    def from_orm(cls, obj: Class, teachers: Optional[List[dict]] = None):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            grade_id=obj.grade_id,
            grade_name=None,  # 需要单独查询
            organization_id=obj.organization_id,
            max_students=(obj.max_students if getattr(obj, "max_students", None) is not None else 0),
            is_active=(obj.is_active if getattr(obj, "is_active", None) is not None else True),
            created_at=(obj.created_time.isoformat() if getattr(obj, "created_time", None) else None),
            updated_at=(obj.updated_time.isoformat() if getattr(obj, "updated_time", None) else None),
            organization_name=None,  # 需要单独查询
            teachers=teachers or [],
        )


@router.get("", response_model=BaseResponse, summary="获取班级列表")
async def list_classes(
    pagination: PaginationQuery = Depends(),
    subject_id: Optional[str] = Query(None, description="学科ID筛选"),
    grade_id: Optional[str] = Query(None, description="年级ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = [Class.is_active == True]

        role = getattr(current_user.user_role, "value", current_user.user_role)
        if role == "teacher":
            # 教师只能看到自己有授课关系的班级
            teacher_class_ids_q = select(Teaching.class_id).where(
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
            teacher_class_ids = [row[0] for row in (await db.execute(teacher_class_ids_q)).all()]
            if teacher_class_ids:
                conditions.append(Class.id.in_(teacher_class_ids))
            else:
                # 如果没有授课班级，返回空结果
                return BaseResponse(
                    success=True,
                    message="获取班级列表成功",
                    data={"items": [], "total": 0, "page": pagination.page, "size": pagination.size, "pages": 0},
                )

        if grade_id:
            conditions.append(Class.grade_id == grade_id)
        if keyword:
            conditions.append(or_(Class.name.contains(keyword), Class.description.contains(keyword)))

        # 如果按学科筛选，需要通过Teaching表
        if subject_id and role == "teacher":
            subject_class_ids_q = select(Teaching.class_id).where(
                Teaching.teacher_id == current_user.user_id,
                Teaching.subject_id == subject_id,
                Teaching.is_active == True
            )
            subject_class_ids = [row[0] for row in (await db.execute(subject_class_ids_q)).all()]
            if subject_class_ids:
                conditions.append(Class.id.in_(subject_class_ids))
            else:
                return BaseResponse(
                    success=True,
                    message="获取班级列表成功",
                    data={"items": [], "total": 0, "page": pagination.page, "size": pagination.size, "pages": 0},
                )

        count_q = select(func.count(Class.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        offset = (pagination.page - 1) * pagination.size
        query = select(Class).where(and_(*conditions)).order_by(Class.created_time.desc()).offset(offset).limit(
            pagination.size
        )
        classes = (await db.execute(query)).scalars().all()

        # 获取每个班级的授课教师信息
        items = []
        for c in classes:
            teachers_q = await db.execute(
                select(Teaching, User.user_full_name, User.user_name)
                .join(User, Teaching.teacher_id == User.user_id)
                .where(Teaching.class_id == c.id, Teaching.is_active == True)
            )
            teachers = []
            for teaching, full_name, username in teachers_q.all():
                teachers.append({
                    "teacher_id": teaching.teacher_id,
                    "teacher_name": full_name or username,
                    "subject_id": teaching.subject_id,
                    "term": teaching.term
                })

            class_data = ClassResponse.from_orm(c, teachers).dict()
            items.append(class_data)

        return BaseResponse(
            success=True,
            message="获取班级列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except Exception as e:
        logger.error(f"获取班级列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取班级列表失败")


@router.get("/search", response_model=BaseResponse, summary="按年级筛选班级")
async def search_classes(
    pagination: PaginationQuery = Depends(),
    grade_id: Optional[str] = Query(None, description="年级ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        conditions = [Class.is_active == True]
        role = getattr(current_user.user_role, "value", current_user.user_role)

        if role == "teacher":
            # 教师只能看到自己有授课关系的班级
            teacher_class_ids_q = select(Teaching.class_id).where(
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
            teacher_class_ids = [row[0] for row in (await db.execute(teacher_class_ids_q)).all()]
            if teacher_class_ids:
                conditions.append(Class.id.in_(teacher_class_ids))
            else:
                return BaseResponse(
                    success=True,
                    message="获取班级列表成功",
                    data={"items": [], "total": 0, "page": pagination.page, "size": pagination.size, "pages": 0},
                )

        if grade_id:
            conditions.append(Class.grade_id == grade_id)
        if keyword:
            conditions.append(or_(Class.name.contains(keyword), Class.description.contains(keyword)))

        total = (await db.execute(select(func.count(Class.id)).where(and_(*conditions)))).scalar() or 0
        offset = (pagination.page - 1) * pagination.size
        result = await db.execute(
            select(Class)
            .where(and_(*conditions))
            .order_by(Class.created_time.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        classes = result.scalars().all()

        # 获取每个班级的授课教师信息
        items = []
        for c in classes:
            teachers_q = await db.execute(
                select(Teaching, User.user_full_name, User.user_name)
                .join(User, Teaching.teacher_id == User.user_id)
                .where(Teaching.class_id == c.id, Teaching.is_active == True)
            )
            teachers = []
            for teaching, full_name, username in teachers_q.all():
                teachers.append({
                    "teacher_id": teaching.teacher_id,
                    "teacher_name": full_name or username,
                    "subject_id": teaching.subject_id,
                    "term": teaching.term
                })

            class_data = ClassResponse.from_orm(c, teachers).dict()
            items.append(class_data)

        return BaseResponse(
            success=True,
            message="获取班级列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except Exception as e:
        logger.error(f"筛选班级失败: {e}")
        raise HTTPException(status_code=500, detail="获取班级列表失败")


@router.get("/{class_id}", response_model=BaseResponse, summary="获取班级详情")
async def get_class(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        role = getattr(current_user.user_role, "value", current_user.user_role)
        if role == "teacher":
            # 检查教师是否有此班级的授课关系
            teaching_check = await db.execute(
                select(Teaching).where(
                    Teaching.class_id == class_id,
                    Teaching.teacher_id == current_user.user_id,
                    Teaching.is_active == True
                )
            )
            if not teaching_check.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="无权访问此班级")

        # 获取班级的授课教师信息
        teachers_q = await db.execute(
            select(Teaching, User.user_full_name, User.user_name)
            .join(User, Teaching.teacher_id == User.user_id)
            .where(Teaching.class_id == class_id, Teaching.is_active == True)
        )
        teachers = []
        for teaching, full_name, username in teachers_q.all():
            teachers.append({
                "teacher_id": teaching.teacher_id,
                "teacher_name": full_name or username,
                "subject_id": teaching.subject_id,
                "term": teaching.term
            })

        return BaseResponse(
            success=True,
            message="获取班级详情成功",
            data=ClassResponse.from_orm(class_obj, teachers).dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取班级详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取班级详情失败")


@router.post("", response_model=BaseResponse, summary="创建班级")
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    try:
        # 验证年级是否存在
        if class_data.grade_id:
            grade_check = await db.execute(select(Grade).where(Grade.id == class_data.grade_id))
            if not grade_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="指定的年级不存在")

        new_class = Class(
            name=class_data.name,
            description=class_data.description,
            grade_id=class_data.grade_id,
            max_students=class_data.max_students,
            organization_id=current_user.organization_id,
        )
        db.add(new_class)
        await db.commit()
        await db.refresh(new_class)

        # 注意: 创建班级后，需要通过Teaching表单独建立授课关系
        # 这里暂不自动建立，让教师通过授课管理API来管理

        return BaseResponse(success=True, message="班级创建成功", data={"class_id": new_class.id})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"班级创建失败: {e}")
        raise HTTPException(status_code=500, detail="班级创建失败")


@router.put("/{class_id}", response_model=BaseResponse, summary="更新班级")
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        # 检查教师是否有此班级的授课关系
        teaching_check = await db.execute(
            select(Teaching).where(
                Teaching.class_id == class_id,
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
        )
        if not teaching_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权修改此班级")

        # 验证年级是否存在
        update_data = class_data.dict(exclude_unset=True)
        if "grade_id" in update_data and update_data["grade_id"]:
            grade_check = await db.execute(select(Grade).where(Grade.id == update_data["grade_id"]))
            if not grade_check.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="指定的年级不存在")

        for k, v in update_data.items():
            setattr(class_obj, k, v)
        await db.commit()
        return BaseResponse(success=True, message="班级更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"班级更新失败: {e}")
        raise HTTPException(status_code=500, detail="班级更新失败")


@router.delete("/{class_id}", response_model=BaseResponse, summary="删除班级")
async def delete_class(
    class_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        # 检查教师是否有此班级的授课关系
        teaching_check = await db.execute(
            select(Teaching).where(
                Teaching.class_id == class_id,
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
        )
        if not teaching_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权删除此班级")

        # 软删除班级
        class_obj.is_active = False

        # 同时将相关的授课关系设为无效
        await db.execute(
            select(Teaching).where(Teaching.class_id == class_id).update({"is_active": False})
        )

        await db.commit()
        return BaseResponse(success=True, message="班级删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"班级删除失败: {e}")
        raise HTTPException(status_code=500, detail="班级删除失败")


@router.get("/{class_id}/students", response_model=BaseResponse, summary="获取班级学生列表")
async def get_class_students(
    class_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        role = getattr(current_user.user_role, "value", current_user.user_role)
        if role == "teacher":
            # 检查教师是否有此班级的授课关系
            teaching_check = await db.execute(
                select(Teaching).where(
                    Teaching.class_id == class_id,
                    Teaching.teacher_id == current_user.user_id,
                    Teaching.is_active == True
                )
            )
            if not teaching_check.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="无权访问此班级")

        from app.models.auth_models import ConfigUser as CU
        rs = await db.execute(
            select(CU).join(ClassStudent, ClassStudent.student_id == CU.user_id).where(ClassStudent.class_id == class_id)
        )
        users = rs.scalars().all()
        students = [
            {
                "id": u.user_id,
                "name": u.user_full_name or u.user_name,
                "email": u.user_email,
                "status": getattr(u.user_status, "value", str(u.user_status)),
                "last_login_time": u.user_last_login_time,
            }
            for u in users
        ]
        return BaseResponse(success=True, message="获取班级学生列表成功", data={"students": students, "total": len(students)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取班级学生列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取班级学生列表失败")


@router.post("/{class_id}/students", response_model=BaseResponse, summary="添加学生到班级")
async def add_student_to_class(
    class_id: str,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        # 检查教师是否有此班级的授课关系
        teaching_check = await db.execute(
            select(Teaching).where(
                Teaching.class_id == class_id,
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
        )
        if not teaching_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权操作该班级")

        student_id = payload.get("student_id")
        if not student_id:
            raise HTTPException(status_code=400, detail="缺少student_id")

        # 验证学生是否存在
        student_check = await db.execute(select(User).where(User.user_id == student_id, User.user_role == "student"))
        if not student_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="指定的学生不存在")

        exists = (
            await db.execute(
                select(ClassStudent).where(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
            )
        ).scalar_one_or_none()
        if not exists:
            db.add(ClassStudent(class_id=class_id, student_id=student_id))
            await db.commit()
        return BaseResponse(success=True, message="添加成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"添加学生失败: {e}")
        raise HTTPException(status_code=500, detail="添加学生失败")


@router.delete("/{class_id}/students/{student_id}", response_model=BaseResponse, summary="从班级移除学生")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    try:
        class_obj = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not class_obj:
            raise HTTPException(status_code=404, detail="班级不存在")

        # 检查教师是否有此班级的授课关系
        teaching_check = await db.execute(
            select(Teaching).where(
                Teaching.class_id == class_id,
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
        )
        if not teaching_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权操作该班级")

        rs = await db.execute(
            select(ClassStudent).where(ClassStudent.class_id == class_id, ClassStudent.student_id == student_id)
        )
        cs = rs.scalar_one_or_none()
        if cs:
            await db.delete(cs)
            await db.commit()
        return BaseResponse(success=True, message="移除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"移除学生失败: {e}")
        raise HTTPException(status_code=500, detail="移除学生失败")

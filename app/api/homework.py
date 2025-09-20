"""
作业管理 API 路由（UTF-8，修复乱码与语法错误）
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.services.auth_service import (
    get_current_teacher,
    get_current_user,
    get_current_student,
)
from app.models.auth_models import ConfigUser as User
from app.models.database_models import (
    Homework,
    Class,
    Question,
    StudentHomework,
    ClassStudent,
    Teaching,
)
from app.models.pydantic_models import BaseResponse, PaginationQuery, PaginationResponse


router = APIRouter(prefix="/homework", tags=["作业管理"])


def _map_status_for_frontend(status_value: str) -> str:
    """数据库状态 -> 前端状态映射"""
    return "pending" if status_value == "assigned" else status_value


def _map_status_from_frontend(status_value: Optional[str]) -> Optional[str]:
    """前端状态 -> 数据库状态映射"""
    if status_value is None:
        return None
    return "assigned" if status_value == "pending" else status_value


class HomeworkCreate(BaseModel):
    """创建作业请求"""

    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    class_id: Optional[str] = None
    subject_id: Optional[str] = None
    question_ids: List[str] = []
    due_at: Optional[datetime] = None
    max_attempts: int = 1


class HomeworkUpdate(BaseModel):
    """更新作业请求"""

    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    question_ids: Optional[List[str]] = None
    due_at: Optional[datetime] = None
    is_published: Optional[bool] = None
    allow_late_submission: Optional[bool] = None
    max_attempts: Optional[int] = None


class HomeworkResponse(BaseModel):
    """作业响应"""

    id: str
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    creator_teacher_id: str
    class_id: Optional[str]
    subject_id: Optional[str] = None
    grade_id: Optional[str] = None
    question_ids: List[str] = []
    due_at: Optional[str] = None
    started_at: Optional[str] = None
    is_published: bool
    allow_late_submission: bool
    max_attempts: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    creator_teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    question_count: int = 0

    @classmethod
    def from_orm(cls, homework_obj: Homework):
        qids_raw = homework_obj.question_ids or []
        if isinstance(qids_raw, list):
            qids = [str(x) for x in qids_raw]
        else:
            qids = []

        data = {
            "id": homework_obj.id,
            "title": homework_obj.title,
            "description": homework_obj.description,
            "instructions": homework_obj.instructions,
            "creator_teacher_id": homework_obj.creator_teacher_id,
            "class_id": homework_obj.class_id,
            "subject_id": getattr(homework_obj, "subject_id", None),
            "grade_id": getattr(homework_obj, "grade_id", None),
            "question_ids": qids,
            "due_at": homework_obj.due_at.isoformat() if homework_obj.due_at else None,
            "started_at": homework_obj.started_at.isoformat() if homework_obj.started_at else None,
            "is_published": bool(getattr(homework_obj, "is_published", False)),
            "allow_late_submission": bool(getattr(homework_obj, "allow_late_submission", True)),
            "max_attempts": homework_obj.max_attempts,
            "created_at": homework_obj.created_time.isoformat()
            if hasattr(homework_obj, "created_time") and homework_obj.created_time
            else None,
            "updated_at": homework_obj.updated_time.isoformat()
            if hasattr(homework_obj, "updated_time") and homework_obj.updated_time
            else None,
            # 避免异步懒加载，名称不在此处取
            "creator_teacher_name": None,
            "class_name": None,
            "question_count": len(qids),
        }

        return cls(**data)


@router.get("", response_model=BaseResponse, summary="获取作业列表")
async def list_homeworks(
    pagination: PaginationQuery = Depends(),
    class_id: Optional[str] = Query(None, description="班级筛选"),
    teacher_id: Optional[str] = Query(None, description="教师筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取作业列表（分页）"""
    try:
        conditions = []
        # 权限过滤
        if current_user.user_role.value == "teacher":
            # 教师只能看到：
            # 1. 自己创建的作业
            # 2. 自己有授课关系的班级的作业
            teacher_created_condition = Homework.creator_teacher_id == current_user.user_id

            # 获取教师授课的班级
            teacher_class_ids_q = select(Teaching.class_id).where(
                Teaching.teacher_id == current_user.user_id,
                Teaching.is_active == True
            )
            teacher_class_ids = [row[0] for row in (await db.execute(teacher_class_ids_q)).all()]

            if teacher_class_ids:
                teacher_teaching_condition = Homework.class_id.in_(teacher_class_ids)
                conditions.append(or_(teacher_created_condition, teacher_teaching_condition))
            else:
                conditions.append(teacher_created_condition)

        elif current_user.user_role.value == "student":
            subq = select(StudentHomework.homework_id).where(
                StudentHomework.student_id == current_user.user_id
            )
            conditions.append(Homework.id.in_(subq))

        # 条件筛选
        if class_id:
            conditions.append(Homework.class_id == class_id)
        if teacher_id:
            conditions.append(Homework.creator_teacher_id == teacher_id)
        if is_published is not None:
            conditions.append(Homework.is_published == is_published)
        if keyword:
            conditions.append(
                or_(
                    Homework.title.contains(keyword),
                    Homework.description.contains(keyword),
                )
            )

        # 统计总数
        count_q = select(func.count(Homework.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = select(Homework)
        if conditions:
            query = query.where(and_(*conditions))
        query = (
            query.order_by(Homework.created_time.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        homeworks = (await db.execute(query)).scalars().all()
        items = [HomeworkResponse.from_orm(hw) for hw in homeworks]

        return BaseResponse(
            success=True,
            message="获取作业列表成功",
            data={
                "items": [i.dict() for i in items],
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except Exception as e:
        logger.error(f"获取作业列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作业列表失败",
        )


# 学生作业相关路由
router_student = APIRouter(prefix="/student/homework", tags=["学生作业"])


@router_student.get("", response_model=BaseResponse, summary="获取学生作业列表")
async def get_student_homeworks(
    pagination: PaginationQuery = Depends(),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """获取当前学生的作业列表（分页）"""
    try:
        db_status = _map_status_from_frontend(status)

        conditions = [StudentHomework.student_id == current_user.user_id]
        if db_status:
            conditions.append(StudentHomework.status == db_status)

        count_q = select(func.count(StudentHomework.id)).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        offset = (pagination.page - 1) * pagination.size
        query = (
            select(StudentHomework)
            .where(and_(*conditions))
            .order_by(StudentHomework.assigned_at.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        result = await db.execute(query)
        student_hws = result.scalars().all()

        items: List[Dict[str, Any]] = []
        if student_hws:
            hw_ids = [sh.homework_id for sh in student_hws]
            hw_map: Dict[str, Homework] = {}
            if hw_ids:
                hws_rs = await db.execute(
                    select(Homework).where(Homework.id.in_(hw_ids))
                )
                for hw in hws_rs.scalars().all():
                    hw_map[hw.id] = hw

            class_ids = list(
                {hw_map[h].class_id for h in hw_map if hw_map[h].class_id}
            )
            class_map: Dict[str, Class] = {}
            if class_ids:
                cl_rs = await db.execute(select(Class).where(Class.id.in_(class_ids)))
                for cl in cl_rs.scalars().all():
                    class_map[cl.id] = cl

            for sh in student_hws:
                hw = hw_map.get(sh.homework_id)
                if not hw:
                    continue
                items.append(
                    {
                        "id": sh.homework_id,
                        "homework_id": sh.homework_id,
                        "student_homework_id": sh.id,
                        "title": hw.title,
                        "class_id": hw.class_id,
                        "class_name": class_map.get(hw.class_id).name
                        if hw.class_id and class_map.get(hw.class_id)
                        else None,
                        "subject": None,
                        "question_count": len(hw.question_ids or []),
                        "due_date": hw.due_at.isoformat() if hw.due_at else None,
                        "progress": int(round((sh.completion_percentage or 0.0))),
                        "status": _map_status_for_frontend(sh.status or "assigned"),
                        "assigned_at": sh.assigned_at.isoformat()
                        if sh.assigned_at
                        else None,
                        "started_at": sh.started_at.isoformat() if sh.started_at else None,
                        "completed_at": sh.completed_at.isoformat()
                        if sh.completed_at
                        else None,
                    }
                )

        return BaseResponse(
            success=True,
            message="获取学生作业列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size,
            },
        )
    except Exception as e:
        logger.error(f"获取学生作业列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取学生作业列表失败"
        )


@router_student.get("/{homework_id}", response_model=BaseResponse, summary="获取学生作业详情")
async def get_student_homework(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """获取学生作业详情"""
    try:
        hw_rs = await db.execute(select(Homework).where(Homework.id == homework_id))
        hw = hw_rs.scalar_one_or_none()
        if not hw:
            raise HTTPException(status_code=404, detail="作业不存在")

        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()

        data = {
            "id": homework_id,
            "title": hw.title,
            "description": hw.description,
            "instructions": hw.instructions,
            "question_ids": hw.question_ids or [],
            "due_date": hw.due_at.isoformat() if hw.due_at else None,
            "status": _map_status_for_frontend(sh.status) if sh else "pending",
            "progress": int(round((sh.completion_percentage or 0.0))) if sh else 0,
            "started_at": sh.started_at.isoformat() if sh and sh.started_at else None,
            "completed_at": sh.completed_at.isoformat() if sh and sh.completed_at else None,
        }

        return BaseResponse(success=True, message="获取学生作业详情成功", data=data)
    except Exception as e:
        logger.error(f"获取学生作业详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取学生作业详情失败"
        )


@router_student.post("/{homework_id}/start", response_model=BaseResponse, summary="开始作业")
async def start_homework(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """学生开始作业（创建/更新学生作业记录）"""
    try:
        hw_rs = await db.execute(select(Homework).where(Homework.id == homework_id))
        hw = hw_rs.scalar_one_or_none()
        if not hw:
            raise HTTPException(status_code=404, detail="作业不存在")

        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        now = datetime.utcnow()
        if not sh:
            sh = StudentHomework(
                homework_id=homework_id,
                student_id=current_user.user_id,
                status="in_progress",
                started_at=now,
                completion_percentage=0.0,
                progress={},
            )
            db.add(sh)
        else:
            if sh.status == "assigned":
                sh.status = "in_progress"
            if not sh.started_at:
                sh.started_at = now

        await db.commit()
        return BaseResponse(success=True, message="作业已开始")
    except Exception as e:
        await db.rollback()
        logger.error(f"开始作业失败: {e}")
        raise HTTPException(status_code=500, detail="开始作业失败")


@router_student.post(
    "/{homework_id}/questions/{question_id}/answer",
    response_model=BaseResponse,
    summary="提交答案",
)
async def submit_answer(
    homework_id: str,
    question_id: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    try:
        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        if not sh:
            sh = StudentHomework(
                homework_id=homework_id,
                student_id=current_user.user_id,
                status="in_progress",
                started_at=datetime.utcnow(),
                completion_percentage=0.0,
                progress={},
            )
            db.add(sh)

        answer = payload.get("answer")
        prog = sh.progress or {}
        answers = prog.get("answers", {})
        answers[question_id] = {
            "answer": answer,
            "updated_at": datetime.utcnow().isoformat(),
        }
        prog["answers"] = answers
        sh.progress = prog

        hw_rs = await db.execute(select(Homework).where(Homework.id == homework_id))
        hw = hw_rs.scalar_one_or_none()
        total = len(hw.question_ids or []) if hw else 0
        answered = len(answers)
        sh.completion_percentage = (answered / total * 100.0) if total > 0 else 0.0

        await db.commit()

        return BaseResponse(
            success=True,
            message="答案提交成功",
            data={
                "answered": answered,
                "total": total,
                "completion_percentage": int(round(sh.completion_percentage)),
            },
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"提交答案失败: {e}")
        raise HTTPException(status_code=500, detail="提交答案失败")


@router_student.post("/{homework_id}/complete", response_model=BaseResponse, summary="完成作业")
async def complete_homework(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    try:
        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        if not sh:
            raise HTTPException(status_code=404, detail="未开始的作业，无法完成")

        sh.status = "completed"
        sh.completed_at = datetime.utcnow()
        sh.completion_percentage = max(sh.completion_percentage or 0.0, 100.0)
        await db.commit()

        return BaseResponse(success=True, message="作业已完成")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"完成作业失败: {e}")
        raise HTTPException(status_code=500, detail="完成作业失败")


@router_student.get("/{homework_id}/result", response_model=BaseResponse, summary="获取作业结果")
async def get_homework_result(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    try:
        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        if not sh:
            raise HTTPException(status_code=404, detail="未找到作业进度")

        hw_rs = await db.execute(select(Homework).where(Homework.id == homework_id))
        hw = hw_rs.scalar_one_or_none()
        total = len(hw.question_ids or []) if hw else 0
        answers = (sh.progress or {}).get("answers", {})
        answered = len(answers)

        return BaseResponse(
            success=True,
            message="获取作业结果成功",
            data={
                "homework_id": homework_id,
                "status": _map_status_for_frontend(sh.status or "assigned"),
                "completion_percentage": int(round(sh.completion_percentage or 0.0)),
                "answered": answered,
                "total": total,
                "answers": answers,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业结果失败: {e}")
        raise HTTPException(status_code=500, detail="获取作业结果失败")


@router_student.get(
    "/{homework_id}/my-progress",
    response_model=BaseResponse,
    summary="获取我的学习进度",
)
async def get_my_progress(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    try:
        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == current_user.user_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        if not sh:
            return BaseResponse(
                success=True,
                message="未开始",
                data={"status": "pending", "completion_percentage": 0},
            )

        return BaseResponse(
            success=True,
            message="获取进度成功",
            data={
                "status": _map_status_for_frontend(sh.status or "assigned"),
                "completion_percentage": int(round(sh.completion_percentage or 0.0)),
            },
        )
    except Exception as e:
        logger.error(f"获取学习进度失败: {e}")
        raise HTTPException(status_code=500, detail="获取学习进度失败")


@router.get(
    "/{homework_id}/student/{student_id}/progress",
    response_model=BaseResponse,
    summary="获取学生作业进度（教师）",
)
async def get_student_progress_for_homework(
    homework_id: str,
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        hw_rs = await db.execute(select(Homework).where(Homework.id == homework_id))
        hw = hw_rs.scalar_one_or_none()
        if not hw:
            raise HTTPException(status_code=404, detail="作业不存在")

        if current_user.user_role.value == "teacher":
            # 教师权限检查：1.自己创建的作业 2.自己有授课关系的班级的作业
            is_creator = hw.creator_teacher_id == current_user.user_id
            has_teaching_relation = False

            if hw.class_id:
                teaching_check = await db.execute(
                    select(Teaching).where(
                        Teaching.class_id == hw.class_id,
                        Teaching.teacher_id == current_user.user_id,
                        Teaching.is_active == True
                    )
                )
                has_teaching_relation = teaching_check.scalar_one_or_none() is not None

            if not (is_creator or has_teaching_relation):
                raise HTTPException(status_code=403, detail="无权查看该作业学生进度")
        elif current_user.user_role.value == "student" and student_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权查看其他学生进度")

        sh_rs = await db.execute(
            select(StudentHomework).where(
                StudentHomework.homework_id == homework_id,
                StudentHomework.student_id == student_id,
            )
        )
        sh = sh_rs.scalar_one_or_none()
        if not sh:
            return BaseResponse(
                success=True,
                message="未开始",
                data={"status": "pending", "completion_percentage": 0},
            )

        return BaseResponse(
            success=True,
            message="获取进度成功",
            data={
                "status": _map_status_for_frontend(sh.status or "assigned"),
                "completion_percentage": int(round(sh.completion_percentage or 0.0)),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生作业进度失败: {e}")
        raise HTTPException(status_code=500, detail="获取学生作业进度失败")


@router.get("/{homework_id}", response_model=BaseResponse, summary="获取作业详情")
async def get_homework(
    homework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取作业详情"""
    try:
        result = await db.execute(select(Homework).where(Homework.id == homework_id))
        homework_obj = result.scalar_one_or_none()

        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限校验
        if current_user.user_role.value == "teacher":
            # 教师可以访问：1.自己创建的作业 2.自己有授课关系的班级的作业
            is_creator = homework_obj.creator_teacher_id == current_user.user_id
            has_teaching_relation = False

            if homework_obj.class_id:
                teaching_check = await db.execute(
                    select(Teaching).where(
                        Teaching.class_id == homework_obj.class_id,
                        Teaching.teacher_id == current_user.user_id,
                        Teaching.is_active == True
                    )
                )
                has_teaching_relation = teaching_check.scalar_one_or_none() is not None

            if not (is_creator or has_teaching_relation):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该作业"
                )

        return BaseResponse(
            success=True,
            message="获取作业详情成功",
            data=HomeworkResponse.from_orm(homework_obj).dict(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取作业详情失败"
        )


@router.post("", response_model=BaseResponse, summary="创建作业")
async def create_homework(
    homework_data: HomeworkCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """创建作业（仅教师）"""
    try:
        # 验证班级是否存在且教师有授课关系
        class_obj = None
        if homework_data.class_id:
            result = await db.execute(select(Class).where(Class.id == homework_data.class_id))
            class_obj = result.scalar_one_or_none()
            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="班级不存在",
                )

            # 检查教师是否有此班级的授课关系
            teaching_check = await db.execute(
                select(Teaching).where(
                    Teaching.class_id == homework_data.class_id,
                    Teaching.teacher_id == current_user.user_id,
                    Teaching.is_active == True
                )
            )
            if not teaching_check.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权在该班级布置作业",
                )

        # 验证题目是否存在
        if homework_data.question_ids:
            result = await db.execute(
                select(Question).where(
                    Question.id.in_(homework_data.question_ids),
                    Question.is_active == True,
                )
            )
            questions = result.scalars().all()
            if len(questions) != len(homework_data.question_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部分题目不存在或已禁用",
                )

        # 计算年级（从班级带出）
        derived_grade_id = getattr(class_obj, "grade_id", None) if homework_data.class_id and class_obj else None
        new_homework = Homework(
            title=homework_data.title,
            description=homework_data.description,
            instructions=homework_data.instructions,
            creator_teacher_id=current_user.user_id,
            class_id=homework_data.class_id,
            subject_id=homework_data.subject_id,
            grade_id=derived_grade_id,
            question_ids=homework_data.question_ids,
            due_at=homework_data.due_at,
            max_attempts=homework_data.max_attempts,
        )

        db.add(new_homework)
        await db.commit()
        await db.refresh(new_homework)

        logger.info(f"作业创建成功: {new_homework.id}")

        return BaseResponse(
            success=True,
            message="作业创建成功",
            data={"homework_id": new_homework.id},
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="作业创建失败"
        )


@router.put("/{homework_id}", response_model=BaseResponse, summary="更新作业")
async def update_homework(
    homework_id: str,
    homework_data: HomeworkUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """更新作业信息（仅作业创建教师）"""
    try:
        result = await db.execute(select(Homework).where(Homework.id == homework_id))
        homework_obj = result.scalar_one_or_none()

        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限校验 - 只有作业创建者可以修改作业
        if homework_obj.creator_teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="只有作业创建者可以修改作业"
            )

        # 验证题目是否存在
        if homework_data.question_ids:
            result = await db.execute(
                select(Question).where(
                    Question.id.in_(homework_data.question_ids),
                    Question.is_active == True,
                )
            )
            questions = result.scalars().all()
            if len(questions) != len(homework_data.question_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部分题目不存在或已禁用",
                )

        # 更新字段
        update_data = homework_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(homework_obj, field, value)

        await db.commit()

        logger.info(f"作业更新成功: {homework_id}")

        return BaseResponse(success=True, message="作业更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="作业更新失败"
        )


@router.delete("/{homework_id}", response_model=BaseResponse, summary="删除作业")
async def delete_homework(
    homework_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """删除作业（软删留作 TODO，当前直接删除记录）"""
    try:
        result = await db.execute(select(Homework).where(Homework.id == homework_id))
        homework_obj = result.scalar_one_or_none()

        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限校验 - 只有作业创建者可以删除作业
        if homework_obj.creator_teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="只有作业创建者可以删除作业"
            )

        await db.delete(homework_obj)
        await db.commit()

        logger.info(f"作业删除成功: {homework_id}")

        return BaseResponse(success=True, message="作业删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="作业删除失败"
        )


@router.post("/{homework_id}/publish", response_model=BaseResponse, summary="发布作业")
async def publish_homework(
    homework_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """发布作业（仅作业创建教师）"""
    try:
        result = await db.execute(select(Homework).where(Homework.id == homework_id))
        homework_obj = result.scalar_one_or_none()

        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限校验 - 只有作业创建者可以发布作业
        if homework_obj.creator_teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="只有作业创建者可以发布作业"
            )

        homework_obj.is_published = True
        homework_obj.started_at = datetime.utcnow()

        # 自动分发给班级学生
        if homework_obj.class_id:
            cs_rs = await db.execute(
                select(ClassStudent.student_id).where(
                    ClassStudent.class_id == homework_obj.class_id
                )
            )
            student_ids = [row[0] for row in cs_rs.all()]
            if student_ids:
                existing_rs = await db.execute(
                    select(StudentHomework.student_id).where(
                        StudentHomework.homework_id == homework_id,
                        StudentHomework.student_id.in_(student_ids),
                    )
                )
                existing_ids = {row[0] for row in existing_rs.all()}
                for sid in student_ids:
                    if sid in existing_ids:
                        continue
                    sh = StudentHomework(
                        homework_id=homework_id,
                        student_id=sid,
                        status="assigned",
                        assigned_at=datetime.utcnow(),
                        completion_percentage=0.0,
                        progress={},
                    )
                    db.add(sh)

        await db.commit()

        logger.info(f"作业发布成功: {homework_id}")

        return BaseResponse(success=True, message="作业发布成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业发布失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="作业发布失败"
        )


@router.get("/{homework_id}/progress", response_model=BaseResponse, summary="获取作业进度")
async def get_homework_progress(
    homework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取作业进度"""
    try:
        result = await db.execute(select(Homework).where(Homework.id == homework_id))
        homework_obj = result.scalar_one_or_none()

        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="作业不存在"
            )

        # 权限校验
        if current_user.user_role.value == "teacher":
            # 教师可以查看：1.自己创建的作业 2.自己有授课关系的班级的作业
            is_creator = homework_obj.creator_teacher_id == current_user.user_id
            has_teaching_relation = False

            if homework_obj.class_id:
                teaching_check = await db.execute(
                    select(Teaching).where(
                        Teaching.class_id == homework_obj.class_id,
                        Teaching.teacher_id == current_user.user_id,
                        Teaching.is_active == True
                    )
                )
                has_teaching_relation = teaching_check.scalar_one_or_none() is not None

            if not (is_creator or has_teaching_relation):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此作业"
                )

        total_q = select(func.count(StudentHomework.id)).where(
            StudentHomework.homework_id == homework_id
        )
        completed_q = select(func.count(StudentHomework.id)).where(
            StudentHomework.homework_id == homework_id,
            StudentHomework.status == "completed",
        )
        in_progress_q = select(func.count(StudentHomework.id)).where(
            StudentHomework.homework_id == homework_id,
            StudentHomework.status == "in_progress",
        )
        assigned_q = select(func.count(StudentHomework.id)).where(
            StudentHomework.homework_id == homework_id,
            StudentHomework.status == "assigned",
        )
        avg_rate_q = select(
            func.coalesce(func.avg(StudentHomework.completion_percentage), 0.0)
        ).where(StudentHomework.homework_id == homework_id)

        total = (await db.execute(total_q)).scalar() or 0
        completed = (await db.execute(completed_q)).scalar() or 0
        in_progress = (await db.execute(in_progress_q)).scalar() or 0
        assigned = (await db.execute(assigned_q)).scalar() or 0
        avg_rate = float((await db.execute(avg_rate_q)).scalar() or 0.0)

        progress_data = {
            "total_students": total,
            "completed_students": completed,
            "in_progress_students": in_progress,
            "not_started_students": assigned,
            "average_completion_rate": round(avg_rate, 2),
        }

        return BaseResponse(
            success=True, message="获取作业进度成功", data=progress_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取作业进度失败"
        )

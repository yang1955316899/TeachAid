"""
作业管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger
from datetime import datetime

from app.core.database import get_db
from app.services.auth_service import get_current_teacher, get_current_user, get_current_student
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Homework, Class, Question, StudentHomework
from app.models.pydantic_models import (
    BaseResponse, PaginationQuery, PaginationResponse
)

router = APIRouter(prefix="/homework", tags=["作业管理"])


# 简化的请求/响应模型
class HomeworkCreate:
    """创建作业请求"""
    def __init__(self, title: str, description: str = None, instructions: str = None,
                 class_id: str = None, question_ids: List[str] = None, 
                 due_at: datetime = None, max_attempts: int = 1):
        self.title = title
        self.description = description
        self.instructions = instructions
        self.class_id = class_id
        self.question_ids = question_ids or []
        self.due_at = due_at
        self.max_attempts = max_attempts


class HomeworkUpdate:
    """更新作业请求"""
    def __init__(self, title: str = None, description: str = None, instructions: str = None,
                 question_ids: List[str] = None, due_at: datetime = None, 
                 is_published: bool = None, allow_late_submission: bool = None, 
                 max_attempts: int = None):
        self.title = title
        self.description = description
        self.instructions = instructions
        self.question_ids = question_ids
        self.due_at = due_at
        self.is_published = is_published
        self.allow_late_submission = allow_late_submission
        self.max_attempts = max_attempts


class HomeworkResponse:
    """作业响应"""
    def __init__(self, homework_obj):
        self.id = homework_obj.id
        self.title = homework_obj.title
        self.description = homework_obj.description
        self.instructions = homework_obj.instructions
        self.teacher_id = homework_obj.teacher_id
        self.class_id = homework_obj.class_id
        self.question_ids = homework_obj.question_ids
        self.due_at = homework_obj.due_at.isoformat() if homework_obj.due_at else None
        self.started_at = homework_obj.started_at.isoformat() if homework_obj.started_at else None
        self.is_published = homework_obj.is_published
        self.allow_late_submission = homework_obj.allow_late_submission
        self.max_attempts = homework_obj.max_attempts
        self.created_at = homework_obj.created_at.isoformat() if homework_obj.created_at else None
        self.updated_at = homework_obj.updated_at.isoformat() if homework_obj.updated_at else None
        
        # 关联信息
        self.teacher_name = None
        self.class_name = None
        self.question_count = len(homework_obj.question_ids) if homework_obj.question_ids else 0
        
        if hasattr(homework_obj, 'teacher') and homework_obj.teacher:
            self.teacher_name = homework_obj.teacher.user_full_name
        if hasattr(homework_obj, 'class_obj') and homework_obj.class_obj:
            self.class_name = homework_obj.class_obj.name


class StudentHomeworkResponse:
    """学生作业响应"""
    def __init__(self, student_homework_obj):
        self.id = student_homework_obj.id
        self.homework_id = student_homework_obj.homework_id
        self.student_id = student_homework_obj.student_id
        self.status = student_homework_obj.status
        self.progress = student_homework_obj.progress
        self.completion_percentage = student_homework_obj.completion_percentage
        self.total_chat_sessions = student_homework_obj.total_chat_sessions
        self.total_messages = student_homework_obj.total_messages
        self.assigned_at = student_homework_obj.assigned_at.isoformat() if student_homework_obj.assigned_at else None
        self.started_at = student_homework_obj.started_at.isoformat() if student_homework_obj.started_at else None
        self.completed_at = student_homework_obj.completed_at.isoformat() if student_homework_obj.completed_at else None
        self.submitted_at = student_homework_obj.submitted_at.isoformat() if student_homework_obj.submitted_at else None


@router.get("", response_model=PaginationResponse, summary="获取作业列表")
async def list_homeworks(
    pagination: PaginationQuery = Depends(),
    class_id: Optional[str] = Query(None, description="班级筛选"),
    teacher_id: Optional[str] = Query(None, description="教师筛选"),
    is_published: Optional[bool] = Query(None, description="发布状态"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取作业列表（分页）
    """
    try:
        # 构建查询条件
        conditions = []
        
        # 权限过滤
        if current_user.user_role == "teacher":
            conditions.append(Homework.teacher_id == current_user.user_id)
        elif current_user.user_role == "student":
            # 学生只能看到自己班级的作业（简化处理）
            pass
        
        # 添加筛选条件
        if class_id:
            conditions.append(Homework.class_id == class_id)
        if teacher_id:
            conditions.append(Homework.teacher_id == teacher_id)
        if is_published is not None:
            conditions.append(Homework.is_published == is_published)
        if keyword:
            conditions.append(
                or_(
                    Homework.title.contains(keyword),
                    Homework.description.contains(keyword)
                )
            )
        
        # 查询总数
        count_query = select(func.count(Homework.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = select(Homework)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Homework.created_at.desc()).offset(offset).limit(pagination.size)
        
        result = await db.execute(query)
        homeworks = result.scalars().all()
        
        # 转换为响应模型
        homework_responses = [HomeworkResponse(hw) for hw in homeworks]
        
        return PaginationResponse(
            items=homework_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取作业列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作业列表失败"
        )


@router.get("/{homework_id}", response_model=BaseResponse, summary="获取作业详情")
async def get_homework(
    homework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取作业详情
    """
    try:
        result = await db.execute(
            select(Homework).where(Homework.id == homework_id)
        )
        homework_obj = result.scalar_one_or_none()
        
        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作业不存在"
            )
        
        # 权限检查
        if (current_user.user_role == "teacher" and homework_obj.teacher_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此作业"
            )
        
        return BaseResponse(
            success=True,
            message="获取作业详情成功",
            data=HomeworkResponse(homework_obj).__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作业详情失败"
        )


@router.post("", response_model=BaseResponse, summary="创建作业")
async def create_homework(
    homework_data: HomeworkCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    创建作业（仅教师）
    """
    try:
        # 验证班级是否存在且属于当前教师
        if homework_data.class_id:
            result = await db.execute(
                select(Class).where(
                    Class.id == homework_data.class_id,
                    Class.teacher_id == current_user.user_id
                )
            )
            class_obj = result.scalar_one_or_none()
            if not class_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="班级不存在或无权访问"
                )
        
        # 验证题目是否存在
        if homework_data.question_ids:
            result = await db.execute(
                select(Question).where(
                    Question.id.in_(homework_data.question_ids),
                    Question.is_active == True
                )
            )
            questions = result.scalars().all()
            if len(questions) != len(homework_data.question_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部分题目不存在或已禁用"
                )
        
        new_homework = Homework(
            title=homework_data.title,
            description=homework_data.description,
            instructions=homework_data.instructions,
            teacher_id=current_user.user_id,
            class_id=homework_data.class_id,
            question_ids=homework_data.question_ids,
            due_at=homework_data.due_at,
            max_attempts=homework_data.max_attempts
        )
        
        db.add(new_homework)
        await db.commit()
        await db.refresh(new_homework)
        
        logger.info(f"作业创建成功: {new_homework.id}")
        
        return BaseResponse(
            success=True,
            message="作业创建成功",
            data={"homework_id": new_homework.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作业创建失败"
        )


@router.put("/{homework_id}", response_model=BaseResponse, summary="更新作业")
async def update_homework(
    homework_id: str,
    homework_data: HomeworkUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    更新作业信息（仅作业创建教师）
    """
    try:
        result = await db.execute(
            select(Homework).where(Homework.id == homework_id)
        )
        homework_obj = result.scalar_one_or_none()
        
        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作业不存在"
            )
        
        # 权限检查
        if homework_obj.teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此作业"
            )
        
        # 验证题目是否存在
        if homework_data.question_ids:
            result = await db.execute(
                select(Question).where(
                    Question.id.in_(homework_data.question_ids),
                    Question.is_active == True
                )
            )
            questions = result.scalars().all()
            if len(questions) != len(homework_data.question_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="部分题目不存在或已禁用"
                )
        
        # 更新字段
        update_data = homework_data.__dict__
        for field, value in update_data.items():
            if value is not None:
                setattr(homework_obj, field, value)
        
        await db.commit()
        
        logger.info(f"作业更新成功: {homework_id}")
        
        return BaseResponse(
            success=True,
            message="作业更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作业更新失败"
        )


@router.delete("/{homework_id}", response_model=BaseResponse, summary="删除作业")
async def delete_homework(
    homework_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    删除作业（软删除，仅作业创建教师）
    """
    try:
        result = await db.execute(
            select(Homework).where(Homework.id == homework_id)
        )
        homework_obj = result.scalar_one_or_none()
        
        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作业不存在"
            )
        
        # 权限检查
        if homework_obj.teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此作业"
            )
        
        # 软删除 - 这里需要添加is_active字段到Homework模型
        # 临时解决方案：直接删除记录
        await db.delete(homework_obj)
        await db.commit()
        
        logger.info(f"作业删除成功: {homework_id}")
        
        return BaseResponse(
            success=True,
            message="作业删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作业删除失败"
        )


@router.post("/{homework_id}/publish", response_model=BaseResponse, summary="发布作业")
async def publish_homework(
    homework_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    发布作业（仅作业创建教师）
    """
    try:
        result = await db.execute(
            select(Homework).where(Homework.id == homework_id)
        )
        homework_obj = result.scalar_one_or_none()
        
        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作业不存在"
            )
        
        # 权限检查
        if homework_obj.teacher_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权发布此作业"
            )
        
        homework_obj.is_published = True
        homework_obj.started_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"作业发布成功: {homework_id}")
        
        return BaseResponse(
            success=True,
            message="作业发布成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"作业发布失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="作业发布失败"
        )


@router.get("/{homework_id}/progress", response_model=BaseResponse, summary="获取作业进度")
async def get_homework_progress(
    homework_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取作业进度
    """
    try:
        result = await db.execute(
            select(Homework).where(Homework.id == homework_id)
        )
        homework_obj = result.scalar_one_or_none()
        
        if not homework_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作业不存在"
            )
        
        # 权限检查
        if (current_user.user_role == "teacher" and homework_obj.teacher_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此作业"
            )
        
        # TODO: 实现进度统计逻辑
        progress_data = {
            "total_students": 0,
            "completed_students": 0,
            "in_progress_students": 0,
            "not_started_students": 0,
            "average_completion_rate": 0.0
        }
        
        return BaseResponse(
            success=True,
            message="获取作业进度成功",
            data=progress_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取作业进度失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取作业进度失败"
        )


# 学生作业相关路由
router_student = APIRouter(prefix="/student/homework", tags=["学生作业"])


@router_student.get("", response_model=BaseResponse, summary="获取学生作业列表")
async def get_student_homeworks(
    pagination: PaginationQuery = Depends(),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前学生的作业列表
    """
    try:
        # TODO: 实现学生作业查询逻辑
        # 需要查询学生班级关联和作业分配
        
        return BaseResponse(
            success=True,
            message="获取学生作业列表成功",
            data={"items": [], "total": 0}
        )
        
    except Exception as e:
        logger.error(f"获取学生作业列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取学生作业列表失败"
        )


@router_student.get("/{homework_id}", response_model=BaseResponse, summary="获取学生作业详情")
async def get_student_homework(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    获取学生作业详情
    """
    try:
        # TODO: 实现学生作业详情查询逻辑
        
        return BaseResponse(
            success=True,
            message="获取学生作业详情成功",
            data={}
        )
        
    except Exception as e:
        logger.error(f"获取学生作业详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取学生作业详情失败"
        )


@router_student.post("/{homework_id}/start", response_model=BaseResponse, summary="开始作业")
async def start_homework(
    homework_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    学生开始作业
    """
    try:
        # TODO: 实现学生开始作业逻辑
        
        return BaseResponse(
            success=True,
            message="作业已开始"
        )
        
    except Exception as e:
        logger.error(f"开始作业失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="开始作业失败"
        )
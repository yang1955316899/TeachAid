"""
公开API路由 - 无需认证的接口
"""
from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from loguru import logger

from app.core.database import get_db
from app.models.database_models import Question
from app.models.pydantic_models import BaseResponse, PaginationQuery, PaginationResponse, QuestionResponse

router = APIRouter(prefix="/public", tags=["公开接口"])


@router.get("/questions", response_model=BaseResponse, summary="获取公开题目列表")
async def get_public_questions(
    pagination: PaginationQuery = Depends(),
    subject: Optional[str] = Query(None, description="学科筛选"),
    question_type: Optional[str] = Query(None, description="题目类型筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开题目列表（无需认证）
    """
    try:
        # 构建查询条件
        conditions = [Question.is_active == True, Question.is_public == True]
        
        if subject:
            conditions.append(Question.subject == subject)
        if question_type:
            conditions.append(Question.question_type == question_type)
        if difficulty:
            conditions.append(Question.difficulty == difficulty)
        if keyword:
            conditions.append(
                or_(
                    Question.title.contains(keyword),
                    Question.content.contains(keyword)
                )
            )
        
        # 构建查询
        query = select(Question).where(*conditions)
        
        # 获取总数
        count_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = query.order_by(Question.created_at.desc()).offset(offset).limit(pagination.size)
        
        result = await db.execute(query)
        questions = result.scalars().all()
        
        # 转换为响应格式
        items = []
        for question in questions:
            items.append(QuestionResponse.model_validate(question))
        
        return BaseResponse(
            success=True,
            message="获取题目列表成功",
            data={
                "items": items,
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
                "pages": (total + pagination.size - 1) // pagination.size
            }
        )
        
    except Exception as e:
        logger.error(f"获取公开题目列表失败: {e}")
        return BaseResponse(
            success=False,
            message="获取题目列表失败",
            data=None
        )


@router.get("/questions/{question_id}", response_model=BaseResponse, summary="获取公开题目详情")
async def get_public_question_detail(
    question_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开题目详情（无需认证）
    """
    try:
        result = await db.execute(
            select(Question).where(
                Question.id == question_id,
                Question.is_active == True,
                Question.is_public == True
            )
        )
        question = result.scalar_one_or_none()
        
        if not question:
            return BaseResponse(
                success=False,
                message="题目不存在或无权访问",
                data=None
            )
        
        return BaseResponse(
            success=True,
            message="获取题目详情成功",
            data=QuestionResponse.model_validate(question)
        )
        
    except Exception as e:
        logger.error(f"获取公开题目详情失败: {e}")
        return BaseResponse(
            success=False,
            message="获取题目详情失败",
            data=None
        )
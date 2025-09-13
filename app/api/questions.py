"""
题目管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_user, get_current_teacher
# from app.services.file_processor import FileProcessorService
# from app.core.unified_ai_framework import UnifiedAIFramework
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Question
from app.models.pydantic_models import (
    BaseResponse, PaginationQuery, PaginationResponse,
    QuestionCreate, QuestionUpdate, QuestionResponse,
    AnswerRewriteConfig, AnswerRewriteResponse,
    FileUploadResponse
)

router = APIRouter(prefix="/questions", tags=["题目管理"])

# 服务实例 - 暂时注释AI相关功能
# file_processor = FileProcessorService()
# ai_framework = UnifiedAIFramework()


# 暂时注释AI功能
# @router.post("/upload", response_model=BaseResponse, summary="上传题目文件")
# async def upload_file(
#     file: UploadFile = File(..., description="题目文件（支持图片、PDF、文本）"),
#     current_user: User = Depends(get_current_teacher)
# ):
#     return BaseResponse(success=False, message="AI功能开发中")


# 暂时注释AI功能
# @router.get("/upload/{file_id}/status", response_model=BaseResponse, summary="获取文件处理状态")
# async def get_upload_status(
#     file_id: str,
#     current_user: User = Depends(get_current_user)
# ):
#     return BaseResponse(success=False, message="AI功能开发中")


@router.post("", response_model=BaseResponse, summary="创建题目")
async def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    手动创建题目
    
    - **title**: 题目标题（可选）
    - **content**: 题目内容（必填）
    - **original_answer**: 原始答案（可选）
    - **subject**: 学科
    - **question_type**: 题目类型
    - **difficulty**: 难度等级
    - **knowledge_points**: 知识点列表
    - **tags**: 标签列表
    """
    try:
        question = Question(
            title=question_data.title,
            content=question_data.content,
            original_answer=question_data.original_answer,
            subject=question_data.subject,
            question_type=question_data.question_type,
            difficulty=question_data.difficulty,
            grade_level=question_data.grade_level,
            knowledge_points=question_data.knowledge_points,
            tags=question_data.tags,
            creator_id=current_user.id
        )
        
        db.add(question)
        await db.commit()
        await db.refresh(question)
        
        logger.info(f"题目创建成功: {question.id}")
        
        return BaseResponse(
            success=True,
            message="题目创建成功",
            data={"question_id": question.id}
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"题目创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="题目创建失败"
        )


@router.get("/public", response_model=PaginationResponse, summary="获取公开题目列表")
async def list_public_questions(
    pagination: PaginationQuery = Depends(),
    subject: Optional[str] = Query(None, description="学科筛选"),
    question_type: Optional[str] = Query(None, description="题目类型筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开题目列表（分页，无需登录）
    
    支持按学科、题目类型、难度等条件筛选
    支持关键词搜索题目内容
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
        
        return PaginationResponse(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取公开题目列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取题目列表失败"
        )


@router.get("", response_model=PaginationResponse, summary="获取题目列表")
async def list_questions(
    pagination: PaginationQuery = Depends(),
    subject: Optional[str] = Query(None, description="学科筛选"),
    question_type: Optional[str] = Query(None, description="题目类型筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目列表（分页）
    
    支持按学科、题目类型、难度等条件筛选
    支持关键词搜索题目内容
    """
    try:
        # 构建查询条件
        conditions = [Question.is_active == True]
        
        # 权限过滤：学生只能看公开题目，教师能看自己创建的和公开的
        if current_user.role == "student":
            conditions.append(Question.is_public == True)
        elif current_user.role == "teacher":
            conditions.append(
                (Question.creator_id == current_user.id) | 
                (Question.is_public == True)
            )
        
        # 添加筛选条件
        if subject:
            conditions.append(Question.subject == subject)
        if question_type:
            conditions.append(Question.question_type == question_type)
        if difficulty:
            conditions.append(Question.difficulty == difficulty)
        if keyword:
            conditions.append(Question.content.contains(keyword))
        
        # 查询总数
        count_query = select(func.count(Question.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = (
            select(Question)
            .where(and_(*conditions))
            .order_by(Question.created_at.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        
        result = await db.execute(query)
        questions = result.scalars().all()
        
        # 转换为响应模型
        question_responses = [QuestionResponse.from_orm(q) for q in questions]
        
        return PaginationResponse(
            items=question_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取题目列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取题目列表失败"
        )


@router.get("/{question_id}", response_model=QuestionResponse, summary="获取题目详情")
async def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取题目详情
    
    - **question_id**: 题目ID
    """
    try:
        result = await db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        # 权限检查
        if (current_user.role == "student" and not question.is_public) or \
           (current_user.role == "teacher" and 
            question.creator_id != current_user.id and not question.is_public):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此题目"
            )
        
        return QuestionResponse.from_orm(question)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取题目详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取题目详情失败"
        )


@router.put("/{question_id}", response_model=BaseResponse, summary="更新题目")
async def update_question(
    question_id: str,
    question_data: QuestionUpdate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    更新题目信息
    
    只有题目创建者或管理员可以更新题目
    """
    try:
        result = await db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        # 权限检查
        if current_user.role != "admin" and question.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此题目"
            )
        
        # 更新字段
        update_data = question_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        await db.commit()
        
        logger.info(f"题目更新成功: {question_id}")
        
        return BaseResponse(
            success=True,
            message="题目更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"题目更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="题目更新失败"
        )


# 暂时注释AI改写功能，等AI库安装后再启用
# @router.put("/{question_id}/rewrite", response_model=AnswerRewriteResponse, summary="重新改写答案")
# async def rewrite_answer(...):
#     return BaseResponse(success=False, message="AI改写功能开发中")


@router.delete("/{question_id}", response_model=BaseResponse, summary="删除题目")
async def delete_question(
    question_id: str,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    删除题目（软删除）
    
    只有题目创建者或管理员可以删除题目
    """
    try:
        result = await db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )
        
        # 权限检查
        if current_user.role != "admin" and question.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此题目"
            )
        
        # 软删除
        question.is_active = False
        await db.commit()
        
        logger.info(f"题目删除成功: {question_id}")
        
        return BaseResponse(
            success=True,
            message="题目删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"题目删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="题目删除失败"
        )
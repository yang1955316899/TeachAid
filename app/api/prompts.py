"""
提示词模板管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_teacher, get_current_user
from app.models.auth_models import ConfigUser as User
from app.models.database_models import PromptTemplate
from app.models.pydantic_models import (
    BaseResponse, PaginationQuery, PaginationResponse
)

router = APIRouter(prefix="/prompts", tags=["提示词模板"])


# 简化的请求/响应模型
class PromptTemplateCreate:
    """创建提示词模板请求"""
    def __init__(self, name: str, description: str = None, category: str = "general",
                 subject: str = None, question_type: str = None, system_prompt: str = None,
                 user_prompt_template: str = None, variables: List = None, examples: List = None):
        self.name = name
        self.description = description
        self.category = category
        self.subject = subject
        self.question_type = question_type
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.variables = variables or []
        self.examples = examples or []


class PromptTemplateUpdate:
    """更新提示词模板请求"""
    def __init__(self, name: str = None, description: str = None, category: str = None,
                 subject: str = None, question_type: str = None, system_prompt: str = None,
                 user_prompt_template: str = None, variables: List = None, examples: List = None,
                 is_active: bool = None):
        self.name = name
        self.description = description
        self.category = category
        self.subject = subject
        self.question_type = question_type
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template
        self.variables = variables
        self.examples = examples
        self.is_active = is_active


class PromptTemplateResponse:
    """提示词模板响应"""
    def __init__(self, template_obj):
        self.id = template_obj.id
        self.name = template_obj.name
        self.description = template_obj.description
        self.category = template_obj.category
        self.subject = template_obj.subject
        self.question_type = template_obj.question_type
        self.system_prompt = template_obj.system_prompt
        self.user_prompt_template = template_obj.user_prompt_template
        self.variables = template_obj.variables
        self.examples = template_obj.examples
        self.version = template_obj.version
        self.parent_template_id = template_obj.parent_template_id
        self.usage_count = template_obj.usage_count
        self.avg_quality_score = template_obj.avg_quality_score
        self.creator_id = template_obj.creator_id
        self.is_active = template_obj.is_active
        self.is_builtin = template_obj.is_builtin
        self.created_at = template_obj.created_at.isoformat() if template_obj.created_at else None
        self.updated_at = template_obj.updated_at.isoformat() if template_obj.updated_at else None


@router.get("", response_model=PaginationResponse, summary="获取提示词模板列表")
async def list_prompt_templates(
    pagination: PaginationQuery = Depends(),
    category: Optional[str] = Query(None, description="分类筛选"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    question_type: Optional[str] = Query(None, description="题目类型筛选"),
    is_builtin: Optional[bool] = Query(None, description="是否内置模板"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提示词模板列表（分页）
    """
    try:
        # 构建查询条件
        conditions = [PromptTemplate.is_active == True]
        
        # 添加筛选条件
        if category:
            conditions.append(PromptTemplate.category == category)
        if subject:
            conditions.append(PromptTemplate.subject == subject)
        if question_type:
            conditions.append(PromptTemplate.question_type == question_type)
        if is_builtin is not None:
            conditions.append(PromptTemplate.is_builtin == is_builtin)
        if keyword:
            conditions.append(
                or_(
                    PromptTemplate.name.contains(keyword),
                    PromptTemplate.description.contains(keyword)
                )
            )
        
        # 查询总数
        count_query = select(func.count(PromptTemplate.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = (
            select(PromptTemplate)
            .where(and_(*conditions))
            .order_by(PromptTemplate.created_at.desc())
            .offset(offset)
            .limit(pagination.size)
        )
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # 转换为响应模型
        template_responses = [PromptTemplateResponse(tpl) for tpl in templates]
        
        return PaginationResponse(
            items=template_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取提示词模板列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取提示词模板列表失败"
        )


@router.get("/{template_id}", response_model=BaseResponse, summary="获取提示词模板详情")
async def get_prompt_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取提示词模板详情
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template_obj = result.scalar_one_or_none()
        
        if not template_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词模板不存在"
            )
        
        # 内置模板所有人可访问，自定义模板只有创建者可访问
        if (not template_obj.is_builtin and template_obj.creator_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此模板"
            )
        
        return BaseResponse(
            success=True,
            message="获取提示词模板详情成功",
            data=PromptTemplateResponse(template_obj).__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取提示词模板详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取提示词模板详情失败"
        )


@router.post("", response_model=BaseResponse, summary="创建提示词模板")
async def create_prompt_template(
    template_data: PromptTemplateCreate,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    创建提示词模板（仅教师）
    """
    try:
        new_template = PromptTemplate(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category,
            subject=template_data.subject,
            question_type=template_data.question_type,
            system_prompt=template_data.system_prompt,
            user_prompt_template=template_data.user_prompt_template,
            variables=template_data.variables,
            examples=template_data.examples,
            creator_id=current_user.user_id
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        logger.info(f"提示词模板创建成功: {new_template.id}")
        
        return BaseResponse(
            success=True,
            message="提示词模板创建成功",
            data={"template_id": new_template.id}
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"提示词模板创建失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提示词模板创建失败"
        )


@router.put("/{template_id}", response_model=BaseResponse, summary="更新提示词模板")
async def update_prompt_template(
    template_id: str,
    template_data: PromptTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新提示词模板信息（仅模板创建者）
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template_obj = result.scalar_one_or_none()
        
        if not template_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词模板不存在"
            )
        
        # 权限检查
        if (template_obj.creator_id != current_user.user_id or template_obj.is_builtin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此模板"
            )
        
        # 更新字段
        update_data = template_data.__dict__
        for field, value in update_data.items():
            if value is not None:
                setattr(template_obj, field, value)
        
        await db.commit()
        
        logger.info(f"提示词模板更新成功: {template_id}")
        
        return BaseResponse(
            success=True,
            message="提示词模板更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"提示词模板更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提示词模板更新失败"
        )


@router.delete("/{template_id}", response_model=BaseResponse, summary="删除提示词模板")
async def delete_prompt_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除提示词模板（软删除，仅模板创建者）
    """
    try:
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        template_obj = result.scalar_one_or_none()
        
        if not template_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="提示词模板不存在"
            )
        
        # 权限检查
        if (template_obj.creator_id != current_user.user_id or template_obj.is_builtin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此模板"
            )
        
        # 软删除
        template_obj.is_active = False
        await db.commit()
        
        logger.info(f"提示词模板删除成功: {template_id}")
        
        return BaseResponse(
            success=True,
            message="提示词模板删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"提示词模板删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提示词模板删除失败"
        )


@router.get("/public/templates", response_model=BaseResponse, summary="获取公开提示词模板")
async def get_public_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    limit: int = Query(10, description="返回数量限制"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开的提示词模板（无需认证）
    """
    try:
        # 构建查询条件
        conditions = [
            PromptTemplate.is_active == True,
            PromptTemplate.is_builtin == True  # 只返回内置模板
        ]
        
        if category:
            conditions.append(PromptTemplate.category == category)
        if subject:
            conditions.append(PromptTemplate.subject == subject)
        
        # 查询模板
        query = (
            select(PromptTemplate)
            .where(and_(*conditions))
            .order_by(PromptTemplate.usage_count.desc())
            .limit(limit)
        )
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        # 转换为响应模型
        template_responses = [PromptTemplateResponse(tpl) for tpl in templates]
        
        return BaseResponse(
            success=True,
            message="获取公开模板成功",
            data={
                "templates": template_responses,
                "total": len(template_responses)
            }
        )
        
    except Exception as e:
        logger.error(f"获取公开提示词模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取公开提示词模板失败"
        )
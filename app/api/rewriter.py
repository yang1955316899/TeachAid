"""
AI答案改写API端点
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from loguru import logger

from app.services.ai_answer_rewriter import (
    answer_rewriter, RewriteContext, RewriteStyle, DifficultyLevel
)
from app.services.auth_service import get_current_user
from app.models.auth_models import ConfigUser
from app.core.config import settings

router = APIRouter(prefix="/rewriter", tags=["AI答案改写"])


@router.post("/rewrite", summary="改写单个答案")
async def rewrite_answer(
    question: str,
    original_answer: str,
    subject: str = "通用",
    question_type: str = "解答题",
    style: RewriteStyle = RewriteStyle.GUIDED,
    difficulty: DifficultyLevel = DifficultyLevel.MIDDLE_SCHOOL,
    keywords: Optional[List[str]] = None,
    learning_objectives: Optional[List[str]] = None,
    custom_requirements: Optional[str] = None,
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    改写单个答案
    
    Args:
        question: 题目内容
        original_answer: 原始答案
        subject: 学科
        question_type: 题目类型
        style: 改写风格
        difficulty: 难度等级
        keywords: 关键词
        learning_objectives: 学习目标
        custom_requirements: 自定义要求
    """
    try:
        context = RewriteContext(
            question=question,
            original_answer=original_answer,
            subject=subject,
            question_type=question_type,
            style=style,
            difficulty=difficulty,
            keywords=keywords or [],
            learning_objectives=learning_objectives or [],
            student_level=getattr(current_user, 'level', None),
            custom_requirements=custom_requirements
        )
        
        result = await answer_rewriter.rewrite_answer(context)
        
        if result.error_message:
            raise HTTPException(status_code=500, detail=result.error_message)
        
        return {
            "success": True,
            "data": {
                "rewritten_answer": result.rewritten_answer,
                "quality_score": result.quality_score,
                "processing_time": result.processing_time,
                "cost": result.cost,
                "model_used": result.model_used,
                "cache_hit": result.cache_hit,
                "style_applied": result.style_applied,
                "suggestions": result.suggestions,
                "follow_up_questions": result.follow_up_questions,
                "knowledge_points": result.knowledge_points
            }
        }
        
    except Exception as e:
        logger.error(f"答案改写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-rewrite", summary="批量改写答案")
async def batch_rewrite_answers(
    requests: List[dict],
    background_tasks: BackgroundTasks,
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    批量改写答案
    
    Args:
        requests: 批量改写请求列表
        background_tasks: 后台任务
    """
    try:
        if len(requests) > 50:  # 限制批量大小
            raise HTTPException(status_code=400, detail="批量处理最多支持50个请求")
        
        contexts = []
        for req in requests:
            context = RewriteContext(
                question=req["question"],
                original_answer=req["original_answer"],
                subject=req.get("subject", "通用"),
                question_type=req.get("question_type", "解答题"),
                style=RewriteStyle(req.get("style", "guided")),
                difficulty=DifficultyLevel(req.get("difficulty", "middle_school")),
                keywords=req.get("keywords", []),
                learning_objectives=req.get("learning_objectives", []),
                student_level=getattr(current_user, 'level', None),
                custom_requirements=req.get("custom_requirements")
            )
            contexts.append(context)
        
        results = await answer_rewriter.batch_rewrite(contexts)
        
        return {
            "success": True,
            "data": [
                {
                    "rewritten_answer": result.rewritten_answer,
                    "quality_score": result.quality_score,
                    "processing_time": result.processing_time,
                    "cost": result.cost,
                    "model_used": result.model_used,
                    "cache_hit": result.cache_hit,
                    "style_applied": result.style_applied,
                    "suggestions": result.suggestions,
                    "follow_up_questions": result.follow_up_questions,
                    "knowledge_points": result.knowledge_points,
                    "error_message": result.error_message
                }
                for result in results
            ],
            "summary": {
                "total_requests": len(results),
                "successful": sum(1 for r in results if not r.error_message),
                "failed": sum(1 for r in results if r.error_message),
                "total_cost": sum(r.cost for r in results),
                "average_quality": sum(r.quality_score for r in results if not r.error_message) / max(1, sum(1 for r in results if not r.error_message))
            }
        }
        
    except Exception as e:
        logger.error(f"批量改写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/styles", summary="获取可用的改写风格")
async def get_rewrite_styles():
    """获取所有可用的改写风格"""
    return {
        "success": True,
        "data": [
            {
                "value": style.value,
                "name": style.value,
                "description": _get_style_description(style)
            }
            for style in RewriteStyle
        ]
    }


@router.get("/difficulties", summary="获取可用的难度等级")
async def get_difficulty_levels():
    """获取所有可用的难度等级"""
    return {
        "success": True,
        "data": [
            {
                "value": difficulty.value,
                "name": difficulty.value,
                "description": _get_difficulty_description(difficulty)
            }
            for difficulty in DifficultyLevel
        ]
    }


@router.get("/statistics", summary="获取改写统计信息")
async def get_rewrite_statistics(
    time_range: int = 7,
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    获取改写统计信息
    
    Args:
        time_range: 时间范围（天数）
    """
    try:
        stats = await answer_rewriter.get_rewrite_statistics(time_range)
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="健康检查")
async def health_check():
    """AI答案改写引擎健康检查"""
    try:
        health = await answer_rewriter.health_check()
        
        return {
            "success": True,
            "data": health
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", summary="预览改写效果")
async def preview_rewrite(
    question: str,
    original_answer: str,
    style: RewriteStyle = RewriteStyle.GUIDED,
    subject: str = "通用",
    current_user: ConfigUser = Depends(get_current_user)
):
    """
    预览改写效果（只返回部分结果，用于快速预览）
    """
    try:
        # 使用简化的上下文进行快速预览
        context = RewriteContext(
            question=question[:200],  # 限制长度
            original_answer=original_answer[:500],  # 限制长度
            subject=subject,
            style=style,
            difficulty=DifficultyLevel.MIDDLE_SCHOOL
        )
        
        result = await answer_rewriter.rewrite_answer(context)
        
        # 只返回核心信息
        return {
            "success": True,
            "data": {
                "preview": result.rewritten_answer[:300] + "..." if len(result.rewritten_answer) > 300 else result.rewritten_answer,
                "quality_score": result.quality_score,
                "style_applied": result.style_applied,
                "estimated_cost": result.cost
            }
        }
        
    except Exception as e:
        logger.error(f"预览改写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_style_description(style: RewriteStyle) -> str:
    """获取风格描述"""
    descriptions = {
        RewriteStyle.GUIDED: "引导式：通过问题引导学生思考，培养独立解决问题的能力",
        RewriteStyle.STEP_BY_STEP: "分步骤：将复杂问题分解为清晰的步骤，便于理解和掌握",
        RewriteStyle.INTERACTIVE: "互动式：设计互动环节，增加学习参与度和趣味性",
        RewriteStyle.SUMMARY: "总结式：提炼核心要点，适合快速复习和知识梳理",
        RewriteStyle.DETAILED: "详细解析：深入分析原理和方法，适合深度学习"
    }
    return descriptions.get(style, "未知风格")


def _get_difficulty_description(difficulty: DifficultyLevel) -> str:
    """获取难度描述"""
    descriptions = {
        DifficultyLevel.ELEMENTARY: "小学：使用简单易懂的语言和概念",
        DifficultyLevel.MIDDLE_SCHOOL: "初中：适中的复杂度和专业术语",
        DifficultyLevel.HIGH_SCHOOL: "高中：较复杂的概念和深入分析",
        DifficultyLevel.UNIVERSITY: "大学：专业术语和理论分析",
        DifficultyLevel.PROFESSIONAL: "专业级：高级概念和专业分析"
    }
    return descriptions.get(difficulty, "未知难度")
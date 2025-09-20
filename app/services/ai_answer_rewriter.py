"""
AI答案改写引擎 - 核心功能实现
整合UnifiedAIFramework、PromptTemplateService、IntelligentCacheService等
"""
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta

from loguru import logger
from pydantic import BaseModel

from app.core.unified_ai_framework import TaskComplexity
from app.services.intelligent_cache_service import IntelligentCacheService
from app.services.prompt_template_service import PromptTemplateService
from app.models.pydantic_models import (
    AnswerRewriteRequest, AnswerRewriteResponse, 
    RewriteQuality, ProcessingStatus
)


class RewriteStyle(str, Enum):
    """改写风格"""
    GUIDED = "guided"  # 引导式
    STEP_BY_STEP = "step_by_step"  # 分步骤
    INTERACTIVE = "interactive"  # 互动式
    SUMMARY = "summary"  # 总结式
    DETAILED = "detailed"  # 详细解析


class DifficultyLevel(str, Enum):
    """难度等级"""
    ELEMENTARY = "elementary"  # 小学
    MIDDLE_SCHOOL = "middle_school"  # 初中
    HIGH_SCHOOL = "high_school"  # 高中
    UNIVERSITY = "university"  # 大学
    PROFESSIONAL = "professional"  # 专业级


class RewriteContext(BaseModel):
    """改写上下文"""
    question: str
    original_answer: str
    subject: str = "通用"
    question_type: str = "解答题"
    style: RewriteStyle = RewriteStyle.GUIDED
    difficulty: DifficultyLevel = DifficultyLevel.MIDDLE_SCHOOL
    keywords: List[str] = []
    learning_objectives: List[str] = []
    student_level: Optional[str] = None
    custom_requirements: Optional[str] = None


class RewriteResult(BaseModel):
    """改写结果"""
    rewritten_answer: str
    quality_score: int
    processing_time: float
    cost: float
    model_used: str
    cache_hit: bool
    style_applied: RewriteStyle
    suggestions: List[str] = []
    follow_up_questions: List[str] = []
    knowledge_points: List[str] = []
    error_message: Optional[str] = None


class AIAnswerRewriter:
    """AI答案改写引擎"""
    
    def __init__(self):
        # 核心服务依赖 - 延迟导入避免循环依赖
        from app.core.unified_ai_framework import unified_ai
        self.ai_framework = unified_ai
        self.cache_service = IntelligentCacheService()
        self.prompt_service = PromptTemplateService()
        
        # 质量阈值配置
        self.quality_thresholds = {
            RewriteStyle.GUIDED: 7,
            RewriteStyle.STEP_BY_STEP: 8,
            RewriteStyle.INTERACTIVE: 7,
            RewriteStyle.SUMMARY: 6,
            RewriteStyle.DETAILED: 8
        }
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # 成本控制
        self.max_cost_per_request = 0.50  # $0.50 per request
        
    async def rewrite_answer(self, context: RewriteContext) -> RewriteResult:
        """主要的答案改写方法"""
        start_time = time.time()
        total_cost = 0.0
        
        try:
            logger.info(f"开始改写答案: {context.subject} - {context.style}")
            
            # 1. 检查缓存
            cache_key = self._generate_cache_key(context)
            cached_result = await self.cache_service.get_cached_response(
                cache_key, 
                model="rewriter",
                enable_semantic=True
            )
            
            if cached_result:
                logger.info("使用缓存结果")
                return RewriteResult(
                    rewritten_answer=cached_result["content"],
                    quality_score=cached_result.get("quality_score", 8),
                    processing_time=time.time() - start_time,
                    cost=0.0,
                    model_used=cached_result.get("model", "cached"),
                    cache_hit=True,
                    style_applied=context.style,
                    suggestions=cached_result.get("suggestions", []),
                    follow_up_questions=cached_result.get("follow_up_questions", []),
                    knowledge_points=cached_result.get("knowledge_points", [])
                )
            
            # 2. 获取适合的提示词模板
            template = await self._get_rewrite_template(context)
            
            # 3. 构建改写请求
            messages = await self._build_rewrite_messages(context, template)
            
            # 4. 执行改写（带重试机制）
            rewrite_result = await self._execute_rewrite_with_retry(
                messages, context, total_cost
            )
            
            # 5. 质量评估
            quality_score = await self._assess_quality(
                context, rewrite_result["content"]
            )
            
            # 6. 生成补充内容
            suggestions, follow_up_questions, knowledge_points = await self._generate_supplements(
                context, rewrite_result["content"]
            )
            
            # 7. 缓存结果
            cache_data = {
                "content": rewrite_result["content"],
                "quality_score": quality_score,
                "model": rewrite_result["model"],
                "suggestions": suggestions,
                "follow_up_questions": follow_up_questions,
                "knowledge_points": knowledge_points,
                "style": context.style,
                "subject": context.subject
            }
            
            await self.cache_service.cache_response(
                cache_key,
                cache_data,
                model="rewriter",
                cost=rewrite_result["cost"],
                ttl=86400  # 24小时
            )
            
            processing_time = time.time() - start_time
            
            result = RewriteResult(
                rewritten_answer=rewrite_result["content"],
                quality_score=quality_score,
                processing_time=processing_time,
                cost=rewrite_result["cost"],
                model_used=rewrite_result["model"],
                cache_hit=False,
                style_applied=context.style,
                suggestions=suggestions,
                follow_up_questions=follow_up_questions,
                knowledge_points=knowledge_points
            )
            
            logger.info(f"改写完成: 质量分数 {quality_score}, 耗时 {processing_time:.2f}s, 成本 ${rewrite_result['cost']:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"答案改写失败: {e}")
            return RewriteResult(
                rewritten_answer="",
                quality_score=0,
                processing_time=time.time() - start_time,
                cost=total_cost,
                model_used="error",
                cache_hit=False,
                style_applied=context.style,
                error_message=str(e)
            )
    
    async def batch_rewrite(self, contexts: List[RewriteContext]) -> List[RewriteResult]:
        """批量改写答案"""
        logger.info(f"开始批量改写: {len(contexts)} 个答案")
        
        # 并发处理，但限制并发数量避免API限制
        semaphore = asyncio.Semaphore(5)  # 最多5个并发
        
        async def process_single(context):
            async with semaphore:
                return await self.rewrite_answer(context)
        
        results = await asyncio.gather(
            *[process_single(context) for context in contexts],
            return_exceptions=True
        )
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量处理第 {i+1} 项失败: {result}")
                processed_results.append(RewriteResult(
                    rewritten_answer="",
                    quality_score=0,
                    processing_time=0,
                    cost=0,
                    model_used="error",
                    cache_hit=False,
                    style_applied=contexts[i].style,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        total_cost = sum(r.cost for r in processed_results)
        success_count = sum(1 for r in processed_results if not r.error_message)
        
        logger.info(f"批量改写完成: {success_count}/{len(contexts)} 成功, 总成本: ${total_cost:.4f}")
        return processed_results
    
    async def _get_rewrite_template(self, context: RewriteContext) -> Dict[str, str]:
        """获取改写模板"""
        # 根据学科和风格选择模板
        template_name = f"{context.subject.lower()}_{context.style.value}"
        
        # 首先尝试专门的模板
        template = await self.prompt_service.get_template(template_name)
        
        if not template:
            # 回退到通用模板
            fallback_name = f"general_{context.style.value}"
            template = await self.prompt_service.get_template(fallback_name)
            
        if not template:
            # 使用默认的引导式模板
            template = await self.prompt_service.get_template("general_guided")
            
        return template or {
            "system_prompt": "你是一位资深教师，请将标准答案改写为引导式教学内容。",
            "user_prompt_template": "题目：{question}\n答案：{answer}\n请改写为引导式内容。"
        }
    
    async def _build_rewrite_messages(self, context: RewriteContext, template: Dict[str, str]) -> List[Dict[str, str]]:
        """构建改写消息"""
        # 系统提示词
        system_prompt = template["system_prompt"]
        
        # 添加风格和难度特定指令
        style_instruction = self._get_style_instruction(context.style)
        difficulty_instruction = self._get_difficulty_instruction(context.difficulty)
        
        enhanced_system_prompt = f"""{system_prompt}

改写风格要求：{style_instruction}

目标难度：{difficulty_instruction}

额外要求：
- 保持答案的准确性和完整性
- 适应 {context.difficulty} 水平的学生
- 融入 {context.subject} 学科特点
"""
        
        if context.custom_requirements:
            enhanced_system_prompt += f"\n特殊要求：{context.custom_requirements}"
            
        # 用户提示词
        user_content = template["user_prompt_template"].format(
            question=context.question,
            answer=context.original_answer,
            subject=context.subject,
            style=context.style.value,
            keywords=", ".join(context.keywords) if context.keywords else "无",
            objectives=", ".join(context.learning_objectives) if context.learning_objectives else "无"
        )
        
        return [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _get_style_instruction(self, style: RewriteStyle) -> str:
        """获取风格指令"""
        instructions = {
            RewriteStyle.GUIDED: "采用引导式教学方法，通过问题引导学生思考，不直接给出答案。",
            RewriteStyle.STEP_BY_STEP: "将解答过程分解为清晰的步骤，每步都有详细说明。",
            RewriteStyle.INTERACTIVE: "设计互动性强的内容，包含思考题和实践环节。",
            RewriteStyle.SUMMARY: "提供简洁的要点总结，突出核心概念。",
            RewriteStyle.DETAILED: "提供详细的解析，包含原理说明和扩展知识。"
        }
        return instructions.get(style, "采用适合的教学方式进行改写。")
    
    def _get_difficulty_instruction(self, difficulty: DifficultyLevel) -> str:
        """获取难度指令"""
        instructions = {
            DifficultyLevel.ELEMENTARY: "使用简单易懂的语言，适合小学生理解。",
            DifficultyLevel.MIDDLE_SCHOOL: "使用中等复杂度的语言和概念，适合初中生。",
            DifficultyLevel.HIGH_SCHOOL: "可以使用较复杂的概念，适合高中生水平。",
            DifficultyLevel.UNIVERSITY: "使用专业术语和深入分析，适合大学生。",
            DifficultyLevel.PROFESSIONAL: "使用专业级别的分析和术语。"
        }
        return instructions.get(difficulty, "使用适合的难度水平。")
    
    async def _execute_rewrite_with_retry(self, messages: List[Dict], context: RewriteContext, total_cost: float) -> Dict[str, Any]:
        """执行改写（带重试机制）"""
        for attempt in range(self.max_retries):
            try:
                # 根据复杂度选择模型
                complexity = self._determine_complexity(context)
                
                # 调用AI框架
                result = await self.ai_framework.call_llm_with_fallback(
                    messages=messages,
                    model_type="rewrite",
                    complexity=complexity,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                if result["success"]:
                    return {
                        "content": result["content"],
                        "model": result["model_used"],
                        "cost": result["cost"]
                    }
                else:
                    logger.warning(f"改写尝试 {attempt + 1} 失败: {result.get('error_message')}")
                    
            except Exception as e:
                logger.error(f"改写尝试 {attempt + 1} 异常: {e}")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception("所有改写尝试都失败了")
    
    def _determine_complexity(self, context: RewriteContext) -> TaskComplexity:
        """确定任务复杂度"""
        # 根据风格、难度、学科等因素确定复杂度
        complexity_score = 0
        
        # 风格复杂度
        style_scores = {
            RewriteStyle.SUMMARY: 1,
            RewriteStyle.GUIDED: 2,
            RewriteStyle.STEP_BY_STEP: 2,
            RewriteStyle.INTERACTIVE: 3,
            RewriteStyle.DETAILED: 3
        }
        complexity_score += style_scores.get(context.style, 2)
        
        # 难度复杂度
        difficulty_scores = {
            DifficultyLevel.ELEMENTARY: 1,
            DifficultyLevel.MIDDLE_SCHOOL: 2,
            DifficultyLevel.HIGH_SCHOOL: 2,
            DifficultyLevel.UNIVERSITY: 3,
            DifficultyLevel.PROFESSIONAL: 3
        }
        complexity_score += difficulty_scores.get(context.difficulty, 2)
        
        # 学科复杂度
        complex_subjects = ["数学", "物理", "化学", "生物"]
        if context.subject in complex_subjects:
            complexity_score += 1
            
        # 自定义要求增加复杂度
        if context.custom_requirements:
            complexity_score += 1
            
        # 映射到枚举
        if complexity_score <= 3:
            return TaskComplexity.LOW
        elif complexity_score <= 5:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.HIGH
    
    async def _assess_quality(self, context: RewriteContext, rewritten_answer: str) -> int:
        """评估改写质量"""
        assessment_prompt = f"""
        请评估以下答案改写的质量（1-10分）：
        
        原题目：{context.question}
        原答案：{context.original_answer}
        改写答案：{rewritten_answer}
        
        评估标准：
        1. 教学启发性（是否引导学生思考）
        2. 内容准确性（是否保持原答案正确性）
        3. 语言适合度（是否适合目标学生群体）
        4. 结构清晰度（是否逻辑清晰）
        5. 风格匹配度（是否符合 {context.style} 风格）
        
        只返回1-10的整数分数。
        """
        
        try:
            result = await self.ai_framework.call_llm_with_fallback(
                messages=[{"role": "user", "content": assessment_prompt}],
                model_type="chat",
                complexity=TaskComplexity.LOW,
                temperature=0.3,
                max_tokens=10
            )
            
            if result["success"]:
                score_text = result["content"].strip()
                score = int(''.join(filter(str.isdigit, score_text))[:2] or 5)
                return min(max(score, 1), 10)
                
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            
        return 5  # 默认中等质量
    
    async def _generate_supplements(self, context: RewriteContext, rewritten_answer: str) -> Tuple[List[str], List[str], List[str]]:
        """生成补充内容：建议、后续问题、知识点"""
        supplement_prompt = f"""
        基于以下改写后的答案，生成补充学习内容：
        
        题目：{context.question}
        学科：{context.subject}
        改写答案：{rewritten_answer}
        
        请生成：
        1. 3个学习建议
        2. 3个后续思考问题
        3. 相关知识点列表
        
        以JSON格式返回：
        {{
            "suggestions": ["建议1", "建议2", "建议3"],
            "follow_up_questions": ["问题1", "问题2", "问题3"],
            "knowledge_points": ["知识点1", "知识点2", "知识点3"]
        }}
        """
        
        try:
            result = await self.ai_framework.call_llm_with_fallback(
                messages=[{"role": "user", "content": supplement_prompt}],
                model_type="chat",
                complexity=TaskComplexity.LOW,
                temperature=0.6,
                max_tokens=500
            )
            
            if result["success"]:
                import json
                data = json.loads(result["content"])
                return (
                    data.get("suggestions", []),
                    data.get("follow_up_questions", []),
                    data.get("knowledge_points", [])
                )
                
        except Exception as e:
            logger.warning(f"补充内容生成失败: {e}")
            
        # 默认返回
        return (
            ["多练习类似题目", "理解核心概念", "关注解题方法"],
            ["还有其他解法吗？", "如何举一反三？", "易错点在哪里？"],
            [context.subject]
        )
    
    def _generate_cache_key(self, context: RewriteContext) -> str:
        """生成缓存键"""
        import hashlib
        
        content = f"{context.question}_{context.original_answer}_{context.subject}_{context.style}_{context.difficulty}"
        if context.custom_requirements:
            content += f"_{context.custom_requirements}"
            
        return f"rewriter_{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_rewrite_statistics(self, time_range: int = 7) -> Dict[str, Any]:
        """获取改写统计信息"""
        try:
            stats = await self.cache_service.get_usage_statistics(
                time_range_days=time_range,
                model_filter="rewriter"
            )
            
            return {
                "total_rewrites": stats.get("total_requests", 0),
                "cache_hit_rate": stats.get("cache_hit_rate", 0),
                "total_cost": stats.get("total_cost", 0),
                "average_quality": stats.get("average_quality", 0),
                "popular_subjects": stats.get("popular_subjects", []),
                "popular_styles": stats.get("popular_styles", [])
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试各个组件
            ai_health = await self.ai_framework.health_check()
            cache_health = await self.cache_service.health_check()
            prompt_health = await self.prompt_service.health_check()
            
            return {
                "status": "healthy" if all([
                    ai_health.get("status") == "healthy",
                    cache_health.get("status") == "healthy", 
                    prompt_health.get("status") == "healthy"
                ]) else "unhealthy",
                "components": {
                    "ai_framework": ai_health,
                    "cache_service": cache_health,
                    "prompt_service": prompt_health
                },
                "version": "1.0.0"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# 全局实例
answer_rewriter = AIAnswerRewriter()
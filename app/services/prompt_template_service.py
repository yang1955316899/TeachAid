"""
提示词模板服务 - PromptTemplateService
支持分层提示词管理、版本控制和效果测试
"""
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.database_models import PromptTemplate
from app.core.unified_ai_framework import TaskComplexity

logger = logging.getLogger(__name__)

@dataclass
class TemplateVariable:
    """模板变量定义"""
    name: str
    type: str  # string, int, float, list, dict
    description: str
    default_value: Any = None
    required: bool = True
    validation_rule: Optional[str] = None

@dataclass
class TemplateExample:
    """模板示例"""
    input_variables: Dict[str, Any]
    expected_output: str
    description: str

@dataclass
class RenderedTemplate:
    """渲染后的模板"""
    system_prompt: str
    user_prompt: str
    messages: List[Dict[str, str]]
    variables_used: Dict[str, Any]

class PromptTemplateService:
    """提示词模板服务"""
    
    def __init__(self):
        """初始化提示词模板服务"""
        
        # 内置模板缓存
        self.builtin_templates: Dict[str, Dict] = {}
        
        # 模板性能统计
        self.template_stats: Dict[str, Dict] = {}
        
        # 初始化内置模板
        self._load_builtin_templates()
        
        logger.info("PromptTemplateService 初始化完成")

    def _load_builtin_templates(self):
        """加载内置模板"""
        
        self.builtin_templates = {
            # 数学题改写模板
            "math_calculation": {
                "id": "math_calculation",
                "name": "数学计算题改写",
                "category": "subject",
                "subject": "数学",
                "question_type": "计算题",
                "system_prompt": """你是一位资深数学教师，擅长将复杂的数学解答转换为启发式的教学内容。

改写原则：
1. 保留原答案的正确性和完整性
2. 将直接的计算步骤转换为引导式问题
3. 增加思路解析和方法总结
4. 突出易错点和注意事项
5. 适当添加变式练习建议

改写风格：
- 语言亲切，符合{grade_level}学生的认知水平
- 逻辑清晰，步骤分明
- 富有启发性，避免直接给出答案
- 注重数学思维的培养""",
                "user_prompt_template": """
原题目：{question}
原答案：{answer}
学生年级：{grade_level}
改写风格：{style}

请将上述数学题答案改写为更适合教学的启发式内容。
""",
                "variables": [
                    TemplateVariable("question", "string", "原题目内容", required=True),
                    TemplateVariable("answer", "string", "原答案内容", required=True),
                    TemplateVariable("grade_level", "string", "学生年级", default_value="初中"),
                    TemplateVariable("style", "string", "改写风格", default_value="引导式")
                ],
                "examples": [
                    TemplateExample(
                        input_variables={
                            "question": "求解方程 2x + 3 = 11",
                            "answer": "2x = 11 - 3 = 8，所以 x = 4",
                            "grade_level": "初一",
                            "style": "引导式"
                        },
                        expected_output="让我们一起来解这个方程...",
                        description="简单一元一次方程"
                    )
                ]
            },
            
            # 语文阅读理解模板
            "chinese_reading": {
                "id": "chinese_reading",
                "name": "语文阅读理解改写",
                "category": "subject",
                "subject": "语文",
                "question_type": "阅读理解",
                "system_prompt": """你是一位资深语文教师，擅长将阅读理解答案转换为启发式教学内容。

改写原则：
1. 保持答案的准确性和完整性
2. 引导学生从文本中寻找答案依据
3. 培养学生的阅读理解能力和思维方法
4. 注重情感体验和价值观引导
5. 适合{grade_level}学生的语言表达能力

改写风格：
- 循循善诱，启发思考
- 联系生活实际
- 注重文学鉴赏能力培养""",
                "user_prompt_template": """
阅读材料：{reading_material}
题目：{question}
原答案：{answer}
学生年级：{grade_level}

请将答案改写为引导学生思考的教学内容。
""",
                "variables": [
                    TemplateVariable("reading_material", "string", "阅读材料", required=True),
                    TemplateVariable("question", "string", "题目内容", required=True),
                    TemplateVariable("answer", "string", "原答案", required=True),
                    TemplateVariable("grade_level", "string", "学生年级", default_value="初中")
                ],
                "examples": []
            },
            
            # 英语语法模板
            "english_grammar": {
                "id": "english_grammar",
                "name": "英语语法题改写",
                "category": "subject",
                "subject": "英语",
                "question_type": "语法题",
                "system_prompt": """You are an experienced English teacher who excels at converting grammar exercise answers into engaging teaching content.

Rewriting principles:
1. Maintain accuracy and completeness of the original answer
2. Transform direct answers into guided questions
3. Add explanation of grammar rules and usage patterns
4. Highlight common mistakes and key points
5. Suitable for {grade_level} students

Rewriting style:
- Clear and encouraging language
- Step-by-step guidance
- Focus on practical usage
- Build confidence in English learning""",
                "user_prompt_template": """
Original Question: {question}
Original Answer: {answer}
Student Level: {grade_level}
Grammar Point: {grammar_point}

Please rewrite this answer into more engaging teaching content.
""",
                "variables": [
                    TemplateVariable("question", "string", "原题目", required=True),
                    TemplateVariable("answer", "string", "原答案", required=True),
                    TemplateVariable("grade_level", "string", "学生水平", default_value="middle school"),
                    TemplateVariable("grammar_point", "string", "语法点", required=False)
                ],
                "examples": []
            },
            
            # 物理实验模板
            "physics_experiment": {
                "id": "physics_experiment",
                "name": "物理实验题改写",
                "category": "subject",
                "subject": "物理",
                "question_type": "实验题",
                "system_prompt": """你是一位资深物理教师，擅长将实验题答案转换为启发式教学内容。

改写原则：
1. 保持实验原理和结论的准确性
2. 引导学生思考实验现象背后的物理规律
3. 强调实验方法和科学思维
4. 注重理论与实际的结合
5. 适合{grade_level}学生的认知水平

改写风格：
- 注重实验探究过程
- 培养科学思维方法
- 联系生活中的物理现象""",
                "user_prompt_template": """
实验题目：{question}
原答案：{answer}
学生年级：{grade_level}
涉及概念：{physics_concepts}

请将答案改写为引导学生理解物理规律的教学内容。
""",
                "variables": [
                    TemplateVariable("question", "string", "实验题目", required=True),
                    TemplateVariable("answer", "string", "原答案", required=True),
                    TemplateVariable("grade_level", "string", "学生年级", default_value="初中"),
                    TemplateVariable("physics_concepts", "list", "涉及的物理概念", default_value=[])
                ],
                "examples": []
            },
            
            # 通用改写模板
            "general_rewrite": {
                "id": "general_rewrite",
                "name": "通用题目改写",
                "category": "general",
                "subject": "通用",
                "question_type": "解答题",
                "system_prompt": """你是一位经验丰富的教师，擅长将标准答案转换为启发式教学内容。

改写原则：
1. 保持答案的正确性和完整性
2. 将直接答案转换为引导式问题和提示
3. 增加思维过程的展示
4. 适合{grade_level}学生的认知水平
5. 营造积极的学习氛围

改写风格：
- 语言亲切自然
- 逐步引导思考
- 鼓励学生参与
- 注重能力培养""",
                "user_prompt_template": """
题目：{question}
原答案：{answer}
学科：{subject}
学生年级：{grade_level}

请将答案改写为更适合教学的引导式内容。
""",
                "variables": [
                    TemplateVariable("question", "string", "题目内容", required=True),
                    TemplateVariable("answer", "string", "原答案", required=True),
                    TemplateVariable("subject", "string", "学科", default_value="通用"),
                    TemplateVariable("grade_level", "string", "学生年级", default_value="初中")
                ],
                "examples": []
            }
        }
        
        logger.info(f"加载了 {len(self.builtin_templates)} 个内置模板")

    async def create_template(self, 
                            template_data: Dict[str, Any],
                            creator_id: str,
                            db: AsyncSession) -> PromptTemplate:
        """创建新的提示词模板"""
        
        template_id = str(uuid.uuid4())
        
        template = PromptTemplate(
            id=template_id,
            name=template_data["name"],
            description=template_data.get("description"),
            category=template_data.get("category", "general"),
            subject=template_data.get("subject"),
            question_type=template_data.get("question_type"),
            system_prompt=template_data.get("system_prompt"),
            user_prompt_template=template_data["user_prompt_template"],
            variables=template_data.get("variables", []),
            examples=template_data.get("examples", []),
            version=1,
            parent_template_id=template_data.get("parent_template_id"),
            usage_count=0,
            avg_quality_score=None,
            creator_id=creator_id,
            is_active=True,
            is_builtin=False,
            created_at=datetime.utcnow()
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"创建新模板: {template.name}")
        return template

    async def get_template_by_id(self, 
                               template_id: str,
                               db: AsyncSession) -> Optional[PromptTemplate]:
        """根据ID获取模板"""
        
        # 先检查内置模板
        if template_id in self.builtin_templates:
            return self._convert_builtin_to_model(self.builtin_templates[template_id])
        
        # 查询数据库模板
        result = await db.execute(
            select(PromptTemplate).where(PromptTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def search_templates(self,
                             subject: Optional[str] = None,
                             question_type: Optional[str] = None,
                             category: Optional[str] = None,
                             include_builtin: bool = True,
                             db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """搜索模板"""
        
        templates = []
        
        # 包含内置模板
        if include_builtin:
            for template_data in self.builtin_templates.values():
                if self._match_criteria(template_data, subject, question_type, category):
                    templates.append({
                        **template_data,
                        "is_builtin": True,
                        "usage_count": self.template_stats.get(template_data["id"], {}).get("usage_count", 0)
                    })
        
        # 查询数据库模板
        if db:
            conditions = [PromptTemplate.is_active == True]
            
            if subject:
                conditions.append(PromptTemplate.subject == subject)
            if question_type:
                conditions.append(PromptTemplate.question_type == question_type)
            if category:
                conditions.append(PromptTemplate.category == category)
            
            result = await db.execute(
                select(PromptTemplate)
                .where(and_(*conditions))
                .order_by(desc(PromptTemplate.usage_count))
            )
            
            db_templates = result.scalars().all()
            
            for template in db_templates:
                templates.append({
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "subject": template.subject,
                    "question_type": template.question_type,
                    "system_prompt": template.system_prompt,
                    "user_prompt_template": template.user_prompt_template,
                    "variables": template.variables,
                    "examples": template.examples,
                    "version": template.version,
                    "usage_count": template.usage_count,
                    "avg_quality_score": template.avg_quality_score,
                    "is_builtin": template.is_builtin,
                    "created_at": template.created_at.isoformat() if template.created_at else None
                })
        
        # 按使用次数排序
        templates.sort(key=lambda x: x.get("usage_count", 0), reverse=True)
        
        return templates

    def _match_criteria(self, 
                       template_data: Dict[str, Any],
                       subject: Optional[str],
                       question_type: Optional[str],
                       category: Optional[str]) -> bool:
        """检查模板是否符合搜索条件"""
        
        if subject and template_data.get("subject") != subject:
            return False
        if question_type and template_data.get("question_type") != question_type:
            return False
        if category and template_data.get("category") != category:
            return False
            
        return True

    async def render_template(self, 
                            template_id: str,
                            variables: Dict[str, Any],
                            db: Optional[AsyncSession] = None) -> RenderedTemplate:
        """渲染提示词模板"""
        
        # 获取模板
        if template_id in self.builtin_templates:
            template_data = self.builtin_templates[template_id]
        elif db:
            template = await self.get_template_by_id(template_id, db)
            if not template:
                raise ValueError(f"模板不存在: {template_id}")
            template_data = {
                "system_prompt": template.system_prompt,
                "user_prompt_template": template.user_prompt_template,
                "variables": template.variables
            }
        else:
            raise ValueError(f"无法找到模板: {template_id}")
        
        # 验证必需变量
        template_vars = template_data.get("variables", [])
        if isinstance(template_vars, list) and len(template_vars) > 0:
            # 处理TemplateVariable对象列表
            for var in template_vars:
                if isinstance(var, TemplateVariable):
                    if var.required and var.name not in variables:
                        if var.default_value is not None:
                            variables[var.name] = var.default_value
                        else:
                            raise ValueError(f"缺少必需变量: {var.name}")
                elif isinstance(var, dict):
                    if var.get("required", True) and var["name"] not in variables:
                        if var.get("default_value") is not None:
                            variables[var["name"]] = var["default_value"]
                        else:
                            raise ValueError(f"缺少必需变量: {var['name']}")
        
        # 渲染模板
        system_prompt = template_data.get("system_prompt", "")
        user_prompt_template = template_data.get("user_prompt_template", "")
        
        try:
            rendered_system = system_prompt.format(**variables) if system_prompt else ""
            rendered_user = user_prompt_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"模板变量缺失: {e}")
        
        # 构建消息列表
        messages = []
        if rendered_system:
            messages.append({"role": "system", "content": rendered_system})
        messages.append({"role": "user", "content": rendered_user})
        
        return RenderedTemplate(
            system_prompt=rendered_system,
            user_prompt=rendered_user,
            messages=messages,
            variables_used=variables.copy()
        )

    async def test_template(self,
                          template_id: str,
                          test_variables: Dict[str, Any],
                          db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """测试模板效果"""
        
        try:
            # 渲染模板
            rendered = await self.render_template(template_id, test_variables, db)
            
            # 使用AI生成测试响应
            from app.core.unified_ai_framework import unified_ai
            ai_response = await unified_ai.call_llm_with_fallback(
                messages=rendered.messages,
                model_type="rewrite",
                complexity=TaskComplexity.MEDIUM
            )
            
            # 评估响应质量
            quality_score = await self._evaluate_response_quality(
                test_variables.get("question", ""),
                test_variables.get("answer", ""),
                ai_response.content
            )
            
            return {
                "success": True,
                "rendered_prompt": {
                    "system_prompt": rendered.system_prompt,
                    "user_prompt": rendered.user_prompt
                },
                "ai_response": ai_response.content,
                "quality_score": quality_score,
                "model_used": ai_response.model_used,
                "cost": ai_response.cost,
                "response_time": ai_response.response_time
            }
            
        except Exception as e:
            logger.error(f"模板测试失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _evaluate_response_quality(self, 
                                       question: str,
                                       original_answer: str,
                                       rewritten_answer: str) -> int:
        """评估改写质量"""
        
        evaluation_prompt = f"""
        请评估以下答案改写的教学质量（1-10分）：
        
        原题目：{question}
        原答案：{original_answer}
        改写答案：{rewritten_answer}
        
        评估维度：
        1. 教学启发性 - 是否能引导学生思考
        2. 内容准确性 - 是否保持原答案正确性
        3. 语言适合度 - 是否符合学生认知水平
        4. 结构清晰度 - 是否逻辑清晰易懂
        
        只返回评分数字（1-10）。
        """
        
        try:
            from app.core.unified_ai_framework import unified_ai
            response = await unified_ai.call_llm_with_fallback(
                messages=[{"role": "user", "content": evaluation_prompt}],
                model_type="analysis",
                complexity=TaskComplexity.LOW
            )
            
            # 提取分数
            score_text = response.content.strip()
            score = int(''.join(filter(str.isdigit, score_text))[:2] or 0)
            return min(max(score, 1), 10)
            
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
            return 5  # 默认中等分数

    async def update_template_stats(self,
                                  template_id: str,
                                  quality_score: int,
                                  db: Optional[AsyncSession] = None):
        """更新模板使用统计"""
        
        # 更新内存统计
        if template_id not in self.template_stats:
            self.template_stats[template_id] = {
                "usage_count": 0,
                "total_quality_score": 0,
                "avg_quality_score": 0
            }
        
        stats = self.template_stats[template_id]
        stats["usage_count"] += 1
        stats["total_quality_score"] += quality_score
        stats["avg_quality_score"] = stats["total_quality_score"] / stats["usage_count"]
        
        # 更新数据库统计（如果是数据库模板）
        if db and template_id not in self.builtin_templates:
            template = await self.get_template_by_id(template_id, db)
            if template:
                template.usage_count += 1
                
                # 更新平均质量分数
                if template.avg_quality_score is None:
                    template.avg_quality_score = quality_score
                else:
                    total_score = template.avg_quality_score * (template.usage_count - 1) + quality_score
                    template.avg_quality_score = total_score / template.usage_count
                
                await db.commit()

    async def create_template_version(self,
                                    parent_template_id: str,
                                    template_data: Dict[str, Any],
                                    creator_id: str,
                                    db: AsyncSession) -> PromptTemplate:
        """创建模板新版本"""
        
        # 获取父模板
        parent_template = await self.get_template_by_id(parent_template_id, db)
        if not parent_template:
            raise ValueError(f"父模板不存在: {parent_template_id}")
        
        # 创建新版本
        new_version = parent_template.version + 1
        template_data["parent_template_id"] = parent_template_id
        
        new_template = await self.create_template(template_data, creator_id, db)
        new_template.version = new_version
        
        await db.commit()
        
        logger.info(f"创建模板新版本: {new_template.name} v{new_version}")
        return new_template

    def _convert_builtin_to_model(self, builtin_data: Dict[str, Any]) -> PromptTemplate:
        """将内置模板数据转换为模型对象"""
        
        return PromptTemplate(
            id=builtin_data["id"],
            name=builtin_data["name"],
            description=builtin_data.get("description"),
            category=builtin_data["category"],
            subject=builtin_data.get("subject"),
            question_type=builtin_data.get("question_type"),
            system_prompt=builtin_data["system_prompt"],
            user_prompt_template=builtin_data["user_prompt_template"],
            variables=builtin_data.get("variables", []),
            examples=builtin_data.get("examples", []),
            version=1,
            usage_count=self.template_stats.get(builtin_data["id"], {}).get("usage_count", 0),
            avg_quality_score=self.template_stats.get(builtin_data["id"], {}).get("avg_quality_score"),
            is_active=True,
            is_builtin=True,
            created_at=datetime.utcnow()
        )

    async def get_template_statistics(self) -> Dict[str, Any]:
        """获取模板使用统计"""
        
        return {
            "total_builtin_templates": len(self.builtin_templates),
            "template_stats": self.template_stats.copy(),
            "most_used_templates": sorted(
                [(tid, stats["usage_count"]) for tid, stats in self.template_stats.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    async def get_recommended_templates(self,
                                     subject: Optional[str] = None,
                                     question_type: Optional[str] = None,
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """获取推荐模板"""
        
        # 根据使用次数和质量分数推荐
        templates = await self.search_templates(
            subject=subject,
            question_type=question_type,
            include_builtin=True
        )
        
        # 计算推荐分数（使用次数 + 平均质量分数）
        for template in templates:
            usage_score = min(template.get("usage_count", 0) / 10, 10)  # 使用次数分数
            quality_score = template.get("avg_quality_score", 5)  # 质量分数
            template["recommendation_score"] = (usage_score + quality_score) / 2
        
        # 按推荐分数排序
        templates.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return templates[:limit]

# 全局实例
prompt_template_service = PromptTemplateService()
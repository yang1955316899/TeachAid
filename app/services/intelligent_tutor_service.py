"""
智能循循善诱教学服务
基于LangGraph的对话式教学系统
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum

import redis.asyncio as aioredis
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from loguru import logger
import openai

from app.core.config import settings


class TeachingPhase(str, Enum):
    """教学阶段"""
    INITIAL_ASSESSMENT = "initial_assessment"  # 初始评估
    GUIDED_QUESTIONING = "guided_questioning"  # 引导提问
    KNOWLEDGE_BUILDING = "knowledge_building"  # 知识构建
    PRACTICE_GUIDANCE = "practice_guidance"    # 练习指导
    REFLECTION_SUMMARY = "reflection_summary"  # 反思总结
    COMPLETED = "completed"                    # 完成


class StudentResponse(str, Enum):
    """学生回答状态"""
    CORRECT = "correct"        # 正确
    PARTIAL = "partial"        # 部分正确
    INCORRECT = "incorrect"    # 错误
    CONFUSED = "confused"      # 困惑
    BLANK = "blank"           # 未回答


class DifficultyLevel(str, Enum):
    """难度等级"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TutorState(BaseModel):
    """教学状态"""
    # 会话基础信息
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None

    # 学习内容
    subject: str = "通用"
    topic: str = ""
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objectives: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)

    # 当前状态
    current_phase: TeachingPhase = TeachingPhase.INITIAL_ASSESSMENT
    current_question: Optional[str] = None
    expected_answer: Optional[str] = None

    # 学生表现
    student_input: Optional[str] = None
    student_response_type: Optional[StudentResponse] = None
    understanding_level: float = 0.5  # 0-1之间，表示理解程度
    confusion_points: List[str] = Field(default_factory=list)

    # 对话历史
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    question_attempts: int = 0
    max_attempts: int = 3

    # 策略控制
    teaching_strategy: str = "socratic"  # socratic, direct, mixed
    patience_level: int = 3  # 1-5，表示耐心程度
    encouragement_needed: bool = False

    # 系统状态
    ai_response: Optional[str] = None
    next_action: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class QwenAPIClient:
    """Qwen API客户端"""

    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "qwen-plus"

    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用Qwen聊天完成"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 1000),
                top_p=kwargs.get("top_p", 0.9)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Qwen API调用失败: {e}")
            raise


class IntelligentTutorService:
    """智能教学服务"""

    def __init__(self):
        # 初始化Qwen客户端
        self.qwen_client = QwenAPIClient(
            api_key="sk-6f1acdba733f42988cdd87e5ebd77412"
        )

        # 构建教学工作流
        self.workflow = self._build_tutor_workflow()

        # 教学策略模板
        self.teaching_prompts = self._init_teaching_prompts()

    def _build_tutor_workflow(self) -> StateGraph:
        """构建教学工作流"""
        workflow = StateGraph(TutorState)

        # 添加节点
        workflow.add_node("assess_input", self._assess_student_input)
        workflow.add_node("generate_question", self._generate_guiding_question)
        workflow.add_node("provide_hint", self._provide_targeted_hint)
        workflow.add_node("explain_concept", self._explain_key_concept)
        workflow.add_node("encourage_student", self._encourage_student)
        workflow.add_node("summarize_learning", self._summarize_learning)
        workflow.add_node("handle_confusion", self._handle_confusion)

        # 设置入口点
        workflow.set_entry_point("assess_input")

        # 条件路由
        workflow.add_conditional_edges(
            "assess_input",
            self._route_teaching_strategy,
            {
                "question": "generate_question",
                "hint": "provide_hint",
                "explain": "explain_concept",
                "encourage": "encourage_student",
                "confused": "handle_confusion",
                "complete": "summarize_learning"
            }
        )

        # 其他节点的边
        workflow.add_edge("generate_question", END)
        workflow.add_edge("provide_hint", END)
        workflow.add_edge("explain_concept", END)
        workflow.add_edge("encourage_student", END)
        workflow.add_edge("handle_confusion", END)
        workflow.add_edge("summarize_learning", END)

        return workflow.compile(checkpointer=MemorySaver())

    def _init_teaching_prompts(self) -> Dict[str, str]:
        """初始化教学提示词模板"""
        return {
            "socratic_question": """
你是一位使用苏格拉底式教学法的老师。学生正在学习{topic}。

当前学习目标：{objectives}
关键概念：{concepts}
学生当前理解水平：{understanding_level}/1.0

学生刚才说："{student_input}"

请提出一个引导性问题，帮助学生自己发现答案，而不是直接告诉他们。
问题应该：
1. 循序渐进，从学生已知的内容出发
2. 激发思考，让学生主动探索
3. 针对学生的理解水平调整难度
4. 保持耐心和鼓励的语气

只返回问题，不要解释。
""",

            "targeted_hint": """
学生在{topic}学习中遇到困难。
学习目标：{objectives}
困惑点：{confusion_points}
学生说："{student_input}"

请提供一个精准的提示，要求：
1. 不直接给出答案
2. 指出正确的思考方向
3. 联系学生已掌握的知识
4. 语言温和鼓励

提示：
""",

            "concept_explanation": """
学生需要理解{topic}中的概念：{concepts}
当前理解水平：{understanding_level}/1.0
学生困惑："{student_input}"

请用简单易懂的方式解释这个概念：
1. 使用类比和例子
2. 分步骤讲解
3. 适合学生的认知水平
4. 引导学生思考而非被动接受

解释：
""",

            "encouragement": """
学生在学习{topic}时感到挫折或困惑。
已尝试次数：{attempts}/{max_attempts}
学生说："{student_input}"

请给予鼓励和支持：
1. 肯定学生的努力
2. 指出进步之处
3. 重燃学习信心
4. 给出继续学习的动力

鼓励话语：
""",

            "confusion_handler": """
学生对{topic}表现出明显困惑。
困惑点：{confusion_points}
学生输入："{student_input}"

请帮助澄清困惑：
1. 识别混乱的根源
2. 简化复杂概念
3. 提供清晰的解释
4. 确认学生理解

澄清：
"""
        }

    async def start_learning_session(self,
                                   user_id: str,
                                   subject: str,
                                   topic: str,
                                   difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                                   learning_objectives: List[str] = None) -> Dict[str, Any]:
        """开始学习会话"""
        session_id = str(uuid.uuid4())

        # 生成初始评估问题
        initial_state = TutorState(
            session_id=session_id,
            user_id=user_id,
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            learning_objectives=learning_objectives or [],
            current_phase=TeachingPhase.INITIAL_ASSESSMENT
        )

        # 生成开场问题
        assessment_question = await self._generate_initial_assessment(initial_state)

        return {
            "session_id": session_id,
            "initial_question": assessment_question,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty.value
        }

    async def process_student_input(self, session_id: str, student_input: str,
                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理学生输入"""

        # 构建当前状态 (简化版，实际应该从数据库加载)
        state = TutorState(
            session_id=session_id,
            user_id=context.get("user_id") if context else None,
            subject=context.get("subject", "通用") if context else "通用",
            topic=context.get("topic", "") if context else "",
            student_input=student_input
        )

        try:
            # 执行工作流
            result = await self.workflow.ainvoke(
                state.dict(),
                config={"configurable": {"thread_id": session_id}}
            )

            return {
                "success": True,
                "session_id": session_id,
                "ai_response": result.get("ai_response", ""),
                "current_phase": result.get("current_phase"),
                "understanding_level": result.get("understanding_level", 0.5),
                "next_action": result.get("next_action"),
                "encouragement_needed": result.get("encouragement_needed", False)
            }

        except Exception as e:
            logger.error(f"处理学生输入失败: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "ai_response": "抱歉，系统遇到了问题，请稍后再试。"
            }

    async def _assess_student_input(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """评估学生输入"""
        student_input = state.get("student_input", "")
        topic = state.get("topic", "")

        if not student_input.strip():
            state["student_response_type"] = StudentResponse.BLANK
            state["understanding_level"] = max(0, state.get("understanding_level", 0.5) - 0.1)
            return state

        # 使用Qwen评估学生回答
        assessment_prompt = f"""
评估学生在学习{topic}时的回答质量。

学生回答："{student_input}"

请从以下维度评估：
1. 正确性（correct/partial/incorrect）
2. 理解程度（0-1之间的小数）
3. 是否表现出困惑（true/false）
4. 需要的帮助类型（question/hint/explain/encourage）

以JSON格式返回：
{{"response_type": "correct|partial|incorrect|confused", "understanding": 0.8, "confused": false, "help_needed": "question"}}
"""

        try:
            assessment_result = await self.qwen_client.chat_completion([
                {"role": "user", "content": assessment_prompt}
            ])

            # 解析评估结果
            import re
            json_match = re.search(r'\{.*\}', assessment_result)
            if json_match:
                result_data = json.loads(json_match.group())
                state["student_response_type"] = result_data.get("response_type", "partial")
                state["understanding_level"] = result_data.get("understanding", 0.5)
                state["next_action"] = result_data.get("help_needed", "question")

                if result_data.get("confused", False):
                    state["confusion_points"].append(student_input)

        except Exception as e:
            logger.error(f"评估学生输入失败: {e}")
            state["student_response_type"] = StudentResponse.PARTIAL
            state["understanding_level"] = 0.5
            state["next_action"] = "question"

        return state

    def _route_teaching_strategy(self, state: Dict[str, Any]) -> str:
        """路由教学策略"""
        understanding = state.get("understanding_level", 0.5)
        response_type = state.get("student_response_type")
        attempts = state.get("question_attempts", 0)
        max_attempts = state.get("max_attempts", 3)

        # 如果学生完全理解且回答正确
        if understanding >= 0.8 and response_type == StudentResponse.CORRECT:
            return "complete"

        # 如果学生困惑或多次尝试失败
        if response_type == StudentResponse.CONFUSED or attempts >= max_attempts:
            return "confused"

        # 如果理解程度较低，需要鼓励
        if understanding < 0.3:
            return "encourage"

        # 根据next_action决定策略
        next_action = state.get("next_action", "question")
        if next_action == "hint":
            return "hint"
        elif next_action == "explain":
            return "explain"
        else:
            return "question"

    async def _generate_guiding_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成引导性问题"""
        prompt = self.teaching_prompts["socratic_question"].format(
            topic=state.get("topic", ""),
            objectives=", ".join(state.get("learning_objectives", [])),
            concepts=", ".join(state.get("key_concepts", [])),
            understanding_level=state.get("understanding_level", 0.5),
            student_input=state.get("student_input", "")
        )

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            state["ai_response"] = response
            state["question_attempts"] = state.get("question_attempts", 0) + 1
        except Exception as e:
            logger.error(f"生成问题失败: {e}")
            state["ai_response"] = "让我们换个角度思考这个问题..."

        return state

    async def _provide_targeted_hint(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """提供针对性提示"""
        prompt = self.teaching_prompts["targeted_hint"].format(
            topic=state.get("topic", ""),
            objectives=", ".join(state.get("learning_objectives", [])),
            confusion_points=", ".join(state.get("confusion_points", [])),
            student_input=state.get("student_input", "")
        )

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            state["ai_response"] = response
        except Exception as e:
            logger.error(f"提供提示失败: {e}")
            state["ai_response"] = "让我给你一个小提示..."

        return state

    async def _explain_key_concept(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """解释关键概念"""
        prompt = self.teaching_prompts["concept_explanation"].format(
            topic=state.get("topic", ""),
            concepts=", ".join(state.get("key_concepts", [])),
            understanding_level=state.get("understanding_level", 0.5),
            student_input=state.get("student_input", "")
        )

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            state["ai_response"] = response
            state["current_phase"] = TeachingPhase.KNOWLEDGE_BUILDING
        except Exception as e:
            logger.error(f"解释概念失败: {e}")
            state["ai_response"] = "让我来解释一下这个概念..."

        return state

    async def _encourage_student(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """鼓励学生"""
        prompt = self.teaching_prompts["encouragement"].format(
            topic=state.get("topic", ""),
            attempts=state.get("question_attempts", 0),
            max_attempts=state.get("max_attempts", 3),
            student_input=state.get("student_input", "")
        )

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            state["ai_response"] = response
            state["encouragement_needed"] = False
        except Exception as e:
            logger.error(f"鼓励学生失败: {e}")
            state["ai_response"] = "你做得很好！让我们继续努力..."

        return state

    async def _handle_confusion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """处理困惑"""
        prompt = self.teaching_prompts["confusion_handler"].format(
            topic=state.get("topic", ""),
            confusion_points=", ".join(state.get("confusion_points", [])),
            student_input=state.get("student_input", "")
        )

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            state["ai_response"] = response
            # 重置尝试次数
            state["question_attempts"] = 0
        except Exception as e:
            logger.error(f"处理困惑失败: {e}")
            state["ai_response"] = "我理解你的困惑，让我们重新开始..."

        return state

    async def _summarize_learning(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """总结学习"""
        summary_prompt = f"""
学生在{state.get('topic', '')}的学习即将结束。
理解程度：{state.get('understanding_level', 0.5)}/1.0

请总结这次学习：
1. 学生的进步
2. 掌握的关键概念
3. 还需要加强的地方
4. 下一步学习建议

总结要积极正面，鼓励学生继续学习。
"""

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": summary_prompt}
            ])
            state["ai_response"] = response
            state["current_phase"] = TeachingPhase.COMPLETED
        except Exception as e:
            logger.error(f"总结学习失败: {e}")
            state["ai_response"] = "这次学习很有收获！"

        return state

    async def _generate_initial_assessment(self, state: TutorState) -> str:
        """生成初始评估问题"""
        prompt = f"""
你是一位经验丰富的老师，要开始教授{state.subject}中的{state.topic}。
难度等级：{state.difficulty.value}
学习目标：{', '.join(state.learning_objectives)}

请设计一个开场问题来评估学生的基础水平：
1. 问题要友好、不具威胁性
2. 能够了解学生的现有知识
3. 为后续教学提供参考
4. 激发学生的学习兴趣

只返回问题内容。
"""

        try:
            response = await self.qwen_client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            return response
        except Exception as e:
            logger.error(f"生成初始评估失败: {e}")
            return f"你好！我们今天要学习{state.topic}，你对这个话题了解多少呢？"


# 全局实例
intelligent_tutor = IntelligentTutorService()
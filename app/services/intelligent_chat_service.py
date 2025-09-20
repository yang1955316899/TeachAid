"""
智能学习对话服务 - IntelligentChatService
基于上下文感知的AI对话系统，为学生提供个性化学习引导
"""
import time
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from app.models.database_models import ChatSession, ChatMessage, Question
from app.core.unified_ai_framework import TaskComplexity
from app.services.intelligent_cache_service import intelligent_cache

logger = logging.getLogger(__name__)

@dataclass
class SessionContext:
    """对话会话上下文"""
    session_id: str
    student_id: str
    question_id: str
    homework_id: Optional[str]
    question_data: Dict[str, Any]
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    understanding_level: int = 3  # 1-5级别
    interaction_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_interaction: float = field(default_factory=time.time)
    student_preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChatResponse:
    """对话响应"""
    content: str
    session_id: str
    message_id: str
    model_used: str
    response_time: float
    from_cache: bool = False
    understanding_hints: List[str] = field(default_factory=list)
    suggested_questions: List[str] = field(default_factory=list)

class IntelligentChatService:
    """智能学习对话服务"""
    
    def __init__(self):
        """初始化智能对话服务"""
        
        # 会话上下文缓存
        self.active_sessions: Dict[str, SessionContext] = {}
        
        # Redis连接（用于会话持久化）
        self.redis_client: Optional[redis.Redis] = None
        
        # 对话配置
        self.max_context_messages = 20  # 最大上下文消息数
        self.session_timeout = 3600     # 会话超时时间（秒）
        self.understanding_threshold = 4 # 理解水平阈值
        
        # 引导式教学提示词
        self.guidance_prompts = {
            "math": """你是一位耐心的数学老师，正在一对一辅导学生。

教学原则：
1. 不直接给出答案，而是通过问题引导学生思考
2. 根据学生的回答调整教学策略
3. 鼓励学生说出自己的想法和解题过程
4. 当学生困惑时，给出适当的提示而非直接答案
5. 关注学生的理解程度，适时调整难度

当前题目信息：{question_context}
学生理解水平：{understanding_level}/5
""",
            "chinese": """你是一位温和的语文老师，善于启发学生思考。

教学原则：
1. 引导学生从文本中寻找答案依据
2. 培养学生的思维能力和表达能力
3. 不直接告诉答案，而是启发思考
4. 注重情感体验和价值观引导
5. 鼓励学生联系生活实际

当前题目信息：{question_context}
学生水平：{understanding_level}/5
""",
            "english": """You are a patient English teacher providing one-on-one tutoring.

Teaching principles:
1. Guide students to discover answers rather than giving direct answers
2. Encourage students to express their thoughts in English
3. Provide hints and encouragement when students are confused
4. Adapt your language level to match the student's ability
5. Focus on building confidence in English learning

Current question context: {question_context}
Student level: {understanding_level}/5
""",
            "general": """你是一位经验丰富的老师，善于因材施教。

教学原则：
1. 以学生为中心，根据其理解水平调整教学方法
2. 通过提问引导学生主动思考
3. 给予积极的鼓励和耐心的指导
4. 不直接提供答案，而是启发学生自己发现
5. 营造轻松愉快的学习氛围

当前题目信息：{question_context}
学生理解水平：{understanding_level}/5
"""
        }
        
        logger.info("IntelligentChatService 初始化完成")

    async def initialize(self):
        """异步初始化"""
        try:
            # 初始化Redis连接用于会话持久化
            if redis:
                from app.core.config import settings
                redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/1')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info("智能对话服务Redis连接成功")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存会话: {e}")

    async def start_chat_session(self,
                                student_id: str,
                                question_id: str,
                                homework_id: Optional[str] = None,
                                db: Optional[AsyncSession] = None) -> str:
        """开始对话会话"""
        
        # 生成会话ID
        session_id = f"chat_{student_id}_{question_id}_{int(time.time())}"
        
        # 获取题目信息
        question_data = {}
        if db:
            result = await db.execute(
                select(Question).where(Question.id == question_id)
            )
            question = result.scalar_one_or_none()
            if question:
                question_data = {
                    "id": question.id,
                    "title": question.title,
                    "content": question.content,
                    "subject": question.subject,
                    "question_type": question.question_type,
                    "difficulty": question.difficulty,
                    "rewritten_answer": question.rewritten_answer,
                    "knowledge_points": question.knowledge_points
                }
        
        # 创建会话上下文
        context = SessionContext(
            session_id=session_id,
            student_id=student_id,
            question_id=question_id,
            homework_id=homework_id,
            question_data=question_data
        )
        
        # 缓存会话
        self.active_sessions[session_id] = context
        
        # 持久化到Redis
        await self._save_session_to_redis(context)
        
        # 创建数据库记录
        if db:
            chat_session = ChatSession(
                id=session_id,
                student_id=student_id,
                question_id=question_id,
                homework_id=homework_id,
                session_data={
                    "understanding_level": context.understanding_level,
                    "created_at": context.created_at
                },
                message_count=0,
                started_at=datetime.utcnow(),
                last_interaction_at=datetime.utcnow()
            )
            
            db.add(chat_session)
            await db.commit()
        
        logger.info(f"创建对话会话: {session_id}")
        
        # 发送欢迎消息
        welcome_message = await self._generate_welcome_message(context)
        await self._save_message(
            session_id, "assistant", welcome_message,
            model_used="system", db=db
        )
        
        return session_id

    async def chat_with_ai(self,
                          session_id: str,
                          user_message: str,
                          selected_text: Optional[str] = None,
                          db: Optional[AsyncSession] = None) -> ChatResponse:
        """与AI进行对话"""
        
        start_time = time.time()
        
        # 获取会话上下文
        context = await self._get_session_context(session_id)
        if not context:
            raise ValueError(f"会话不存在: {session_id}")
        
        # 保存用户消息
        await self._save_message(session_id, "user", user_message, selected_text=selected_text, db=db)
        
        # 更新上下文
        context.chat_history.append({"role": "user", "content": user_message})
        context.interaction_count += 1
        context.last_interaction = time.time()
        
        # 构建对话上下文
        conversation_context = await self._build_conversation_context(context, selected_text)
        
        # 尝试从缓存获取响应
        cache_key = f"{user_message}:{selected_text or ''}:{context.question_id}"
        cached_response = await intelligent_cache.get_cached_response(
            cache_key, model="chat", enable_semantic=True
        )
        
        if cached_response:
            ai_content = cached_response["response"]
            model_used = cached_response["model_used"]
            from_cache = True
            response_time = time.time() - start_time
        else:
            # 生成AI响应
            try:
                from app.core.unified_ai_framework import unified_ai
                ai_response = await unified_ai.call_llm_with_fallback(
                    user_message=user_message,
                    context=context.question_data,
                    selected_text=selected_text,
                    session_history=context.chat_history[-10:]  # 最近10轮对话
                )
                
                ai_content = ai_response.content
                model_used = ai_response.model_used
                from_cache = False
                response_time = time.time() - start_time
                
                # 缓存响应
                await intelligent_cache.cache_response(
                    cache_key, ai_content, model_used, ai_response.cost
                )
                
            except Exception as e:
                logger.error(f"AI对话失败: {e}")
                ai_content = "抱歉，我现在无法回答你的问题。请稍后再试，或者重新表述你的问题。"
                model_used = "fallback"
                from_cache = False
                response_time = time.time() - start_time
        
        # 生成消息ID
        message_id = str(uuid.uuid4())
        
        # 保存AI响应
        await self._save_message(
            session_id, "assistant", ai_content,
            model_used=model_used, response_time=int(response_time * 1000), db=db
        )
        
        # 更新会话历史
        context.chat_history.append({"role": "assistant", "content": ai_content})
        
        # 保持历史长度限制
        if len(context.chat_history) > self.max_context_messages:
            context.chat_history = context.chat_history[-self.max_context_messages:]
        
        # 分析学生理解水平
        await self._analyze_understanding_level(context, user_message, ai_content)
        
        # 生成学习建议
        understanding_hints, suggested_questions = await self._generate_learning_suggestions(context)
        
        # 更新会话缓存
        self.active_sessions[session_id] = context
        await self._save_session_to_redis(context)
        
        return ChatResponse(
            content=ai_content,
            session_id=session_id,
            message_id=message_id,
            model_used=model_used,
            response_time=response_time,
            from_cache=from_cache,
            understanding_hints=understanding_hints,
            suggested_questions=suggested_questions
        )

    async def stream_chat_response(self,
                                 session_id: str,
                                 user_message: str,
                                 selected_text: Optional[str] = None) -> AsyncGenerator[str, None]:
        """流式对话响应"""
        
        try:
            # 获取会话上下文
            context = await self._get_session_context(session_id)
            if not context:
                yield "error: 会话不存在"
                return
            
            # 构建流式响应
            async for chunk in self._generate_streaming_response(context, user_message, selected_text):
                yield chunk
                
        except Exception as e:
            logger.error(f"流式对话失败: {e}")
            yield f"error: {str(e)}"

    async def _generate_streaming_response(self,
                                         context: SessionContext,
                                         user_message: str,
                                         selected_text: Optional[str]) -> AsyncGenerator[str, None]:
        """生成流式响应（模拟）"""
        
        # 这里应该调用支持流式响应的LLM接口
        # 暂时用模拟实现
        
        full_response = await self.chat_with_ai(
            context.session_id, user_message, selected_text
        )
        
        # 分块发送响应
        words = full_response.content.split()
        for i, word in enumerate(words):
            yield word + " "
            if i % 3 == 0:  # 每3个词暂停一下
                await asyncio.sleep(0.1)
        
        yield "[DONE]"

    async def get_chat_history(self,
                             session_id: str,
                             limit: int = 50,
                             db: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """获取对话历史"""
        
        if not db:
            # 从内存缓存获取
            context = self.active_sessions.get(session_id)
            if context:
                return [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": time.time()  # 简化时间戳
                    }
                    for msg in context.chat_history[-limit:]
                ]
            return []
        
        # 从数据库获取
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(limit)
        )
        
        messages = result.scalars().all()
        
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "selected_text": msg.selected_text,
                "model_used": msg.model_used,
                "response_time": msg.response_time,
                "from_cache": msg.from_cache,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]

    async def end_chat_session(self,
                             session_id: str,
                             db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """结束对话会话"""
        
        context = self.active_sessions.get(session_id)
        if not context:
            return {"success": False, "error": "会话不存在"}
        
        # 生成会话总结
        session_summary = await self._generate_session_summary(context)
        
        # 更新数据库记录
        if db:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            chat_session = result.scalar_one_or_none()
            if chat_session:
                chat_session.understanding_level = context.understanding_level
                chat_session.last_interaction_at = datetime.utcnow()
                chat_session.session_data = {
                    **chat_session.session_data,
                    "final_understanding_level": context.understanding_level,
                    "total_interactions": context.interaction_count,
                    "session_summary": session_summary
                }
                await db.commit()
        
        # 清理会话缓存
        del self.active_sessions[session_id]
        
        # 从Redis清理
        if self.redis_client:
            await self.redis_client.delete(f"session:{session_id}")
        
        logger.info(f"结束对话会话: {session_id}")
        
        return {
            "success": True,
            "session_summary": session_summary,
            "final_understanding_level": context.understanding_level,
            "total_interactions": context.interaction_count
        }

    async def _get_session_context(self, session_id: str) -> Optional[SessionContext]:
        """获取会话上下文"""
        
        # 先从内存缓存查找
        if session_id in self.active_sessions:
            context = self.active_sessions[session_id]
            
            # 检查是否超时
            if time.time() - context.last_interaction > self.session_timeout:
                del self.active_sessions[session_id]
                return None
                
            return context
        
        # 从Redis恢复
        if self.redis_client:
            try:
                session_data = await self.redis_client.get(f"session:{session_id}")
                if session_data:
                    context_dict = json.loads(session_data)
                    context = SessionContext(**context_dict)
                    
                    # 检查是否超时
                    if time.time() - context.last_interaction > self.session_timeout:
                        await self.redis_client.delete(f"session:{session_id}")
                        return None
                    
                    self.active_sessions[session_id] = context
                    return context
                    
            except Exception as e:
                logger.warning(f"从Redis恢复会话失败: {e}")
        
        return None

    async def _build_conversation_context(self,
                                        context: SessionContext,
                                        selected_text: Optional[str]) -> str:
        """构建对话上下文提示词"""
        
        subject = context.question_data.get("subject", "general").lower()
        
        # 选择合适的引导提示词
        if "数学" in subject or "math" in subject:
            base_prompt = self.guidance_prompts["math"]
        elif "语文" in subject or "chinese" in subject:
            base_prompt = self.guidance_prompts["chinese"]  
        elif "英语" in subject or "english" in subject:
            base_prompt = self.guidance_prompts["english"]
        else:
            base_prompt = self.guidance_prompts["general"]
        
        # 构建题目上下文信息
        question_context = f"""
题目：{context.question_data.get('content', '未知题目')}
学科：{context.question_data.get('subject', '通用')}
难度：{context.question_data.get('difficulty', '中等')}
知识点：{', '.join(context.question_data.get('knowledge_points', []))}
"""
        
        # 如果有选中文本，添加特别说明
        if selected_text:
            question_context += f"\n学生对这部分内容有疑问：「{selected_text}」"
        
        return base_prompt.format(
            question_context=question_context,
            understanding_level=context.understanding_level
        )

    async def _generate_welcome_message(self, context: SessionContext) -> str:
        """生成欢迎消息"""
        
        question_title = context.question_data.get("title", "这道题目")
        subject = context.question_data.get("subject", "")
        
        welcome_messages = [
            f"你好！我是你的AI学习助手。我看到你要学习{subject}的题目：{question_title}。",
            "我会陪伴你一步步思考这道题，引导你找到答案。",
            "如果你有任何疑问，随时告诉我。你可以选中题目中的任何部分来提问哦！",
            "让我们开始吧！你觉得这道题的关键是什么？"
        ]
        
        return " ".join(welcome_messages)

    async def _save_message(self,
                          session_id: str,
                          role: str,
                          content: str,
                          selected_text: Optional[str] = None,
                          model_used: Optional[str] = None,
                          response_time: Optional[int] = None,
                          db: Optional[AsyncSession] = None):
        """保存对话消息"""
        
        if not db:
            return
            
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            selected_text=selected_text,
            model_used=model_used,
            response_time=response_time or 0,
            from_cache=False,
            created_at=datetime.utcnow()
        )
        
        db.add(message)
        await db.commit()

    async def _analyze_understanding_level(self,
                                         context: SessionContext,
                                         user_message: str,
                                         ai_response: str):
        """分析学生理解水平"""
        
        try:
            # 基于对话内容分析理解水平
            analysis_prompt = f"""
            基于以下对话判断学生的理解水平（1-5分）：
            
            学生问题：{user_message}
            AI回答：{ai_response}
            
            评估标准：
            1分 - 完全不理解，问题很基础
            2分 - 理解有限，需要大量帮助
            3分 - 基本理解，需要适当指导
            4分 - 理解良好，能独立思考
            5分 - 理解深刻，能举一反三
            
            只返回1-5的数字。
            """
            
            from app.core.unified_ai_framework import unified_ai
            response = await unified_ai.call_llm_with_fallback(
                messages=[{"role": "user", "content": analysis_prompt}],
                model_type="analysis",
                complexity=TaskComplexity.LOW
            )
            
            # 提取理解水平
            level_text = response.content.strip()
            new_level = int(''.join(filter(str.isdigit, level_text))[:1] or 3)
            new_level = max(1, min(5, new_level))
            
            # 平滑更新理解水平（避免剧烈波动）
            context.understanding_level = int((context.understanding_level + new_level) / 2)
            
        except Exception as e:
            logger.warning(f"理解水平分析失败: {e}")

    async def _generate_learning_suggestions(self,
                                           context: SessionContext) -> Tuple[List[str], List[str]]:
        """生成学习建议"""
        
        understanding_hints = []
        suggested_questions = []
        
        # 根据理解水平生成提示
        if context.understanding_level <= 2:
            understanding_hints = [
                "不要担心，学习是一个渐进的过程",
                "可以先复习相关的基础知识",
                "试着将问题分解成更小的步骤"
            ]
            suggested_questions = [
                "这道题涉及哪些基础概念？",
                "能否先解释一下题目的意思？"
            ]
        elif context.understanding_level >= 4:
            understanding_hints = [
                "你理解得很好！",
                "试着思考这类题目的一般解题方法",
                "可以考虑这道题的变式或拓展"
            ]
            suggested_questions = [
                "如果题目条件改变了，该怎么解决？",
                "这种解题方法还能用在哪些地方？"
            ]
        else:
            understanding_hints = [
                "你的思路很不错",
                "再仔细看看题目的关键信息",
                "试着用自己的话总结一下解题思路"
            ]
            suggested_questions = [
                "你觉得解题的关键步骤是什么？",
                "还有其他解法吗？"
            ]
        
        return understanding_hints[:2], suggested_questions[:2]

    async def _generate_session_summary(self, context: SessionContext) -> Dict[str, Any]:
        """生成会话总结"""
        
        return {
            "session_duration": time.time() - context.created_at,
            "total_interactions": context.interaction_count,
            "final_understanding_level": context.understanding_level,
            "question_id": context.question_id,
            "subject": context.question_data.get("subject"),
            "key_topics_discussed": context.question_data.get("knowledge_points", [])
        }

    async def _save_session_to_redis(self, context: SessionContext):
        """保存会话到Redis"""
        
        if not self.redis_client:
            return
            
        try:
            session_data = {
                "session_id": context.session_id,
                "student_id": context.student_id,
                "question_id": context.question_id,
                "homework_id": context.homework_id,
                "question_data": context.question_data,
                "chat_history": context.chat_history[-self.max_context_messages:],
                "understanding_level": context.understanding_level,
                "interaction_count": context.interaction_count,
                "created_at": context.created_at,
                "last_interaction": context.last_interaction,
                "student_preferences": context.student_preferences
            }
            
            await self.redis_client.setex(
                f"session:{context.session_id}",
                self.session_timeout,
                json.dumps(session_data, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.warning(f"保存会话到Redis失败: {e}")

    async def get_active_sessions_count(self) -> int:
        """获取活跃会话数量"""
        return len(self.active_sessions)

    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        
        current_time = time.time()
        expired_sessions = []
        
        for session_id, context in self.active_sessions.items():
            if current_time - context.last_interaction > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            
        logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
        return len(expired_sessions)

# 全局实例
intelligent_chat_service = IntelligentChatService()
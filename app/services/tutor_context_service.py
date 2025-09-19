"""
智能教学上下文管理服务
负责会话数据的保存、加载和关联管理
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from loguru import logger

from app.core.database import get_db
from app.models.database_models import TutorSession, TutorMessage, StudentProgress
from app.services.intelligent_tutor_service import TeachingPhase, DifficultyLevel


class TutorContextService:
    """教学上下文管理服务"""

    def __init__(self):
        pass

    async def create_session(self,
                           user_id: str,
                           subject: str,
                           topic: str,
                           difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                           learning_objectives: List[str] = None,
                           key_concepts: List[str] = None) -> str:
        """创建新的教学会话"""
        async with get_db_session() as db:
            try:
                session = TutorSession(
                    user_id=user_id,
                    subject=subject,
                    topic=topic,
                    difficulty=difficulty.value,
                    learning_objectives=learning_objectives or [],
                    key_concepts=key_concepts or [],
                    current_phase=TeachingPhase.INITIAL_ASSESSMENT.value,
                    understanding_level=0.5,
                    teaching_strategy="socratic"
                )

                db.add(session)
                await db.commit()
                await db.refresh(session)

                logger.info(f"创建教学会话成功: {session.id}, 用户: {user_id}, 主题: {topic}")
                return session.id

            except Exception as e:
                await db.rollback()
                logger.error(f"创建教学会话失败: {e}")
                raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        async with get_db_session() as db:
            try:
                result = await db.execute(
                    select(TutorSession)
                    .options(selectinload(TutorSession.messages))
                    .where(TutorSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return None

                return {
                    "id": session.id,
                    "user_id": session.user_id,
                    "subject": session.subject,
                    "topic": session.topic,
                    "difficulty": session.difficulty,
                    "learning_objectives": session.learning_objectives or [],
                    "key_concepts": session.key_concepts or [],
                    "current_phase": session.current_phase,
                    "understanding_level": session.understanding_level,
                    "teaching_strategy": session.teaching_strategy,
                    "total_questions": session.total_questions,
                    "correct_answers": session.correct_answers,
                    "session_duration": session.session_duration,
                    "is_active": session.is_active,
                    "created_time": session.created_time,
                    "updated_time": session.updated_time,
                    "messages": [
                        {
                            "id": msg.id,
                            "role": msg.role,
                            "content": msg.content,
                            "message_type": msg.message_type,
                            "teaching_phase": msg.teaching_phase,
                            "understanding_level": msg.understanding_level,
                            "response_type": msg.response_type,
                            "confusion_points": msg.confusion_points or [],
                            "timestamp": msg.timestamp
                        }
                        for msg in sorted(session.messages, key=lambda x: x.timestamp)
                    ]
                }

            except Exception as e:
                logger.error(f"获取会话失败: {e}")
                return None

    async def add_message(self,
                         session_id: str,
                         role: str,
                         content: str,
                         message_type: str = None,
                         teaching_phase: str = None,
                         understanding_level: float = None,
                         response_type: str = None,
                         confusion_points: List[str] = None) -> bool:
        """添加对话消息"""
        async with get_db_session() as db:
            try:
                message = TutorMessage(
                    session_id=session_id,
                    role=role,
                    content=content,
                    message_type=message_type,
                    teaching_phase=teaching_phase,
                    understanding_level=understanding_level,
                    response_type=response_type,
                    confusion_points=confusion_points or []
                )

                db.add(message)

                # 同时更新会话统计
                if role == "user":
                    await db.execute(
                        update(TutorSession)
                        .where(TutorSession.id == session_id)
                        .values(
                            total_questions=TutorSession.total_questions + 1,
                            updated_time=datetime.now()
                        )
                    )

                    # 如果是正确回答，更新正确数
                    if response_type == "correct":
                        await db.execute(
                            update(TutorSession)
                            .where(TutorSession.id == session_id)
                            .values(correct_answers=TutorSession.correct_answers + 1)
                        )

                # 更新理解程度
                if understanding_level is not None:
                    await db.execute(
                        update(TutorSession)
                        .where(TutorSession.id == session_id)
                        .values(
                            understanding_level=understanding_level,
                            current_phase=teaching_phase or TutorSession.current_phase
                        )
                    )

                await db.commit()
                logger.info(f"添加消息成功: 会话{session_id}, 角色{role}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"添加消息失败: {e}")
                return False

    async def update_session_phase(self,
                                 session_id: str,
                                 phase: TeachingPhase,
                                 understanding_level: float = None) -> bool:
        """更新会话阶段"""
        async with get_db_session() as db:
            try:
                update_data = {
                    "current_phase": phase.value,
                    "updated_time": datetime.now()
                }

                if understanding_level is not None:
                    update_data["understanding_level"] = understanding_level

                await db.execute(
                    update(TutorSession)
                    .where(TutorSession.id == session_id)
                    .values(**update_data)
                )

                await db.commit()
                logger.info(f"更新会话阶段成功: {session_id} -> {phase.value}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"更新会话阶段失败: {e}")
                return False

    async def complete_session(self, session_id: str) -> bool:
        """完成会话"""
        async with get_db_session() as db:
            try:
                # 计算会话持续时间
                result = await db.execute(
                    select(TutorSession.created_time)
                    .where(TutorSession.id == session_id)
                )
                created_time = result.scalar_one_or_none()

                if created_time:
                    duration = int((datetime.now() - created_time).total_seconds())
                else:
                    duration = 0

                await db.execute(
                    update(TutorSession)
                    .where(TutorSession.id == session_id)
                    .values(
                        current_phase=TeachingPhase.COMPLETED.value,
                        is_active=False,
                        completed_at=datetime.now(),
                        session_duration=duration,
                        updated_time=datetime.now()
                    )
                )

                await db.commit()
                logger.info(f"完成会话: {session_id}, 持续时间: {duration}秒")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"完成会话失败: {e}")
                return False

    async def get_user_sessions(self,
                              user_id: str,
                              limit: int = 10,
                              offset: int = 0,
                              active_only: bool = False) -> List[Dict[str, Any]]:
        """获取用户的会话列表"""
        async with get_db_session() as db:
            try:
                query = select(TutorSession).where(TutorSession.user_id == user_id)

                if active_only:
                    query = query.where(TutorSession.is_active == True)

                query = query.order_by(TutorSession.updated_time.desc()).limit(limit).offset(offset)

                result = await db.execute(query)
                sessions = result.scalars().all()

                return [
                    {
                        "id": session.id,
                        "subject": session.subject,
                        "topic": session.topic,
                        "difficulty": session.difficulty,
                        "current_phase": session.current_phase,
                        "understanding_level": session.understanding_level,
                        "total_questions": session.total_questions,
                        "correct_answers": session.correct_answers,
                        "is_active": session.is_active,
                        "created_time": session.created_time,
                        "updated_time": session.updated_time,
                        "completed_at": session.completed_at
                    }
                    for session in sessions
                ]

            except Exception as e:
                logger.error(f"获取用户会话列表失败: {e}")
                return []

    async def get_or_create_student_progress(self,
                                           user_id: str,
                                           subject: str,
                                           topic: str) -> Dict[str, Any]:
        """获取或创建学生进度记录"""
        async with get_db_session() as db:
            try:
                # 先尝试获取现有记录
                result = await db.execute(
                    select(StudentProgress)
                    .where(
                        StudentProgress.user_id == user_id,
                        StudentProgress.subject == subject,
                        StudentProgress.topic == topic
                    )
                )
                progress = result.scalar_one_or_none()

                if not progress:
                    # 创建新记录
                    progress = StudentProgress(
                        user_id=user_id,
                        subject=subject,
                        topic=topic,
                        total_sessions=0,
                        completed_sessions=0,
                        average_understanding=0.0,
                        strengths=[],
                        weaknesses=[],
                        confusion_history=[]
                    )
                    db.add(progress)
                    await db.commit()
                    await db.refresh(progress)

                return {
                    "id": progress.id,
                    "user_id": progress.user_id,
                    "subject": progress.subject,
                    "topic": progress.topic,
                    "total_sessions": progress.total_sessions,
                    "completed_sessions": progress.completed_sessions,
                    "average_understanding": progress.average_understanding,
                    "strengths": progress.strengths or [],
                    "weaknesses": progress.weaknesses or [],
                    "confusion_history": progress.confusion_history or [],
                    "preferred_teaching_style": progress.preferred_teaching_style,
                    "response_pattern": progress.response_pattern,
                    "first_learned": progress.first_learned,
                    "last_studied": progress.last_studied
                }

            except Exception as e:
                logger.error(f"获取学生进度失败: {e}")
                return {}

    async def update_student_progress(self,
                                    user_id: str,
                                    subject: str,
                                    topic: str,
                                    session_data: Dict[str, Any]) -> bool:
        """更新学生学习进度"""
        async with get_db_session() as db:
            try:
                # 获取现有进度
                result = await db.execute(
                    select(StudentProgress)
                    .where(
                        StudentProgress.user_id == user_id,
                        StudentProgress.subject == subject,
                        StudentProgress.topic == topic
                    )
                )
                progress = result.scalar_one_or_none()

                if not progress:
                    # 如果不存在，先创建
                    await self.get_or_create_student_progress(user_id, subject, topic)
                    result = await db.execute(
                        select(StudentProgress)
                        .where(
                            StudentProgress.user_id == user_id,
                            StudentProgress.subject == subject,
                            StudentProgress.topic == topic
                        )
                    )
                    progress = result.scalar_one_or_none()

                # 计算新的平均理解程度
                current_understanding = session_data.get("understanding_level", 0.5)
                new_total = progress.total_sessions + 1
                new_avg = (progress.average_understanding * progress.total_sessions + current_understanding) / new_total

                # 更新统计
                update_data = {
                    "total_sessions": new_total,
                    "average_understanding": new_avg,
                    "last_studied": datetime.now(),
                    "updated_time": datetime.now()
                }

                # 如果会话完成，增加完成数
                if session_data.get("is_completed", False):
                    update_data["completed_sessions"] = progress.completed_sessions + 1

                # 更新困惑历史
                if session_data.get("confusion_points"):
                    confusion_history = progress.confusion_history or []
                    confusion_history.extend(session_data["confusion_points"])
                    # 保留最近的20个困惑点
                    update_data["confusion_history"] = confusion_history[-20:]

                await db.execute(
                    update(StudentProgress)
                    .where(StudentProgress.id == progress.id)
                    .values(**update_data)
                )

                await db.commit()
                logger.info(f"更新学生进度成功: {user_id}, {subject}-{topic}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"更新学生进度失败: {e}")
                return False

    async def get_conversation_history(self,
                                     session_id: str,
                                     limit: int = 50) -> List[Dict[str, Any]]:
        """获取对话历史"""
        async with get_db_session() as db:
            try:
                result = await db.execute(
                    select(TutorMessage)
                    .where(TutorMessage.session_id == session_id)
                    .order_by(TutorMessage.timestamp.desc())
                    .limit(limit)
                )
                messages = result.scalars().all()

                return [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "message_type": msg.message_type,
                        "teaching_phase": msg.teaching_phase,
                        "understanding_level": msg.understanding_level,
                        "response_type": msg.response_type,
                        "confusion_points": msg.confusion_points or [],
                        "timestamp": msg.timestamp
                    }
                    for msg in reversed(messages)  # 返回正序
                ]

            except Exception as e:
                logger.error(f"获取对话历史失败: {e}")
                return []

    async def delete_session(self, session_id: str) -> bool:
        """删除会话（级联删除消息）"""
        async with get_db_session() as db:
            try:
                await db.execute(
                    delete(TutorSession)
                    .where(TutorSession.id == session_id)
                )
                await db.commit()
                logger.info(f"删除会话成功: {session_id}")
                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"删除会话失败: {e}")
                return False

    async def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户的学习统计"""
        async with get_db_session() as db:
            try:
                # 总会话数
                total_sessions_result = await db.execute(
                    select(func.count(TutorSession.id))
                    .where(TutorSession.user_id == user_id)
                )
                total_sessions = total_sessions_result.scalar() or 0

                # 完成的会话数
                completed_sessions_result = await db.execute(
                    select(func.count(TutorSession.id))
                    .where(
                        TutorSession.user_id == user_id,
                        TutorSession.is_active == False
                    )
                )
                completed_sessions = completed_sessions_result.scalar() or 0

                # 平均理解程度
                avg_understanding_result = await db.execute(
                    select(func.avg(TutorSession.understanding_level))
                    .where(TutorSession.user_id == user_id)
                )
                avg_understanding = avg_understanding_result.scalar() or 0.0

                # 学习的科目数
                subjects_result = await db.execute(
                    select(func.count(func.distinct(TutorSession.subject)))
                    .where(TutorSession.user_id == user_id)
                )
                subjects_count = subjects_result.scalar() or 0

                # 总学习时长（分钟）
                total_duration_result = await db.execute(
                    select(func.sum(TutorSession.session_duration))
                    .where(TutorSession.user_id == user_id)
                )
                total_duration_seconds = total_duration_result.scalar() or 0
                total_duration_minutes = total_duration_seconds // 60

                return {
                    "total_sessions": total_sessions,
                    "completed_sessions": completed_sessions,
                    "completion_rate": completed_sessions / total_sessions if total_sessions > 0 else 0,
                    "average_understanding": round(avg_understanding, 2),
                    "subjects_studied": subjects_count,
                    "total_study_time_minutes": total_duration_minutes,
                    "last_activity": await self._get_last_activity(db, user_id)
                }

            except Exception as e:
                logger.error(f"获取用户统计失败: {e}")
                return {}

    async def _get_last_activity(self, db: AsyncSession, user_id: str) -> Optional[datetime]:
        """获取最后活动时间"""
        try:
            result = await db.execute(
                select(TutorSession.updated_time)
                .where(TutorSession.user_id == user_id)
                .order_by(TutorSession.updated_time.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except:
            return None


# 全局实例
tutor_context_service = TutorContextService()
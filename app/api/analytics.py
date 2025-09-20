"""
学习分析与统计 API
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from loguru import logger

from app.core.database import get_db
from app.services.auth_service import get_current_user, get_current_teacher, get_current_student
from app.models.auth_models import ConfigUser as User, ConfigUser
from app.models.database_models import (
    Class,
    ClassStudent,
    Homework,
    StudentHomework,
    ChatSession,
    ChatMessage,
    Question,
)
from app.models.pydantic_models import BaseResponse


router = APIRouter(prefix="/analytics", tags=["学习分析"])


def _safe_div(n: float, d: float) -> float:
    return float(n) / float(d) if d else 0.0


@router.get("/student/{student_id}/report", response_model=BaseResponse, summary="学生学习报告")
async def get_student_report(
    student_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数范围"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """汇总学生的学习对话与作业进度情况。教师可查看任意学生，本人可查看自己的。"""
    try:
        if getattr(current_user.user_role, "value", current_user.user_role) == "student" and current_user.user_id != student_id:
            raise HTTPException(status_code=403, detail="无权查看其他学生报告")

        since = datetime.utcnow() - timedelta(days=days)

        # 聊天会话统计
        cs_q = select(ChatSession).where(ChatSession.student_id == student_id)
        cs = (await db.execute(cs_q)).scalars().all()
        total_sessions = len(cs)
        total_messages = sum(s.message_count or 0 for s in cs)
        avg_session_length = _safe_div(total_messages, total_sessions)

        # 计算最活跃学科
        # 取问题的 subject
        if cs:
            q_ids = list({s.question_id for s in cs if s.question_id})
            subj_map: Dict[str, int] = {}
            if q_ids:
                q_rs = await db.execute(select(Question.id, Question.subject).where(Question.id.in_(q_ids)))
                for qid, subj in q_rs.all():
                    key = (subj or "通用")
                    subj_map[key] = subj_map.get(key, 0) + 1
            most_active_subject = max(subj_map.items(), key=lambda x: x[1])[0] if subj_map else None
        else:
            most_active_subject = None

        # 作业统计
        sh_q = select(StudentHomework).where(StudentHomework.student_id == student_id)
        sh_rows = (await db.execute(sh_q)).scalars().all()
        total_homeworks = len(sh_rows)
        avg_completion = _safe_div(sum((r.completion_percentage or 0.0) for r in sh_rows), total_homeworks)

        # 简单弱项识别：对话涉及知识点统计（需要 Question.knowledge_points）
        weak_points: List[str] = []
        if cs:
            q_ids = list({s.question_id for s in cs if s.question_id})
            if q_ids:
                q_rs = await db.execute(select(Question.knowledge_points).where(Question.id.in_(q_ids)))
                freq: Dict[str, int] = {}
                for (kp_list,) in q_rs.all():
                    for kp in (kp_list or []):
                        freq[kp] = freq.get(kp, 0) + 1
                weak_points = [k for k, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]

        data = {
            "student_id": student_id,
            "time_range_days": days,
            "learning_summary": {
                "total_questions": len({s.question_id for s in cs if s.question_id}),
                "total_chat_sessions": total_sessions,
                "average_session_length": round(avg_session_length, 2),
                "most_active_subject": most_active_subject,
            },
            "homework_summary": {
                "total_homeworks": total_homeworks,
                "average_completion_rate": round(avg_completion, 2),
            },
            "weak_knowledge_points": weak_points,
        }

        return BaseResponse(success=True, message="获取学生学习报告成功", data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学生学习报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取学生学习报告失败")


@router.get("/class/{class_id}/overview", response_model=BaseResponse, summary="班级学习概览")
async def get_class_overview(
    class_id: str,
    days: int = Query(30, ge=1, le=365, description="统计天数范围"),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    """为教师提供班级层面的学习情况概览，字段适配前端统计弹窗。"""
    try:
        # 班级校验与权限
        c = (await db.execute(select(Class).where(Class.id == class_id))).scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="班级不存在")
        if c.teacher_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="无权查看该班级统计")

        since = datetime.utcnow() - timedelta(days=days)

        # 学生列表
        stu_rs = await db.execute(select(ClassStudent.student_id).where(ClassStudent.class_id == class_id))
        student_ids = [row[0] for row in stu_rs.all()]
        total_students = len(student_ids)

        # 班级作业
        hw_rs = await db.execute(select(Homework.id).where(Homework.class_id == class_id))
        hw_ids = [row[0] for row in hw_rs.all()]
        total_homeworks = len(hw_ids)

        # 完成率统计
        avg_completion = 0.0
        high = medium = low = 0
        if hw_ids and student_ids:
            sh_rs = await db.execute(
                select(StudentHomework.completion_percentage).where(
                    StudentHomework.homework_id.in_(hw_ids),
                    StudentHomework.student_id.in_(student_ids),
                )
            )
            rates = [r[0] or 0.0 for r in sh_rs.all()]
            if rates:
                avg_completion = sum(rates) / len(rates)
                high = round(100 * _safe_div(len([r for r in rates if r >= 80]), len(rates)))
                medium = round(100 * _safe_div(len([r for r in rates if 50 <= r < 80]), len(rates)))
                low = round(100 * _safe_div(len([r for r in rates if r < 50]), len(rates)))

        # 活跃度：以最近 days 天是否有对话为准
        active = inactive = 0
        if student_ids:
            act_rs = await db.execute(
                select(ChatSession.student_id, func.max(ChatSession.last_interaction_at)).where(
                    ChatSession.student_id.in_(student_ids)
                ).group_by(ChatSession.student_id)
            )
            last_map = {sid: ts for sid, ts in act_rs.all()}
            for sid in student_ids:
                ts = last_map.get(sid)
                if ts and ts >= since:
                    active += 1
                else:
                    inactive += 1

        # 平均登录次数
        avg_login = 0
        if student_ids:
            u_rs = await db.execute(select(ConfigUser.user_login_count).where(ConfigUser.user_id.in_(student_ids)))
            counts = [x[0] or 0 for x in u_rs.all()]
            if counts:
                avg_login = round(sum(counts) / len(counts))

        data = {
            "totalStudents": total_students,
            "totalHomeworks": total_homeworks,
            "averageCompletionRate": round(avg_completion, 2),
            "highCompletionRate": high,
            "mediumCompletionRate": medium,
            "lowCompletionRate": low,
            "activeStudents": active,
            "inactiveStudents": inactive,
            "averageLoginCount": avg_login,
        }

        return BaseResponse(success=True, message="获取班级学习概览成功", data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取班级学习概览失败: {e}")
        raise HTTPException(status_code=500, detail="获取班级学习概览失败")


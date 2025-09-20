"""
智能教学API端点
提供循循善诱的AI教学功能
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.intelligent_tutor_service import (
    intelligent_tutor,
    DifficultyLevel,
    TeachingPhase
)
from app.services.tutor_context_service import tutor_context_service
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/intelligent-tutor", tags=["智能教学"])


class StartSessionRequest(BaseModel):
    """开始学习会话请求"""
    subject: str
    topic: str
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_objectives: Optional[List[str]] = None


class StartSessionResponse(BaseModel):
    """开始学习会话响应"""
    session_id: str
    initial_question: str
    subject: str
    topic: str
    difficulty: str


class StudentInputRequest(BaseModel):
    """学生输入请求"""
    session_id: str
    content: str


class StudentInputResponse(BaseModel):
    """学生输入响应"""
    success: bool
    session_id: str
    ai_response: str
    current_phase: Optional[str] = None
    understanding_level: float = 0.5
    next_action: Optional[str] = None
    encouragement_needed: bool = False
    error_message: Optional[str] = None


class SessionInfo(BaseModel):
    """会话信息"""
    id: str
    subject: str
    topic: str
    difficulty: str
    current_phase: str
    understanding_level: float
    total_questions: int
    correct_answers: int
    is_active: bool
    created_time: str
    updated_time: str


class MessageInfo(BaseModel):
    """消息信息"""
    id: str
    role: str
    content: str
    message_type: Optional[str]
    teaching_phase: Optional[str]
    understanding_level: Optional[float]
    response_type: Optional[str]
    timestamp: str


@router.post("/start-session", response_model=StartSessionResponse)
async def start_learning_session(
    request: StartSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """开始新的学习会话"""
    try:
        user_id = current_user["user_id"]

        # 使用智能教学服务生成初始问题
        session_data = await intelligent_tutor.start_learning_session(
            user_id=user_id,
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty,
            learning_objectives=request.learning_objectives
        )

        # 在数据库中创建会话记录
        session_id = await tutor_context_service.create_session(
            user_id=user_id,
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty,
            learning_objectives=request.learning_objectives or [],
            key_concepts=[]
        )

        # 记录初始问题
        await tutor_context_service.add_message(
            session_id=session_id,
            role="assistant",
            content=session_data["initial_question"],
            message_type="initial_assessment",
            teaching_phase=TeachingPhase.INITIAL_ASSESSMENT.value
        )

        return StartSessionResponse(
            session_id=session_id,
            initial_question=session_data["initial_question"],
            subject=request.subject,
            topic=request.topic,
            difficulty=request.difficulty.value
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始学习会话失败: {str(e)}")


@router.post("/student-input", response_model=StudentInputResponse)
async def process_student_input(
    request: StudentInputRequest,
    current_user: dict = Depends(get_current_user)
):
    """处理学生输入"""
    try:
        user_id = current_user["user_id"]

        # 验证会话是否属于当前用户
        session_data = await tutor_context_service.get_session(request.session_id)
        if not session_data or session_data["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        if not session_data["is_active"]:
            raise HTTPException(status_code=400, detail="会话已结束")

        # 记录学生输入
        await tutor_context_service.add_message(
            session_id=request.session_id,
            role="user",
            content=request.content
        )

        # 使用智能教学服务处理输入
        context = {
            "user_id": user_id,
            "subject": session_data["subject"],
            "topic": session_data["topic"],
            "difficulty": session_data["difficulty"],
            "learning_objectives": session_data["learning_objectives"],
            "current_phase": session_data["current_phase"],
            "understanding_level": session_data["understanding_level"]
        }

        result = await intelligent_tutor.process_student_input(
            session_id=request.session_id,
            student_input=request.content,
            context=context
        )

        if result["success"]:
            # 记录AI回复
            await tutor_context_service.add_message(
                session_id=request.session_id,
                role="assistant",
                content=result["ai_response"],
                message_type=result.get("next_action"),
                teaching_phase=result.get("current_phase"),
                understanding_level=result.get("understanding_level")
            )

            # 如果学习完成，结束会话
            if result.get("current_phase") == TeachingPhase.COMPLETED.value:
                await tutor_context_service.complete_session(request.session_id)

                # 更新学生进度
                await tutor_context_service.update_student_progress(
                    user_id=user_id,
                    subject=session_data["subject"],
                    topic=session_data["topic"],
                    session_data={
                        "understanding_level": result.get("understanding_level", 0.5),
                        "is_completed": True
                    }
                )

        return StudentInputResponse(
            success=result["success"],
            session_id=request.session_id,
            ai_response=result["ai_response"],
            current_phase=result.get("current_phase"),
            understanding_level=result.get("understanding_level", 0.5),
            next_action=result.get("next_action"),
            encouragement_needed=result.get("encouragement_needed", False),
            error_message=result.get("error_message")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理学生输入失败: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    limit: int = 10,
    offset: int = 0,
    active_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """获取用户的学习会话列表"""
    try:
        user_id = current_user["user_id"]
        sessions = await tutor_context_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset,
            active_only=active_only
        )

        return [
            SessionInfo(
                id=session["id"],
                subject=session["subject"],
                topic=session["topic"],
                difficulty=session["difficulty"],
                current_phase=session["current_phase"],
                understanding_level=session["understanding_level"],
                total_questions=session["total_questions"],
                correct_answers=session["correct_answers"],
                is_active=session["is_active"],
                created_time=session["created_time"].isoformat(),
                updated_time=session["updated_time"].isoformat()
            )
            for session in sessions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """获取会话详情"""
    try:
        user_id = current_user["user_id"]
        session_data = await tutor_context_service.get_session(session_id)

        if not session_data or session_data["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        return {
            "session": {
                "id": session_data["id"],
                "subject": session_data["subject"],
                "topic": session_data["topic"],
                "difficulty": session_data["difficulty"],
                "learning_objectives": session_data["learning_objectives"],
                "key_concepts": session_data["key_concepts"],
                "current_phase": session_data["current_phase"],
                "understanding_level": session_data["understanding_level"],
                "teaching_strategy": session_data["teaching_strategy"],
                "total_questions": session_data["total_questions"],
                "correct_answers": session_data["correct_answers"],
                "session_duration": session_data["session_duration"],
                "is_active": session_data["is_active"],
                "created_time": session_data["created_time"].isoformat(),
                "updated_time": session_data["updated_time"].isoformat()
            },
            "messages": [
                MessageInfo(
                    id=msg["id"],
                    role=msg["role"],
                    content=msg["content"],
                    message_type=msg["message_type"],
                    teaching_phase=msg["teaching_phase"],
                    understanding_level=msg["understanding_level"],
                    response_type=msg["response_type"],
                    timestamp=msg["timestamp"].isoformat()
                )
                for msg in session_data["messages"]
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """手动结束会话"""
    try:
        user_id = current_user["user_id"]
        session_data = await tutor_context_service.get_session(session_id)

        if not session_data or session_data["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        if not session_data["is_active"]:
            raise HTTPException(status_code=400, detail="会话已结束")

        success = await tutor_context_service.complete_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="结束会话失败")

        # 更新学生进度
        await tutor_context_service.update_student_progress(
            user_id=user_id,
            subject=session_data["subject"],
            topic=session_data["topic"],
            session_data={
                "understanding_level": session_data["understanding_level"],
                "is_completed": True
            }
        )

        return {"message": "会话已成功结束"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"结束会话失败: {str(e)}")


@router.get("/progress/{subject}/{topic}")
async def get_student_progress(
    subject: str,
    topic: str,
    current_user: dict = Depends(get_current_user)
):
    """获取学生在特定主题的学习进度"""
    try:
        user_id = current_user["user_id"]
        progress = await tutor_context_service.get_or_create_student_progress(
            user_id=user_id,
            subject=subject,
            topic=topic
        )

        return progress

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习进度失败: {str(e)}")


@router.get("/statistics")
async def get_learning_statistics(
    current_user: dict = Depends(get_current_user)
):
    """获取用户的学习统计数据"""
    try:
        user_id = current_user["user_id"]
        stats = await tutor_context_service.get_session_statistics(user_id)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习统计失败: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除会话"""
    try:
        user_id = current_user["user_id"]
        session_data = await tutor_context_service.get_session(session_id)

        if not session_data or session_data["user_id"] != user_id:
            raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

        success = await tutor_context_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="删除会话失败")

        return {"message": "会话已成功删除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")
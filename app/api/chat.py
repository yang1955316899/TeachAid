"""
聊天相关API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json as _json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import uuid
from datetime import datetime

from app.core.database import get_db
from app.services.auth_service import get_current_student
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Question, ChatSession, ChatMessage
from app.models.pydantic_models import (
    BaseResponse, ChatSessionStart, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse
)

router = APIRouter(prefix="/chat", tags=["智能对话"])


@router.post("/sessions", response_model=BaseResponse, summary="开始对话会话")
async def start_chat_session(
    session_data: ChatSessionStart,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    开始新的对话会话
    
    - **question_id**: 题目ID
    """
    try:
        # 验证题目是否存在且可访问
        result = await db.execute(
            select(Question).where(
                Question.id == session_data.question_id,
                Question.is_active == True,
                Question.is_public == True
            )
        )
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在或无权访问"
            )
        
        # 创建对话会话
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(
            id=session_id,
            student_id=current_user.id,
            question_id=session_data.question_id,
            session_data={
                "start_time": datetime.utcnow().isoformat(),
                "question_title": question.title,
                "subject": question.subject
            },
            started_at=datetime.utcnow(),
            last_interaction_at=datetime.utcnow()
        )
        
        db.add(chat_session)
        await db.commit()
        
        logger.info(f"对话会话创建成功: {session_id}")
        
        return BaseResponse(
            success=True,
            message="对话会话创建成功",
            data={
                "session_id": session_id,
                "question_id": question.id,
                "started_at": chat_session.started_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建对话会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建对话会话失败"
        )


@router.post("/{session_id}/stream", summary="SSE流式对话")
async def stream_chat(
    session_id: str,
    message: ChatMessageCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE流式响应：逐步返回AI回复片段。
    """
    # 简化：使用本模块的占位AI回复生成器，按词片段流式发送
    # 验证会话归属
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.student_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="对话会话不存在")

    async def event_generator():
        # 先保存用户消息
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=message.content,
            selected_text=message.selected_text,
            created_at=datetime.utcnow()
        )
        db.add(user_msg)
        await db.commit()

        reply = _generate_ai_reply(message.content, message.selected_text)
        words = reply.split()
        buffer = []
        for i, w in enumerate(words, 1):
            buffer.append(w)
            # 每5个词发送一块
            if i % 5 == 0:
                chunk = " ".join(buffer)
                yield f"data: {{\"content\": {_json.dumps(chunk)} }}\n\n"
                buffer.clear()
                # 轻微延迟以模拟生成
                import asyncio
                await asyncio.sleep(0.05)
        if buffer:
            chunk = " ".join(buffer)
            yield f"data: {{\"content\": {_json.dumps(chunk)} }}\n\n"

        # 保存AI完整消息
        ai_msg = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=reply,
            created_at=datetime.utcnow()
        )
        db.add(ai_msg)
        session.message_count = (session.message_count or 0) + 2
        session.last_interaction_at = datetime.utcnow()
        await db.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{session_id}/messages", response_model=BaseResponse, summary="发送消息")
async def send_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    发送对话消息
    
    - **content**: 消息内容
    - **selected_text**: 选中的文本（可选）
    """
    try:
        # 验证会话是否存在且属于当前用户
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.student_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话会话不存在"
            )
        
        # 保存用户消息
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=message_data.content,
            selected_text=message_data.selected_text,
            created_at=datetime.utcnow()
        )
        
        db.add(user_message)
        
        # 生成AI回复（暂时使用简单回复，后续集成AI）
        ai_reply = _generate_ai_reply(message_data.content, message_data.selected_text)
        
        ai_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=ai_reply,
            created_at=datetime.utcnow()
        )
        
        db.add(ai_message)
        
        # 更新会话信息
        session.message_count = (session.message_count or 0) + 2
        session.last_interaction_at = datetime.utcnow()
        
        await db.commit()
        
        return BaseResponse(
            success=True,
            message="消息发送成功",
            data={
                "content": ai_reply,
                "message_id": ai_message.id,
                "timestamp": ai_message.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送消息失败"
        )


@router.get("/{session_id}/messages", response_model=BaseResponse, summary="获取对话历史")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话历史消息
    """
    try:
        # 验证会话是否存在且属于当前用户
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.student_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话会话不存在"
            )
        
        # 获取消息列表
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = result.scalars().all()
        
        # 转换为响应格式
        message_responses = []
        for msg in messages:
            message_responses.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "selected_text": msg.selected_text,
                "created_at": msg.created_at.isoformat()
            })
        
        return BaseResponse(
            success=True,
            message="获取对话历史成功",
            data={
                "messages": message_responses,
                "session_info": {
                    "session_id": session.id,
                    "question_id": session.question_id,
                    "started_at": session.started_at.isoformat(),
                    "message_count": session.message_count
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取对话历史失败"
        )


@router.post("/{session_id}/end", response_model=BaseResponse, summary="结束对话")
async def end_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    结束对话会话
    """
    try:
        # 验证会话是否存在且属于当前用户
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.student_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话会话不存在"
            )
        
        # 更新会话状态
        session.last_interaction_at = datetime.utcnow()
        # 可以添加会话结束状态字段
        
        await db.commit()
        
        logger.info(f"对话会话结束: {session_id}")
        
        return BaseResponse(
            success=True,
            message="对话会话已结束"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"结束对话会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="结束对话会话失败"
        )


def _generate_ai_reply(user_content: str, selected_text: str = None) -> str:
    """
    生成AI回复（临时实现，后续替换为真实AI调用）
    """
    if selected_text:
        return f"关于你选中的内容\"{selected_text}\"，这是一个很好的问题！让我来帮你分析一下。首先，我们需要理解这个问题的关键点..."
    
    if any(keyword in user_content for keyword in ["不懂", "不会", "不明白"]):
        return "没关系，学习过程中遇到问题很正常。让我们一步步来分析这个问题，你会发现其实并不难。首先，你觉得应该从哪个角度开始思考呢？"
    
    if "为什么" in user_content:
        return "这个问题问得很好！要理解'为什么'，我们需要从基本原理开始分析。你能先说说你对这个问题的理解吗？这样我可以更好地帮助你。"
    
    if any(keyword in user_content for keyword in ["步骤", "怎么做", "方法"]):
        return "好的，让我为你详细讲解解题步骤。首先，我们需要分析题目要求，然后确定解题思路，最后逐步推导答案。你觉得第一步应该做什么呢？"
    
    return "这是一个很好的问题！我很高兴能帮助你。在学习过程中，重要的不仅仅是得到答案，更是理解解题思路。你能先告诉我你的想法吗？"

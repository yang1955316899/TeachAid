"""
学生笔记模块 API
支持笔记的增删改查、与题目关联、AI交互内容存储等功能
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.models.database_models import Note, Question, ChatSession, ChatMessage, Homework
from app.models.auth_models import ConfigUser, UserRole
from app.models.pydantic_models import (
    NoteCreate, NoteUpdate, NoteResponse, NoteListResponse,
    NoteWithQuestionResponse, NoteSummaryResponse
)

router = APIRouter(prefix="/notes", tags=["笔记管理"])


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """创建新笔记"""

    # 构建笔记数据
    note_dict = {
        "title": note_data.title,
        "content": note_data.content,
        "summary": note_data.summary,
        "category": note_data.category,
        "tags": note_data.tags or [],
        "subject": note_data.subject,
        "knowledge_points": note_data.knowledge_points or [],
        "difficulty_level": note_data.difficulty_level,
        "mastery_level": note_data.mastery_level,
        "is_starred": note_data.is_starred,
        "is_public": note_data.is_public,
        "student_id": current_user.user_id
    }

    # 如果关联题目，存储题目快照
    if note_data.question_id:
        question_result = await db.execute(
            select(Question).where(Question.id == note_data.question_id)
        )
        question = question_result.scalars().first()
        if question:
            note_dict.update({
                "question_id": question.id,
                "question_title": question.title,
                "question_content": question.content
            })

    # 如果关联对话会话，存储AI对话快照
    if note_data.chat_session_id:
        session_result = await db.execute(
            select(ChatSession).where(ChatSession.id == note_data.chat_session_id)
        )
        chat_session = session_result.scalars().first()
        if chat_session:
            # 获取对话消息
            messages_result = await db.execute(
                select(ChatMessage).where(ChatMessage.session_id == note_data.chat_session_id)
                .order_by(ChatMessage.created_at)
            )
            messages = messages_result.scalars().all()

            chat_data = []
            for msg in messages:
                chat_data.append({
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "selected_text": msg.selected_text
                })

            note_dict.update({
                "chat_session_id": chat_session.id,
                "chat_messages": chat_data
            })

    # 如果关联作业，存储作业快照
    if note_data.homework_id:
        homework_result = await db.execute(
            select(Homework).where(Homework.id == note_data.homework_id)
        )
        homework = homework_result.scalars().first()
        if homework:
            note_dict.update({
                "homework_id": homework.id,
                "homework_title": homework.title
            })

    # 创建笔记
    note = Note(**note_dict)
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note


@router.get("/", response_model=NoteListResponse)
async def get_notes(
    category: Optional[str] = Query(None, description="笔记分类筛选"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    is_starred: Optional[bool] = Query(None, description="是否收藏"),
    is_archived: Optional[bool] = Query(False, description="是否显示归档笔记"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_time", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """获取用户笔记列表"""

    # 构建查询条件
    conditions = [Note.student_id == current_user.user_id]

    if category:
        conditions.append(Note.category == category)

    if subject:
        conditions.append(Note.subject == subject)

    if is_starred is not None:
        conditions.append(Note.is_starred == is_starred)

    if not is_archived:
        conditions.append(Note.is_archived == False)

    if search:
        conditions.append(
            or_(
                Note.title.contains(search),
                Note.content.contains(search),
                Note.summary.contains(search)
            )
        )

    # 构建查询
    query = select(Note).where(and_(*conditions))

    # 排序
    if hasattr(Note, sort_by):
        order_col = getattr(Note, sort_by)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(order_col))

    # 分页
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # 执行查询
    result = await db.execute(query)
    notes = result.scalars().all()

    # 获取总数
    count_query = select(Note).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return {
        "notes": notes,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{note_id}", response_model=NoteWithQuestionResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """获取笔记详情"""

    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                or_(
                    Note.student_id == current_user.user_id,
                    Note.is_public == True
                )
            )
        )
    )
    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    # 更新最后复习时间
    if note.student_id == current_user.user_id:
        note.last_reviewed_at = datetime.utcnow()
        note.review_count += 1
        await db.commit()

    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """更新笔记"""

    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                Note.student_id == current_user.user_id
            )
        )
    )
    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权限")

    # 更新字段
    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(note, field):
            setattr(note, field, value)

    await db.commit()
    await db.refresh(note)

    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """删除笔记"""

    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                Note.student_id == current_user.user_id
            )
        )
    )
    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权限")

    await db.delete(note)
    await db.commit()

    return {"message": "笔记已删除"}


@router.post("/from-chat/{session_id}", response_model=NoteResponse)
async def create_note_from_chat(
    session_id: str,
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """从AI对话创建笔记"""

    # 验证对话会话
    session_result = await db.execute(
        select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.student_id == current_user.user_id
            )
        )
    )
    chat_session = session_result.scalars().first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="对话会话不存在")

    # 获取对话消息
    messages_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()

    # 构建对话快照
    chat_data = []
    for msg in messages:
        chat_data.append({
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "selected_text": msg.selected_text
        })

    # 获取关联的题目信息
    question_data = {}
    if chat_session.question_id:
        question_result = await db.execute(
            select(Question).where(Question.id == chat_session.question_id)
        )
        question = question_result.scalars().first()
        if question:
            question_data = {
                "question_id": question.id,
                "question_title": question.title,
                "question_content": question.content,
                "subject": question.subject,
                "knowledge_points": question.knowledge_points
            }

    # 创建笔记
    note = Note(
        title=note_data.title,
        content=note_data.content,
        summary=note_data.summary,
        category="chat",
        tags=note_data.tags or [],
        chat_session_id=session_id,
        chat_messages=chat_data,
        mastery_level=note_data.mastery_level,
        is_starred=note_data.is_starred,
        student_id=current_user.user_id,
        **question_data
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note


@router.get("/summary/stats", response_model=NoteSummaryResponse)
async def get_notes_summary(
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """获取笔记统计摘要"""

    # 总笔记数
    total_result = await db.execute(
        select(Note).where(Note.student_id == current_user.user_id)
    )
    total_notes = len(total_result.scalars().all())

    # 收藏笔记数
    starred_result = await db.execute(
        select(Note).where(
            and_(
                Note.student_id == current_user.user_id,
                Note.is_starred == True
            )
        )
    )
    starred_notes = len(starred_result.scalars().all())

    # 按分类统计
    categories_result = await db.execute(
        select(Note).where(Note.student_id == current_user.user_id)
    )
    notes = categories_result.scalars().all()

    category_stats = {}
    subject_stats = {}

    for note in notes:
        # 分类统计
        if note.category not in category_stats:
            category_stats[note.category] = 0
        category_stats[note.category] += 1

        # 学科统计
        if note.subject and note.subject not in subject_stats:
            subject_stats[note.subject] = 0
        if note.subject:
            subject_stats[note.subject] += 1

    return {
        "total_notes": total_notes,
        "starred_notes": starred_notes,
        "category_stats": category_stats,
        "subject_stats": subject_stats
    }


@router.put("/{note_id}/star")
async def toggle_note_star(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """切换笔记收藏状态"""

    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                Note.student_id == current_user.user_id
            )
        )
    )
    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权限")

    note.is_starred = not note.is_starred
    await db.commit()

    return {"is_starred": note.is_starred}


@router.put("/{note_id}/archive")
async def toggle_note_archive(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: ConfigUser = Depends(get_current_user)
):
    """切换笔记归档状态"""

    result = await db.execute(
        select(Note).where(
            and_(
                Note.id == note_id,
                Note.student_id == current_user.user_id
            )
        )
    )
    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或无权限")

    note.is_archived = not note.is_archived
    await db.commit()

    return {"is_archived": note.is_archived}
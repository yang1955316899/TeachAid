"""
基础教务维度 API：年级、学科、章节
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.services.auth_service import get_current_user
from app.models.auth_models import ConfigUser as User
from app.models.database_models import Grade, Subject, Chapter

router = APIRouter(prefix="/taxonomy", tags=["教务维度"])


@router.get("/grades")
async def list_grades(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = await db.execute(select(Grade).order_by(Grade.level))
        items = [
            {
                "id": g.id,
                "name": g.name,
                "level": g.level,
            }
            for g in result.scalars().all()
        ]
        return {"success": True, "message": "ok", "data": {"items": items}}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取年级失败")


@router.get("/subjects")
async def list_subjects(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        result = await db.execute(select(Subject).order_by(Subject.name))
        items = [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
            }
            for s in result.scalars().all()
        ]
        return {"success": True, "message": "ok", "data": {"items": items}}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取学科失败")


@router.get("/chapters")
async def list_chapters(
    grade_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        conditions = []
        if grade_id:
            conditions.append(Chapter.grade_id == grade_id)
        if subject_id:
            conditions.append(Chapter.subject_id == subject_id)
        if parent_id is not None:
            conditions.append(Chapter.parent_id == parent_id)
        query = select(Chapter)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Chapter.sort_order.nulls_last(), Chapter.name)
        result = await db.execute(query)
        items = [
            {
                "id": c.id,
                "name": c.name,
                "grade_id": c.grade_id,
                "subject_id": c.subject_id,
                "parent_id": c.parent_id,
                "sort_order": c.sort_order,
            }
            for c in result.scalars().all()
        ]
        return {"success": True, "message": "ok", "data": {"items": items}}
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取章节失败")


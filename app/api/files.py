"""
文件上传管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.services.auth_service import get_current_teacher, get_current_user
from app.models.auth_models import ConfigUser as User
from app.models.database_models import FileUpload
from app.models.pydantic_models import (
    BaseResponse, PaginationQuery, PaginationResponse, FileUploadResponse
)

router = APIRouter(prefix="/files", tags=["文件管理"])

# 配置文件上传路径
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


@router.get("", response_model=PaginationResponse, summary="获取文件上传记录列表")
async def list_file_uploads(
    pagination: PaginationQuery = Depends(),
    file_type: Optional[str] = Query(None, description="文件类型筛选"),
    status: Optional[str] = Query(None, description="处理状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文件上传记录列表（分页）
    """
    try:
        # 构建查询条件
        conditions = []
        
        # 权限过滤
        if current_user.user_role != "admin":
            conditions.append(FileUpload.uploader_id == current_user.user_id)
        
        # 添加筛选条件
        if file_type:
            conditions.append(FileUpload.file_type == file_type)
        if status:
            conditions.append(FileUpload.status == status)
        if keyword:
            conditions.append(
                or_(
                    FileUpload.filename.contains(keyword),
                    FileUpload.original_filename.contains(keyword)
                )
            )
        
        # 查询总数
        count_query = select(func.count(FileUpload.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页查询
        offset = (pagination.page - 1) * pagination.size
        query = select(FileUpload)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(FileUpload.created_at.desc()).offset(offset).limit(pagination.size)
        
        result = await db.execute(query)
        files = result.scalars().all()
        
        # 转换为响应模型
        file_responses = [FileUploadResponse.from_orm(f) for f in files]
        
        return PaginationResponse(
            items=file_responses,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size
        )
        
    except Exception as e:
        logger.error(f"获取文件上传记录列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件上传记录列表失败"
        )


@router.get("/{file_id}", response_model=BaseResponse, summary="获取文件上传记录详情")
async def get_file_upload(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文件上传记录详情
    """
    try:
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件记录不存在"
            )
        
        # 权限检查
        if (current_user.user_role != "admin" and file_obj.uploader_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此文件"
            )
        
        return BaseResponse(
            success=True,
            message="获取文件记录详情成功",
            data=FileUploadResponse.from_orm(file_obj).__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件上传记录详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取文件上传记录详情失败"
        )


@router.post("/upload", response_model=BaseResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    is_public: bool = False,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文件（仅教师）
    """
    try:
        # 验证文件
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型，支持的类型：{', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 生成文件ID和路径
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        new_filename = f"{file_id}{file_ext}"
        
        # 确保上传目录存在
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, new_filename)
        
        # 保存文件
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
                file_size = len(content)
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文件保存失败"
            )
        
        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制，最大允许 {get_file_size(MAX_FILE_SIZE)}"
            )
        
        # 获取文件类型
        file_type = file_ext.lower()
        mime_type = file.content_type
        
        # 创建文件记录
        file_record = FileUpload(
            id=file_id,
            filename=new_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            mime_type=mime_type,
            status="uploaded",
            uploader_id=current_user.user_id,
            is_public=is_public
        )
        
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        
        logger.info(f"文件上传成功: {file_id}")
        
        return BaseResponse(
            success=True,
            message="文件上传成功",
            data=FileUploadResponse.from_orm(file_record).__dict__
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败"
        )


@router.get("/{file_id}/download", summary="下载文件")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    下载文件
    """
    try:
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 权限检查
        if (not file_obj.is_public and 
            current_user.user_role != "admin" and 
            file_obj.uploader_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权下载此文件"
            )
        
        # 检查文件是否存在
        if not os.path.exists(file_obj.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件已被删除"
            )
        
        from fastapi.responses import FileResponse
        
        return FileResponse(
            path=file_obj.file_path,
            filename=file_obj.original_filename,
            media_type=file_obj.mime_type or 'application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件下载失败"
        )


@router.delete("/{file_id}", response_model=BaseResponse, summary="删除文件")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除文件及其记录
    """
    try:
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 权限检查
        if (current_user.user_role != "admin" and file_obj.uploader_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此文件"
            )
        
        # 删除物理文件
        try:
            if os.path.exists(file_obj.file_path):
                os.remove(file_obj.file_path)
        except Exception as e:
            logger.warning(f"物理文件删除失败: {e}")
        
        # 删除数据库记录
        await db.delete(file_obj)
        await db.commit()
        
        logger.info(f"文件删除成功: {file_id}")
        
        return BaseResponse(
            success=True,
            message="文件删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"文件删除失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件删除失败"
        )


@router.put("/{file_id}/public", response_model=BaseResponse, summary="更新文件公开状态")
async def update_file_public_status(
    file_id: str,
    is_public: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新文件公开状态
    """
    try:
        result = await db.execute(
            select(FileUpload).where(FileUpload.id == file_id)
        )
        file_obj = result.scalar_one_or_none()
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 权限检查
        if (current_user.user_role != "admin" and file_obj.uploader_id != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此文件"
            )
        
        file_obj.is_public = is_public
        await db.commit()
        
        logger.info(f"文件公开状态更新成功: {file_id} -> {is_public}")
        
        return BaseResponse(
            success=True,
            message="文件公开状态更新成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"文件公开状态更新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件公开状态更新失败"
        )
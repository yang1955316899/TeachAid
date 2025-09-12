"""
文件处理服务 - 处理上传文件的解析和内容提取
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

import fitz  # PDF处理库
from PIL import Image
from fastapi import UploadFile, HTTPException
from loguru import logger

from app.core.config import settings
from app.core.unified_ai_framework import UnifiedAIFramework
from app.models.pydantic_models import FileProcessingStatus


class FileProcessorService:
    """文件处理服务"""
    
    def __init__(self):
        self.ai_framework = UnifiedAIFramework()
        self.upload_dir = Path(settings.file_upload.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 支持的文件类型
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        self.document_extensions = {'.pdf', '.txt'}
        self.all_extensions = self.image_extensions | self.document_extensions
        
    async def process_upload(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """处理文件上传"""
        try:
            # 验证文件
            validation_result = self._validate_file(file)
            if not validation_result["valid"]:
                raise HTTPException(status_code=400, detail=validation_result["error"])
            
            # 保存文件
            file_info = await self._save_file(file, user_id)
            
            # 启动后台处理
            asyncio.create_task(self._process_file_background(file_info))
            
            return {
                "file_id": file_info["id"],
                "filename": file_info["filename"], 
                "status": FileProcessingStatus.UPLOADED,
                "message": "文件上传成功，正在后台处理中"
            }
            
        except Exception as e:
            logger.error(f"文件上传处理失败: {e}")
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    
    def _validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """验证上传文件"""
        # 检查文件大小
        if hasattr(file, 'size') and file.size > settings.file_upload.max_size_bytes:
            return {
                "valid": False,
                "error": f"文件大小超过限制 ({settings.file_upload.max_size_mb}MB)"
            }
        
        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.all_extensions:
            return {
                "valid": False,
                "error": f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(self.all_extensions)}"
            }
        
        # 检查MIME类型
        mime_type, _ = mimetypes.guess_type(file.filename)
        allowed_mimes = [
            'image/jpeg', 'image/png', 'image/webp',
            'application/pdf', 'text/plain'
        ]
        
        if mime_type not in allowed_mimes:
            logger.warning(f"MIME类型检查失败: {mime_type}")
        
        return {"valid": True}
    
    async def _save_file(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """保存上传文件"""
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix.lower()
        safe_filename = f"{file_id}{file_ext}"
        
        # 创建用户目录
        user_dir = self.upload_dir / user_id
        user_dir.mkdir(exist_ok=True)
        
        file_path = user_dir / safe_filename
        
        # 保存文件
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 重置文件指针
        await file.seek(0)
        
        logger.info(f"文件保存成功: {file_path}")
        
        return {
            "id": file_id,
            "filename": safe_filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "file_type": file_ext[1:],  # 去掉点号
            "user_id": user_id
        }
    
    async def _process_file_background(self, file_info: Dict[str, Any]):
        """后台处理文件"""
        file_id = file_info["id"]
        file_path = file_info["file_path"]
        file_type = file_info["file_type"]
        
        try:
            logger.info(f"开始处理文件: {file_id}")
            
            # 根据文件类型选择处理方式
            if file_type in ['jpg', 'jpeg', 'png', 'webp']:
                processed_files = [file_path]
            elif file_type == 'pdf':
                processed_files = await self._split_pdf_pages(file_path)
            elif file_type == 'txt':
                processed_files = [file_path]
            else:
                raise ValueError(f"不支持的文件类型: {file_type}")
            
            # 提取内容
            extracted_questions = []
            for processed_file in processed_files:
                questions = await self._extract_questions(processed_file, file_type)
                extracted_questions.extend(questions)
            
            logger.info(f"文件处理完成: {file_id}，提取到 {len(extracted_questions)} 个题目")
            
            # TODO: 更新数据库状态
            # await self._update_file_status(file_id, FileProcessingStatus.COMPLETED, extracted_questions)
            
        except Exception as e:
            logger.error(f"文件处理失败: {file_id}, {e}")
            # TODO: 更新数据库错误状态
            # await self._update_file_status(file_id, FileProcessingStatus.FAILED, error=str(e))
    
    async def _split_pdf_pages(self, pdf_path: str) -> List[str]:
        """分割PDF页面"""
        try:
            doc = fitz.open(pdf_path)
            page_files = []
            
            base_path = Path(pdf_path)
            base_name = base_path.stem
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # 转换为高分辨率图片
                mat = fitz.Matrix(2, 2)  # 2倍分辨率
                pix = page.get_pixmap(matrix=mat)
                
                # 保存图片
                img_path = base_path.parent / f"{base_name}_page_{page_num + 1}.png"
                pix.save(str(img_path))
                page_files.append(str(img_path))
                
                pix = None  # 释放内存
            
            doc.close()
            
            logger.info(f"PDF分页完成: {len(page_files)} 页")
            return page_files
            
        except Exception as e:
            logger.error(f"PDF分页失败: {e}")
            raise
    
    async def _extract_questions(self, file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """从文件中提取题目"""
        try:
            if file_type in ['jpg', 'jpeg', 'png', 'webp']:
                return await self._extract_from_image(file_path)
            elif file_type == 'txt':
                return await self._extract_from_text(file_path)
            else:
                logger.warning(f"不支持的提取类型: {file_type}")
                return []
                
        except Exception as e:
            logger.error(f"题目提取失败: {file_path}, {e}")
            return []
    
    async def _extract_from_image(self, image_path: str) -> List[Dict[str, Any]]:
        """从图片中提取题目"""
        try:
            # 构建视觉AI提示
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的教学材料分析专家。请分析图片中的题目内容，提取以下信息：
1. 题目内容（完整题目描述）
2. 答案内容（如果有的话）
3. 学科类型
4. 题目类型
5. 知识点

请以JSON格式返回，格式如下：
{
    "questions": [
        {
            "content": "题目内容",
            "answer": "答案内容",
            "subject": "学科",
            "type": "题目类型",
            "knowledge_points": ["知识点1", "知识点2"]
        }
    ]
}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请分析这张图片中的题目内容"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{self._encode_image_base64(image_path)}"
                            }
                        }
                    ]
                }
            ]
            
            # 使用AI框架处理
            import litellm
            response = await litellm.acompletion(
                model="gpt-4o",  # 视觉模型
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # 解析JSON响应
            import json
            result = json.loads(content)
            questions = result.get("questions", [])
            
            logger.info(f"从图片提取到 {len(questions)} 个题目")
            return questions
            
        except Exception as e:
            logger.error(f"图片题目提取失败: {e}")
            return []
    
    async def _extract_from_text(self, text_path: str) -> List[Dict[str, Any]]:
        """从文本文件中提取题目"""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用AI分析文本内容
            messages = [
                {
                    "role": "system",
                    "content": """你是一个教学材料分析专家。请分析文本中的题目和答案，提取结构化信息。

请以JSON格式返回：
{
    "questions": [
        {
            "content": "题目内容",
            "answer": "答案内容",
            "subject": "推测的学科",
            "type": "题目类型",
            "knowledge_points": ["相关知识点"]
        }
    ]
}"""
                },
                {
                    "role": "user", 
                    "content": f"请分析以下文本内容：\n\n{content}"
                }
            ]
            
            import litellm
            response = await litellm.acompletion(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            import json
            result = json.loads(content)
            questions = result.get("questions", [])
            
            logger.info(f"从文本提取到 {len(questions)} 个题目")
            return questions
            
        except Exception as e:
            logger.error(f"文本题目提取失败: {e}")
            return []
    
    def _encode_image_base64(self, image_path: str) -> str:
        """将图片编码为base64"""
        import base64
        
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图片编码失败: {e}")
            return ""
    
    async def get_processing_status(self, file_id: str) -> Dict[str, Any]:
        """获取文件处理状态"""
        # TODO: 从数据库获取实际状态
        return {
            "file_id": file_id,
            "status": FileProcessingStatus.PROCESSING,
            "progress": 50,
            "message": "正在处理中..."
        }
    
    async def cleanup_temp_files(self, file_path: str):
        """清理临时文件"""
        try:
            base_path = Path(file_path)
            base_name = base_path.stem
            
            # 清理PDF分页生成的图片
            parent_dir = base_path.parent
            for temp_file in parent_dir.glob(f"{base_name}_page_*.png"):
                temp_file.unlink()
                logger.info(f"清理临时文件: {temp_file}")
                
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        path = Path(file_path)
        
        if not path.exists():
            return {"exists": False}
        
        stat = path.stat()
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "extension": path.suffix.lower(),
            "name": path.name
        }
"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, JSON, Text, Boolean, Integer, 
    ForeignKey, Float, func
)
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid4())


class Class(Base):
    """班级表"""
    __tablename__ = "data_classes"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    
    # 班级属性
    grade_level: Mapped[Optional[str]] = Column(String(20))  # 年级
    subject: Mapped[Optional[str]] = Column(String(50))      # 学科
    
    # 关联
    teacher_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    organization_id: Mapped[str] = Column(String(36), ForeignKey("config_organizations.organization_id"))
    
    # 班级设置
    max_students: Mapped[int] = Column(Integer, default=50)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    teacher = relationship("ConfigUser", foreign_keys=[teacher_id])
    organization = relationship("ConfigOrganization", back_populates="classes")
    homeworks = relationship("Homework", back_populates="class_obj")


class Question(Base):
    """题目表"""
    __tablename__ = "data_questions"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[Optional[str]] = Column(String(200))
    content: Mapped[str] = Column(Text, nullable=False)      # 题目内容
    
    # 答案相关
    original_answer: Mapped[Optional[str]] = Column(Text)    # 原始答案
    rewritten_answer: Mapped[Optional[str]] = Column(Text)   # AI改写后的答案
    
    # 分类信息
    subject: Mapped[Optional[str]] = Column(String(50))      # 学科
    question_type: Mapped[Optional[str]] = Column(String(50)) # 题目类型
    difficulty: Mapped[Optional[str]] = Column(String(20))   # 难度等级
    grade_level: Mapped[Optional[str]] = Column(String(20))  # 适用年级
    
    # 知识点标签
    knowledge_points: Mapped[Optional[List]] = Column(JSON, default=list)
    tags: Mapped[Optional[List]] = Column(JSON, default=list)
    
    # AI处理相关
    extraction_model: Mapped[Optional[str]] = Column(String(50))  # 提取使用的模型
    rewrite_template_id: Mapped[Optional[str]] = Column(String(36))   # 改写使用的模板
    quality_score: Mapped[Optional[int]] = Column(Integer)        # 质量评分 (1-10)
    processing_cost: Mapped[Optional[float]] = Column(Float)      # 处理成本
    
    # 文件相关
    source_file_path: Mapped[Optional[str]] = Column(String(500)) # 原始文件路径
    has_image: Mapped[bool] = Column(Boolean, default=False)
    has_formula: Mapped[bool] = Column(Boolean, default=False)
    
    # 创建者和权限
    creator_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    is_public: Mapped[bool] = Column(Boolean, default=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    creator = relationship("ConfigUser", back_populates="created_questions")


class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = "data_prompt_templates"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    
    # 分类
    category: Mapped[str] = Column(String(50), default="general")  # system/subject/type
    subject: Mapped[Optional[str]] = Column(String(50))            # 适用学科
    question_type: Mapped[Optional[str]] = Column(String(50))      # 适用题型
    
    # 模板内容
    system_prompt: Mapped[Optional[str]] = Column(Text)            # 系统提示词
    user_prompt_template: Mapped[str] = Column(Text, nullable=False) # 用户提示词模板
    variables: Mapped[List] = Column(JSON, default=list)           # 模板变量定义
    examples: Mapped[List] = Column(JSON, default=list)            # 少样本示例
    
    # 版本控制
    version: Mapped[int] = Column(Integer, default=1)
    parent_template_id: Mapped[Optional[str]] = Column(String(36))     # 父模板ID
    
    # 使用统计
    usage_count: Mapped[int] = Column(Integer, default=0)
    avg_quality_score: Mapped[Optional[float]] = Column(Float)
    
    # 权限
    creator_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_users.user_id"))
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_builtin: Mapped[bool] = Column(Boolean, default=False)  # 内置模板
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class Homework(Base):
    """作业表"""
    __tablename__ = "data_homeworks"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = Column(String(200), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    instructions: Mapped[Optional[str]] = Column(Text)  # 作业说明
    
    # 关联
    teacher_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    class_id: Mapped[str] = Column(String(36), ForeignKey("data_classes.id"))
    
    # 题目列表
    question_ids: Mapped[List] = Column(JSON, default=list)  # 包含的题目ID列表
    
    # 时间管理
    due_at: Mapped[Optional[datetime]] = Column(DateTime, comment="截止时间")
    started_at: Mapped[Optional[datetime]] = Column(DateTime, default=func.now(), comment="开始时间")
    
    # 作业设置
    is_published: Mapped[bool] = Column(Boolean, default=False)
    allow_late_submission: Mapped[bool] = Column(Boolean, default=True)
    max_attempts: Mapped[int] = Column(Integer, default=1)  # 最大尝试次数
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    teacher = relationship("ConfigUser", foreign_keys=[teacher_id])
    class_obj = relationship("Class", back_populates="homeworks")
    student_homeworks = relationship("StudentHomework", back_populates="homework")


class StudentHomework(Base):
    """学生作业表"""
    __tablename__ = "data_student_homeworks"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    homework_id: Mapped[str] = Column(String(36), ForeignKey("data_homeworks.id"))
    student_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    
    # 状态管理
    status: Mapped[str] = Column(String(20), default="assigned")  # assigned/in_progress/completed
    progress: Mapped[dict] = Column(JSON, default=dict)           # 每道题的进度信息
    
    # 完成情况
    completion_percentage: Mapped[float] = Column(Float, default=0.0)
    total_chat_sessions: Mapped[int] = Column(Integer, default=0)
    total_messages: Mapped[int] = Column(Integer, default=0)
    
    # 统一时间字段命名
    assigned_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="分配时间")
    started_at: Mapped[Optional[datetime]] = Column(DateTime, comment="开始时间")
    completed_at: Mapped[Optional[datetime]] = Column(DateTime, comment="完成时间")
    submitted_at: Mapped[Optional[datetime]] = Column(DateTime, comment="提交时间")
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    homework = relationship("Homework", back_populates="student_homeworks")
    student = relationship("ConfigUser", back_populates="student_homeworks")


class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "data_chat_sessions"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 关联
    student_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    question_id: Mapped[str] = Column(String(36), ForeignKey("data_questions.id"))
    homework_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("data_homeworks.id"))
    
    # 会话信息
    session_data: Mapped[dict] = Column(JSON, default=dict)  # 会话元数据
    context: Mapped[dict] = Column(JSON, default=dict)       # 对话上下文
    
    # 统计信息
    message_count: Mapped[int] = Column(Integer, default=0)
    understanding_level: Mapped[Optional[int]] = Column(Integer) # 理解程度评估 (1-5)
    
    # AI使用统计
    total_tokens_used: Mapped[int] = Column(Integer, default=0)
    total_cost: Mapped[float] = Column(Float, default=0.0)
    
    # 统一时间字段命名
    started_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="开始时间")
    last_interaction_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="最后交互时间")
    ended_at: Mapped[Optional[datetime]] = Column(DateTime, comment="结束时间")
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    student = relationship("ConfigUser", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "data_chat_messages"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = Column(String(36), ForeignKey("data_chat_sessions.id"))
    
    # 消息内容
    role: Mapped[str] = Column(String(10), nullable=False)  # user/assistant
    content: Mapped[str] = Column(Text, nullable=False)
    selected_text: Mapped[Optional[str]] = Column(Text)     # 用户选中的文本
    
    # AI响应相关
    model_used: Mapped[Optional[str]] = Column(String(50))
    token_count: Mapped[int] = Column(Integer, default=0)
    response_time: Mapped[int] = Column(Integer, default=0)  # 响应时间(ms)
    from_cache: Mapped[bool] = Column(Boolean, default=False)
    cost: Mapped[float] = Column(Float, default=0.0)
    
    # 质量评估
    quality_score: Mapped[Optional[float]] = Column(Float)
    user_feedback: Mapped[Optional[int]] = Column(Integer)   # 用户评分 (1-5)
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关系
    session = relationship("ChatSession", back_populates="messages")


class FileUpload(Base):
    """文件上传记录表"""
    __tablename__ = "data_file_uploads"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    filename: Mapped[str] = Column(String(255), nullable=False)
    original_filename: Mapped[str] = Column(String(255), nullable=False)
    file_path: Mapped[str] = Column(String(500), nullable=False)
    
    # 文件信息
    file_size: Mapped[int] = Column(Integer, nullable=False)
    file_type: Mapped[str] = Column(String(50), nullable=False)
    mime_type: Mapped[Optional[str]] = Column(String(100))
    
    # 处理状态
    status: Mapped[str] = Column(String(20), default="uploaded")  # uploaded/processing/completed/failed
    processing_result: Mapped[dict] = Column(JSON, default=dict)   # 处理结果
    extracted_questions: Mapped[List] = Column(JSON, default=list) # 提取的题目列表
    error_message: Mapped[Optional[str]] = Column(Text)
    
    # 处理统计
    processing_time: Mapped[Optional[float]] = Column(Float)  # 处理耗时（秒）
    processing_cost: Mapped[Optional[float]] = Column(Float)  # 处理成本
    
    # 权限
    uploader_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))
    is_public: Mapped[bool] = Column(Boolean, default=False)
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    processed_at: Mapped[Optional[datetime]] = Column(DateTime, comment="处理时间")
    
    # 关系
    uploader = relationship("ConfigUser", back_populates="file_uploads")


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "log_system"
    
    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    
    # 日志信息
    level: Mapped[str] = Column(String(10), nullable=False)  # DEBUG/INFO/WARNING/ERROR
    message: Mapped[str] = Column(Text, nullable=False)
    category: Mapped[str] = Column(String(50), default="general")  # AI/AUTH/DB/FILE等
    
    # 关联信息
    user_id: Mapped[Optional[str]] = Column(String(36))
    session_id: Mapped[Optional[str]] = Column(String(36))
    request_id: Mapped[Optional[str]] = Column(String(36))
    
    # 详细信息
    details: Mapped[dict] = Column(JSON, default=dict)
    stack_trace: Mapped[Optional[str]] = Column(Text)
    
    # 统一时间字段命名
    created_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
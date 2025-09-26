"""
数据库模型定义
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    Float,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped

from app.core.database import Base


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid4())


class TutorSession(Base):
    """智能教学会话表"""
    __tablename__ = "tutor_sessions"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = Column(String(36), nullable=False)
    subject: Mapped[str] = Column(String(50), nullable=False)
    topic: Mapped[str] = Column(String(100), nullable=False)
    difficulty: Mapped[str] = Column(String(20), default="intermediate")

    # 学习目标和关键概念
    learning_objectives: Mapped[Optional[List]] = Column(JSON)
    key_concepts: Mapped[Optional[List]] = Column(JSON)

    # 教学状态
    current_phase: Mapped[str] = Column(String(30), default="initial_assessment")
    understanding_level: Mapped[float] = Column(Float, default=0.5)
    teaching_strategy: Mapped[str] = Column(String(20), default="socratic")

    # 会话统计
    total_questions: Mapped[int] = Column(Integer, default=0)
    correct_answers: Mapped[int] = Column(Integer, default=0)
    session_duration: Mapped[Optional[int]] = Column(Integer)  # 秒

    # 会话状态
    is_active: Mapped[bool] = Column(Boolean, default=True)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime)

    created_time: Mapped[datetime] = Column(DateTime, default=func.now())
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    messages = relationship("TutorMessage", back_populates="session", cascade="all, delete-orphan")


class TutorMessage(Base):
    """教学对话消息表"""
    __tablename__ = "tutor_messages"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = Column(String(36), ForeignKey("tutor_sessions.id"), nullable=False)

    # 消息内容
    role: Mapped[str] = Column(String(20), nullable=False)  # user/assistant
    content: Mapped[str] = Column(Text, nullable=False)

    # 消息元数据
    message_type: Mapped[Optional[str]] = Column(String(30))  # question/hint/explanation/encouragement
    teaching_phase: Mapped[Optional[str]] = Column(String(30))
    understanding_level: Mapped[Optional[float]] = Column(Float)

    # 学生回答分析
    response_type: Mapped[Optional[str]] = Column(String(20))  # correct/partial/incorrect/confused
    confusion_points: Mapped[Optional[List]] = Column(JSON)

    # 时间戳
    timestamp: Mapped[datetime] = Column(DateTime, default=func.now())

    # 关联关系
    session = relationship("TutorSession", back_populates="messages")


class StudentProgress(Base):
    """学生学习进度表"""
    __tablename__ = "student_progress"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = Column(String(36), nullable=False)
    subject: Mapped[str] = Column(String(50), nullable=False)
    topic: Mapped[str] = Column(String(100), nullable=False)

    # 进度统计
    total_sessions: Mapped[int] = Column(Integer, default=0)
    completed_sessions: Mapped[int] = Column(Integer, default=0)
    average_understanding: Mapped[float] = Column(Float, default=0.0)

    # 学习表现
    strengths: Mapped[Optional[List]] = Column(JSON)  # 优势知识点
    weaknesses: Mapped[Optional[List]] = Column(JSON)  # 薄弱环节
    confusion_history: Mapped[Optional[List]] = Column(JSON)  # 历史困惑点

    # 学习偏好
    preferred_teaching_style: Mapped[Optional[str]] = Column(String(20))
    response_pattern: Mapped[Optional[str]] = Column(String(20))  # fast/slow/careful

    # 时间信息
    first_learned: Mapped[datetime] = Column(DateTime, default=func.now())
    last_studied: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now())

    created_time: Mapped[datetime] = Column(DateTime, default=func.now())
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now())

    # 唯一约束
    __table_args__ = (UniqueConstraint('user_id', 'subject', 'topic', name='unique_user_subject_topic'),)







class Teaching(Base):
    """教师授课关系：哪个老师在某班教哪门学科"""
    __tablename__ = "edu_teaching"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    teacher_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"), nullable=False)
    class_id: Mapped[str] = Column(String(36), ForeignKey("data_classes.id"), nullable=False)
    subject_id: Mapped[str] = Column(String(36), ForeignKey("edu_subjects.id"), nullable=False)
    term: Mapped[Optional[str]] = Column(String(50))

    # 授课状态
    is_active: Mapped[bool] = Column(Boolean, default=True)

    created_time: Mapped[datetime] = Column(DateTime, default=func.now())
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now())

    # 移除原有的唯一约束，改为允许多个老师教同一班级同一科目，但同一老师不能重复授课同一班级同一科目
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", "subject_id", "term", name="uq_teaching_unique"),
    )

    # 关系
    subject = relationship("Subject")
    class_obj = relationship("Class", back_populates="teachings")
    teacher = relationship("ConfigUser")


class Class(Base):
    """班级表"""
    __tablename__ = "data_classes"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)

    # 班级属性
    grade_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_grades.id"))  # 关联年级表

    # 关联
    organization_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_organizations.organization_id"))

    # 班级设置
    max_students: Mapped[int] = Column(Integer, default=50)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    grade = relationship("Grade")
    organization = relationship("ConfigOrganization", back_populates="classes")
    homeworks = relationship("Homework", back_populates="class_obj")
    teachings = relationship("Teaching", back_populates="class_obj")
    # 学生关系
    # 注意：不建立复杂的反向关系以避免循环导入，仅提供简化映射表


class ClassStudent(Base):
    """班级-学生关联表"""
    __tablename__ = "data_class_students"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    class_id: Mapped[str] = Column(String(36), ForeignKey("data_classes.id"))
    student_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))

    joined_at: Mapped[datetime] = Column(DateTime, default=func.now(), comment="加入时间")
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")


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
    # 新增：规范化外键（保留旧字段以便迁移期可读写）
    subject_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_subjects.id"))
    grade_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_grades.id"))
    
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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    creator = relationship("ConfigUser", back_populates="created_questions")
    subject = relationship("Subject", back_populates="questions")
    grade = relationship("Grade", back_populates="questions")


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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class Homework(Base):
    """作业表"""
    __tablename__ = "data_homeworks"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = Column(String(200), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    instructions: Mapped[Optional[str]] = Column(Text)  # 作业说明

    # 关联
    creator_teacher_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"))  # 创建作业的老师
    class_id: Mapped[str] = Column(String(36), ForeignKey("data_classes.id"))
    subject_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_subjects.id"))
    grade_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_grades.id"))

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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    creator_teacher = relationship("ConfigUser", foreign_keys=[creator_teacher_id])
    class_obj = relationship("Class", back_populates="homeworks")
    student_homeworks = relationship("StudentHomework", back_populates="homework")
    subject = relationship("Subject")
    grade = relationship("Grade")


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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
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
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    processed_at: Mapped[Optional[datetime]] = Column(DateTime, comment="处理时间")
    
    # 关系
    uploader = relationship("ConfigUser", back_populates="file_uploads")


class Note(Base):
    """学生笔记表"""
    __tablename__ = "data_notes"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)

    # 笔记基本信息
    title: Mapped[str] = Column(String(200), nullable=False, comment="笔记标题")
    content: Mapped[str] = Column(Text, nullable=False, comment="笔记内容")
    summary: Mapped[Optional[str]] = Column(Text, comment="笔记摘要")

    # 笔记分类
    category: Mapped[str] = Column(String(50), default="general", comment="笔记分类")  # general/question/chat/homework
    tags: Mapped[List] = Column(JSON, default=list, comment="标签")

    # 关联信息（冗余存储以防数据丢失）
    question_id: Mapped[Optional[str]] = Column(String(36), comment="关联题目ID")
    question_title: Mapped[Optional[str]] = Column(String(200), comment="题目标题快照")
    question_content: Mapped[Optional[str]] = Column(Text, comment="题目内容快照")

    chat_session_id: Mapped[Optional[str]] = Column(String(36), comment="关联对话会话ID")
    chat_messages: Mapped[Optional[List]] = Column(JSON, default=list, comment="AI对话内容快照")

    homework_id: Mapped[Optional[str]] = Column(String(36), comment="关联作业ID")
    homework_title: Mapped[Optional[str]] = Column(String(200), comment="作业标题快照")

    # 学习相关
    subject: Mapped[Optional[str]] = Column(String(50), comment="学科")
    knowledge_points: Mapped[List] = Column(JSON, default=list, comment="知识点")
    difficulty_level: Mapped[Optional[str]] = Column(String(20), comment="难度等级")

    # 个人学习状态
    mastery_level: Mapped[int] = Column(Integer, default=1, comment="掌握程度 1-5")
    review_count: Mapped[int] = Column(Integer, default=0, comment="复习次数")
    last_reviewed_at: Mapped[Optional[datetime]] = Column(DateTime, comment="最后复习时间")

    # 笔记状态
    is_starred: Mapped[bool] = Column(Boolean, default=False, comment="是否收藏")
    is_public: Mapped[bool] = Column(Boolean, default=False, comment="是否公开")
    is_archived: Mapped[bool] = Column(Boolean, default=False, comment="是否归档")

    # 创建者
    student_id: Mapped[str] = Column(String(36), ForeignKey("config_users.user_id"), nullable=False)

    # 统一时间字段命名
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    student = relationship("ConfigUser", back_populates="notes")


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


# =============================================================================
# 基础教务数据模型
# =============================================================================

class ConfigOrganization(Base):
    """机构组织表"""
    __tablename__ = "config_organizations"

    organization_id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    organization_name: Mapped[str] = Column(String(100), nullable=False, comment="机构名称")
    organization_code: Mapped[Optional[str]] = Column(String(50), unique=True, comment="机构代码")

    # 机构信息
    organization_type: Mapped[str] = Column(String(20), default="school", comment="机构类型")  # school/training/company
    description: Mapped[Optional[str]] = Column(Text, comment="机构描述")

    # 联系信息
    contact_person: Mapped[Optional[str]] = Column(String(50), comment="联系人")
    contact_phone: Mapped[Optional[str]] = Column(String(20), comment="联系电话")
    contact_email: Mapped[Optional[str]] = Column(String(100), comment="联系邮箱")
    address: Mapped[Optional[str]] = Column(Text, comment="地址")

    # 配置信息
    settings: Mapped[dict] = Column(JSON, default=dict, comment="机构配置")

    # 状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否激活")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    users = relationship("ConfigUser", back_populates="organization")
    classes = relationship("Class", back_populates="organization")


class Grade(Base):
    """年级表"""
    __tablename__ = "edu_grades"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(50), nullable=False, comment="年级名称")
    code: Mapped[Optional[str]] = Column(String(20), comment="年级代码")

    # 年级属性
    level: Mapped[int] = Column(Integer, comment="年级级别")  # 1-12
    stage: Mapped[str] = Column(String(20), comment="学段")  # primary/middle/high
    description: Mapped[Optional[str]] = Column(Text, comment="年级描述")

    # 关联
    organization_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_organizations.organization_id"))

    # 排序
    sort_order: Mapped[int] = Column(Integer, default=0, comment="排序")

    # 状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否激活")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    organization = relationship("ConfigOrganization")
    classes = relationship("Class", back_populates="grade")
    subjects = relationship("Subject", back_populates="grade")
    questions = relationship("Question", back_populates="grade")
    homeworks = relationship("Homework", back_populates="grade")


class Subject(Base):
    """学科表"""
    __tablename__ = "edu_subjects"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(50), nullable=False, comment="学科名称")
    code: Mapped[Optional[str]] = Column(String(20), comment="学科代码")

    # 学科属性
    category: Mapped[str] = Column(String(30), default="academic", comment="学科类别")  # academic/art/sports/tech
    description: Mapped[Optional[str]] = Column(Text, comment="学科描述")

    # 关联
    grade_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_grades.id"))
    organization_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("config_organizations.organization_id"))

    # 配置
    color: Mapped[Optional[str]] = Column(String(10), comment="主题色")
    icon: Mapped[Optional[str]] = Column(String(50), comment="图标")

    # 排序
    sort_order: Mapped[int] = Column(Integer, default=0, comment="排序")

    # 状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否激活")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    grade = relationship("Grade", back_populates="subjects")
    organization = relationship("ConfigOrganization")
    questions = relationship("Question", back_populates="subject")
    homeworks = relationship("Homework", back_populates="subject")
    teachings = relationship("Teaching", back_populates="subject")


class Chapter(Base):
    """章节表"""
    __tablename__ = "edu_chapters"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = Column(String(100), nullable=False, comment="章节名称")
    code: Mapped[Optional[str]] = Column(String(50), comment="章节代码")

    # 章节属性
    subject_id: Mapped[str] = Column(String(36), ForeignKey("edu_subjects.id"), nullable=False)
    grade_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_grades.id"))

    # 层级结构
    parent_id: Mapped[Optional[str]] = Column(String(36), ForeignKey("edu_chapters.id"))
    level: Mapped[int] = Column(Integer, default=1, comment="层级")
    path: Mapped[Optional[str]] = Column(String(500), comment="路径")

    # 内容
    description: Mapped[Optional[str]] = Column(Text, comment="章节描述")
    objectives: Mapped[List] = Column(JSON, default=list, comment="学习目标")
    knowledge_points: Mapped[List] = Column(JSON, default=list, comment="知识点")

    # 排序
    sort_order: Mapped[int] = Column(Integer, default=0, comment="排序")

    # 状态
    is_active: Mapped[bool] = Column(Boolean, default=True, comment="是否激活")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")
    updated_time: Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    subject = relationship("Subject")
    grade = relationship("Grade")
    parent = relationship("Chapter", remote_side=[id])
    children = relationship("Chapter", back_populates="parent")


class QuestionChapter(Base):
    """题目章节关联表"""
    __tablename__ = "data_question_chapters"

    id: Mapped[str] = Column(String(36), primary_key=True, default=generate_uuid)
    question_id: Mapped[str] = Column(String(36), ForeignKey("data_questions.id"), nullable=False)
    chapter_id: Mapped[str] = Column(String(36), ForeignKey("edu_chapters.id"), nullable=False)

    # 关联权重
    weight: Mapped[float] = Column(Float, default=1.0, comment="关联权重")

    # 时间字段
    created_time: Mapped[datetime] = Column(DateTime, default=func.now(), comment="创建时间")

    # 唯一约束
    __table_args__ = (UniqueConstraint('question_id', 'chapter_id', name='uq_question_chapter'),)

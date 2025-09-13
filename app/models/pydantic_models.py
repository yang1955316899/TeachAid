"""
Pydantic模型定义 - 用于API请求和响应
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, EmailStr


# 枚举定义
class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class HomeworkStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FileProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 基础模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class PaginationQuery(BaseModel):
    """分页查询参数"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")


class PaginationResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# 用户相关模型
class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8)
    organization_code: Optional[str] = None
    invitation_code: Optional[str] = None


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    is_active: bool
    is_verified: bool
    organization_id: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# 机构相关模型
class OrganizationBase(BaseModel):
    """机构基础模型"""
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """机构创建模型"""
    pass


class OrganizationResponse(OrganizationBase):
    """机构响应模型"""
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 题目相关模型
class QuestionBase(BaseModel):
    """题目基础模型"""
    title: Optional[str] = None
    content: str
    subject: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    grade_level: Optional[str] = None
    knowledge_points: List[str] = []
    tags: List[str] = []


class QuestionCreate(QuestionBase):
    """题目创建模型"""
    original_answer: Optional[str] = None


class QuestionUpdate(BaseModel):
    """题目更新模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    rewritten_answer: Optional[str] = None
    subject: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[QuestionDifficulty] = None
    knowledge_points: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class QuestionResponse(QuestionBase):
    """题目响应模型"""
    id: str
    original_answer: Optional[str]
    rewritten_answer: Optional[str]
    quality_score: Optional[int]
    has_image: bool
    has_formula: bool
    creator_id: str
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnswerRewriteConfig(BaseModel):
    """答案改写配置"""
    template_id: Optional[str] = None
    grade_level: str = "初中"
    style: str = "引导式"
    include_examples: bool = True
    custom_instructions: Optional[str] = None


class AnswerRewriteResponse(BaseModel):
    """答案改写响应"""
    question_id: str
    original_answer: str
    rewritten_answer: str
    model_used: str
    quality_score: int
    processing_time: float
    cost: float


# 提示词模板相关模型
class PromptTemplateBase(BaseModel):
    """提示词模板基础模型"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = "general"
    subject: Optional[str] = None
    question_type: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: str
    variables: List[str] = []
    examples: List[Dict[str, str]] = []


class PromptTemplateCreate(PromptTemplateBase):
    """提示词模板创建模型"""
    pass


class PromptTemplateResponse(PromptTemplateBase):
    """提示词模板响应模型"""
    id: str
    version: int
    usage_count: int
    avg_quality_score: Optional[float]
    creator_id: str
    is_active: bool
    is_builtin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 作业相关模型
class HomeworkBase(BaseModel):
    """作业基础模型"""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    question_ids: List[str]
    due_date: Optional[datetime] = None


class HomeworkCreate(HomeworkBase):
    """作业创建模型"""
    class_id: str
    allow_late_submission: bool = True
    max_attempts: int = 1


class HomeworkUpdate(BaseModel):
    """作业更新模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None
    is_published: Optional[bool] = None


class HomeworkResponse(HomeworkBase):
    """作业响应模型"""
    id: str
    teacher_id: str
    class_id: str
    is_published: bool
    allow_late_submission: bool
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudentHomeworkResponse(BaseModel):
    """学生作业响应模型"""
    id: str
    homework_id: str
    student_id: str
    status: HomeworkStatus
    progress: Dict[str, Any]
    completion_percentage: float
    total_chat_sessions: int
    total_messages: int
    assigned_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# 对话相关模型
class ChatSessionStart(BaseModel):
    """开始对话会话"""
    question_id: str
    homework_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """对话会话响应"""
    session_id: str
    question_id: str
    status: str = "active"


class ChatMessageCreate(BaseModel):
    """对话消息创建"""
    content: str = Field(..., min_length=1)
    selected_text: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    id: str
    session_id: str
    role: str
    content: str
    selected_text: Optional[str]
    model_used: Optional[str]
    response_time: int
    from_cache: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 文件上传相关模型
class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    status: FileProcessingStatus
    uploader_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileProcessingResult(BaseModel):
    """文件处理结果"""
    file_id: str
    status: FileProcessingStatus
    extracted_questions: List[QuestionResponse]
    processing_time: Optional[float]
    processing_cost: Optional[float]
    error_message: Optional[str]


# 学习分析相关模型
class LearningProgress(BaseModel):
    """学习进度"""
    question_id: str
    chat_sessions: int
    total_messages: int
    last_interaction: Optional[datetime]
    understanding_level: Optional[int]


class StudentReport(BaseModel):
    """学生学习报告"""
    student_id: str
    time_range: tuple
    total_questions: int
    total_chat_sessions: int
    average_session_length: float
    most_active_subject: Optional[str]
    weak_knowledge_points: List[str]
    recommendations: List[str]


# 系统配置相关模型
class AIModelConfig(BaseModel):
    """AI模型配置"""
    primary_vision: str = "gpt-4o"
    primary_chat: str = "gpt-4o-mini"
    primary_rewrite: str = "claude-3-5-sonnet-20241022"
    fallback_models: Dict[str, str] = {}
    budget_models: Dict[str, str] = {}


class CacheConfig(BaseModel):
    """缓存配置"""
    enable_semantic_cache: bool = True
    semantic_threshold: float = 0.85
    exact_cache_ttl: int = 86400
    redis_url: str = "redis://localhost:6379/0"


class SystemStatus(BaseModel):
    """系统状态"""
    version: str
    uptime: int
    database_status: str
    redis_status: str
    ai_models_available: List[str]
    total_users: int
    total_questions: int
    total_chat_sessions: int
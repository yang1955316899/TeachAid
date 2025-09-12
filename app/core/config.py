"""
应用核心配置
"""
from typing import Optional, List
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """数据库配置"""
    url: str = "mysql+aiomysql://root:root@localhost:3306/teachaid"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20


class RedisSettings(BaseModel):
    """Redis配置"""
    url: str = "redis://localhost:6379/0"
    encoding: str = "utf-8"
    decode_responses: bool = True


class JWTSettings(BaseModel):
    """JWT配置"""
    secret: str = "your-super-secret-jwt-key"
    algorithm: str = "HS256"
    expire_minutes: int = 60
    refresh_expire_days: int = 7


class AISettings(BaseModel):
    """AI模型配置"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    yi_api_key: Optional[str] = None
    
    # LiteLLM配置
    litellm_log: str = "ERROR"
    litellm_drop_params: bool = True
    
    # LangSmith配置
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "TeachAid"


class FileUploadSettings(BaseModel):
    """文件上传配置"""
    max_size_mb: int = 50
    upload_dir: str = "uploads"
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "pdf", "txt"]
    
    @property
    def max_size_bytes(self) -> int:
        return self.max_size_mb * 1024 * 1024


class CacheSettings(BaseModel):
    """缓存配置"""
    ttl: int = 3600
    semantic_threshold: float = 0.85
    exact_cache_ttl: int = 86400


class CostControlSettings(BaseModel):
    """成本控制配置"""
    monthly_budget_limit: float = 1000.0
    cost_tracking_enabled: bool = True
    alert_threshold: float = 0.8


class Settings(BaseSettings):
    """应用总配置"""
    app_name: str = "TeachAid"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 50002
    
    # 各模块配置
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    jwt: JWTSettings = JWTSettings()
    ai: AISettings = AISettings()
    file_upload: FileUploadSettings = FileUploadSettings()
    cache: CacheSettings = CacheSettings()
    cost_control: CostControlSettings = CostControlSettings()
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False
        
        # 环境变量映射
        fields = {
            "database": {
                "env": "DATABASE_URL"
            },
            "redis": {
                "env": "REDIS_URL" 
            },
            "jwt": {
                "secret": {"env": "JWT_SECRET"},
                "algorithm": {"env": "JWT_ALGORITHM"},
                "expire_minutes": {"env": "JWT_EXPIRE_MINUTES"}
            },
            "ai": {
                "openai_api_key": {"env": "OPENAI_API_KEY"},
                "anthropic_api_key": {"env": "ANTHROPIC_API_KEY"},
                "qwen_api_key": {"env": "QWEN_API_KEY"},
                "yi_api_key": {"env": "YI_API_KEY"}
            }
        }


# 全局配置实例
settings = Settings()
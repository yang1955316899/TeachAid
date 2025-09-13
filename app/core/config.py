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
    secret: str = "your-super-secret-jwt-key-change-in-production"
    algorithm: str = "HS256"
    expire_minutes: int = 30  # 访问令牌30分钟过期
    refresh_expire_days: int = 7  # 刷新令牌7天过期
    issuer: str = "TeachAid"
    audience: str = "TeachAid-Users"
    token_prefix: str = "Bearer"


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
    
    # 数据库配置
    database_url: str = "mysql+aiomysql://root:root@localhost:3306/teachaid"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_encoding: str = "utf-8"
    redis_decode_responses: bool = True
    
    # JWT配置
    jwt_secret: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    jwt_issuer: str = "TeachAid"
    jwt_audience: str = "TeachAid-Users"
    jwt_token_prefix: str = "Bearer"
    
    # AI配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    yi_api_key: Optional[str] = None
    litellm_log: str = "ERROR"
    litellm_drop_params: bool = True
    langchain_tracing_v2: bool = False
    langchain_api_key: Optional[str] = None
    langchain_project: str = "TeachAid"
    
    # 文件上传配置
    max_upload_size: int = 50
    upload_dir: str = "uploads"
    allowed_extensions_str: str = "jpg,jpeg,png,pdf,txt"
    
    # 缓存配置
    cache_ttl: int = 3600
    semantic_cache_threshold: float = 0.85
    exact_cache_ttl: int = 86400
    
    # 成本控制配置
    monthly_budget_limit: float = 1000.0
    cost_tracking_enabled: bool = True
    alert_threshold: float = 0.8
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }
    
    @property
    def database(self) -> DatabaseSettings:
        """获取数据库配置"""
        return DatabaseSettings(
            url=self.database_url,
            echo=self.database_echo,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow
        )
    
    @property
    def redis(self) -> RedisSettings:
        """获取Redis配置"""
        return RedisSettings(
            url=self.redis_url,
            encoding=self.redis_encoding,
            decode_responses=self.redis_decode_responses
        )
    
    @property
    def jwt(self) -> JWTSettings:
        """获取JWT配置"""
        return JWTSettings(
            secret=self.jwt_secret,
            algorithm=self.jwt_algorithm,
            expire_minutes=self.jwt_expire_minutes,
            refresh_expire_days=self.jwt_refresh_expire_days,
            issuer=self.jwt_issuer,
            audience=self.jwt_audience,
            token_prefix=self.jwt_token_prefix
        )
    
    @property
    def ai(self) -> AISettings:
        """获取AI配置"""
        return AISettings(
            openai_api_key=self.openai_api_key,
            anthropic_api_key=self.anthropic_api_key,
            qwen_api_key=self.qwen_api_key,
            yi_api_key=self.yi_api_key,
            litellm_log=self.litellm_log,
            litellm_drop_params=self.litellm_drop_params,
            langchain_tracing_v2=self.langchain_tracing_v2,
            langchain_api_key=self.langchain_api_key,
            langchain_project=self.langchain_project
        )
    
    @property
    def allowed_extensions(self) -> List[str]:
        """解析允许的文件扩展名"""
        return [ext.strip() for ext in self.allowed_extensions_str.split(',')]
    
    @property
    def file_upload(self) -> FileUploadSettings:
        """获取文件上传配置"""
        return FileUploadSettings(
            max_size_mb=self.max_upload_size,
            upload_dir=self.upload_dir,
            allowed_extensions=self.allowed_extensions
        )
    
    @property
    def cache(self) -> CacheSettings:
        """获取缓存配置"""
        return CacheSettings(
            ttl=self.cache_ttl,
            semantic_threshold=self.semantic_cache_threshold,
            exact_cache_ttl=self.exact_cache_ttl
        )
    
    @property
    def cost_control(self) -> CostControlSettings:
        """获取成本控制配置"""
        return CostControlSettings(
            monthly_budget_limit=self.monthly_budget_limit,
            cost_tracking_enabled=self.cost_tracking_enabled,
            alert_threshold=self.alert_threshold
        )


# 全局配置实例
settings = Settings()
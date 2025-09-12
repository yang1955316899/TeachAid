import pytest
import os
from unittest.mock import Mock, patch
from app.core.config import settings

def test_settings_initialization():
    """测试配置初始化"""
    assert settings is not None

def test_database_url():
    """测试数据库URL配置"""
    with patch.dict(os.environ, {'DATABASE_URL': 'mysql+aiomysql://test:test@localhost:3306/testdb'}):
        from app.core.config import settings
        assert 'testdb' in settings.DATABASE_URL

def test_redis_url():
    """测试Redis URL配置"""
    with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379'}):
        from app.core.config import settings
        assert 'redis://localhost:6379' in settings.REDIS_URL

def test_ai_api_keys():
    """测试AI API密钥配置"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        from app.core.config import settings
        assert settings.OPENAI_API_KEY == 'test-key'
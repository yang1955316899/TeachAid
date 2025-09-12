# 测试配置文件
# 用于pytest和测试环境

import pytest
import os
from unittest.mock import patch

@pytest.fixture(scope="session")
def app():
    """创建应用实例用于测试"""
    from app.main import app
    return app

@pytest.fixture(scope="session")
def client(app):
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_env_variables():
    """模拟环境变量"""
    env_vars = {
        'DATABASE_URL': 'sqlite+aiosqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/0',
        'OPENAI_API_KEY': 'test-key',
        'ANTHROPIC_API_KEY': 'test-key',
        'SECRET_KEY': 'test-secret-key-for-testing-only',
    }
    
    with patch.dict(os.environ, env_vars):
        yield

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

@pytest.fixture
def sample_question_data():
    """示例题目数据"""
    return {
        "title": "测试题目",
        "content": "这是一道测试题目",
        "difficulty": "medium",
        "subject": "数学",
        "answer": "测试答案"
    }
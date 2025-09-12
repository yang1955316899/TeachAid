import pytest
from unittest.mock import Mock, patch
from app.core.unified_ai_framework import UnifiedAIFramework

@pytest.fixture
def ai_framework():
    """创建AI框架测试实例"""
    return UnifiedAIFramework()

def test_ai_framework_initialization(ai_framework):
    """测试AI框架初始化"""
    assert ai_framework is not None

def test_model_loading(ai_framework):
    """测试模型加载"""
    with patch('app.core.unified_ai_framework.load_model') as mock_load:
        mock_load.return_value = Mock()
        result = ai_framework.load_model("test-model")
        assert result is not None

@pytest.mark.asyncio
async def test_async_processing(ai_framework):
    """测试异步处理"""
    with patch('app.core.unified_ai_framework.process_request') as mock_process:
        mock_process.return_value = {"result": "test"}
        result = await ai_framework.process_async("test-input")
        assert result["result"] == "test"
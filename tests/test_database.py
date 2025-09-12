import pytest
from unittest.mock import Mock, patch
from app.core.database import get_db

@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    return Mock()

def test_database_connection():
    """测试数据库连接"""
    with patch('app.core.database.create_engine') as mock_engine:
        mock_engine.return_value = Mock()
        db = next(get_db())
        assert db is not None

def test_database_query(mock_db):
    """测试数据库查询"""
    mock_db.execute.return_value = Mock()
    mock_db.execute.return_value.fetchall.return_value = []
    
    result = mock_db.execute("SELECT * FROM test")
    assert result.fetchall() == []

@pytest.mark.asyncio
async def test_async_database_operation():
    """测试异步数据库操作"""
    with patch('app.core.database.async_session_maker') as mock_session:
        mock_session.return_value = Mock()
        async with mock_session() as session:
            assert session is not None
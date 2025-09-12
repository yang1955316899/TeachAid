import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

@pytest.mark.asyncio
async def test_async_endpoint():
    """测试异步端点"""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
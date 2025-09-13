"""
Redis客户端配置 - 企业级连接池实现
"""
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
import json
import asyncio
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings


class RedisClient:
    """Redis异步客户端 - 企业级连接池"""
    
    def __init__(self):
        self.pool: Optional[redis.ConnectionPool] = None
        self.redis: Optional[redis.Redis] = None
        self.connected = False
    
    async def connect(self):
        """连接Redis - 使用企业级连接池"""
        try:
            # 创建连接池
            self.pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                encoding=settings.redis_encoding,
                decode_responses=settings.redis_decode_responses,
                # 连接池配置
                max_connections=20,  # 最大连接数
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL  
                    3: 5   # TCP_KEEPCNT
                },
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 创建Redis实例
            self.redis = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            await self.redis.ping()
            self.connected = True
            logger.info("Redis连接池初始化成功")
            
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.connected = False
            # 不抛异常，降级到内存存储
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
        self.connected = False
        logger.info("Redis连接池已关闭")
    
    async def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.connected or not self.redis:
            return False
        
        try:
            await self.redis.ping()
            return True
        except Exception:
            self.connected = False
            return False
    
    # =============================================================================
    # 基础操作
    # =============================================================================
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[int] = None
    ) -> bool:
        """设置键值"""
        if not await self.is_available():
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            
            result = await self.redis.set(key, value, ex=expire)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET失败 {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """获取值"""
        if not await self.is_available():
            return None
        
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            
            # 尝试JSON解析
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Redis GET失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除键"""
        if not await self.is_available():
            return False
        
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis DELETE失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not await self.is_available():
            return False
        
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXISTS失败 {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        if not await self.is_available():
            return False
        
        try:
            result = await self.redis.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis EXPIRE失败 {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """获取键的TTL"""
        if not await self.is_available():
            return -1
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL失败 {key}: {e}")
            return -1
    
    # =============================================================================
    # Hash操作
    # =============================================================================
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """设置hash字段"""
        if not await self.is_available():
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, default=str)
            
            result = await self.redis.hset(name, key, value)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis HSET失败 {name}:{key}: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取hash字段"""
        if not await self.is_available():
            return None
        
        try:
            value = await self.redis.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Redis HGET失败 {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """获取所有hash字段"""
        if not await self.is_available():
            return {}
        
        try:
            result = await self.redis.hgetall(name)
            if not result:
                return {}
            
            # 尝试JSON解析所有值
            parsed_result = {}
            for key, value in result.items():
                try:
                    parsed_result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_result[key] = value
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Redis HGETALL失败 {name}: {e}")
            return {}
    
    async def hdel(self, name: str, key: str) -> bool:
        """删除hash字段"""
        if not await self.is_available():
            return False
        
        try:
            result = await self.redis.hdel(name, key)
            return bool(result)
        except Exception as e:
            logger.error(f"Redis HDEL失败 {name}:{key}: {e}")
            return False
    
    # =============================================================================
    # Set操作
    # =============================================================================
    
    async def sadd(self, name: str, *values) -> int:
        """添加到集合"""
        if not await self.is_available():
            return 0
        
        try:
            result = await self.redis.sadd(name, *values)
            return int(result)
        except Exception as e:
            logger.error(f"Redis SADD失败 {name}: {e}")
            return 0
    
    async def srem(self, name: str, *values) -> int:
        """从集合删除"""
        if not await self.is_available():
            return 0
        
        try:
            result = await self.redis.srem(name, *values)
            return int(result)
        except Exception as e:
            logger.error(f"Redis SREM失败 {name}: {e}")
            return 0
    
    async def smembers(self, name: str) -> List[str]:
        """获取集合成员"""
        if not await self.is_available():
            return []
        
        try:
            result = await self.redis.smembers(name)
            return list(result) if result else []
        except Exception as e:
            logger.error(f"Redis SMEMBERS失败 {name}: {e}")
            return []
    
    async def scard(self, name: str) -> int:
        """获取集合大小"""
        if not await self.is_available():
            return 0
        
        try:
            result = await self.redis.scard(name)
            return int(result)
        except Exception as e:
            logger.error(f"Redis SCARD失败 {name}: {e}")
            return 0


# 全局Redis客户端实例
redis_client = RedisClient()


# 初始化和清理函数
async def init_redis():
    """初始化Redis连接"""
    await redis_client.connect()


async def close_redis():
    """关闭Redis连接"""
    await redis_client.disconnect()
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

    # =============================================================================
    # 缓存增强功能
    # =============================================================================

    async def incr(self, key: str, amount: int = 1) -> int:
        """递增计数器"""
        if not await self.is_available():
            return 0

        try:
            result = await self.redis.incr(key, amount)
            return int(result)
        except Exception as e:
            logger.error(f"Redis INCR失败 {key}: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """递减计数器"""
        if not await self.is_available():
            return 0

        try:
            result = await self.redis.decr(key, amount)
            return int(result)
        except Exception as e:
            logger.error(f"Redis DECR失败 {key}: {e}")
            return 0

    async def keys(self, pattern: str) -> List[str]:
        """按模式获取键列表"""
        if not await self.is_available():
            return []

        try:
            result = await self.redis.keys(pattern)
            return list(result) if result else []
        except Exception as e:
            logger.error(f"Redis KEYS失败 {pattern}: {e}")
            return []

    async def scan_iter(self, pattern: str = "*", count: int = 100):
        """迭代扫描键（推荐用于大数据集）"""
        if not await self.is_available():
            return

        try:
            async for key in self.redis.scan_iter(match=pattern, count=count):
                yield key
        except Exception as e:
            logger.error(f"Redis SCAN失败 {pattern}: {e}")

    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取多个键的值"""
        if not await self.is_available() or not keys:
            return {}

        try:
            values = await self.redis.mget(keys)
            result = {}

            for i, key in enumerate(keys):
                if i < len(values) and values[i] is not None:
                    try:
                        result[key] = json.loads(values[i])
                    except (json.JSONDecodeError, TypeError):
                        result[key] = values[i]

            return result
        except Exception as e:
            logger.error(f"Redis批量获取失败: {e}")
            return {}

    async def batch_set(self, mapping: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """批量设置多个键值对"""
        if not await self.is_available() or not mapping:
            return False

        try:
            # 准备数据
            processed_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    processed_mapping[key] = json.dumps(value, ensure_ascii=False, default=str)
                else:
                    processed_mapping[key] = str(value)

            # 批量设置
            await self.redis.mset(processed_mapping)

            # 如果需要设置过期时间
            if expire:
                pipeline = self.redis.pipeline()
                for key in mapping.keys():
                    pipeline.expire(key, expire)
                await pipeline.execute()

            return True
        except Exception as e:
            logger.error(f"Redis批量设置失败: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有键"""
        if not await self.is_available():
            return 0

        count = 0
        try:
            async for key in self.scan_iter(pattern=pattern):
                await self.redis.delete(key)
                count += 1

            logger.info(f"清除了 {count} 个匹配 {pattern} 的键")
            return count
        except Exception as e:
            logger.error(f"Redis清除模式失败 {pattern}: {e}")
            return 0

    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取Redis内存使用情况"""
        if not await self.is_available():
            return {}

        try:
            info = await self.redis.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'memory_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0),
            }
        except Exception as e:
            logger.error(f"获取Redis内存信息失败: {e}")
            return {}

    async def get_stats(self) -> Dict[str, Any]:
        """获取Redis统计信息"""
        if not await self.is_available():
            return {}

        try:
            info = await self.redis.info()
            return {
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'hit_rate': 0
            }
        except Exception as e:
            logger.error(f"获取Redis统计信息失败: {e}")
            return {}

    async def pipeline_execute(self, commands: List[Dict]) -> List[Any]:
        """批量执行Redis命令"""
        if not await self.is_available() or not commands:
            return []

        try:
            pipeline = self.redis.pipeline()

            for cmd in commands:
                method = getattr(pipeline, cmd['command'])
                args = cmd.get('args', [])
                kwargs = cmd.get('kwargs', {})
                method(*args, **kwargs)

            results = await pipeline.execute()
            return results
        except Exception as e:
            logger.error(f"Redis管道执行失败: {e}")
            return []


# 全局Redis客户端实例
redis_client = RedisClient()


# 初始化和清理函数
async def init_redis():
    """初始化Redis连接"""
    await redis_client.connect()


async def close_redis():
    """关闭Redis连接"""
    await redis_client.disconnect()
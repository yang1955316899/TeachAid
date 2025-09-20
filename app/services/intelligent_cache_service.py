"""
智能缓存服务 - IntelligentCacheService
基于语义相似度的智能缓存和成本控制
"""
import hashlib
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# Redis缓存
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available, using memory cache")

# 语义相似度计算
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SEMANTIC_AVAILABLE = True
except ImportError:
    SEMANTIC_AVAILABLE = False
    print("SentenceTransformer not available, using exact match cache only")

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    content: str
    response: str
    created_at: float
    hit_count: int
    model_used: str
    cost: float
    embedding: Optional[List[float]] = None

class IntelligentCacheService:
    """智能缓存服务"""
    
    def __init__(self):
        """初始化智能缓存服务"""
        
        # 缓存配置
        self.enable_semantic_cache = True
        self.semantic_threshold = 0.85
        self.exact_cache_ttl = 86400  # 24小时
        self.semantic_cache_ttl = 3600  # 1小时
        self.max_cache_entries = 10000
        
        # 成本控制配置
        self.daily_budget = 50.0  # 美元
        self.cost_tracking_enabled = True
        
        # 初始化存储
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.semantic_model = None
        
        # 预算管理
        self.daily_costs: Dict[str, float] = {}
        self.model_usage_stats: Dict[str, Dict] = {}
        
        # 异步初始化标志
        self._initialized = False
        
        logger.info("IntelligentCacheService 初始化中...")

    async def initialize(self):
        """异步初始化"""
        if self._initialized:
            return
            
        # 初始化Redis连接
        await self._init_redis()
        
        # 初始化语义模型
        await self._init_semantic_model()
        
        # 加载今日成本统计
        await self._load_daily_costs()
        
        self._initialized = True
        logger.info("IntelligentCacheService 初始化完成")

    async def _init_redis(self):
        """初始化Redis连接"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis不可用，使用内存缓存")
            return
            
        try:
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # 测试连接
            await self.redis_client.ping()
            logger.info("Redis连接成功")
            
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，使用内存缓存")
            self.redis_client = None

    async def _init_semantic_model(self):
        """初始化语义相似度模型"""
        if not SEMANTIC_AVAILABLE:
            logger.warning("语义模型不可用，仅使用精确匹配缓存")
            self.enable_semantic_cache = False
            return
            
        try:
            # 使用轻量级中文语义模型
            self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("语义模型加载成功")
            
        except Exception as e:
            logger.warning(f"语义模型加载失败: {e}，禁用语义缓存")
            self.enable_semantic_cache = False

    async def _load_daily_costs(self):
        """加载今日成本统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if self.redis_client:
                cost_key = f"daily_cost:{today}"
                cost_str = await self.redis_client.get(cost_key)
                if cost_str:
                    self.daily_costs[today] = float(cost_str)
                    
        except Exception as e:
            logger.warning(f"加载每日成本失败: {e}")

    def _generate_cache_key(self, content: str, model: str = "") -> str:
        """生成缓存键"""
        combined = f"{content}:{model}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def get_cached_response(self, 
                                 content: str,
                                 model: str = "",
                                 enable_semantic: bool = True) -> Optional[Dict[str, Any]]:
        """获取缓存的响应"""
        
        if not self._initialized:
            await self.initialize()
            
        # 1. 首先尝试精确匹配缓存
        exact_key = self._generate_cache_key(content, model)
        cached_entry = await self._get_exact_cache(exact_key)
        
        if cached_entry:
            await self._update_cache_hit(cached_entry.key)
            logger.info(f"精确匹配缓存命中: {exact_key[:8]}...")
            
            return {
                "response": cached_entry.response,
                "from_cache": True,
                "cache_type": "exact",
                "model_used": cached_entry.model_used,
                "original_cost": cached_entry.cost,
                "hit_count": cached_entry.hit_count
            }
        
        # 2. 尝试语义相似度缓存
        if enable_semantic and self.enable_semantic_cache:
            semantic_match = await self._find_semantic_match(content, model)
            
            if semantic_match:
                await self._update_cache_hit(semantic_match["cache_key"])
                logger.info(f"语义缓存命中，相似度: {semantic_match['similarity']:.3f}")
                
                return {
                    "response": semantic_match["response"],
                    "from_cache": True, 
                    "cache_type": "semantic",
                    "similarity": semantic_match["similarity"],
                    "model_used": semantic_match["model_used"],
                    "original_cost": semantic_match["cost"],
                    "hit_count": semantic_match.get("hit_count", 1)
                }
        
        return None

    async def cache_response(self,
                           content: str,
                           response: str,
                           model: str,
                           cost: float):
        """缓存响应"""
        
        if not self._initialized:
            await self.initialize()
            
        cache_key = self._generate_cache_key(content, model)
        
        # 生成语义嵌入
        embedding = None
        if self.enable_semantic_cache and self.semantic_model:
            try:
                embedding = self.semantic_model.encode([content])[0].tolist()
            except Exception as e:
                logger.warning(f"生成语义嵌入失败: {e}")
        
        # 创建缓存条目
        cache_entry = CacheEntry(
            key=cache_key,
            content=content,
            response=response,
            created_at=time.time(),
            hit_count=0,
            model_used=model,
            cost=cost,
            embedding=embedding
        )
        
        # 存储到内存缓存
        self.memory_cache[cache_key] = cache_entry
        
        # 存储到Redis（如果可用）
        await self._store_to_redis(cache_entry)
        
        # 更新成本统计
        await self._update_cost_stats(model, cost)
        
        logger.info(f"响应已缓存: {cache_key[:8]}...")

    async def _get_exact_cache(self, cache_key: str) -> Optional[CacheEntry]:
        """获取精确匹配的缓存"""
        
        # 首先检查内存缓存
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # 检查是否过期
            if time.time() - entry.created_at < self.exact_cache_ttl:
                return entry
            else:
                # 清理过期缓存
                del self.memory_cache[cache_key]
        
        # 检查Redis缓存
        if self.redis_client:
            try:
                cached_data = await self.redis_client.hgetall(f"cache:{cache_key}")
                if cached_data:
                    return CacheEntry(
                        key=cache_key,
                        content=cached_data.get("content", ""),
                        response=cached_data.get("response", ""),
                        created_at=float(cached_data.get("created_at", 0)),
                        hit_count=int(cached_data.get("hit_count", 0)),
                        model_used=cached_data.get("model_used", ""),
                        cost=float(cached_data.get("cost", 0)),
                        embedding=json.loads(cached_data.get("embedding", "null"))
                    )
                    
            except Exception as e:
                logger.warning(f"Redis缓存读取失败: {e}")
        
        return None

    async def _find_semantic_match(self, 
                                 content: str,
                                 model: str) -> Optional[Dict[str, Any]]:
        """查找语义相似的缓存"""
        
        if not self.semantic_model:
            return None
            
        try:
            # 生成查询嵌入
            query_embedding = self.semantic_model.encode([content])[0]
            
            best_match = None
            best_similarity = 0.0
            
            # 搜索内存缓存
            for cache_key, entry in self.memory_cache.items():
                if entry.embedding and entry.model_used == model:
                    # 计算余弦相似度
                    similarity = cosine_similarity(
                        [query_embedding], 
                        [entry.embedding]
                    )[0][0]
                    
                    if similarity > best_similarity and similarity >= self.semantic_threshold:
                        best_similarity = similarity
                        best_match = {
                            "cache_key": cache_key,
                            "response": entry.response,
                            "similarity": similarity,
                            "model_used": entry.model_used,
                            "cost": entry.cost,
                            "hit_count": entry.hit_count
                        }
            
            # TODO: 也可以搜索Redis中的语义缓存
            # 这需要Redis的向量搜索功能（如RedisSearch）
            
            return best_match
            
        except Exception as e:
            logger.warning(f"语义匹配搜索失败: {e}")
            return None

    async def _store_to_redis(self, cache_entry: CacheEntry):
        """存储到Redis"""
        
        if not self.redis_client:
            return
            
        try:
            cache_data = {
                "content": cache_entry.content,
                "response": cache_entry.response,
                "created_at": cache_entry.created_at,
                "hit_count": cache_entry.hit_count,
                "model_used": cache_entry.model_used,
                "cost": cache_entry.cost,
                "embedding": json.dumps(cache_entry.embedding) if cache_entry.embedding else "null"
            }
            
            # 使用哈希存储
            await self.redis_client.hset(f"cache:{cache_entry.key}", mapping=cache_data)
            
            # 设置过期时间
            await self.redis_client.expire(f"cache:{cache_entry.key}", self.exact_cache_ttl)
            
        except Exception as e:
            logger.warning(f"Redis存储失败: {e}")

    async def _update_cache_hit(self, cache_key: str):
        """更新缓存命中计数"""
        
        # 更新内存缓存
        if cache_key in self.memory_cache:
            self.memory_cache[cache_key].hit_count += 1
        
        # 更新Redis缓存
        if self.redis_client:
            try:
                await self.redis_client.hincrby(f"cache:{cache_key}", "hit_count", 1)
            except Exception as e:
                logger.warning(f"Redis命中计数更新失败: {e}")

    async def _update_cost_stats(self, model: str, cost: float):
        """更新成本统计"""
        
        if not self.cost_tracking_enabled:
            return
            
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 更新每日成本
        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0
        self.daily_costs[today] += cost
        
        # 更新模型使用统计
        if model not in self.model_usage_stats:
            self.model_usage_stats[model] = {
                "total_calls": 0,
                "total_cost": 0.0,
                "avg_cost": 0.0
            }
        
        stats = self.model_usage_stats[model]
        stats["total_calls"] += 1
        stats["total_cost"] += cost
        stats["avg_cost"] = stats["total_cost"] / stats["total_calls"]
        
        # 持久化到Redis
        if self.redis_client:
            try:
                await self.redis_client.set(f"daily_cost:{today}", self.daily_costs[today])
                await self.redis_client.hset(
                    f"model_stats:{model}",
                    mapping={
                        "total_calls": stats["total_calls"],
                        "total_cost": stats["total_cost"],
                        "avg_cost": stats["avg_cost"]
                    }
                )
            except Exception as e:
                logger.warning(f"成本统计持久化失败: {e}")

    async def get_cost_statistics(self) -> Dict[str, Any]:
        """获取成本统计"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_cost = self.daily_costs.get(today, 0.0)
        
        return {
            "daily_budget": self.daily_budget,
            "current_cost": current_cost,
            "remaining_budget": max(0, self.daily_budget - current_cost),
            "budget_usage_percentage": (current_cost / self.daily_budget) * 100,
            "model_stats": self.model_usage_stats.copy(),
            "cache_stats": await self.get_cache_statistics()
        }

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        
        total_entries = len(self.memory_cache)
        total_hits = sum(entry.hit_count for entry in self.memory_cache.values())
        
        # 计算命中率（需要总请求数统计）
        hit_rate = 0.0
        if total_hits > 0:
            # 这里简化计算，实际需要维护总请求数
            estimated_requests = total_hits + total_entries
            hit_rate = (total_hits / estimated_requests) * 100 if estimated_requests > 0 else 0
        
        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "estimated_hit_rate": hit_rate,
            "semantic_cache_enabled": self.enable_semantic_cache,
            "redis_available": self.redis_client is not None
        }

    async def check_budget_limit(self, estimated_cost: float) -> Dict[str, Any]:
        """检查预算限制"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_cost = self.daily_costs.get(today, 0.0)
        
        if current_cost + estimated_cost > self.daily_budget:
            return {
                "allowed": False,
                "reason": "daily_budget_exceeded",
                "current_cost": current_cost,
                "estimated_cost": estimated_cost,
                "daily_budget": self.daily_budget
            }
        
        # 警告阈值（80%）
        if current_cost + estimated_cost > self.daily_budget * 0.8:
            return {
                "allowed": True,
                "warning": "approaching_budget_limit",
                "current_cost": current_cost,
                "remaining_budget": self.daily_budget - current_cost
            }
        
        return {
            "allowed": True,
            "current_cost": current_cost,
            "remaining_budget": self.daily_budget - current_cost
        }

    async def cleanup_expired_cache(self):
        """清理过期缓存"""
        
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if current_time - entry.created_at > self.exact_cache_ttl:
                expired_keys.append(key)
        
        # 清理过期缓存
        for key in expired_keys:
            del self.memory_cache[key]
        
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")
        return len(expired_keys)

    async def clear_cache(self, cache_type: str = "all"):
        """清理缓存"""
        
        if cache_type in ["all", "memory"]:
            self.memory_cache.clear()
            
        if cache_type in ["all", "redis"] and self.redis_client:
            try:
                # 清理所有缓存键（谨慎操作）
                async for key in self.redis_client.scan_iter(match="cache:*"):
                    await self.redis_client.delete(key)
                    
            except Exception as e:
                logger.error(f"清理Redis缓存失败: {e}")
        
        logger.info(f"已清理 {cache_type} 缓存")

    async def get_popular_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门查询（命中率高的缓存）"""
        
        sorted_entries = sorted(
            self.memory_cache.values(),
            key=lambda x: x.hit_count,
            reverse=True
        )
        
        return [
            {
                "content": entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                "hit_count": entry.hit_count,
                "model_used": entry.model_used,
                "created_at": datetime.fromtimestamp(entry.created_at).isoformat()
            }
            for entry in sorted_entries[:limit]
        ]

# 全局实例
intelligent_cache = IntelligentCacheService()
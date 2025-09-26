"""
性能优化工具和装饰器
"""
import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from loguru import logger


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.function_stats = defaultdict(list)
        self.query_stats = defaultdict(list)
        self.cache_stats = {"hits": 0, "misses": 0}

    def profile_function(self, func_name: str, execution_time: float):
        """记录函数执行时间"""
        self.function_stats[func_name].append({
            "time": execution_time,
            "timestamp": datetime.utcnow()
        })

        # 只保留最近1000次记录
        if len(self.function_stats[func_name]) > 1000:
            self.function_stats[func_name] = self.function_stats[func_name][-1000:]

    def profile_query(self, query_type: str, execution_time: float):
        """记录数据库查询时间"""
        self.query_stats[query_type].append({
            "time": execution_time,
            "timestamp": datetime.utcnow()
        })

        # 只保留最近1000次记录
        if len(self.query_stats[query_type]) > 1000:
            self.query_stats[query_type] = self.query_stats[query_type][-1000:]

    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_stats["hits"] += 1

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_stats["misses"] += 1

    def get_function_stats(self, func_name: str) -> Dict[str, Any]:
        """获取函数性能统计"""
        stats = self.function_stats.get(func_name, [])
        if not stats:
            return {"message": f"没有 {func_name} 的性能数据"}

        times = [s["time"] for s in stats]
        return {
            "function": func_name,
            "call_count": len(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times)
        }

    def get_top_slow_functions(self, limit: int = 10) -> list:
        """获取最慢的函数"""
        function_averages = []

        for func_name, stats in self.function_stats.items():
            if stats:
                times = [s["time"] for s in stats]
                avg_time = sum(times) / len(times)
                function_averages.append({
                    "function": func_name,
                    "avg_time": avg_time,
                    "call_count": len(times)
                })

        function_averages.sort(key=lambda x: x["avg_time"], reverse=True)
        return function_averages[:limit]

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total * 100) if total > 0 else 0

        return {
            "cache_hits": self.cache_stats["hits"],
            "cache_misses": self.cache_stats["misses"],
            "total_requests": total,
            "hit_rate": round(hit_rate, 2)
        }


# 全局性能分析器实例
profiler = PerformanceProfiler()


def performance_monitor(func_name: Optional[str] = None):
    """性能监控装饰器"""
    def decorator(func: Callable) -> Callable:
        name = func_name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    profiler.profile_function(name, execution_time)

                    # 记录慢函数
                    if execution_time > 1.0:  # 超过1秒
                        logger.warning(f"慢函数警告: {name} 耗时 {execution_time:.2f}s")

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    profiler.profile_function(name, execution_time)

                    # 记录慢函数
                    if execution_time > 1.0:  # 超过1秒
                        logger.warning(f"慢函数警告: {name} 耗时 {execution_time:.2f}s")

            return sync_wrapper

    return decorator


def cache_result(ttl: int = 300, key_prefix: str = ""):
    """结果缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            import hashlib
            import json

            key_data = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items()))
            }
            cache_key = f"{key_prefix}{hashlib.md5(json.dumps(key_data).encode()).hexdigest()}"

            # 检查缓存
            current_time = time.time()
            if cache_key in cache:
                cache_time = cache_times.get(cache_key, 0)
                if current_time - cache_time < ttl:
                    profiler.record_cache_hit()
                    logger.debug(f"缓存命中: {func.__name__}")
                    return cache[cache_key]
                else:
                    # 缓存过期，删除
                    del cache[cache_key]
                    del cache_times[cache_key]

            # 缓存未命中，执行函数
            profiler.record_cache_miss()
            logger.debug(f"缓存未命中: {func.__name__}")

            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 存储到缓存
            cache[cache_key] = result
            cache_times[cache_key] = current_time

            # 限制缓存大小
            if len(cache) > 1000:
                # 删除最老的缓存项
                oldest_key = min(cache_times.keys(), key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]

            return result

        return wrapper

    return decorator


class DatabaseQueryOptimizer:
    """数据库查询优化器"""

    def __init__(self):
        self.slow_queries = []
        self.query_patterns = defaultdict(int)

    def analyze_query(self, query: str, execution_time: float, params: tuple = None):
        """分析查询性能"""
        # 记录慢查询
        if execution_time > 0.5:  # 超过500ms
            self.slow_queries.append({
                "query": query,
                "execution_time": execution_time,
                "params": params,
                "timestamp": datetime.utcnow()
            })

            # 只保留最近100条慢查询
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

        # 统计查询模式
        pattern = self._extract_query_pattern(query)
        self.query_patterns[pattern] += 1

        profiler.profile_query(pattern, execution_time)

    def _extract_query_pattern(self, query: str) -> str:
        """提取查询模式（去除具体值）"""
        import re

        # 简化的模式提取：将数字和字符串替换为占位符
        pattern = re.sub(r"'[^']*'", "'?'", query)  # 字符串
        pattern = re.sub(r'\b\d+\b', '?', pattern)  # 数字
        pattern = re.sub(r'\s+', ' ', pattern)  # 多个空格替换为单个
        return pattern.strip()

    def get_slow_queries(self, limit: int = 10) -> list:
        """获取慢查询列表"""
        sorted_queries = sorted(
            self.slow_queries,
            key=lambda x: x["execution_time"],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_query_recommendations(self) -> list:
        """获取查询优化建议"""
        recommendations = []

        # 分析慢查询
        for query_data in self.slow_queries[-10:]:  # 分析最近10条慢查询
            query = query_data["query"].upper()
            suggestions = []

            if "SELECT *" in query:
                suggestions.append("避免使用 SELECT *，明确指定需要的列")

            if "WHERE" not in query and "SELECT" in query:
                suggestions.append("考虑添加 WHERE 条件限制结果集")

            if "LIMIT" not in query and "SELECT" in query:
                suggestions.append("考虑添加 LIMIT 限制返回行数")

            if "ORDER BY" in query and "LIMIT" not in query:
                suggestions.append("ORDER BY 通常应该配合 LIMIT 使用")

            if suggestions:
                recommendations.append({
                    "query": query_data["query"][:100] + "...",
                    "execution_time": query_data["execution_time"],
                    "suggestions": suggestions
                })

        return recommendations


# 全局查询优化器实例
query_optimizer = DatabaseQueryOptimizer()


class AsyncConnectionPool:
    """异步连接池优化"""

    def __init__(self, create_connection_func, max_size: int = 10, min_size: int = 2):
        self.create_connection_func = create_connection_func
        self.max_size = max_size
        self.min_size = min_size
        self.pool = asyncio.Queue(maxsize=max_size)
        self.created_connections = 0
        self.active_connections = 0
        self.lock = asyncio.Lock()

    async def initialize(self):
        """初始化连接池"""
        async with self.lock:
            for _ in range(self.min_size):
                connection = await self.create_connection_func()
                await self.pool.put(connection)
                self.created_connections += 1

    async def get_connection(self):
        """获取连接"""
        try:
            # 尝试从池中获取连接（非阻塞）
            connection = self.pool.get_nowait()
            self.active_connections += 1
            return connection
        except asyncio.QueueEmpty:
            # 池为空，检查是否可以创建新连接
            async with self.lock:
                if self.created_connections < self.max_size:
                    connection = await self.create_connection_func()
                    self.created_connections += 1
                    self.active_connections += 1
                    return connection

            # 等待可用连接
            connection = await self.pool.get()
            self.active_connections += 1
            return connection

    async def return_connection(self, connection):
        """归还连接"""
        self.active_connections -= 1
        await self.pool.put(connection)

    async def close_all(self):
        """关闭所有连接"""
        while not self.pool.empty():
            connection = await self.pool.get()
            await connection.close()
        self.created_connections = 0
        self.active_connections = 0

    def get_stats(self) -> Dict[str, int]:
        """获取连接池统计"""
        return {
            "pool_size": self.pool.qsize(),
            "created_connections": self.created_connections,
            "active_connections": self.active_connections,
            "max_size": self.max_size,
            "min_size": self.min_size
        }


def batch_operation(batch_size: int = 100):
    """批量操作装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(items: list, *args, **kwargs):
            if len(items) <= batch_size:
                return await func(items, *args, **kwargs)

            # 分批处理
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_result = await func(batch, *args, **kwargs)
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)

                # 避免过载，在批次间稍作延迟
                if i + batch_size < len(items):
                    await asyncio.sleep(0.01)

            return results

        return wrapper

    return decorator


class MemoryProfiler:
    """内存使用分析器"""

    def __init__(self):
        self.memory_snapshots = []

    def take_snapshot(self, label: str = ""):
        """拍摄内存快照"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            snapshot = {
                "label": label,
                "timestamp": datetime.utcnow(),
                "rss": memory_info.rss,  # 常驻内存
                "vms": memory_info.vms,  # 虚拟内存
                "percent": process.memory_percent()
            }

            self.memory_snapshots.append(snapshot)

            # 只保留最近100个快照
            if len(self.memory_snapshots) > 100:
                self.memory_snapshots = self.memory_snapshots[-100:]

            return snapshot

        except ImportError:
            logger.warning("psutil 未安装，无法获取内存信息")
            return None

    def get_memory_trend(self) -> Dict[str, Any]:
        """获取内存使用趋势"""
        if len(self.memory_snapshots) < 2:
            return {"message": "数据不足，无法分析趋势"}

        recent = self.memory_snapshots[-10:]  # 最近10个快照
        rss_values = [s["rss"] for s in recent]
        percent_values = [s["percent"] for s in recent]

        return {
            "snapshots_count": len(recent),
            "rss_trend": {
                "min": min(rss_values),
                "max": max(rss_values),
                "avg": sum(rss_values) / len(rss_values),
                "current": rss_values[-1]
            },
            "percent_trend": {
                "min": min(percent_values),
                "max": max(percent_values),
                "avg": sum(percent_values) / len(percent_values),
                "current": percent_values[-1]
            }
        }


# 全局内存分析器实例
memory_profiler = MemoryProfiler()


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "function_performance": {
            "top_slow_functions": profiler.get_top_slow_functions(5),
            "cache_stats": profiler.get_cache_stats()
        },
        "database_performance": {
            "slow_queries": query_optimizer.get_slow_queries(5),
            "query_recommendations": query_optimizer.get_query_recommendations()
        },
        "memory_usage": memory_profiler.get_memory_trend()
    }
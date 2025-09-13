"""
Token管理服务 - 基于Redis的JWT令牌管理
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from loguru import logger

from app.core.redis_client import redis_client


class TokenService:
    """基于Redis的Token管理服务"""
    
    def __init__(self):
        self.token_prefix = "auth:token:"
        self.user_tokens_prefix = "auth:user_tokens:"
        self.blacklist_prefix = "auth:blacklist:"
        self.session_prefix = "auth:session:"
    
    async def store_token(
        self,
        user_id: str,
        token_id: str,
        token_data: Dict[str, Any],
        expires_in: int
    ) -> bool:
        """存储Token"""
        try:
            # 存储token详细信息
            token_key = f"{self.token_prefix}{token_id}"
            token_info = {
                "user_id": user_id,
                "token_id": token_id,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
                **token_data
            }
            
            # 设置token信息，带过期时间
            await redis_client.set(token_key, token_info, expire=expires_in)
            
            # 维护用户的token集合
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            await redis_client.sadd(user_tokens_key, token_id)
            await redis_client.expire(user_tokens_key, expires_in + 3600)  # 多1小时缓冲
            
            return True
            
        except Exception as e:
            logger.error(f"存储Token失败: {e}")
            return False
    
    async def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """获取Token信息"""
        try:
            token_key = f"{self.token_prefix}{token_id}"
            return await redis_client.get(token_key)
        except Exception as e:
            logger.error(f"获取Token失败: {e}")
            return None
    
    async def validate_token(self, token_id: str) -> bool:
        """验证Token是否有效"""
        try:
            # 检查是否在黑名单
            blacklist_key = f"{self.blacklist_prefix}{token_id}"
            if await redis_client.exists(blacklist_key):
                return False
            
            # 检查token是否存在且未过期
            token_key = f"{self.token_prefix}{token_id}"
            return await redis_client.exists(token_key)
            
        except Exception as e:
            logger.error(f"验证Token失败: {e}")
            return False
    
    async def revoke_token(self, token_id: str, ttl: int = 86400) -> bool:
        """撤销Token（加入黑名单）"""
        try:
            # 获取token信息
            token_info = await self.get_token(token_id)
            if not token_info:
                return True  # 不存在的token视为已撤销
            
            # 删除token
            token_key = f"{self.token_prefix}{token_id}"
            await redis_client.delete(token_key)
            
            # 加入黑名单，防止已签发但未过期的token被使用
            blacklist_key = f"{self.blacklist_prefix}{token_id}"
            await redis_client.set(blacklist_key, "revoked", expire=ttl)
            
            # 从用户token集合中移除
            if "user_id" in token_info:
                user_tokens_key = f"{self.user_tokens_prefix}{token_info['user_id']}"
                await redis_client.srem(user_tokens_key, token_id)
            
            return True
            
        except Exception as e:
            logger.error(f"撤销Token失败: {e}")
            return False
    
    async def revoke_user_tokens(self, user_id: str) -> bool:
        """撤销用户所有Token"""
        try:
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            token_ids = await redis_client.smembers(user_tokens_key)
            
            success_count = 0
            for token_id in token_ids:
                if await self.revoke_token(token_id):
                    success_count += 1
            
            # 清除用户token集合
            await redis_client.delete(user_tokens_key)
            
            logger.info(f"撤销用户 {user_id} 的 {success_count}/{len(token_ids)} 个token")
            return True
            
        except Exception as e:
            logger.error(f"撤销用户Token失败: {e}")
            return False
    
    async def get_user_active_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户活跃Token列表"""
        try:
            user_tokens_key = f"{self.user_tokens_prefix}{user_id}"
            token_ids = await redis_client.smembers(user_tokens_key)
            
            active_tokens = []
            for token_id in token_ids:
                token_info = await self.get_token(token_id)
                if token_info and await self.validate_token(token_id):
                    active_tokens.append(token_info)
            
            return active_tokens
            
        except Exception as e:
            logger.error(f"获取用户活跃Token失败: {e}")
            return []
    
    async def cleanup_expired_tokens(self) -> int:
        """清理过期Token（定时任务用）"""
        # Redis的TTL会自动清理过期键，这里主要做一些统计
        try:
            # 实际上Redis会自动清理，这里可以做一些统计
            return 0
        except Exception as e:
            logger.error(f"清理过期Token失败: {e}")
            return 0


# 全局Token管理器实例
token_service = TokenService()
"""
安全中间件和工具
"""
import time
import hashlib
import json
from typing import Dict, Optional, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer
from loguru import logger
import re


class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self):
        # 请求限流存储
        self.request_limits = defaultdict(lambda: deque(maxlen=100))
        
        # IP黑名单
        self.ip_blacklist = set()
        
        # 可疑请求模式
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union.*select',  # SQL注入
            r'drop.*table',  # SQL注入
            r'exec\(',  # 命令注入
            r'eval\(',  # 代码注入
            r'system\(',  # 系统调用
            r'\.\./',  # 路径遍历
            r'<\?php',  # PHP代码
            r'javascript:',  # JavaScript协议
        ]
        
        # 安全头部
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; font-src 'self' data:; object-src 'none';",
        }
    
    async def check_request_security(self, request: Request) -> Dict[str, any]:
        """检查请求安全性"""
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        path = request.url.path
        method = request.method
        
        # 检查IP黑名单
        if client_ip in self.ip_blacklist:
            logger.warning(f"黑名单IP尝试访问: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="访问被拒绝"
            )
        
        # 检查请求频率
        await self.check_rate_limit(client_ip, path)
        
        # 检查User-Agent
        if not user_agent or len(user_agent) < 10:
            logger.warning(f"可疑User-Agent: {user_agent} from {client_ip}")
        
        # 检查路径安全性
        self.check_path_security(path)
        
        # 检查查询参数
        query_params = dict(request.query_params)
        self.check_parameter_security(query_params, client_ip)
        
        # 记录安全日志
        await self.log_security_event({
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'method': method,
            'path': path,
            'user_agent': user_agent,
            'status': 'allowed'
        })
        
        return {
            'client_ip': client_ip,
            'security_score': self.calculate_security_score(client_ip, user_agent)
        }
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # 默认使用客户端地址
        return request.client.host if request.client else 'unknown'
    
    async def check_rate_limit(self, client_ip: str, path: str) -> None:
        """检查请求频率限制"""
        now = time.time()
        window_start = now - 60  # 1分钟窗口
        
        # 清理过期记录
        self.request_limits[client_ip] = deque(
            [t for t in self.request_limits[client_ip] if t > window_start],
            maxlen=100
        )
        
        # 检查频率限制
        requests_in_window = len(self.request_limits[client_ip])
        
        # 不同路径的限流规则
        limits = {
            '/api/auth/login': 50,  # 登录接口每分钟5次
            '/api/auth/register': 30,  # 注册接口每分钟3次
            '/api/': 100,  # 其他API每分钟100次
            'default': 60  # 默认每分钟60次
        }
        
        limit = limits.get(path, limits['default'])
        
        if requests_in_window >= limit:
            logger.warning(f"IP {client_ip} 超出限流限制: {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后重试"
            )
        
        # 记录请求时间
        self.request_limits[client_ip].append(now)
    
    def check_path_security(self, path: str) -> None:
        """检查路径安全性"""
        # 检查路径遍历攻击
        if '../' in path or '..\\' in path:
            logger.warning(f"路径遍历攻击尝试: {path}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="非法路径"
            )

        # 允许的合法 admin 路径
        allowed_admin_paths = [
            '/api/admin',  # API 路径
            '/admin/',     # 前端路由（斜杠结尾）
        ]

        # 如果是合法的 admin 路径，直接返回
        for allowed_path in allowed_admin_paths:
            if path.lower().startswith(allowed_path.lower()):
                return

        # 检查敏感路径
        sensitive_paths = [
            '/.env',
            '/config',
            '/admin',      # 只拦截根 /admin 路径，不拦截子路径
            '/wp-admin',
            '/phpmyadmin'
        ]

        for sensitive_path in sensitive_paths:
            # 精确匹配，避免误拦截合法路径
            if path.lower() == sensitive_path.lower() or path.lower().startswith(sensitive_path.lower() + '/'):
                # 但是排除我们的合法路径
                if not any(path.lower().startswith(allowed.lower()) for allowed in allowed_admin_paths):
                    logger.warning(f"敏感路径访问尝试: {path}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="页面不存在"
                    )
    
    def check_parameter_security(self, params: Dict[str, str], client_ip: str) -> None:
        """检查参数安全性"""
        for key, value in params.items():
            if not value:
                continue
            
            # 检查XSS和注入攻击
            for pattern in self.suspicious_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    logger.warning(f"可疑参数检测 - IP: {client_ip}, 参数: {key}={value}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="参数包含非法内容"
                    )
            
            # 检查参数长度
            if len(value) > 1000:
                logger.warning(f"参数过长 - IP: {client_ip}, 参数: {key}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="参数过长"
                )
    
    def calculate_security_score(self, client_ip: str, user_agent: str) -> int:
        """计算安全评分"""
        score = 100
        
        # 根据请求频率调整评分
        request_count = len(self.request_limits[client_ip])
        if request_count > 50:
            score -= 20
        elif request_count > 20:
            score -= 10
        
        # 根据User-Agent调整评分
        if not user_agent or len(user_agent) < 20:
            score -= 15
        
        # 检查是否为已知扫描器
        suspicious_agents = ['curl', 'wget', 'python', 'bot', 'spider', 'crawler']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            score -= 25
        
        return max(0, score)
    
    async def log_security_event(self, event: Dict[str, any]) -> None:
        """记录安全事件日志"""
        try:
            # 这里可以添加到数据库或日志系统
            logger.info(f"安全事件: {json.dumps(event, ensure_ascii=False)}")
        except Exception as e:
            logger.error(f"记录安全事件失败: {e}")
    
    def get_security_headers(self) -> Dict[str, str]:
        """获取安全响应头"""
        return self.security_headers.copy()
    
    def add_to_blacklist(self, client_ip: str, reason: str = "") -> None:
        """添加IP到黑名单"""
        self.ip_blacklist.add(client_ip)
        logger.warning(f"IP {client_ip} 已添加到黑名单: {reason}")
    
    def remove_from_blacklist(self, client_ip: str) -> None:
        """从黑名单移除IP"""
        if client_ip in self.ip_blacklist:
            self.ip_blacklist.remove(client_ip)
            logger.info(f"IP {client_ip} 已从黑名单移除")


class CSRFProtection:
    """CSRF保护"""
    
    def __init__(self):
        self.csrf_tokens = {}
        self.token_expiry = 3600  # 1小时过期
    
    def generate_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        import secrets
        token = secrets.token_urlsafe(32)
        
        self.csrf_tokens[session_id] = {
            'token': token,
            'expiry': time.time() + self.token_expiry
        }
        
        return token
    
    def validate_token(self, session_id: str, token: str) -> bool:
        """验证CSRF令牌"""
        if session_id not in self.csrf_tokens:
            return False
        
        token_data = self.csrf_tokens[session_id]
        
        # 检查令牌是否过期
        if time.time() > token_data['expiry']:
            del self.csrf_tokens[session_id]
            return False
        
        # 验证令牌
        return token_data['token'] == token
    
    def cleanup_expired_tokens(self) -> None:
        """清理过期令牌"""
        now = time.time()
        expired_sessions = [
            session_id for session_id, data in self.csrf_tokens.items()
            if now > data['expiry']
        ]
        
        for session_id in expired_sessions:
            del self.csrf_tokens[session_id]


# 全局安全中间件实例
security_middleware = SecurityMiddleware()
csrf_protection = CSRFProtection()
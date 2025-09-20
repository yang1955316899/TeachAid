"""
认证服务 - 完整的用户认证、授权、会话管理和安全控制
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger
import re
import ipaddress

from app.core.config import settings
from app.core.database import get_db
from app.services.token_service import token_service
from app.models.auth_models import (
    ConfigUser, ConfigOrganization, LogLogin, 
    ConfigPermission, ConfigRolePermission, LogAudit,
    UserRole, UserStatus
)


class AuthService:
    """认证服务 - 企业级安全最佳实践"""
    
    def __init__(self):
        # 密码加密配置 - 使用更强的加密方式
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__rounds=4,
            argon2__memory_cost=65536,
            argon2__parallelism=1,
            bcrypt__rounds=14
        )
        
        self.security = HTTPBearer()
        
        # JWT配置
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire = settings.jwt_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_expire_days
        self.issuer = settings.jwt_issuer
        self.audience = settings.jwt_audience
        
        # 安全配置
        self.max_failed_attempts = 5  # 最大失败尝试次数
        self.lockout_duration = 30  # 锁定时长（分钟）
        self.password_min_length = 8
        self.require_password_complexity = True
        self.max_sessions_per_user = 3
        
        
        # 权限定义
        self.role_permissions = {
            UserRole.ADMIN: [
                # 用户管理
                "user:create", "user:read", "user:update", "user:delete",
                "user:list", "user:export", "user:import",
                
                # 组织管理
                "organization:create", "organization:read", "organization:update", "organization:delete",
                "organization:list", "organization:settings",
                
                # 系统管理
                "system:settings", "system:logs", "system:audit", "system:backup",
                "system:maintenance", "system:monitor",
                
                # 权限管理
                "auth:manage", "role:manage", "permission:manage",
                
                # 内容管理
                "question:create", "question:read", "question:update", "question:delete",
                "question:export", "question:import", "question:moderate",
                
                # 作业管理
                "homework:create", "homework:read", "homework:update", "homework:delete",
                "homework:assign", "homework:grade", "homework:statistics",
                
                # 分析报告
                "analytics:read", "analytics:export", "report:generate"
            ],
            
            UserRole.TEACHER: [
                # 基本信息
                "user:read_self", "user:update_self",
                
                # 题目管理
                "question:create", "question:read", "question:update", "question:delete_own",
                "question:search", "question:favorite",
                
                # 作业管理
                "homework:create", "homework:read", "homework:update", "homework:delete_own",
                "homework:assign", "homework:grade", "homework:publish",
                
                # 学生管理
                "student:read", "student:list", "student:progress",
                
                # 对话管理
                "chat:read", "chat:monitor", 
                
                # 统计分析
                "analytics:read_own", "report:generate_own",
                
                # 班级管理
                "class:create", "class:read", "class:update", "class:manage_students"
            ],
            
            UserRole.STUDENT: [
                # 基本信息
                "user:read_self", "user:update_self",
                
                # 题目学习
                "question:read", "question:search", "question:favorite",
                
                # 作业完成
                "homework:read", "homework:submit", "homework:view_progress",
                
                # 对话学习
                "chat:create", "chat:read_own", "chat:delete_own",
                
                # 学习记录
                "progress:read_own", "achievement:read_own"
            ]
        }
    
    # =============================================================================
    # 密码和加密相关
    # =============================================================================
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        if len(password) < self.password_min_length:
            return False, f"密码长度至少{self.password_min_length}位"
        
        if not self.require_password_complexity:
            return True, "密码符合要求"
        
        # 复杂度检查
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength_checks = [has_upper, has_lower, has_digit, has_special]
        if sum(strength_checks) < 3:
            return False, "密码必须包含大写字母、小写字母、数字和特殊字符中的至少3种"
        
        # 常见密码检查
        common_passwords = ["password", "123456", "admin", "user", "test"]
        if password.lower() in common_passwords:
            return False, "密码过于简单，请使用更复杂的密码"
        
        return True, "密码符合要求"
    
    def hash_password(self, password: str) -> str:
        """密码哈希 - 返回哈希值和盐值"""
        # 生成盐值
        salt = secrets.token_hex(16)

        # 使用argon2加密
        password_hash = self.pwd_context.hash(password + salt)

        return f"{password_hash}${salt}"
    
    def verify_password(self, plain_password: str, hashed_password: str, salt: str = None) -> bool:
        """验证密码"""
        try:
            if salt:
                return self.pwd_context.verify(plain_password + salt, hashed_password)
            elif '$' in hashed_password:
                # 新格式：argon2_hash$salt
                # 找到最后一个$符号的位置
                last_dollar_pos = hashed_password.rfind('$')
                if last_dollar_pos != -1:
                    stored_hash = hashed_password[:last_dollar_pos]
                    salt = hashed_password[last_dollar_pos + 1:]
                    return self.pwd_context.verify(plain_password + salt, stored_hash)
                else:
                    return self.pwd_context.verify(plain_password, hashed_password)
            else:
                return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False
    
    # =============================================================================
    # JWT令牌管理
    # =============================================================================
    
    def create_access_token(
        self, 
        user_data: Dict[str, Any],
        device_id: str = None,
        ip_address: str = None
    ) -> str:
        """创建访问令牌"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "iss": self.issuer,
            "aud": self.audience,
            "jti": secrets.token_hex(16),  # JWT ID
            "device_id": device_id,
            "ip": ip_address
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_data: Dict[str, Any], 
        device_id: str = None,
        ip_address: str = None
    ) -> str:
        """创建刷新令牌"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "iss": self.issuer,
            "aud": self.audience,
            "jti": secrets.token_hex(16),
            "device_id": device_id,
            "ip": ip_address
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """解码令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期，请重新登录"
            )
        except jwt.InvalidIssuerError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌颁发者"
            )
        except jwt.InvalidAudienceError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌接收者"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )
        except Exception as e:
            logger.error(f"令牌解码失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌验证失败"
            )
    
    # =============================================================================
    # 会话管理
    # =============================================================================
    
    async def create_user_session(
        self,
        user_id: str,
        device_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建用户会话 - 使用Redis存储Token"""
        try:
            # 检查现有活跃Token数量
            active_tokens = await token_service.get_user_active_tokens(user_id)
            
            # 如果超过最大会话数，撤销最旧的会话
            if len(active_tokens) >= self.max_sessions_per_user:
                # 按创建时间排序，撤销最旧的
                sorted_tokens = sorted(active_tokens, key=lambda x: x.get("created_at", ""))
                tokens_to_revoke = len(active_tokens) - self.max_sessions_per_user + 1
                
                for i in range(tokens_to_revoke):
                    if i < len(sorted_tokens):
                        await token_service.revoke_token(sorted_tokens[i]["token_id"])
            
            # 生成令牌数据
            device_id = device_info.get("device_id", secrets.token_hex(16))
            ip_address = device_info.get("ip_address")
            
            token_data = {
                "sub": user_id,
                "username": device_info.get("username"),
                "role": device_info.get("role")
            }
            
            # 创建JWT令牌
            access_token = self.create_access_token(token_data, device_id, ip_address)
            refresh_token = self.create_refresh_token(token_data, device_id, ip_address)
            
            # 解码获取JTI用作Redis键
            access_payload = self.decode_token(access_token)
            refresh_payload = self.decode_token(refresh_token)
            
            access_jti = access_payload["jti"]
            refresh_jti = refresh_payload["jti"]
            
            # 存储访问令牌到Redis
            await token_service.store_token(
                user_id=user_id,
                token_id=access_jti,
                token_data={
                    "type": "access",
                    "device_id": device_id,
                    "device_name": device_info.get("device_name"),
                    "device_type": device_info.get("device_type"),
                    "user_agent": device_info.get("user_agent"),
                    "ip_address": ip_address,
                    "username": device_info.get("username"),
                    "role": device_info.get("role")
                },
                expires_in=self.access_token_expire * 60
            )
            
            # 存储刷新令牌到Redis
            await token_service.store_token(
                user_id=user_id,
                token_id=refresh_jti,
                token_data={
                    "type": "refresh",
                    "device_id": device_id,
                    "device_name": device_info.get("device_name"),
                    "device_type": device_info.get("device_type"),
                    "user_agent": device_info.get("user_agent"),
                    "ip_address": ip_address,
                    "username": device_info.get("username"),
                    "role": device_info.get("role")
                },
                expires_in=self.refresh_token_expire_days * 24 * 3600
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.access_token_expire * 60,
                "device_id": device_id
            }
            
        except Exception as e:
            logger.error(f"创建用户会话失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="会话创建失败"
            )
    
    async def revoke_user_session(
        self,
        user_id: str,
        device_id: str = None
    ) -> bool:
        """撤销用户会话 - 使用Redis"""
        try:
            if device_id:
                # 撤销特定设备的会话
                active_tokens = await token_service.get_user_active_tokens(user_id)
                success_count = 0
                
                for token_info in active_tokens:
                    if token_info.get("device_id") == device_id:
                        if await token_service.revoke_token(token_info["token_id"]):
                            success_count += 1
                
                logger.info(f"撤销用户 {user_id} 设备 {device_id} 的 {success_count} 个token")
                return success_count > 0
            else:
                # 撤销用户所有会话
                return await token_service.revoke_user_tokens(user_id)
            
        except Exception as e:
            logger.error(f"撤销用户会话失败: {e}")
            return False
    
    # =============================================================================
    # 用户注册和认证
    # =============================================================================
    
    async def register_user(
        self,
        user_data: Dict[str, Any],
        db: AsyncSession,
        request: Request = None
    ) -> Dict[str, Any]:
        """用户注册"""
        try:
            username = user_data.get("user_name")
            email = user_data.get("user_email")
            password = user_data.get("password")
            
            # 验证输入
            if not all([username, email, password]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名、邮箱和密码不能为空"
                )
            
            # 验证密码强度
            is_valid, message = self.validate_password_strength(password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
            
            # 检查用户名和邮箱是否已存在
            existing_user = await db.execute(
                select(ConfigUser).where(
                    or_(
                        ConfigUser.user_name == username,
                        ConfigUser.user_email == email
                    )
                )
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名或邮箱已存在"
                )
            
            # 验证机构代码（如果提供）
            organization_id = None
            if user_data.get("organization_code"):
                org_result = await db.execute(
                    select(ConfigOrganization).where(
                        ConfigOrganization.organization_code == user_data["organization_code"]
                    )
                )
                organization = org_result.scalar_one_or_none()
                if not organization:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的机构代码"
                    )
                organization_id = organization.organization_id
            
            # 加密密码
            password_hash = self.hash_password(password)

            # 创建用户
            user = ConfigUser(
                user_name=username,
                user_email=email,
                user_password_hash=password_hash,
                user_password_salt="",  # 盐值已包含在哈希中
                user_full_name=user_data.get("user_full_name"),
                user_role=UserRole(user_data.get("user_role", "student")),
                organization_id=organization_id,
                user_verification_token=secrets.token_urlsafe(32),
                user_active_sessions={},
                user_settings={},
                user_preferences={}
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # 记录审计日志
            if request:
                audit_log = LogAudit(
                    user_id=user.user_id,
                    action_type="USER_REGISTER",
                    resource="user",
                    resource_id=user.user_id,
                    description=f"用户 {username} 注册成功",
                    request_method=request.method,
                    request_url=str(request.url),
                    ip_address=request.client.host if request.client else "unknown",
                    user_agent=request.headers.get("User-Agent"),
                    status="SUCCESS",
                    result={}
                )
                db.add(audit_log)
                await db.commit()
            
            logger.info(f"用户注册成功: {username}")
            
            return {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "user_email": user.user_email,
                "user_role": user.user_role.value,
                "verification_required": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"用户注册失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册失败，请稍后重试"
            )
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        request: Request,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """用户认证登录"""
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # 记录登录尝试
        login_log = LogLogin(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            is_success=False
        )
        
        try:
            # 查找真实用户
            result = await db.execute(
                select(ConfigUser).where(
                    or_(
                        ConfigUser.user_name == username,
                        ConfigUser.user_email == username
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if not user:
                login_log.failure_reason = "用户不存在"
                db.add(login_log)
                await db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            # 检查账户状态
            if user.user_status == UserStatus.LOCKED:
                if user.user_locked_until and user.user_locked_until > datetime.utcnow():
                    login_log.failure_reason = "账户已锁定"
                    login_log.user_id = user.user_id
                    db.add(login_log)
                    await db.commit()
                    
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail=f"账户已锁定，请于 {user.user_locked_until.strftime('%Y-%m-%d %H:%M:%S')} 后重试"
                    )
                else:
                    # 锁定已过期，重置状态
                    user.user_status = UserStatus.ACTIVE
                    user.user_locked_until = None
                    user.user_failed_login_attempts = 0
            
            if user.user_status != UserStatus.ACTIVE:
                login_log.failure_reason = f"账户状态异常: {user.user_status.value}"
                login_log.user_id = user.user_id
                db.add(login_log)
                await db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账户已被禁用或暂停"
                )
            
            # 验证密码
            if not self.verify_password(password, user.user_password_hash):
                # 增加失败次数
                user.user_failed_login_attempts += 1
                
                # 检查是否需要锁定账户
                if user.user_failed_login_attempts >= self.max_failed_attempts:
                    user.user_status = UserStatus.LOCKED
                    user.user_locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
                    
                    login_log.failure_reason = f"密码错误，账户已锁定{self.lockout_duration}分钟"
                else:
                    remaining_attempts = self.max_failed_attempts - user.user_failed_login_attempts
                    login_log.failure_reason = f"密码错误，还有{remaining_attempts}次尝试机会"
                
                login_log.user_id = user.user_id
                db.add(login_log)
                await db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=login_log.failure_reason
                )
            
            # 登录成功，重置失败计数
            user.user_failed_login_attempts = 0
            user.user_last_login_time = datetime.utcnow()
            user.user_last_login_ip = ip_address
            user.user_last_activity = datetime.utcnow()
            user.user_login_count += 1
            
            # 准备设备信息
            device_info = {
                "username": user.user_name,
                "role": user.user_role.value,
                "device_id": secrets.token_hex(16),
                "device_name": request.headers.get("X-Device-Name", "Unknown Device"),
                "device_type": "web",
                "user_agent": user_agent,
                "ip_address": ip_address
            }
            
            # 创建会话
            session_data = await self.create_user_session(user.user_id, device_info)
            
            # 记录成功的登录日志
            login_log.is_success = True
            login_log.email = user.user_email
            login_log.user_id = user.user_id
            db.add(login_log)
            
            await db.commit()
            
            logger.info(f"用户登录成功: {username}")
            
            return {
                **session_data,
                "user": {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "user_email": user.user_email,
                    "user_full_name": user.user_full_name,
                    "user_role": user.user_role.value,
                    "user_status": user.user_status.value,
                    "organization_id": user.organization_id,
                    "user_is_verified": user.user_is_verified,
                    "created_time": user.created_time,
                    "last_login_time": user.user_last_login_time
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            login_log.failure_reason = f"系统错误: {str(e)}"
            db.add(login_log)
            await db.commit()
            
            logger.error(f"用户认证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="登录失败，请稍后重试"
            )
    
    # =============================================================================
    # 当前用户获取
    # =============================================================================
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        db: AsyncSession = Depends(get_db)
    ) -> ConfigUser:
        """获取当前用户"""
        try:
            token = credentials.credentials
            payload = self.decode_token(token)
            
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的访问令牌类型"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌中缺少用户信息"
                )
            
            # 验证令牌是否在Redis中存在且有效
            token_jti = payload.get("jti")
            if not token_jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌格式无效"
                )
            
            if not await token_service.validate_token(token_jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已失效或不存在"
                )
            
            # 获取用户信息
            user_result = await db.execute(
                select(ConfigUser).where(ConfigUser.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在"
                )
            
            if user.user_status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="用户账户已被禁用"
                )
            
            # 更新用户最后活跃时间
            user.user_last_activity = datetime.utcnow()
            await db.commit()
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="身份验证失败"
            )
    
    # =============================================================================
    # 权限管理
    # =============================================================================
    
    async def has_permission(self, user: ConfigUser, permission: str) -> bool:
        """检查用户是否有指定权限"""
        try:
            user_permissions = self.role_permissions.get(user.user_role, [])
            return permission in user_permissions
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    async def get_user_permissions(self, user: ConfigUser) -> List[str]:
        """获取用户权限列表"""
        return self.role_permissions.get(user.user_role, [])
    
    # =============================================================================
    # 密码管理
    # =============================================================================
    
    async def change_password(
        self,
        user: ConfigUser,
        old_password: str,
        new_password: str,
        db: AsyncSession
    ) -> bool:
        """修改密码"""
        try:
            # 验证原密码
            if not self.verify_password(old_password, user.user_password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="原密码错误"
                )
            
            # 验证新密码强度
            is_valid, message = self.validate_password_strength(new_password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message
                )
            
            # 加密新密码
            new_password_hash = self.hash_password(new_password)

            # 更新用户密码
            user.user_password_hash = new_password_hash
            user.user_password_salt = ""  # 盐值已包含在哈希中
            user.user_last_password_change = datetime.utcnow()
            
            # 撤销所有现有会话（强制重新登录）
            await self.revoke_user_session(user.user_id)
            
            await db.commit()
            
            logger.info(f"用户密码修改成功: {user.user_name}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"密码修改失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码修改失败"
            )


# 全局认证服务实例
auth_service = AuthService()


# 依赖注入函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> ConfigUser:
    """获取当前用户（依赖注入）"""
    return await auth_service.get_current_user(credentials, db)


async def get_current_admin(current_user: ConfigUser = Depends(get_current_user)) -> ConfigUser:
    """获取当前管理员用户"""
    if current_user.user_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_teacher(current_user: ConfigUser = Depends(get_current_user)) -> ConfigUser:
    """获取当前教师用户"""
    if current_user.user_role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user


async def get_current_student(current_user: ConfigUser = Depends(get_current_user)) -> ConfigUser:
    """获取当前学生用户"""
    if current_user.user_role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学生权限"
        )
    return current_user


def hash_password(password: str) -> str:
    """独立的密码哈希函数 - 供其他模块使用"""
    return auth_service.hash_password(password)
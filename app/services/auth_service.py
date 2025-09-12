"""
认证服务 - 用户认证、授权和权限管理
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.config import settings
from app.core.database import get_db
from app.models.database_models import User, Organization
from app.models.pydantic_models import UserCreate, UserLogin, TokenResponse, UserRole


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        
        # JWT配置
        self.secret_key = settings.jwt.secret
        self.algorithm = settings.jwt.algorithm
        self.access_token_expire = settings.jwt.expire_minutes
        self.refresh_token_expire_days = settings.jwt.refresh_expire_days
        
        # 权限定义
        self.permissions = {
            UserRole.ADMIN: [
                "user:create", "user:read", "user:update", "user:delete",
                "organization:create", "organization:read", "organization:update", 
                "question:create", "question:read", "question:update", "question:delete",
                "homework:create", "homework:read", "homework:update", "homework:delete",
                "system:config", "system:logs"
            ],
            UserRole.TEACHER: [
                "question:create", "question:read", "question:update",
                "homework:create", "homework:read", "homework:update",
                "student:read", "chat:read", "analytics:read"
            ],
            UserRole.STUDENT: [
                "question:read", "homework:read", "chat:create", "chat:read"
            ]
        }
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效令牌"
            )
    
    async def register_user(self, user_data: UserCreate, db: AsyncSession) -> Dict[str, Any]:
        """用户注册"""
        try:
            # 检查用户名和邮箱是否已存在
            existing_user = await db.execute(
                select(User).where(
                    (User.username == user_data.username) | 
                    (User.email == user_data.email)
                )
            )
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名或邮箱已存在"
                )
            
            # 验证机构代码（如果提供）
            organization_id = None
            if user_data.organization_code:
                org_result = await db.execute(
                    select(Organization).where(Organization.code == user_data.organization_code)
                )
                organization = org_result.scalar_one_or_none()
                if not organization:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="无效的机构代码"
                    )
                organization_id = organization.id
            
            # 创建用户
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=self.hash_password(user_data.password),
                full_name=user_data.full_name,
                role=user_data.role,
                organization_id=organization_id
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"用户注册成功: {user.username}")
            
            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"用户注册失败: {e}")
            raise
    
    async def authenticate_user(self, credentials: UserLogin, db: AsyncSession) -> TokenResponse:
        """用户认证"""
        try:
            # 查找用户
            result = await db.execute(
                select(User).where(User.username == credentials.username)
            )
            user = result.scalar_one_or_none()
            
            if not user or not self.verify_password(credentials.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="账户已被禁用"
                )
            
            # 生成令牌
            token_data = {"sub": user.id, "username": user.username, "role": user.role}
            access_token = self.create_access_token(token_data)
            refresh_token = self.create_refresh_token(token_data)
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            await db.commit()
            
            logger.info(f"用户登录成功: {user.username}")
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire * 60,
                user={
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "organization_id": user.organization_id,
                    "created_at": user.created_at,
                    "last_login": user.last_login
                }
            )
            
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str, db: AsyncSession) -> Dict[str, Any]:
        """刷新访问令牌"""
        try:
            payload = self.decode_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的刷新令牌"
                )
            
            user_id = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")
            
            # 验证用户仍然存在且活跃
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在或已被禁用"
                )
            
            # 生成新的访问令牌
            token_data = {"sub": user_id, "username": username, "role": role}
            new_access_token = self.create_access_token(token_data)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire * 60
            }
            
        except Exception as e:
            logger.error(f"令牌刷新失败: {e}")
            raise
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """获取当前用户"""
        try:
            payload = self.decode_token(credentials.credentials)
            
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的访问令牌"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌中缺少用户信息"
                )
            
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="账户已被禁用"
                )
            
            return user
            
        except Exception as e:
            logger.error(f"获取当前用户失败: {e}")
            raise
    
    async def has_permission(self, user: User, permission: str) -> bool:
        """检查用户权限"""
        user_permissions = self.permissions.get(UserRole(user.role), [])
        return permission in user_permissions
    
    def require_permission(self, permission: str):
        """权限装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 从kwargs中获取current_user
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要认证"
                    )
                
                if not await self.has_permission(current_user, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="权限不足"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, required_role: UserRole):
        """角色装饰器"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要认证"
                    )
                
                if UserRole(current_user.role) != required_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要{required_role}角色"
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def get_user_permissions(self, user: User) -> List[str]:
        """获取用户权限列表"""
        return self.permissions.get(UserRole(user.role), [])
    
    async def change_password(
        self, 
        user: User, 
        old_password: str, 
        new_password: str, 
        db: AsyncSession
    ) -> bool:
        """修改密码"""
        try:
            if not self.verify_password(old_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="原密码错误"
                )
            
            user.password_hash = self.hash_password(new_password)
            await db.commit()
            
            logger.info(f"用户密码修改成功: {user.username}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"密码修改失败: {e}")
            raise


# 全局认证服务实例
auth_service = AuthService()


# 依赖注入函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户（依赖注入）"""
    return await auth_service.get_current_user(credentials, db)


async def get_current_teacher(current_user: User = Depends(get_current_user)) -> User:
    """获取当前教师用户"""
    if UserRole(current_user.role) not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user


async def get_current_student(current_user: User = Depends(get_current_user)) -> User:
    """获取当前学生用户"""
    if UserRole(current_user.role) != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学生权限"
        )
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if UserRole(current_user.role) != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
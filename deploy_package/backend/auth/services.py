"""
用户鉴权服务
"""
import os
import re
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.context import CryptContext

from .models import PhoneWhitelist, UsageRecord, AdminUser, hash_phone, generate_id

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 1

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthError(Exception):
    """鉴权错误"""
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthService:
    """用户鉴权服务"""
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏"""
        if len(phone) != 11:
            return phone
        return phone[:3] + "****" + phone[-4:]
    
    @classmethod
    def login(cls, db: Session, phone: str) -> Dict:
        """
        用户登录
        
        Returns:
            {
                "access_token": "...",
                "token_type": "Bearer",
                "expires_in": 86400,
                "user": {
                    "phone_masked": "138****8000",
                    "total_quota": 10,
                    "used_quota": 3,
                    "remaining_quota": 7
                }
            }
        """
        # 1. 验证手机号格式
        if not cls.validate_phone(phone):
            raise AuthError("手机号格式错误", 2001)
        
        # 2. 计算手机号哈希
        phone_hash = hash_phone(phone)
        
        # 3. 查询白名单
        whitelist = db.query(PhoneWhitelist).filter(
            PhoneWhitelist.phone_hash == phone_hash
        ).first()
        
        if not whitelist:
            raise AuthError("手机号未授权，请联系管理员", 1001)
        
        # 4. 检查状态
        if whitelist.status != "active":
            raise AuthError("账号已禁用，请联系管理员", 1003)
        
        # 5. 检查配额
        remaining = whitelist.remaining_quota
        if remaining <= 0:
            raise AuthError("使用次数已用完", 1002)
        
        # 6. 生成 JWT Token
        expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
        payload = {
            "sub": phone_hash,
            "remaining_quota": remaining,
            "exp": expire,
            "type": "user"
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # 7. 更新最后使用时间
        whitelist.last_used_at = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRE_DAYS * 86400,
            "user": {
                "phone_masked": cls.mask_phone(phone),
                "total_quota": whitelist.total_quota,
                "used_quota": whitelist.used_quota,
                "remaining_quota": remaining
            }
        }
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict]:
        """验证 Token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return {
                "phone_hash": payload.get("sub"),
                "remaining_quota": payload.get("remaining_quota"),
                "type": payload.get("type", "user")
            }
        except jwt.ExpiredSignatureError:
            raise AuthError("Token 已过期", 1004)
        except jwt.InvalidTokenError:
            raise AuthError("Token 无效", 1004)


class QuotaService:
    """配额服务"""
    
    @classmethod
    def consume_quota(cls, db: Session, phone_hash: str, feature: str, 
                      feature_name: str, session_id: str, metadata: Optional[Dict] = None) -> Dict:
        """
        扣减使用次数
        
        Returns:
            {"consumed": True, "remaining_quota": 6}
        """
        # 查询白名单
        whitelist = db.query(PhoneWhitelist).filter(
            PhoneWhitelist.phone_hash == phone_hash
        ).with_for_update().first()
        
        if not whitelist:
            raise AuthError("白名单记录不存在", 1001)
        
        # 检查剩余次数
        remaining = whitelist.remaining_quota
        if remaining <= 0:
            raise AuthError("使用次数已用完", 1002)
        
        # 扣减次数
        whitelist.used_quota += 1
        new_remaining = whitelist.remaining_quota
        
        # 记录使用日志
        usage_record = UsageRecord(
            id=generate_id("ur"),
            phone_hash=phone_hash,
            feature=feature,
            feature_name=feature_name,
            session_id=session_id,
            consumed_before=remaining,
            consumed_after=new_remaining,
            meta_data=metadata
        )
        db.add(usage_record)
        db.commit()
        
        return {
            "consumed": True,
            "remaining_quota": new_remaining
        }
    
    @classmethod
    def get_quota(cls, db: Session, phone_hash: str) -> Dict:
        """获取当前配额"""
        whitelist = db.query(PhoneWhitelist).filter(
            PhoneWhitelist.phone_hash == phone_hash
        ).first()
        
        if not whitelist:
            raise AuthError("白名单记录不存在", 1001)
        
        return {
            "total_quota": whitelist.total_quota,
            "used_quota": whitelist.used_quota,
            "remaining_quota": whitelist.remaining_quota,
            "last_used_at": whitelist.last_used_at.isoformat() if whitelist.last_used_at else None
        }


class WhitelistService:
    """白名单管理服务"""
    
    @classmethod
    def add_whitelist(cls, db: Session, phone: str, total_quota: int = 10, 
                      remark: Optional[str] = None, created_by: str = "admin") -> PhoneWhitelist:
        """添加白名单，如果已存在则累加配额"""
        # 验证手机号
        if not AuthService.validate_phone(phone):
            raise AuthError("手机号格式错误", 2001)
        
        phone_hash = hash_phone(phone)
        
        # 检查是否已存在
        existing = db.query(PhoneWhitelist).filter(
            PhoneWhitelist.phone_hash == phone_hash
        ).first()
        
        if existing:
            # 已存在，累加配额
            existing.total_quota += total_quota
            if remark:
                existing.remark = remark
            db.commit()
            db.refresh(existing)
            return existing
        
        # 创建白名单记录
        whitelist = PhoneWhitelist(
            phone_hash=phone_hash,
            phone_number=phone,  # 存储明文手机号
            total_quota=total_quota,
            remark=remark,
            created_by=created_by
        )
        db.add(whitelist)
        db.commit()
        db.refresh(whitelist)
        
        return whitelist
    
    @classmethod
    def get_whitelist(cls, db: Session, whitelist_id: str) -> Optional[PhoneWhitelist]:
        """获取白名单详情"""
        return db.query(PhoneWhitelist).filter(PhoneWhitelist.id == whitelist_id).first()
    
    @classmethod
    def list_whitelist(cls, db: Session, status: Optional[str] = None, 
                       skip: int = 0, limit: int = 100) -> list:
        """获取白名单列表"""
        query = db.query(PhoneWhitelist)
        if status:
            query = query.filter(PhoneWhitelist.status == status)
        return query.order_by(PhoneWhitelist.created_at.desc()).offset(skip).limit(limit).all()
    
    @classmethod
    def update_quota(cls, db: Session, whitelist_id: str, total_quota: int) -> PhoneWhitelist:
        """修改配额"""
        if total_quota < 0:
            raise AuthError("配额不能为负数", 2003)
        
        whitelist = db.query(PhoneWhitelist).filter(PhoneWhitelist.id == whitelist_id).first()
        if not whitelist:
            raise AuthError("白名单记录不存在", 1001)
        
        whitelist.total_quota = total_quota
        db.commit()
        db.refresh(whitelist)
        return whitelist
    
    @classmethod
    def update_status(cls, db: Session, whitelist_id: str, status: str) -> PhoneWhitelist:
        """修改状态"""
        if status not in ["active", "disabled"]:
            raise AuthError("状态值无效", 2003)
        
        whitelist = db.query(PhoneWhitelist).filter(PhoneWhitelist.id == whitelist_id).first()
        if not whitelist:
            raise AuthError("白名单记录不存在", 1001)
        
        whitelist.status = status
        db.commit()
        db.refresh(whitelist)
        return whitelist
    
    @classmethod
    def delete_whitelist(cls, db: Session, whitelist_id: str):
        """删除白名单"""
        whitelist = db.query(PhoneWhitelist).filter(PhoneWhitelist.id == whitelist_id).first()
        if not whitelist:
            raise AuthError("白名单记录不存在", 1001)
        
        db.delete(whitelist)
        db.commit()
    
    @classmethod
    def get_usage_records(cls, db: Session, phone_hash: str, skip: int = 0, 
                          limit: int = 100) -> list:
        """获取使用记录"""
        return db.query(UsageRecord).filter(
            UsageRecord.phone_hash == phone_hash
        ).order_by(UsageRecord.consumed_at.desc()).offset(skip).limit(limit).all()


class AdminService:
    """管理员服务"""
    
    @classmethod
    def create_admin(cls, db: Session, username: str, password: str) -> AdminUser:
        """创建管理员"""
        # 检查是否已存在
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            raise AuthError("管理员已存在", 2002)
        
        # bcrypt 密码长度限制为 72 字节
        password_bytes = password.encode('utf-8')[:72]
        admin = AdminUser(
            username=username,
            password_hash=pwd_context.hash(password_bytes)
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    
    @classmethod
    def login_admin(cls, db: Session, username: str, password: str) -> Dict:
        """管理员登录"""
        admin = db.query(AdminUser).filter(AdminUser.username == username).first()
        # bcrypt 密码长度限制为 72 字节
        password_bytes = password.encode('utf-8')[:72]
        if not admin or not pwd_context.verify(password_bytes, admin.password_hash):
            raise AuthError("用户名或密码错误", 1004)
        
        # 生成 Token
        expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
        payload = {
            "sub": admin.id,
            "username": admin.username,
            "type": "admin",
            "exp": expire
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # 更新最后登录时间
        admin.last_login_at = datetime.utcnow()
        db.commit()
        
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRE_DAYS * 86400,
            "admin": {
                "id": admin.id,
                "username": admin.username
            }
        }
    
    @classmethod
    def verify_admin_token(cls, token: str) -> Optional[Dict]:
        """验证管理员 Token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "admin":
                raise AuthError("无管理员权限", 1005)
            return {
                "admin_id": payload.get("sub"),
                "username": payload.get("username"),
                "type": "admin"
            }
        except jwt.ExpiredSignatureError:
            raise AuthError("Token 已过期", 1004)
        except jwt.InvalidTokenError:
            raise AuthError("Token 无效", 1004)

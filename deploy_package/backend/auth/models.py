"""
用户鉴权数据库模型
使用 SQLite 简化实现（生产环境可替换为 PostgreSQL）
"""
import os
import hashlib
import secrets
import string
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 使用 SQLite 简化实现
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./interview_auth.db")

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_id(prefix: str, length: int = 16) -> str:
    """生成唯一ID"""
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}_{random_part}"


def hash_phone(phone: str) -> str:
    """手机号 SHA256 哈希"""
    return hashlib.sha256(phone.encode()).hexdigest()


class PhoneWhitelist(Base):
    """手机号白名单表"""
    __tablename__ = "phone_whitelist"
    
    id = Column(String(32), primary_key=True, default=lambda: generate_id("wl"))
    phone_hash = Column(String(64), nullable=False, unique=True, index=True)
    phone_number = Column(String(20), nullable=False)  # 明文手机号
    total_quota = Column(Integer, nullable=False, default=10)
    used_quota = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")  # active/disabled
    remark = Column(String(200), nullable=True)
    created_by = Column(String(32), nullable=False, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    @property
    def remaining_quota(self) -> int:
        """剩余次数"""
        return max(0, self.total_quota - self.used_quota)
    
    def to_dict(self):
        return {
            "id": self.id,
            "phone": self.phone_number,  # 显示明文手机号
            "phone_hash": self.phone_hash[:8] + "...",
            "total_quota": self.total_quota,
            "used_quota": self.used_quota,
            "remaining_quota": self.remaining_quota,
            "status": self.status,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class UsageRecord(Base):
    """使用记录表"""
    __tablename__ = "usage_records"
    
    id = Column(String(32), primary_key=True, default=lambda: generate_id("ur"))
    phone_hash = Column(String(64), nullable=False, index=True)
    feature = Column(String(20), nullable=False, index=True)  # parse/score/interview
    feature_name = Column(String(50), nullable=False)
    session_id = Column(String(64), nullable=False, index=True)
    consumed_at = Column(DateTime, default=datetime.utcnow)
    consumed_before = Column(Integer, nullable=False)
    consumed_after = Column(Integer, nullable=False)
    meta_data = Column(JSON, nullable=True)  # 使用 meta_data 避免与 SQLAlchemy metadata 冲突
    
    def to_dict(self):
        return {
            "id": self.id,
            "phone_hash": self.phone_hash[:8] + "...",
            "feature": self.feature,
            "feature_name": self.feature_name,
            "session_id": self.session_id,
            "consumed_at": self.consumed_at.isoformat() if self.consumed_at else None,
            "consumed_before": self.consumed_before,
            "consumed_after": self.consumed_after
        }


class AdminUser(Base):
    """管理员表"""
    __tablename__ = "admin_users"
    
    id = Column(String(32), primary_key=True, default=lambda: generate_id("admin"))
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)


# 创建所有表
def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

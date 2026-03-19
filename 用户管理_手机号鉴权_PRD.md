# AI 智能面试助手 - 用户管理与手机号鉴权模块

> 需求文档（PRD）for Kimi Code  
> 版本: v1.0  
> 日期: 2026-03-17

---

## 1. 产品概述

### 1.1 功能定位
用户管理与手机号鉴权模块是 AI 智能面试助手的访问控制层，采用**白名单 + 次数限制**的鉴权模式，确保只有授权用户才能使用系统功能。

### 1.2 核心规则
1. **白名单机制**：只有被管理员手动添加的手机号才能通过鉴权
2. **次数限制**：每个手机号有独立的使用次数配额
3. **双重校验**：白名单通过 + 次数充足 才能使用功能

### 1.3 使用场景
- 用户首次访问系统，输入手机号进行鉴权
- 用户使用功能时，系统检查剩余次数并扣减
- 管理员在后台管理白名单和配额

---

## 2. 功能模块

### 2.1 模块列表

| 模块 | 功能 | 优先级 |
|------|------|--------|
| 用户鉴权 | 手机号登录、Token 发放 | P0 |
| 次数管理 | 配额扣减、使用记录 | P0 |
| 白名单管理 | 增删改查、批量导入 | P0 |
| 管理后台 | 白名单管理界面 | P1 |

---

## 3. 技术架构

### 3.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI | Python 3.10+ |
| 数据库 | PostgreSQL 14+ | 主数据库 |
| ORM | SQLAlchemy 2.0+ | 异步支持 |
| 缓存 | Redis 7+ | Token、限流 |
| 加密 | cryptography | AES-256-GCM |
| 认证 | PyJWT | JWT Token |
| 迁移 | Alembic | 数据库迁移 |

---

## 4. 数据库设计

### 4.1 白名单表 (phone_whitelist)

```sql
CREATE TABLE phone_whitelist (
    id VARCHAR(32) PRIMARY KEY COMMENT '记录ID，如: wl_abc123',
    phone_encrypted VARCHAR(255) NOT NULL COMMENT 'AES加密后的手机号',
    phone_hash VARCHAR(64) NOT NULL COMMENT '手机号SHA256哈希，用于查询',
    total_quota INT NOT NULL DEFAULT 10 COMMENT '总使用次数配额',
    used_quota INT NOT NULL DEFAULT 0 COMMENT '已使用次数',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态: active/disabled',
    remark VARCHAR(200) NULL COMMENT '备注，如: 客户名称',
    created_by VARCHAR(32) NOT NULL COMMENT '创建人ID',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE NULL COMMENT '最后使用时间',
    
    CONSTRAINT uk_phone_hash UNIQUE (phone_hash),
    CONSTRAINT chk_total_quota CHECK (total_quota >= 0),
    CONSTRAINT chk_used_quota CHECK (used_quota >= 0)
);

CREATE INDEX idx_whitelist_status ON phone_whitelist(status);
CREATE INDEX idx_whitelist_created_at ON phone_whitelist(created_at);
CREATE INDEX idx_whitelist_last_used ON phone_whitelist(last_used_at);
```

### 4.2 使用记录表 (usage_records)

```sql
CREATE TABLE usage_records (
    id VARCHAR(32) PRIMARY KEY COMMENT '记录ID，如: ur_abc123',
    phone_hash VARCHAR(64) NOT NULL COMMENT '手机号',
    feature VARCHAR(20) NOT NULL COMMENT '功能类型: parse/score/interview',
    feature_name VARCHAR(50) NOT NULL COMMENT '功能名称: 简历解析/智能评分/模拟面试',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID，关联业务会话',
    consumed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP COMMENT '扣减时间',
    consumed_before INT NOT NULL COMMENT '扣减前剩余次数',
    consumed_after INT NOT NULL COMMENT '扣减后剩余次数',
    metadata JSONB NULL COMMENT '扩展信息，如: {"company": "美团", "job_name": "产品经理"}',
    
    CONSTRAINT chk_consumed_before CHECK (consumed_before >= 0),
    CONSTRAINT chk_consumed_after CHECK (consumed_after >= 0)
);

CREATE INDEX idx_usage_phone_hash ON usage_records(phone_hash);
CREATE INDEX idx_usage_consumed_at ON usage_records(consumed_at);
CREATE INDEX idx_usage_feature ON usage_records(feature);
CREATE INDEX idx_usage_session ON usage_records(session_id);
```

---

## 5. 接口定义

### 5.1 用户鉴权接口

#### POST /api/v1/auth/login - 手机号登录

**请求体：**
```json
{
  "phone": "13800138000"
}
```

**成功响应 (200)：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "phone_masked": "138****8000",
      "total_quota": 10,
      "used_quota": 3,
      "remaining_quota": 7
    }
  }
}
```

**失败响应：**
- 1001: 手机号未授权
- 1002: 使用次数已用完
- 1003: 账号已禁用

#### GET /api/v1/auth/quota - 查询当前配额

**请求头：** `Authorization: Bearer <token>`

**响应：**
```json
{
  "code": 0,
  "data": {
    "total_quota": 10,
    "used_quota": 3,
    "remaining_quota": 7,
    "last_used_at": "2026-03-17T14:30:00+08:00"
  }
}
```

### 5.2 次数扣减接口

#### POST /api/v1/quota/consume - 扣减使用次数

**请求头：** `Authorization: Bearer <token>`

**请求体：**
```json
{
  "feature": "score",
  "session_id": "sess_abc123",
  "metadata": {
    "company": "美团",
    "job_name": "产品经理"
  }
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "consumed": true,
    "remaining_quota": 6
  }
}
```

### 5.3 管理员接口

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/admin/whitelist | POST | 添加白名单 |
| /api/v1/admin/whitelist/batch | POST | 批量添加 |
| /api/v1/admin/whitelist | GET | 获取列表 |
| /api/v1/admin/whitelist/{id}/quota | PUT | 修改配额 |
| /api/v1/admin/whitelist/{id}/status | PUT | 修改状态 |
| /api/v1/admin/whitelist/{id} | DELETE | 删除 |
| /api/v1/admin/whitelist/{id}/usage | GET | 使用记录 |
| /api/v1/admin/whitelist/export | GET | 导出 |

---

## 6. 核心代码实现

### 6.1 用户登录服务

```python
class AuthService:
    async def login(self, phone: str) -> LoginResult:
        # 1. 校验手机号格式
        if not self._validate_phone(phone):
            raise ValidationError("手机号格式错误")
        
        # 2. 计算手机号哈希
        phone_hash = self._hash_phone(phone)
        
        # 3. 查询白名单
        whitelist = await self._get_whitelist_by_hash(phone_hash)
        if not whitelist:
            raise AuthError("手机号未授权，请联系管理员", code=1001)
        
        # 4. 检查状态
        if whitelist.status != "active":
            raise AuthError("账号已禁用，请联系管理员", code=1003)
        
        # 5. 检查配额
        remaining = whitelist.total_quota - whitelist.used_quota
        if remaining <= 0:
            raise AuthError("使用次数已用完", code=1002)
        
        # 6. 生成 Token
        token = self._generate_token(phone_hash, remaining)
        
        # 7. 更新最后登录时间
        await self._update_last_login(whitelist.id)
        
        return LoginResult(
            access_token=token,
            user=UserInfo(
                phone_masked=self._mask_phone(phone),
                total_quota=whitelist.total_quota,
                used_quota=whitelist.used_quota,
                remaining_quota=remaining
            )
        )
```

### 6.2 次数扣减服务

```python
class QuotaService:
    async def consume_quota(self, phone_hash: str, feature: str, 
                           feature_name: str, session_id: str) -> ConsumeResult:
        async with self.db.begin():
            # 1. 查询白名单（加锁）
            whitelist = await self.db.execute(
                select(PhoneWhitelist)
                .where(PhoneWhitelist.phone_hash == phone_hash)
                .with_for_update()
            )
            whitelist = whitelist.scalar_one_or_none()
            
            if not whitelist:
                raise NotFoundError("白名单记录不存在")
            
            # 2. 检查剩余次数
            remaining = whitelist.total_quota - whitelist.used_quota
            if remaining <= 0:
                raise QuotaExceededError("使用次数已用完")
            
            # 3. 扣减次数
            new_used = whitelist.used_quota + 1
            await self.db.execute(
                update(PhoneWhitelist)
                .where(PhoneWhitelist.id == whitelist.id)
                .values(used_quota=new_used, last_used_at=datetime.utcnow())
            )
            
            # 4. 记录使用日志
            usage_record = UsageRecord(
                id=generate_id("ur"),
                phone_hash=phone_hash,
                feature=feature,
                feature_name=feature_name,
                session_id=session_id,
                consumed_before=remaining,
                consumed_after=remaining - 1
            )
            self.db.add(usage_record)
        
        return ConsumeResult(consumed=True, remaining_quota=remaining - 1)
```

### 6.3 鉴权中间件

```python
class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.public_paths = ["/api/v1/auth/login", "/api/v1/health", "/docs"]
    
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.public_paths):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")
        
        token = auth_header.replace("Bearer ", "")
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            request.state.phone_hash = payload.get("sub")
            request.state.remaining_quota = payload.get("remaining_quota")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return await call_next(request)
```

### 6.4 加密工具

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import hashlib
import os

class PhoneEncryption:
    def __init__(self, key: bytes):
        self.aesgcm = AESGCM(key)
    
    def encrypt(self, phone: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, phone.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted.encode())
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()
    
    @staticmethod
    def hash(phone: str) -> str:
        return hashlib.sha256(phone.encode()).hexdigest()
```

### 6.5 ID 生成器

```python
import secrets
import string

def generate_id(prefix: str, length: int = 16) -> str:
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}_{random_part}"
```

---

## 7. 数据模型

### 7.1 SQLAlchemy 模型

```python
class PhoneWhitelist(Base):
    __tablename__ = "phone_whitelist"
    
    id = Column(String(32), primary_key=True)
    phone_encrypted = Column(String(255), nullable=False)
    phone_hash = Column(String(64), nullable=False, unique=True)
    total_quota = Column(Integer, nullable=False, default=10)
    used_quota = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")
    remark = Column(String(200), nullable=True)
    created_by = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def remaining_quota(self) -> int:
        return max(0, self.total_quota - self.used_quota)


class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(String(32), primary_key=True)
    phone_hash = Column(String(64), nullable=False, index=True)
    feature = Column(String(20), nullable=False, index=True)
    feature_name = Column(String(50), nullable=False)
    session_id = Column(String(64), nullable=False, index=True)
    consumed_at = Column(DateTime(timezone=True), server_default=func.now())
    consumed_before = Column(Integer, nullable=False)
    consumed_after = Column(Integer, nullable=False)
    metadata = Column(JSON, nullable=True)
```

### 7.2 Pydantic 模型

```python
class LoginRequest(BaseModel):
    phone: str = Field(..., regex=r'^1[3-9]\d{9}$')

class ConsumeQuotaRequest(BaseModel):
    feature: str = Field(..., regex=r'^(parse|score|interview)$')
    session_id: str
    metadata: Optional[dict] = None

class CreateWhitelistRequest(BaseModel):
    phone: str = Field(..., regex=r'^1[3-9]\d{9}$')
    total_quota: int = Field(default=10, ge=0)
    remark: Optional[str] = Field(default=None, max_length=200)

class UserInfo(BaseModel):
    phone_masked: str
    total_quota: int
    used_quota: int
    remaining_quota: int

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserInfo
```

---

## 8. 配置

### 8.1 环境变量

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/interview_db
REDIS_URL=redis://localhost:6379/0
ENCRYPTION_KEY=b64encoded_32byte_key
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=1
```

### 8.2 配置文件

```python
class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    encryption_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 1
    
    class Config:
        env_file = ".env"
```

---

## 9. 错误码

| 错误码 | 说明 | HTTP状态码 |
|--------|------|-----------|
| 0 | 成功 | 200 |
| 1001 | 手机号未授权 | 403 |
| 1002 | 使用次数已用完 | 403 |
| 1003 | 账号已禁用 | 403 |
| 1004 | Token 无效或过期 | 401 |
| 1005 | 无管理员权限 | 403 |
| 2001 | 手机号格式错误 | 400 |
| 2002 | 手机号已存在 | 409 |
| 2003 | 配额不能为负数 | 400 |

---

## 10. 项目结构

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # 鉴权路由
│   │   ├── quota.py         # 配额路由
│   │   └── admin.py         # 管理路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── quota_service.py
│   │   └── whitelist_service.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth_middleware.py
│   └── utils/
│       ├── __init__.py
│       ├── encryption.py
│       └── id_generator.py
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── .env                     # 环境变量
└── requirements.txt
```

---

## 11. 依赖安装

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1
redis==5.0.1
pyjwt==2.8.0
cryptography==41.0.7
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
openpyxl==3.1.2          # Excel导出
```

---

*文档版本: v1.0*  
*创建日期: 2026-03-17*  
*作者: AI 智能面试助手开发团队*

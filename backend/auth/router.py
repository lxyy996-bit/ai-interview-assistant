"""
用户鉴权路由
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from .models import get_db
from .services import AuthService, QuotaService, WhitelistService, AdminService, AuthError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
security = HTTPBearer(auto_error=False)


# ============ Pydantic 模型 ============

class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$')


class LoginResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict


class QuotaResponse(BaseModel):
    code: int = 0
    data: dict


class ConsumeQuotaRequest(BaseModel):
    feature: str = Field(..., pattern=r'^(parse|score|interview)$')
    session_id: str
    metadata: Optional[dict] = None


class CreateWhitelistRequest(BaseModel):
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$')
    total_quota: int = Field(default=10, ge=0)
    remark: Optional[str] = Field(default=None, max_length=200)


class UpdateQuotaRequest(BaseModel):
    total_quota: int = Field(..., ge=0)


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., pattern=r'^(active|disabled)$')


class AdminLoginRequest(BaseModel):
    username: str
    password: str


# ============ 依赖函数 ============

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                     db: Session = Depends(get_db)):
    """获取当前登录用户"""
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少认证信息")
    
    try:
        token_data = AuthService.verify_token(credentials.credentials)
        return token_data
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security),
                      db: Session = Depends(get_db)):
    """获取当前管理员"""
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少认证信息")
    
    try:
        admin_data = AdminService.verify_admin_token(credentials.credentials)
        return admin_data
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.message)


# ============ 用户鉴权接口 ============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """手机号登录"""
    try:
        result = AuthService.login(db, request.phone)
        return LoginResponse(data=result)
    except AuthError as e:
        raise HTTPException(status_code=403, detail={"code": e.code, "message": e.message})


@router.get("/quota", response_model=QuotaResponse)
async def get_quota(current_user: dict = Depends(get_current_user), 
                    db: Session = Depends(get_db)):
    """查询当前配额"""
    try:
        result = QuotaService.get_quota(db, current_user["phone_hash"])
        return QuotaResponse(data=result)
    except AuthError as e:
        raise HTTPException(status_code=403, detail={"code": e.code, "message": e.message})


@router.post("/quota/consume", response_model=QuotaResponse)
async def consume_quota(request: ConsumeQuotaRequest,
                        current_user: dict = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """扣减使用次数"""
    try:
        feature_names = {
            "parse": "简历解析",
            "score": "智能评分",
            "interview": "模拟面试"
        }
        result = QuotaService.consume_quota(
            db=db,
            phone_hash=current_user["phone_hash"],
            feature=request.feature,
            feature_name=feature_names.get(request.feature, request.feature),
            session_id=request.session_id,
            metadata=request.metadata
        )
        return QuotaResponse(data=result)
    except AuthError as e:
        raise HTTPException(status_code=403, detail={"code": e.code, "message": e.message})


# ============ 管理员接口 ============

@admin_router.post("/login", response_model=LoginResponse)
async def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    try:
        result = AdminService.login_admin(db, request.username, request.password)
        return LoginResponse(data=result)
    except AuthError as e:
        raise HTTPException(status_code=401, detail={"code": e.code, "message": e.message})


@admin_router.post("/whitelist")
async def create_whitelist(request: CreateWhitelistRequest,
                           admin: dict = Depends(get_current_admin),
                           db: Session = Depends(get_db)):
    """添加白名单"""
    try:
        whitelist = WhitelistService.add_whitelist(
            db=db,
            phone=request.phone,
            total_quota=request.total_quota,
            remark=request.remark,
            created_by=admin["admin_id"]
        )
        return {"code": 0, "data": whitelist.to_dict()}
    except AuthError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@admin_router.get("/whitelist")
async def list_whitelist(status: Optional[str] = None,
                         skip: int = 0, limit: int = 100,
                         admin: dict = Depends(get_current_admin),
                         db: Session = Depends(get_db)):
    """获取白名单列表"""
    whitelists = WhitelistService.list_whitelist(db, status=status, skip=skip, limit=limit)
    return {
        "code": 0,
        "data": {
            "total": len(whitelists),
            "items": [w.to_dict() for w in whitelists]
        }
    }


@admin_router.put("/whitelist/{whitelist_id}/quota")
async def update_whitelist_quota(whitelist_id: str,
                                 request: UpdateQuotaRequest,
                                 admin: dict = Depends(get_current_admin),
                                 db: Session = Depends(get_db)):
    """修改配额"""
    try:
        whitelist = WhitelistService.update_quota(db, whitelist_id, request.total_quota)
        return {"code": 0, "data": whitelist.to_dict()}
    except AuthError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@admin_router.put("/whitelist/{whitelist_id}/status")
async def update_whitelist_status(whitelist_id: str,
                                  request: UpdateStatusRequest,
                                  admin: dict = Depends(get_current_admin),
                                  db: Session = Depends(get_db)):
    """修改状态"""
    try:
        whitelist = WhitelistService.update_status(db, whitelist_id, request.status)
        return {"code": 0, "data": whitelist.to_dict()}
    except AuthError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@admin_router.delete("/whitelist/{whitelist_id}")
async def delete_whitelist(whitelist_id: str,
                           admin: dict = Depends(get_current_admin),
                           db: Session = Depends(get_db)):
    """删除白名单"""
    try:
        WhitelistService.delete_whitelist(db, whitelist_id)
        return {"code": 0, "message": "删除成功"}
    except AuthError as e:
        raise HTTPException(status_code=400, detail={"code": e.code, "message": e.message})


@admin_router.get("/whitelist/{whitelist_id}/usage")
async def get_usage_records(whitelist_id: str,
                            skip: int = 0, limit: int = 100,
                            admin: dict = Depends(get_current_admin),
                            db: Session = Depends(get_db)):
    """获取使用记录"""
    whitelist = WhitelistService.get_whitelist(db, whitelist_id)
    if not whitelist:
        raise HTTPException(status_code=404, detail="白名单记录不存在")
    
    records = WhitelistService.get_usage_records(db, whitelist.phone_hash, skip, limit)
    return {
        "code": 0,
        "data": {
            "total": len(records),
            "items": [r.to_dict() for r in records]
        }
    }

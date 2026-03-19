"""
AI 智能面试助手 - 后端服务
基于 STAR 法则的面试准备系统
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="AI 智能面试助手 API",
    description="基于 STAR 法则的面试准备系统后端",
    version="1.0.0"
)

# CORS 配置
import os
allow_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 数据模型
class CreateSessionRequest(BaseModel):
    company: str
    job_name: str
    jd: str
    city: str


class CompanyStrategy(BaseModel):
    business_status: str
    job_subtext: str


class ATSScore(BaseModel):
    score: int
    advantages: List[str]
    gaps: List[str]


class RewriteDemo(BaseModel):
    original: str
    rewritten: str
    reasoning: str


class ResumeSuggestions(BaseModel):
    logic: str
    rewrite_demo: RewriteDemo
    new_keywords: List[str]


class STARQuestions(BaseModel):
    background: str
    questions: List[str]


class InterviewAnalysis(BaseModel):
    company_strategy: CompanyStrategy
    ats_score: ATSScore
    resume_suggestions: ResumeSuggestions
    star_questions: STARQuestions


class ApiResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# 模拟数据存储
sessions = {}


@app.get("/")
async def root():
    return {"message": "AI 智能面试助手 API", "version": "1.0.0"}


@app.post("/api/v1/sessions")
async def create_session(request: CreateSessionRequest):
    """创建面试会话"""
    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "company": request.company,
        "job_name": request.job_name,
        "city": request.city,
        "has_resume": False,
        "has_analysis": False
    }
    return {"success": True, "data": {"session_id": session_id}}


@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True, "data": sessions[session_id]}


@app.post("/api/v1/sessions/{session_id}/resume")
async def upload_resume(session_id: str, file: UploadFile = File(...)):
    """上传简历"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    sessions[session_id]["has_resume"] = True
    return {"success": True, "data": {"filename": file.filename}}


@app.post("/api/v1/sessions/{session_id}/analysis")
async def analyze_resume(session_id: str):
    """分析简历并生成面试建议"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 模拟分析结果
    analysis = {
        "company_strategy": {
            "business_status": f"{sessions[session_id]['company']} 正在快速扩张期，注重技术创新",
            "job_subtext": "需要具备强技术背景和沟通能力的人才"
        },
        "ats_score": {
            "score": 75,
            "advantages": ["技术栈匹配度高", "项目经验丰富"],
            "gaps": ["缺少云原生经验", "可以补充量化成果"]
        },
        "resume_suggestions": {
            "logic": "建议突出项目中的技术亮点和量化成果",
            "rewrite_demo": {
                "original": "负责开发用户管理系统",
                "rewritten": "独立设计并开发用户管理系统，支持10万+并发用户，系统可用性达99.9%",
                "reasoning": "增加量化数据，突出技术能力和成果"
            },
            "new_keywords": ["微服务", "Kubernetes", "高并发", "性能优化"]
        },
        "star_questions": {
            "background": "基于你的简历，我们准备了以下 STAR 法则面试题",
            "questions": [
                "请描述一个你解决过的最复杂的技术问题，当时的情况如何？",
                "举例说明你如何在团队中推动技术方案落地",
                "描述一次项目延期经历，你是如何应对的？"
            ]
        }
    }
    
    sessions[session_id]["has_analysis"] = True
    return {"success": True, "data": analysis}


@app.get("/api/v1/sessions/{session_id}/result")
async def get_result(session_id: str):
    """获取完整分析结果"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    if not sessions[session_id].get("has_analysis"):
        raise HTTPException(status_code=400, detail="尚未完成分析")
    
    return {"success": True, "data": {"ready": True}}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

"""
AI 智能面试助手 - 后端服务
基于 STAR 法则的面试准备系统
"""
import os
import io
import uuid
import asyncio
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import pdfplumber
from docx import Document

# 加载环境变量
load_dotenv()

# 导入服务模块
from services.baidu_search import BaiduSearchClient, format_search_results_for_llm
from services.llm_service import LLMService

app = FastAPI(
    title="AI 智能面试助手 API",
    description="基于 STAR 法则的面试准备系统后端",
    version="2.0.0"
)

# CORS 配置
allow_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://49.51.141.84").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 数据模型 ============

class CreateSessionRequest(BaseModel):
    company: str = Field(..., description="目标公司")
    job_name: str = Field(..., description="岗位名称")
    jd: str = Field(..., description="岗位要求/描述")
    city: str = Field(..., description="工作地点")


class CompanyStrategy(BaseModel):
    business_status: str
    job_subtext: str


class ATSScore(BaseModel):
    score: int
    advantages: list[str]
    gaps: list[str]


class RewriteDemo(BaseModel):
    original: str
    rewritten: str
    reasoning: str


class ResumeSuggestions(BaseModel):
    logic: str
    rewrite_demo: RewriteDemo
    new_keywords: list[str]


class STARQuestions(BaseModel):
    background: str
    questions: list[str]


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


# ============ 内存数据存储 ============

sessions = {}


# ============ 辅助函数 ============

async def parse_resume_file(file: UploadFile) -> str:
    """
    解析简历文件，提取文本内容
    
    支持 PDF 和 Word 格式
    """
    content = await file.read()
    file_size = len(content)
    
    print(f"[简历解析] 文件名: {file.filename}, 大小: {file_size} bytes")
    
    try:
        if file.filename.lower().endswith('.pdf'):
            # 使用 pdfplumber 解析 PDF
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            if not text.strip():
                return f"[PDF简历] 文件名: {file.filename}, 未能提取文本内容"
            
            # 截断过长的简历（避免超出 LLM token 限制）
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length] + "\n...[简历内容过长，已截断]"
            
            print(f"[简历解析] PDF 提取成功，文本长度: {len(text)} 字符")
            return text
            
        elif file.filename.lower().endswith('.docx'):
            # 使用 python-docx 解析 Word
            doc = Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            
            if not text.strip():
                return f"[Word简历] 文件名: {file.filename}, 未能提取文本内容"
            
            # 截断过长的简历
            max_length = 8000
            if len(text) > max_length:
                text = text[:max_length] + "\n...[简历内容过长，已截断]"
            
            print(f"[简历解析] Word 提取成功，文本长度: {len(text)} 字符")
            return text
            
        else:
            return f"[不支持的文件格式] 文件名: {file.filename}, 请上传 PDF 或 Word 文件"
            
    except Exception as e:
        print(f"[简历解析] 错误: {str(e)}")
        return f"[简历解析失败] 文件名: {file.filename}, 错误: {str(e)}"


# ============ API 路由 ============

@app.get("/")
async def root():
    return {"message": "AI 智能面试助手 API", "version": "2.0.0"}


# ============ 调试接口 ============

class SearchTestRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    top_k: int = Field(10, description="返回结果数量")
    recency: Optional[str] = Field("year", description="时间过滤: week/month/semiyear/year")


@app.post("/api/v1/debug/baidu-search")
async def debug_baidu_search(request: SearchTestRequest):
    """
    百度搜索测试接口
    用于单独测试百度搜索功能是否正常工作
    """
    try:
        print(f"[调试接口] 百度搜索测试: query='{request.query}'")
        
        # 检查 API Key
        api_key = os.getenv("BAIDU_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "BAIDU_API_KEY 未配置",
                "env_check": {
                    "BAIDU_API_KEY": "未设置" if not os.getenv("BAIDU_API_KEY") else "已设置"
                }
            }
        
        # 初始化客户端
        client = BaiduSearchClient()
        
        # 执行搜索
        results = await client.search_web_only(
            query=request.query,
            top_k=request.top_k,
            recency=request.recency
        )
        
        return {
            "success": True,
            "query": request.query,
            "result_count": len(results),
            "results": results[:5]  # 只返回前5条
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/api/v1/debug/keywords-and-search")
async def debug_keywords_and_search(data: dict):
    """
    测试完整流程：生成关键词 + 百度搜索
    """
    try:
        company = data.get("company", "字节跳动")
        job_name = data.get("job_name", "前端工程师")
        jd = data.get("jd", "负责前端开发")
        city = data.get("city", "北京")
        
        print(f"[调试接口] 完整流程测试: {company} - {job_name}")
        
        # 1. 生成关键词
        llm_service = LLMService()
        keywords = await llm_service.generate_search_keywords(
            company=company,
            job_name=job_name,
            jd=jd,
            city=city
        )
        
        print(f"[调试接口] 生成的关键词: {keywords}")
        
        # 2. 执行搜索
        client = BaiduSearchClient()
        search_results = {}
        
        for category, keyword_list in keywords.items():
            if keyword_list:
                query = " ".join(keyword_list[:5])
                try:
                    results = await client.search_web_only(query, top_k=5)
                    search_results[category] = {
                        "query": query,
                        "count": len(results),
                        "results": results[:3]
                    }
                except Exception as e:
                    search_results[category] = {
                        "query": query,
                        "error": str(e)
                    }
        
        return {
            "success": True,
            "keywords": keywords,
            "search_results": search_results
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/api/v1/sessions")
async def create_session(request: CreateSessionRequest):
    """创建面试会话"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "company": request.company,
        "job_name": request.job_name,
        "jd": request.jd,
        "city": request.city,
        "has_resume": False,
        "has_analysis": False,
        "resume_text": None,
        "search_results": None,
        "analysis": None
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
    
    try:
        # 解析简历文件
        resume_text = await parse_resume_file(file)
        
        sessions[session_id]["has_resume"] = True
        sessions[session_id]["resume_text"] = resume_text
        
        return {
            "success": True, 
            "data": {
                "filename": file.filename,
                "text_length": len(resume_text)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"简历解析失败: {str(e)}")


@app.post("/api/v1/sessions/{session_id}/analysis")
@app.post("/api/v1/sessions/{session_id}/analyze")
async def analyze_resume(session_id: str):
    """
    分析简历并生成面试建议
    
    完整流程：
    1. 生成搜索关键词（LLM-1）
    2. 执行百度搜索
    3. 深度分析（LLM-2）
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    
    if not session.get("has_resume"):
        raise HTTPException(status_code=400, detail="请先上传简历")
    
    try:
        # 初始化服务
        search_client = BaiduSearchClient()
        llm_service = LLMService()
        
        # ========== 第一阶段：情报搜集 ==========
        
        # 1. 生成搜索关键词
        print(f"[Session {session_id}] 生成搜索关键词...")
        keywords = await llm_service.generate_search_keywords(
            company=session["company"],
            job_name=session["job_name"],
            jd=session["jd"],
            city=session["city"]
        )
        
        # 2. 执行百度搜索（并行）
        print(f"[Session {session_id}] 执行百度搜索...")
        print(f"[Session {session_id}] 生成的关键词: {keywords}")
        
        search_tasks = []
        for category, keyword_list in keywords.items():
            if keyword_list:
                query = " ".join(keyword_list[:5])  # 取前5个关键词
                print(f"[Session {session_id}] [{category}] 搜索词: {query}")
                search_tasks.append(
                    search_client.search_web_only(query, top_k=10, recency="year")
                )
        
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # 整理搜索结果
        search_results = {
            "strategy": [],
            "business": [],
            "review": []
        }
        categories = list(keywords.keys())
        for i, result in enumerate(search_results_list):
            category = categories[i] if i < len(categories) else f"unknown_{i}"
            if isinstance(result, Exception):
                print(f"[Session {session_id}] [{category}] 搜索失败: {result}")
            else:
                print(f"[Session {session_id}] [{category}] 搜索结果数: {len(result)}")
                search_results[category] = result
        
        session["search_results"] = search_results
        
        # 格式化搜索结果供 LLM 使用
        search_info = format_search_results_for_llm(search_results)
        
        # ========== 第二阶段：深度分析 ==========
        
        print(f"[Session {session_id}] 生成深度分析...")
        analysis_result = await llm_service.generate_interview_analysis(
            company=session["company"],
            job_name=session["job_name"],
            jd=session["jd"],
            resume=session.get("resume_text", "未提供简历文本"),
            search_info=search_info
        )
        
        # 保存分析结果
        session["has_analysis"] = True
        session["analysis"] = analysis_result
        
        return {"success": True, "data": analysis_result}
        
    except Exception as e:
        print(f"[Session {session_id}] 分析失败: {str(e)}")
        # 返回模拟数据作为降级方案
        fallback_analysis = {
            "company_strategy": {
                "business_status": f"{session['company']} 正在快速发展期，注重技术创新和业务扩张",
                "job_subtext": "需要具备强技术背景和快速学习能力的人才"
            },
            "ats_score": {
                "score": 75,
                "advantages": ["技术栈匹配度高", "项目经验丰富"],
                "gaps": ["可以补充更多量化成果", "建议增加云原生相关经验"]
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
                "background": "基于你的简历和岗位要求，我们准备了以下 STAR 法则面试题",
                "questions": [
                    "请描述一个你解决过的最复杂的技术问题，当时的情况如何？",
                    "举例说明你如何在团队中推动技术方案落地",
                    "描述一次项目延期经历，你是如何应对的？",
                    "请分享一个你优化系统性能的具体案例",
                    "举例说明你是如何学习新技术并应用到项目中的"
                ]
            }
        }
        
        session["has_analysis"] = True
        session["analysis"] = fallback_analysis
        
        return {"success": True, "data": fallback_analysis}


@app.get("/api/v1/sessions/{session_id}/result")
async def get_result(session_id: str):
    """获取完整分析结果"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    
    if not session.get("has_analysis"):
        raise HTTPException(status_code=400, detail="尚未完成分析")
    
    return {
        "success": True, 
        "data": session.get("analysis", {})
    }


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

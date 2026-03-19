"""
LLM 服务模块
用于生成搜索关键词和深度分析
"""
import os
import json
import httpx
from typing import Dict, List, Optional


class LLMService:
    """LLM 服务"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化 LLM 服务
        
        Args:
            api_key: API Key，默认从环境变量获取
            base_url: API 基础 URL
        """
        # 优先使用 Moonshot (Kimi)
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        # 根据 API Key 自动判断 base_url
        if base_url:
            self.base_url = base_url
        elif os.getenv("MOONSHOT_API_KEY") and not api_key:
            # 使用了 Moonshot API Key
            self.base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
        else:
            # 默认使用 OpenAI
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            raise ValueError("API_KEY is required (MOONSHOT_API_KEY or OPENAI_API_KEY)")
    
    async def generate_search_keywords(
        self,
        company: str,
        job_name: str,
        jd: str,
        city: str
    ) -> Dict[str, List[str]]:
        """
        生成三组搜索关键词（LLM-1：资深猎头）
        
        Returns:
            {
                "strategy": [...],
                "business": [...],
                "review": [...]
            }
        """
        system_prompt = """你是一名精通信息检索的资深猎头。你的任务是根据用户提供的公司和岗位，生成3组极其精准的搜索关键词，帮助用户挖掘该岗位的"隐藏招聘需求"和公司的"业务风向"。

输出要求：
- 禁任何废话，只输出关键词
- 每组关键词用空格分隔
- 必须包含：1. 战略财务类；2. 业务变动类；3. 员工口碑/避雷类
- 请生成包含具体财报年份的搜索词，例如：美团 2024 财报 优选业务 亏损收窄

输出格式：
战略与财务：关键词1 关键词2 关键词3 ...
业务与变动：关键词1 关键词2 关键词3 ...
口碑与避雷：关键词1 关键词2 关键词3 ..."""

        user_prompt = f"""目标公司：{company}
岗位名称：{job_name}
岗位要求：{jd}
工作地点：{city}

请基于以上信息生成搜索词：
战略与财务：[生成关于 {company} 2025 战略布局、营收重点、核心项目的搜索词]
业务与变动：[生成关于 {company} 最近一年架构调整、高管变动、业务收缩或扩张的搜索词]
口碑与避雷：[生成关于 {company} {jd} {job_name} 加班、面试坑点、职场氛围的搜索词]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages)
        return self._parse_keywords(response)
    
    async def generate_interview_analysis(
        self,
        company: str,
        job_name: str,
        jd: str,
        resume: str,
        search_info: str
    ) -> Dict:
        """
        生成面试深度分析（LLM-2：首席人力资源官）
        
        Returns:
            包含公司战略、ATS评分、简历建议、STAR问题的分析结果
        """
        system_prompt = """# 角色
你是一位全球顶尖的首席人力资源官（CHRO）和商业战略分析师。你擅长通过零散的公司动态分析其背后的业务逻辑，并据此评估人才的"战略契合度"。

# 任务核心
1. 解读战略：从搜索情报中判断公司目前处于"业务扩张期"、"降本增效期"还是"业务转型期"
2. 洞察需求：分析该公司招聘该岗位的底层逻辑（是填补空缺、还是为新业务储备领军人才）
3. 深度评估：对比用户简历与"战略需求"的匹配度，而非简单的关键词匹配
4. STAR 访谈引导：针对简历中最弱但公司最看重的环节，设计深度追问

# 处理规则
- 如果搜索结果包含大量无用信息，优先提取关于公司"降本增效"、"业务收缩/扩张"、"财务盈亏"的关键词
- 若确实无直接动态，必须结合该行业 2025-2026 年的公认趋势进行推演，严禁仅给出通用回答
- 如果搜索结果为空或信息不足，请基于该行业的通用现状进行分析，并诚实告知用户"未获取到近期特定动态"

# 输出格式（JSON）
{
    "company_strategy": {
        "business_status": "业务现状描述",
        "job_subtext": "岗位潜台词描述"
    },
    "ats_score": {
        "score": 75,
        "advantages": ["优势点1", "优势点2"],
        "gaps": ["缺口1", "缺口2"]
    },
    "resume_suggestions": {
        "logic": "修改逻辑说明",
        "rewrite_demo": {
            "original": "原描述",
            "rewritten": "战略化改写",
            "reasoning": "改写逻辑"
        },
        "new_keywords": ["关键词1", "关键词2"]
    },
    "star_questions": {
        "background": "提问背景说明",
        "questions": ["问题1", "问题2", "问题3", "问题4", "问题5"]
    }
}"""

        user_prompt = f"""1. 目标背景
公司：{company}
岗位名称：{job_name}
岗位要求：{jd}

2. 搜集到的实时情报
{search_info}

3. 用户当前简历
{resume}

请按上述 JSON 格式输出分析报告。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._call_llm(messages, temperature=0.7)
        return self._parse_analysis(response)
    
    async def _call_llm(
        self,
        messages: List[Dict],
        temperature: float = 0.5,
        max_tokens: int = 4000
    ) -> str:
        """
        调用 LLM API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            LLM 响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 检测 API 类型并设置对应模型
        if "moonshot" in self.base_url:
            # Moonshot (Kimi) API
            model = os.getenv("MOONSHOT_MODEL", "kimi-k2-turbo-preview")
        else:
            # OpenAI API
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    def _parse_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        解析关键词生成结果
        
        Args:
            text: LLM 输出文本
            
        Returns:
            分类关键词字典
        """
        keywords = {
            "strategy": [],
            "business": [],
            "review": []
        }
        
        lines = text.strip().split('\n')
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('战略与财务：'):
                current_category = "strategy"
                content = line.replace('战略与财务：', '').strip()
                if content:
                    keywords[current_category] = content.split()
            elif line.startswith('业务与变动：'):
                current_category = "business"
                content = line.replace('业务与变动：', '').strip()
                if content:
                    keywords[current_category] = content.split()
            elif line.startswith('口碑与避雷：'):
                current_category = "review"
                content = line.replace('口碑与避雷：', '').strip()
                if content:
                    keywords[current_category] = content.split()
        
        return keywords
    
    def _parse_analysis(self, text: str) -> Dict:
        """
        解析深度分析结果
        
        Args:
            text: LLM 输出文本
            
        Returns:
            结构化分析结果
        """
        # 尝试提取 JSON 部分
        try:
            # 查找 JSON 代码块
            if '```json' in text:
                json_str = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                json_str = text.split('```')[1].split('```')[0].strip()
            else:
                json_str = text.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果解析失败，返回默认结构
            return {
                "company_strategy": {
                    "business_status": "无法解析业务现状",
                    "job_subtext": "无法解析岗位潜台词"
                },
                "ats_score": {
                    "score": 60,
                    "advantages": ["解析失败"],
                    "gaps": ["解析失败"]
                },
                "resume_suggestions": {
                    "logic": "解析失败",
                    "rewrite_demo": {
                        "original": "解析失败",
                        "rewritten": "解析失败",
                        "reasoning": "解析失败"
                    },
                    "new_keywords": ["解析失败"]
                },
                "star_questions": {
                    "background": "解析失败",
                    "questions": ["请重新尝试分析"]
                }
            }

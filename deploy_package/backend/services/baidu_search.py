"""
百度搜索服务模块
基于百度千帆 AI 搜索 API
"""
import os
import httpx
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResource:
    """搜索资源配置"""
    type: str  # web/video/image/aladdin
    top_k: int


class BaiduSearchClient:
    """百度搜索客户端"""
    
    BASE_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: 百度千帆 API Key，默认从环境变量获取
        """
        self.api_key = api_key or os.getenv("BAIDU_API_KEY")
        if not self.api_key:
            raise ValueError("BAIDU_API_KEY is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def search(
        self,
        query: str,
        edition: str = "standard",
        resource_types: Optional[List[SearchResource]] = None,
        search_recency_filter: Optional[str] = None,
        block_websites: Optional[List[str]] = None,
        safe_search: bool = False
    ) -> Dict:
        """
        执行搜索
        
        Args:
            query: 搜索关键词（最多 72 个字符）
            edition: 搜索版本，standard 或 lite
            resource_types: 资源类型过滤配置
            search_recency_filter: 时间过滤，week/month/semiyear/year
            block_websites: 屏蔽的网站列表，最多 20 个
            safe_search: 是否开启安全搜索
            
        Returns:
            API 响应结果
        """
        # 截断 query 到 72 字符（一个汉字占两个字符）
        query = self._truncate_query(query, 72)
        
        # 构建 resource_type_filter
        if resource_types is None:
            resource_types = [
                SearchResource(type="web", top_k=20),
                SearchResource(type="video", top_k=0),
                SearchResource(type="image", top_k=0),
                SearchResource(type="aladdin", top_k=0)
            ]
        
        # 构建请求体
        payload = {
            "messages": [{"role": "user", "content": query}],
            "edition": edition,
            "search_source": "baidu_search_v2",
            "resource_type_filter": [
                {"type": r.type, "top_k": r.top_k} for r in resource_types
            ],
            "safe_search": safe_search
        }
        
        # 添加可选参数
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
        if block_websites:
            payload["block_websites"] = block_websites[:20]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"[百度搜索] 原始响应: {result}")
            return result
    
    async def search_web_only(
        self,
        query: str,
        top_k: int = 20,
        recency: Optional[str] = None
    ) -> List[Dict]:
        """
        仅搜索网页
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量，最大 50
            recency: 时间过滤
            
        Returns:
            网页搜索结果列表
        """
        print(f"[百度搜索] 查询: '{query}', top_k={top_k}, recency={recency}")
        
        resource_types = [SearchResource(type="web", top_k=min(top_k, 50))]
        
        result = await self.search(
            query=query,
            resource_types=resource_types,
            search_recency_filter=recency
        )
        
        # 百度千帆 AI 搜索 API 返回格式：{'request_id': ..., 'references': [...]}
        # 或者 {'code': 0, 'message': 'success', 'data': {...}} (标准格式)
        
        if "references" in result:
            # AI 搜索格式
            references = result.get("references", [])
            print(f"[百度搜索] AI搜索返回结果数: {len(references)}")
            
            # 转换为标准格式
            search_results = []
            for ref in references:
                search_results.append({
                    "title": ref.get("title", ""),
                    "url": ref.get("url", ""),
                    "snippet": ref.get("snippet", ref.get("content", "")),
                    "source": ref.get("website", ref.get("source", "")),
                    "publish_time": ref.get("date", "")
                })
            return search_results
            
        elif result.get("code") == 0:
            # 标准格式
            search_results = result.get("data", {}).get("search_results", [])
            print(f"[百度搜索] 标准格式返回结果数: {len(search_results)}")
            return search_results
        else:
            error_msg = result.get('message', 'Unknown error')
            print(f"[百度搜索] 错误: {error_msg}, 完整响应: {result}")
            raise Exception(f"Search failed: {error_msg}")
    
    def _truncate_query(self, query: str, max_bytes: int) -> str:
        """
        截断字符串到指定字节数（UTF-8 编码）
        
        Args:
            query: 原始查询字符串
            max_bytes: 最大字节数
            
        Returns:
            截断后的字符串
        """
        encoded = query.encode('utf-8')
        if len(encoded) <= max_bytes:
            return query
        
        # 逐步截断直到符合长度要求
        while len(encoded) > max_bytes:
            query = query[:-1]
            encoded = query.encode('utf-8')
        return query
    
    def format_results(self, results: List[Dict]) -> str:
        """
        格式化搜索结果为文本
        
        Args:
            results: 搜索结果列表
            
        Returns:
            格式化后的文本
        """
        formatted = []
        for item in results:
            formatted.append(
                f"标题: {item.get('title', '')}\n"
                f"链接: {item.get('url', '')}\n"
                f"摘要: {item.get('snippet', '')}\n"
                f"来源: {item.get('source', '')}"
            )
        return "\n\n---\n\n".join(formatted)


async def generate_search_keywords(
    client: BaiduSearchClient,
    company: str,
    job_name: str,
    jd: str,
    city: str
) -> Dict[str, List[Dict]]:
    """
    生成三组搜索关键词并执行搜索
    
    Returns:
        {
            "strategy": [...],  # 战略财务类
            "business": [...],  # 业务变动类
            "review": [...]     # 员工口碑类
        }
    """
    # 构建搜索词（注意长度限制 72 字符）
    queries = {
        "strategy": f"{company} 2024 财报 战略布局 营收重点",
        "business": f"{company} 2024 组织架构调整 高管变动",
        "review": f"{company} {job_name} 加班 面试 职场氛围"
    }
    
    # 执行批量搜索
    results = {}
    for key, query in queries.items():
        try:
            result = await client.search(
                query=query,
                resource_types=[SearchResource(type="web", top_k=10)],
                search_recency_filter="year"  # 最近一年
            )
            if result.get("code") == 0:
                results[key] = result.get("data", {}).get("search_results", [])
            else:
                results[key] = []
        except Exception as e:
            print(f"Search failed for {key}: {e}")
            results[key] = []
    
    return results


def format_search_results_for_llm(results: Dict[str, List[Dict]]) -> str:
    """
    将搜索结果格式化为 LLM 可用的文本
    
    Args:
        results: 分类搜索结果
        
    Returns:
        格式化文本
    """
    sections = []
    
    category_names = {
        "strategy": "战略与财务",
        "business": "业务与变动",
        "review": "口碑与避雷"
    }
    
    for category, items in results.items():
        if not items:
            continue
        
        section = [f"## {category_names.get(category, category)}"]
        
        for i, item in enumerate(items[:5], 1):  # 每类取前 5 条
            section.append(
                f"{i}. {item.get('title', '')}\n"
                f"   来源: {item.get('source', '')}\n"
                f"   摘要: {item.get('snippet', '')}"
            )
        
        sections.append("\n".join(section))
    
    return "\n\n".join(sections)

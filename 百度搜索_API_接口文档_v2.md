# 百度搜索 API 接口文档

> 本文档用于指导 Kimi Code 集成百度搜索功能  
> 官方文档：https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy

---

## 1. 接口概述

### 1.1 服务说明
百度搜索 API 是百度千帆平台提供的搜索服务接口，支持通过 API 方式调用百度搜索能力，获取网页、视频、图片等多模态搜索结果。

### 1.2 接入方式
| 项目 | 说明 |
|------|------|
| 接入协议 | HTTPS |
| 请求方式 | POST |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

### 1.3 接口地址
```
POST https://qianfan.baidubce.com/v2/ai_search/web_search
```

---

## 2. 认证方式

### 2.1 请求签名
在请求头中携带 API Key：

```http
Authorization: Bearer <API Key>
Content-Type: application/json
```

---

## 3. 请求参数

### 3.1 Header 参数

除公共头域外，无其它特殊头域。

| 参数名 | 数据类型 | 是否必须 | 描述 |
|--------|----------|----------|------|
| Authorization | string | 必须 | 请求签名，格式：`Bearer <API Key>` |
| Content-Type | string | 必须 | 固定值：`application/json` |

### 3.2 Body 参数

| 参数名 | 数据类型 | 是否必须 | 描述 |
|--------|----------|----------|------|
| messages | array<Message> | 必须 | 搜索输入；仅支持单轮输入，若传入多轮输入，则以最后的 content 为输入查询 |
| edition | string | 非必须 | 搜索版本。默认：`standard`。可选值：`standard`（完整版本）、`lite`（标准版本，时延更好，效果略弱） |
| search_source | string | 非必须 | 使用的搜索引擎版本。固定值：`baidu_search_v2` |
| resource_type_filter | array<SearchResource> | 非必须 | 支持设置网页、视频、图片、阿拉丁搜索模态。默认：`[{"type": "web","top_k": 20},{"type": "video","top_k": 0},{"type": "image","top_k": 0},{"type": "aladdin","top_k": 0}]` |
| search_filter | SearchFilter | 非必须 | 根据子条件做检索过滤 |
| block_websites | array<string> | 非必须 | 不检索该名单的网页、视频等结果。支持最多 20 个站点。示例：`["tieba.baidu.com"]` |
| safe_search | boolean | 非必须 | 是否开启安全搜索，默认 `false`。开启后采用更严格的风控策略 |
| search_recency_filter | string | 非必须 | 根据网页发布时间筛选。枚举值：`week`（最近 7 天）、`month`（最近 30 天）、`semiyear`（最近 180 天）、`year`（最近 365 天） |
| config_id | string | 非必须 | query 干预配置项的配置 ID，默认为空 |

### 3.3 Message 对象

| 参数名 | 数据类型 | 是否必须 | 描述 |
|--------|----------|----------|------|
| role | string | 必须 | 角色设定。可选值：`user`（用户）、`assistant`（模型） |
| content | string | 必须 | 对话内容，即用户的 query 问题。不能为空，长度限制 72 个字符（一个汉字占两个字符），过长时只取前 72 个字符检索 |

### 3.4 SearchResource 对象

| 参数名 | 数据类型 | 是否必须 | 描述 |
|--------|----------|----------|------|
| type | string | 必须 | 搜索资源类型。可选值：`web`（网页）、`video`（视频）、`image`（图片）、`aladdin`（阿拉丁） |
| top_k | int | 必须 | 指定模态最大返回个数。网页最大 50，视频最大 10，图片最大 30，阿拉丁最大 5 |

---

## 4. 响应参数

### 4.1 响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "search_results": [...],
    "answer": "..."
  }
}
```

### 4.2 响应字段说明

| 参数名 | 数据类型 | 描述 |
|--------|----------|------|
| code | int | 错误码，0 表示成功 |
| message | string | 错误信息 |
| data | object | 搜索结果数据 |
| data.search_results | array | 搜索结果列表 |
| data.answer | string | AI 总结的回答（如有） |

### 4.3 搜索结果对象

| 参数名 | 数据类型 | 描述 |
|--------|----------|------|
| title | string | 搜索结果标题 |
| url | string | 搜索结果链接 |
| snippet | string | 搜索结果摘要 |
| source | string | 来源网站 |
| publish_time | string | 发布时间 |
| type | string | 资源类型：`web`/`video`/`image`/`aladdin` |

---

## 5. 请求示例

### 5.1 基础搜索

```bash
curl -X POST https://qianfan.baidubce.com/v2/ai_search/web_search \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "美团 2024 财报 优选业务"
      }
    ],
    "edition": "standard",
    "search_source": "baidu_search_v2",
    "resource_type_filter": [
      {"type": "web", "top_k": 20},
      {"type": "video", "top_k": 0},
      {"type": "image", "top_k": 0},
      {"type": "aladdin", "top_k": 0}
    ]
  }'
```

### 5.2 带过滤条件的搜索

```bash
curl -X POST https://qianfan.baidubce.com/v2/ai_search/web_search \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "美团 组织架构调整"
      }
    ],
    "edition": "standard",
    "search_source": "baidu_search_v2",
    "resource_type_filter": [
      {"type": "web", "top_k": 10}
    ],
    "search_recency_filter": "month",
    "block_websites": ["tieba.baidu.com"],
    "safe_search": true
  }'
```

---

## 6. Python 实现代码

### 6.1 同步版本

```python
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SearchResource:
    """搜索资源配置"""
    type: str  # web/video/image/aladdin
    top_k: int


@dataclass
class Message:
    """消息对象"""
    role: str = "user"  # user/assistant
    content: str = ""


class BaiduSearchClient:
    """百度搜索客户端"""
    
    BASE_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    
    def __init__(self, api_key: str):
        """
        初始化客户端
        
        Args:
            api_key: 百度千帆 API Key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def search(
        self,
        query: str,
        edition: str = "standard",
        resource_types: Optional[List[SearchResource]] = None,
        search_recency_filter: Optional[str] = None,
        block_websites: Optional[List[str]] = None,
        safe_search: bool = False,
        config_id: Optional[str] = None
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
            config_id: query 干预配置 ID
            
        Returns:
            API 响应结果
        """
        # 截断 query 到 72 字符
        query = query[:72] if len(query) > 72 else query
        
        # 构建 messages
        messages = [Message(role="user", content=query)]
        
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
            "messages": [{"role": m.role, "content": m.content} for m in messages],
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
            payload["block_websites"] = block_websites[:20]  # 最多 20 个
        if config_id:
            payload["config_id"] = config_id
        
        response = requests.post(
            self.BASE_URL,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def search_web_only(
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
        resource_types = [SearchResource(type="web", top_k=min(top_k, 50))]
        
        result = self.search(
            query=query,
            resource_types=resource_types,
            search_recency_filter=recency
        )
        
        if result.get("code") == 0:
            return result.get("data", {}).get("search_results", [])
        else:
            raise Exception(f"Search failed: {result.get('message')}")
    
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


# 使用示例
if __name__ == "__main__":
    client = BaiduSearchClient(api_key="your_api_key")
    
    # 基础搜索
    result = client.search_web_only("美团 2024 财报 优选业务", top_k=10)
    print(client.format_results(result))
```

### 6.2 异步版本

```python
import aiohttp
import asyncio
from typing import List, Dict, Optional


class AsyncBaiduSearchClient:
    """异步百度搜索客户端"""
    
    BASE_URL = "https://qianfan.baidubce.com/v2/ai_search/web_search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search(
        self,
        query: str,
        edition: str = "standard",
        resource_types: Optional[List[Dict]] = None,
        search_recency_filter: Optional[str] = None,
        block_websites: Optional[List[str]] = None,
        safe_search: bool = False
    ) -> Dict:
        """异步搜索"""
        query = query[:72] if len(query) > 72 else query
        
        if resource_types is None:
            resource_types = [
                {"type": "web", "top_k": 20},
                {"type": "video", "top_k": 0},
                {"type": "image", "top_k": 0},
                {"type": "aladdin", "top_k": 0}
            ]
        
        payload = {
            "messages": [{"role": "user", "content": query}],
            "edition": edition,
            "search_source": "baidu_search_v2",
            "resource_type_filter": resource_types,
            "safe_search": safe_search
        }
        
        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter
        if block_websites:
            payload["block_websites"] = block_websites[:20]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return await response.json()
    
    async def batch_search(
        self,
        queries: List[str],
        **kwargs
    ) -> List[Dict]:
        """
        批量搜索
        
        Args:
            queries: 搜索关键词列表
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        tasks = [self.search(q, **kwargs) for q in queries]
        return await asyncio.gather(*tasks)


# 使用示例
async def main():
    client = AsyncBaiduSearchClient(api_key="your_api_key")
    
    # 批量搜索
    queries = [
        "美团 2024 财报 优选业务",
        "美团 组织架构调整 2024",
        "美团 产品经理 面试"
    ]
    
    results = await client.batch_search(queries)
    
    for query, result in zip(queries, results):
        print(f"\n搜索: {query}")
        if result.get("code") == 0:
            count = len(result.get("data", {}).get("search_results", []))
            print(f"结果数: {count}")
        else:
            print(f"错误: {result.get('message')}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 7. AI 面试助手集成

### 7.1 生成三组搜索关键词

```python
async def generate_search_keywords(
    client: AsyncBaiduSearchClient,
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
        result = await client.search(
            query=query,
            resource_types=[{"type": "web", "top_k": 10}],
            search_recency_filter="year"  # 最近一年
        )
        if result.get("code") == 0:
            results[key] = result.get("data", {}).get("search_results", [])
        else:
            results[key] = []
    
    return results
```

### 7.2 格式化搜索结果供 LLM 使用

```python
def format_search_results_for_llm(results: Dict[str, List[Dict]]) -> str:
    """
    将搜索结果格式化为 LLM 可用的文本
    
    Args:
        results: 分类搜索结果
        
    Returns:
        格式化文本
    """
    sections = []
    
    for category, items in results.items():
        if not items:
            continue
            
        category_names = {
            "strategy": "战略与财务",
            "business": "业务与变动",
            "review": "口碑与避雷"
        }
        
        section = [f"## {category_names.get(category, category)}"]
        
        for i, item in enumerate(items[:5], 1):  # 每类取前 5 条
            section.append(
                f"{i}. {item.get('title', '')}\n"
                f"   来源: {item.get('source', '')}\n"
                f"   摘要: {item.get('snippet', '')}"
            )
        
        sections.append("\n".join(section))
    
    return "\n\n".join(sections)
```

---

## 8. 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 1 | 系统错误 | 稍后重试 |
| 2 | 参数错误 | 检查请求参数格式 |
| 3 | 无权限访问 | 检查 API Key 是否有效 |
| 4 | 访问频率受限 | 降低请求频率，实现退避重试 |
| 6 | 无数据返回 | 更换搜索关键词 |
| 17 | 请求量超限 | 检查套餐配额 |
| 18 | 服务不可用 | 联系百度客服 |
| 100 | 无效的 API Key | 检查 API Key 配置 |

---

## 9. 注意事项

### 9.1 长度限制
- `content` 字段最多 72 个字符（一个汉字占两个字符）
- `block_websites` 最多 20 个站点

### 9.2 资源类型限制
- 网页 (`web`): top_k 最大 50
- 视频 (`video`): top_k 最大 10
- 图片 (`image`): top_k 最大 30
- 阿拉丁 (`aladdin`): top_k 最大 5

### 9.3 阿拉丁使用注意
1. 不支持站点、时效过滤
2. 建议搭配网页模态使用
3. 返回参数为 beta 版本，后续可能变更

### 9.4 最佳实践
1. **关键词精简**: 由于 72 字符限制，搜索词应精简明确
2. **时间过滤**: 使用 `search_recency_filter` 获取最新信息
3. **安全搜索**: 对敏感场景开启 `safe_search`
4. **错误处理**: 对常见错误码实现针对性处理

---

## 10. 配置示例

### 10.1 环境变量
```bash
BAIDU_API_KEY=your_api_key_here
```

### 10.2 配置文件 (config.yaml)
```yaml
baidu_search:
  api_key: "${BAIDU_API_KEY}"
  default_edition: "standard"
  default_top_k: 20
  timeout: 30
  retry_times: 3
```

---

## 11. 相关链接

- [百度千帆官网](https://cloud.baidu.com/product-s/qianfan_home)
- [百度搜索 API 官方文档](https://cloud.baidu.com/doc/qianfan/s/2mh4su4uy)
- [获取 API Key](https://console.bce.baidu.com/qianfan/ais/console/applicationConsole)

---

*文档版本: v1.0*  
*创建日期: 2026-03-17*  
*作者: AI 智能面试助手开发团队*

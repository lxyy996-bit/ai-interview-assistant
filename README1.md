        # AI 智能面试助手

基于 STAR 法则的面试准备系统，帮助求职者分析简历、生成面试题、提供优化建议。

## 功能特性

- 📄 **简历上传**：支持 PDF/DOCX 格式简历上传
- 🔍 **智能分析**：AI 分析简历与岗位匹配度
- 💡 **优化建议**：提供简历改写建议和关键词推荐
- ❓ **面试题库**：基于 STAR 法则生成个性化面试题
- 📊 **ATS 评分**：评估简历通过 ATS 系统的概率

## 技术栈

### 前端
- React 18 + TypeScript
- Tailwind CSS
- React Router
- Lucide React (图标)

### 后端
- FastAPI (Python)
- Uvicorn (ASGI 服务器)

## 项目结构

```
ai-interview-assistant/
├── frontend/          # 前端项目
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   ├── types/         # TypeScript 类型
│   │   └── utils/         # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
└── backend/           # 后端项目
    ├── main.py        # FastAPI 入口
    └── requirements.txt
```

## 启动方式

### 前端
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:3000

### 后端
```bash
cd backend
pip install -r requirements.txt
python main.py
```
API 地址 http://localhost:8000

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/sessions` | POST | 创建面试会话 |
| `/api/v1/sessions/{id}` | GET | 获取会话信息 |
| `/api/v1/sessions/{id}/resume` | POST | 上传简历 |
| `/api/v1/sessions/{id}/analysis` | POST | 分析简历 |
| `/api/v1/sessions/{id}/result` | GET | 获取分析结果 |

## License

MIT

# NGA - Next Generation Analytics

NGA (Next Generation Analytics) 是一个强大的数据分析平台，通过自然语言处理技术，让用户能够以对话的方式对各类数据源进行深度分析和洞察。基于Dify平台进行了大量定制化开发，为用户提供了更专业、更灵活的数据分析解决方案。

## 项目特点

- 自然语言驱动的数据分析
- 多数据源集成支持
- 智能数据洞察
- 可视化分析结果
- 自定义分析流程

## 项目结构

```
.
├── frontend/          # React前端应用
└── backend/           # FastAPI后端服务
```
后端依赖项目： https://github.com/new-bakery/nga-dify

## 技术栈

### 前端
- React 18
- Vite
- React Router DOM
- Axios
- React Flow
- Recharts
- React Markdown
- 其他UI组件库

### 后端
- FastAPI
- SQLAlchemy
- Celery
- Redis
- PostgreSQL
- MongoDB
- LLM API集成
- Dify平台集成

## 功能特性

- 自然语言数据查询
- 多数据源连接和管理
- 智能数据分析洞察
- 自定义分析流程
- 数据可视化展示
- 用户认证和授权
- 异步任务处理
- 数据库集成

## 开始使用

### 前置要求

- Node.js 18+
- Python 3.8+
- PostgreSQL
- Redis
- MongoDB
- Dify平台账号

### 安装步骤

1. 克隆仓库
```bash
git clone [repository-url]
cd nga
```

2. 前端设置
```bash
cd frontend
npm install
npm run dev
```

3. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

4. 环境配置
- 复制 `.env.example` 到 `.env`
- 填写必要的环境变量（数据库连接、API密钥、Dify配置等）

5. 启动服务
```bash
# 启动后端服务
uvicorn main:app --reload

# 启动Celery worker
celery -A worker worker --loglevel=info
```

## 开发指南

### 代码规范
- 前端使用ESLint进行代码检查
- 后端遵循PEP 8规范
- 使用TypeScript进行类型检查

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

## API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 部署

### 生产环境配置
1. 设置环境变量
2. 构建前端
```bash
cd frontend
npm run build
```
3. 配置Nginx
4. 使用Gunicorn运行后端
5. 设置数据库迁移

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

This project uses a **Modified Apache License 2.0**.

You are free to use, modify, and distribute this code **for non-commercial purposes only** under the terms of the Apache 2.0 License, with an added restriction that **commercial use is prohibited** without a separate license agreement.

📧 For commercial licensing, please contact: hong.zheng@newbakery.net / eric.liu@newbakery.net
🔗 Original Apache License: http://www.apache.org/licenses/LICENSE-2.0

## 作者

- Hong Zheng (hong.zheng@newbakery.net)
- Eric Liu (eric.liu@newbakery.net)

## 致谢

本项目基于 [Dify](https://github.com/langgenius/dify) 平台进行了大量定制化开发，感谢Dify团队提供的优秀开源项目。 

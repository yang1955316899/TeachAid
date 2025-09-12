# TeachAid 后端框架 - 快速启动指南

## 项目概述

TeachAid是一个基于大语言模型的AI辅助教学平台，通过多模态AI技术提升教培机构的教学效率。

### 核心特色

- 🤖 **统一AI框架**：LiteLLM整合100+大语言模型，智能路由和故障转移
- 🔄 **工作流编排**：LangGraph处理复杂多步骤AI工作流
- 📊 **多模态理解**：支持图片、PDF、文本等多种格式题目解析
- 💡 **智能改写**：将标准答案转换为引导式教学内容
- 💬 **学习对话**：为学生提供个性化AI答疑和学习引导
- 📈 **数据分析**：学习轨迹跟踪和薄弱点分析

### 技术架构

- **后端框架**：FastAPI + Python 3.11+
- **数据库**：MySQL 8.0 + Redis 7
- **AI框架**：LiteLLM + LangGraph + LangSmith
- **认证**：JWT + FastAPI-Users
- **部署**：Docker + Docker Compose

## 环境要求

- Python 3.11+
- MySQL 8.0+
- Redis 7+
- Docker (可选)
- uv (Python包管理器)

## 快速启动

### 方法一：使用uv开发环境

1. **安装uv**
   ```bash
   # Windows
   pip install uv
   
   # 或使用pip
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **克隆项目并安装依赖**
   ```bash
   cd TeachAid
   uv sync --python 3.11 --all-extras
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，配置数据库连接和AI API密钥
   ```

4. **启动数据库服务**
   ```bash
   # 使用Docker快速启动数据库
   docker-compose up -d db redis
   ```

5. **初始化数据库**
   ```bash
   # 创建迁移文件
   uv run alembic revision --autogenerate -m "Initial migration"
   
   # 执行迁移
   uv run alembic upgrade head
   ```

6. **启动应用**
   ```bash
   uv run python run.py
   ```

### 方法二：Docker一键启动

1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，设置AI API密钥
   ```

2. **启动所有服务**
   ```bash
   docker-compose up -d
   ```

3. **查看服务状态**
   ```bash
   docker-compose ps
   docker-compose logs app
   ```

## 环境变量配置

重要的环境变量：

```env
# 基本配置
DEBUG=true
HOST=0.0.0.0
PORT=50002

# 数据库
DATABASE_URL=mysql+aiomysql://root:root@localhost:3306/teachaid
REDIS_URL=redis://localhost:6379/0

# JWT密钥（生产环境必须修改）
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# AI模型API密钥
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
QWEN_API_KEY=your-qwen-api-key
YI_API_KEY=your-yi-api-key

# LangSmith（可选）
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key
```

## 验证安装

启动成功后，访问以下地址：

- **API文档**：http://localhost:50002/docs
- **健康检查**：http://localhost:50002/health
- **系统信息**：http://localhost:50002/

## API接口概览

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新令牌
- `GET /api/auth/profile` - 获取用户信息

### 题目管理
- `POST /api/questions/upload` - 上传题目文件
- `GET /api/questions/upload/{file_id}/status` - 查看处理状态
- `GET /api/questions` - 获取题目列表
- `POST /api/questions` - 创建题目
- `PUT /api/questions/{id}/rewrite` - AI改写答案

## 开发指南

### 项目结构

```
TeachAid/
├── app/                    # 应用主目录
│   ├── core/              # 核心配置
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── unified_ai_framework.py  # AI框架
│   ├── models/            # 数据模型
│   │   ├── database_models.py      # SQLAlchemy模型
│   │   └── pydantic_models.py      # API模型
│   ├── services/          # 业务服务
│   │   ├── auth_service.py         # 认证服务
│   │   └── file_processor.py       # 文件处理
│   ├── api/               # API路由
│   │   ├── auth.py        # 认证接口
│   │   └── questions.py   # 题目接口
│   └── main.py            # 应用入口
├── alembic/               # 数据库迁移
├── uploads/               # 文件上传目录
├── logs/                  # 日志目录
├── pyproject.toml         # uv项目配置
├── requirements.txt       # pip依赖
├── docker-compose.yml     # Docker编排
└── Dockerfile            # Docker镜像
```

### 添加新功能

1. **数据模型**：在 `app/models/database_models.py` 中定义
2. **API模型**：在 `app/models/pydantic_models.py` 中定义
3. **业务逻辑**：在 `app/services/` 中实现
4. **API接口**：在 `app/api/` 中定义路由
5. **注册路由**：在 `app/main.py` 中注册

### 数据库迁移

```bash
# 创建迁移
uv run alembic revision --autogenerate -m "Add new table"

# 执行迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

### 测试

```bash
# 运行测试
uv run pytest

# 代码格式化
uv run black .
uv run isort .

# 代码检查
uv run flake8 .
```

## 生产部署

### 环境准备

1. 服务器配置：4核8G内存，50G存储
2. MySQL数据库
3. Redis缓存
4. Nginx反向代理
5. SSL证书

### 部署步骤

1. **克隆代码**
   ```bash
   git clone <repository>
   cd TeachAid
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 设置生产环境配置
   ```

3. **启动服务**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **配置Nginx**
   ```nginx
   server {
       listen 80;
       server_name teachaid.com;
       
       location /api/ {
           proxy_pass http://127.0.0.1:50002/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 常见问题

### 1. 数据库连接失败
检查MySQL服务状态和连接配置

### 2. AI API调用失败
确认API密钥配置正确，网络连接正常

### 3. 文件上传处理慢
检查AI服务响应时间，考虑使用更快的模型

### 4. 权限错误
确认用户角色和权限配置

## 技术支持

- **文档**: 查看README.md了解详细功能设计
- **Issues**: 项目GitHub Issues页面
- **讨论**: GitHub Discussions

## 许可证

MIT License - 详见LICENSE文件

---

🎉 **祝您使用愉快！TeachAid助力教育事业！**
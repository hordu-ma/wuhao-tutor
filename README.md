# 五好伴学 (wuhao-tutor)

基于阿里云百炼智能体的K12学情管理系统

## 🎯 项目概述

**项目名称**: 五好伴学  
**英文名称**: wuhao-tutor  
**版本**: 0.1.0  
**项目类型**: 基于阿里云百炼智能体的K12学情管理系统  
**技术栈**: Python + FastAPI + PostgreSQL + Redis + 阿里云百炼 + Vue3 + 微信小程序  

### 核心功能

- 🎯 **智能作业批改** - 基于百炼智能体的自动批改和分析
- 📊 **个性化学情分析** - 智能识别知识薄弱点和学习模式
- 🔄 **智能学习问答** - 基于学情数据的个性化AI交互助教
- 🤖 **统一AI服务** - 所有AI功能通过百炼智能体统一提供

## 🚀 快速开始

### 环境要求

- **Python**: >= 3.11
- **Node.js**: >= 18.0 (前端开发)
- **PostgreSQL**: >= 14 (生产环境)
- **Redis**: >= 6.0
- **阿里云账号**: 用于百炼智能体访问

### 1. 克隆项目

```bash
git clone <repository-url>
cd wuhao-tutor
```

### 2. 安装依赖

```bash
# 使用 uv 安装Python依赖
uv sync

# 激活虚拟环境（可选）
source .venv/bin/activate  # macOS/Linux
```

### 3. 环境配置

```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

**重要环境变量**:
```bash
ENVIRONMENT=development
DEBUG=true
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db

# 百炼智能体配置（可选）
BAILIAN_APPLICATION_ID=your_application_id
BAILIAN_API_KEY=sk-your_api_key

# 数据库配置（生产环境）
DATABASE_URL=postgresql+asyncpg://user:password@localhost/wuhao_tutor
REDIS_URL=redis://localhost:6379
```

### 4. 验证安装

```bash
# 运行诊断脚本
uv run python scripts/diagnose.py

# 预期输出：🟢 所有检查通过
```

### 5. 启动应用

```bash
# 开发服务器启动
uv run uvicorn src.main:app --reload

# 或者使用模块方式
uv run python -m src.main
```

访问 http://localhost:8000/docs 查看API文档

## 📋 项目状态

### ✅ 已完成功能

- **基础架构**: 100% ✅
  - FastAPI应用框架
  - SQLAlchemy 2.0异步ORM
  - Pydantic v2数据验证
  - 结构化日志系统

- **核心服务**: 100% ✅
  - 阿里云百炼智能体集成
  - 用户认证和会话管理
  - 学习问答AI助教
  - 作业批改工作流程

- **API接口**: 100% ✅
  - RESTful API设计
  - OpenAPI/Swagger文档
  - 50个路由端点
  - 完整的错误处理

- **数据管理**: 100% ✅
  - SQLite开发环境
  - PostgreSQL生产支持
  - Alembic数据库迁移
  - Redis缓存系统

- **性能和安全**: 100% ✅
  - 性能监控系统
  - 多层限流保护
  - CORS和安全头配置
  - 查询优化和缓存

### 🔄 开发中功能

- **前端界面**: 80% ✅
  - Vue 3 + TypeScript项目架构 ✅
  - 用户认证界面 ✅  
  - 作业批改界面 ✅
  - 学习问答界面 ✅
  - 学情分析界面 ⏳

## 🏗️ 项目架构

```
wuhao-tutor/
├── src/                    # 源代码目录
│   ├── api/               # API路由层
│   │   └── v1/endpoints/  # v1版本API端点
│   ├── core/              # 核心配置和工具
│   ├── models/            # SQLAlchemy数据模型  
│   ├── schemas/           # Pydantic数据模型
│   ├── services/          # 业务逻辑层
│   ├── repositories/      # 数据访问层
│   ├── utils/             # 工具模块
│   └── main.py           # 应用入口
├── scripts/               # 自动化脚本
│   └── diagnose.py       # 系统诊断脚本
├── tests/                 # 测试目录
├── frontend/              # 前端Vue3项目
├── alembic/              # 数据库迁移
├── .env                  # 环境配置
└── pyproject.toml        # 项目配置
```

## 🔧 开发工具

### 诊断脚本

运行综合诊断检查所有模块：

```bash
uv run python scripts/diagnose.py
```

检查项目包括：
- ✅ 模块导入测试
- ✅ 配置加载验证  
- ✅ FastAPI应用创建
- ✅ 数据库连接测试
- ✅ 服务初始化检查
- ✅ 数据模型验证
- ✅ Schema模型测试

### 代码质量

```bash
# 代码格式化
uv run black src/
uv run isort src/

# 类型检查
uv run mypy src/

# 运行测试
uv run pytest tests/
```

## 📚 API文档

启动应用后，访问以下端点：

- **API文档**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 主要API端点

- **认证**: `/api/v1/auth/`
  - POST `/login` - 用户登录
  - POST `/register` - 用户注册
  - POST `/refresh` - 刷新令牌

- **学习问答**: `/api/v1/learning/`
  - POST `/ask` - 向AI提问
  - GET `/sessions` - 获取会话列表
  - GET `/questions` - 问答历史

- **作业批改**: `/api/v1/homework/`
  - POST `/upload` - 上传作业
  - GET `/{id}/correct` - 获取批改结果

## 🚨 故障排除

### 常见问题

1. **配置错误**: 参考 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **导入失败**: 使用 `uv run python -m src.main` 启动
3. **数据库问题**: 检查SQLite文件权限
4. **端口占用**: 使用 `--port 8001` 指定其他端口

### 完全重置

如果遇到无法解决的问题：

```bash
# 删除虚拟环境和数据库
rm -rf .venv *.db

# 重新安装
uv sync

# 重新运行诊断
uv run python scripts/diagnose.py
```

详细故障排除指南: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`) 
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

**项目维护者**: Liguo Ma  
**邮箱**: maliguo@outlook.com  
**项目地址**: [GitHub Repository]

---

_最后更新时间: 2025-09-28_  
_项目状态: 核心功能完成，前端开发中_
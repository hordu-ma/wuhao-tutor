# 五好伴学（wuhao-tutor）开发指南

## 项目概述

**项目名称**: 五好伴学
**英文名称**: wuhao-tutor
**项目类型**: 基于阿里云百炼智能体的K12学情管理系统
**技术栈**: Python + FastAPI + PostgreSQL + Redis + 阿里云百炼 + Vue3 + 微信小程序

### 项目愿景

构建一个基于阿里云百炼智能体的学情管理平台，通过统一的AI服务帮助K12学生：

- 🎯 **智能作业批改** - 基于百炼智能体的自动批改和分析
- 📊 **个性化学情分析** - 智能识别知识薄弱点和学习模式
- 🔄 **智能学习问答** - 基于学情数据的个性化AI交互助教
- 🤖 **统一AI服务** - 所有AI功能通过百炼智能体统一提供

### 核心价值主张

- **统一AI服务** - 所有大模型调用通过阿里云百炼智能体完成
- **多模态输入支持** - 文字、语音、图像三种交互方式
- **个性化学情分析** - 基于作业批改结果的智能分析
- **简化架构设计** - 减少AI服务复杂度，提高系统稳定性

---

## 技术架构

### 整体架构设计

```
┌─────────────────── 用户层 ──────────────────┐
│     Web端(Vue3)      │    微信小程序端        │
├─────────────────── 接口层 ──────────────────┤
│              FastAPI Gateway               │
├─────────────────── 服务层 ──────────────────┤
│  用户服务  │  作业服务  │  学情服务  │ 百炼AI服务 │
├─────────────────── 数据层 ──────────────────┤
│    PostgreSQL     │      Redis缓存          │
├─────────────────── AI服务层 ────────────────┤
│          阿里云百炼智能体 "五好-伴学K12"        │
├─────────────────── 外部服务 ────────────────┤
│    微信API     │    OSS存储    │   短信服务   │
└─────────────────────────────────────────────┘
```

### 架构优化调整

#### 核心调整说明

1. **统一AI服务**: 所有AI功能（作业批改、学习问答、学情分析）统一调用百炼智能体
2. **简化服务层**: 移除多个独立的AI服务模块，整合为单一的百炼AI服务
3. **配置集中化**: 百炼智能体的配置信息统一管理
4. **接口标准化**: 统一的AI服务调用接口和响应格式

#### 分层架构详解

##### 1. 表现层 (Presentation Layer)

- **Web端**: Vue3 + TypeScript + Vite
- **小程序端**: 微信小程序原生开发
- **职责**: 用户交互、页面展示、状态管理

##### 2. API层 (API Layer)

- **框架**: FastAPI + Pydantic
- **版本管理**: `/api/v1/` 路径前缀
- **职责**: 请求路由、参数验证、响应格式化

##### 3. 业务逻辑层 (Business Logic Layer)

- **核心服务模块**:
    - 用户管理服务 (UserService)
    - 作业管理服务 (HomeworkService) - 处理作业上传、存储
    - 学情分析服务 (AnalyticsService) - 基于AI结果进行数据分析
    - 百炼AI服务 (BailianService) - 统一的AI调用服务
- **职责**: 核心业务逻辑、数据处理、AI服务调用

##### 4. 数据访问层 (Data Access Layer)

- **ORM**: SQLAlchemy 2.0+ (异步)
- **仓储模式**: Repository Pattern
- **职责**: 数据库操作、缓存管理、数据模型映射

##### 5. 数据存储层 (Data Storage Layer)

- **主数据库**: PostgreSQL (用户数据、作业数据、学情数据)
- **缓存层**: Redis (会话、临时数据、AI响应缓存)
- **文件存储**: 阿里云OSS (作业图片、音频文件)

---

## 阿里云百炼智能体集成

### 智能体配置信息

```python
# 百炼智能体配置
BAILIAN_CONFIG = {
    "name": "五好-伴学K12",
    "application_id": "db9f923dc3ae48dd9127929efa5eb108",
    "api_key": "sk-7f591a92e1cd4f4d9ed2f94761f0c1db",
    "base_url": "https://dashscope.aliyuncs.com/api/v1",
    "timeout": 30,
    "max_retries": 3
}
```

### AI服务统一接口设计

#### 1. 作业批改服务

```python
@dataclass
class HomeworkCorrectionRequest:
    """作业批改请求"""
    user_id: str
    subject: str           # 学科
    grade_level: int       # 年级
    homework_text: str     # OCR识别的题目文本
    answer_text: str       # 学生答案
    image_urls: List[str]  # 作业图片URL

@dataclass
class HomeworkCorrectionResponse:
    """作业批改响应"""
    correction_id: str
    is_correct: bool
    score: float           # 分数 (0-100)
    corrections: List[str] # 批改意见
    knowledge_points: List[str]  # 涉及知识点
    difficulty_level: str  # 难度等级
    suggestions: List[str] # 学习建议
    error_analysis: Optional[str]  # 错误分析
```

#### 2. 学习问答服务

```python
@dataclass
class StudyQARequest:
    """学习问答请求"""
    user_id: str
    question: str          # 学生问题
    context: str           # 上下文（学情数据）
    subject: str           # 学科
    grade_level: int       # 年级

@dataclass
class StudyQAResponse:
    """学习问答响应"""
    answer: str            # AI回答
    knowledge_points: List[str]  # 相关知识点
    difficulty_level: str  # 问题难度
    follow_up_questions: List[str]  # 延伸问题
    learning_resources: List[str]   # 推荐学习资源
```

#### 3. 学情分析服务

```python
@dataclass
class LearningAnalysisRequest:
    """学情分析请求"""
    user_id: str
    time_range: str        # 分析时间范围
    subjects: List[str]    # 分析学科
    analysis_type: str     # 分析类型: weekly/monthly/term

@dataclass
class LearningAnalysisResponse:
    """学情分析响应"""
    analysis_report: str   # 分析报告
    strengths: List[str]   # 优势知识点
    weaknesses: List[str]  # 薄弱知识点
    study_suggestions: List[str]  # 学习建议
    progress_trend: Dict   # 进步趋势数据
    next_review_plan: List[Dict]  # 复习计划
```

---

## 项目结构

```
wuhao-tutor/
├── src/                        # 源代码目录
│   ├── api/                    # API路由层
│   │   ├── v1/                # v1版本API
│   │   │   ├── endpoints/     # 各模块端点
│   │   │   │   ├── auth.py        # 认证相关
│   │   │   │   ├── homework.py    # 作业相关
│   │   │   │   ├── learning.py    # 学习问答
│   │   │   │   └── analytics.py   # 学情分析
│   │   │   └── dependencies/  # API依赖注入
│   │   └── __init__.py
│   ├── core/                   # 核心配置和工具
│   │   ├── config.py          # 配置管理
│   │   ├── logging.py         # 日志配置
│   │   ├── security.py        # 安全相关
│   │   └── database.py        # 数据库配置
│   ├── models/                 # SQLAlchemy数据模型
│   │   ├── user.py            # 用户模型
│   │   ├── homework.py        # 作业模型
│   │   └── analytics.py       # 学情模型
│   ├── schemas/                # Pydantic模型
│   │   ├── user.py            # 用户Schema
│   │   ├── homework.py        # 作业Schema
│   │   ├── bailian.py         # 百炼AI Schema
│   │   └── common.py          # 通用Schema
│   ├── services/               # 业务逻辑层
│   │   ├── user_service.py    # 用户管理服务
│   │   ├── homework_service.py # 作业管理服务
│   │   ├── analytics_service.py # 学情分析服务
│   │   └── bailian_service.py # 百炼AI服务 [核心]
│   ├── repositories/           # 数据访问层
│   │   ├── user_repository.py # 用户仓储
│   │   ├── homework_repository.py # 作业仓储
│   │   └── base_repository.py # 基础仓储
│   ├── utils/                  # 工具模块
│   │   ├── ocr.py             # OCR工具
│   │   ├── file_upload.py     # 文件上传工具
│   │   └── cache.py           # 缓存工具
│   └── main.py                # 应用入口
├── tests/                      # 测试目录
│   ├── unit/                  # 单元测试
│   │   └── test_bailian_service.py # 百炼服务测试
│   ├── integration/           # 集成测试
│   └── fixtures/              # 测试数据
├── scripts/                    # 自动化脚本
│   ├── init/                  # 初始化脚本
│   └── dev/                   # 开发工具脚本
├── docs/                       # 文档目录
│   ├── api/                   # API文档
│   └── bailian/               # 百炼集成文档
├── alembic/                    # 数据库迁移
├── .env.example               # 环境配置模板
├── pyproject.toml             # 项目配置
└── Makefile                   # 自动化任务
```

---

## 开发环境搭建

### 环境要求

- **Python**: >= 3.11
- **Node.js**: >= 18.0 (前端开发)
- **PostgreSQL**: >= 14
- **Redis**: >= 6.0
- **阿里云账号**: 用于百炼智能体访问

### 1. 克隆项目

```bash
git clone <repository-url>
cd wuhao-tutor
```

### 2. Python环境配置

```bash
# 使用 uv 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
```

### 3. 环境配置

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件，重点配置百炼智能体
vim .env
```

**关键环境变量**:

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost/wuhao_tutor_dev
REDIS_URL=redis://localhost:6379

# 阿里云百炼智能体配置
BAILIAN_APPLICATION_ID=db9f923dc3ae48dd9127929efa5eb108
BAILIAN_API_KEY=sk-7f591a92e1cd4f4d9ed2f94761f0c1db
BAILIAN_BASE_URL=https://dashscope.aliyuncs.com/api/v1
BAILIAN_TIMEOUT=30
BAILIAN_MAX_RETRIES=3

# 文件存储配置
OSS_BUCKET_NAME=wuhao-tutor-files
OSS_ACCESS_KEY_ID=your_access_key
OSS_ACCESS_KEY_SECRET=your_secret_key
```

### 4. 数据库初始化

```bash
# 启动PostgreSQL和Redis
brew services start postgresql
brew services start redis

# 创建数据库
createdb wuhao_tutor_dev

# 运行数据库迁移
make db-init
```

### 5. 启动开发服务器

```bash
# 启动后端服务
make dev

# 或直接使用Python
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 验证环境

访问 http://localhost:8000/docs 查看API文档

---

## 开发规范

### 代码规范

#### Python代码规范

- **格式化工具**: Black (line-length=88)
- **类型检查**: MyPy
- **代码检查**: Flake8
- **导入排序**: isort

```bash
# 代码格式化
make format

# 代码检查
make lint

# 类型检查
make type-check
```

#### 百炼AI服务调用规范

```python
# 正确的服务调用方式
from src.services.bailian_service import BailianService

class HomeworkService:
    def __init__(self):
        self.bailian_service = BailianService()

    async def correct_homework(self, request: HomeworkCorrectionRequest) -> HomeworkCorrectionResponse:
        """作业批改"""
        try:
            # 构建AI请求
            ai_prompt = self._build_correction_prompt(request)

            # 调用百炼智能体
            ai_response = await self.bailian_service.chat_completion(
                messages=[{"role": "user", "content": ai_prompt}],
                context={
                    "user_id": request.user_id,
                    "subject": request.subject,
                    "grade_level": request.grade_level
                }
            )

            # 解析AI响应
            return self._parse_correction_response(ai_response)

        except Exception as e:
            logger.error(f"作业批改失败: {e}")
            raise HomeworkCorrectionError(f"批改失败: {str(e)}")
```

### API设计规范

#### RESTful API设计

```python
# 作业相关API
POST   /api/v1/homework/upload          # 上传作业
GET    /api/v1/homework/{homework_id}   # 获取作业详情
POST   /api/v1/homework/{homework_id}/correct  # 批改作业

# 学习问答API
POST   /api/v1/learning/ask             # 学习提问
GET    /api/v1/learning/history         # 问答历史

# 学情分析API
GET    /api/v1/analytics/report         # 获取学情报告
POST   /api/v1/analytics/analyze        # 生成分析
```

#### AI服务统一响应格式

```json
// 成功响应
{
  "code": "SUCCESS",
  "message": "AI处理成功",
  "data": {
    "ai_result": {
      // 具体AI响应数据
    },
    "processing_time": 1.23,
    "tokens_used": 150
  }
}

// 错误响应
{
  "code": "AI_SERVICE_ERROR",
  "message": "百炼智能体调用失败",
  "details": {
    "error_type": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60
  }
}
```

### 提交规范

#### Git提交消息格式

```
<type>(<scope>): <description>

<body>

<footer>
```

#### 提交类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `ai`: AI服务相关调整

#### 示例

```bash
feat(bailian): 集成阿里云百炼智能体作业批改功能

- 实现统一的百炼AI服务调用
- 添加作业批改API接口
- 完善错误处理和重试机制

Closes #123
```

---

## 测试策略

### 百炼AI服务测试

#### 1. 单元测试

```python
# tests/unit/test_bailian_service.py
import pytest
from unittest.mock import AsyncMock, patch
from src.services.bailian_service import BailianService

@pytest.mark.asyncio
async def test_chat_completion_success():
    """测试百炼智能体调用成功"""
    service = BailianService()

    with patch.object(service, '_call_bailian_api') as mock_call:
        mock_call.return_value = {
            "choices": [{"message": {"content": "测试响应"}}],
            "usage": {"total_tokens": 100}
        }

        result = await service.chat_completion([
            {"role": "user", "content": "测试问题"}
        ])

        assert result.content == "测试响应"
        assert result.tokens_used == 100

@pytest.mark.asyncio
async def test_homework_correction():
    """测试作业批改功能"""
    service = BailianService()

    request = HomeworkCorrectionRequest(
        user_id="test_user",
        subject="数学",
        grade_level=8,
        homework_text="解方程: 2x + 3 = 7",
        answer_text="x = 2"
    )

    result = await service.correct_homework(request)
    assert result.is_correct == True
    assert result.score >= 0
    assert len(result.corrections) >= 0
```

#### 2. 集成测试

```python
# tests/integration/test_homework_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_homework_correction_flow(client: AsyncClient):
    """测试作业批改完整流程"""
    # 上传作业
    response = await client.post("/api/v1/homework/upload",
        files={"image": ("test.jpg", test_image_bytes, "image/jpeg")},
        data={"subject": "数学", "grade_level": 8}
    )
    assert response.status_code == 201
    homework_id = response.json()["data"]["homework_id"]

    # 批改作业
    response = await client.post(f"/api/v1/homework/{homework_id}/correct")
    assert response.status_code == 200

    result = response.json()["data"]
    assert "is_correct" in result
    assert "corrections" in result
    assert "knowledge_points" in result
```

### 测试配置

```bash
# 运行所有测试
make test

# 运行AI服务相关测试
make test-ai

# 生成覆盖率报告
make test-coverage
```

---

## 数据库设计调整

### 新增作业相关表

```sql
-- 作业记录表
CREATE TABLE homework_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    subject VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    original_images JSON,  -- 原始作业图片URLs
    ocr_text TEXT,        -- OCR识别文本
    student_answers JSON,  -- 学生答案
    ai_corrections JSON,   -- AI批改结果
    knowledge_points JSON, -- 涉及知识点
    score DECIMAL(5,2),   -- 得分
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 学习问答记录表
CREATE TABLE qa_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    context JSON,         -- 问答上下文
    knowledge_points JSON, -- 相关知识点
    satisfaction_rating INTEGER, -- 满意度评分
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI调用记录表 (用于监控和分析)
CREATE TABLE ai_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    service_type VARCHAR(50) NOT NULL, -- homework_correction, qa, analysis
    request_data JSON,
    response_data JSON,
    tokens_used INTEGER,
    processing_time DECIMAL(6,3),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 部署方案

### 容器化部署

#### Docker配置

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖 (OCR相关)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: "3.8"
services:
    web:
        build: .
        ports:
            - "8000:8000"
        environment:
            - ENVIRONMENT=production
            - BAILIAN_APPLICATION_ID=${BAILIAN_APPLICATION_ID}
            - BAILIAN_API_KEY=${BAILIAN_API_KEY}
        depends_on:
            - postgres
            - redis

    postgres:
        image: postgres:15
        environment:
            POSTGRES_DB: wuhao_tutor
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
        volumes:
            - postgres_data:/var/lib/postgresql/data

    redis:
        image: redis:7-alpine
        command: redis-server --appendonly yes
        volumes:
            - redis_data:/data

volumes:
    postgres_data:
    redis_data:
```

---

## 功能开发路线图

### 第一阶段：百炼AI服务集成 (1-2周)

- [ ] 创建百炼AI服务基础框架
- [ ] 实现统一的AI调用接口
- [ ] 完成作业批改功能集成
- [ ] 添加错误处理和重试机制
- [ ] 编写AI服务单元测试

### 第二阶段：作业管理核心功能 (2-3周)

- [ ] 作业图片上传和存储
- [ ] OCR文本识别集成
- [ ] 作业批改API实现
- [ ] 作业记录管理
- [ ] 批改结果可视化

### 第三阶段：学习问答功能 (1-2周)

- [ ] 学习问答API实现
- [ ] 上下文管理和学情关联
- [ ] 问答历史记录
- [ ] 智能推荐问题

### 第四阶段：学情分析优化 (2周)

- [ ] 基于AI分析的学情报告
- [ ] 知识点掌握度统计
- [ ] 学习进度跟踪
- [ ] 个性化学习建议

### 第五阶段：前端界面和用户体验 (2-3周)

- [ ] Web端作业上传界面
- [ ] 批改结果展示页面
- [ ] 学情分析仪表板
- [ ] 微信小程序核心功能

### 第六阶段：性能优化和部署 (1周)

- [ ] AI服务性能优化
- [ ] 缓存策略完善
- [ ] 生产环境部署
- [ ] 监控和日志完善

---

## 常见问题 FAQ

### Q: 百炼智能体调用失败如何处理？

A:

1. 检查API Key和Application ID配置
2. 确认网络连接和防火墙设置
3. 查看AI调用日志: `tail -f logs/ai_calls.log`
4. 检查配额使用情况和限制
5. 使用重试机制和降级策略

### Q: 如何优化AI服务调用性能？

A:

1. 使用Redis缓存相似请求结果
2. 实现请求批处理机制
3. 设置合理的超时时间
4. 使用异步调用避免阻塞
5. 监控Token使用量控制成本

### Q: 作业图片处理的最佳实践？

A:

1. 图片上传前进行格式和大小检查
2. 使用OSS存储，CDN加速访问
3. OCR前对图片进行预处理（去噪、矫正）
4. 缓存OCR结果避免重复识别

### Q: 如何确保AI分析结果的准确性？

A:

1. 设计合理的提示词模板
2. 对AI响应进行结构化验证
3. 建立人工审核机制
4. 收集用户反馈持续优化

---

## 监控和日志

### AI服务监控指标

```python
# 关键监控指标
AI_METRICS = {
    "call_success_rate": "AI调用成功率",
    "average_response_time": "平均响应时间",
    "tokens_usage": "Token使用量",
    "error_rate_by_type": "分类型错误率",
    "daily_costs": "每日调用成本"
}
```

### 日志配置

```python
# 百炼AI服务专用日志
LOGGING_CONFIG = {
    "loggers": {
        "bailian_service": {
            "handlers": ["ai_file"],
            "level": "INFO",
            "propagate": False
        }
    },
    "handlers": {
        "ai_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/ai_calls.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    }
}
```

---

## 联系方式

**项目维护者**: Liguo Ma
**邮箱**: maliguo@outlook.com
**项目地址**: [GitHub Repository]
**百炼智能体**: 五好-伴学K12

---

_最后更新时间: 2025-01-27_
_架构调整: 集成阿里云百炼智能体统一AI服务_

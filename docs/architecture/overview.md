# 五好伴学系统架构说明 (ARCHITECTURE)

Last Updated: 2025-10-05
版本适用范围:后端 0.1.x 开发分支(未达稳定发布)

---

## 1. 架构目标

| 目标     | 说明                               | 体现                  |
| -------- | ---------------------------------- | --------------------- |
| 可扩展性 | 支持未来接入更多学情分析与 AI 能力 | 分层 + 统一 AI 接口   |
| 可观察性 | 快速定位性能瓶颈与异常             | 监控中间件 + 限流指标 |
| 一致性   | 请求/响应、错误模型统一            | Response Wrapper      |
| 可维护   | 清晰边界、职责分离                 | Repository + Service  |
| 安全     | 内建安全头、限流、隔离             | Security Middleware   |
| 渐进演进 | 先单体 → 可切分                    | 领域模块化结构        |

---

## 2. 高层架构总览

```/dev/null/overview-diagram.txt#L1-30
 ┌──────────────────────────────────────────────────────────┐
 │                    Client / 前端 (Web / 小程序)          │
 └───────────────▲───────────────────────────────▲──────────┘
                 │                               │
          (HTTPS / REST)                   (静态资源)
                 │                               │
        ┌────────┴────────┐               ┌─────┴─────┐
        │  API Gateway /   │ (Nginx/反向代理+TLS+限流)  │
        │  Reverse Proxy   │               │  CDN(可选)│
        └────────┬────────┘               └───────────┘
                 │
        ┌────────▼─────────────────────────────────────────┐
        │                FastAPI 应用进程                   │
        │  ┌────────────────────────────────────────────┐  │
        │  │ Routing / Dependency Injection             │  │
        │  ├────────────────────────────────────────────┤  │
        │  │     API Layer (Pydantic Schemas)           │  │
        │  ├────────────────────────────────────────────┤  │
        │  │     Service Layer (业务逻辑/聚合)           │  │
        │  ├────────────────────────────────────────────┤  │
        │  │ Repository Layer (通用CRUD + 业务查询)      │  │
        │  ├────────────────────────────────────────────┤  │
        │  │ Infrastructure (监控/限流/安全/缓存)        │  │
        │  └────────────────────────────────────────────┘  │
        └────────┬───────────────────────┬────────────────┘
                 │                       │
        ┌────────▼────────┐    ┌────────▼─────────┐
        │ PostgreSQL       │    │ Redis (缓存/速率) │
        └────────┬────────┘    └────────┬─────────┘
                 │                       │
            ┌────▼────┐          ┌──────▼──────┐
            │ 文件存储 │(本地/OSS) │ 外部 AI (百炼) │
            └─────────┘          └─────────────┘
```

---

## 3. 分层职责 (Layered Responsibility)

| 层            | 主要文件/目录            | 职责                                     | 不应做的事                       |
| ------------- | ------------------------ | ---------------------------------------- | -------------------------------- |
| API 层        | `src/api/v1/endpoints/*` | 路由、请求验证、调用服务                 | 复杂业务判断 / 原生 SQL          |
| Schema 层     | `src/schemas/`           | 数据结构约束、序列化                     | 调用数据库                       |
| Service 层    | `src/services/`          | 业务组合 / 事务协调 / 流程控制           | 直接拼接 SQL / 直接返回 ORM 对象 |
| Repository 层 | `src/repositories/`      | 通用 CRUD、复杂查询封装                  | 写业务流程                       |
| Model 层      | `src/models/`            | ORM 实体定义                             | 含业务逻辑                       |
| Core/Infra    | `src/core/`              | 配置、数据库、监控、限流、安全、性能分析 | 领域逻辑                         |
| Utils         | `src/utils/`             | 通用工具、格式/ID生成                    | 跨上下文副作用                   |

---

## 4. 关键组件说明

| 组件        | 位置                                      | 核心点                          | 演进方向                 |
| ----------- | ----------------------------------------- | ------------------------------- | ------------------------ |
| 配置系统    | `src/core/config.py`                      | Pydantic Settings + 环境隔离    | 引入远程配置中心（可选） |
| 数据库      | `src/core/database.py`                    | Async SQLAlchemy + Session 工厂 | 连接池指标外显           |
| 仓储        | `src/repositories/base_repository.py`     | 泛型 + 异步 CRUD                | 增加缓存装饰器           |
| 学习仓储    | `src/repositories/learning_repository.py` | 统计 + 复杂查询                 | 引入查询缓存与物化视图   |
| 监控        | `src/core/monitoring.py`                  | 请求耗时、分位数、慢端点        | Prometheus Export        |
| 限流        | `src/core/security.py`                    | 令牌桶 + 滑动窗口               | 分布式令牌桶（Redis）    |
| 性能        | `src/core/performance.py`                 | Query 监听 + 缓存结构           | 自适应缓存策略           |
| AI 服务封装 | `src/services/bailian_service.py`         | 统一调用入口                    | 多模型策略路由           |
| 部署脚本    | `scripts/deploy.py`                       | 构建/启动/健康检查              | CI/CD 管道               |
| 备份        | `scripts/db_backup.py`                    | PostgreSQL 备份/轮换            | 加增量差异策略           |

---

## 5. 典型请求处理流

```/dev/null/request-flow.txt#L1-40
[客户端请求]
   ↓  (HTTPS/Nginx: TLS终止 + 基础限流 + 安全头补充)
[FastAPI 路由匹配]
   ↓  (Pydantic 解析 / 校验)
[API Endpoint 函数]
   ↓  调用
[Service 层(组合/校验/策略)]
   ↓  调用
[Repository 层 / 查询组装]
   ↓  (SQLAlchemy 异步执行)
[数据库返回 ORM 实体]
   ↓  (Service 转换为 Schema)
[响应包装 { success, data }]
   ↓  (中间件附加监控 / 安全头 / 限流标记)
→ 返回客户端
```

---

## 6. 关键中间件链路（自外向内）

| 顺序 | 中间件         | 功能                       |
| ---- | -------------- | -------------------------- |
| 1    | 性能监控       | 统计请求耗时、路径聚合     |
| 2    | 安全头         | 注入 CSP / HSTS 等         |
| 3    | 限流控制       | IP / 用户 / AI / 登录流控  |
| 4    | CORS           | 允许跨域（受控）           |
| 5    | Trusted Host   | 主机名白名单（测试可跳过） |
| 6    | 日志（如使用） | 请求/响应概要              |
| 7    | FastAPI 内部   | 路由调度/依赖注入          |

---

## 7. 数据模型核心实体 (逻辑视角)

| 实体                | 目的         | 关键字段（示意）                            |
| ------------------- | ------------ | ------------------------------------------- |
| User                | 用户身份     | id / username / role / created_at           |
| HomeworkTemplate    | 作业模板     | id / subject / criteria / max_score         |
| HomeworkSubmission  | 用户提交     | id / template_id / status / file_url        |
| HomeworkCorrection  | 批改结果     | submission_id / total_score / feedback[]    |
| ChatSession         | 问答会话     | id / user_id / status / topic               |
| Question            | 提问         | id / session_id / content / created_at      |
| Answer              | 回答         | id / question_id / answer_text / confidence |
| LearningStat (规划) | 学习统计聚合 | user_id / window / metrics(JSON)            |

> 详细结构迁移至：`api/models.md`（迁移后维护单一来源）

---

## 8. AI 集成策略

| 方面       | 当前实现               | 后续演进                      |
| ---------- | ---------------------- | ----------------------------- |
| 调用模式   | 单一智能体封装（同步） | 增加异步批处理 / 重试策略     |
| 超时控制   | 基础超时配置           | 自适应超时 (基于历史耗时分位) |
| 回退策略   | 暂不启用               | 失败回退到"简化模板"          |
| 上下文管理 | Phase 4-5: MCP 精确查询 | Phase 6: 引入 RAG 向量检索 |
| 成本控制   | 未统计 tokens          | 监控 + 阈值告警               |

### 8.1 上下文构建策略 (MCP + RAG 混合)

**设计理念**：两阶段演进策略，先精确后语义，先简单后复杂。

#### Phase 4-5: MCP 上下文服务 (当前阶段)

**核心目标**：基于精确 SQL 查询构建学情画像，为 AI 对话提供个性化上下文。

**关键能力**：
- **薄弱知识点查询** - 基于错误率 + 时间衰减算法
- **学习偏好分析** - 答题时间分布、学科偏好统计
- **最近错题统计** - 近 7 天/30 天错题聚合
- **知识点掌握度评估** - 综合正确率、答题数、时间衰减的多维评分
- **学习路径推荐** - 基于知识图谱的前置/后续知识点推荐

**数据来源**：
```python
# MCP 查询示例
context = {
    "weak_points": await repo.get_weak_knowledge_points(user_id, top_k=5),
    "recent_errors": await repo.get_recent_errors(user_id, days=7),
    "mastery_scores": await repo.calculate_mastery_scores(user_id),
    "learning_preferences": await repo.analyze_learning_patterns(user_id),
    "knowledge_graph": await repo.get_related_knowledge_nodes(weak_points)
}
```

**优势**：
- ✅ 精确可控，查询逻辑透明
- ✅ 无需向量化，开发成本低
- ✅ 数据库原生支持，性能可预测
- ✅ 易于调试和优化

**局限**：
- ⚠️ 无法处理语义相似的问题
- ⚠️ 需要预定义查询维度
- ⚠️ 跨知识点的语义关联能力弱

---

#### Phase 6: RAG 语义检索增强 (计划中)

**触发条件**：当用户历史数据达到一定规模(> 100条问答记录)，且 MCP 上下文效果出现瓶颈时启动。

**技术架构**：
```
用户提问 → Embedding(通义千问 API) → 向量化
                                    ↓
    PGVector 相似度检索 ← 历史问答/错题向量库
                                    ↓
    Top-K 相似内容 + MCP 精确数据 → 混合上下文
                                    ↓
                  AI 模型生成个性化回答
```

**核心能力**：
- **相似错题语义检索** - 找到语义相似但表述不同的历史错题
- **历史问答语义检索** - 检索过往相似问题的高质量回答
- **知识点语义聚类** - 自动发现隐含的知识点关联
- **个性化学习路径** - 基于语义相似度的智能推荐

**实现方案**：
```sql
-- PGVector 扩展安装
CREATE EXTENSION IF NOT EXISTS vector;

-- 向量表结构
CREATE TABLE question_embeddings (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    embedding vector(1536),  -- 通义千问 Embedding 维度
    created_at TIMESTAMP DEFAULT NOW()
);

-- 相似度检索索引
CREATE INDEX ON question_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

**混合检索策略**：
```python
# MCP(精确) + RAG(语义) 混合权重
context = {
    "mcp_context": {  # 权重 0.6
        "weak_points": [...],
        "recent_errors": [...],
        "mastery_scores": {...}
    },
    "rag_context": {  # 权重 0.4
        "similar_questions": await vector_search(query_embedding, top_k=5),
        "semantic_related_errors": await find_similar_errors(user_id, query_embedding),
        "knowledge_clusters": await cluster_knowledge_points(user_id)
    }
}
```

**成本考量**：
- **Embedding API 调用** - 通义千问约 ¥0.0007/千token (需评估月成本)
- **存储成本** - 向量数据约为原始数据的 2-3 倍
- **查询性能** - IVFFlat 索引在百万级数据下查询耗时 < 50ms

**渐进式迁移**：
1. Week 1: 安装 PGVector 扩展 + 基础表结构
2. Week 2: 批量向量化历史数据(离线任务)
3. Week 3: 实现混合检索 API，灰度 10% 用户
4. Week 4: 监控效果指标(回答相关性、用户满意度)
5. Week 5: 根据数据调优权重，全量发布

---

### 8.2 百炼智能体集成详解

**智能体配置信息**：

```/dev/null/bailian-config.py#L1-20
BAILIAN_CONFIG = {
    "name": "五好-伴学K12",
    "application_id": "db9f923dc3ae48dd9127929efa5eb108",
    "api_key": "sk-7f591a92e1cd4f4d9ed2f94761f0c1db",  # 示例，生产需替换
    "base_url": "https://dashscope.aliyuncs.com/api/v1",
    "timeout": 30,
    "max_retries": 3,
    "model": "qwen-max",  # 或其他支持的模型
    "temperature": 0.7,   # 创新性控制
    "max_tokens": 2000    # 响应长度限制
}
```

**核心服务数据模型**：

| 服务类型 | 请求模型                  | 响应模型                   | 说明                        |
| -------- | ------------------------- | -------------------------- | --------------------------- |
| 作业批改 | HomeworkCorrectionRequest | HomeworkCorrectionResponse | 支持多模态输入（文本+图片） |
| 学习问答 | StudyQARequest            | StudyQAResponse            | 基于上下文的个性化回答      |
| 学情分析 | LearningAnalysisRequest   | LearningAnalysisResponse   | 学习数据聚合分析            |

**请求模型结构**（示例：作业批改）：

```/dev/null/homework-models.py#L1-25
@dataclass
class HomeworkCorrectionRequest:
    user_id: str
    subject: str           # 学科：math, chinese, english, etc.
    grade_level: int       # 年级：1-12
    homework_text: str     # OCR识别的题目文本
    answer_text: str       # 学生答案
    image_urls: List[str]  # 作业图片URL（可选）
    context: Optional[str] # 额外上下文信息

@dataclass
class HomeworkCorrectionResponse:
    correction_id: str
    is_correct: bool
    score: float           # 分数 (0-100)
    corrections: List[str] # 批改意见
    knowledge_points: List[str]  # 涉及知识点
    difficulty_level: str  # 难度等级: easy/medium/hard
    suggestions: List[str] # 学习建议
    error_analysis: Optional[str]  # 错误分析
    confidence_score: float        # AI 置信度 (0.0-1.0)
    processing_time_ms: int        # 处理时间
```

**调用封装策略**：

- **统一入口**：`BailianService` 类封装所有 AI 调用
- **错误处理**：分类处理网络超时、API 限流、模型错误
- **重试机制**：指数退避，最大 3 次重试
- **结果缓存**：计划对相似问题启用语义缓存（规划）

---

## 9. 性能与扩展策略

| 关注点     | 现状                   | 优先后续                         |
| ---------- | ---------------------- | -------------------------------- |
| DB 查询    | 通过监听分析慢查询     | 增加索引建议生成器               |
| 查询缓存   | 结构已留（QueryCache） | 对热点接口启用                   |
| 分页策略   | Limit/Offset           | 大数据集：基于游标分页           |
| 并发       | 单进程多协程           | 多进程 + 连接池调优              |
| 静态资源   | 前端独立构建           | CDN / 版本指纹                   |
| 横向扩展   | 由容器数目扩展         | 会话/限流状态集中化              |
| 任务异步化 | 同步路径为主           | 引入任务队列(如 RQ/Redis Stream) |

---

## 10. 安全控制点概览

| 层级     | 控制点           | 说明                       |
| -------- | ---------------- | -------------------------- |
| 入口     | Nginx + TLS      | 强制 HTTPS 与头部注入      |
| 传输     | CORS 限制        | 仅允许白名单               |
| 身份     | Token（规划Jwt） | 后续加入刷新机制           |
| 访问频率 | 限流中间件       | 多维度分类                 |
| 数据     | ORM + 参数校验   | 防注入 + 类型安全          |
| 输出     | 统一包装         | 防内部结构泄漏             |
| 机密     | Secrets 脚本     | 权限 600 + 轮换计划 (规划) |

---

## 11. 可观察性 (当前 vs 规划)

| 维度     | 当前             | 规划                  |
| -------- | ---------------- | --------------------- |
| 请求统计 | 内存指标收集     | 指标导出 (Prometheus) |
| 错误分类 | 日志 + 响应结构  | 统一错误码索引        |
| 性能分位 | p95/p99 内部统计 | 外部可视化面板        |
| DB 查询  | 慢查询列表       | 查询模式聚合分析      |
| 限流状态 | 端点查询         | 历史趋势存档          |
| 业务指标 | 基础计数         | 学情分析可视化        |

详见：`OBSERVABILITY.md`（待补）

---

## 12. 错误与异常处理策略

| 类型     | 例子              | 处理                         |
| -------- | ----------------- | ---------------------------- |
| 校验错误 | Pydantic 验证失败 | 422 + 统一 error payload     |
| 业务错误 | 资源不存在        | 404 + 业务编码               |
| 授权错误 | 未认证/权限不足   | 401 / 403                    |
| 限流错误 | 频次超限          | 429 + `Retry-After`          |
| 系统错误 | DB 连接失败       | 500 + 追踪日志（不暴露堆栈） |

响应标准（成功/失败）定义在：`api/overview.md`（迁移后）

---

## 13. 配置与环境

| 环境           | 数据库                 | 监控           | 安全级别        | 备注       |
| -------------- | ---------------------- | -------------- | --------------- | ---------- |
| development    | SQLite / Postgres 可选 | 指标可视化关闭 | 宽松            | 热开发     |
| testing        | 内存/隔离 DB           | 关闭限流       | 严格断言        | CI 规划    |
| staging (规划) | PostgreSQL             | 预生产指标     | 接近生产        | 压测/回归  |
| production     | PostgreSQL + 备份      | 全量指标与告警 | 强安全头 + 限流 | 稳定性优先 |

Env 管理脚本：`scripts/env_manager.py`

---

## 14. 未来拆分可能路径 (Monolith → Modular)

| 拆分候选        | 拆分触发条件         | 形态             |
| --------------- | -------------------- | ---------------- |
| AI 服务调用模块 | 多模型/多策略/高并发 | 独立微服务       |
| 学情分析计算    | 批量统计/异步调度    | 定时任务服务     |
| 文件处理 / OCR  | 图片/附件处理增强    | 独立异步处理管道 |
| 监控导出层      | 指标聚合/集中收集    | Sidecar/Agent    |
| 通知/消息       | 新增消息通道         | 事件驱动微服务   |

---

## 15. 依赖与外部接口

| 类别    | 依赖           | 作用            | 风险             |
| ------- | -------------- | --------------- | ---------------- |
| Runtime | FastAPI        | Web 框架        | 框架更新语义变更 |
| ORM     | SQLAlchemy 2.x | 异步 ORM        | API 变动         |
| AI      | 阿里云百炼     | 智能生成/批改   | 外部 SLA         |
| 缓存    | Redis          | 限流 / 未来缓存 | 网络延迟         |
| 存储    | PostgreSQL     | 持久化          | 备份/恢复策略    |
| 监控    | psutil         | 系统指标        | 平台兼容性       |

---

## 16. 架构演进路线图 (Roadmap Snapshot)

| 阶段  | 技术重点           | 架构影响            |
| ----- | ------------------ | ------------------- |
| 0.1.x | 功能拼装与文档重构 | 单体 + 分层稳定     |
| 0.2.x | 学情分析指标固化   | 引入分析聚合结构    |
| 0.3.x | 可观察性闭环       | 导出指标 / 告警策略 |
| 0.4.x | 缓存/性能调优      | 查询缓存生效        |
| 1.0.0 | 稳定版             | 结构冻结 + ADR 齐全 |
| 1.x+  | 服务拆分（按负载） | 模块 → 独立部署     |

---

## 17. 简化 ADR 引用

| ID     | 标题                 | 摘要            | 状态   |
| ------ | -------------------- | --------------- | ------ |
| ADR-01 | FastAPI + async ORM  | 性能 + 类型支持 | 固定   |
| ADR-02 | 分层 + 仓储模式      | 低耦合 / 易测试 | 固定   |
| ADR-03 | 限流双策略           | 突发+平滑       | 固定   |
| ADR-04 | 内建监控替代外部依赖 | 快速迭代        | 固定   |
| ADR-05 | 文档拆分结构化       | 降低维护成本    | 执行中 |
| ADR-06 | 短期不引入消息队列   | 复杂度控制      | 可复审 |

---

## 18. 质量保障与边界

| 保障点     | 机制                     | 衔接文件         |
| ---------- | ------------------------ | ---------------- |
| 类型安全   | Pydantic v2 + mypy       | DEVELOPMENT.md   |
| 结构一致   | Schemas/Response Wrapper | api/overview.md  |
| 慢查询发现 | 性能监控模块             | OBSERVABILITY.md |
| 流量防护   | 限流中间件 + 429         | SECURITY.md      |
| 配置漂移   | 环境脚本模板化           | DEPLOYMENT.md    |
| 回滚       | 备份 + 镜像标签          | DEPLOYMENT.md    |

---

## 19. 约束与非目标 (Out of Scope 当前阶段)

| 非目标               | 原因                         |
| -------------------- | ---------------------------- |
| 分布式事务           | 当前无跨服务写操作           |
| 实时推送（WS）       | 先保证核心批改/问答链路稳定  |
| 复杂 AB 测试框架     | 用户规模未达需求             |
| 零依赖 Serverless 化 | 长期热点存在，常驻更优       |
| 多云动态调度         | 运维复杂度不符合当前阶段收益 |

---

## 20. 文件/模块快速参考

| 需求            | 查找位置                                  |
| --------------- | ----------------------------------------- |
| 查看 API 路由   | `src/api/v1/endpoints/`                   |
| 新增数据模型    | `src/models/` + Alembic 迁移              |
| 增加业务逻辑    | 新建 Service 或扩展现有                   |
| 修改限流策略    | `src/core/security.py`                    |
| 性能监控逻辑    | `src/core/monitoring.py`                  |
| Query 缓存/跟踪 | `src/core/performance.py`                 |
| 数据统计查询    | `src/repositories/learning_repository.py` |
| 加新端点        | 路由 + Schema + Service 调用              |
| 备份/恢复       | `scripts/db_backup.py`                    |
| 部署            | `scripts/deploy.py`                       |

---

## 21. 示例：仓储到服务调用关系

```/dev/null/service-repo-example.py#L1-40
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories import BaseRepository
from src.models.learning import ChatSession
from src.schemas.learning import ChatSessionCreate, ChatSessionOut

class ChatSessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BaseRepository(ChatSession, db)

    async def create_session(self, payload: ChatSessionCreate) -> ChatSessionOut:
        obj = await self.repo.create(payload.model_dump())
        return ChatSessionOut.model_validate(obj.__dict__)
```

---

## 22. 示例：统一响应包装（逻辑片段）

```/dev/null/response-wrapper.py#L1-30
from fastapi import APIRouter
from src.schemas.common import DataResponse
from src.services.chat import ChatService

router = APIRouter()

@router.post("/ask", response_model=DataResponse[str])
async def ask_question(req):
    answer = await ChatService().answer(req.question)
    return DataResponse(success=True, data=answer, message="OK")
```

---

## 23. 后续补充计划

| 补充项             | 说明                          |
| ------------------ | ----------------------------- |
| ASCII → 正式架构图 | 使用 Mermaid / UML 图增强表达 |
| 指标参考表         | 与 Prometheus 命名对齐        |
| 缓存策略草案       | 热点读/分析读区分             |
| 学情分析算法说明   | 指标→权重→解释体系            |
| 全局错误码清单     | 错误处理标准化支持前端提示    |

---

## 24. 维护指引

1. 新增模块 → 评估是否需要增加服务层/仓储层
2. 设计变更 → 若影响跨层协作，追加简化 ADR
3. 文件更新策略：
    - 结构变更：更新本文件对应章节
    - 函数级细节：不要写入架构文件（放代码注释）
4. 废弃组件：标记 `[DEPRECATED: 日期]` 并在本文件“演进路线”标注处理计划

---

## 25. 反馈与修订

发现架构文件过时或不一致：

- 提交 Issue：标签 `architecture`
- 或 PR：附摘要（变更原因 / 影响范围 / 回滚难度）

---

（END）

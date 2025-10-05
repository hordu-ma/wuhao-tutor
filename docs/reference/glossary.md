# 五好伴学 项目术语表 (GLOSSARY)

Last Updated: 2025-09-29
适用范围：后端与前端协同 / 文档重构阶段（初稿）

本文件用于统一项目中出现的业务、技术、AI、数据与运维相关术语，降低歧义，提升沟通效率。
凡新增领域名词 / 缩写，需在此登记。
排序按主题分组 + 组内字典序；多义词需标“[注意]”。

---

## 1. 业务域核心术语

| 术语 | 英文 / 缩写 | 定义 | 备注 / 约束 |
|------|-------------|------|-------------|
| 作业模板 | Homework Template | 教师创建的批改规则与题目集定义实体 | 不包含学生答案 |
| 作业提交 | Homework Submission | 学生一次具体作业提交记录 | 关联模板；含文本或文件 |
| 批改结果 | Homework Correction | 针对一次提交的 AI/系统评估结果 | 可能是异步生成 |
| 学习会话 | Learning Session / Chat Session | 用户与 AI 在同一主题/上下文下的交互容器 | ID 稳定；可归档 |
| 问题 | Question | 用户在会话中的单次提问 | 关联会话 |
| 回答 | Answer | AI 生成的响应（含置信度） | 可包含引用来源（规划） |
| 学情分析 | Learning Analytics | 针对学习行为与结果的统计与推断 | 指标化 + 可视化 |
| 知识点掌握 | Knowledge Mastery | 对特定知识点的掌握度估计（0~1 或百分比） | 需基于统计与策略 |
| 学习洞察 | Learning Insight | 基于行为数据给出的结构化可操作反馈 | 派生于分析层 |
| 建议 | Suggestion | 针对学习薄弱环节的改进提示 | 来源：AI 或规则 |
| 反馈项 | Feedback Item | 批改结果中针对具体题目/小项的评价结构 | 含得分/评语/标签 |
| 活跃日 | Active Day | 有有效学习事件（问答/作业）的日历日 | 用于活跃度统计 |
| 题目数 | Question Count | 指定窗口内提问总数 | 受过滤（去重策略可选） |

---

## 2. AI 相关术语

|| 术语 | 英文 / 缩写 | 定义 | 备注 |
||------|-------------|------|------|
|| 智能体 | Agent | 百炼封装的模型服务实体 | 受外部平台配置 |
|| Prompt | Prompt | 发送给模型的指令/上下文串 | 内部不对外泄露系统提示 |
|| 置信度 | Confidence Score | 模型对回答可靠性打分（0~1 区间） | 非严格统计意义 |
|| Tokens | Tokens | 模型处理的单位字片段 | 用于成本计量（规划） |
|| 引用来源 | Source / Evidence | 回答引用的文档/片段指针 | 规划字段：sources[] |
|| 模型开销 | Cost / Usage | 按 tokens 或次数计的资源用量 | 后续监控展示 |
|| 限流（AI） | AI Rate Limit | 针对 AI 接口的专用调用限制 | 防止滥用与失控成本 |
|| 上下文会话 | Context Window | AI 可以一次处理的 token 范围 | 超出需截断或摘要 |
|| 降级 | Fallback / Degrade | 外部 AI 失败时采用的应急策略 | 当前以失败返回为主，规划降级 |
|| MCP | Model Context Protocol | 基于精确数据库查询的上下文构建协议 | Phase 4-5 实现 |
|| RAG | Retrieval-Augmented Generation | 检索增强生成，结合向量检索和LLM | Phase 6 计划 |
|| 向量检索 | Vector Search | 基于语义相似度的检索技术 | 使用 PGVector 实现 |
|| Embedding | Embedding | 文本向量化表示 | 通义千问 Embedding API |
|| 语义检索 | Semantic Search | 理解语义的智能检索 | RAG 核心能力 |
|| 混合检索 | Hybrid Search | MCP（精确）+ RAG（语义）融合检索 | 最终目标架构 |
|| 时间衰减 | Time Decay | 近期数据权重更高的衰减算法 | MCP 查询策略 |
|| 知识点掌握度 | Knowledge Mastery Score | 基于错误率和时间衰减的掌握度评估 | MCP 输出指标 |

---

## 3. 数据与统计术语

| 术语 | 英文 | 定义 | 备注 |
|------|------|------|------|
| 窗口期 | Time Window | 统计计算的时间范围（如最近 7 天） | days 参数传入 |
| 分位数 | Percentile (p95/p99) | 排序后位置的延迟或数值 | 性能/响应指标 |
| 平均分 | Average Score | 某组作业的平均批改得分 | 平滑策略可选 |
| 掌握度 | Mastery Score | 知识点熟练度估计值 | 0~1 或百分制，需说明 |
| 活跃度 | Activity Level | 用户在时间窗口内的行为强度指标 | 行为类型可配置 |
| 延迟 | Latency | 请求或 AI 调用耗时 | 单位 ms |
| 慢查询 | Slow Query | 超过阈值的数据库查询 | prod 阈值默认 500ms |
| 命中率 | Hit Ratio | 缓存命中数量 / 总访问 | 规划指标 |

---

## 4. 性能与监控术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| QPS | Queries Per Second | 每秒处理的请求数量 | 评估吞吐 |
| 吞吐量 | Throughput | 单位时间内处理事件数 | 广义，可指 AI 调用 |
| p95 / p99 | Percentile | 95% / 99% 请求不超过的耗时 | 用户体验窗口 |
| 在途请求 | In-Flight Requests | 当前正在处理尚未完成的请求数 | 反映并发 |
| 限流触发 | Rate Limit Hit | 请求因速率控制被拒绝 | 返回 429 |
| 熔断 | Circuit Breaker | 检测外部故障后短路调用 | 尚未实装 |
| 软限 | Soft Limit | 达到预警阈值但未阻断 | 规划阶段 |
| 资源探针 | Probe | 健康/就绪状态检查点 | /health /ready 等 |
| 性能快照 | Performance Snapshot | 采样/周期记录的性能聚合数据 | 用于对比 |

---

## 5. 安全与访问控制术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 认证 | Authentication | 确认请求身份 | 规划使用 JWT |
| 授权 | Authorization | 决定是否允许访问资源 | 角色/属主校验 |
| 角色 | Role | 用户权限集合标签 | student / teacher / admin（规划） |
| 限流范围 | Rate Scope | 限流分类：per_ip / per_user / ai_service / login | 统一写法 |
| 配额 | Quota | 长周期使用上限（如月度） | 规划中 |
| 安全头 | Security Headers | HTTP 头增强策略 | CSP / HSTS 等 |
| CSP | Content Security Policy | 前端资源加载白名单策略 | 防脚本注入 |
| HSTS | HTTP Strict Transport Security | 浏览器强制使用 HTTPS | 生产启用 |
| 维护模式 | Maintenance Mode | 应用进入只读/受限状态 | 规划可切换端点 |
| 审计日志 | Audit Log | 记录敏感或关键操作 | 规划中 |
| 幂等键 | Idempotency Key | 确保重复请求效果一致的标识 | 规划，用于敏感 POST |

---

## 6. API 设计与响应术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 版本前缀 | API Version Prefix | `/api/v1` 的路径级版本声明 | 非 Header |
| 资源路径 | Resource Path | REST 风格资源访问路径 | `/homework/submissions` |
| 分页 | Pagination | 列表结果分段返回机制 | limit + offset（初版） |
| 偏移量 | Offset | 当前结果集起始位置 | 与 limit 配合 |
| has_more | Has More | 是否存在下一段结果 | 计算方式：条目数 vs total |
| 响应包装 | Response Envelope | 统一结构：success/data/error | 所有端点一致 |
| 错误码 | Error Code | error.code 枚举值 | 定义于 errors.md |
| 软删除 | Soft Delete | 标记删除而非物理删除 | 当前未开放对外 |
| 并发提交 | Concurrent Submission | 多次同时写入的冲突场景 | 返回 409 |
| 幂等 | Idempotency | 多次执行结果不发生变化 | GET/DELETE/PUT 天然幂等 |

---

## 7. 数据访问与存储术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 仓储层 | Repository Layer | 封装数据库 CRUD 与查询逻辑 | BaseRepository / 业务仓储 |
| 业务仓储 | Business Repository | 面向领域的复合/统计查询集合 | LearningRepository 等 |
| ORM 模型 | ORM Model | 映射数据库表的类 | SQLAlchemy Declarative |
| 事务 | Transaction | 一组操作的原子性单元 | async session 管理 |
| 迁移 | Migration | 数据库结构演进步骤脚本 | Alembic |
| 回滚 | Rollback | 迁移逆向执行或事务撤销 | 控制异常一致性 |
| 索引 | Index | 数据库性能结构 | 需文档说明用途 |
| 缓存层 | Cache Layer | 加速热点数据访问机制 | 规划：内存 + Redis |
| 查询缓存 | Query Cache | 针对特定查询结果的临时缓存 | TTL 控制 |
| 慢查询阈值 | Slow Query Threshold | 识别慢查询的耗时界限 | 环境可变 |

---

## 8. 日志与观察术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 结构化日志 | Structured Log | JSON 或键值化的日志格式 | 便于聚合分析 |
| Trace ID | Trace Identifier | 整个请求链的唯一标识 | 规划注入 |
| 事件日志 | Event Log | 重要状态变化的离散记录 | 与指标互补 |
| 指标 | Metric | 可聚合数值型观测点 | request_count 等 |
| 分位数 | Percentile | 延迟统计中的百分位位置 | p95/p99 |
| 采样 | Sampling | 只记录/上报部分数据的策略 | Trace/日志 降噪 |
| 仪表板 | Dashboard | 可视化展示面板 | Grafana（规划） |
| 告警 | Alert | 指标超出阈值的自动通知 | 规划引入 |

---

## 9. 文件与上传处理术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 原始文件名 | Original Filename | 客户端上传的文件显示名称 | 不作信任利用 |
| 存储文件名 | Stored Filename | 服务端存储时生成的安全文件名 | 防冲突/穿越 |
| 预览地址 | Preview URL | 文件部分内容访问链接 | 权限控制必要 |
| 下载地址 | Download URL | 文件完整获取链接 | 需鉴权 |
| MIME 类型 | MIME Type | 内容类型标识 | 需验证 |
| 校验和 | Checksum | 内容哈希摘要 | 防篡改（规划） |
| 清理策略 | Retention / Cleanup Policy | 临时或过期文件回收机制 | 定时任务 |

---

## 10. 角色与协作术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 维护者 | Maintainer | 负责核心设计与合并决策人员 | 代码审查权 |
| 贡献者 | Contributor | 提交代码/文档改进的参与人 | PR 合规即可 |
| 审阅者 | Reviewer | 进行代码评估与质量把控 | 可多人 |
| 发布负责人 | Release Owner | 推进一次版本发版流程 | 编写变更说明 |
| 文档责任人 | Documentation Owner | 保障文档同步与结构 | 当前：重构组 |
| 安全责任人 | Security Owner | 关注安全事件处理与策略维护 | 定期巡检 |
| 运维责任人 | Ops Owner | 监控与部署运行保障 | 生产环境锁定权限 |

---

## 11. 风险与质量相关术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 回归 | Regression | 修复或新增功能导致旧功能失效 | 需补回归测试 |
| 缺陷复现 | Reproduction | 重建导致缺陷的最小步骤 | 提交时需说明 |
| 覆盖率 | Coverage | 测试代码执行覆盖程度 | 行/分支视维度 |
| 基线 | Baseline | 当前可接受的指标数值标准 | 用于预警参考 |
| 冻结期 | Code Freeze | 发版前限制非必要变动窗口 | 减少不确定性 |
| ADR | Architecture Decision Record | 架构决策记录 | 可简化 |
| 弃用 | Deprecated | 功能/字段计划移除 | 提前公告 |
| 观测盲区 | Observability Gap | 缺少监控/日志支持的风险区域 | 需计划补齐 |

---

## 12. 规划 / 路线图术语

| 术语 | 英文 | 定义 | 说明 |
|------|------|------|------|
| 规划中 | Planned | 尚未实现但已进入路线图 | 有优先级 |
| 骨架完成 | Skeleton Ready | 基础结构可用但功能不完整 | 后续增强 |
| 稳定版 | Stable Release | 无破坏性大改；具备发布标准 | 对应 v1.0.0 目标 |
| 实验性 | Experimental | 试验性质功能，可能重构或移除 | 不建议对外依赖 |
| 观察期 | Observation Window | 新功能上线后重点监测阶段 | 常见 1~2 周 |
| 冻结 | Frozen | 暂不接受结构性变更 | 保证发布稳定 |
| 回滚 | Rollback | 恢复到前一发布状态或迁移前状态 | 需预案验证 |

---

## 13. 多义 / 易混淆术语与澄清

| 术语 | 误用场景 | 正确认知 | 备注 |
|------|----------|----------|------|
| Session（会话） | 混指“HTTP 会话”与“学习会话” | 项目内默认指“学习会话”（Chat Session），HTTP 会话写明 “HTTP Session” | 文档需明确 |
| 作业批改“实时” | 误以为立即返回结果 | 当前可能异步（视实现），需轮询或延迟获取 | 结果接口设计需区分状态 |
| AI 置信度 | 误以为绝对准确概率 | 仅为启发式参考分值 | 不作为评判唯一标准 |
| 延迟 | 误用为“响应时间 + 排队时间不区分” | 统计为端到端请求耗时（不含客户端渲染） | 需明确定义 |
| 学情分析 | 误解为“AI 推断全部” | 由统计 +（规划）部分算法/AI 增强组合 | 分层结构 |

---

## 14. 缩写表

| 缩写 | 全称 | 说明 |
|------|------|------|
| ADR | Architecture Decision Record | 架构决策说明 |
| CSP | Content Security Policy | 内容安全策略 |
| HSTS | HTTP Strict Transport Security | 强制 HTTPS 机制 |
| TTL | Time To Live | 缓存有效期 |
| SLA | Service Level Agreement | 服务可用性协议（外部 AI） |
| QPS | Queries Per Second | 请求吞吐指标 |
| P95/P99 | Percentile 95/99 | 延迟统计分位 |
| DB | Database | 数据库 |
| ORM | Object Relational Mapping | 对象关系映射 |
| API | Application Programming Interface | 应用接口 |
| SDK | Software Development Kit | 开发工具包 |
| KPI | Key Performance Indicator | 关键性能指标（规划） |
| ETA | Estimated Time of Arrival | 预计完成时间 |
| WIP | Work In Progress | 进行中 |
| PoC | Proof of Concept | 概念验证 |
| I/O | Input / Output | 输入输出 |
| RPS | Requests Per Second | 每秒请求数（与 QPS 类似） |

---

## 15. 变更登记

| 日期 | 变更 | 描述 | 维护人 |
|------|------|------|--------|
| 2025-09-29 | 初稿 | 建立骨架与核心术语集 | 文档重构组 |
| (待填) | ... | ... | ... |
| (待填) | ... | ... | ... |

---

## 16. 维护与使用规范

1. 新增术语：按所属分类添加；不确定则暂放“业务域核心术语”并 TODO 标记
2. 修改术语定义：需检查是否影响 API / 文档 / 代码注释
3. 移除术语：仅限废弃功能；需在 变更登记 标注原因
4. 评审节奏：建议每 2 周或每次重要版本前审阅
5. 自动化（规划）：为关键术语生成校验脚本，检测文档内未引用或重复拼写
6. 与前端协作：前端新增可视化指标/标签时需同步本文件

---

## 17. TODO（改进列表）

| 项 | 优先级 | 说明 |
|----|--------|------|
| 标注“规划中”术语最终初次出现版本 | P1 | 便于跟踪引入时点 |
| 增加“示例 JSON 片段引用列” | P2 | 学情分析 / 批改结果等 |
| 引入多语言（英文版 Glossary） | P3 | 国际化准备 |
| 自动检测术语未在代码出现 | P3 | 减少僵尸词条 |
| AI 相关评分/解释机制词条补充 | P2 | 置信度/来源/建议分类 |
| 添加“风险术语”标签列 | P2 | 快速定位敏感含义词 |

---

## 18. 使用建议（给开发/文档/前端）

| 场景 | 建议 |
|------|------|
| 写接口文档 | 优先引用本术语拼写，不自造近义词 |
| 前端展示标签 | 与英文/技术标识分离（UI 文案可二次映射） |
| 代码注释 | 可引用：`参见 GLOSSARY: 学情分析` |
| 评审 PR | 出现不明概念 → 要求加入或采用现有术语 |
| 培训新人 | 结合架构图 + 本术语表第一节快速过一遍 |

---

> 若发现术语歧义、缺失、冲突，请创建 Issue（标签：glossary）并附：术语 / 场景 / 期望定义 / 影响范围。

（END）

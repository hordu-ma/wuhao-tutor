# 五好伴学 API 端点清单 (Endpoints)

Last Updated: 2025-09-29
适用：后端 0.1.x（文档重构阶段，端点逐步核对中）
本文件列出按模块分类的 REST 端点，提供：方法 / 路径 / 功能概述 / 认证 / 速率限制 / 请求与响应模型占位。
详细数据模型与错误码：参见 `models.md` / `errors.md`（创建中）。

---

## 目录
- 1. 说明与约定
- 2. 认证模块 (auth)
- 3. 作业批改模块 (homework)
- 4. 学习问答模块 (learning)
- 5. 学情分析模块 (analysis)【规划】
- 6. 文件管理模块 (files)
- 7. 健康与监控模块 (health)
- 8. 管理/运维模块 (admin)【规划】
- 9. 公共结构参考
- 10. 新增端点流程
- 11. 变更记录占位

---

## 1. 说明与约定

| 字段 | 说明 |
|------|------|
| Auth | 是否需要认证（`None / Optional / Required / Role:<name>`） |
| Rate Scope | 关联限流维度（`per_ip` / `per_user` / `ai_service` / `login` / `none`） |
| Idempotent | 幂等特性说明（GET/DELETE/PUT 预期幂等；POST 说明是否支持幂等键【规划】） |
| Models | 引用请求/响应 Schema 名（在 `models.md` 中定义） |
| Status | 当前实现状态：`✅` 已实现 / `⏳` 进行中 / `🧩 规划` / `🚧 待验证` |
| Notes | 额外注意事项（如：可能性能敏感 / 后续扩展字段） |

命名规范：
- 资源集合：`/resource`（复数语义）
- 单一资源：`/resource/{id}`
- 动作式操作（非标准 CRUD）：使用后缀 `/action` 或嵌入语义端点（尽量先评估是否可归为资源状态）

---

## 2. 认证模块 (auth)

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| POST | /api/v1/auth/login | 用户登录（获取访问令牌） | None | login | LoginRequest | AuthTokensResponse | 🧩 | 规划支持刷新 |
| POST | /api/v1/auth/register | 用户注册 | None | per_ip | RegisterRequest | UserBasicResponse | 🧩 | 审核策略待定 |
| POST | /api/v1/auth/refresh | 刷新令牌 | Optional | per_user | RefreshRequest | AuthTokensResponse | 🧩 | 需实现 refresh token |
| POST | /api/v1/auth/logout | 注销（令牌失效） | Required | per_user | LogoutRequest? | SuccessResponse | 🧩 | 令牌黑名单策略 |
| GET | /api/v1/auth/me | 当前用户信息 | Required | per_user | - | UserProfileResponse | 🧩 | 与前端缓存策略联动 |

---

## 3. 作业批改模块 (homework)

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| POST | /api/v1/homework/templates | 创建作业模板 | Required | per_user | HomeworkTemplateCreate | HomeworkTemplateOut | ✅ | 教师权限（规划角色） |
| GET | /api/v1/homework/templates | 模板列表 | Required | per_user | Query: subject / limit / offset | Paginated[HomeworkTemplateOut] | ✅ | 分页统一化待核对 |
| GET | /api/v1/homework/templates/{template_id} | 获取模板详情 | Required | per_user | Path param | HomeworkTemplateOut | ✅ | - |
| PUT | /api/v1/homework/templates/{template_id} | 更新模板 | Required | per_user | HomeworkTemplateUpdate | HomeworkTemplateOut | ⏳ | 局部 vs 全量需确认 |
| DELETE | /api/v1/homework/templates/{template_id} | 删除模板 | Required | per_user | Path param | SuccessResponse | 🧩 | 可能改软删除 |
| POST | /api/v1/homework/submissions | 提交作业（含文件引用或文本） | Required | per_user | HomeworkSubmissionCreate | HomeworkSubmissionOut | ✅ | 文件需先上传 |
| GET | /api/v1/homework/submissions | 查询作业提交列表 | Required | per_user | Query: template_id / status / limit / offset | Paginated[HomeworkSubmissionOut] | ✅ | 可加按时间范围 |
| GET | /api/v1/homework/submissions/{submission_id} | 作业提交详情 | Required | per_user | Path param | HomeworkSubmissionOut | ✅ | - |
| POST | /api/v1/homework/submissions/{submission_id}/correct | 触发批改（同步/异步） | Required | ai_service | CorrectionTriggerRequest? | HomeworkCorrectionOut / AcceptedResponse | ⏳ | 规划异步队列 |
| GET | /api/v1/homework/corrections/{submission_id} | 获取批改结果 | Required | per_user | Path param | HomeworkCorrectionOut | ✅ | 若异步则轮询 |
| GET | /api/v1/homework/stats | 作业统计（已批改/平均分等） | Required | per_user | Query: range | HomeworkStatsResponse | 🧩 | 与分析模块融合 |

---

## 4. 学习问答模块 (learning)

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| POST | /api/v1/learning/sessions | 创建学习会话 | Required | per_user | LearningSessionCreate | LearningSessionOut | ✅ | 主题/学科可选 |
| GET | /api/v1/learning/sessions | 会话列表 | Required | per_user | Query: status / limit / offset | Paginated[LearningSessionOut] | ✅ | - |
| GET | /api/v1/learning/sessions/{session_id} | 会话详情 | Required | per_user | Path | LearningSessionDetailOut | ✅ | 可含最近问题 |
| POST | /api/v1/learning/ask | 向 AI 提问（自动关联会话或新建） | Required | ai_service | AskQuestionRequest | QuestionAnswerOut | ✅ | 响应包含 answer / latency |
| GET | /api/v1/learning/questions | 历史提问列表 | Required | per_user | Query: session_id / limit / offset | Paginated[QuestionOut] | ✅ | - |
| GET | /api/v1/learning/questions/{question_id} | 单个问题+回答 | Required | per_user | Path | QuestionAnswerOut | ✅ | - |
| GET | /api/v1/learning/questions/search | 搜索问题 | Required | per_user | Query: q / subject / limit | Paginated[QuestionOut] | ⏳ | 需索引策略 |
| GET | /api/v1/learning/insights (规划) | 学习互动洞察（频次等） | Required | per_user | Query: days | LearningInsightsResponse | 🧩 | 与 analysis 重叠待裁剪 |

---

## 5. 学情分析模块 (analysis)【规划】

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| GET | /api/v1/analysis/overview | 学情总览（概况） | Required | per_user | Query: days | LearningOverviewResponse | 🧩 | 依赖统计聚合 |
| GET | /api/v1/analysis/activity | 活跃度时间分布 | Required | per_user | Query: days | ActivityPatternResponse | 🧩 | 需预计算优化 |
| GET | /api/v1/analysis/mastery | 知识点掌握推断 | Required | per_user | Query: subject | KnowledgeMasteryResponse | 🧩 | 算法策略需定义 |
| GET | /api/v1/analysis/recommendations | 个性化建议 | Required | per_user | Query: subject | LearningSuggestionsResponse | 🧩 | 可能依赖 AI |
| GET | /api/v1/analysis/trends | 学习趋势（得分/频次） | Required | per_user | Query: metric / days | TrendSeriesResponse | 🧩 | 支持多个 metric |

---

## 6. 文件管理模块 (files)

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| POST | /api/v1/files/upload | 上传文件（作业/素材） | Required | per_user | multipart(form-data) | FileInfoOut | ✅ | 需限制类型 |
| GET | /api/v1/files | 列表（可按类别） | Required | per_user | Query: category / limit / offset | Paginated[FileInfoOut] | ✅ | 分页统一核对 |
| GET | /api/v1/files/{file_id} | 文件元数据 | Required | per_user | Path | FileInfoOut | ✅ | - |
| GET | /api/v1/files/{file_id}/download | 下载 | Required | per_user | Path | Binary/Streaming | ✅ | 需要权限校验 |
| GET | /api/v1/files/{file_id}/preview | 预览（可选转换） | Required | per_user | Path | PreviewResponse | ⏳ | 转码策略规划 |
| DELETE | /api/v1/files/{file_id} | 删除文件 | Required | per_user | Path | SuccessResponse | 🧩 | 软硬删除策略待定 |
| GET | /api/v1/files/stats | 文件使用统计 | Required | per_user | Query: category | FileStatsResponse | 🧩 | 与监控联动 |

---

## 7. 健康与监控模块 (health)

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| GET | /health | 基础健康（可公开） | None | per_ip | - | BasicHealthResponse | ✅ | 仅核心存活 |
| GET | /health/live | 活性探针 | None | per_ip | - | LiveProbeResponse | ✅ | Kubernetes 场景 |
| GET | /health/ready | 就绪探针 | None | per_ip | - | ReadyProbeResponse | ✅ | 依赖检查 |
| GET | /api/v1/health/performance | 性能指标 | Required? (可选开放) | per_ip | - | PerformanceMetricsResponse | ✅ | 包含延迟统计 |
| GET | /api/v1/health/rate-limits | 限流状态 | Required | per_user | - | RateLimitStatusResponse | ✅ | 调试/运维 |
| GET | /api/v1/health/metrics | 综合指标（性能+系统） | Required | per_user | - | AggregatedMetricsResponse | ✅ | 后续对接 Prometheus |
| GET | /api/v1/health/system (规划) | 系统资源（CPU/内存等） | Required | per_user | - | SystemProbeResponse | 🧩 | 运维模式 |
| GET | /api/v1/health/dependencies (规划) | 外部依赖状态 | Required | per_user | - | DependencyStatusResponse | 🧩 | AI / DB / Redis |
| GET | /api/v1/health/version | 版本与构建信息 | None | per_ip | - | VersionInfoResponse | ⏳ | 结合 CI 注入 |
| GET | /api/v1/health/config (受限) | 运行配置概要（脱敏） | Role:admin | per_user | - | SanitizedConfigResponse | 🧩 | 严格控制暴露 |

---

## 8. 管理/运维模块 (admin)【规划】

| Method | Path | 功能 | Auth | Rate Scope | Request | Response | Status | Notes |
|--------|------|------|------|------------|---------|----------|--------|-------|
| GET | /api/v1/admin/users | 用户列表（分页） | Role:admin | per_user | Query | Paginated[UserAdminOut] | 🧩 | 需权限模型 |
| PATCH | /api/v1/admin/users/{user_id} | 修改用户属性 | Role:admin | per_user | UserAdminUpdate | UserAdminOut | 🧩 | 审计日志 |
| GET | /api/v1/admin/audit-logs | 审计日志 | Role:admin | per_user | Query: type / range | Paginated[AuditLogOut] | 🧩 | 依赖记录策略 |
| POST | /api/v1/admin/cache/clear | 清理缓存 | Role:admin | per_user | CacheClearRequest | SuccessResponse | 🧩 | 加防护确认 |
| GET | /api/v1/admin/stats | 系统聚合统计 | Role:admin | per_user | Query: scope | SystemStatsResponse | 🧩 | 监控端口聚合 |
| POST | /api/v1/admin/maintenance/mode | 切换维护模式 | Role:admin | per_user | MaintenanceToggleRequest | MaintenanceStateResponse | 🧩 | 会话策略 |

---

## 9. 公共结构参考（占位）

| 类型 | 描述 |
|------|------|
| Paginated[T] | `{ items: [T], total?: int, limit: int, offset: int, has_more: bool }` |
| SuccessResponse | `{ success: true, data: null, message?: str }` |
| ErrorResponse | `{ success: false, error: { code, message, details? } }` |
| Timestamp | ISO8601, UTC (`Z` 结尾) |
| ID | UUID v4（或内部短 ID 规划） |
| ScoreRange | 数值型（0..max_score） |
| Confidence | 0.0 ~ 1.0 浮点 |
| RateLimitHeaders | `X-RateLimit-*` 系列（规划统一） |

---

## 10. 新增端点流程

| 步骤 | 动作 | 输出 |
|------|------|------|
| 1 | 评估是否可复用现有资源 | 避免重复 |
| 2 | 定义 Schema | `schemas/` 下新增或复用 |
| 3 | 在 Service 中实现业务 | 避免直接在路由写逻辑 |
| 4 | 编写路由（API Layer） | 统一响应包装 |
| 5 | 补充测试 | 单测 + 集成（必要时性能） |
| 6 | 更新本文件条目 | 添加行（保持分类与排序） |
| 7 | 更新 `models.md` / `errors.md` | 统一文档 |
| 8 | 若为敏感操作 | 评估限流 / 权限 / 审计 |
| 9 | 提交 PR | 标题含 `feat(api):` |
| 10 | 发布后追踪 | 性能与错误监控初期观察 |

命名提示：
- 若端点表达“触发批处理/后台任务”，优先考虑是否建“资源 + 状态”模式，而不是动词式 URL。
- 行为型补丁（如关闭、归档）可使用：`PATCH /resource/{id}` + body `{ "status": "archived" }`。

---

## 11. 变更记录占位

| 日期 | 端点 | 变更 | 影响 | 版本 |
|------|------|------|------|------|
| 2025-09-29 | （整体） | 端点首次结构化登记 | 文档重构基础 | 0.1.x |
| (待填) | /api/v1/homework/... | ... | ... | ... |
| (待填) | /api/v1/learning/... | ... | ... | ... |
| (待填) | /api/v1/health/version | 新增 | 版本可视化 | 0.1.x |
| (待填) | /api/v1/analysis/* | 模块上线 | 新功能集 | 0.2.x(规划) |
| (待填) | /api/v1/auth/refresh | 实现刷新机制 | 认证增强 | 0.2.x |
| (待填) | ... | ... | ... | ... |
| (规划说明) | 破坏性变更需移动或新增版本前缀 | v1 冻结后严格控制 | - | - |
| (规划说明) | 废弃端点需标记 deprecated 字段 | 提供过渡期 | - | - |
| (规划说明) | 合并端点需更新本表与 CHANGELOG | 减少漂移 | - | - |

---

补充说明：
- 若本清单与真实实现不符，以实际后端代码与自动生成 OpenAPI 为准，并应回填修正。
- 初期阶段（0.x）允许合理调整，但需在 PR 中说明兼容性影响。

（END）

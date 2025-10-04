# 五好伴学 API 总览 (API Overview)

Last Updated: 2025-09-29
适用版本：后端 0.1.x （未发布稳定版）
API 稳定层级：v1（内部迭代中，尚未冻结）

---

## 1. 设计目标

| 目标 | 说明 | 体现 |
|------|------|------|
| 一致性 | 所有响应结构统一 | success / data / error |
| 可演进 | 版本前缀 + 去破坏性策略 | `/api/v1/...` |
| 可观测 | 标准化性能/限流头部 | 监控端点 + 限流响应 |
| 安全性 | 标准认证与最小暴露 | 鉴权中间件 + 安全头 |
| 清晰语义 | 资源/动作遵循 REST | 模块化端点分区 |
| 可集成 | 友好 SDK 结构 | Python / JS 示例（后续拆分） |

---

## 2. 基础信息

| 项目 | 值 |
|------|----|
| 基础路径 (Base Path) | `/api/v1` |
| 协议 | HTTPS（生产）/ HTTP（本地） |
| 内容类型 | `application/json; charset=utf-8` |
| 编码 | UTF-8 |
| 认证方式 | （规划）Bearer Token / （当前）可匿名测试端点 |
| 速率限制 | 多维度（IP / 用户 / AI / 登录） |
| 超时建议（客户端） | 10s（普通）、25s（AI调用场景） |
| 时区 | UTC 存储，必要时前端本地化 |

---

## 3. 模块分区（逻辑）

| 模块 | 前缀示例 | 说明 |
|------|----------|------|
| 认证 (auth) | `/api/v1/auth/...` | 登录、注册、令牌（规划扩展） |
| 作业批改 (homework) | `/api/v1/homework/...` | 模板、提交、批改结果 |
| 学习问答 (learning) | `/api/v1/learning/...` | 会话、提问、回答记录 |
| 学情分析 (analysis, 规划) | `/api/v1/analysis/...` | 指标、进度、知识掌握 |
| 文件管理 (files) | `/api/v1/files/...` | 上传、列表、下载、预览 |
| 健康与监控 (health) | `/api/v1/health/...` | 活性、就绪、性能、限流状态 |
| 管理/运维 (admin, 规划) | `/api/v1/admin/...` | 配置、统计、后台控制 |

各模块详细端点将拆分在 `endpoints.md` 中。

---

## 4. 版本策略 (Versioning)

| 规则 | 内容 |
|------|------|
| 路径版本 | 使用前缀：`/api/v1/...` |
| 非破坏性更新 | 可在 v1 下添加字段、添加端点 |
| 破坏性变更 | 通过新版本（未来：`/api/v2`） |
| 字段弃用 | 返回 payload 中标注 `deprecated: true`（规划） |
| 生命周期 | 版本发布 → 冻结 → 软弃用 → 移除 |

---

## 5. 认证与授权 (Authentication & Authorization)

当前阶段：
- 内部开发测试环境可匿名调用部分端点
- 规划引入：
  - 用户注册/登录：`/auth/login`
  - JWT Access Token + Refresh Token
  - 角色/权限（教师 / 学生 / 管理员）
  - Token 失效与轮换策略

请求示例（规划格式）：
```
Authorization: Bearer <access_token>
```

后续将在 `auth.md` 或 `security.md` 中补充。

---

## 6. 请求规范 (Request Conventions)

| 项目 | 规范 |
|------|------|
| 方法语义 | GET=读取、POST=创建/动作、PUT/PATCH=更新、DELETE=删除 |
| Body | JSON（文件上传为 multipart） |
| 编码 | UTF-8 JSON（不要表单模拟 JSON） |
| 日期时间 | ISO8601（UTC），例：`2025-09-29T12:34:56Z` |
| 布尔 | JSON 标准：true / false |
| ID 类型 | UUID / 短标识（未来支持） |
| 排序参数 | `?order_by=field` 或 `?order_by=-field`（降序） |
| 过滤参数 | 扁平查询：`?status=active&subject=math` |
| 搜索参数 | `?search=关键词`（具体字段见对应端点文档） |

---

## 7. 响应结构 (Response Envelope)

成功 (带数据)：
```json
{
  "success": true,
  "data": { "id": "123", "name": "..." },
  "message": "OK"
}
```

成功 (无数据，仅确认)：
```json
{
  "success": true,
  "data": null,
  "message": "Deleted"
}
```

失败：
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源不存在",
    "details": {
      "resource": "HomeworkSubmission",
      "id": "a3c7..."
    }
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 是否成功 |
| data | any / null | 成功数据载荷 |
| message | string / null | 人类可读提示（成功时可选） |
| error | object / null | 错误信息（失败时存在） |
| error.code | string | 机器可解析错误码（统一枚举） |
| error.message | string | 人类可读错误说明 |
| error.details | object | 可选结构化上下文 |

错误码枚举将在 `errors.md` 中维护（待拆分）。

---

## 8. 常见 HTTP 状态码

| 状态码 | 使用场景 | 响应结构 |
|--------|----------|----------|
| 200 | 读取成功 | success=true |
| 201 | 创建成功 | success=true |
| 202 | 排队/异步处理（规划） | success=true |
| 204 | 删除成功（可选择用 200） | （可能为空） |
| 400 | 参数错误 / 业务拒绝 | success=false |
| 401 | 未认证 | success=false |
| 403 | 无权限 | success=false |
| 404 | 资源不存在 | success=false |
| 409 | 冲突（重复提交等） | success=false |
| 422 | 验证失败（Pydantic） | success=false |
| 429 | 触发限流 | success=false |
| 500 | 未捕获异常 | success=false |
| 503 | 下游依赖暂不可用（规划） | success=false |

---

## 9. 分页 (Pagination)

当前策略：偏移量分页

请求：
```
GET /api/v1/homework/submissions?limit=20&offset=40
```

响应（示例结构—规划）：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 128,
    "limit": 20,
    "offset": 40,
    "has_more": true
  }
}
```

| 字段 | 说明 |
|------|------|
| total | 可选，大数据集可能省略以减轻统计成本 |
| has_more | 基于 total 或本次条目数推断 |

未来扩展：游标分页（`?cursor=<token>`）用于深翻页性能优化。

---

## 10. 过滤 / 搜索 (Filtering & Search)

| 类型 | 说明 | 示例 |
|------|------|------|
| 精确过滤 | `?status=active` | 单值匹配 |
| 多值过滤（规划） | `?status=active,closed` | 使用逗号分隔 |
| 模糊搜索 | `?search=代数` | 限定字段集合 |
| 范围（规划） | `?created_from=...&created_to=...` | 日期范围 |
| 排序 | `?order_by=-created_at` | 支持多字段（规划） |

---

## 11. 限流 (Rate Limiting)

限流返回：
- 状态码：429
- 头部示例（规划统一化）：

| 头部 | 说明 |
|------|------|
| `X-RateLimit-Limit` | 当前窗口限制值 |
| `X-RateLimit-Remaining` | 剩余请求数 |
| `X-RateLimit-Reset` | 重置时间戳（秒） |
| `Retry-After` | 建议等待秒数 |

错误体：
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求过于频繁，请稍后再试",
    "details": {
      "scope": "per_ip",
      "limit": 60,
      "remaining": 0,
      "reset_in": 42
    }
  }
}
```

---

## 12. 幂等性 (Idempotency)

| 场景 | 策略 |
|------|------|
| 幂等读取 | GET 保证无副作用 |
| 创建接口 | 默认非幂等；未来对关键接口可加 `Idempotency-Key` |
| 更新 | PUT/PATCH 语义需满足重复调用不改变最终状态 |
| 删除 | DELETE 多次调用返回相同行为（可返回 404 或成功提示） |
| AI 任务（规划） | 使用客户端生成请求幂等标识防重复提交 |

---

## 13. 文件上传 (File Upload)

当前策略：
- 使用 `multipart/form-data`
- 字段示例：`file=<binary>`、`meta=<json-string>`（规划）
- 返回：
```json
{
  "success": true,
  "data": {
    "id": "file_123",
    "original_filename": "homework.jpg",
    "content_type": "image/jpeg",
    "size": 234234,
    "download_url": "/api/v1/files/file_123/download"
  }
}
```

未来增强：
- 病毒扫描（规划）
- OCR 预处理（规划）
- 临时凭证访问（规划）

---

## 14. 错误码分类（预留）

将在 `errors.md` 中统一维护：
- VALIDATION_ERROR
- AUTH_INVALID_CREDENTIALS
- AUTH_EXPIRED
- RESOURCE_NOT_FOUND
- RATE_LIMIT_EXCEEDED
- CONFLICT
- AI_SERVICE_FAILURE
- INTERNAL_SERVER_ERROR
- DEPENDENCY_UNAVAILABLE
- FILE_TYPE_NOT_ALLOWED
- FILE_TOO_LARGE

---

## 15. AI 相关端点注意事项

| 关注点 | 说明 |
|--------|------|
| 响应延迟 | 可能显著高于普通 CRUD（需超时容忍） |
| 回答可信度 | 字段：`confidence_score`（范围规范待定） |
| 内容来源（规划） | `sources: [{type, reference, snippet}]` |
| 重试策略 | 客户端重试需加幂等标记避免重复扣费（未来） |
| 审计 | 建议持久化问题/回答以便复盘（内部已支持） |

---

## 16. 安全基线（摘要）

| 项目 | 当前 | 规划 |
|------|------|------|
| TLS | 本地可 HTTP，生产强制 HTTPS | 强制 HSTS |
| CORS | 开发宽松 | 生产白名单 |
| 安全头 | 中间件注入 | CSP 动态策略 |
| 鉴权 | 规划中 | JWT + 刷新令牌 |
| 敏感日志 | 避免输出 Token | 安全审计扩展 |
| 文件校验 | 扩展名 + 大小 | MIME 深度检测 |

详见 `SECURITY.md`（生成后）。

---

## 17. 可观测性（摘录）

| 端点 | 说明 |
|------|------|
| `/api/v1/health` | 基础健康检查 |
| `/api/v1/health/performance` | 请求统计 / 分位数 |
| `/api/v1/health/rate-limits` | 限流信息 |
| `/api/v1/health/metrics` | 聚合指标（性能 + 安全） |

更多指标定义：`OBSERVABILITY.md`（待补）。

---

## 18. 去破坏性变更策略

| 类型 | 允许 | 示例 |
|------|------|------|
| 添加字段 | ✅ | 在 `data` 中新增可选字段 |
| 添加端点 | ✅ | 新功能模块 |
| 字段重命名 | ❌ (需新字段 + 弃用期) | `old_field` → `new_field` |
| 移除字段 | 需弃用周期 | 标注 deprecated 后至少 2 次小版本 |
| 改变字段语义 | ❌ | 需新字段 |
| 改变返回结构 | ❌ | 需新 API 版本 |
| 状态码调整 | 谨慎 | 记录在变更日志 |

---

## 19. 客户端重试建议

| 状态码 | 可重试 | 策略 |
|--------|--------|------|
| 408 / 超时 | 是 | 指数退避 |
| 429 | 是 | 等待 Retry-After |
| 500 / 503 | 条件性 | 避免无限重试 |
| 400 / 422 | 否 | 修复请求参数 |
| 401 | 条件性 | 刷新或重新认证 |
| 409 | 条件性 | 根据场景决定（例如重传） |

---

## 20. 示例快速调用 (暂示例化)

简单提问：
```
POST /api/v1/learning/ask
{
  "question": "什么是质数？"
}
```

响应：
```json
{
  "success": true,
  "data": {
    "question_id": "q_123",
    "answer": "质数是大于 1 且只能被 1 和自身整除的自然数。",
    "confidence_score": 0.92,
    "session_id": "sess_abc",
    "response_time_ms": 842
  }
}
```

---

## 21. 未来文档拆分关联

| 文件 | 说明 |
|------|------|
| `endpoints.md` | 各资源端点详细列表 |
| `models.md` | Schema / 字段含义 |
| `errors.md` | 错误码与语义 |
| `sdk-python.md` | Python SDK 示例 |
| `sdk-js.md` | JavaScript SDK 示例 |
| `changelog` / `STATUS.md` | 版本与演进说明 |

---

## 22. 待办 / 占位 (TODO)

| 项 | 状态 | 优先级 |
|------|------|--------|
| 分页统一返回结构落地 | 待确认 | P1 |
| 错误码专用文档 | 未创建 | P1 |
| AI 回答来源结构 | 设计中 | P2 |
| 幂等性键支持 | 未实现 | P2 |
| 游标分页机制 | 未设计 | P3 |
| SDK 文档拆分 | 规划中 | P1 |
| 认证模块 API | 即将规划 | P1 |
| Deprecation 机制 | 未落地 | P3 |

---

## 23. 反馈与修订

如发现：
- 与实际响应不一致
- 字段未记录
- 状态码误用
- 文档遗漏

请提交 Issue（标签：`api-docs`），或 PR 附：
1. 端点
2. 现状 vs 预期
3. 重现步骤（若适用）
4. 建议修订

---

（END）

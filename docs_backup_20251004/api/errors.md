# 五好伴学 API 错误码规范 (errors.md)

Last Updated: 2025-09-29
适用版本：后端 0.1.x （文档重构阶段）
状态：初稿（需与实际实现逐步核对）

---

## 1. 文档目的

本文件作为“统一错误语义来源（Single Source of Truth）”，用于：
- 规范错误码命名、分组与使用场景
- 指导前端/客户端统一处理与展示
- 支撑日志归类、监控统计、告警与回归测试
- 降低散乱自造错误结构的风险

与之相关的结构定义参见：`api/overview.md` 与 `api/models.md` 中的“错误结构”章节。

---

## 2. 错误响应基础结构

标准失败响应（所有 API 保持一致）：

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源不存在",
    "details": {
      "resource": "HomeworkSubmission",
      "id": "9d5e8ab1-..."
    }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 固定为 false |
| error.code | string | 是 | 参见本文件错误码枚举 |
| error.message | string | 是 | 人类可读短语（中文，前端可直接展示或二次本地化） |
| error.details | object/null | 否 | 结构化上下文（字段名、资源标识、限制值等） |

约束：
1. 不在根级直接返回 `message`（保持结构统一）
2. 不追加无定义的顶级字段（如 `status`, `err`, `reason` 等）
3. `error.code` 必须来自本文件（或通过“新增流程”正式引入）

---

## 3. 错误码命名原则

| 原则 | 描述 | 示例 |
|------|------|------|
| 全大写 + 下划线 | 统一格式 | `RESOURCE_NOT_FOUND` |
| 语义明确 | 读名字即可判断类型 | `INVALID_CREDENTIALS` |
| 避免歧义 | 不使用模糊词：`FAILED` / `ERROR` | ✅ `PERMISSION_DENIED` |
| 不含领域耦合 | 领域限定放到 details | `HOMEWORK_NOT_FOUND` → ❌（推荐 RESOURCE_NOT_FOUND + details.resource="Homework"） |
| 可扩展 | 预留分类空间 | 认证前缀：`AUTH_`、文件：`FILE_` |
| 非破坏性演进 | 新增 > 修改；废弃需标记 | 旧值保留一个小版本周期 |

---

## 4. 错误分层分类

| 类别 | 说明 | Code 前缀建议 |
|------|------|---------------|
| 验证/输入 | 参数格式、业务规则、类型约束 | （无或 VALIDATION_*） |
| 认证/授权 | 登录、令牌、权限 | AUTH_* / PERMISSION_* |
| 资源状态 | 不存在、冲突、状态非法 | RESOURCE_* / CONFLICT_* |
| 限流/配额 | 请求频率、容量限制 | RATE_LIMIT_* / QUOTA_* |
| 外部依赖 | AI 服务 / 第三方系统不可用 | DEPENDENCY_* / AI_* |
| 文件处理 | 类型、大小、存储失败 | FILE_* |
| 系统内部 | 未预期异常、不可恢复错误 | INTERNAL_* |
| 业务规则 | 合法但被业务拒绝（策略/状态） | BUSINESS_* |
| 安全策略 | 访问被策略阻止 | SECURITY_* |
| 运行模式 | 系统处于维护/只读 | MAINTENANCE_* |

---

## 5. 错误码总表（初稿）

| 错误码 | HTTP 状态建议 | 分类 | 典型场景 | details 示例 |
|--------|----------------|------|----------|--------------|
| VALIDATION_ERROR | 422 | 输入校验 | Pydantic 验证失败 / 自定义验证不通过 | { "field": "subject", "reason": "unsupported" } |
| INVALID_REQUEST | 400 | 输入格式 | JSON 解析失败 / 不支持的内容类型 | { "content_type": "text/plain" } |
| MISSING_REQUIRED_FIELD | 400 | 输入校验 | 必填字段缺失（业务层补充） | { "field": "template_id" } |
| AUTH_INVALID_CREDENTIALS | 401 | 认证 | 用户名或密码错误 | { "attempts": 1 } |
| AUTH_TOKEN_EXPIRED | 401 | 认证 | Access Token 过期（需刷新） | { "expired_at": "…" } |
| AUTH_TOKEN_INVALID | 401 | 认证 | Token 格式不合法或签名错误 | { "reason": "signature_mismatch" } |
| PERMISSION_DENIED | 403 | 授权 | 角色/权限不足 | { "required_role": "teacher" } |
| RESOURCE_NOT_FOUND | 404 | 资源 | 查询的 ID 不存在 | { "resource": "HomeworkSubmission", "id": "…" } |
| RESOURCE_GONE (规划) | 410 | 资源 | 已删除或不可访问 | { "resource": "File", "id": "…" } |
| CONFLICT | 409 | 资源冲突 | 并发更新 / 重复创建 | { "resource": "Template", "field": "name" } |
| DUPLICATE_SUBMISSION | 409 | 业务冲突 | 用户重复提交同作业 | { "template_id": "…" } |
| RATE_LIMIT_EXCEEDED | 429 | 限流 | IP / 用户请求频率超限 | { "scope": "per_ip", "limit": 60, "remaining": 0 } |
| QUOTA_EXCEEDED (规划) | 429/403 | 配额 | 用户月度配额耗尽 | { "quota_type": "ai_calls", "allocated": 1000 } |
| AI_SERVICE_FAILURE | 502 | 外部依赖 | AI 响应异常 / 格式错误 | { "provider": "bailian", "trace_id": "…" } |
| AI_TIMEOUT | 504 | 外部依赖 | AI 超时未响应 | { "timeout_ms": 10000 } |
| DEPENDENCY_UNAVAILABLE | 503 | 外部依赖 | Redis/DB/对象存储暂不可用 | { "service": "redis" } |
| FILE_TOO_LARGE | 413 | 文件 | 上传超过最大大小 | { "max_size": 5242880, "actual_size": 7340032 } |
| FILE_TYPE_NOT_ALLOWED | 415 | 文件 | 不允许的 MIME/扩展名 | { "allowed": ["jpg","png"], "actual": "exe" } |
| FILE_STORAGE_FAILED | 500 | 文件 | 保存失败（IO/权限） | { "reason": "disk_full" } |
| BUSINESS_RULE_VIOLATION | 400/409 | 业务 | 状态不允许操作 | { "rule": "submission_locked" } |
| STATE_NOT_ALLOWED | 409 | 业务状态 | 当前状态不支持该动作 | { "current_state": "correcting", "action": "cancel" } |
| SECURITY_POLICY_BLOCKED | 403 | 安全 | 被安全策略拒绝（CSP/Host） | { "policy": "trusted_host" } |
| MAINTENANCE_MODE | 503 | 运行模式 | 系统维护中只读 | { "mode": "read_only" } |
| INTERNAL_SERVER_ERROR | 500 | 系统 | 未捕获异常 | { "trace_id": "…" } |
| SERVICE_DEGRADED (规划) | 503 | 系统/降级 | 系统进入降级模式 | { "reason": "high_latency" } |
| RETRY_REQUIRED (规划) | 425/503 | 并发/一致性 | 需客户端稍后重试 | { "retry_after_ms": 500 } |
| UNSUPPORTED_OPERATION | 400/501 | 功能 | 端点存在但未启用 | { "feature": "analysis" } |
| IDempotency_KEY_CONFLICT (规划) | 409 | 幂等 | 相同幂等键重复冲突 | { "key": "abc123" } |
| PAYLOAD_TOO_LARGE (与 FILE 分离) | 413 | 输入 | JSON/文本体超限 | { "max_bytes": 1048576 } |
| REQUEST_TOO_LARGE_FIELD | 400 | 输入 | 单字段长度超限 | { "field": "content_text", "max_len": 5000 } |
| UNSUPPORTED_VERSION (规划) | 400 | 版本 | Client/Schema 版本不兼容 | { "client_version": "0.9.0" } |
| FEATURE_NOT_AVAILABLE | 403/404 | 功能开关 | 功能未启用（灰度/付费） | { "feature": "advanced_analysis" } |
| SESSION_EXPIRED (规划) | 401 | 会话 | 会话过期需重建 | { "session_id": "…" } |
| RATE_LIMIT_SOFT (规划) | 200 + header | 限流提示 | 软限流提醒（不阻断） | { "scope": "per_user", "warning": true } |
| DATA_INTEGRITY_ERROR | 500 | 数据 | 违反内部约束（非用户可控） | { "constraint": "fk_submission_template" } |
| UPLOAD_INCOMPLETE (规划) | 400 | 文件 | 分片或断点上传未完成 | { "received_chunks": 3, "expected": 5 } |
| UNSUPPORTED_MEDIA_TYPE | 415 | 输入 | Content-Type 不被接受 | { "content_type": "text/xml" } |
| INVALID_STATE_TRANSITION | 409 | 状态机 | 状态转移非法 | { "from": "closed", "to": "active" } |

> HTTP 状态选择说明：如业务仍想用 200 包含错误语义（不推荐），需团队评审；**必须**使用标准 4xx/5xx 体现语义，不使用自定义非标准码。

---

## 6. HTTP 状态码映射指南

| HTTP Code | 使用边界说明 | 备注 |
|-----------|--------------|------|
| 400 | 请求格式合法但语义/业务不通过 | 与 422 区分：422 更偏结构级/类型级 |
| 401 | 未认证或 Token 无效/过期 | 认证通过但权限不足 → 403 |
| 403 | 认证通过但权限不足或策略阻断 | 也用于功能未授权 |
| 404 | 资源真实不存在或不暴露 | 避免返回对象内部状态差异 |
| 409 | 资源当前状态与请求冲突 | 并发修改 / 状态不合法 |
| 410 | 资源已删除且不再可用 | （规划，谨慎使用） |
| 413 | 请求/文件过大 | 同时可返回可接受的限制 |
| 415 | 媒体类型不支持 | 文件类型或请求 Content-Type |
| 422 | 结构化验证失败 | 主要由 Pydantic / Schema 层触发 |
| 425/425-like | 幂等性/排序等待（可选） | 需明确客户端行为 |
| 429 | 限流触发 | 需带 `Retry-After` 头 |
| 500 | 未预料内部错误 | 避免返回敏感信息 |
| 502 | 下游 AI / 代理层错误 | 语义：上游返回非法响应 |
| 503 | 依赖不可用 / 维护模式 | 临时状态，客户端可重试 |
| 504 | 下游超时 | 支持重试或失败提示 |
| 501 | 暂未实现（谨慎） | 多用 FEATURE_NOT_AVAILABLE |

---

## 7. 与前端展示策略建议（摘要）

| 错误码 | 展示优先建议 |
|--------|--------------|
| AUTH_INVALID_CREDENTIALS | 表单内错误提示（不弹窗） |
| RATE_LIMIT_EXCEEDED | 顶部警告条 + 倒计时（如果有 reset_in） |
| RESOURCE_NOT_FOUND | 页面级空状态 / 返回上一层 |
| PERMISSION_DENIED | 引导联系管理员或降级说明 |
| AI_SERVICE_FAILURE | “AI 服务暂不可用，稍后再试” |
| FILE_* | 上传组件内错误提示 |
| VALIDATION_ERROR | 高亮字段 + 逐字段 messages |
| INTERNAL_SERVER_ERROR | 统一“系统繁忙，请稍后再试” |
| MAINTENANCE_MODE | 维护页跳转或覆盖层 |
| CONFLICT / STATE_NOT_ALLOWED | Toast + 可选“刷新重试”按钮 |

---

## 8. 日志与监控映射（初步）

| 维度 | 记录内容 | 示例字段 |
|------|----------|----------|
| 错误分类 | `error.code` | RATE_LIMIT_EXCEEDED |
| 请求上下文 | trace_id / path / method | 自动注入 |
| 用户上下文 | user_id / role | 认证中间件填充 |
| 重试信息 | retry_count（若中间层实现） | 2 |
| 依赖信息 | dependency_name / latency | ai_service |
| 安全告警 | policy / blocked | trusted_host |
| 限流指标 | scope / limit / remaining | per_ip / 60 / 0 |
| 性能关联 | duration_ms / p95 flag | 最高层中间件 |

监控指标（规划）：
- `api_errors_total{code="…"}`
- `api_error_rate{code="…"}`
- `rate_limit_trigger_total{scope="per_user"}`
- `ai_failures_total{provider="bailian"}`

---

## 9. 新增错误码流程

| 步骤 | 内容 | 输出 |
|------|------|------|
| 1 | 评估是否可复用现有错误码 | 若可复用，终止申请 |
| 2 | 给出场景 & 语义描述 | 场景说明（谁 + 何时 + why） |
| 3 | 拟定命名（遵循规范） | CODE_CANDIDATE |
| 4 | 确认 HTTP 状态码 | 对齐上表 |
| 5 | 补充 details 结构约定 | 字段名与样例 |
| 6 | 更新本文件表格（暂记“候选”） | PR 中标注 |
| 7 | 代码中实现映射 | 异常 → 统一处理器 |
| 8 | 添加测试覆盖 | 单元 + 集成用例 |
| 9 | 完成 PR / 评审 | 合并后归档 |
| 10 | 发布时写入 CHANGELOG | 可追踪演进 |

---

## 10. 废弃（Deprecated）策略

| 阶段 | 说明 |
|------|------|
| 标记阶段 | 在本文件对应行尾添加 `[DEPRECATED: YYYY-MM-DD]` |
| 过渡期 | 保留 ≥ 1 个次版本周期（0.x 阶段可为 2~3 周） |
| 替代方案 | 明确替换错误码 |
| 移除 | 移除行并在 CHANGELOG 中注明 |

示例：
```
OLD_ERROR_CODE  →  新：BUSINESS_RULE_VIOLATION
```

---

## 11. 统一使用建议 & 反例

| 坑 / 反例 | 原因 | 正确做法 |
|-----------|------|----------|
| 混用 `message` + `error.message` | 解析不统一 | 仅使用结构化包装 |
| 在 details 放用户可见文案 | 表达层与结构耦合 | details 仅结构化上下文 |
| 用 200 返回错误语义 | 客户端难以兼容 | 使用正确 4xx/5xx |
| 抛出裸字符串异常 | 无结构 | 自定义异常或统一转换 |
| `code` 与 HTTP 状态重复 | 语义贫乏 | code 要表达业务语义 |
| 文案硬编码英文 | 不适合中文用户 | 统一中文，可二次国际化 |
| details 无字段约定 | 难以解析 | 明确字段名（resource/id/field） |
| 过度拆分错误码 | 爆炸式增长 | 优先复用 + details 说明差异 |

---

## 12. 示例（Python 伪代码片段）

```python
from fastapi import HTTPException

class DomainError(HTTPException):
    def __init__(self, code: str, message: str, status: int, details: dict | None = None):
        super().__init__(status_code=status, detail={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            }
        })

# 使用示例：
def get_submission(submission_id: str):
    submission = repo.get(submission_id)
    if not submission:
        raise DomainError(
            code="RESOURCE_NOT_FOUND",
            message="资源不存在",
            status=404,
            details={"resource": "HomeworkSubmission", "id": submission_id}
        )
    return submission
```

（实际项目中可通过统一异常转换中间件代替直接抛 HTTPException。）

---

## 13. 测试建议

| 测试类型 | 重点 |
|----------|------|
| 单元测试 | 每个自定义异常 → 结构断言（code/message/details） |
| 集成测试 | 端到端触发典型错误场景（权限/不存在/限流） |
| 回归测试 | 避免错误码/状态码被意外更改 |
| 负载测试 | 错误率统计与限流触发比对 |
| 模糊输入测试 | 验证不会触发 500 而是期望的校验错误 |
| 合规测试 | 不泄露内部实现（堆栈/绝对路径） |

示例断言（伪）：
```python
resp = client.get("/api/v1/homework/submissions/non-exist-id")
assert resp.status_code == 404
j = resp.json()
assert j["error"]["code"] == "RESOURCE_NOT_FOUND"
assert "HomeworkSubmission" in j["error"]["details"]["resource"]
```

---

## 14. 监控与告警（规划）

| 告警指标 | 条件示例 | 动作 |
|----------|----------|------|
| error_rate_total | 5 分钟窗口 > 5% | 记录 + 分析 |
| error_code_surge{code="AI_SERVICE_FAILURE"} | 5 分钟次数突增 | 检查 AI 依赖 |
| rate_limit_exceeded | 单用户连续超过阈值 | 观察是否攻击 |
| internal_server_error | 短时间 > 基线 | 触发紧急排障流程 |
| dependency_unavailable | 持续 > 1 分钟 | 切换降级策略 |

---

## 15. 未来扩展占位

| 方向 | 说明 |
|------|------|
| 分级错误严重度 | 增加 severity（INFO/WARN/ERROR）辅助监控 |
| 可本地化 message key | `message_key` + i18n 资源映射 |
| 批量错误返回结构 | 用于批处理（例如文件批量操作） |
| partial success | 混合成功/失败部分结果语义 |
| trace_id 链路化 | 错误中自动包含 trace_id |
| 自动统计脚本 | 校验代码中是否有未登记错误码 |

---

## 16. 变更记录（本文件）

| 日期 | 版本 | 变更 | 描述 |
|------|------|------|------|
| 2025-09-29 | draft-1 | 初稿 | 建立基础分类与错误码集合 |
| (待填) | ... | ... | ... |

---

## 17. TODO（执行优先级建议）

| 项 | 优先级 | 说明 |
|----|--------|------|
| 与现有异常处理代码核对 | P0 | 确认未遗漏/未使用的 code |
| 增加统一异常转换层说明 | P0 | 使所有异常进入统一结构 |
| 定义 details 字段规范清单 | P1 | 避免字段混乱 |
| 增加错误监控指标导出 | P1 | Prometheus 接入 |
| 设计幂等冲突错误码 & 语义 | P2 | 结合未来 idempotency-key |
| 引入 severity 字段 | P2 | 方便日志分级 |
| 加入国际化 message_key | P3 | 为后续英文界面准备 |
| 自动化 lint：发现未注册错误码 | P3 | CI 检测 |
| 废弃过期/不再使用的错误码标记流程 | P3 | 规范生命周期 |

---

## 18. 反馈方式

发现以下情况之一：
- 错误码语义不清晰 / 与现实现不符
- HTTP 状态不符合标准
- 某端点返回了未登记错误码
- 需要新增错误码

请：
1. 创建 Issue（标签：`api-error`）
2. 填写：场景 → 期望行为 → 当前行为 → 复现步骤
3. 若需新增：附命名建议 + HTTP 状态 + details 示例

---

（END）

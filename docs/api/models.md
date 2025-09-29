# 五好伴学 API 数据模型规范 (API Models)

Last Updated: 2025-09-29
适用版本：后端 0.1.x （文档重构阶段）
状态：初稿（待与实际代码逐项核对）

---

## 目录
1. 文档目的
2. 命名与通用约定
3. 基础数据类型别名
4. 响应包装 (Response Envelope)
5. 分页结构 (Pagination)
6. 错误结构 (Error Model)
7. 核心领域模型
   - 7.1 用户 User
   - 7.2 作业模板 HomeworkTemplate
   - 7.3 作业提交 HomeworkSubmission
   - 7.4 批改结果 HomeworkCorrection
   - 7.5 学习会话 ChatSession
   - 7.6 问题 Question
   - 7.7 回答 Answer
   - 7.8 文件 FileInfo
8. 学情分析相关（规划）
9. AI 相关扩展字段说明
10. 统一字段语义规范
11. 示例对象
12. 兼容与演进策略
13. 未来扩展占位
14. 修订日志（本文件）
15. TODO 列表

---

## 1. 文档目的

本文件为 API 层输出/输入的数据结构权威来源（Single Source of Truth），保证：
- 字段命名一致
- 语义清晰且可扩展
- 与前端/SDK 的协同不依赖“口头解释”
- 变更可追踪（结合 CHANGELOG / STATUS）

不描述数据库内部实现细节（如索引、列类型），仅描述对外语义与格式。

---

## 2. 命名与通用约定

| 分类 | 约定 |
|------|------|
| 命名风格 | `snake_case`（JSON 字段） |
| 时间字段 | ISO8601 UTC，示例：`2025-09-29T12:34:56Z` |
| 标识字段 | 主键统一 `id`；引用使用 `<entity>_id` |
| 枚举字段 | 字符串枚举（小写） |
| 可选字段 | 缺失与 null 区分（尽量避免返回 null 可用场景） |
| 数字精度 | 分数/评分使用整数或固定小数（明确说明） |
| 列表字段 | 空集合返回 `[]`，不返回 `null` |
| Boolean | JSON 规范：`true / false` |
| 只读字段 | 出现在响应中，不出现在创建请求中 |
| 软删除 | 暂未对外暴露（规划阶段再引入） |

---

## 3. 基础数据类型别名

| 别名 | 实际类型 | 描述 |
|------|----------|------|
| ID | string(UUID v4) | 资源主键 |
| ShortID(规划) | string | 可读性较高的短标识 |
| Timestamp | string | ISO8601 UTC |
| Score | number | 题目/作业评分（整数或浮点） |
| Confidence | number (0.0~1.0) | 置信度 |
| Percentage | number (0~100) | 百分比（可能用于分析） |
| JsonObject | object | 扩展信息，结构受限 |
| JsonArray | array | 结构化列表 |
| Token(规划) | string | 认证 Token |

---

## 4. 响应包装 (Response Envelope)

标准成功：
```json
{
  "success": true,
  "data": { ... },
  "message": "OK"
}
```

标准失败：
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "资源不存在",
    "details": {
      "resource": "HomeworkSubmission",
      "id": "..."
    }
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 是否成功 |
| data | any / null | 条件 | 成功时数据载荷 |
| message | string / null | 否 | 人类可读提示语（成功） |
| error | ErrorObject / null | 条件 | 失败时的错误信息 |

---

## 5. 分页结构 (Pagination)

分页响应示例：
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 120,
    "limit": 20,
    "offset": 40,
    "has_more": true
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 当前页数据 |
| total | integer (可选) | 数据总条数（可能省略以提升性能） |
| limit | integer | 每页大小 |
| offset | integer | 当前偏移量 |
| has_more | boolean | 是否还有后续数据 |

---

## 6. 错误结构 (Error Model)

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 机器可解析错误编码（枚举） |
| message | string | 人类可读消息 |
| details | object / null | 附加上下文：参数名 / 资源 ID 等 |

示例：
```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数不合法",
  "details": {
    "field": "subject",
    "reason": "unsupported"
  }
}
```

常见错误码（初版草案，详见 `errors.md` 规划文件）：
- VALIDATION_ERROR
- AUTH_INVALID_CREDENTIALS
- AUTH_EXPIRED
- PERMISSION_DENIED
- RESOURCE_NOT_FOUND
- CONFLICT
- RATE_LIMIT_EXCEEDED
- AI_SERVICE_FAILURE
- FILE_TOO_LARGE
- FILE_TYPE_NOT_ALLOWED
- INTERNAL_SERVER_ERROR
- DEPENDENCY_UNAVAILABLE

---

## 7. 核心领域模型

### 7.1 用户 User（规划中）
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 用户唯一标识 |
| username | string | 否 | 登录/显示唯一名（策略待定） |
| role | string(enum) | 否 | 用户角色：student / teacher / admin（规划） |
| created_at | Timestamp | 是 | 创建时间 |
| updated_at | Timestamp | 是 | 最近更新时间（规划） |

（尚未公开的认证字段：密码哈希、状态等不在响应中暴露）

### 7.2 作业模板 HomeworkTemplate
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 模板主键 |
| name | string | 否 | 模板名称 |
| subject | string | 否 | 学科：math / chinese / english 等（需约束字典） |
| description | string / null | 否 | 说明文本 |
| template_content | string | 否 | 模板内容（结构化或富文本待定） |
| correction_criteria | JsonArray / null | 否 | 批改规则（例如多维评分项） |
| max_score | integer | 否 | 总评分上限 |
| created_at | Timestamp | 是 | 创建时间 |
| updated_at | Timestamp | 是 | 更新时间 |

请求模型：
- 创建：必填 `name` `subject` `template_content` `max_score`
- 更新：允许部分字段更新（需定义允许范围）

### 7.3 作业提交 HomeworkSubmission
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 提交主键 |
| template_id | ID | 否 | 关联模板 |
| student_id (规划) | ID | 否 | 学生用户 ID |
| student_name | string | 否 | 学生名称（临时，规划改为 user 绑定） |
| file_url | string / null | 否 | 附件路径（若为图片/PDF/Zip） |
| content_text | string / null | 否 | 纯文本作业内容（可选） |
| status | string(enum) | 是 | submitted / correcting / corrected / failed |
| submitted_at | Timestamp | 是 | 提交时间 |
| completed_at | Timestamp / null | 是 | 批改完成时间（有结果才填） |
| additional_info | JsonObject / null | 否 | 扩展信息（如客户端 meta） |

请求模型：
- 创建：`template_id` + (`file_url` 或 `content_text`) 二选一必填
- 触发批改：可能 POST 动作端点或自动触发（策略待定）

### 7.4 批改结果 HomeworkCorrection
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| submission_id | ID | 是 | 对应提交 ID（即主键 + 外键） |
| total_score | number | 是 | 总分（可能浮点） |
| max_score | number | 是 | 满分（冗余保存） |
| overall_comment | string | 是 | 总体评价 |
| detailed_feedback | array[FeedbackItem] | 是 | 题目级或片段级反馈 |
| suggestions | array[string] | 是 | 建议列表（学习改进） |
| corrected_at | Timestamp | 是 | 批改完成时间 |
| ai_metadata | JsonObject / null | 是 | AI 处理相关信息（tokens / model 等） |

FeedbackItem：
| 字段 | 类型 | 说明 |
|------|------|------|
| item_index | integer | 题目序号或段落序号 |
| score | number | 实际得分 |
| max_score | number | 该小项满分 |
| comment | string | 评语 |
| tags (规划) | array[string] | 分类标签：知识点 / 能力维度 |

### 7.5 学习会话 ChatSession
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 会话主键 |
| user_id | ID | 否 | 发起用户 |
| subject | string / null | 否 | 学科分类（可选） |
| title | string / null | 否 | 会话标题（可由首个问题生成） |
| status | string(enum) | 是 | active / archived / closed |
| created_at | Timestamp | 是 | 创建时间 |
| updated_at | Timestamp | 是 | 最近交互时间 |
| question_count | integer | 是 | 问题数量（可冗余） |
| metadata | JsonObject / null | 否 | 扩展（设备/上下文版本等） |

### 7.6 问题 Question
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 问题主键 |
| session_id | ID | 否 | 所属会话 |
| user_id | ID | 否 | 发起用户 ID |
| content | string | 否 | 问题内容（原始文本） |
| subject | string / null | 否 | 学科标签 |
| created_at | Timestamp | 是 | 创建时间 |
| answer_id | ID / null | 是 | 已关联回答（若存在） |
| metadata | JsonObject / null | 否 | 扩展（例如来源渠道） |

### 7.7 回答 Answer
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 回答主键 |
| question_id | ID | 否 | 关联问题 |
| session_id | ID | 否 | 会话冗余（便于查询性能） |
| answer | string | 否 | 回答内容（富文本/Markdown 待定） |
| sources | array[AnswerSource] / null | 否 | 来源引用（规划） |
| confidence_score | number (0~1) | 否 | AI 置信度 |
| response_time_ms | integer | 是 | 生成耗时（毫秒） |
| created_at | Timestamp | 是 | 创建时间 |
| ai_metadata | JsonObject / null | 是 | 模型/参数摘要（用于调试） |

AnswerSource（规划）：
| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | source 类型：document / knowledge_base / snippet |
| reference | string | 引用标识（ID/URL） |
| snippet | string | 摘要内容 |
| score | number | 相关性评分（可选） |

### 7.8 文件 FileInfo
| 字段 | 类型 | 只读 | 说明 |
|------|------|------|------|
| id | ID | 是 | 文件 ID |
| original_filename | string | 否 | 原始文件名 |
| stored_filename | string | 是 | 存储文件名（内部） |
| content_type | string | 是 | MIME 类型 |
| size | integer | 是 | 字节大小 |
| category | string / null | 否 | 业务分类：homework / material 等 |
| description | string / null | 否 | 描述 |
| download_url | string | 是 | 下载路径（相对或绝对） |
| preview_url | string / null | 是 | 预览路径（若适用） |
| uploaded_at | Timestamp | 是 | 上传时间 |
| download_count | integer | 是 | 下载次数（可延迟更新） |
| checksum (规划) | string | 用于内容校验 |
| storage_backend (规划) | string | local / oss / s3 |

---

## 8. 学情分析相关（规划）

拟引入结构（示意）：
### LearningOverview
| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | ID | 用户 |
| period_days | integer | 统计窗口 |
| total_questions | integer | 问题总数 |
| active_days | integer | 活跃日数 |
| avg_questions_per_day | number | 平均每日提问数 |
| mastery (规划) | array[TopicMastery] | 知识点掌握情况 |
| suggestions | array[string] | 提示/建议文本 |

### TopicMastery
| 字段 | 类型 | 说明 |
|------|------|------|
| topic | string | 知识点 |
| mastery_score | number(0~1) | 掌握度 |
| confidence | number(0~1) | 推断置信度 |
| evidence (规划) | array[string] | 支撑样本引用 |

---

## 9. AI 相关扩展字段说明

| 字段 | 场景 | 说明 |
|------|------|------|
| ai_metadata | 回答/批改 | 内含模型名称、tokens 使用、内部 trace_id |
| confidence_score | 回答 | 非绝对准确性，只作参考 |
| response_time_ms | 回答/批改 | 从请求到结果生成的耗时 |
| sources (规划) | 回答 | 用于解释性和可追溯 |
| suggestions | 批改/分析 | AI 给出的提升建议语句列表 |

> 注意：AI 生成结果可能存在误差，应在前端展示“AI 辅助”提示。

---

## 10. 统一字段语义规范

| 字段 | 语义约定 |
|------|----------|
| created_at | 资源初次持久化时间 |
| updated_at | 资源最近一次可见属性更新 |
| submitted_at | 作业提交时间 |
| completed_at | 作业批改完成时间 |
| corrected_at | 批改结果生成时间（与 completed_at 可关联） |
| status | 需枚举列表集中管理 |
| metadata | 不影响业务主干的扩展信息（结构受限，避免滥用） |

---

## 11. 示例对象

作业批改结果示例：
```json
{
  "success": true,
  "data": {
    "submission_id": "9d5e8ab1-...",
    "total_score": 85,
    "max_score": 100,
    "overall_comment": "整体表现良好，语法基本正确。",
    "detailed_feedback": [
      { "item_index": 1, "score": 8, "max_score": 10, "comment": "回答完整" },
      { "item_index": 2, "score": 7, "max_score": 10, "comment": "逻辑略简略" }
    ],
    "suggestions": [
      "加强对关键概念的举例说明",
      "复习第二题相关章节"
    ],
    "corrected_at": "2025-09-29T12:40:13Z",
    "ai_metadata": {
      "model": "bailian-x",
      "prompt_tokens": 512,
      "completion_tokens": 238,
      "latency_ms": 1732
    }
  }
}
```

学习问答响应示例：
```json
{
  "success": true,
  "data": {
    "question_id": "q_123",
    "answer": "质数是大于 1 且只能被 1 和自身整除的自然数。",
    "confidence_score": 0.94,
    "session_id": "sess_abcd",
    "response_time_ms": 842,
    "created_at": "2025-09-29T12:50:00Z"
  }
}
```

---

## 12. 兼容与演进策略

| 场景 | 策略 |
|------|------|
| 新增字段 | 直接添加（必须为可选或有默认语义） |
| 字段弃用 | 标记 deprecated（规划：通过元信息返回） |
| 字段重命名 | 旧字段保留一段周期 + 新字段并行 |
| 字段移除 | 需在 CHANGELOG 标记 + 弃用期结束后删除 |
| 枚举扩展 | 直接添加（前端需兼容未知值） |
| 结构变更 | 必要时通过新端点或 API 版本升级 |
| 精度变更 | 不直接更改类型（改名 + 新字段） |
| 语义变更 | 文档高亮 + 需要版本号或明确发布说明 |

---

## 13. 未来扩展占位

| 模块 | 可能增加 |
|------|----------|
| 用户 | 头像字段 / 状态标记 / 角色权限分组 |
| 作业 | 批改进度轮询状态 / 异步任务追踪 ID |
| AI 回答 | 追踪引用 / 反事实解释（Explainability） |
| 学情分析 | 成长曲线 / 警示阈值 / 指标标签体系 |
| 多媒体 | OCR 解析结构 / 图片批注坐标 |
| 国际化 | 字段本地化支持（多语言） |
| 安全 | 内容审核标记（is_flagged / violation_tags） |

---

## 14. 修订日志（本文件）
| 日期 | 版本 | 变更 | 描述 | 责任人 |
|------|------|------|------|--------|
| 2025-09-29 | draft-1 | 初稿 | 结构与核心模型列出 | 文档重构 |
| (待填) | ... | ... | ... | ... |

---

## 15. TODO 列表
| 项 | 优先级 | 说明 |
|----|--------|------|
| 字段与实际代码核对 | P0 | 逐模型对齐 Pydantic / ORM |
| errors.md 拆分 | P0 | 错误码单独文档 |
| 分页统一 Schema 实现 | P0 | 与返回包装整合 |
| AI sources 结构落地 | P1 | 增加来源引用可靠性 |
| 学情分析模型实装 | P1 | 与统计仓储输出对齐 |
| 复杂评分 rubric 结构化 | P1 | 批改 criteria 标准化 |
| 幂等性 idempotency-key 约定 | P2 | 适配重复请求 |
| 元数据字段白名单策略 | P2 | 防滥用 metadata |
| 字段 deprecate 机制 | P2 | 增加元信息 |
| SDK 自动生成适配 | P3 | 结构映射生成 |
| 模型差异检测脚本 | P3 | 防止代码与文档漂移 |

---

反馈或修订：请提 Issue 标记 `api-models`，说明：
1. 模型名称
2. 字段差异或缺失
3. 建议修改方案
4. 兼容性评估（是否为破坏性）

（END）

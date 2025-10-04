# 五好伴学前后端协作与集成指南 (FRONTEND-INTEGRATION)

Last Updated: 2025-09-29
适用范围：Web 前端（Vue3 + TS）与后端 `/api/v1` 版本（0.1.x 内测阶段，API 尚未冻结）

> 目的：为前端工程提供一份“接口调用 + 状态处理 + 错误展示 + 性能/安全约定”统一规范，减少沟通成本，避免各自实现分叉逻辑。
> 若本文件与 `api/overview.md` / `api/endpoints.md` / `api/models.md` 不一致，以后者为数据定义来源，并需提 PR 同步修正。

---

## 目录

1. 集成总览
2. 环境配置与运行约定
3. API 基础封装建议
4. 认证与会话管理（规划）
5. 错误处理与 UI 反馈模式
6. 限流与重试策略
7. 分页 / 搜索 / 排序统一约定
8. 数据缓存与状态管理策略
9. 提交与乐观更新（场景建议）
10. 文件上传与进度展示
11. AI 交互体验规范（问答 / 批改）
12. 性能优化与请求合并策略
13. 安全与合规注意事项
14. 日志 / 埋点 / 分析（前端侧）
15. 版本兼容与接口变更跟踪
16. 前端单元 / 集成测试建议
17. 常见交互模式清单
18. 问题排查指南（前端 → 后端）
19. 协作流程（需求 → 对接 → 验证）
20. TODO / 规划项
21. 变更记录

---

## 1. 集成总览

| 项目 | 当前值 | 说明 |
|------|--------|------|
| API Base URL (dev) | `http://localhost:8000/api/v1` | 本地默认 |
| API Base URL (prod 规划) | `https://api.wuhao-tutor.com/api/v1` | 待域名与网关 |
| Auth 方式 | （规划）Bearer JWT | 暂未强制 |
| 响应包装 | `{ success, data, error? }` | 全局统一 |
| 错误码来源 | `api/errors.md` | 枚举与语义 |
| 限流维度 | per_ip / per_user / ai_service / login | 影响 UI 反馈 |
| 超时建议 | 普通 10s / AI 30s | 超时提示分类 |
| 可观测端点 | `/api/v1/health/*` | Dev 调试与本地面板 |

---

## 2. 环境配置与运行约定

前端 `.env.*` 中建议变量：
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_ENV=development
VITE_ENABLE_API_LOG=true
VITE_AI_ASK_TIMEOUT_MS=30000
VITE_DEFAULT_PAGE_SIZE=20
```

环境差异：
| 环境 | 行为 | 注意 |
|------|------|------|
| dev | 宽松 CORS / 可匿名测试 | 不要假设无鉴权逻辑 |
| staging (规划) | 生产镜像 + 测试数据 | 验证限流 / 安全头 |
| prod | 完整鉴权 / 限流严格 | 使用标准错误提示策略 |

---

## 3. API 基础封装建议

核心模块结构（示例）：
```
api/
  http.ts          # 基础实例（fetch / axios 二选一）
  interceptors.ts  # 请求/响应拦截
  auth.ts          # 认证相关
  homework.ts      # 作业批改模块
  learning.ts      # 学习问答模块
  files.ts         # 文件上传/下载
  analysis.ts      # 学情分析（规划）
  health.ts        # 健康/监控（调试）
  types.ts         # 公共类型定义
```

推荐封装要点：
- 统一 `request<T>` 函数：处理包装结构与错误态映射。
- 响应中 `success=false` 仍要抛出自定义错误对象（保持调用层逻辑清晰）。
- 增加“幂等占位”参数（未来 POST 幂等支持）。

示例接口调用（伪 TypeScript）：
```ts
async function apiRequest<T>(path: string, options: RequestInit & { skipAuth?: boolean } = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token && !options.skipAuth ? { Authorization: `Bearer ${token}` } : {})
    },
    ...options
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok || !json.success) {
    throw mapApiError(res.status, json?.error);
  }
  return json.data as T;
}
```

---

## 4. 认证与会话管理（规划）

| 方面 | 初期做法 | 稳定后规划 |
|------|----------|-----------|
| 登录流程 | 临时开放（无 token） | 登录接口 + JWT access + refresh |
| Token 存储 | - | 内存（优先）+ 刷新时旋转 |
| 失效处理 | 统一监听 401 | 刷新/跳转登录 |
| 权限控制 | 前端基于角色字段 | 后端补增资源属主校验 |
| “我”信息缓存 | 请求 `/auth/me` | Pinia/Store 缓存 + 过期策略 |

状态码 → 前端处理：
| 状态码 | 动作 |
|--------|------|
| 401 | 清理本地状态，跳转登录页 |
| 403 | Toast：“无权限执行该操作” |
| 419/498（规划） | Token 已失效，需要刷新 |

---

## 5. 错误处理与 UI 反馈模式

统一错误对象结构（前端映射）：
```
interface AppError {
  httpStatus: number;
  code: string;          // error.code
  message: string;       // 可展示（中文）
  details?: Record<string, any>;
  traceId?: string;      // 规划：后端响应头
  retryable?: boolean;   // 派生属性
}
```

UI 展示策略（示例）：
| 错误码 | 展示方式 | 附加操作 |
|--------|----------|----------|
| VALIDATION_ERROR | 表单字段高亮 | 滚动到首个错误 |
| RATE_LIMIT_EXCEEDED | 顶部警告条 + 剩余时间 | 递减计时/按钮禁用 |
| RESOURCE_NOT_FOUND | 页面级空态 | “返回上一页”按钮 |
| AUTH_INVALID_CREDENTIALS | 登录表单内提示 | 清空密码框 |
| AI_SERVICE_FAILURE | 气泡/对话内条目标红 | “重试”按钮 |
| INTERNAL_SERVER_ERROR | 全局 Toast | 引导重试/反馈 |
| FILE_TYPE_NOT_ALLOWED | 上传控件内赤色标记 | 显示允许列表 |
| BUSINESS_RULE_VIOLATION | Toast + 按钮失效 | 引导用户修正 |

错误优先级（影响埋点/日志）：
| 级别 | 错误码示例 | 是否上报 |
|------|-------------|----------|
| critical | INTERNAL_SERVER_ERROR / DATA_INTEGRITY_ERROR | 是 |
| warning | RATE_LIMIT_EXCEEDED / AI_SERVICE_FAILURE | 是 |
| info | VALIDATION_ERROR / RESOURCE_NOT_FOUND | 可选 |
| silent | 用户取消 / 前端拦截 | 否 |

---

## 6. 限流与重试策略

| 场景 | 建议 |
|------|------|
| 普通接口 429 | 等待 `Retry-After` 或静默 3~5s 再试 |
| AI 接口 429 | 显示“请求频率过快”提示，5s 按钮冷却 |
| 网络超时 | 普通接口重试 1 次；AI 接口不自动重试 |
| 幂等重试（规划） | 提供 `Idempotency-Key` 头配合后端 |
| 登录限流 | 超 3 次提示“稍后再试” |

针对频繁触发的 429：
- 增加前端自适应节流（如 ask 频率 2 秒一次）
- 记录最近失败时间，避免瞬时多次调用 API 相同端点

---

## 7. 分页 / 搜索 / 排序统一约定

| 规则 | 描述 |
|------|------|
| 分页参数 | `?limit=20&offset=0`；超出范围返回空列表 |
| 返回结构 | `{ items, total?, limit, offset, has_more }` |
| 排序参数 | `?order_by=created_at` 或 `?order_by=-created_at` |
| 搜索参数 | `?search=关键字`（后端配置有限字段） |
| 多过滤组合 | 简单键值：`?status=active&subject=math` |
| 保留滚动位置 | 使用 `keep-alive` + `cursor key`（未来游标分页） |
| 空态处理 | “无记录”展示 + CTA（如“创建模板”） |

前端封装：
```ts
async function fetchPaged<T>(path: string, params: { limit?: number; offset?: number; [k: string]: any }) {
  const query = new URLSearchParams({ limit: String(params.limit ?? 20), offset: String(params.offset ?? 0), ...params });
  return apiRequest<Paginated<T>>(`${path}?${query.toString()}`);
}
```

---

## 8. 数据缓存与状态管理策略

| 数据类型 | 缓存策略 | 失效触发 |
|----------|----------|----------|
| 当前用户信息 | 登录后获取，内存缓存 | 退出登录 |
| 会话列表 | 分页缓存（按 offset） | 新建会话 / 删除会话 |
| 问答历史 | 每会话独立存储 | 新问题/回答时 append |
| 作业模板列表 | 短期内存（5 分钟） | 新建/更新/删除模板 |
| 批改结果 | 根据 submission_id 缓存 | 强制刷新按钮 |
| 健康/性能数据 | 不缓存（调试页面） | - |

建议：使用 `Map<string, { data: T; ts: number }>` 简易缓存结构；或集成 SWR / React Query 类似逻辑思想（Vue 生态可手写 composable）。

---

## 9. 提交与乐观更新（场景建议）

| 场景 | 是否适合乐观更新 | 策略 |
|------|------------------|------|
| 提交作业 | 否 | 需等待后端校验/文件成功 |
| 修改模板标题 | 是 | UI 先更新 → 失败回滚 |
| 创建会话 | 是（避免初次空白闪烁） | 临时 ID → 成功后替换真实 ID |
| 删除文件 | 是 | 标记删除状态→失败恢复 |
| AI 问答 | 否（需等待 answer） | 可显示“生成中 …”占位条目 |

---

## 10. 文件上传与进度展示

建议流程：
1. 用户选择文件 → 校验扩展名与大小（前端先行）
2. 进度条（使用 `XMLHttpRequest` 或 fetch + streams polyfill）
3. 成功：加入文件列表并允许预览
4. 失败：分类文案（大小 / 类型 / 网络 / 429）

错误映射：
| 前端错误 | 说明 |
|----------|------|
| size_exceeded | 大于前端限制（与后端最大阈值同步） |
| type_unsupported | 不在白名单 |
| upload_aborted | 用户取消 |
| server_rejected | 返回非 success |
| network_failure | 超时 / 掉线 |

---

## 11. AI 交互体验规范（问答 / 批改）

| 交互阶段 | UI 提示 | 注意 |
|----------|---------|------|
| 发送中 | 在对话流中插入“思考中...”气泡 | 禁止重复发送（禁用按钮） |
| 完成 | 替换占位气泡 → 渲染回答 | 支持复制 / 反馈按钮（规划） |
| 失败 | 气泡内红框 + “重试”按钮 | 错误码区分：网络 / AI / 限流 |
| 多轮上下文 | 依赖 session_id | 超限策略：截断前历史（后端统一） |
| 批改等待 | 显示“排队/分析中”状态 | 若异步化会加入轮询（规划） |

并发控制：
- 同一个会话同时只能有一个进行中的 AI 请求。
- 若用户快速连续点击发送：前端节流 + 提示。

---

## 12. 性能优化与请求合并策略

| 优化点 | 说明 |
|--------|------|
| 请求合并 | 同一时刻重复发起同一 GET（如会话列表）→ 使用飞行中 Promise 复用 |
| 去抖动 | 搜索输入框 300ms 去抖后请求 |
| 预取 | 用户打开“作业列表”时预取最近批改结果摘要 |
| 分块加载 | 问答历史分页加载，上滑加载更多 |
| 渐进渲染 | 优先渲染结构骨架 → 填充数据 |
| 缓存失效 | 修改依赖某列表的数据后精准失效指定 key |
| 大量数据 | 表格虚拟滚动（学情分析未来可能使用） |

---

## 13. 安全与合规注意事项（前端）

| 项目 | 要求 |
|------|------|
| 不在源码硬编码密钥 | 所有敏感值通过环境变量或后端请求获取 |
| 不信任后端自由文本 | 避免 `v-html` 注入未净化内容 |
| Token 存储 | 优先内存或受保护 Cookie；避免 LocalStorage 长期保存（规划阶段灵活） |
| 防调试敏感信息 | 生产构建禁用详细日志 (`VITE_ENABLE_API_LOG=false`) |
| 防重复提交 | 表单提交按钮提交中禁用 |
| 处理 429 | 正确告知用户等待而不是无限重试 |
| 下载文件 | 使用受控可选 `blob` 流处理，避免 URL 注入 |
| 依赖第三方脚本 | 严格审查来源与版本锁定 |
| Console 输出 | 不输出 token/原始错误堆栈（生产） |

---

## 14. 日志 / 埋点 / 分析（前端侧）

| 事件类型 | 字段建议 | 目的 |
|----------|----------|------|
| api_request | endpoint, method, duration, success, code | 性能与故障分析 |
| ai_interaction | session_id, latency, success, error_code | AI 质量与体验 |
| rate_limit_hit | scope, endpoint | 行为与配额策略调优 |
| file_upload | type, size, success | 文件类型分布 |
| page_view | route, ts | 使用趋势（可选） |
| error_displayed | code, ui_component | UI 错误覆盖检测 |

埋点上报节流：
- 聚合 30 秒批量发送
- 或关键事件即时上报（AI 失败、严重错误）

---

## 15. 版本兼容与接口变更跟踪

| 类型 | 前端应对策略 |
|------|--------------|
| 新增字段 | 默认兼容（忽略未知字段） |
| 删除字段 | 发布前检测：若依赖则同步改动 UI |
| 改字段语义 | 后端需在变更说明中标记，前端预期跟随（发布前回归） |
| 新增错误码 | 回退到默认错误展示（未映射） |
| 端点路径变更 | 提前提供两个版本重叠期（规划） |
| API v2 引入 | 提供多 baseURL 适配层 |

---

## 16. 前端测试建议

| 测试层 | 内容 | 工具 |
|--------|------|------|
| 单元 | API 封装 / 错误映射 | Vitest |
| 组件 | 表单校验 / 空态 / 错误态渲染 | Vue Test Utils |
| 集成（Mock） | 问答提交流程 / 模板 CRUD | Mock Service Worker (MSW) |
| 合同（契约） | 响应结构快照（与 models.md 对齐） | 规划：生成类型 |
| 性能（轻量） | 列表渲染 100+ 行 | 自定义脚本 |
| 可访问性（a11y） | 关键交互（按钮/对话框） | axe-core（可选） |

---

## 17. 常见交互模式清单

| 模式 | UI 要求 | 技术点 |
|------|---------|--------|
| 列表加载中 | Skeleton 或占位条目 | 防闪烁 |
| 分页加载更多 | “加载更多”按钮 / 无限滚动 | 去重处理 |
| 表单校验失败 | 内联+顶部合并错误概览 | focus 第一错误 |
| 提交中状态 | 按钮 loading + 防连点 | 全局节流 |
| 重试按钮 | AI / 网络错误特有 | 导致请求重新发起 |
| 空态 | 指引 + CTA | 允许“刷新”操作 |
| 危险操作 | 二次确认弹窗 | 规划：统一 Confirm 组件 |
| 上下文会话切换 | 当前会话高亮 | 懒加载右侧内容 |
| 批改结果细节折叠 | 点开反馈项 | 虚拟列表可选 |
| 文件拖拽上传 | 拖入区域高亮 | MIME 再校验 |

---

## 18. 问题排查指南（前端 → 后端）

| 症状 | 排查步骤 | 可能原因 |
|------|----------|----------|
| 所有请求失败 | 检查 baseURL / 控制台 CORS | 跨域 / 服务未启动 |
| 部分 401 | 确认鉴权是否启用 / token 是否注入 | Token 过期 / 未登录 |
| AI 响应超时 | 控制台耗时日志 / 后端性能端点 | 外部模型延迟 |
| 429 高频 | 控制台统计触发接口 | 前端缺节流 |
| 列表重复数据 | 查看 offset 与分页缓存 | 未清理缓存或分页参数错误 |
| 文件预览失败 | 响应类型 / Content-Type | URL 失效 / 权限 |
| JSON 解析错误 | 后端返回非 JSON | 服务异常返回 HTML 等 |
| P95 延迟高 | 采集 local 端点延迟对比 | 网络/后端压测阶段 |

---

## 19. 协作流程（需求 → 对接 → 验证）

| 阶段 | 动作 | 输出 |
|------|------|------|
| 需求澄清 | 定义交互 / 状态 / 边界 | 界面稿 / 交互说明 |
| 模型确认 | 字段核对 `api/models.md` | 差异清单 / 新增需求 |
| 接口差异评审 | 需要新增/调整端点 | PR 规划 / 后端评估 |
| Mock 阶段 | 前端本地假数据联调 | Mock 模块 / Storybook |
| 真机联调 | 切换真实 API | Bug 列表 / 性能观测 |
| 验收 | 流程回放与边界测试 | 通过清单 |
| 上线前检查 | 错误态/限流/超时/回滚 UI | 验证报告 |
| 版本冻结 | 锁定接口使用范围 | CHANGELOG 条目 |

---

## 20. TODO / 规划项

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 认证集成与 token 刷新 | P0 | 需后端支持 |
| 错误码 → 文案映射表配置化 | P0 | 多语言准备 |
| AI 请求取消（AbortController） | P1 | 用户手动中断 |
| 幂等键支持（POST 重试） | P1 | 批改/提交接口 |
| 合同测试生成（OpenAPI → TS） | P1 | 保证类型同步 |
| 指标面板（本地调试页） | P2 | 显示健康/性能 |
| 前端限流软警告浮层 | P2 | 接近阈值先提示 |
| 文件秒传（哈希校验） | P3 | 减少重复上传 |
| 问答流式响应（规划） | P3 | 增强交互体验 |
| AI 来源引用展示 | P3 | 需后端 sources 字段 |
| 前后端同步 Trace-ID | P3 | 日志追踪 |

---

## 21. 变更记录

| 日期 | 版本 | 变更 | 说明 |
|------|------|------|------|
| 2025-09-29 | draft-1 | 初稿 | 文档重构阶段创建 |
| (待填) | ... | ... | ... |

---

## 结语

本指南为“活体文档”：
- 新增模块、端点、错误码、响应模型等，需要判断是否影响本文件。
- 发现与当前实现不符（或前端出现大量重复代码绕过规范）应及时创建 Issue。
- 优先遵循“约定优于重复讨论”：未特殊说明的交互，按本文件既定模式执行。

反馈标签建议：`frontend-integration`。

（END）

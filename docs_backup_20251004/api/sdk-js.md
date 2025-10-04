# 五好伴学 JavaScript / TypeScript SDK 使用指南 (sdk-js.md)

_Last Updated: 2025-09-29_
_适用后端 API：/api/v1 （内部迭代阶段，尚未冻结）_
_状态：初稿（等待端点、错误码、模型进一步核对）_

---

## 1. 目标

为 Web / Node.js / 前端工程提供统一、轻量、可扩展的 API 访问封装，减少以下重复性工作：

| 需求 | 本 SDK 目标 |
|------|-------------|
| 统一请求封装 | 基于 fetch / 可替换传输层 |
| 错误处理 | 标准化 error.code / HTTP 状态封装 |
| 限流与重试 | 提供策略插拔点（初版手动） |
| 分页遍历 | 提供统一迭代器工具 |
| TypeScript 类型 | 对应 `api/models.md` 数据模型 |
| 可观测 | 钩子收集调用耗时、错误分布 |
| 幂等与扩展 | 预留 Idempotency-Key 支持 |
| 灵活运行环境 | 浏览器 / Node / SSR / Edge Runtime |

---

## 2. 安装（规划与当前用法）

当前未发布 NPM 包，可直接将示例文件 `wuhao-sdk.js` / `wuhao-sdk.ts` 拷贝至工程。

未来（规划）：
```bash
npm install @wuhao-tutor/sdk
# 或
pnpm add @wuhao-tutor/sdk
# 或
yarn add @wuhao-tutor/sdk
```

---

## 3. 运行环境兼容性

| 环境 | 支持情况 | 说明 |
|------|----------|------|
| 浏览器（现代） | ✅ | 使用原生 fetch |
| Node.js ≥ 18 | ✅ | 内置 fetch (或 node-fetch/polyfill) |
| Edge / Cloudflare Workers | ✅ (需避免 Node 专属 API) |
| React / Vue SPA | ✅ | 可直接在 service 层使用 |
| SSR (Next.js) | ✅ | 注意避免在服务端缓存用户令牌 |
| 小程序（需适配） | 🧩 规划 | 可注入自定义 fetch 实现 |

---

## 4. 快速上手

```ts
import { WuhaoClient } from './wuhao-sdk';

const client = new WuhaoClient({
  baseURL: 'http://localhost:8000/api/v1',
  token: 'your-token-if-enabled'
});

async function main() {
  const answer = await client.learning.askQuestion({
    question: '什么是质数？'
  });
  console.log(answer.answer, answer.confidence_score);
}

main();
```

---

## 5. 核心设计原则

| 原则 | 体现 |
|------|------|
| 可分层 | 模块：auth / homework / learning / files / health |
| 最小内核 | 只有 HTTP 包装 + 错误转换 + 可选重试 |
| 副作用外置 | 不做本地存储/缓存；调用者决定 |
| 类型安全 | TS：接口 + 类型守卫；JS：JSDoc 提示 |
| 易扩展 | 钩子（onRequest / onResponse / onError） |
| 不入侵 | 不绑定框架（React/Vue），只提供纯函数接口 |
| 可观测 | 预留 metrics 收集点 |
| 渐进增强 | 初版不强制重试/幂等，后续可插入策略模块 |

---

## 6. 基础类型（与 models.md 对应的简化版）

> 最终以 `api/models.md` 为权威；此处仅列使用频率高的子集，后续通过代码生成或手动同步。

```ts
export interface AskQuestionRequest {
  question: string;
  session_id?: string;
  subject?: string;
}

export interface AskQuestionResponse {
  question_id: string;
  answer: string;
  confidence_score?: number;
  session_id?: string;
  response_time_ms?: number;
  created_at: string;
}

export interface HomeworkSubmissionCreate {
  template_id: string;
  content_text?: string;
  file_url?: string;
}

export interface HomeworkSubmissionOut {
  id: string;
  template_id: string;
  status: 'submitted' | 'correcting' | 'corrected' | 'failed';
  submitted_at: string;
  completed_at?: string | null;
}

export interface Paginated<T> {
  items: T[];
  total?: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface APIErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIErrorResponse {
  success: false;
  error: APIErrorPayload;
}

export interface APISuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

export type APIResponse<T> = APISuccessResponse<T> | APIErrorResponse;
```

---

## 7. 错误体系

| 类 | 场景 |
|----|------|
| `APIHttpError` | 业务/协议错误（已收到服务端 JSON） |
| `TransportError` | 网络失败 / 超时 / 非 2xx 且未返回结构化 JSON |
| `SDKConfigError` | 初始参数非法（baseURL 缺失等） |
| `SerializationError` | JSON 解析失败 |

错误对象公共字段：
```ts
interface WuhaoError extends Error {
  name: string;
  cause?: unknown;
}

class APIHttpError extends Error {
  status: number;
  code: string;
  details?: Record<string, unknown>;
}
```

---

## 8. 最小实现（参考示例）

```ts
// wuhao-sdk.ts (示例片段，可直接复制使用)
export interface WuhaoClientOptions {
  baseURL: string;
  token?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
  headers?: Record<string, string>;
  onRequest?: (ctx: { method: string; url: string; body?: any }) => void;
  onResponse?: (ctx: { method: string; url: string; status: number; elapsedMs: number }) => void;
  onError?: (ctx: { error: unknown; method: string; url: string }) => void;
  retry?: {
    enabled: boolean;
    retries: number;
    backoffBaseMs: number;
    retryOnCodes?: number[];
  };
}

class TransportError extends Error {}
class APIHttpError extends Error {
  status: number;
  code: string;
  details?: Record<string, unknown>;
  constructor(status: number, code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'APIHttpError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export class WuhaoClient {
  private baseURL: string;
  private token?: string;
  private timeoutMs: number;
  private fetchImpl: typeof fetch;
  private hooks: WuhaoClientOptions;
  private retryCfg: Required<WuhaoClientOptions['retry']>;

  constructor(opts: WuhaoClientOptions) {
    if (!opts.baseURL) throw new Error('baseURL 不能为空');
    this.baseURL = opts.baseURL.replace(/\/+$/, '');
    this.token = opts.token;
    this.timeoutMs = opts.timeoutMs ?? 15000;
    this.fetchImpl = opts.fetchImpl ?? fetch;
    this.hooks = opts;
    this.retryCfg = {
      enabled: opts.retry?.enabled ?? false,
      retries: opts.retry?.retries ?? 2,
      backoffBaseMs: opts.retry?.backoffBaseMs ?? 300,
      retryOnCodes: opts.retry?.retryOnCodes ?? [429, 502, 503, 504],
    };
  }

  setToken(token: string | undefined) {
    this.token = token;
  }

  private buildHeaders(extra?: Record<string, string>): Record<string, string> {
    const base: Record<string, string> = {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(this.hooks.headers || {}),
    };
    if (this.token) base.Authorization = `Bearer ${this.token}`;
    return { ...base, ...(extra || {}) };
  }

  private async coreFetch(
    method: string,
    path: string,
    body?: unknown,
    params?: Record<string, any>
  ): Promise<any> {
    const url = this.composeURL(path, params);
    const payload = body == null ? undefined : JSON.stringify(body);
    const headers = this.buildHeaders();

    this.hooks.onRequest?.({ method, url, body });

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    const started = performance.now?.() ?? Date.now();

    let resp: Response;
    try {
      resp = await this.fetchImpl(url, {
        method,
        headers,
        body: payload,
        signal: controller.signal,
      });
    } catch (e) {
      clearTimeout(timer);
      this.hooks.onError?.({ error: e, method, url });
      throw new TransportError(`网络错误或超时: ${(e as Error).message}`);
    } finally {
      clearTimeout(timer);
    }

    const elapsed =
      (performance.now?.() ?? Date.now()) - started;
    this.hooks.onResponse?.({ method, url, status: resp.status, elapsedMs: elapsed });

    let json: any = null;
    const text = await resp.text().catch(() => '');

    if (text) {
      try {
        json = JSON.parse(text);
      } catch {
        // 非 JSON 返回
      }
    }

    if (!resp.ok || !json?.success) {
      // 标准错误结构
      if (json?.error) {
        throw new APIHttpError(
          resp.status,
          json.error.code || 'UNKNOWN_ERROR',
            json.error.message || `Request failed (${resp.status})`,
            json.error.details
        );
      }
      throw new APIHttpError(
        resp.status,
        'HTTP_ERROR',
        `HTTP ${resp.status}`,
        { raw: text.slice(0, 500) }
      );
    }
    return json.data;
  }

  private composeURL(path: string, params?: Record<string, any>) {
    const p = new URL(this.baseURL + (path.startsWith('/') ? path : `/${path}`));
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) p.searchParams.set(k, String(v));
      });
    }
    return p.toString();
  }

  private async request<T>(
    method: string,
    path: string,
    opts: {
      body?: any;
      params?: Record<string, any>;
    } = {}
  ): Promise<T> {
    const { enabled, retries, backoffBaseMs, retryOnCodes } = this.retryCfg;

    let attempt = 0;
    let lastErr: unknown;

    while (true) {
      try {
        return await this.coreFetch(method, path, opts.body, opts.params);
      } catch (err) {
        lastErr = err;
        const isRetriable =
          enabled &&
          err instanceof APIHttpError &&
          retryOnCodes.includes(err.status) &&
          attempt < retries;

        if (!isRetriable) throw err;
        const backoff = backoffBaseMs * Math.pow(2, attempt);
        await new Promise(r => setTimeout(r, backoff));
        attempt += 1;
      }
    }
  }

  // ---- 模块分发封装 ----
  readonly learning = {
    askQuestion: (payload: AskQuestionRequest) =>
      this.request<AskQuestionResponse>('POST', '/learning/ask', { body: payload }),

    listSessions: (opts: { limit?: number; offset?: number } = {}) =>
      this.request<Paginated<any>>('GET', '/learning/sessions', {
        params: { limit: opts.limit ?? 20, offset: opts.offset ?? 0 },
      }),
  };

  readonly homework = {
    createSubmission: (payload: HomeworkSubmissionCreate) =>
      this.request<HomeworkSubmissionOut>('POST', '/homework/submissions', { body: payload }),

    getCorrection: (submissionId: string) =>
      this.request<any>('GET', `/homework/corrections/${submissionId}`),
  };

  readonly files = {
    list: (opts: { category?: string; limit?: number; offset?: number } = {}) =>
      this.request<Paginated<any>>('GET', '/files', {
        params: { category: opts.category, limit: opts.limit ?? 20, offset: opts.offset ?? 0 },
      }),
  };

  readonly health = {
    basic: () => this.request<any>('GET', '/health'),
    performance: () => this.request<any>('GET', '/health/performance'),
    rateLimits: () => this.request<any>('GET', '/health/rate-limits'),
  };
}
```

---

## 9. 分页迭代器辅助

```ts
export async function* paginate<T>(
  fetchPage: (offset: number, limit: number) => Promise<Paginated<T>>,
  pageSize = 50,
  startOffset = 0
): AsyncGenerator<T, void, unknown> {
  let offset = startOffset;
  while (true) {
    const page = await fetchPage(offset, pageSize);
    for (const item of page.items) yield item;
    if (!page.has_more || page.items.length === 0) break;
    offset += pageSize;
  }
}
```

使用：
```ts
for await (const session of paginate(
  (offset, limit) => client.learning.listSessions({ offset, limit })
)) {
  console.log(session);
}
```

---

## 10. 错误处理示例

```ts
try {
  const r = await client.learning.askQuestion({ question: '解释牛顿第二定律' });
  console.log(r.answer);
} catch (e) {
  if (e instanceof APIHttpError) {
    if (e.code === 'RATE_LIMIT_EXCEEDED') {
      // 显示“稍后再试”提示
    } else if (e.status === 404) {
      // 资源不存在
    } else {
      console.warn('业务错误', e.code, e.message);
    }
  } else {
    console.error('网络/其它错误', e);
  }
}
```

---

## 11. 重试策略（当前实现 & 建议）

| 场景 | 是否重试 | 说明 |
|------|----------|------|
| 429 | ✅（默认） | 等待指数退避，可读取 headers（规划扩展） |
| 502 / 503 / 504 | ✅ | 外部依赖瞬时不可用 |
| 500 | ❌ | 避免放大服务端错误 |
| 400 / 401 / 403 / 404 | ❌ | 客户端需修复请求 |
| 网络超时 | ✅ (TransportError)（可选） | 可为超时添加第二策略 |
| AI_SERVICE_FAILURE | ❌（默认） | 避免重复消耗配额，可由调用方决定 |

---

## 12. 幂等与安全（规划接口）

| 功能 | 现状 | 计划 |
|------|------|------|
| Idempotency-Key | 未实现 | `client.request()` 可接受 `idempotencyKey` 头 |
| 自动 Token 续期 | 未实现 | 可在 onError 里拦截 401 调刷新 |
| CSR 防护 | 前端自行处理 | 可通过 headers 注入自定义 CSRF Token |
| 统一 trace-id | 后端支持后从响应头读取 | 透传到下一次请求（可写钩子） |

---

## 13. 性能与可观测性钩子

可通过 options 注册：
```ts
const client = new WuhaoClient({
  baseURL: 'http://localhost:8000/api/v1',
  onRequest: ({ method, url }) => console.debug('[REQ]', method, url),
  onResponse: ({ method, url, status, elapsedMs }) =>
    console.debug('[RES]', method, url, status, elapsedMs + 'ms'),
  onError: ({ error, method, url }) =>
    console.error('[ERR]', method, url, (error as Error).message)
});
```

未来可增加：
- 钩子返回布尔值决定是否拦截 / 重试
- 收集 metrics 上传到监控系统

---

## 14. 与前端状态管理集成建议

| 状态管理 | 建议方式 |
|----------|----------|
| Vue + Pinia | 在 store 中封装业务方法，注入 client |
| React + RTK Query | 自定义 baseQuery 使用 client.request |
| React Query / TanStack Query | 将 `client.*` 方法作为 queryFn |
| SWR | 以 `(key) => client.xxx()` 作为 fetcher |
| 失效缓存 | 错误码 `RESOURCE_NOT_FOUND` → 删除本地缓存条目 |

---

## 15. SSR / 边缘注意

| 场景 | 风险 | 建议 |
|------|------|------|
| SSR 共享 client 单例 | Token 被串用 | 每请求实例化或注入上下文 Token |
| Edge Runtime fetch 限制 | 部分 Node API 不可用 | 不使用 Node 特有模块 |
| 构建 Tree-Shaking | 未分模块 | 未来拆分子入口（/learning 等） |

---

## 16. Roadmap（SDK 演进）

| 版本 (规划) | 内容 | 说明 |
|-------------|------|------|
| 0.1 | 基础请求 + 错误封装 | 当前示例 |
| 0.2 | 幂等键 + 重试策略细分 | 结合后端支持 |
| 0.3 | 自动分页迭代器正式化 | 发布 paginate 工具 |
| 0.4 | Token 刷新机制 Hook | 支持 refresh 回调 |
| 0.5 | 指标收集 + 事件总线 | 观测增强 |
| 0.6 | 代码生成模型绑定 | OpenAPI → TS 类型 |
| 0.7 | 可选持久化层（缓存） | Layer 插件 |
| 1.0 | 稳定发布 / 语义化版本 | 与后端 v1 冻结同步 |

---

## 17. 常见问题 (FAQ)

| 问题 | 解答 |
|------|------|
| 需不需要 axios？ | 不必要，fetch 足够，axios 可自行封装适配器 |
| 浏览器旧环境？ | 需要 polyfill（可用 whatwg-fetch） |
| 上传文件如何处理？ | 使用原生 `FormData`，需单独实现 `client.files.upload(formData)`（本初稿未内置） |
| 如何取消请求？ | 增加 AbortController 支持（在 coreFetch 内部暴露） |
| 支持 WebSocket 吗？ | 当前仅 REST；未来可扩展实时协作模块 |
| 错误信息是否可国际化？ | 服务端返回中文；可在前端建立 code → message 映射表 |

---

## 18. 上传文件建议（扩展示例）

```ts
async function uploadFile(client: WuhaoClient, file: File, extra?: Record<string, any>) {
  const form = new FormData();
  form.append('file', file);
  if (extra) {
    Object.entries(extra).forEach(([k, v]) => form.append(k, String(v)));
  }

  const url = client['composeURL']('/files/upload'); // 或单独实现
  const resp = await fetch(url, {
    method: 'POST',
    headers: client['buildHeaders']({ 'Content-Type': undefined as any }), // 让浏览器自动设置
    body: form
  });

  const json = await resp.json().catch(() => ({}));
  if (!resp.ok || !json.success) {
    throw new APIHttpError(resp.status, json?.error?.code || 'UPLOAD_FAILED', json?.error?.message || '上传失败', json?.error?.details);
  }
  return json.data;
}
```
> 上述访问了内部私有方法，仅作概念展示；正式实现可在 SDK 中添加独立模块 `files.upload()`。

---

## 19. 与错误码 (errors.md) 对齐策略

| 行为 | 要求 |
|------|------|
| 新增后端错误码 | 在 SDK 中不需要更新（除非要做特殊语义处理） |
| 替换旧错误码 | 前端捕获 fallback → 提示“未知错误（请刷新）” |
| 去除错误码 | 迁移期保留兼容分支 |
| 新增限流软告警 | 读取响应头（规划：X-RateLimit-*） |

---

## 20. 质量保证

| 检查项 | 说明 |
|--------|------|
| TypeScript 严格模式 | `strict: true` |
| 构建产物（未来） | ESM + CJS + 类型声明 |
| 单元测试（规划） | 使用 msw / fetch-mock |
| Lint | ESLint + Prettier (printWidth=100) |
| 发布前 | 与 `api/models.md` Diff 检查（脚本化） |
| 兼容回归 | 最低 Node 18 + Chrome 最新主线 |

---

## 21. 迁移/集成建议

| 场景 | 做法 |
|------|------|
| 现有项目已有 axios 封装 | 将 `client.request = (m,p,o)=>axios...`，保持接口一致 |
| 多后端环境（dev/staging/prod） | 外部注入 baseURL；不要在 SDK 内写死 |
| 多租户 Token | 每次请求前 `client.setToken(activeToken)` |
| 并发大量同类请求 | 结合外层队列/并发池（避免触发限流） |

---

## 22. 待办 (TODO)

| 项 | 优先级 | 说明 |
|----|--------|------|
| 与实际端点字段全量核对 | P0 | 逐字段 mapping 校验 |
| 集成统一错误模型守卫 | P0 | 类型缩小 |
| 上传文件官方封装 | P1 | 支持进度事件 |
| 幂等键支持 | P1 | Header: Idempotency-Key |
| Token 自动刷新 Hook | P1 | 封装 refresh 逻辑 |
| 指标钩子说明文档化 | P2 | metrics 上报结构 |
| OpenAPI → 类型生成脚本 | P2 | 防止模型漂移 |
| 分页迭代器添加取消能力 | P2 | abort 支持 |
| WebSocket/实时计划评估 | P3 | 结合学习会话实时性 |
| 单元测试基线 | P3 | 覆盖率 ≥ 70% |
| NPM 发布流程文档 | P3 | 构建/版本/签名 |

---

## 23. 反馈与贡献

| 方式 | 说明 |
|------|------|
| Issue | 标题前缀：`[sdk-js]`，描述环境/复现/期望 |
| PR | 遵循 commit 规范；附破坏性风险说明 |
| 性能问题 | 提供调用模式、频率、复现脚本 |
| 安全问题 | 不在公开 Issue；使用私下渠道（维护者邮箱） |

---

## 24. 免责声明（初版）

本 SDK 仍处于迭代阶段：
- 可能随后端模型变更而调整
- 仅保证在列出的兼容环境下行为稳定
- 不建议直接在生产用户流量大规模集成（直到 v1 稳定标记发布）

---

## 25. 附录：最小 JS 纯函数调用（无需 SDK）

```js
async function askQuestionRaw(baseURL, question, token) {
  const resp = await fetch(`${baseURL.replace(/\/+$/, '')}/learning/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ question })
  });
  const data = await resp.json();
  if (!resp.ok || !data.success) {
    throw new Error(data?.error?.message || `HTTP ${resp.status}`);
  }
  return data.data;
}
```

---

## 26. 修订日志（本文件）

| 日期 | 版本 | 变更 | 说明 |
|------|------|------|------|
| 2025-09-29 | draft-1 | 初稿 | 建立文件骨架与示例 |
| (待填) | ... | ... | ... |

---

_本文件为占位与结构化基线，后续内容将与后端正式冻结的 API / 错误码 / 数据模型同步更新。_

（END）

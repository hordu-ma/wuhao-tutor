# 五好伴学 Python SDK 使用指南 (sdk-python.md)

Last Updated: 2025-09-29
适用 API 版本：v1（内部迭代阶段，未冻结）
状态：初稿（等待与实际端点/错误码对齐）

---

## 1. 目标

本文件提供一个“官方建议实现风格”的 Python 客户端（SDK）示例，帮助：
- 快速调用后端 API（统一封装 HTTP / 重试 / 错误处理）
- 约束请求与返回结构的使用方式
- 演示同步与异步调用模式
- 提供分页 / 限流 / 幂等（规划）扩展点

> 说明：当前 SDK 为“示例 + 约定模板”，尚未发布为 PyPI 包。后续可抽离为独立仓库。

---

## 2. 设计原则

| 原则 | 说明 |
|------|------|
| 轻依赖 | 仅使用 `httpx`（或 `requests`）与标准库 |
| 明确边界 | 不做业务缓存 / 不内嵌持久化 |
| 可测试 | 通过注入 transport/mock 方便测试 |
| 可扩展 | 支持自定义中间件（拦截器） |
| 安全 | 不自动打印敏感信息（token） |
| 清晰错误 | 将 HTTP/业务错误统一转换为清晰异常层次 |
| 可观测 | 预留钩子记录耗时 / 统计调用频率 |
| 渐进增强 | 幂等 / 重试 / 速率自适应 后续逐步加入 |

---

## 3. 安装（示例）

当前项目内联使用，可直接复制 `sdk_client.py`（示例）到本地。
未来（规划）：
```bash
pip install wuhao-tutor-sdk   # (计划)
```

依赖推荐：
```bash
pip install httpx>=0.27.0
```

---

## 4. 最小示例

```python
from sdk_client import WuHaoTutorClient

client = WuHaoTutorClient(
    base_url="http://localhost:8000/api/v1",
    timeout=10,
    token="your-access-token"  # 若已启用认证
)

answer = client.ask_question("什么是质数？")
print(answer.answer, answer.confidence_score)
```

---

## 5. 同步客户端参考实现（示例代码片段）

```python
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

class WuHaoTutorError(Exception):
    """基础异常"""
    pass

class APIHTTPError(WuHaoTutorError):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        super().__init__(f"[{status}][{code}] {message}")
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}

class TransportError(WuHaoTutorError):
    """网络/超时/连接错误"""
    pass

@dataclass
class AskAnswer:
    question_id: str
    answer: str
    confidence_score: float
    session_id: Optional[str]
    response_time_ms: int
    created_at: str

class WuHaoTutorClient:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        timeout: float = 15.0,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = httpx.Client(timeout=timeout)
        self.default_headers = default_headers or {}

    # --- 内部工具 ---
    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "WuhaoTutorPythonSDK/0.1",
            **self.default_headers
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra:
            headers.update(extra)
        return headers

    def _handle_response(self, r: httpx.Response) -> Any:
        try:
            data = r.json()
        except Exception:
            raise TransportError(f"无法解析响应体 (status={r.status_code})")

        if r.status_code >= 400 or not data.get("success", False):
            # 提取标准错误结构
            err = data.get("error") or {}
            raise APIHTTPError(
                status=r.status_code,
                code=err.get("code", "UNKNOWN_ERROR"),
                message=err.get("message", "未预期的错误"),
                details=err.get("details"),
            )
        return data.get("data")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json,
                headers=self._build_headers()
            )
        except httpx.TimeoutException as e:
            raise TransportError(f"请求超时: {e}") from e
        except httpx.HTTPError as e:
            raise TransportError(f"网络错误: {e}") from e
        return self._handle_response(resp)

    # --- 公开方法 ---
    def ask_question(
        self,
        question: str,
        session_id: Optional[str] = None,
        subject: Optional[str] = None
    ) -> AskAnswer:
        payload = {
            "question": question,
        }
        if session_id:
            payload["session_id"] = session_id
        if subject:
            payload["subject"] = subject
        data = self._request("POST", "/learning/ask", json=payload)
        return AskAnswer(
            question_id=data["question_id"],
            answer=data["answer"],
            confidence_score=data.get("confidence_score", 0.0),
            session_id=data.get("session_id"),
            response_time_ms=data.get("response_time_ms", -1),
            created_at=data.get("created_at"),
        )

    def list_sessions(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/learning/sessions",
            params={"limit": limit, "offset": offset}
        )

    def create_homework_submission(
        self,
        template_id: str,
        content_text: str | None = None,
        file_url: str | None = None
    ) -> Dict[str, Any]:
        if not (content_text or file_url):
            raise ValueError("content_text 与 file_url 至少提供一个")
        payload = {
            "template_id": template_id,
            "content_text": content_text,
            "file_url": file_url
        }
        return self._request("POST", "/homework/submissions", json=payload)

    def get_correction(self, submission_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/homework/corrections/{submission_id}")

    def close(self):
        self.session.close()
```

---

## 6. 异步客户端（示例片段）

```python
import httpx
from typing import Any, Optional

class AsyncWuHaoTutorClient(WuHaoTutorClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 覆盖同步 session
        self.session = httpx.AsyncClient(timeout=self.timeout)

    async def _request(self, method: str, path: str,
                       *, params=None, json=None) -> Any:
        url = f"{self.base_url}{path}"
        try:
            resp = await self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json,
                headers=self._build_headers()
            )
        except httpx.TimeoutException as e:
            raise TransportError(f"请求超时: {e}") from e
        except httpx.HTTPError as e:
            raise TransportError(f"网络错误: {e}") from e
        return self._handle_response(resp)

    async def ask_question(self, question: str) -> AskAnswer:
        data = await self._request("POST", "/learning/ask", json={"question": question})
        return AskAnswer(
            question_id=data["question_id"],
            answer=data["answer"],
            confidence_score=data.get("confidence_score", 0.0),
            session_id=data.get("session_id"),
            response_time_ms=data.get("response_time_ms", -1),
            created_at=data.get("created_at"),
        )

    async def aclose(self):
        await self.session.aclose()
```

---

## 7. 错误处理模式

| 异常类型 | 含义 | 典型处理 |
|----------|------|----------|
| `APIHTTPError` | 服务器业务/协议层错误（含 code） | 按 `code` 分支处理 |
| `TransportError` | 网络 / 超时 / 解析失败 | 重试或提示用户 |
| `WuHaoTutorError` | 根异常基类 | 捕获做兜底 |

使用示例：
```python
try:
    ans = client.ask_question("解释勾股定理")
except APIHTTPError as e:
    if e.code == "RATE_LIMIT_EXCEEDED":
        # 等待 Retry-After 或走降级
        ...
    else:
        ...
```

---

## 8. 分页与迭代器封装（可选实现）

```python
def iter_sessions(client: WuHaoTutorClient, page_size=50):
    offset = 0
    while True:
        page = client.list_sessions(limit=page_size, offset=offset)
        items = page["items"]
        if not items:
            break
        for it in items:
            yield it
        if not page.get("has_more"):
            break
        offset += page_size
```

---

## 9. 重试与幂等（规划）

建议策略（尚未内置）：
| 场景 | 策略 |
|------|------|
| 网络瞬时错误 | 指数退避重试（如 3 次：0.2s / 0.5s / 1.2s） |
| 429 | 按 `Retry-After` 秒等待，再一次性重试 |
| 5xx (非 501/503 长期) | 限次重试 |
| 幂等创建 | 未来：自定义 `Idempotency-Key` 头 |
| AI 超时 | 不自动重试（避免重复计费），可要求前端人工重试 |

---

## 10. 限流识别

当捕获 `APIHTTPError` 且 `code == RATE_LIMIT_EXCEEDED` 时，可读取：
```python
e.details.get("scope")
e.details.get("limit")
e.details.get("remaining")
e.details.get("reset_in")
```
可扩展：SDK 记录最近一次限流时间，避免短窗口内重试风暴。

---

## 11. 指标钩子（预留）

可在 `_request` 内部注入回调：
```python
def __init__(..., on_request_end=None):
    self.on_request_end = on_request_end

# 请求结束后：
if self.on_request_end:
    self.on_request_end({
        "method": method,
        "path": path,
        "status": resp.status_code,
        "elapsed_ms": resp.elapsed.total_seconds() * 1000
    })
```

---

## 12. 调试与日志建议

| 需求 | 做法 |
|------|------|
| 查看原始请求/响应 | 使用 httpx `event_hooks` |
| 屏蔽敏感头 | 日志中过滤 Authorization |
| 捕获 Trace-ID（规划） | 响应头若返回可记录 |
| 本地排查 | 开启 `HTTPX_LOG_LEVEL=debug` |

---

## 13. 测试策略建议

| 类型 | 示例 |
|------|------|
| 单元测试 | 对 `_handle_response` 输入不同假响应结构 |
| 集成测试 | 使用本地运行的后端 + 真实调用 |
| 回归测试 | 错误码变化应有断言（与 `errors.md` 对齐） |
| 性能冒烟 | 高并发问答调用（不要滥用 AI 配额） |

示例（pytest）：
```python
def test_parse_success_response(mock_success_response):
    client = WuHaoTutorClient("http://x")
    data = client._handle_response(mock_success_response)
    assert "question_id" in data
```

---

## 14. 常见问题 (FAQ)

| 问题 | 答案 |
|------|------|
| 是否需要全局单例？ | 视使用场景。可在函数式脚本中复用一个 client。 |
| 是否支持代理？ | 传入 `httpx.Client(proxies=...)`（扩展构造） |
| 是否支持异步？ | 使用 `AsyncWuHaoTutorClient` |
| 是否做本地缓存？ | 当前不做（保持透明） |
| AI 调用耗时较长怎么办？ | 调高超时或做异步调用 + 进度提示 |
| 如何获取原始响应头？ | 修改 `_request` 返回 `(headers, data)` 或扩展属性缓存 |
| Pydantic 模型？ | 可选：把 dataclass 换成 Pydantic BaseModel 提供验证 |

---

## 15. 规划路线 (Roadmap for SDK)

| 阶段 | 内容 | 备注 |
|------|------|------|
| 0.1 | 基础同步 / 异步封装 | 已示例 |
| 0.2 | 重试 + 幂等头支持 | 依赖后端规范 |
| 0.3 | 自动分页迭代器 | 通用化 |
| 0.4 | 速率自适应（软限提示） | 读取限流头 |
| 0.5 | 观测钩子 + OpenTelemetry（可选） | 需后端 trace |
| 0.6 | 发布 PyPI 初版 | 与 CHANGELOG 绑定 |
| 0.7 | 生成型 Schema 绑定（models.md diff 检测） | 防漂移 |
| 1.0 | 稳定 API 套件 | 对应后端 v1 冻结 |

---

## 16. 变更影响与兼容策略

| 变更类型 | SDK 应对 |
|----------|----------|
| 新增响应字段 | 可直接透传（不破坏） |
| 删除字段 | 升级大版本或添加兼容层 |
| 错误码新增 | 不需改 SDK（用户可判断） |
| 错误码删除/替换 | 文档同步 + 版本公告 |
| 分页模型变更 | 统一修改迭代器逻辑 |
| 路径版本升级 | 新增 `base_url_v2` / 多版本 client |

---

## 17. 文件组织建议（未来独立包）

```
wuhao_tutor_sdk/
├── __init__.py
├── client.py          # 主同步客户端
├── async_client.py    # 异步客户端
├── models.py          # Pydantic/Dataclass 模型
├── errors.py          # 异常定义
├── pagination.py      # 分页与迭代
├── retries.py         # 重试策略（可选）
├── telemetry.py       # 指标钩子（可选）
└── utils.py
```

---

## 18. 待办 (TODO)

| 项 | 优先级 | 说明 |
|----|--------|------|
| 与实际端点字段核对 | P0 | 对照 `api/models.md` |
| 错误码映射自动测试 | P0 | 防止后端新增未覆盖 |
| 加入重试策略 | P1 | 网络/429 场景 |
| 幂等性头支持 | P2 | 结合后端实现 |
| 分页统一模型类 | P2 | 泛型封装 |
| OpenTelemetry 支持 | P3 | 可选 |
| CLI 快速调试工具 | P3 | `python -m sdk.cli ask "..."` |
| 模型差异检测脚本 | P3 | 防漂移 |
| 文档自动生成 | P4 | 从 OpenAPI 拉取构建模型 |
| 测试覆盖率报告 | P4 | CI 集成 |

---

## 19. 反馈与改进

请在主仓库提 Issue：
- 标签：`sdk`
- 附带信息：使用场景 / 问题描述 / 期望行为 / 代码片段（如有）

或提交 PR：
1. 遵循分支命名：`feat/sdk-*` / `fix/sdk-*`
2. 附变更说明与兼容性评估
3. 更新本文件相关章节（若涉及接口）

---

（END）

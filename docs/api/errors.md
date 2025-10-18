# API 错误码文档

> **最后更新**: 2025-10-12
> **状态**: ✅ 已更新 - 反映当前实现

---

## 📋 目录

1. [概述](#概述)
2. [错误响应格式](#错误响应格式)
3. [HTTP 状态码映射](#http-状态码映射)
4. [错误码分类](#错误码分类)
5. [详细错误码列表](#详细错误码列表)
6. [错误处理最佳实践](#错误处理最佳实践)

---

## 概述

本文档定义了五好伴学 API 的所有错误码和错误处理规范。

**位置**: `src/core/exceptions.py`

**设计原则**:

- ✅ 错误码采用 `SCREAMING_SNAKE_CASE` 命名
- ✅ 错误信息清晰易懂，便于前端展示
- ✅ 包含详细的错误上下文（details）
- ✅ 支持国际化（i18n）
- ✅ 统一的错误响应格式

---

## 错误响应格式

### 标准错误响应

```json
{
  "detail": "用户不存在",
  "error_code": "USER_NOT_FOUND_ERROR",
  "details": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 字段说明

| 字段         | 类型   | 说明                               |
| ------------ | ------ | ---------------------------------- |
| `detail`     | `str`  | 人类可读的错误描述                 |
| `error_code` | `str`  | 机器可解析的错误码（用于程序处理） |
| `details`    | `dict` | 错误的详细上下文信息（可选）       |

### 验证错误响应

```json
{
  "detail": [
    {
      "loc": ["body", "phone"],
      "msg": "手机号格式不正确",
      "type": "value_error"
    }
  ]
}
```

**说明**: Pydantic 验证错误返回详细的字段级错误信息。

---

## HTTP 状态码映射

| HTTP 状态码 | 说明                  | 典型场景                   |
| ----------- | --------------------- | -------------------------- |
| `400`       | Bad Request           | 请求参数错误、验证失败     |
| `401`       | Unauthorized          | 未认证、Token 无效或过期   |
| `403`       | Forbidden             | 权限不足                   |
| `404`       | Not Found             | 资源不存在                 |
| `409`       | Conflict              | 资源冲突（如重复创建）     |
| `429`       | Too Many Requests     | 请求频率超限               |
| `500`       | Internal Server Error | 服务器内部错误             |
| `502`       | Bad Gateway           | 上游服务错误（如 AI 服务） |
| `503`       | Service Unavailable   | 服务暂时不可用（如限流）   |
| `504`       | Gateway Timeout       | 上游服务超时               |

---

## 错误码分类

### 1. 认证与授权错误 (401/403)

| 错误码                  | HTTP | 说明         |
| ----------------------- | ---- | ------------ |
| `AUTHENTICATION_ERROR`  | 401  | 认证失败     |
| `TOKEN_EXPIRED_ERROR`   | 401  | Token 已过期 |
| `INVALID_TOKEN_ERROR`   | 401  | 无效的 Token |
| `USER_AUTH_ERROR`       | 401  | 用户认证失败 |
| `AUTHORIZATION_ERROR`   | 403  | 授权失败     |
| `USER_PERMISSION_ERROR` | 403  | 用户权限不足 |

### 2. 资源错误 (404/409)

| 错误码                        | HTTP | 说明         |
| ----------------------------- | ---- | ------------ |
| `RECORD_NOT_FOUND_ERROR`      | 404  | 记录未找到   |
| `USER_NOT_FOUND_ERROR`        | 404  | 用户不存在   |
| `CACHE_KEY_NOT_FOUND_ERROR`   | 404  | 缓存键不存在 |
| `RECORD_ALREADY_EXISTS_ERROR` | 409  | 记录已存在   |

### 3. 验证与请求错误 (400)

| 错误码                   | HTTP | 说明         |
| ------------------------ | ---- | ------------ |
| `VALIDATION_ERROR`       | 400  | 数据验证失败 |
| `HOMEWORK_UPLOAD_ERROR`  | 400  | 作业上传失败 |
| `QUESTION_PROCESS_ERROR` | 400  | 问题处理失败 |
| `FILE_PROCESS_ERROR`     | 400  | 文件处理失败 |

### 4. 限流错误 (429/503)

| 错误码                         | HTTP | 说明                  |
| ------------------------------ | ---- | --------------------- |
| `RATE_LIMIT_ERROR`             | 429  | API 调用频率过高      |
| `BAILIAN_RATE_LIMIT_ERROR`     | 503  | 百炼 API 调用频率过高 |
| `BAILIAN_QUOTA_EXCEEDED_ERROR` | 503  | 百炼 API 配额已用完   |

### 5. AI 服务错误 (502/504)

| 错误码                         | HTTP | 说明                  |
| ------------------------------ | ---- | --------------------- |
| `BAILIAN_AUTH_ERROR`           | 502  | 百炼 API 认证失败     |
| `BAILIAN_RESPONSE_PARSE_ERROR` | 502  | 百炼 API 响应格式错误 |
| `BAILIAN_TIMEOUT_ERROR`        | 504  | 百炼 API 调用超时     |
| `AI_SERVICE_ERROR`             | 502  | AI 服务错误           |
| `OCR_PROCESS_ERROR`            | 500  | OCR 处理失败          |

### 6. 业务逻辑错误 (500)

| 错误码                      | HTTP | 说明               |
| --------------------------- | ---- | ------------------ |
| `HOMEWORK_CORRECTION_ERROR` | 500  | 作业批改失败       |
| `CONTEXT_LOAD_ERROR`        | 500  | 学习上下文加载失败 |

### 7. 系统错误 (500)

| 错误码                      | HTTP | 说明             |
| --------------------------- | ---- | ---------------- |
| `DATABASE_CONNECTION_ERROR` | 500  | 数据库连接失败   |
| `CACHE_CONNECTION_ERROR`    | 500  | 缓存服务连接失败 |
| `CONFIGURATION_ERROR`       | 500  | 配置错误         |
| `ENVIRONMENT_ERROR`         | 500  | 环境变量错误     |

---

## 详细错误码列表

### AUTHENTICATION_ERROR

**HTTP 状态码**: 401

**说明**: 认证失败，用户身份验证未通过

**示例**:

```json
{
  "detail": "认证失败",
  "error_code": "AUTHENTICATION_ERROR"
}
```

**前端处理**: 跳转到登录页面

---

### TOKEN_EXPIRED_ERROR

**HTTP 状态码**: 401

**说明**: JWT Token 已过期

**示例**:

```json
{
  "detail": "Token已过期",
  "error_code": "TOKEN_EXPIRED_ERROR"
}
```

**前端处理**: 使用 Refresh Token 刷新，或提示用户重新登录

---

### INVALID_TOKEN_ERROR

**HTTP 状态码**: 401

**说明**: Token 格式错误或签名验证失败

**示例**:

```json
{
  "detail": "无效的Token",
  "error_code": "INVALID_TOKEN_ERROR"
}
```

**前端处理**: 清除本地 Token，跳转到登录页面

---

### USER_NOT_FOUND_ERROR

**HTTP 状态码**: 404

**说明**: 指定的用户不存在

**示例**:

```json
{
  "detail": "用户不存在",
  "error_code": "USER_NOT_FOUND_ERROR",
  "details": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**前端处理**: 显示友好的错误提示

---

### USER_PERMISSION_ERROR

**HTTP 状态码**: 403

**说明**: 用户权限不足，无法访问该资源

**示例**:

```json
{
  "detail": "用户权限不足",
  "error_code": "USER_PERMISSION_ERROR",
  "details": {
    "required_permission": "admin"
  }
}
```

**前端处理**: 显示权限不足提示，禁用相关功能

---

### VALIDATION_ERROR

**HTTP 状态码**: 400

**说明**: 请求参数验证失败

**示例**:

```json
{
  "detail": "数据验证失败",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field_errors": {
      "phone": "手机号格式不正确",
      "password": "密码长度必须在8-32位之间"
    }
  }
}
```

**前端处理**: 在表单对应字段显示错误提示

---

### RECORD_NOT_FOUND_ERROR

**HTTP 状态码**: 404

**说明**: 数据库记录不存在

**示例**:

```json
{
  "detail": "记录未找到",
  "error_code": "RECORD_NOT_FOUND_ERROR",
  "details": {
    "resource": "Mistake",
    "resource_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**前端处理**: 显示资源不存在提示，返回列表页面

---

### RECORD_ALREADY_EXISTS_ERROR

**HTTP 状态码**: 409

**说明**: 记录已存在，违反唯一性约束

**示例**:

```json
{
  "detail": "记录已存在",
  "error_code": "RECORD_ALREADY_EXISTS_ERROR",
  "details": {
    "resource": "User",
    "unique_field": "phone"
  }
}
```

**前端处理**: 提示用户该资源已存在（如手机号已注册）

---

### RATE_LIMIT_ERROR

**HTTP 状态码**: 429

**说明**: API 调用频率超过限制

**示例**:

```json
{
  "detail": "API调用频率过高",
  "error_code": "RATE_LIMIT_ERROR",
  "details": {
    "limit": 100,
    "window": 3600
  }
}
```

**前端处理**: 显示限流提示，建议稍后重试

**Retry-After**: 响应头包含建议的重试时间（秒）

---

### BAILIAN_AUTH_ERROR

**HTTP 状态码**: 502

**说明**: 阿里云百炼 API 认证失败

**示例**:

```json
{
  "detail": "百炼API认证失败",
  "error_code": "BAILIAN_AUTH_ERROR"
}
```

**前端处理**: 显示 AI 服务暂时不可用提示

---

### BAILIAN_TIMEOUT_ERROR

**HTTP 状态码**: 504

**说明**: 阿里云百炼 API 调用超时

**示例**:

```json
{
  "detail": "百炼API调用超时",
  "error_code": "BAILIAN_TIMEOUT_ERROR",
  "details": {
    "timeout": 30
  }
}
```

**前端处理**: 提示 AI 服务响应超时，建议重试

---

### BAILIAN_RATE_LIMIT_ERROR

**HTTP 状态码**: 503

**说明**: 百炼 API 调用频率过高

**示例**:

```json
{
  "detail": "百炼API调用频率过高",
  "error_code": "BAILIAN_RATE_LIMIT_ERROR",
  "details": {
    "retry_after": 60
  }
}
```

**前端处理**: 显示限流提示，建议等待后重试

---

### FILE_PROCESS_ERROR

**HTTP 状态码**: 400

**说明**: 文件处理失败（如格式不支持、文件过大）

**示例**:

```json
{
  "detail": "文件处理失败",
  "error_code": "FILE_PROCESS_ERROR",
  "details": {
    "file_name": "homework.pdf",
    "file_size": 15728640
  }
}
```

**前端处理**: 显示文件相关错误提示（如"文件过大，请上传小于10MB的文件"）

---

### DATABASE_CONNECTION_ERROR

**HTTP 状态码**: 500

**说明**: 数据库连接失败

**示例**:

```json
{
  "detail": "数据库连接失败",
  "error_code": "DATABASE_CONNECTION_ERROR"
}
```

**前端处理**: 显示系统错误提示，建议联系管理员

---

## 错误处理最佳实践

### 前端处理原则

1. **根据 HTTP 状态码进行分类处理**

```typescript
switch (error.response.status) {
  case 401:
    // 跳转登录
    router.push("/login");
    break;
  case 403:
    // 显示权限不足
    showMessage("权限不足");
    break;
  case 404:
    // 显示资源不存在
    showMessage("资源不存在");
    break;
  case 429:
    // 显示限流提示
    showMessage("请求过于频繁，请稍后重试");
    break;
  case 500:
  case 502:
  case 503:
  case 504:
    // 显示服务器错误
    showMessage("服务暂时不可用，请稍后重试");
    break;
}
```

2. **使用错误码进行精确处理**

```typescript
if (error.response.data.error_code === "TOKEN_EXPIRED_ERROR") {
  // 刷新 Token
  await refreshToken();
  // 重试原请求
  return retryRequest(originalRequest);
}
```

3. **显示友好的错误消息**

```typescript
const errorMessages = {
  USER_NOT_FOUND_ERROR: "用户不存在",
  VALIDATION_ERROR: "输入信息有误，请检查后重试",
  RATE_LIMIT_ERROR: "操作过于频繁，请稍后再试",
  // ...
};

const message = errorMessages[error.error_code] || error.detail || "操作失败";
showMessage(message);
```

### 后端处理原则

1. **使用具体的异常类型**

```python
# ✅ 推荐
from src.core.exceptions import UserNotFoundError

if not user:
    raise UserNotFoundError(f"用户 {user_id} 不存在")

# ❌ 避免
raise Exception("用户不存在")
```

2. **提供详细的错误上下文**

```python
raise ValidationError(
    message="数据验证失败",
    field_errors={
        "phone": "手机号格式不正确",
        "password": "密码长度必须在8-32位之间"
    }
)
```

3. **记录错误日志**

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = await service.process()
except BailianServiceError as e:
    logger.error(f"百炼服务调用失败: {e.message}", extra=e.details)
    raise
```

### 重试策略

| 错误类型       | 是否重试 | 重试策略                |
| -------------- | -------- | ----------------------- |
| 4xx 客户端错误 | ❌       | 不重试（除 429）        |
| 429 限流       | ✅       | 指数退避，最多重试 3 次 |
| 500 服务器错误 | ✅       | 立即重试 1 次           |
| 502/503/504    | ✅       | 延迟重试，最多重试 2 次 |
| 网络错误       | ✅       | 指数退避，最多重试 3 次 |

---

## 版本历史

| 日期       | 版本 | 变更说明                        |
| ---------- | ---- | ------------------------------- |
| 2025-10-12 | v2.0 | 根据 exceptions.py 完全重写文档 |
| 2025-09-29 | v1.0 | 初始版本（草稿）                |

---

## 相关文档

- [API 端点文档](./endpoints.md) - 完整的 API 接口列表
- [API 数据模型](./models.md) - 请求响应数据结构
- [API 概览](./overview.md) - RESTful 设计原则

---

**维护者**: 五好伴学开发团队
**反馈**: 通过 GitHub Issues 提交文档问题和改进建议

# API 端点文档

> **最后更新**: 2025-10-12
> **API 版本**: v1
> **基础路径**: `/api/v1`
> **状态**: ✅ 生产环境运行中

本文档列出所有已实现的 API 端点。所有端点均已在生产环境中部署和测试。

---

## 📋 目录

- [认证模块 (auth)](#认证模块-auth) - 20 个端点
- [学习问答 (learning)](#学习问答-learning) - 22 个端点
- [作业批改 (homework)](#作业批改-homework) - 17 个端点
- [错题手册 (mistakes)](#错题手册-mistakes) - 7 个端点
- [学情分析 (analytics)](#学情分析-analytics) - 7 个端点
- [文件管理 (file)](#文件管理-file) - 12 个端点
- [每日目标 (goals)](#每日目标-goals) - 1 个端点
- [用户统计 (user)](#用户统计-user) - 2 个端点
- [健康检查 (health)](#健康检查-health) - 6 个端点

**总计**: 94+ 个 API 端点

---

## 🔐 认证说明

### 认证方式

- **方式**: Bearer Token (JWT)
- **请求头**: `Authorization: Bearer <access_token>`
- **Token 类型**: Access Token + Refresh Token

### 认证要求

| 标记 | 说明         |
| ---- | ------------ |
| 🔓   | 无需认证     |
| 🔒   | 需要认证     |
| 👑   | 需要特定角色 |

---

## 认证模块 (auth)

**路由前缀**: `/api/v1/auth`

### 注册与登录

| 方法 | 路径            | 认证 | 说明           |
| ---- | --------------- | ---- | -------------- |
| POST | `/register`     | 🔓   | 用户注册       |
| POST | `/login`        | 🔓   | 用户登录       |
| POST | `/wechat-login` | 🔓   | 微信小程序登录 |
| POST | `/refresh`      | 🔓   | 刷新访问令牌   |
| POST | `/logout`       | 🔒   | 用户登出       |

**注册请求示例**:

```json
{
  "phone": "13800138000",
  "password": "SecurePass123",
  "role": "student"
}
```

**登录响应示例**:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "phone": "13800138000",
    "role": "student"
  }
}
```

### 用户管理

| 方法 | 路径          | 认证 | 说明             |
| ---- | ------------- | ---- | ---------------- |
| GET  | `/me`         | 🔒   | 获取当前用户信息 |
| PUT  | `/profile`    | 🔒   | 更新用户资料     |
| POST | `/avatar`     | 🔒   | 上传头像         |
| POST | `/deactivate` | 🔒   | 停用账号         |

### 密码管理

| 方法 | 路径               | 认证 | 说明     |
| ---- | ------------------ | ---- | -------- |
| POST | `/change-password` | 🔒   | 修改密码 |
| POST | `/forgot-password` | 🔓   | 忘记密码 |
| POST | `/reset-password`  | 🔓   | 重置密码 |

### 验证功能

| 方法 | 路径                      | 认证 | 说明             |
| ---- | ------------------------- | ---- | ---------------- |
| POST | `/send-verification-code` | 🔓   | 发送验证码       |
| POST | `/verify-email`           | 🔓   | 验证邮箱         |
| POST | `/resend-verification`    | 🔓   | 重发验证码       |
| GET  | `/verify-token`           | 🔒   | 验证令牌有效性   |
| GET  | `/check-username`         | 🔓   | 检查用户名可用性 |
| GET  | `/check-email`            | 🔓   | 检查邮箱可用性   |

### 双因素认证

| 方法 | 路径           | 认证 | 说明           |
| ---- | -------------- | ---- | -------------- |
| POST | `/2fa/enable`  | 🔒   | 启用双因素认证 |
| POST | `/2fa/disable` | 🔒   | 禁用双因素认证 |

---

## 学习问答 (learning)

**路由前缀**: `/api/v1/learning`

### AI 问答

| 方法 | 路径             | 认证 | 说明        |
| ---- | ---------------- | ---- | ----------- |
| POST | `/ask`           | 🔒   | AI 问答提问 |
| POST | `/feedback`      | 🔒   | 提交反馈    |
| POST | `/voice-to-text` | 🔒   | 语音转文字  |

**提问请求示例**:

```json
{
  "question": "如何求解一元二次方程？",
  "session_id": "uuid",
  "context": {
    "subject": "数学",
    "grade": 8
  },
  "images": []
}
```

**提问响应示例**:

```json
{
  "success": true,
  "data": {
    "answer": "一元二次方程的求解方法有...",
    "question_id": "uuid",
    "session_id": "uuid",
    "knowledge_points": ["一元二次方程", "求根公式"],
    "difficulty": 3,
    "response_time": 1.23
  }
}
```

### 会话管理

| 方法   | 路径                      | 认证 | 说明         |
| ------ | ------------------------- | ---- | ------------ |
| POST   | `/sessions`               | 🔒   | 创建会话     |
| GET    | `/sessions`               | 🔒   | 获取会话列表 |
| GET    | `/sessions/{id}`          | 🔒   | 获取会话详情 |
| PUT    | `/sessions/{id}`          | 🔒   | 更新会话     |
| PATCH  | `/sessions/{id}`          | 🔒   | 部分更新会话 |
| DELETE | `/sessions/{id}`          | 🔒   | 删除会话     |
| PATCH  | `/sessions/{id}/archive`  | 🔒   | 归档会话     |
| PATCH  | `/sessions/{id}/activate` | 🔒   | 激活会话     |

### 问题历史

| 方法 | 路径                       | 认证 | 说明             |
| ---- | -------------------------- | ---- | ---------------- |
| GET  | `/sessions/{id}/questions` | 🔒   | 获取会话问答历史 |
| GET  | `/sessions/{id}/history`   | 🔒   | 获取会话完整历史 |
| GET  | `/questions`               | 🔒   | 获取所有问题     |
| GET  | `/questions/history`       | 🔒   | 获取问题历史     |
| GET  | `/questions/search`        | 🔒   | 搜索问题         |
| GET  | `/questions/{id}`          | 🔒   | 获取问题详情     |

### 统计信息

| 方法 | 路径            | 认证 | 说明       |
| ---- | --------------- | ---- | ---------- |
| GET  | `/stats/daily`  | 🔒   | 获取日统计 |
| GET  | `/stats/weekly` | 🔒   | 获取周报告 |

### 健康检查

| 方法 | 路径      | 认证 | 说明             |
| ---- | --------- | ---- | ---------------- |
| GET  | `/health` | 🔓   | 学习模块健康检查 |
| GET  | `/test`   | 🔓   | 测试端点         |

---

## 作业批改 (homework)

**路由前缀**: `/api/v1/homework`

### 作业模板

| 方法 | 路径                       | 认证 | 说明         |
| ---- | -------------------------- | ---- | ------------ |
| GET  | `/templates`               | 🔒   | 获取模板列表 |
| POST | `/templates`               | 🔒   | 创建作业模板 |
| GET  | `/templates/{template_id}` | 🔒   | 获取模板详情 |

### 作业提交

| 方法 | 路径                                      | 认证 | 说明         |
| ---- | ----------------------------------------- | ---- | ------------ |
| POST | `/submit`                                 | 🔒   | 提交作业     |
| GET  | `/submissions`                            | 🔒   | 获取提交列表 |
| GET  | `/submissions/{submission_id}`            | 🔒   | 获取提交详情 |
| PUT  | `/submissions/{submission_id}`            | 🔒   | 更新提交     |
| GET  | `/submissions/{submission_id}/correction` | 🔒   | 获取批改结果 |

### 批改功能

| 方法 | 路径            | 认证 | 说明     |
| ---- | --------------- | ---- | -------- |
| POST | `/{id}/correct` | 🔒   | 批改作业 |
| POST | `/{id}/retry`   | 🔒   | 重新批改 |

**批改请求示例**:

```json
{
  "homework_id": "uuid",
  "answers": [
    {
      "question_id": "q1",
      "answer": "学生答案"
    }
  ]
}
```

### 作业管理

| 方法   | 路径    | 认证 | 说明     |
| ------ | ------- | ---- | -------- |
| GET    | `/list` | 🔒   | 作业列表 |
| GET    | `/{id}` | 🔒   | 作业详情 |
| PUT    | `/{id}` | 🔒   | 更新作业 |
| DELETE | `/{id}` | 🔒   | 删除作业 |

### 统计信息

| 方法 | 路径     | 认证 | 说明     |
| ---- | -------- | ---- | -------- |
| GET  | `/stats` | 🔒   | 作业统计 |

### 健康检查

| 方法 | 路径      | 认证 | 说明             |
| ---- | --------- | ---- | ---------------- |
| GET  | `/health` | 🔓   | 作业模块健康检查 |

### 兼容性 API

**路由前缀**: `/api/v1/homework-compatibility`

| 方法 | 路径                     | 认证 | 说明             |
| ---- | ------------------------ | ---- | ---------------- |
| GET  | `/list`                  | 🔒   | 兼容旧版列表接口 |
| GET  | `/{homework_id}`         | 🔒   | 兼容旧版详情接口 |
| POST | `/{homework_id}/correct` | 🔒   | 兼容旧版批改接口 |
| GET  | `/{homework_id}/ocr`     | 🔒   | OCR 识别         |

---

## 错题手册 (mistakes)

**路由前缀**: `/api/v1/mistakes`

### 错题管理

| 方法   | 路径            | 认证 | 说明         |
| ------ | --------------- | ---- | ------------ |
| GET    | `/`             | 🔒   | 获取错题列表 |
| POST   | `/`             | 🔒   | 添加错题     |
| GET    | `/{mistake_id}` | 🔒   | 获取错题详情 |
| DELETE | `/{mistake_id}` | 🔒   | 删除错题     |

**错题列表查询参数**:

```
?page=1
&page_size=20
&subject=数学
&mastery_status=learning
&search=二次方程
```

**添加错题请求示例**:

```json
{
  "title": "一元二次方程求解",
  "question_content": "求解方程 x² - 5x + 6 = 0",
  "student_answer": "x = 2",
  "correct_answer": "x = 2 或 x = 3",
  "explanation": "需要求出两个根",
  "subject": "数学",
  "difficulty_level": 3,
  "knowledge_points": ["一元二次方程", "因式分解"],
  "image_urls": []
}
```

### 复习功能

| 方法 | 路径                   | 认证 | 说明             |
| ---- | ---------------------- | ---- | ---------------- |
| GET  | `/today-review`        | 🔒   | 获取今日复习任务 |
| POST | `/{mistake_id}/review` | 🔒   | 完成复习         |

**完成复习请求示例**:

```json
{
  "review_result": "correct",
  "confidence_level": 4,
  "time_spent": 120,
  "user_answer": "x = 2 或 x = 3",
  "notes": "已掌握"
}
```

### 统计分析

| 方法 | 路径          | 认证 | 说明         |
| ---- | ------------- | ---- | ------------ |
| GET  | `/statistics` | 🔒   | 获取错题统计 |

**统计响应示例**:

```json
{
  "total_mistakes": 45,
  "mastered_count": 12,
  "learning_count": 20,
  "new_count": 13,
  "by_subject": {
    "数学": 25,
    "物理": 12,
    "英语": 8
  },
  "by_difficulty": {
    "1": 5,
    "2": 15,
    "3": 18,
    "4": 5,
    "5": 2
  },
  "review_completion_rate": 0.73
}
```

---

## 学情分析 (analytics)

**路由前缀**: `/api/v1/analytics`

### 学习统计

| 方法 | 路径                 | 认证 | 说明         |
| ---- | -------------------- | ---- | ------------ |
| GET  | `/learning-stats`    | 🔒   | 学习统计概览 |
| GET  | `/learning-progress` | 🔒   | 学习进度趋势 |
| GET  | `/user/stats`        | 🔒   | 用户统计信息 |

**学习进度查询参数**:

```
?days=7        # 最近7天
&granularity=day  # 粒度: day/week/month
```

### 知识点分析

| 方法 | 路径                | 认证 | 说明           |
| ---- | ------------------- | ---- | -------------- |
| GET  | `/knowledge-points` | 🔒   | 知识点掌握情况 |
| GET  | `/knowledge-map`    | 🔒   | 知识图谱数据   |

### 学科统计

| 方法 | 路径             | 认证 | 说明         |
| ---- | ---------------- | ---- | ------------ |
| GET  | `/subject-stats` | 🔒   | 学科统计分析 |

**学科统计响应示例**:

```json
{
  "subjects": [
    {
      "subject": "数学",
      "total_questions": 156,
      "correct_count": 120,
      "accuracy": 0.77,
      "study_time": 3600,
      "mastery_points": 45,
      "weak_points": ["一元二次方程", "三角函数"]
    }
  ]
}
```

### 健康检查

| 方法 | 路径      | 认证 | 说明             |
| ---- | --------- | ---- | ---------------- |
| GET  | `/health` | 🔓   | 分析模块健康检查 |

---

## 文件管理 (file)

**路由前缀**: `/api/v1/files`

### 文件上传

| 方法 | 路径                         | 认证 | 说明             |
| ---- | ---------------------------- | ---- | ---------------- |
| POST | `/upload`                    | 🔒   | 通用文件上传     |
| POST | `/upload-image-for-learning` | 🔒   | 学习问答图片上传 |
| POST | `/upload-for-ai`             | 🔒   | AI 分析图片上传  |

**上传请求** (multipart/form-data):

```
file: <binary>
category: learning/homework/avatar
```

**上传响应示例**:

```json
{
  "success": true,
  "data": {
    "file_id": "uuid",
    "filename": "image.jpg",
    "url": "/api/v1/files/ai/image.jpg",
    "size": 102400,
    "content_type": "image/jpeg"
  }
}
```

### 文件访问

| 方法   | 路径                  | 认证 | 说明       |
| ------ | --------------------- | ---- | ---------- |
| GET    | `/`                   | 🔒   | 文件列表   |
| GET    | `/{file_id}`          | 🔒   | 文件元数据 |
| GET    | `/{file_id}/download` | 🔒   | 下载文件   |
| GET    | `/{file_id}/preview`  | 🔒   | 预览文件   |
| DELETE | `/{file_id}`          | 🔒   | 删除文件   |

### 特殊路径

| 方法 | 路径                  | 认证 | 说明             |
| ---- | --------------------- | ---- | ---------------- |
| GET  | `/avatars/{filename}` | 🔓   | 获取头像         |
| GET  | `/ai/{filename}`      | 🔒   | 获取 AI 分析图片 |

### 统计信息

| 方法 | 路径             | 认证 | 说明         |
| ---- | ---------------- | ---- | ------------ |
| GET  | `/stats/summary` | 🔒   | 文件统计概览 |

### 健康检查

| 方法 | 路径      | 认证 | 说明             |
| ---- | --------- | ---- | ---------------- |
| GET  | `/health` | 🔓   | 文件模块健康检查 |

---

## 每日目标 (goals)

**路由前缀**: `/api/v1/goals`

| 方法 | 路径           | 认证 | 说明             |
| ---- | -------------- | ---- | ---------------- |
| GET  | `/daily-goals` | 🔒   | 获取每日学习目标 |

**响应示例**:

```json
{
  "date": "2025-10-12",
  "goals": [
    {
      "type": "study_time",
      "target": 3600,
      "current": 2400,
      "progress": 0.67,
      "completed": false
    },
    {
      "type": "questions_answered",
      "target": 20,
      "current": 15,
      "progress": 0.75,
      "completed": false
    },
    {
      "type": "mistakes_reviewed",
      "target": 5,
      "current": 5,
      "progress": 1.0,
      "completed": true
    }
  ]
}
```

---

## 用户统计 (user)

**路由前缀**: `/api/v1/user`

| 方法 | 路径          | 认证 | 说明         |
| ---- | ------------- | ---- | ------------ |
| GET  | `/activities` | 🔒   | 用户活动记录 |
| GET  | `/stats`      | 🔒   | 用户统计信息 |

---

## 健康检查 (health)

**路由前缀**: `/api/v1/health`

| 方法 | 路径           | 认证 | 说明         |
| ---- | -------------- | ---- | ------------ |
| GET  | `/`            | 🔓   | 综合健康检查 |
| GET  | `/readiness`   | 🔓   | 就绪探针     |
| GET  | `/liveness`    | 🔓   | 存活探针     |
| GET  | `/metrics`     | 🔓   | 系统指标     |
| GET  | `/performance` | 🔓   | 性能指标     |
| GET  | `/rate-limits` | 🔒   | 限流状态     |

**健康检查响应示例**:

```json
{
  "status": "healthy",
  "timestamp": "2025-10-12T10:30:00Z",
  "version": "0.3.0",
  "checks": {
    "database": "healthy",
    "ai_service": "healthy",
    "cache": "healthy",
    "storage": "healthy"
  }
}
```

---

## 📊 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数错误",
    "details": {
      "field": "phone",
      "reason": "手机号格式不正确"
    }
  }
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "has_more": true
  }
}
```

---

## 🚦 HTTP 状态码

| 状态码 | 说明             |
| ------ | ---------------- |
| 200    | 请求成功         |
| 201    | 创建成功         |
| 204    | 删除成功(无内容) |
| 400    | 请求参数错误     |
| 401    | 未认证或认证失败 |
| 403    | 无权限           |
| 404    | 资源不存在       |
| 409    | 资源冲突         |
| 422    | 数据验证失败     |
| 429    | 请求频率过高     |
| 500    | 服务器内部错误   |
| 503    | 服务不可用       |

---

## 🔒 限流策略

| 维度    | 限制        | 说明          |
| ------- | ----------- | ------------- |
| IP      | 100 req/min | 单个 IP 地址  |
| 用户    | 60 req/min  | 认证用户      |
| AI 服务 | 20 req/min  | AI 问答和批改 |
| 登录    | 5 req/min   | 登录尝试      |

超过限制返回 `429 Too Many Requests`，响应头包含:

- `X-RateLimit-Limit`: 限制值
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间戳

---

## 📝 更新日志

- **2025-10-12**: 完全重写，反映实际实现的 94+ 个端点
- **2025-09-29**: 初始版本(已过时)

---

## 🔗 相关文档

- [API 数据模型](models.md) - 请求和响应的数据结构
- [错误码参考](errors.md) - 完整的错误码列表
- [前后端集成](../integration/frontend.md) - 前端调用指南
- [认证机制](../architecture/security.md) - 详细的认证说明

---

**维护者**: 五好伴学开发团队
**反馈**: 发现文档问题请提交 Issue

# API 数据模型文档

> **最后更新**: 2025-10-12
> **状态**: ✅ 已更新 - 反映当前实现

---

## 📋 目录

1. [概述](#概述)
2. [通用约定](#通用约定)
3. [响应格式](#响应格式)
4. [认证模块](#认证模块)
5. [用户模块](#用户模块)
6. [学习模块](#学习模块)
7. [作业模块](#作业模块)
8. [错题模块](#错题模块)
9. [学习目标模块](#学习目标模块)
10. [分析模块](#分析模块)
11. [文件模块](#文件模块)
12. [通用模型](#通用模型)

---

## 概述

本文档描述五好伴学 API 的所有数据模型（Pydantic Schemas），定义了 API 请求和响应的数据结构。

**位置**: `src/schemas/`

**原则**:

- ✅ 使用 `snake_case` 命名 JSON 字段
- ✅ 所有时间字段使用 ISO8601 格式（UTC）
- ✅ ID 字段统一使用 UUID v4
- ✅ 枚举类型使用字符串表示
- ✅ 可选字段使用 `Optional[Type]`

---

## 通用约定

### 数据类型

| 类型         | 说明                  | 示例                            |
| ------------ | --------------------- | ------------------------------- |
| `UUID`       | UUID v4 字符串        | `"550e8400-e29b-41d4-a716-..."` |
| `datetime`   | ISO8601 时间戳（UTC） | `"2025-10-12T08:30:00Z"`        |
| `str`        | 字符串                | `"学习记录"`                    |
| `int`        | 整数                  | `100`                           |
| `float`      | 浮点数                | `95.5`                          |
| `bool`       | 布尔值                | `true` / `false`                |
| `List[Type]` | 数组                  | `[1, 2, 3]`                     |
| `Dict`       | 对象/字典             | `{"key": "value"}`              |

### 枚举类型

| 枚举           | 值                                                   | 说明     |
| -------------- | ---------------------------------------------------- | -------- |
| `Subject`      | `math`, `chinese`, `english`, `physics`, `other`     | 学科     |
| `Difficulty`   | `easy`, `medium`, `hard`                             | 难度     |
| `UserRole`     | `student`, `teacher`, `parent`, `admin`              | 用户角色 |
| `MasteryLevel` | `not_mastered`, `learning`, `mastered`, `proficient` | 掌握程度 |

---

## 响应格式

### 标准响应包装

**成功响应**:

```json
{
  "code": 200,
  "message": "Success",
  "data": { ... }
}
```

**错误响应**:

```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE"
}
```

### 分页响应

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

## 认证模块

**位置**: `src/schemas/auth.py`

### TokenResponse

JWT Token 响应

```python
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 691200  # 8 天（秒）
}
```

| 字段            | 类型  | 说明                        |
| --------------- | ----- | --------------------------- |
| `access_token`  | `str` | 访问令牌                    |
| `refresh_token` | `str` | 刷新令牌                    |
| `token_type`    | `str` | Token 类型（固定 "bearer"） |
| `expires_in`    | `int` | 过期时间（秒）              |

### UserRegister

用户注册请求

```python
{
  "phone": "13800138000",
  "password": "SecurePass123!",
  "username": "张三",
  "role": "student"
}
```

| 字段       | 类型       | 必填 | 说明                 |
| ---------- | ---------- | ---- | -------------------- |
| `phone`    | `str`      | ✅   | 手机号（11 位）      |
| `password` | `str`      | ✅   | 密码（8-32 位）      |
| `username` | `str`      | ✅   | 用户名               |
| `role`     | `UserRole` | ❌   | 用户角色（默认学生） |

### UserLogin

用户登录请求

```python
{
  "phone": "13800138000",
  "password": "SecurePass123!"
}
```

---

## 用户模块

**位置**: `src/schemas/user.py`

### UserResponse

用户信息响应

```python
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "13800138000",
  "username": "张三",
  "role": "student",
  "avatar_url": "/uploads/avatars/abc.jpg",
  "grade": "初三",
  "school": "实验中学",
  "parent_phone": "13900139000",
  "created_at": "2025-10-01T08:00:00Z",
  "updated_at": "2025-10-12T10:30:00Z"
}
```

| 字段           | 类型       | 说明             |
| -------------- | ---------- | ---------------- |
| `id`           | `UUID`     | 用户 ID          |
| `phone`        | `str`      | 手机号           |
| `username`     | `str`      | 用户名           |
| `role`         | `UserRole` | 用户角色         |
| `avatar_url`   | `str`      | 头像 URL（可选） |
| `grade`        | `str`      | 年级（可选）     |
| `school`       | `str`      | 学校（可选）     |
| `parent_phone` | `str`      | 家长电话（可选） |
| `created_at`   | `datetime` | 创建时间         |
| `updated_at`   | `datetime` | 更新时间         |

### UserUpdate

用户信息更新请求

```python
{
  "username": "李四",
  "grade": "高一",
  "school": "第一中学"
}
```

**说明**: 所有字段均为可选，只更新提供的字段。

---

## 学习模块

**位置**: `src/schemas/learning.py`

### ChatSessionCreate

创建学习会话请求

```python
{
  "title": "数学问题讨论",
  "subject": "math"
}
```

| 字段      | 类型      | 必填 | 说明     |
| --------- | --------- | ---- | -------- |
| `title`   | `str`     | ❌   | 会话标题 |
| `subject` | `Subject` | ❌   | 学科分类 |

### ChatSessionResponse

学习会话响应

```python
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "数学问题讨论",
  "subject": "math",
  "message_count": 5,
  "created_at": "2025-10-12T08:00:00Z",
  "updated_at": "2025-10-12T10:30:00Z"
}
```

### QuestionCreate

提问请求

```python
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "什么是质数？",
  "subject": "math",
  "images": [
    "https://example.com/image1.jpg"
  ]
}
```

| 字段         | 类型        | 必填 | 说明                    |
| ------------ | ----------- | ---- | ----------------------- |
| `session_id` | `UUID`      | ✅   | 会话 ID                 |
| `content`    | `str`       | ✅   | 问题内容                |
| `subject`    | `Subject`   | ❌   | 学科                    |
| `images`     | `List[str]` | ❌   | 图片 URL 列表（多模态） |

### AnswerResponse

AI 回答响应

```python
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "question_id": "880e8400-e29b-41d4-a716-446655440003",
  "content": "质数是指大于1且只能被1和自身整除的自然数...",
  "confidence_score": 0.95,
  "sources": [
    {
      "title": "数学基础知识",
      "url": "https://example.com/doc1"
    }
  ],
  "created_at": "2025-10-12T10:31:00Z"
}
```

| 字段               | 类型         | 说明                 |
| ------------------ | ------------ | -------------------- |
| `id`               | `UUID`       | 回答 ID              |
| `question_id`      | `UUID`       | 问题 ID              |
| `content`          | `str`        | 回答内容             |
| `confidence_score` | `float`      | AI 置信度（0.0-1.0） |
| `sources`          | `List[Dict]` | 参考来源（可选）     |
| `created_at`       | `datetime`   | 创建时间             |

---

## 作业模块

**位置**: `src/schemas/homework.py`

### HomeworkCreate

创建作业请求

```python
{
  "title": "第三章练习题",
  "subject": "math",
  "grade": "初三",
  "description": "完成课本第三章习题",
  "deadline": "2025-10-20T23:59:59Z"
}
```

### HomeworkSubmissionCreate

提交作业请求

```python
{
  "homework_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "作业答案...",
  "images": [
    "https://example.com/homework1.jpg"
  ]
}
```

### HomeworkReviewResponse

作业批改结果响应

```python
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "submission_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "score": 85,
  "max_score": 100,
  "overall_comment": "整体完成良好，部分细节需要加强",
  "detailed_feedback": [
    {
      "question_number": 1,
      "score": 10,
      "max_score": 10,
      "comment": "完全正确"
    },
    {
      "question_number": 2,
      "score": 7,
      "max_score": 10,
      "comment": "步骤有遗漏"
    }
  ],
  "suggestions": [
    "加强解题步骤的完整性",
    "注意单位换算"
  ],
  "corrected_at": "2025-10-12T11:00:00Z"
}
```

---

## 错题模块

**位置**: `src/schemas/mistake.py`

### MistakeCreate

创建错题记录请求

```python
{
  "subject": "math",
  "question_content": "求解方程 x² + 5x + 6 = 0",
  "correct_answer": "x = -2 或 x = -3",
  "my_answer": "x = 2 或 x = 3",
  "knowledge_points": ["一元二次方程", "因式分解"],
  "difficulty": "medium",
  "source": "课堂练习",
  "images": [
    "https://example.com/mistake1.jpg"
  ]
}
```

| 字段               | 类型         | 必填 | 说明          |
| ------------------ | ------------ | ---- | ------------- |
| `subject`          | `Subject`    | ✅   | 学科          |
| `question_content` | `str`        | ✅   | 题目内容      |
| `correct_answer`   | `str`        | ❌   | 正确答案      |
| `my_answer`        | `str`        | ❌   | 我的答案      |
| `knowledge_points` | `List[str]`  | ❌   | 知识点列表    |
| `difficulty`       | `Difficulty` | ❌   | 难度          |
| `source`           | `str`        | ❌   | 来源          |
| `images`           | `List[str]`  | ❌   | 图片 URL 列表 |

### MistakeResponse

错题记录响应

```python
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "subject": "math",
  "question_content": "求解方程 x² + 5x + 6 = 0",
  "correct_answer": "x = -2 或 x = -3",
  "my_answer": "x = 2 或 x = 3",
  "ai_analysis": "错误原因：符号判断错误，需要注意因式分解的正负号...",
  "knowledge_points": ["一元二次方程", "因式分解"],
  "difficulty": "medium",
  "mastery_level": "learning",
  "review_count": 2,
  "next_review_date": "2025-10-15T08:00:00Z",
  "created_at": "2025-10-12T08:00:00Z",
  "updated_at": "2025-10-12T10:30:00Z"
}
```

| 字段               | 类型           | 说明                         |
| ------------------ | -------------- | ---------------------------- |
| `mastery_level`    | `MasteryLevel` | 掌握程度                     |
| `review_count`     | `int`          | 复习次数                     |
| `next_review_date` | `datetime`     | 下次复习日期（艾宾浩斯曲线） |
| `ai_analysis`      | `str`          | AI 错因分析                  |

### MistakeReviewCreate

提交复习记录请求

```python
{
  "mistake_id": "bb0e8400-e29b-41d4-a716-446655440006",
  "mastery_level": "mastered",
  "notes": "已经完全理解因式分解的方法"
}
```

### MistakeReviewResponse

复习记录响应

```python
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "mistake_id": "bb0e8400-e29b-41d4-a716-446655440006",
  "mastery_level": "mastered",
  "notes": "已经完全理解因式分解的方法",
  "next_review_date": "2025-10-19T08:00:00Z",
  "created_at": "2025-10-12T14:00:00Z"
}
```

---

## 学习目标模块

**位置**: `src/schemas/goal.py`

### LearningGoalCreate

创建学习目标请求

```python
{
  "title": "掌握一元二次方程",
  "description": "能够熟练解答一元二次方程相关题目",
  "subject": "math",
  "target_date": "2025-11-01T23:59:59Z",
  "milestones": [
    "理解因式分解法",
    "掌握配方法",
    "熟练公式法"
  ]
}
```

### LearningGoalResponse

学习目标响应

```python
{
  "id": "dd0e8400-e29b-41d4-a716-446655440008",
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "掌握一元二次方程",
  "description": "能够熟练解答一元二次方程相关题目",
  "subject": "math",
  "status": "in_progress",
  "progress": 45,
  "target_date": "2025-11-01T23:59:59Z",
  "completed_at": null,
  "milestones": [
    {
      "title": "理解因式分解法",
      "completed": true
    },
    {
      "title": "掌握配方法",
      "completed": false
    }
  ],
  "created_at": "2025-10-01T08:00:00Z",
  "updated_at": "2025-10-12T10:30:00Z"
}
```

| 字段           | 类型       | 说明                                                         |
| -------------- | ---------- | ------------------------------------------------------------ |
| `status`       | `str`      | 状态：`not_started`, `in_progress`, `completed`, `cancelled` |
| `progress`     | `int`      | 进度百分比（0-100）                                          |
| `completed_at` | `datetime` | 完成时间（可选）                                             |

---

## 分析模块

**位置**: `src/schemas/analytics.py`

### LearningStatsResponse

学习统计响应

```python
{
  "user_id": "660e8400-e29b-41d4-a716-446655440001",
  "period_days": 7,
  "total_questions": 45,
  "total_mistakes": 12,
  "total_reviews": 8,
  "active_days": 5,
  "avg_questions_per_day": 6.4,
  "subject_distribution": {
    "math": 25,
    "physics": 15,
    "english": 5
  },
  "mastery_distribution": {
    "not_mastered": 3,
    "learning": 6,
    "mastered": 3,
    "proficient": 0
  },
  "daily_activity": [
    {
      "date": "2025-10-12",
      "questions": 8,
      "mistakes": 2,
      "reviews": 1
    }
  ]
}
```

### SubjectAnalysisResponse

学科分析响应

```python
{
  "subject": "math",
  "total_mistakes": 12,
  "mastered_count": 5,
  "learning_count": 4,
  "not_mastered_count": 3,
  "knowledge_points": [
    {
      "name": "一元二次方程",
      "mistake_count": 5,
      "mastery_level": "learning"
    },
    {
      "name": "因式分解",
      "mistake_count": 3,
      "mastery_level": "mastered"
    }
  ],
  "difficulty_distribution": {
    "easy": 2,
    "medium": 7,
    "hard": 3
  }
}
```

---

## 文件模块

**位置**: `src/schemas/file.py`

### FileUploadResponse

文件上传响应

```python
{
  "id": "ee0e8400-e29b-41d4-a716-446655440009",
  "filename": "homework.jpg",
  "content_type": "image/jpeg",
  "size": 524288,
  "url": "https://example.com/uploads/homework.jpg",
  "thumbnail_url": "https://example.com/uploads/thumbnails/homework_thumb.jpg",
  "uploaded_at": "2025-10-12T11:00:00Z"
}
```

| 字段            | 类型       | 说明                   |
| --------------- | ---------- | ---------------------- |
| `id`            | `UUID`     | 文件 ID                |
| `filename`      | `str`      | 原始文件名             |
| `content_type`  | `str`      | MIME 类型              |
| `size`          | `int`      | 文件大小（字节）       |
| `url`           | `str`      | 文件访问 URL           |
| `thumbnail_url` | `str`      | 缩略图 URL（图片类型） |
| `uploaded_at`   | `datetime` | 上传时间               |

**支持的文件类型**:

- 图片: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- 文档: `.pdf`
- 最大文件大小: 10MB

---

## 通用模型

**位置**: `src/schemas/common.py`

### PaginationParams

分页参数（Query）

```python
{
  "page": 1,
  "page_size": 20,
  "sort_by": "created_at",
  "sort_order": "desc"
}
```

| 字段         | 类型  | 默认值       | 说明                    |
| ------------ | ----- | ------------ | ----------------------- |
| `page`       | `int` | `1`          | 页码（从 1 开始）       |
| `page_size`  | `int` | `20`         | 每页数量（最大 100）    |
| `sort_by`    | `str` | `created_at` | 排序字段                |
| `sort_order` | `str` | `desc`       | 排序方向：`asc`, `desc` |

### PaginatedResponse

分页响应包装

```python
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5,
  "has_next": true,
  "has_prev": false
}
```

---

## 字段验证规则

### 通用规则

| 字段类型 | 验证规则                  |
| -------- | ------------------------- |
| 手机号   | 11 位数字，1 开头         |
| 密码     | 8-32 位，包含字母和数字   |
| 用户名   | 2-20 位，中文、英文、数字 |
| 邮箱     | 标准邮箱格式验证          |
| URL      | 有效的 HTTP/HTTPS URL     |
| 日期     | ISO8601 格式，UTC 时区    |

### 业务规则

| 场景     | 规则             |
| -------- | ---------------- |
| 问题内容 | 1-2000 字符      |
| 标题     | 1-200 字符       |
| 描述     | 最多 1000 字符   |
| 分数     | 0-100 之间的数字 |
| 图片列表 | 最多 9 张图片    |

---

## 版本历史

| 日期       | 版本 | 变更说明                 |
| ---------- | ---- | ------------------------ |
| 2025-10-12 | v2.0 | 根据当前实现完全重写文档 |
| 2025-09-29 | v1.0 | 初始版本（草稿）         |

---

## 相关文档

- [API 端点文档](./endpoints.md) - 完整的 API 接口列表
- [错误码文档](./errors.md) - API 错误处理规范
- [API 概览](./overview.md) - RESTful 设计原则

---

**维护者**: 五好伴学开发团队
**反馈**: 通过 GitHub Issues 提交文档问题和改进建议

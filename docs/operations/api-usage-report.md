# API使用情况分析报告

> **生成时间**: 2025-10-26  
> **分析范围**: 后端 src/api/v1/endpoints vs 小程序 miniprogram/

---

## 📊 统计摘要

| 指标 | 数量 | 占比 |
|------|------|------|
| 后端定义端点总数 | 88 | 100% |
| 小程序调用端点总数 | 34 | - |
| **✅ 已使用端点** | 37 | 42.0% |
| **❌ 未使用端点** | 51 | 58.0% |
| ⚠️ 前端调用但后端未定义 | 34 | - |

---

## ❌ 未使用的后端端点 (51个)

**需要人工确认是否可以删除或标记为计划功能**


### 📦 analytics.py (6个未使用)

- `GET /knowledge-map`
- `GET /knowledge-points`
- `GET /learning-progress`
- `GET /learning-stats`
- `GET /subject-stats`
- `GET /user/stats`

### 📦 auth.py (15个未使用)

- `GET /check-email`
- `GET /check-username`
- `GET /verify-token`
- `POST /2fa/confirm`
- `POST /2fa/disable`
- `POST /avatar`
- `POST /change-password`
- `POST /deactivate`
- `POST /forgot-password`
- `POST /login`
- `POST /register`
- `POST /resend-verification`
- `POST /reset-password`
- `POST /send-verification-code`
- `POST /verify-email`

### 📦 file.py (7个未使用)

- `GET /:id/download`
- `GET /:id/preview`
- `GET /ai/:id`
- `GET /avatars/:id`
- `GET /stats/summary`
- `POST /upload-for-ai`
- `POST /upload-image-for-learning`

### 📦 goals.py (1个未使用)

- `GET /daily-goals`

### 📦 health.py (5个未使用)

- `GET /liveness`
- `GET /metrics`
- `GET /performance`
- `GET /rate-limits`
- `GET /readiness`

### 📦 homework.py (3个未使用)

- `POST /:id/retry`
- `POST /batch-delete`
- `POST /submit`

### 📦 homework_compatibility.py (1个未使用)

- `GET /:id/ocr`

### 📦 learning.py (10个未使用)

- `GET /analytics`
- `GET /questions/history`
- `GET /sessions/:id/history`
- `GET /sessions/:id/questions`
- `GET /stats/weekly`
- `GET /test`
- `PATCH /sessions/:id/activate`
- `PATCH /sessions/:id/archive`
- `POST /feedback`
- `POST /voice-to-text`

### 📦 mistakes.py (3个未使用)

- `GET /statistics`
- `GET /today-review`
- `POST /:id/review`

---

## ⚠️ 前端调用但后端未找到的端点

**可能原因**: 路径匹配问题、动态路由、或前端代码错误

- `/api/v1/auth/logout`
- `/api/v1/auth/me`
- `/api/v1/auth/profile`
- `/api/v1/auth/refresh-token`
- `/api/v1/auth/wechat-login`
- `/api/v1/files/upload`
- `/api/v1/homework/:id`
- `/api/v1/homework/:id/correct`
- `/api/v1/homework/list`
- `/api/v1/homework/submissions`
- `/api/v1/homework/submissions/:id`
- `/api/v1/homework/submissions/:id/correction`
- `/api/v1/homework/templates`
- `/api/v1/homework/templates/:id`
- `/api/v1/learning/ask`
- `/api/v1/learning/health`
- `/api/v1/learning/questions`
- `/api/v1/learning/questions/:id`
- `/api/v1/learning/questions/:id/add-to-mistakes`
- `/api/v1/learning/questions/:id/favorite`

... 还有 14 个

---

## ✅ 已确认使用的端点


### 📦 auth.py (5个使用中)

- `GET /me`
- `POST /logout`
- `POST /refresh`
- `POST /wechat-login`
- `PUT /profile`

### 📦 file.py (4个使用中)

- `DELETE /:id`
- `GET /`
- `GET /:id`
- `POST /upload`

### 📦 homework.py (9个使用中)

- `GET /stats`
- `GET /submissions`
- `GET /submissions/:id`
- `GET /submissions/:id/correction`
- `GET /templates`
- `GET /templates/:id`
- `POST /templates`
- `PUT /:id`
- `PUT /submissions/:id`

### 📦 homework_compatibility.py (2个使用中)

- `GET /list`
- `POST /:id/correct`

### 📦 learning.py (13个使用中)

- `DELETE /sessions/:id`
- `GET /health`
- `GET /questions`
- `GET /questions/search`
- `GET /recommendations`
- `GET /sessions`
- `GET /sessions/:id`
- `GET /stats/daily`
- `PATCH /sessions/:id`
- `POST /ask`
- ... 还有 3 个端点

### 📦 mistakes.py (1个使用中)

- `POST /`

### 📦 user.py (3个使用中)

- `GET /activities`
- `GET /preferences`
- `PUT /preferences`

---

## 🔍 详细分析建议


### Homework 模块
- ✅ 使用中: 9 个端点
- ❌ 未使用: 3 个端点
- 💡 **建议**: 大量使用，核心模块

### Learning 模块  
- ✅ 使用中: 13 个端点
- ❌ 未使用: 10 个端点
- 💡 **建议**: 大量使用，核心模块

### 合并可行性分析

---

## 📋 下一步行动


1. **立即处理**: 检查"前端调用但后端未定义"的端点
2. **本周处理**: 与产品确认"未使用端点"的状态
3. **规划处理**: 
   - 为计划功能添加 TODO 注释
   - 为废弃功能添加 @deprecated 注释
   - 创建备份分支后删除确认废弃代码

---

**报告生成**: `scripts/compare-api-usage.py`  
**复查周期**: 每季度一次

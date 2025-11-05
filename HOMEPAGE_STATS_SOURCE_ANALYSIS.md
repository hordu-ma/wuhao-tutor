# 首页统计数据来源分析报告

**分析时间**: 2025-11-05  
**分析范围**: 今日问答、学习报告、今日学习三个统计指标

---

## 📊 核心发现总结

### 结论

✅ **是的，这三个统计数据都来自真实的用户行为数据**  
⚠️ **但是数据统计逻辑存在一些问题需要说明**

---

## 1️⃣ 今日问答 (question_count)

### 数据来源

**表**: `questions` (学习问答表)  
**统计 SQL**:

```python
# src/services/analytics_service.py:120-123
question_stmt = select(func.count(Question.id).label("count")).where(
    Question.user_id == str(user_id)
)
question_count = question_result.scalar() or 0
```

### 触发场景

✅ **用户使用学习问答功能时会产生记录**

**触发入口**:

1. **小程序学习页面** (`pages/learning/index`)
2. **API 端点**: `POST /api/v1/learning/ask`
3. **数据创建**: `learning_service.py:498-523` (`_save_question()`)

**代码调用链**:

```
用户在小程序提问
  → miniprogram/api/learning.js:askQuestion()
  → POST /api/v1/learning/ask
  → learning_service.ask_question()
  → learning_service._save_question()
  → 创建 Question 记录到数据库
```

### ⚠️ 当前问题

1. **统计范围错误**:
   - ❌ 统计的是**所有时间**的问答总数
   - ✅ 应该统计**今日**的问答数
2. **字段命名误导**:
   - 前端显示"今日问答"
   - 实际返回"总问答数"

---

## 2️⃣ 学习报告 (homework_count)

### 数据来源

**表**: `homework_submissions` (作业提交表)  
**统计 SQL**:

```python
# src/services/analytics_service.py:111-116
homework_stmt = select(
    func.count(HomeworkSubmission.id).label("count"),
    func.avg(HomeworkSubmission.total_score).label("avg_score"),
).where(HomeworkSubmission.student_id == str(user_id))
homework_count = int(homework_stats[0]) if homework_stats else 0
```

### 触发场景

✅ **用户提交作业批改时会产生记录**

**触发入口**:

1. **作业批改功能** (图片上传批改)
2. **API 端点**: `POST /api/v1/homework/submit` (假设)
3. **数据创建**: 作业服务创建 `HomeworkSubmission` 记录

**实际含义**:

- **不是**"学习报告"的数量
- **而是**"作业提交"的总数
- 每次批改作业 = 1 条提交记录

### ⚠️ 当前问题

1. **命名不准确**:

   - ❌ 显示"学习报告"
   - ✅ 实际是"作业总数"或"批改次数"

2. **统计范围错误**:
   - ❌ 统计的是**所有时间**的作业总数
   - ✅ 应该根据场景调整（今日/本周/总计）

---

## 3️⃣ 今日学习 (study_hours)

### 数据来源

**计算公式（估算）**:

```python
# src/services/analytics_service.py:129-132
estimated_hours = (question_count * 5 + homework_count * 15) / 60

返回值: {
  "study_hours": round(estimated_hours, 1)
}
```

### 触发场景

⚠️ **这不是真实的学习时长，而是估算值**

**估算逻辑**:

- 每个问答 = 5 分钟
- 每个作业 = 15 分钟
- 总时长 = (问答数 × 5 + 作业数 × 15) / 60 小时

**示例**:

```
用户数据:
- 问答10次
- 作业3次

计算:
estimated_hours = (10 * 5 + 3 * 15) / 60
                = (50 + 45) / 60
                = 95 / 60
                ≈ 1.6 小时
```

### ⚠️ 当前问题

1. **非真实时长**:

   - ❌ 不是用户实际学习时间
   - ⚠️ 仅根据活动次数估算

2. **统计范围错误**:

   - ❌ 统计的是**所有时间**的估算时长
   - ✅ 显示"今日学习"但实际是总时长

3. **TODO 注释**:
   - 后端代码 `error_count: 0,  # TODO: 从错题本获取`
   - 说明还有功能未完善

---

## 🚨 核心问题汇总

### 问题 1: 时间范围不匹配

| 显示文本 | 实际统计   | 应该统计                   |
| -------- | ---------- | -------------------------- |
| 今日问答 | 总问答数   | 今天的问答数               |
| 学习报告 | 总作业数   | 总作业数（正确）或今日作业 |
| 今日学习 | 总估算时长 | 今天的估算时长             |

### 问题 2: 字段命名不准确

- "学习报告" 实际是 "作业批改次数"
- "今日学习" 实际是 "估算学习时长"

### 问题 3: 后端统计逻辑缺陷

后端 `get_user_stats()` 方法**没有**时间筛选：

```python
# ❌ 当前代码 - 无时间限制
question_stmt = select(func.count(Question.id)).where(
    Question.user_id == str(user_id)
)

# ✅ 应该改为 - 加入今日筛选
from datetime import datetime, timedelta

today_start = datetime.now().replace(hour=0, minute=0, second=0)
question_stmt = select(func.count(Question.id)).where(
    and_(
        Question.user_id == str(user_id),
        Question.created_at >= today_start
    )
)
```

---

## 🎯 推荐修复方案

### 方案 A: 快速修复（仅改显示文本）

**工作量**: 5 分钟  
**修改**: 前端文本与实际统计对齐

```xml
<!-- miniprogram/pages/index/index.wxml -->
<text class="stat-label">累计问答</text>  <!-- 改为"累计" -->
<text class="stat-label">作业批改</text>  <!-- 改为"作业批改" -->
<text class="stat-label">学习时长(小时)</text>  <!-- 改为"学习时长" -->
```

**优点**: 快速解决误导问题  
**缺点**: 首页显示的不是"今日"数据

---

### 方案 B: 后端修复（推荐）

**工作量**: 2-3 小时  
**修改**: 后端添加今日统计方法

#### 步骤 1: 新增今日统计 API

```python
# src/services/analytics_service.py

async def get_today_stats(self, user_id: UUID) -> Dict[str, Any]:
    """获取今日统计数据"""
    from datetime import datetime, timedelta

    # 今天的开始时间
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 统计今日问答
    question_stmt = select(func.count(Question.id)).where(
        and_(
            Question.user_id == str(user_id),
            Question.created_at >= today_start
        )
    )
    question_result = await self.db.execute(question_stmt)
    today_questions = question_result.scalar() or 0

    # 统计今日作业
    homework_stmt = select(func.count(HomeworkSubmission.id)).where(
        and_(
            HomeworkSubmission.student_id == str(user_id),
            HomeworkSubmission.created_at >= today_start
        )
    )
    homework_result = await self.db.execute(homework_stmt)
    today_homework = homework_result.scalar() or 0

    # 估算今日学习时长
    today_study_hours = (today_questions * 5 + today_homework * 15) / 60

    return {
        "today_question_count": today_questions,
        "today_homework_count": today_homework,
        "today_study_hours": round(today_study_hours, 1),
        "total_question_count": await self._count_all_questions(user_id),
        "total_homework_count": await self._count_all_homework(user_id),
    }
```

#### 步骤 2: 添加 API 端点

```python
# src/api/v1/endpoints/analytics.py

@router.get(
    "/user/today-stats",
    summary="获取今日统计数据",
    response_model=DataResponse[dict],
)
async def get_today_stats(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取用户今日统计数据"""
    analytics_service = get_analytics_service(db)
    stats = await analytics_service.get_today_stats(user_id=UUID(current_user_id))
    return DataResponse(success=True, data=stats, message="获取今日统计成功")
```

#### 步骤 3: 前端调用新 API

```javascript
// miniprogram/utils/api.js
analysis: {
  getTodayStats: () =>
    apiClient.get('/analytics/user/today-stats', {}, {
      enableCache: true,
      cache: { ttl: 1 * 60 * 1000 }, // 1分钟缓存
    }),
}

// miniprogram/pages/index/index.js
async loadUserStats() {
  const response = await api.analysis.getTodayStats();
  const stats = {
    questionCount: response.data.today_question_count || 0,
    reportCount: response.data.today_homework_count || 0,
    todayStudyTime: response.data.today_study_hours || 0,
  };
  this.setData({ stats });
}
```

**优点**: 数据准确，符合 UI 表达  
**缺点**: 需要后端开发

---

### 方案 C: 混合方案

**工作量**: 1 小时  
**修改**: 使用现有数据，调整前端显示

保留当前 API，但前端改为显示累计数据：

```xml
<view class="stat-item">
  <text class="stat-number">{{stats.questionCount}}</text>
  <text class="stat-label">累计问答</text>
  <text class="stat-hint">全部时间</text>
</view>
```

---

## 💡 数据流向图解

```
┌─────────────────────────────────────────────────────┐
│                    用户行为                          │
└───────────┬────────────────────────────┬────────────┘
            │                            │
    ┌───────▼────────┐          ┌───────▼────────┐
    │  学习问答功能   │          │  作业批改功能   │
    │ (learning/ask) │          │ (homework)     │
    └───────┬────────┘          └───────┬────────┘
            │                            │
    创建 Question 记录         创建 HomeworkSubmission
            │                            │
    ┌───────▼────────────────────────────▼────────┐
    │          数据库 (PostgreSQL)                 │
    │  - questions 表                              │
    │  - homework_submissions 表                   │
    └───────┬──────────────────────────────────────┘
            │
    ┌───────▼────────┐
    │ Analytics API  │ (当前实现)
    │ get_user_stats │
    └───────┬────────┘
            │
     统计全部时间数据
     - question_count (总问答)
     - homework_count (总作业)
     - study_hours (总估算时长)
            │
    ┌───────▼────────┐
    │  小程序首页     │
    │  显示"今日"    │ ❌ 名称与数据不符
    └────────────────┘
```

---

## 📝 验证方法

### 测试 1: 问答数据验证

```sql
-- 在生产数据库执行
SELECT COUNT(*) as total_questions,
       COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_questions
FROM questions
WHERE user_id = 'YOUR_USER_ID';
```

### 测试 2: 作业数据验证

```sql
SELECT COUNT(*) as total_homework,
       COUNT(CASE WHEN DATE(created_at) = CURRENT_DATE THEN 1 END) as today_homework
FROM homework_submissions
WHERE student_id = 'YOUR_USER_ID';
```

### 测试 3: 小程序操作验证

1. 记录当前统计数字
2. 使用学习问答功能提问 1 次
3. 刷新首页，观察"今日问答"是否+1
4. 提交 1 次作业批改
5. 刷新首页，观察"学习报告"是否+1

---

## 🎯 建议

### 短期（本周）

1. ✅ **先采用方案 A**：修改前端显示文本为"累计问答"、"作业批改"、"学习时长"
2. ✅ 添加时间范围说明（小字提示"全部时间"）

### 中期（下周）

1. ✅ **实施方案 B**：后端开发今日统计 API
2. ✅ 前端对接新 API
3. ✅ 保留总计数据作为"我的"页面展示

### 长期（未来）

1. ✅ 添加真实学习时长跟踪（页面停留时间）
2. ✅ 丰富统计维度（周报、月报）
3. ✅ 完善错题本统计

---

## ❓ 您的决策

请告诉我您希望采用哪个方案：

- **方案 A**: 快速修改文本（5 分钟） - 数据不变，消除误导
- **方案 B**: 完整修复（2-3 小时） - 开发今日统计功能
- **方案 C**: 混合方案（1 小时） - 保留现有，调整展示

我可以立即开始实施！ 🚀

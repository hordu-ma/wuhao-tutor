# Homework vs Learning 功能合并可行性分析

> **生成时间**: 2025-10-26  
> **分析目标**: 评估将 homework 相关功能合并到 learning 模块的可行性

---

## 📊 核心发现

### ❌ **您的疑问解答：homework_service.py 确实被小程序大量使用！**

虽然小程序端使用的是 `api.homework.*` 调用，但实际路由的**后端端点分散在多个文件**：

| 小程序调用                           | 后端实际端点                                      | 文件位置                       | 状态       |
| ------------------------------------ | ------------------------------------------------- | ------------------------------ | ---------- |
| `api.homework.getTemplates()`        | `GET /api/v1/homework/templates`                  | `homework.py` ✅               | 使用中     |
| `api.homework.submitHomework()`      | `POST /api/v1/homework/submissions`               | `homework.py` ✅               | 使用中     |
| `api.homework.getCorrectionResult()` | `GET /api/v1/homework/submissions/:id/correction` | `homework.py` ✅               | 使用中     |
| ~~`api.homework.getList()`~~         | ~~`GET /api/v1/homework/list`~~                   | `homework_compatibility.py` ⚠️ | **兼容层** |
| ~~`api.homework.correctHomework()`~~ | ~~`POST /api/v1/homework/:id/correct`~~           | `homework_compatibility.py` ⚠️ | **兼容层** |

**关键发现**：

- ✅ **homework.py** (主模块): 9 个端点在用，3 个未用
- ⚠️ **homework_compatibility.py** (兼容层): 2 个端点在用，专门为旧版小程序保留
- ✅ **homework_service.py** (业务逻辑): 被上述端点大量调用

---

## 🔍 详细使用情况分析

### 1️⃣ 小程序对 Homework API 的调用（实际使用）

#### ✅ **确认使用的端点** (11 个)

```javascript
// miniprogram/api/homework.js 中定义，小程序实际调用

✅ GET  /api/v1/homework/templates          // 获取作业模板列表
✅ GET  /api/v1/homework/templates/:id      // 获取模板详情
✅ POST /api/v1/homework/templates          // 创建模板
✅ GET  /api/v1/homework/submissions        // 获取提交列表
✅ GET  /api/v1/homework/submissions/:id    // 获取提交详情
✅ POST /api/v1/homework/submissions        // 提交作业（文本+图片）
✅ PUT  /api/v1/homework/submissions/:id    // 更新提交
✅ GET  /api/v1/homework/submissions/:id/correction  // 获取批改结果
✅ GET  /api/v1/homework/stats              // 统计数据
✅ GET  /api/v1/homework/list               // 兼容层：旧版列表接口
✅ POST /api/v1/homework/:id/correct        // 兼容层：旧版批改接口
```

**调用页面**:

- `miniprogram/pages/homework/list/index.js` - 作业列表页（176 行使用）
- `miniprogram/pages/homework/submit/index.js` - 作业提交页（87 行使用）
- `miniprogram/pages/homework/detail/index.js` - 作业详情页（54 行使用）

#### ❌ **未使用的端点** (3 个)

```javascript
❌ POST /api/v1/homework/submit             // 废弃？已改用 submissions
❌ POST /api/v1/homework/:id/retry          // 重新批改功能（未上线）
❌ POST /api/v1/homework/batch-delete       // 批量删除（未上线）
```

---

### 2️⃣ 小程序对 Learning API 的调用（问答功能）

#### ✅ **确认使用的端点** (13 个)

```javascript
✅ POST /api/v1/learning/ask                // AI问答（核心功能）
✅ GET  /api/v1/learning/sessions           // 会话列表
✅ POST /api/v1/learning/sessions           // 创建会话
✅ GET  /api/v1/learning/sessions/:id       // 会话详情
✅ PUT  /api/v1/learning/sessions/:id       // 更新会话
✅ DELETE /api/v1/learning/sessions/:id     // 删除会话
✅ GET  /api/v1/learning/questions          // 问题列表
✅ GET  /api/v1/learning/questions/:id      // 问题详情
✅ GET  /api/v1/learning/health             // 健康检查
✅ GET  /api/v1/learning/recommendations    // 推荐问题
... 还有3个
```

**调用页面**:

- `miniprogram/pages/learning/index/index.js` - 学习问答页（主要）

---

## 🤔 合并的矛盾点分析

### 问题 1: 为什么说 homework 被大量使用？

**真相**：

1. **后端层面**: `homework_service.py` 是核心业务逻辑，确实被大量使用
2. **API 层面**:
   - `homework.py` - 9 个端点（标准 RESTful 接口）
   - `homework_compatibility.py` - 2 个端点（旧版兼容）
3. **小程序层面**: 3 个页面文件，**317 行调用代码**

```bash
# 统计证据
grep -r "api.homework" miniprogram/pages/homework/*.js | wc -l
# 输出: 42 处直接调用
```

---

### 问题 2: Homework 和 Learning 的功能边界

| 维度           | Homework (作业批改)                    | Learning (学习问答)                 |
| -------------- | -------------------------------------- | ----------------------------------- |
| **核心场景**   | 提交作业 → AI 批改 → 查看结果          | 提问 → AI 回答 → 收藏/复习          |
| **数据模型**   | `HomeworkSubmission`, `HomeworkReview` | `Question`, `Answer`, `ChatSession` |
| **AI 调用**    | 批改 prompt（结构化输出）              | 问答 prompt（对话式）               |
| **用户流程**   | 单次提交-批改-查看                     | 多轮对话-历史记录                   |
| **小程序页面** | 3 个专用页面                           | 1 个问答页面                        |
| **重叠部分**   | ⚠️ **都调用 BailianService**           | ⚠️ **都需要知识点提取**             |

**结论**: 功能场景不同，但底层服务有重叠！

---

## 💡 合并方案建议

### 方案 A: 保持分离（推荐）✅

**理由**:

1. **业务逻辑清晰**: 作业批改和学习问答是两个独立场景
2. **代码已稳定**: homework 相关代码已被 3 个小程序页面深度依赖
3. **扩展性更好**: 未来可能增加更多作业类型（视频批改、口语评测）

**优化建议**:

```python
# 提取共用服务到基础层
src/services/
├── base/
│   ├── ai_service_base.py       # 统一AI调用基类
│   └── knowledge_base.py        # 知识点提取基类
├── homework_service.py          # 继承AI基类
└── learning_service.py          # 继承AI基类
```

---

### 方案 B: 部分合并（折中）⚠️

**只合并共用部分**:

1. 保留 `homework_service.py` 和 `learning_service.py`
2. 提取共用逻辑：
   - `BailianService` 调用封装
   - 知识点提取逻辑
   - 答案质量评估

**风险**: 重构成本高，可能引入 bug

---

### 方案 C: 完全合并（不推荐）❌

**需要改动**:

1. 重构 11+ 个 API 端点
2. 修改 3 个小程序页面（317 行代码）
3. 合并 2 个数据模型
4. 重写批改逻辑

**风险**:

- 破坏现有稳定功能
- 回归测试工作量巨大
- 用户体验可能受影响

---

## 📋 实际行动建议

### 立即执行（本周）

1. **清理 homework 未使用端点**

   ```python
   # 可以删除的端点（标记 @deprecated）
   - POST /api/v1/homework/submit  # 已被 submissions 替代
   - POST /api/v1/homework/:id/retry  # 未上线功能
   - POST /api/v1/homework/batch-delete  # 未上线功能
   ```

2. **标记兼容层代码**
   ```python
   # src/api/v1/endpoints/homework_compatibility.py
   # @deprecated 2025-10-26
   # 原因: 为旧版小程序保留，计划Q1统一升级后删除
   # 复查: 2025-12-31
   ```

---

### 中期优化（1-2 个月）

3. **提取共用 AI 基类**

   ```python
   # 新建 src/services/base/ai_service_base.py
   class AIServiceBase:
       def __init__(self):
           self.bailian = get_bailian_service()

       async def call_ai_with_context(self, messages, context):
           """统一的AI调用入口"""
           pass

   # homework_service.py 继承
   class HomeworkService(AIServiceBase):
       async def start_ai_review(self, ...):
           return await self.call_ai_with_context(...)
   ```

4. **统一知识点提取**

   ```python
   # 两个模块都调用同一个服务
   from src.services.knowledge.extraction_service import KnowledgeExtractionService

   # homework 和 learning 共用
   knowledge_service = KnowledgeExtractionService()
   ```

---

### 长期规划（Q1 2026）

5. **小程序 API 统一升级**

   - 删除 `homework_compatibility.py`
   - 小程序全部改用标准 RESTful 接口
   - 版本号升级到 v2

6. **考虑更高层抽象**
   ```python
   # 未来可以抽象为"AI辅导服务"
   src/services/
   ├── ai_tutoring/
   │   ├── homework_tutor.py    # 作业批改场景
   │   ├── qa_tutor.py          # 问答场景
   │   ├── practice_tutor.py    # 练习场景（新增）
   │   └── base_tutor.py        # 共用基类
   ```

---

## ⚠️ 风险提示

### 如果现在强行合并

| 风险项         | 影响范围                 | 严重程度 |
| -------------- | ------------------------ | -------- |
| API 端点重构   | 11 个端点需要迁移        | 🔴 高    |
| 小程序代码修改 | 3 个页面，317 行代码     | 🔴 高    |
| 数据模型冲突   | `Homework` vs `Question` | 🟡 中    |
| 业务逻辑混乱   | 批改逻辑 vs 问答逻辑     | 🔴 高    |
| 回归测试成本   | 所有作业和问答功能       | 🔴 高    |
| 用户体验影响   | 可能导致 bug             | 🟡 中    |

**保守估计工作量**: 5-7 个工作日，风险不可控

---

## ✅ 最终建议

### 推荐方案：保持分离 + 优化重构

1. **保留现状**

   - `homework_service.py` - 作业批改业务
   - `learning_service.py` - 学习问答业务
   - 两者功能场景明确，各司其职

2. **提取共用层**（本周开始）

   ```bash
   # 创建基础服务层
   mkdir -p src/services/base
   touch src/services/base/ai_service_base.py
   touch src/services/base/knowledge_base.py
   ```

3. **清理冗余代码**（本周完成）

   - 删除 3 个未使用的 homework 端点
   - 标记 homework_compatibility.py 为 deprecated

4. **文档更新**
   - 在架构文档中明确两个模块的职责边界
   - 添加 TODO: Q1 升级小程序 API

---

## 📞 决策建议

**问您自己 3 个问题**:

1. **业务侧**: 未来作业批改和学习问答是否会独立演化？

   - 如果是 → 保持分离 ✅
   - 如果否 → 考虑合并

2. **技术侧**: 是否有充足时间（5-7 天）+ 完整测试？

   - 如果有 → 可以尝试合并
   - 如果没有 → 保持现状 ✅

3. **产品侧**: 用户能接受功能暂时下线的风险吗？
   - 能接受 → 可以合并
   - 不能接受 → 保持分离 ✅

**我的建议**: **保持分离，优化共用部分**  
**理由**: 稳定性 > 代码优雅度，业务价值优先

---

**生成时间**: 2025-10-26  
**下次复查**: 2026-01-26  
**责任人**: 技术负责人

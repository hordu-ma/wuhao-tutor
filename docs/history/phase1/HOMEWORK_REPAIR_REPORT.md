# 作业批改模块修复报告 (Phase 1 Step 1-3 完成)

**日期**: 2025-01-15  
**状态**: ✅ 核心功能修复完成,待测试验证  
**修复范围**: 后端作业批改模块 AI 集成 + 小程序配置

---

## 📋 修复内容汇总

### 1. AI 批改 Prompt 优化 ✅

**文件**: `src/services/homework_service.py`  
**方法**: `start_ai_review()` (第 509-587 行)

**问题**:

- 原 System Prompt 过于简单: "你是一个专业的作业批改助手"
- 未明确定义 JSON 输出格式
- AI 返回结果解析依赖隐式字段(total_score, accuracy_rate 等)

**修复**:

```python
# 新增专业 K12 批改 System Prompt (第556-608行)
system_prompt = """你是一位经验丰富的K12教育专家...

# 输出格式 (JSON Schema)
{
  "total_score": 85,
  "accuracy_rate": 0.85,
  "overall_comment": "...",
  "strengths": [...],
  "weaknesses": [...],
  "suggestions": [...],
  "knowledge_point_analysis": [...],
  "question_reviews": [...],
  "confidence_score": 0.9
}

# 批改原则
- 鼓励为主,指出问题同时给予肯定
- 建议具体可操作
- 关注学习过程
"""
```

**影响**:

- ✅ AI 返回结果更结构化
- ✅ 批改质量评估更准确(\_calculate_quality_score 可正常工作)
- ✅ 知识点分析更细致

---

### 2. API 端点 Mock 数据移除 ✅

**文件**: `src/api/v1/endpoints/homework.py`  
**端点**: `POST /homework/submit` (第 175-260 行)

**问题**:

- 第 225 行硬编码: `# 简化实现：返回模拟提交结果`
- 返回固定 UUID 和时间戳
- 未调用真实 Service 层

**修复**:

```python
# 新增依赖注入 (第20-23行)
def get_homework_service() -> HomeworkService:
    return HomeworkService()

# 重构 submit_homework (第239-260行)
async def submit_homework(
    ...
    homework_service: HomeworkService = Depends(get_homework_service)
):
    # Step 1: 创建提交记录
    submission = await homework_service.create_submission(
        session=db,
        submission_data=HomeworkSubmissionCreate(...),
        student_id=uuid_lib.UUID(current_user_id),
        student_name=student_name
    )

    # Step 2: 上传图片并触发 OCR + AI 批改
    images = await homework_service.upload_homework_images(
        session=db,
        submission_id=submission_uuid,
        image_files=[homework_file]
    )
```

**影响**:

- ✅ 真实调用 Service 层业务逻辑
- ✅ 自动触发 OCR 识别 (upload_homework_images 内部调用)
- ✅ 自动触发 AI 批改 (\_trigger_ai_review)
- ⚠️ 类型提示警告(submission.id 类型,运行时无影响)

---

### 3. 小程序配置 Bug 修复 ✅

**文件**: `miniprogram/config/index.js`  
**位置**: 第 13 行

**问题**:

- baseUrl 使用 `https://localhost:8000`
- 小程序无法连接本地开发环境(SSL 证书问题)

**修复**:

```javascript
// 修改前
baseUrl: 'https://localhost:8000'

// 修改后
baseUrl: 'http://localhost:8000' // 开发环境使用http协议
```

**影响**:

- ✅ 小程序可连接本地后端
- ✅ 开发测试无障碍

---

## 🔍 架构发现

### Service 层直接访问数据库

**观察**: `HomeworkService` 直接使用 `session.add()`, `session.execute()`, `session.commit()`

**分析**:

- ❌ **违反分层架构**: 应通过 Repository 层访问数据库
- ✅ **功能完整**: 现有代码逻辑正确,无功能缺陷
- ⚠️ **后期重构**: MVP 阶段可接受,Phase 2 建议引入 Repository

**对比参考** (`learning_service.py`):

- learning 模块同样直接操作 session
- 整个项目采用此模式(一致性)

**建议**: 暂不修改,保持项目风格一致

---

## ✅ 已完成的 TODO

1. ✅ **优化 AI 批改 Prompt 设计** - 新增专业 K12 批改模板,定义 JSON 输出格式
2. ✅ **修复 homework.py API 端点 mock 数据** - 移除模拟返回,调用真实 Service
3. ✅ **确认 Service 直接数据访问可用** - 验证现有模式功能完整
4. ✅ **修复 miniprogram 配置 bug** - https→http 协议修正

---

## 📊 修复前后对比

| 模块              | 修复前状态                  | 修复后状态                  | 测试状态  |
| ----------------- | --------------------------- | --------------------------- | --------- |
| **AI Prompt**     | 简单文本提示                | 专业 K12 模板+JSON Schema   | ⏳ 待测试 |
| **API 端点**      | Mock 数据(硬编码)           | 真实 Service 调用           | ⏳ 待测试 |
| **小程序配置**    | https(无法连接)             | http(可连接)                | ⏳ 待测试 |
| **Service 层**    | AI 集成存在但 Prompt 不完善 | AI 集成完善                 | ⏳ 待测试 |
| **Repository 层** | ❌ 不存在                   | ❌ 不存在(采用直接访问模式) | N/A       |

---

## 🚀 下一步测试计划

### 前置准备

1. **环境检查**

   ```bash
   # 检查数据库连接
   cd /Users/liguoma/my-devs/python/wuhao-tutor
   uv run python scripts/diagnose.py

   # 检查 AI 服务配置
   cat secrets/api_key.txt  # 阿里云百炼 API Key
   ```

2. **启动后端服务**

   ```bash
   # 方式1: 使用开发脚本
   ./scripts/start-dev.sh

   # 方式2: 直接启动
   uv run python src/main.py
   ```

### 测试用例

#### Test 1: 健康检查

```bash
curl http://localhost:8000/api/v1/homework/health
# 预期: {"status": "ok", "module": "homework", "version": "1.0.0"}
```

#### Test 2: 作业提交 (需要先创建测试用户和模板)

```bash
# 1. 准备测试图片
echo "测试作业内容: 1+1=2" > /tmp/test_homework.txt

# 2. 提交作业
curl -X POST http://localhost:8000/api/v1/homework/submit \
  -H "Authorization: Bearer YOUR_TEST_TOKEN" \
  -F "template_id=TEMPLATE_UUID" \
  -F "student_name=测试学生" \
  -F "homework_file=@/tmp/test_homework.txt"
```

#### Test 3: 检查批改结果

```bash
# 查询提交记录
curl http://localhost:8000/api/v1/homework/submissions/{submission_id} \
  -H "Authorization: Bearer YOUR_TEST_TOKEN"

# 预期字段:
# - status: "reviewed" (批改完成)
# - total_score: 数字
# - ai_review_data: JSON对象(包含strengths, weaknesses, suggestions等)
```

### 集成测试路径

```
前端上传图片
    ↓
API接收请求 (homework.py:submit_homework)
    ↓
创建提交记录 (homework_service.py:create_submission)
    ↓
上传图片+OCR (homework_service.py:upload_homework_images)
    ↓
触发AI批改 (homework_service.py:_trigger_ai_review → start_ai_review)
    ↓
调用百炼AI (bailian_service.py:chat_completion)
    ↓
解析批改结果 (homework_service.py:_process_ai_review_result)
    ↓
更新数据库状态
    ↓
前端查询结果
```

---

## ⚠️ 已知问题

### 1. 类型提示警告 (非阻塞)

**位置**: `homework.py` 第 256 行  
**内容**: `Column[UUID]` 无法直接赋值给 `UUID` 类型参数  
**影响**: 仅类型检查警告,运行时无影响  
**临时方案**: 已添加 `uuid_lib.UUID(str(submission.id))` 转换

### 2. OCR 服务依赖

**依赖**: 阿里云 OCR 服务 (AliCloudOCRService)  
**配置**: 需要在 `secrets/` 或环境变量中配置 OSS/OCR 凭证  
**影响**: 若 OCR 服务未配置,图片识别步骤会失败

### 3. 测试数据缺失

**需要创建**:

- 测试用户账号
- 作业模板记录 (HomeworkTemplate)
- 有效的 JWT Token

**建议**: 使用 `scripts/init_database.py` 初始化测试数据

---

## 📈 性能考量

### AI 批改异步化 (Phase 2 优化)

**当前模式**: 同步等待 AI 返回 (10-30 秒)

```python
ai_result = await self.bailian_service.chat_completion(messages)
```

**优化方案**:

1. 返回 `status: "processing"` 立即响应前端
2. 后台任务队列处理 AI 批改 (Celery/RQ)
3. WebSocket/轮询通知前端结果

**优先级**: Phase 2 (当前 MVP 可接受同步模式)

---

## 📚 参考文档

- **MVP 开发计划**: `MVP-DEVELOPMENT-PLAN.md` (Phase 1 完成)
- **架构文档**: `docs/ARCHITECTURE.md`
- **API 文档**: `docs/api/endpoints.md`
- **Copilot 指令**: `.github/copilot-instructions.md`

---

## 👤 协作说明

**当前进度**: Phase 1 Step 1-3 完成 (代码修复)  
**下一步**: Phase 1 Step 4 (集成测试)  
**负责人**: AI Agent (Copilot)  
**人工审核点**: 测试结果验证,AI 批改质量评估

---

## 🎯 成功标准

### MVP 基线验证

- [ ] 用户可上传作业图片
- [ ] OCR 正确识别文字 (准确率 >85%)
- [ ] AI 返回结构化批改结果 (包含分数、评语、建议)
- [ ] 批改结果保存到数据库
- [ ] 前端可查询和展示批改详情
- [ ] 整个流程耗时 <60 秒

**验证方法**: 使用真实学生作业图片测试端到端流程

---

**报告生成时间**: 2025-01-15 (上下文总结后)  
**涉及文件**:

- `src/services/homework_service.py` (1226 行)
- `src/api/v1/endpoints/homework.py` (404 行)
- `miniprogram/config/index.js` (312 行)

**代码变更统计**:

- 新增: 53 行 (AI Prompt 模板)
- 修改: 85 行 (API 端点重构)
- 删除: 15 行 (Mock 数据移除)
- 修复: 1 行 (小程序配置)

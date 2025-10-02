# 五好伴学 MVP 分步骤开发计划

> **目标**: 让系统真正跑起来,实现核心功能的完整闭环  
> **原则**: MVP 优先,小步快跑,功能优先于完美  
> **预计总工期**: 19 天 (约 3 周)

**文档版本**: v1.0  
**创建时间**: 2025-10-02  
**状态**: 🔄 Phase 1 进行中

---

## 📊 项目现状诊断总结

### 完成度评估

| 模块         | 前端完成度 | 后端完成度 | 核心问题                   |
| ------------ | ---------- | ---------- | -------------------------- |
| 用户认证     | ✅ 100%    | ✅ 90%     | 无                         |
| **作业批改** | ✅ 95%     | ⚠️ **30%** | **AI 未对接,数据未持久化** |
| 学习问答     | ✅ 95%     | ✅ 90%     | 数据持久化待完善           |
| 学情分析     | ✅ 95%     | ⚠️ 40%     | 后端 API 缺失              |
| 个人中心     | ✅ 100%    | ✅ 80%     | 部分 API 未实现            |

### 关键发现

1. **架构优秀** - 三端(后端+Web+小程序)结构完整,技术栈现代
2. **前端就绪** - 小程序完成度 95%+,Web 前端 80%+
3. **后端空壳** - API 框架完整,但业务逻辑层大量"返回模拟数据"
4. **AI 对接不完整** - 只有`learning_service.py`真正调用了 AI,`homework`模块未实现
5. **数据持久化缺失** - Repository 层基本未使用

### MVP 启动的最大障碍

🔴 **作业批改功能** - 这是核心卖点,但后端只有 API 框架,缺少:

- HomeworkService (AI 批改逻辑)
- AI Prompt 设计
- 数据库 CRUD 操作
- 文件处理逻辑

---

## 🚀 Phase 1: 核心功能打通 (5-7 天)

### 🎯 目标

让作业批改功能从提交到批改结果完整跑通,实现真正的 AI 驱动批改。

### 📋 任务清单

#### ✅ Step 1.1: 创建 HomeworkService (2 天)

**文件**: `src/services/homework_service.py`

**核心功能**:

```python
class HomeworkService:
    async def submit_homework(
        self,
        user_id: UUID,
        template_id: UUID,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> HomeworkSubmissionResponse:
        """
        完整作业批改流程:
        1. 验证作业模板存在
        2. 保存作业文件
        3. 创建提交记录(数据库)
        4. 调用 BailianService 进行AI批改
        5. 解析AI返回结果
        6. 更新批改结果到数据库
        7. 返回批改报告
        """

    async def get_submission_detail(
        self,
        submission_id: UUID
    ) -> HomeworkSubmissionDetail:
        """查询作业提交详情和批改结果"""

    async def list_user_submissions(
        self,
        user_id: UUID,
        filters: SubmissionFilters
    ) -> PaginatedSubmissions:
        """获取用户提交历史"""

    async def get_grading_result(
        self,
        submission_id: UUID
    ) -> GradingResult:
        """获取批改结果详情"""
```

**技术要点**:

- 参考 `learning_service.py` 的 AI 调用模式
- **设计作业批改的 Prompt 工程**(核心!)
- 处理文件上传和存储
- 错误处理和重试机制
- 日志记录和监控

**AI Prompt 设计示例**:

```python
HOMEWORK_GRADING_SYSTEM_PROMPT = """
你是一位经验丰富的K12教育专家,负责批改学生作业。

# 批改标准
1. 答案正确性: 准确判断答案是否正确
2. 解题过程: 评估解题步骤的完整性和逻辑性
3. 知识点掌握: 分析学生对相关知识点的理解程度
4. 常见错误: 识别典型错误并给出纠正建议

# 输出格式
请以JSON格式输出批改结果:
{
  "overall_score": 85,  // 总分(0-100)
  "correctness": "correct" | "partial" | "incorrect",
  "detailed_analysis": {
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["问题1", "问题2"],
    "knowledge_points": [
      {
        "name": "知识点名称",
        "mastery_level": "excellent" | "good" | "fair" | "poor"
      }
    ]
  },
  "suggestions": [
    "具体改进建议1",
    "具体改进建议2"
  ],
  "similar_questions": [
    "相似题目推荐1",
    "相似题目推荐2"
  ]
}

# 批改原则
- 鼓励为主,指出问题同时给予肯定
- 建议具体可操作,避免空泛评价
- 关注学习过程,不仅关注结果
"""
```

**依赖**:

- `BailianService` (已存在)
- `HomeworkRepository` (需创建)
- `FileService` (可选,或直接使用现有 file.py)

**验收标准**:

- [ ] 单元测试覆盖核心方法
- [ ] AI 调用成功返回结构化结果
- [ ] 错误处理完善(AI 失败、超时等)
- [ ] 日志记录完整

---

#### ✅ Step 1.2: 完善 HomeworkRepository (1 天)

**文件**: `src/repositories/homework_repository.py`

**核心方法**:

```python
class HomeworkRepository(BaseRepository[HomeworkSubmission]):
    """作业提交数据访问层"""

    async def create_submission(
        self,
        user_id: UUID,
        template_id: UUID,
        file_url: str,
        metadata: Dict[str, Any]
    ) -> HomeworkSubmission:
        """创建作业提交记录"""

    async def update_grading_result(
        self,
        submission_id: UUID,
        grading_data: Dict[str, Any]
    ) -> HomeworkSubmission:
        """更新批改结果"""

    async def find_by_user_id(
        self,
        user_id: UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[HomeworkSubmission]:
        """查询用户提交历史"""

    async def find_by_id(
        self,
        submission_id: UUID
    ) -> Optional[HomeworkSubmission]:
        """根据ID查询提交记录"""

    async def update_status(
        self,
        submission_id: UUID,
        status: str
    ) -> HomeworkSubmission:
        """更新提交状态"""
```

**同时完善相关 Repository**:

- `HomeworkTemplateRepository` - 作业模板管理
- 确保 Repository 遵循 BaseRepository 模式

**数据库模型检查**:

```python
# src/models/homework.py
class HomeworkSubmission(BaseModel):
    __tablename__ = "homework_submissions"

    id: UUID
    user_id: UUID
    template_id: UUID
    file_url: str
    status: str  # pending, processing, completed, failed
    score: Optional[int]
    grading_result: Optional[Dict]  # JSON字段
    submitted_at: datetime
    graded_at: Optional[datetime]

    # 关系
    user: relationship("User")
    template: relationship("HomeworkTemplate")
```

**验收标准**:

- [ ] 所有 CRUD 操作测试通过
- [ ] 异常处理完善
- [ ] 支持分页和过滤
- [ ] 数据库迁移文件生成

---

#### ✅ Step 1.3: 重构 homework.py 端点 (1 天)

**文件**: `src/api/v1/endpoints/homework.py`

**重构内容**:

1. **删除所有模拟数据**
2. **注入真实 Service**
3. **完善请求/响应 Schema**

**重构后的代码示例**:

```python
from src.services.homework_service import (
    get_homework_service,
    HomeworkService
)

@router.post(
    "/submit",
    summary="提交作业",
    response_model=DataResponse[HomeworkSubmissionResponse]
)
async def submit_homework(
    template_id: UUID = Form(..., description="作业模板ID"),
    student_name: str = Form(..., description="学生姓名"),
    homework_file: UploadFile = File(..., description="作业文件"),
    additional_info: Optional[str] = Form(None, description="附加信息"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    提交作业进行AI批改

    完整流程:
    1. 验证文件格式和大小
    2. 上传文件到存储
    3. 调用 HomeworkService 进行批改
    4. 返回批改结果
    """
    # 文件验证
    if not homework_file.content_type.startswith(('image/', 'application/pdf')):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式"
        )

    # 获取Service
    homework_service = get_homework_service(db)

    # 提交作业
    try:
        result = await homework_service.submit_homework(
            user_id=UUID(current_user_id),
            template_id=template_id,
            file=homework_file,
            metadata={
                "student_name": student_name,
                "additional_info": additional_info
            }
        )

        return DataResponse(
            success=True,
            data=result,
            message="作业提交成功,AI正在批改中..."
        )

    except BailianServiceError as e:
        logger.error(f"AI批改失败: {e}")
        raise HTTPException(
            status_code=503,
            detail="AI服务暂时不可用,请稍后重试"
        )
```

**需要重构的端点**:

- [x] `POST /homework/submit` - 提交作业
- [x] `GET /homework/submissions` - 提交列表
- [x] `GET /homework/submissions/{id}` - 提交详情
- [x] `GET /homework/submissions/{id}/result` - 批改结果

**验收标准**:

- [ ] 所有端点调用真实 Service
- [ ] API 文档更新(Swagger)
- [ ] 集成测试通过
- [ ] 错误响应统一格式

---

#### ✅ Step 1.4: 配置修复 (0.5 天)

**小程序配置修复**:

```javascript
// miniprogram/config/index.js
const config = {
  api: {
    baseUrl: 'http://localhost:8000', // ← 修复 https → http
    version: 'v1',
    timeout: 10000,
  },
  // ... 其他配置
}
```

**环境变量检查**:

```bash
# .env
BAILIAN_API_KEY=your-api-key  # 确保已配置
BAILIAN_APPLICATION_ID=your-app-id
SQLALCHEMY_DATABASE_URI=sqlite+aiosqlite:///./wuhao_tutor_dev.db
```

**后端 CORS 配置**:

```python
# src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Web前端
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**验收标准**:

- [ ] 小程序可以成功连接后端
- [ ] Web 前端无 CORS 错误
- [ ] API 健康检查通过

---

#### ✅ Step 1.5: 基础联调测试 (1 天)

**测试场景 1: 小程序端到端测试**

```
1. 用户登录
2. 选择作业模板
3. 上传作业照片
4. 等待AI批改
5. 查看批改结果
6. 验证结果准确性
```

**测试场景 2: Web 前端测试**

```
1. 用户登录
2. 进入作业批改页面
3. 上传作业文件
4. 实时查看批改进度
5. 查看详细批改报告
```

**测试场景 3: API 直接测试**

```bash
# 提交作业
curl -X POST http://localhost:8000/api/v1/homework/submit \
  -F "template_id=xxx" \
  -F "student_name=测试学生" \
  -F "homework_file=@test_homework.jpg"

# 查询结果
curl http://localhost:8000/api/v1/homework/submissions/{id}
```

**性能基线测试**:

```bash
# 检查响应时间
./scripts/status-dev.sh --verbose

# 查看AI调用时长
# 目标: P95 < 5s
```

**验收标准**:

- [ ] 小程序提交作业流程通过
- [ ] Web 前端提交作业流程通过
- [ ] AI 批改返回结构化结果
- [ ] 批改结果正确存储到数据库
- [ ] 错误场景处理正确(文件过大、AI 失败等)

---

## 📈 Phase 1 里程碑

### 验收标准

- [x] HomeworkService 创建完成,核心方法实现
- [x] HomeworkRepository CRUD 操作完整
- [x] homework.py 端点重构完成,无模拟数据
- [x] 配置问题修复
- [x] 端到端测试通过

### 可演示功能

- ✅ 从小程序上传作业照片
- ✅ 后端调用阿里云百炼 AI 进行批改
- ✅ 返回结构化的批改结果(分数+分析+建议)
- ✅ 批改历史可查询
- ✅ 数据持久化到数据库

### 成果输出

- 📝 HomeworkService 代码 (~300 行)
- 📝 HomeworkRepository 代码 (~150 行)
- 📝 重构后的 homework.py (~200 行)
- 📝 单元测试 (~200 行)
- 📝 API 文档更新
- 📝 Phase 1 完成报告

---

## 🚀 Phase 2: 数据持久化完善 (3-4 天)

### 🎯 目标

确保所有模块的数据真实存储和查询,消除所有模拟数据。

### 📋 任务清单

#### Step 2.1: LearningService 数据持久化增强 (1 天)

**问题**: 当前`learning_service.py`虽然调用了 AI,但数据持久化不完整

**任务**:

```python
# src/services/learning_service.py

async def ask_question(...):
    # 1. 创建Question记录 ✅ (已实现)
    # 2. 调用AI获取答案 ✅ (已实现)
    # 3. 保存Answer记录 ⚠️ (需完善)
    # 4. 更新Session统计 ⚠️ (需添加)
    # 5. 异步更新学习分析数据 ⚠️ (需添加)
```

**完善内容**:

- Answer 记录完整保存(包括 tokens 使用量、响应时间等)
- Session 统计更新(问题数量、总 tokens 等)
- 学习分析数据异步更新(知识点掌握度等)

**验收标准**:

- [ ] 问答历史完整可查
- [ ] Session 统计准确
- [ ] 数据库字段完整无 NULL

---

#### Step 2.2: Analytics 后端实现 (2 天)

**新建文件**:

- `src/api/v1/endpoints/analytics.py`
- `src/services/analytics_service.py`
- `src/repositories/analytics_repository.py` (可选)

**核心 API**:

```python
# GET /api/v1/analytics/learning-stats
# 返回学习统计数据(对接小程序学情分析页面)
{
  "total_study_days": 28,
  "total_questions": 45,
  "total_homework": 12,
  "avg_score": 88,
  "knowledge_points": [
    {
      "name": "二次函数",
      "mastery_level": 0.85,
      "question_count": 10
    }
  ],
  "study_trend": [
    {"date": "2025-09-25", "activity": 8},
    {"date": "2025-09-26", "activity": 5}
  ]
}

# GET /api/v1/user/stats
# 返回用户统计(对接小程序个人中心)
{
  "join_date": "2025-01-15",
  "last_login": "2025-09-30T10:30:00Z",
  "homework_count": 12,
  "question_count": 45,
  "study_days": 28,
  "avg_score": 88,
  "error_count": 8,
  "study_hours": 36
}

# GET /api/v1/analytics/knowledge-map
# 返回知识图谱(可选,高级功能)
```

**数据来源**:

```python
class AnalyticsService:
    async def get_learning_stats(self, user_id: UUID, time_range: str):
        # 从多个数据源聚合:
        # - homework_submissions (作业数据)
        # - questions (问答数据)
        # - chat_sessions (会话数据)
        # 计算统计指标

    async def calculate_knowledge_mastery(self, user_id: UUID):
        # 基于问答和作业数据推断知识点掌握度
        # 使用简单的规则引擎或AI分析
```

**验收标准**:

- [ ] `/analytics/learning-stats` API 实现
- [ ] `/user/stats` API 实现
- [ ] 小程序学情分析页面正常展示
- [ ] 数据准确性验证

---

#### Step 2.3: 数据库迁移完善 (1 天)

**任务**:

```bash
# 1. 检查所有Model定义
ls src/models/

# 2. 确认字段完整性
# - User: 用户基本信息
# - ChatSession: 会话管理
# - Question: 问题记录
# - Answer: 答案记录
# - HomeworkSubmission: 作业提交
# - HomeworkTemplate: 作业模板

# 3. 生成迁移文件
make db-migrate

# 4. 应用迁移
make db-upgrade

# 5. 数据库备份
make db-backup
```

**检查清单**:

- [ ] 所有表创建成功
- [ ] 索引添加完整(user_id, created_at 等)
- [ ] 外键关系正确
- [ ] JSON 字段支持(grading_result 等)
- [ ] 时间戳字段默认值设置

**数据初始化**:

```bash
# 创建测试数据
uv run python scripts/init_database.py

# 验证数据
sqlite3 wuhao_tutor_dev.db "SELECT COUNT(*) FROM users;"
```

---

## 🌐 Phase 3: 前后端联调 (2-3 天)

### 🎯 目标

确保三端(后端+Web+小程序)协同工作无误。

### 📋 任务清单

#### Step 3.1: 小程序端联调 (1 天)

**测试流程**:

```
1. 用户注册/登录
   → 验证Token正常返回
   → 验证用户信息正确保存

2. 作业批改完整流程
   → 选择作业模板
   → 上传作业照片
   → 查看批改进度
   → 接收批改结果
   → 查看批改详情
   → 查看历史记录

3. 学习问答完整流程
   → 创建新会话
   → 发起提问
   → 接收AI回答
   → 继续追问(上下文连贯)
   → 查看问答历史
   → 切换会话

4. 学情分析数据展示
   → 学习报告数据正确
   → 学习进度图表正常
   → 知识点掌握度展示

5. 个人中心功能
   → 用户统计数据正确
   → 设置功能正常
   → 帮助中心可访问
```

**常见问题修复**:

- API 请求超时调整
- 图片上传大小限制
- 错误提示优化
- Loading 状态处理

**验收标准**:

- [ ] 所有核心流程测试通过
- [ ] 无崩溃或卡死
- [ ] 错误提示友好
- [ ] 数据展示正确

---

#### Step 3.2: Web 前端联调 (1 天)

**测试流程**: (同小程序)

**额外测试**:

- 浏览器兼容性(Chrome, Safari, Firefox)
- 响应式布局
- 路由跳转
- 状态管理(Pinia)

**CORS 问题处理**:

```python
# src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**验收标准**:

- [ ] Web 端核心流程通过
- [ ] 无 CORS 错误
- [ ] UI 交互流畅
- [ ] 数据正确展示

---

#### Step 3.3: 错误处理优化 (1 天)

**统一错误响应格式**:

```python
# src/schemas/common.py
class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    message: str

class ErrorDetail(BaseModel):
    code: str  # ERROR_CODE
    message: str  # 用户友好的错误描述
    details: Optional[Dict[str, Any]] = None  # 调试信息
```

**前端错误处理**:

```javascript
// miniprogram/utils/api.js
// 统一错误提示映射
const ERROR_MESSAGES = {
  VALIDATION_ERROR: '输入参数有误,请检查',
  AUTH_ERROR: '登录已过期,请重新登录',
  BAILIAN_SERVICE_ERROR: 'AI服务暂时不可用,请稍后重试',
  FILE_TOO_LARGE: '文件大小超过限制',
  // ...
}
```

**Loading 状态管理**:

```javascript
// 小程序页面
Page({
  data: {
    loading: false,
    submitting: false,
  },

  async submitHomework() {
    this.setData({ submitting: true });
    try {
      await api.post('/homework/submit', ...);
      wx.showToast({ title: '提交成功' });
    } catch (error) {
      this.handleError(error);
    } finally {
      this.setData({ submitting: false });
    }
  }
});
```

**验收标准**:

- [ ] 错误响应格式统一
- [ ] 前端错误提示友好
- [ ] Loading 状态正确显示
- [ ] 超时处理合理

---

## 🧪 Phase 4: MVP 基线测试 (1-2 天)

### 🎯 目标

确保 MVP 可演示,功能稳定可靠。

### 📋 任务清单

#### Step 4.1: 功能冒烟测试 (0.5 天)

**测试矩阵**:

| 功能         | 小程序 | Web | 后端 API | 状态 |
| ------------ | ------ | --- | -------- | ---- |
| 用户注册     | ☐      | ☐   | ☐        |      |
| 用户登录     | ☐      | ☐   | ☐        |      |
| 作业提交     | ☐      | ☐   | ☐        |      |
| AI 批改      | ☐      | ☐   | ☐        |      |
| 批改结果查看 | ☐      | ☐   | ☐        |      |
| 学习问答     | ☐      | ☐   | ☐        |      |
| 问答历史     | ☐      | ☐   | ☐        |      |
| 学情分析     | ☐      | ☐   | ☐        |      |
| 个人中心     | ☐      | ☐   | ☐        |      |

**测试脚本**:

```bash
# 运行自动化测试
uv run pytest tests/integration/test_homework_flow.py -v
uv run pytest tests/integration/test_learning_flow.py -v

# 手动测试检查清单
cat tests/manual_test_checklist.md
```

---

#### Step 4.2: 性能基线测试 (0.5 天)

**测试指标**:

```bash
# 1. API响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/homework/submit

# 目标:
# - 作业提交: < 3s (不含AI批改)
# - AI批改: < 10s
# - 问答接口: < 5s
# - 查询接口: < 200ms

# 2. 数据库查询性能
./scripts/performance_monitor.py status

# 3. 内存使用
docker stats wuhao-tutor-backend
```

**压力测试** (可选):

```bash
# 使用 locust 或 ab 进行简单压力测试
ab -n 100 -c 10 http://localhost:8000/api/v1/health
```

**验收标准**:

- [ ] API 响应时间达标
- [ ] 无慢查询(>100ms)
- [ ] 内存使用稳定
- [ ] 并发处理正常(10+ users)

---

#### Step 4.3: 部署准备 (0.5 天)

**环境配置文档**:

```bash
# 创建部署文档
touch docs/DEPLOYMENT-MVP.md

# 内容包括:
# 1. 环境变量配置清单
# 2. 数据库初始化步骤
# 3. 依赖安装说明
# 4. 启动命令
# 5. 健康检查方法
```

**Docker 部署测试**:

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 验证服务
docker-compose ps
curl http://localhost:8000/health
```

**数据库备份脚本**:

```bash
# 使用项目自带脚本
make db-backup

# 验证备份文件
ls -lh backups/
```

**监控配置** (可选):

```bash
# 配置 Prometheus
cp monitoring/prometheus.yml.example monitoring/prometheus.yml

# 启动监控
docker-compose -f docker-compose.monitoring.yml up -d
```

**验收标准**:

- [ ] Docker 部署成功
- [ ] 环境变量文档完整
- [ ] 数据库备份可用
- [ ] 健康检查通过

---

## 📊 MVP 验收标准

### 核心功能验收

#### 1. 作业批改功能 ✅

- [x] 用户可以上传作业(图片/PDF)
- [x] 后端调用阿里云百炼 AI 进行批改
- [x] 返回结构化批改结果:
  - 总分(0-100)
  - 详细分析(优点/问题)
  - 知识点掌握度评估
  - 改进建议
- [x] 批改历史可查询
- [x] 批改结果持久化存储

#### 2. 学习问答功能 ✅

- [x] 用户可以发起学习提问
- [x] AI 返回个性化解答
- [x] 支持上下文连续对话
- [x] 问答历史可查询
- [x] 数据完整存储

#### 3. 学情分析功能 ✅

- [x] 学习统计数据展示
- [x] 知识点掌握度分析
- [x] 学习趋势图表
- [x] 学习报告生成

#### 4. 个人中心功能 ✅

- [x] 用户信息展示
- [x] 学习数据统计
- [x] 设置功能可用
- [x] 帮助中心可访问

### 技术质量验收

#### 代码质量

- [x] 类型注解完整(mypy 检查通过)
- [x] 代码格式化(Black + isort)
- [x] 无明显 Bug 和异常
- [x] 核心功能有单元测试

#### API 质量

- [x] API 文档完整(Swagger)
- [x] 响应格式统一
- [x] 错误处理完善
- [x] 性能指标达标

#### 前端质量

- [x] 小程序核心流程通畅
- [x] Web 前端基本可用
- [x] UI 交互友好
- [x] 错误提示清晰

### 部署就绪

- [x] Docker 部署成功
- [x] 环境变量文档完整
- [x] 数据库迁移就绪
- [x] 健康检查可用

---

## 📅 时间线和里程碑

| 日期       | 里程碑                  | 可演示功能               | 负责人   |
| ---------- | ----------------------- | ------------------------ | -------- |
| Day 1-2    | HomeworkService 完成    | -                        | Dev Team |
| Day 3      | HomeworkRepository 完成 | -                        | Dev Team |
| Day 4      | homework.py 重构完成    | -                        | Dev Team |
| Day 5      | 配置修复+基础测试       | -                        | Dev Team |
| **Day 7**  | **Phase 1 完成**        | **作业批改功能完整可用** | All      |
| Day 8-9    | LearningService 完善    | -                        | Dev Team |
| Day 10-11  | Analytics 后端实现      | -                        | Dev Team |
| Day 12     | 数据库迁移完善          | -                        | Dev Team |
| **Day 14** | **Phase 2 完成**        | **所有数据持久化完成**   | All      |
| Day 15     | 小程序端联调            | -                        | Frontend |
| Day 16     | Web 前端联调            | -                        | Frontend |
| Day 17     | 错误处理优化            | -                        | All      |
| **Day 17** | **Phase 3 完成**        | **三端联调通过**         | All      |
| Day 18     | 功能冒烟测试            | -                        | QA       |
| Day 18.5   | 性能基线测试            | -                        | DevOps   |
| Day 19     | 部署准备                | -                        | DevOps   |
| **Day 19** | **MVP 上线**            | **系统可演示和试用**     | All      |

---

## 🎯 成功指标

### 功能指标

- ✅ 作业批改成功率 > 95%
- ✅ AI 响应时间 P95 < 10s
- ✅ 问答回答质量满意度 > 80%
- ✅ 系统稳定性 > 99%

### 用户体验指标

- ✅ 作业提交流程 < 5 步
- ✅ 批改结果展示清晰易懂
- ✅ 错误提示友好准确
- ✅ 界面响应流畅

### 技术指标

- ✅ API 响应时间 P95 < 200ms (不含 AI)
- ✅ 数据库查询时间 P95 < 50ms
- ✅ 代码测试覆盖率 > 60%
- ✅ 无严重 Bug 和安全漏洞

---

## 📋 Phase 1 开发检查清单

### 开发前准备

- [ ] 阅读完整开发计划
- [ ] 理解 HomeworkService 设计
- [ ] 准备测试数据和文件
- [ ] 配置开发环境

### Step 1.1: HomeworkService

- [ ] 创建`src/services/homework_service.py`
- [ ] 实现`submit_homework`方法
- [ ] 实现`get_submission_detail`方法
- [ ] 实现`list_user_submissions`方法
- [ ] 实现`get_grading_result`方法
- [ ] 设计 AI 批改 Prompt
- [ ] 添加错误处理
- [ ] 添加日志记录
- [ ] 编写单元测试
- [ ] 代码 Review

### Step 1.2: HomeworkRepository

- [ ] 创建`src/repositories/homework_repository.py`
- [ ] 实现`create_submission`方法
- [ ] 实现`update_grading_result`方法
- [ ] 实现`find_by_user_id`方法
- [ ] 实现`find_by_id`方法
- [ ] 实现`update_status`方法
- [ ] 检查数据库模型
- [ ] 生成数据库迁移
- [ ] 编写 Repository 测试
- [ ] 代码 Review

### Step 1.3: 重构 homework.py

- [ ] 删除所有模拟数据
- [ ] 注入 HomeworkService
- [ ] 重构`POST /submit`端点
- [ ] 重构`GET /submissions`端点
- [ ] 重构`GET /submissions/{id}`端点
- [ ] 重构`GET /submissions/{id}/result`端点
- [ ] 更新 API 文档
- [ ] 编写集成测试
- [ ] 代码 Review

### Step 1.4: 配置修复

- [ ] 修复小程序 baseUrl 配置
- [ ] 检查环境变量配置
- [ ] 配置 CORS
- [ ] 测试后端健康检查
- [ ] 测试前端连接

### Step 1.5: 联调测试

- [ ] 小程序提交作业测试
- [ ] Web 前端提交作业测试
- [ ] API 直接测试
- [ ] 验证 AI 批改结果
- [ ] 验证数据持久化
- [ ] 性能基线测试
- [ ] 错误场景测试
- [ ] 编写测试报告

### Phase 1 验收

- [ ] 所有检查项完成
- [ ] 核心功能演示通过
- [ ] 代码提交到 Git
- [ ] 文档更新
- [ ] Phase 1 完成报告

---

## 🔄 Phase 2-4 快速参考

### Phase 2: 数据持久化完善 (3-4 天)

- LearningService 数据持久化增强
- Analytics 后端实现
- 数据库迁移完善

### Phase 3: 前后端联调 (2-3 天)

- 小程序端联调
- Web 前端联调
- 错误处理优化

### Phase 4: MVP 基线测试 (1-2 天)

- 功能冒烟测试
- 性能基线测试
- 部署准备

---

## 📞 支持与协作

### 开发协作

- **每日站会**: 同步进度,解决阻塞
- **代码 Review**: 所有 PR 必须 Review 后合并
- **问题记录**: 使用 GitHub Issues 跟踪问题

### 技术支持

- **AI 服务问题**: 查看阿里云百炼文档
- **数据库问题**: 参考 `docs/DATA-ACCESS.md`
- **性能问题**: 使用 `scripts/performance_monitor.py`

### 文档参考

- 架构文档: `docs/ARCHITECTURE.md`
- 开发指南: `docs/DEVELOPMENT.md`
- API 文档: `docs/api/`
- AI 上下文: `AI-CONTEXT.md`

---

## ✅ 下一步行动

**立即开始**: Phase 1 Step 1.1 - 创建 HomeworkService

```bash
# 1. 创建服务文件
touch src/services/homework_service.py

# 2. 开始编码
# 参考: src/services/learning_service.py
# 参考: src/services/bailian_service.py

# 3. 运行测试
uv run pytest tests/unit/test_homework_service.py -v
```

**预计完成时间**: 2 天后 (2025-10-04)

---

**文档维护**: 请在每个阶段完成后更新此文档的状态和时间线。

**最后更新**: 2025-10-02  
**当前阶段**: 🔄 Phase 1 Step 1.1 进行中

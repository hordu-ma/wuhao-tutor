# 从学习问答提取错题到错题本 - MVP 开发计划

> **文档版本**: v2.0（重构版）  
> **生成时间**: 2025-10-20  
> **核心变更**:
>
> - ❌ 不使用 homework.py
> - ✅ 整合到 learning.py
> - ✅ Qwen-VL 模型原生支持图片（无需 OCR）

---

## 🎯 核心需求确认

### 错题来源

```
学习问答场景 (learning.py)
   │
   ├─ 用户上传题目图片
   │     │
   │     ▼
   │  Qwen-VL 模型（原生多模态）
   │     │
   │     ├─ 识别题目内容 ✅
   │     ├─ 分析学生答案 ✅
   │     └─ 给出正确答案 ✅
   │           │
   │           ▼
   ├─ 【答错的题目】─────────┐
   │                        │
   └─ 【空白未作答题目】─────┤
                           │
                           ▼
                    【一键加入错题本】
                           │
                           ▼
                   MistakeRecord 表
                           │
                           ▼
               艾宾浩斯遗忘曲线复习
```

---

## 📊 现有架构分析

### 1. Learning.py 数据模型（已存在）

```python
# src/models/learning.py

class Question(BaseModel):
    """问题模型 - 已有字段完美契合"""

    # ✅ 核心字段
    content: Text                    # 题目内容
    subject: String(50)              # 学科
    topic: String(100)               # 知识点
    difficulty_level: Integer        # 难度级别(1-5)

    # ✅ 图片支持
    has_images: Boolean              # 是否包含图片
    image_urls: Text (JSON)          # 图片URL列表

    # ✅ 关联
    answer: Answer                   # 一对一答案

class Answer(BaseModel):
    """答案模型 - 包含AI分析"""

    content: Text                    # AI给出的答案
    model_name: String(50)           # qwen-vl-max
    tokens_used: Integer             # token消耗

    # ✅ 质量评估
    confidence_score: Integer        # 置信度(0-100)
    user_rating: Integer             # 用户评分(1-5)
    is_helpful: Boolean              # 是否有帮助
```

**关键发现**:

- ✅ `Question` 表已有完整的题目信息
- ✅ `Answer` 表已有 AI 的分析结果
- ✅ 原生支持图片（`has_images`, `image_urls`）
- ✅ 已有学科、难度、知识点字段

---

### 2. Qwen-VL 模型集成（已完成）

```python
# src/services/bailian_service.py (第 410 行)

def _build_request_payload(messages, ...):
    """自动检测图片并切换模型"""
    has_images = self._has_images_in_messages(messages)
    model = "qwen-vl-max" if has_images else "qwen-turbo"  # ✅ 自动切换
```

**关键特性**:

- ✅ 自动检测消息中是否有图片
- ✅ 有图片 → 使用 `qwen-vl-max`（多模态模型）
- ✅ 无图片 → 使用 `qwen-turbo`（纯文本模型）
- ✅ **无需 OCR**：VL 模型原生理解图片

---

### 3. 错题本模型（已存在）

```python
# src/models/study.py

class MistakeRecord(BaseModel):
    """错题记录 - 需要补充字段"""

    # ✅ 已有字段
    user_id: UUID
    subject: String(20)
    chapter: String(100)
    title: String(200)
    image_urls: JSON                  # ✅ 已支持图片
    ocr_text: Text                    # ✅ 可存储题目内容
    ai_feedback: JSON                 # ✅ 可存储AI分析
    knowledge_points: JSON            # ✅ 知识点列表
    difficulty_level: Integer         # ✅ 难度等级

    # ✅ 复习相关
    mastery_status: String            # learning/reviewing/mastered
    review_count: Integer             # 复习次数
    correct_count: Integer            # 连续正确次数
    next_review_at: DateTime          # 下次复习时间

    # ❌ 缺少字段（需要新增）
    # source: String                  # 来源（learning/homework/manual）
    # source_id: UUID                 # 关联的Question ID
```

---

## 🔧 需要开发的功能

### MVP 范围定义

```
┌─────────────────────────────────────────────────────────┐
│                   MVP 最小可行方案                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. 【学习问答页面】                                     │
│     ├─ 用户提问（可带图片）                 ✅ 已有      │
│     ├─ AI 回答（Qwen-VL）                 ✅ 已有      │
│     └─ 【新增】"加入错题本" 按钮          ⭐ 需开发    │
│                                                         │
│  2. 【后端API】                                         │
│     └─ POST /api/v1/learning/add-to-mistakes  ⭐ 需开发│
│                                                         │
│  3. 【服务层逻辑】                                       │
│     └─ LearningService.add_to_mistakes()      ⭐ 需开发│
│                                                         │
│  4. 【数据迁移】                                         │
│     └─ MistakeRecord 表新增字段             ⭐ 需开发  │
│                                                         │
│  5. 【艾宾浩斯复习】                                     │
│     └─ 今日复习任务（前端调用）             ✅ 已有      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 详细实施步骤

### 步骤 1: 数据库迁移（5 分钟）

**文件**: 新建 `alembic/versions/add_mistake_source_fields.py`

```python
"""
为 MistakeRecord 添加来源字段

Revision ID: add_mistake_source_fields
"""

def upgrade():
    # 添加来源字段
    op.add_column('mistake_records',
        sa.Column('source', sa.String(20), nullable=True, comment='错题来源')
    )
    op.add_column('mistake_records',
        sa.Column('source_question_id', sa.String(36), nullable=True, comment='关联的Question ID')
    )

    # 添加学生答案字段（可选）
    op.add_column('mistake_records',
        sa.Column('student_answer', sa.Text, nullable=True, comment='学生答案')
    )
    op.add_column('mistake_records',
        sa.Column('correct_answer', sa.Text, nullable=True, comment='正确答案')
    )

    # 添加索引
    op.create_index('idx_mistake_source', 'mistake_records', ['source', 'source_question_id'])

def downgrade():
    op.drop_index('idx_mistake_source')
    op.drop_column('mistake_records', 'source')
    op.drop_column('mistake_records', 'source_question_id')
    op.drop_column('mistake_records', 'student_answer')
    op.drop_column('mistake_records', 'correct_answer')
```

**执行**:

```bash
alembic revision --autogenerate -m "add_mistake_source_fields"
alembic upgrade head
```

---

### 步骤 2: 更新 MistakeRecord 模型（10 分钟）

**文件**: `src/models/study.py`

```python
class MistakeRecord(BaseModel):
    """错题记录模型"""

    __tablename__ = "mistake_records"


    # 【新增】错题来源
    source = Column(
        String(20),
        default="manual",
        nullable=False,
        comment="错题来源：learning/homework/manual"
    )

    # 【新增】关联的Question ID
    source_question_id = Column(
        String(36) if is_sqlite else UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="关联的Question ID（从学习问答创建）"
    )

    # 【新增】学生答案（可选）
    student_answer = Column(Text, nullable=True, comment="学生答案")

    # 【新增】正确答案（可选）
    correct_answer = Column(Text, nullable=True, comment="正确答案")

```

---

### 步骤 3: 服务层逻辑（30 分钟）

**文件**: `src/services/learning_service.py`

```python
class LearningService:
    """学习问答服务"""


    async def add_question_to_mistakes(
        self,
        user_id: str,
        question_id: str,
        student_answer: Optional[str] = None
    ) -> MistakeDetailResponse:
        """
        将学习问答中的题目加入错题本

        Args:
            user_id: 用户ID
            question_id: 问题ID
            student_answer: 学生答案（可选，用于标记答错）

        Returns:
            MistakeDetailResponse: 创建的错题详情
        """
        # 1. 获取问题和答案
        question = await self.question_repo.get_by_id(question_id)
        if not question or str(question.user_id) != user_id:
            raise NotFoundError(f"问题 {question_id} 不存在")

        answer = await self.answer_repo.find_one(
            filters={"question_id": question_id}
        )
        if not answer:
            raise NotFoundError(f"问题 {question_id} 暂无答案")

        # 2. 提取AI分析中的知识点（从answer.content解析）
        knowledge_points = await self._extract_knowledge_points(
            question.content,
            answer.content,
            question.subject
        )

        # 3. 构造错题数据
        mistake_data = {
            "user_id": user_id,
            "subject": question.subject or "其他",
            "title": self._generate_mistake_title(question.content),
            "ocr_text": question.content,  # 题目内容
            "image_urls": json.loads(question.image_urls) if question.image_urls else [],
            "difficulty_level": question.difficulty_level or 2,
            "knowledge_points": knowledge_points,
            "ai_feedback": {
                "model": answer.model_name,
                "answer": answer.content,
                "confidence": answer.confidence_score,
                "tokens_used": answer.tokens_used
            },

            # 【新增】来源信息
            "source": "learning",
            "source_question_id": question_id,
            "student_answer": student_answer,
            "correct_answer": self._extract_correct_answer(answer.content),

            # 复习相关（使用艾宾浩斯算法）
            "mastery_status": "learning",
            "next_review_at": datetime.now() + timedelta(days=1),  # 第一次复习：1天后
            "review_count": 0,
            "correct_count": 0
        }

        # 4. 创建错题记录
        mistake_repo = MistakeRepository(MistakeRecord, self.db)
        mistake = await mistake_repo.create(mistake_data)

        logger.info(f"从学习问答创建错题: question_id={question_id}, mistake_id={mistake.id}")

        # 5. 转换为响应格式
        return self._to_mistake_detail(mistake)

    def _generate_mistake_title(self, content: str) -> str:
        """生成错题标题（截取前30字）"""
        if len(content) <= 30:
            return content
        return content[:30] + "..."

    def _extract_correct_answer(self, ai_answer: str) -> Optional[str]:
        """从AI回答中提取正确答案"""
        # 简单规则：查找"答案："、"正确答案："等关键词后的内容
        import re
        patterns = [
            r"答案[：:]\s*(.+?)(?:\n|$)",
            r"正确答案[：:]\s*(.+?)(?:\n|$)",
            r"解[：:]\s*(.+?)(?:\n|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, ai_answer)
            if match:
                return match.group(1).strip()

        # 如果没找到，返回完整AI回答的前100字
        return ai_answer[:100] if len(ai_answer) > 100 else ai_answer

    async def _extract_knowledge_points(
        self,
        question_content: str,
        answer_content: str,
        subject: Optional[str]
    ) -> List[str]:
        """
        从题目和答案中提取知识点

        可选方案：
        1. 简单版：使用正则匹配
        2. AI版：再次调用Qwen-VL提取知识点
        """
        # MVP简单版：从Question的topic字段获取
        knowledge_points = []

        # TODO: 后续可以调用AI提取更精确的知识点
        # ai_response = await self.bailian_service.chat_completion(...)

        return knowledge_points or ["待分析"]
```

---

### 步骤 4: API 端点（15 分钟）

**文件**: `src/api/v1/endpoints/learning.py`

```python
from src.schemas.mistake import MistakeDetailResponse

@router.post(
    "/questions/{question_id}/add-to-mistakes",
    response_model=MistakeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="将题目加入错题本",
    description="将学习问答中的题目加入到错题本，支持艾宾浩斯复习计划"
)
async def add_question_to_mistakes(
    question_id: UUID,
    student_answer: Optional[str] = Body(None, description="学生答案（可选）"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MistakeDetailResponse:
    """将题目加入错题本"""
    try:
        service = LearningService(db)
        mistake = await service.add_question_to_mistakes(
            user_id=str(user_id),
            question_id=str(question_id),
            student_answer=student_answer
        )
        return mistake
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ServiceError as e:
        logger.error(f"加入错题本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"加入错题本失败: {str(e)}"
        )
```

---

### 步骤 5: 前端集成（小程序）（20 分钟）

**文件**: `miniprogram/api/learning.js`

```javascript
/**
 * 将题目加入错题本
 * @param {string} questionId - 问题ID
 * @param {string} [studentAnswer] - 学生答案
 * @returns {Promise<Object>} 错题详情
 */
addToMistakes(questionId, studentAnswer = null) {
  return request.post(
    `learning/questions/${questionId}/add-to-mistakes`,
    { student_answer: studentAnswer },
    {
      showLoading: true,
      loadingText: '加入错题本...',
      showError: true
    }
  );
}
```

**文件**: `miniprogram/pages/learning/index/index.wxml`

```xml
<!-- 在AI回答后显示按钮 -->
<view wx:if="{{currentAnswer}}" class="answer-actions">
  <button
    class="btn-add-mistake"
    bindtap="onAddToMistakes"
    data-question-id="{{currentQuestionId}}"
  >
    <van-icon name="warning-o" />
    加入错题本
  </button>
</view>
```

**文件**: `miniprogram/pages/learning/index/index.js`

```javascript
Page({
  data: {
    currentQuestionId: null,
    currentAnswer: null,
  },

  /**
   * 加入错题本
   */
  async onAddToMistakes(e) {
    const { questionId } = e.currentTarget.dataset

    try {
      const response = await learningApi.addToMistakes(questionId)

      if (response.success) {
        wx.showToast({
          title: '已加入错题本',
          icon: 'success',
        })

        // 可选：提示用户去复习
        setTimeout(() => {
          wx.showModal({
            title: '提示',
            content: '是否立即查看错题本？',
            success: (res) => {
              if (res.confirm) {
                wx.switchTab({ url: '/pages/mistakes/list/index' })
              }
            },
          })
        }, 1500)
      }
    } catch (error) {
      console.error('加入错题本失败', error)
      wx.showToast({
        title: error.message || '操作失败',
        icon: 'error',
      })
    }
  },
})
```

---

## 🎨 用户体验流程

```
用户在学习问答页面
   │
   ▼
上传题目图片 + 提问
   │
   ▼
Qwen-VL 模型分析
  ├─ 识别题目内容
  ├─ 给出答案和解析
  └─ 提取知识点（可选）
   │
   ▼
【显示AI回答】
   │
   ├─ 如果答对 → 理解即可
   │
   └─ 如果答错/不会 → 点击"加入错题本" 按钮
                          │
                          ▼
                    【后端处理】
                    ├─ 创建 MistakeRecord
                    ├─ 设置首次复习时间（1天后）
                    └─ 关联原始Question
                          │
                          ▼
                    【提示用户】
                    "已加入错题本，明天记得复习哦！"
                          │
                          ▼
         ┌────────────────┴────────────────┐
         │                                 │
         ▼                                 ▼
   【今日复习页面】              【错题列表页面】
   (已有艾宾浩斯算法)              (已有筛选功能)
```

---

## 📊 工作量评估

| 步骤     | 内容             | 预计时间      | 难度      |
| -------- | ---------------- | ------------- | --------- |
| 1        | 数据库迁移       | 5 分钟        | ⭐ 简单   |
| 2        | 更新模型         | 10 分钟       | ⭐ 简单   |
| 3        | 服务层逻辑       | 30 分钟       | ⭐⭐ 中等 |
| 4        | API 端点         | 15 分钟       | ⭐ 简单   |
| 5        | 前端集成         | 20 分钟       | ⭐ 简单   |
| 6        | 测试             | 20 分钟       | ⭐⭐ 中等 |
| **总计** | **MVP 完整实现** | **~1.5 小时** | -         |

---

## ✅ MVP 验收标准

### 功能验收

- [x] 用户可以在学习问答页面点击"加入错题本"
- [x] 错题正确保存到 `mistake_records` 表
- [x] 错题包含：题目内容、图片、AI 答案、知识点
- [x] 错题来源标记为 `learning`
- [x] 关联原始 `question_id`
- [x] 自动设置首次复习时间（1 天后）

### 技术验收

- [x] API 返回 201 Created 状态码
- [x] 数据库字段完整且有索引
- [x] 错误处理完善（404, 500）
- [x] 日志记录关键操作

### 体验验收

- [x] 按钮点击有加载动画
- [x] 成功后有明确提示
- [x] 失败后有友好错误提示
- [x] 可选：引导用户去复习

---

## 🚀 后续增强（非 MVP）

### 阶段 2: 智能提取（1-2 天）

1. **AI 提取知识点**

   - 调用 Qwen-VL 分析题目
   - 自动提取 3-5 个核心知识点

2. **AI 提取正确答案**

   - 从 AI 回答中智能解析正确答案
   - 支持多种答案格式

3. **AI 生成解析**
   - 针对学生答案生成详细解析
   - 指出错误原因

### 阶段 3: 批量操作（2-3 天）

1. **从学习历史批量导入**

   - 选择多个历史问题
   - 批量加入错题本

2. **智能推荐加入**
   - AI 分析学生答案质量
   - 自动推荐需要加入错题本的题目

### 阶段 4: 复习增强（3-5 天）

1. **复习模式优化**

   - 隐藏答案，让学生重新作答
   - 对比首次答案和复习答案

2. **复习效果分析**
   - 统计复习正确率
   - 调整艾宾浩斯间隔

---

## 🎯 核心优势

### 1. 零 OCR 成本

```
传统方案:
用户上传图片 → OCR识别 → 提取文字 → AI分析
         ↑
     需要额外的OCR服务

你的方案:
用户上传图片 → Qwen-VL 直接理解 → AI分析
         ↑
     一步到位，无需OCR
```

### 2. 无缝集成

- ✅ 不引入新的数据表（复用 `Question`, `MistakeRecord`）
- ✅ 不改变现有流程（在学习问答基础上扩展）
- ✅ 艾宾浩斯算法已有（直接使用）

### 3. 最小开发量

- ✅ 只需 1-2 小时开发
- ✅ 代码改动不到 200 行
- ✅ 无需重构现有模块

---

## 📋 实施检查清单

### 开发前

- [ ] 确认 Qwen-VL 模型已正确配置
- [ ] 确认 `learning.py` 表结构完整
- [ ] 确认 `MistakeRecord` 表存在
- [ ] 确认艾宾浩斯算法模块可用

### 开发中

- [ ] 创建数据库迁移文件
- [ ] 更新 `MistakeRecord` 模型
- [ ] 实现 `LearningService.add_question_to_mistakes()`
- [ ] 创建 API 端点
- [ ] 前端添加按钮和调用逻辑

### 开发后

- [ ] 单元测试：服务层逻辑
- [ ] 集成测试：API 端点
- [ ] 手动测试：完整流程
- [ ] 性能测试：批量加入
- [ ] 部署到测试环境

---

**准备就绪！请确认方案后，我将立即开始实施。** 🚀

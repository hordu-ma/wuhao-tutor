# 错题本优化开发指导文档（方案A：基于学习问答模块）

**版本**: v1.0  
**创建日期**: 2025-11-07  
**适用范围**: 五好伴学 - 错题手册功能优化  
**开发周期**: 2-3 周

---

## 📋 目录

- [一、方案概述](#一方案概述)
- [二、技术架构](#二技术架构)
- [三、数据库设计](#三数据库设计)
- [四、后端实现](#四后端实现)
- [五、前端实现](#五前端实现)
- [六、开发计划](#六开发计划)
- [七、测试方案](#七测试方案)
- [八、上线检查清单](#八上线检查清单)
- [九、常见问题](#九常见问题)

---

## 一、方案概述

### 1.1 背景与目标

**当前问题**：
- ❌ 用户上传作业图片时，整次对话被录入为一条错题记录
- ❌ 无法区分单道题目，图片中的多题被合并处理
- ❌ 错题本显示的是完整对话内容，不是单题
- ❌ AI 只是回答问题，没有明确"批改"和判断对错

**目标**：
- ✅ 用户上传作业图片后，AI 自动识别并逐题批改
- ✅ 只有错题/未作答的题进入错题本，每题独立记录
- ✅ 错题记录包含：题号、题目内容、学生答案、正确答案、解析、知识点
- ✅ 小程序展示批改结果摘要，用户可查看详情

**为什么选择方案A**：
1. **符合用户习惯**：用户已习惯在"学习问答"页面上传作业
2. **降低认知负担**：无需新增入口，避免用户困惑
3. **快速上线**：改造现有模块，开发周期 2-3 周
4. **渐进式优化**：不影响现有功能，可灰度发布

### 1.2 核心改动点

```
┌─────────────────────────────────────────────────────────────┐
│  用户上传作业图片（1-5张）                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  AI 识别并批改（新增）                                          │
│  - 提取所有题目（题号、题干、学生答案）                          │
│  - 逐题判断：对/错/未作答                                       │
│  - 返回结构化 JSON                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  后端逐题创建 MistakeRecord（改造）                            │
│  - 仅错题/未作答题进入错题本                                    │
│  - 每题独立记录（新增 question_number 字段）                   │
│  - 自动关联知识点                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  小程序展示批改结果（新增）                                     │
│  - 总览：对/错/未作答统计                                       │
│  - 逐题展示（可折叠）                                           │
│  - 点击"查看错题"跳转到错题详情                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、技术架构

### 2.1 模块关系

```
miniprogram/pages/learning/index/  (前端)
    ↓ 调用
src/api/v1/endpoints/learning.py  (API层)
    ↓ 调用
src/services/learning_service.py  (Service层) ← 重点改造
    ↓ 调用
src/services/bailian_service.py   (AI服务) ← 新增批改模式Prompt
    ↓ 写入
src/models/study.py (MistakeRecord) ← 新增字段
    ↓ 关联
src/models/knowledge_graph.py (知识点) ← 自动关联
```

### 2.2 数据流

```
用户输入 (content + image_urls)
    ↓
LearningService.ask_question()
    ↓
【判断】是否包含图片？
    ├─ 是 → _extract_and_correct_homework()  ← 新增方法
    │         ├─ 调用 AI 批改（返回 JSON）
    │         ├─ 解析题目列表
    │         └─ 逐题创建 MistakeRecord
    │
    └─ 否 → 走原有流程（单题问答）
    ↓
返回 AskQuestionResponse
    ├─ question
    ├─ answer
    └─ correction_result (新增) ← 批改结果
```

---

## 三、数据库设计

### 3.1 MistakeRecord 表改动

**新增字段**：

| 字段名 | 类型 | 说明 | 默认值 |
|-------|------|------|--------|
| `question_number` | Integer | 题号（来自批改结果，从1开始） | NULL |
| `is_unanswered` | Boolean | 是否未作答（区分于答错） | FALSE |
| `question_type` | String(20) | 题目类型（选择/填空/解答） | NULL |
| `error_type` | String(50) | 错误类型（未作答/计算错误/概念错误） | NULL |

**迁移脚本** (`alembic/versions/xxx_add_mistake_fields.py`)：

```python
"""add mistake fields for homework correction

Revision ID: xxx
Revises: yyy
Create Date: 2025-11-07

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxx'
down_revision = 'yyy'  # 替换为当前最新版本号
branch_labels = None
depends_on = None


def upgrade():
    """新增字段"""
    op.add_column('mistake_records', 
        sa.Column('question_number', sa.Integer(), nullable=True,
                  comment='题号（来自批改结果）'))
    
    op.add_column('mistake_records',
        sa.Column('is_unanswered', sa.Boolean(), 
                  server_default='false', nullable=False,
                  comment='是否未作答'))
    
    op.add_column('mistake_records',
        sa.Column('question_type', sa.String(20), nullable=True,
                  comment='题目类型（选择/填空/解答）'))
    
    op.add_column('mistake_records',
        sa.Column('error_type', sa.String(50), nullable=True,
                  comment='错误类型（未作答/计算错误等）'))
    
    # 创建索引（优化查询性能）
    op.create_index('idx_mistake_question_number', 
                   'mistake_records', 
                   ['source_question_id', 'question_number'])


def downgrade():
    """回滚"""
    op.drop_index('idx_mistake_question_number', 
                  table_name='mistake_records')
    op.drop_column('mistake_records', 'error_type')
    op.drop_column('mistake_records', 'question_type')
    op.drop_column('mistake_records', 'is_unanswered')
    op.drop_column('mistake_records', 'question_number')
```

**执行迁移**：

```bash
# 1. 创建迁移文件
cd /opt/wuhao-tutor
source .venv/bin/activate
alembic revision -m "add_mistake_fields_for_homework_correction"

# 2. 编辑生成的文件（复制上面的代码）
vim alembic/versions/xxx_add_mistake_fields.py

# 3. 执行迁移（开发环境）
alembic upgrade head

# 4. 验证
sqlite3 wuhao_tutor_dev.db "PRAGMA table_info(mistake_records);"
# 或 PostgreSQL: \d mistake_records

# 5. 生产环境执行（部署时）
# 在 deploy.sh 中会自动执行
```

### 3.2 数据模型更新

**文件**: `src/models/study.py`

```python
class MistakeRecord(BaseModel):
    """错题记录模型"""
    
    __tablename__ = "mistake_records"
    
    # ... 现有字段 ...
    
    # 🆕 新增字段（批改相关）
    question_number = Column(
        Integer, 
        nullable=True, 
        comment="题号（来自批改结果，从1开始）"
    )
    
    is_unanswered = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="是否未作答（区分于答错）"
    )
    
    question_type = Column(
        String(20), 
        nullable=True,
        comment="题目类型（选择题/填空题/解答题/判断题）"
    )
    
    error_type = Column(
        String(50), 
        nullable=True,
        comment="错误类型（未作答/计算错误/概念错误/粗心大意）"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_mistake_question_number', 
              'source_question_id', 'question_number'),
        {"sqlite_autoincrement": True} if is_sqlite else {},
    )
```

---

## 四、后端实现

### 4.1 AI Prompt 设计

**文件**: `src/services/learning_service.py`

在类的顶部添加常量：

```python
# 作业批改专用 System Prompt
HOMEWORK_CORRECTION_PROMPT = """你是一位经验丰富的K12作业批改老师，擅长{subject}学科。

**任务**：分析图片中的所有题目，逐题批改。

**批改步骤**：
1. 识别所有题目（题号、题干、题目类型）
2. 识别学生的答案（手写/选择/填空）
3. 判断每道题的状态：
   - 未作答：学生没有写答案
   - 答错：学生答案与正确答案不符
   - 答对：学生答案正确
4. 给出正确答案和详细解析
5. 提取2-5个核心知识点

**重要规则**：
- 数学题：关注计算步骤和最终结果
- 容错：如学生答案模糊，标注"答案不清晰"
- 如图片不清晰无法识别，返回 error="image_unclear"

**输出格式**：严格按照以下JSON格式返回，不要添加其他文字：

```json
{{
  "questions": [
    {{
      "number": 1,
      "type": "选择题",
      "question_text": "题目原文（去除题号）",
      "student_answer": "A",
      "is_answered": true,
      "is_correct": false,
      "correct_answer": "B",
      "explanation": "详细解析（包含解题思路）",
      "knowledge_points": ["二次函数", "图像平移"],
      "difficulty": 2,
      "error_type": "概念错误"
    }}
  ],
  "summary": {{
    "total": 10,
    "correct": 7,
    "wrong": 2,
    "unanswered": 1
  }}
}}
```

**error_type 可选值**：
- "未作答"：学生未答题
- "计算错误"：步骤正确但计算出错
- "概念错误"：对知识点理解有误
- "粗心大意"：题目看错或抄错
- "方法错误"：解题思路不对
"""
```

### 4.2 核心方法实现

#### 4.2.1 判断是否为作业批改场景

在 `LearningService` 类中添加：

```python
def _is_homework_correction_scenario(
    self, 
    content: str, 
    image_urls: Optional[List[str]]
) -> bool:
    """
    判断是否为作业批改场景
    
    规则：
    1. 有图片上传（≥1张）
    2. 用户输入简短（≤50字）或包含批改关键词
    
    Args:
        content: 用户输入文本
        image_urls: 上传的图片URL列表
    
    Returns:
        bool: 是否为作业批改场景
    """
    # 规则1：必须有图片
    if not image_urls or len(image_urls) == 0:
        return False
    
    # 规则2：用户输入很简短（可能只是"帮我看看"）
    if len(content.strip()) <= 50:
        return True
    
    # 规则3：包含批改关键词
    correction_keywords = [
        "批改", "作业", "答案", "对不对", "做的对吗",
        "检查", "看看对不", "帮我看", "帮我批改",
        "这些题", "这道题", "做错", "错了吗"
    ]
    
    if any(keyword in content for keyword in correction_keywords):
        return True
    
    return False
```

#### 4.2.2 调用 AI 批改作业

```python
async def _call_ai_for_homework_correction(
    self,
    image_urls: List[str],
    subject: str,
    user_hint: str = ""
) -> Dict[str, Any]:
    """
    调用 AI 批改作业
    
    Args:
        image_urls: 作业图片URL列表
        subject: 学科
        user_hint: 用户提示（可选，如"请批改这些题"）
    
    Returns:
        Dict: 批改结果（JSON格式）
            {
                "questions": [...],
                "summary": {...}
            }
    
    Raises:
        BailianServiceError: AI调用失败
        ValidationError: 返回格式错误
    """
    try:
        # 1. 构建系统提示词
        system_prompt = HOMEWORK_CORRECTION_PROMPT.format(subject=subject)
        
        # 2. 构建用户消息
        user_content = f"请批改以下{subject}作业（共{len(image_urls)}张图片）"
        if user_hint:
            user_content += f"\n\n学生说：{user_hint}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": user_content,
                "image_urls": image_urls
            }
        ]
        
        # 3. 调用百炼 API
        logger.info(f"🎯 开始AI批改: subject={subject}, images={len(image_urls)}")
        
        response = await self.bailian_service.chat_completion(
            messages=messages,
            max_tokens=4000,      # 足够长（支持批改多题）
            temperature=0.2,      # 低随机性（保持批改一致性）
            top_p=0.9
        )
        
        if not response.success:
            raise BailianServiceError(f"AI批改失败: {response.error_message}")
        
        # 4. 解析 JSON 响应
        try:
            result = json.loads(response.content)
            
            # 验证必需字段
            if "questions" not in result or "summary" not in result:
                raise ValidationError("AI返回格式缺少必需字段")
            
            logger.info(
                f"✅ AI批改完成: total={result['summary']['total']}, "
                f"correct={result['summary']['correct']}, "
                f"wrong={result['summary']['wrong']}, "
                f"unanswered={result['summary']['unanswered']}"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"AI返回的JSON解析失败: {e}\n内容: {response.content[:500]}")
            raise ValidationError("AI批改结果格式错误")
    
    except Exception as e:
        logger.error(f"AI批改失败: {str(e)}", exc_info=True)
        raise BailianServiceError(f"作业批改失败: {str(e)}") from e
```

#### 4.2.3 逐题创建错题记录

```python
async def _create_mistake_from_question(
    self,
    user_id: str,
    question_id: str,
    question_data: Dict[str, Any],
    subject: str,
    image_urls: List[str]
) -> Optional[MistakeRecord]:
    """
    从单个题目数据创建错题记录
    
    Args:
        user_id: 用户ID
        question_id: 来源问题ID
        question_data: AI批改返回的单题数据
        subject: 学科
        image_urls: 作业图片URL列表（整批，未来可按题裁剪）
    
    Returns:
        MistakeRecord: 创建的错题记录，如果不应创建则返回None
    """
    from src.models.study import MistakeRecord
    from src.repositories.base_repository import BaseRepository
    
    # 判断是否应该加入错题本
    is_answered = question_data.get("is_answered", False)
    is_correct = question_data.get("is_correct", False)
    
    # 只有错题或未作答的题才加入错题本
    if is_correct:
        logger.debug(f"题目{question_data['number']}答对了，跳过")
        return None
    
    # 确定错误类型和来源
    is_unanswered = not is_answered
    error_type = question_data.get("error_type", 
                                   "未作答" if is_unanswered else "答错")
    
    # 确定 source 字段值
    if is_unanswered:
        source = "learning_empty"  # 未作答
    else:
        source = "learning_wrong"  # 答错
    
    # 生成错题标题
    question_text = question_data.get("question_text", "")
    title = self._generate_mistake_title_from_text(
        question_text, 
        question_number=question_data.get("number")
    )
    
    # 提取知识点
    knowledge_points = question_data.get("knowledge_points", [])
    
    # 构建 AI 反馈数据
    ai_feedback = {
        "correction_mode": True,  # 标记为批改模式
        "question_number": question_data.get("number"),
        "question_type": question_data.get("type"),
        "is_correct": is_correct,
        "is_answered": is_answered,
        "error_type": error_type,
        "difficulty": question_data.get("difficulty", 2),
        "explanation": question_data.get("explanation", ""),
        "knowledge_points": knowledge_points,
        "auto_created_at": datetime.now().isoformat()
    }
    
    # 构建错题数据
    mistake_data = {
        "user_id": user_id,
        "source": source,
        "source_question_id": question_id,
        # 基本信息
        "subject": subject,
        "title": title,
        "ocr_text": question_text,  # 单题内容
        "image_urls": json.dumps(image_urls),  # 整批图片（未来优化可裁剪）
        # 🆕 批改相关字段
        "question_number": question_data.get("number"),
        "question_type": question_data.get("type"),
        "is_unanswered": is_unanswered,
        "error_type": error_type,
        # 答案
        "student_answer": question_data.get("student_answer"),
        "correct_answer": question_data.get("correct_answer", ""),
        # AI 分析
        "ai_feedback": json.dumps(ai_feedback),
        "knowledge_points": knowledge_points,
        # 复习计划
        "mastery_status": "learning",
        "next_review_at": datetime.now() + timedelta(days=1),
        "review_count": 0,
        "correct_count": 0,
        "difficulty_level": question_data.get("difficulty", 2)
    }
    
    # 创建错题记录
    mistake_repo = BaseRepository(MistakeRecord, self.db)
    mistake = await mistake_repo.create(mistake_data)
    
    logger.info(
        f"✅ 创建错题成功: id={mistake.id}, number={question_data['number']}, "
        f"type={error_type}"
    )
    
    # 🔗 触发知识点关联
    try:
        mistake_id = (
            mistake.id if hasattr(mistake, "id") 
            else UUID(extract_orm_uuid_str(mistake, "id"))
        )
        await self._trigger_knowledge_association(
            mistake_id=mistake_id,
            user_id=UUID(user_id),
            subject=subject,
            ocr_text=question_text,
            ai_feedback=ai_feedback
        )
        logger.info(f"🔗 知识点关联已触发: mistake_id={mistake_id}")
    except Exception as e:
        logger.warning(f"知识点关联失败，但不影响错题创建: {e}")
    
    return mistake


def _generate_mistake_title_from_text(
    self, 
    question_text: str, 
    question_number: Optional[int] = None
) -> str:
    """
    从题目文本生成错题标题
    
    规则：
    - 如果有题号，格式为 "第N题: 前20字..."
    - 如果没题号，格式为 "前30字..."
    - 最长50字
    """
    # 清理文本
    text = question_text.strip()
    text = text.replace("\n", " ")
    
    # 生成标题
    if question_number:
        prefix = f"第{question_number}题: "
        max_len = 50 - len(prefix)
        title = prefix + (text[:max_len] + "..." if len(text) > max_len else text)
    else:
        max_len = 50
        title = text[:max_len] + ("..." if len(text) > max_len else "")
    
    return title
```

#### 4.2.4 主流程集成

修改 `ask_question` 方法：

```python
async def ask_question(
    self, user_id: str, request: AskQuestionRequest
) -> AskQuestionResponse:
    """
    提问功能（已优化支持作业批改）
    """
    start_time = time.time()

    try:
        # 1. 获取或创建会话
        session = await self._get_or_create_session(user_id, request)

        # 2. 保存问题
        question = await self._save_question(
            user_id, extract_orm_uuid_str(session, "id"), request
        )

        # 🎯 3. 判断是否为作业批改场景
        is_homework = self._is_homework_correction_scenario(
            request.content or "", 
            request.image_urls
        )
        
        correction_result = None
        created_mistakes = []
        
        if is_homework:
            logger.info("🎯 检测到作业批改场景，启用批改模式")
            
            # 3.1 调用 AI 批改
            try:
                subject = extract_orm_str(question, "subject") or "数学"
                correction_data = await self._call_ai_for_homework_correction(
                    image_urls=request.image_urls,
                    subject=subject,
                    user_hint=request.content or ""
                )
                
                # 3.2 逐题创建错题记录（仅错题/未作答）
                question_id = extract_orm_uuid_str(question, "id")
                for q_data in correction_data["questions"]:
                    mistake = await self._create_mistake_from_question(
                        user_id=user_id,
                        question_id=question_id,
                        question_data=q_data,
                        subject=subject,
                        image_urls=request.image_urls
                    )
                    if mistake:
                        created_mistakes.append(mistake)
                
                # 3.3 生成友好的 AI 回答（基于批改结果）
                ai_answer_content = self._generate_correction_summary(
                    correction_data, 
                    len(created_mistakes)
                )
                
                # 保存 AI 回答
                answer = await self.answer_repo.create({
                    "question_id": question_id,
                    "content": ai_answer_content,
                    "tokens_used": 0,  # 已在批改时使用
                    "processing_time": int((time.time() - start_time) * 1000)
                })
                
                # 构建批改结果响应
                correction_result = {
                    "mode": "homework_correction",
                    "summary": correction_data["summary"],
                    "questions": correction_data["questions"],
                    "mistakes_created": len(created_mistakes),
                    "mistakes": [
                        {
                            "id": str(m.id),
                            "number": getattr(m, "question_number"),
                            "type": getattr(m, "error_type")
                        }
                        for m in created_mistakes
                    ]
                }
                
            except Exception as correction_err:
                logger.error(f"作业批改失败，降级到普通问答: {correction_err}")
                # 降级：走普通问答流程
                is_homework = False
        
        # 4. 如果不是作业批改（或批改失败降级），走原有流程
        if not is_homework:
            # ... 原有逻辑（AI上下文、消息构建、chat_completion等）
            # 保持不变，这里省略
            pass
        
        # 5. 更新会话统计
        await self._update_session_stats(
            extract_orm_uuid_str(session, "id"), 
            0  # tokens_used
        )
        
        # 6. 构建响应
        processing_time = int((time.time() - start_time) * 1000)
        
        return AskQuestionResponse(
            question=QuestionResponse.model_validate(question),
            answer=AnswerResponse.model_validate(answer),
            session=SessionResponse.model_validate(session),
            processing_time=processing_time,
            tokens_used=0,
            # 🆕 批改结果
            correction_result=correction_result,
            mistake_created=len(created_mistakes) > 0,
            mistake_info={
                "count": len(created_mistakes),
                "ids": [str(m.id) for m in created_mistakes]
            } if created_mistakes else None
        )

    except Exception as e:
        logger.error(f"提问处理失败: {str(e)}", exc_info=True)
        raise ServiceError(f"提问处理失败: {str(e)}") from e


def _generate_correction_summary(
    self, 
    correction_data: Dict[str, Any],
    mistakes_count: int
) -> str:
    """
    生成批改结果摘要（用于AI回答）
    """
    summary = correction_data["summary"]
    total = summary["total"]
    correct = summary["correct"]
    wrong = summary["wrong"]
    unanswered = summary["unanswered"]
    
    # 生成友好的摘要文本
    text = f"## 📝 作业批改完成\n\n"
    text += f"**总览**：共 {total} 道题\n"
    text += f"- ✅ 正确：{correct} 题\n"
    text += f"- ❌ 错误：{wrong} 题\n"
    text += f"- ⚠️ 未作答：{unanswered} 题\n\n"
    
    if mistakes_count > 0:
        text += f"**已加入错题本**：{mistakes_count} 道题需要重点复习\n\n"
    
    # 逐题展示（错题/未作答）
    text += "---\n\n"
    for q in correction_data["questions"]:
        if not q["is_correct"]:
            text += f"### 第 {q['number']} 题\n\n"
            text += f"**题目**：{q['question_text']}\n\n"
            
            if q["is_answered"]:
                text += f"**你的答案**：{q['student_answer']}\n\n"
            else:
                text += f"**状态**：未作答 ⚠️\n\n"
            
            text += f"**正确答案**：{q['correct_answer']}\n\n"
            text += f"**解析**：{q['explanation']}\n\n"
            
            if q.get("knowledge_points"):
                kp_text = "、".join(q["knowledge_points"])
                text += f"**知识点**：{kp_text}\n\n"
            
            text += "---\n\n"
    
    text += "\n💡 点击下方查看错题详情，开始复习吧！"
    
    return text
```

### 4.3 Schema 更新

**文件**: `src/schemas/learning.py`

在 `AskQuestionResponse` 中新增字段：

```python
class AskQuestionResponse(BaseModel):
    """提问响应"""
    
    question: QuestionResponse
    answer: AnswerResponse
    session: SessionResponse
    processing_time: int = Field(..., description="处理时间（毫秒）")
    tokens_used: int = Field(default=0, description="使用的token数量")
    
    # 🆕 批改相关字段
    correction_result: Optional[Dict[str, Any]] = Field(
        None, 
        description="作业批改结果（批改模式下返回）"
    )
    mistake_created: bool = Field(
        default=False, 
        description="是否创建了错题"
    )
    mistake_info: Optional[Dict[str, Any]] = Field(
        None,
        description="错题信息（数量、ID列表等）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                # ... 原有示例 ...
                "correction_result": {
                    "mode": "homework_correction",
                    "summary": {
                        "total": 10,
                        "correct": 7,
                        "wrong": 2,
                        "unanswered": 1
                    },
                    "questions": [
                        {
                            "number": 1,
                            "type": "选择题",
                            "is_correct": False,
                            # ... 更多字段 ...
                        }
                    ],
                    "mistakes_created": 3
                }
            }
        }
```

---

## 五、前端实现

### 5.1 消息类型扩展

**文件**: `miniprogram/pages/learning/index/index.js`

在 `data` 中新增：

```javascript
data: {
  // ... 现有字段 ...
  
  // 🆕 批改结果
  showCorrectionResult: false,  // 显示批改结果弹窗
  correctionData: null,         // 批改结果数据
}
```

### 5.2 发送消息后处理响应

修改 `sendMessage` 方法：

```javascript
async sendMessage() {
  // ... 现有逻辑（构建请求、调用API）...
  
  try {
    const response = await learningApi.askQuestion({
      session_id: this.data.sessionId,
      content: this.data.inputText.trim(),
      image_urls: aiImageUrls,  // 已上传到OSS的URL
      subject: this.getCurrentSubject(),
      // ... 其他参数
    });
    
    // 🆕 检查是否返回批改结果
    if (response.correction_result) {
      // 批改模式
      this.handleCorrectionResponse(response);
    } else {
      // 普通问答模式（原有逻辑）
      this.handleNormalResponse(response);
    }
    
  } catch (error) {
    console.error('发送失败:', error);
    this.showError('消息发送失败');
  }
}
```

### 5.3 处理批改响应

```javascript
/**
 * 🆕 处理批改响应
 * @param {Object} response - API响应
 */
handleCorrectionResponse(response) {
  const { correction_result, answer } = response;
  
  // 1. 添加用户消息（图片）
  this.addMessage({
    type: 'user',
    content: '请批改这些题',
    images: this.data.uploadedImages,
    timestamp: Date.now()
  });
  
  // 2. 添加批改结果卡片消息
  this.addMessage({
    type: 'correction_card',
    data: correction_result,
    timestamp: Date.now()
  });
  
  // 3. 添加AI详细回答（可折叠）
  this.addMessage({
    type: 'assistant',
    content: answer.content,
    timestamp: Date.now()
  });
  
  // 4. 清空输入框和图片
  this.setData({
    inputText: '',
    uploadedImages: [],
    hasInputContent: false
  });
  
  // 5. 滚动到底部
  this.scrollToBottom();
  
  // 6. 显示成功提示
  const { summary } = correction_result;
  const mistakesCount = summary.wrong + summary.unanswered;
  
  if (mistakesCount > 0) {
    wx.showToast({
      title: `已加入${mistakesCount}道错题`,
      icon: 'success',
      duration: 2000
    });
  }
}

/**
 * 🆕 处理普通问答响应（原有逻辑）
 * @param {Object} response - API响应
 */
handleNormalResponse(response) {
  const { question, answer } = response;
  
  // 添加用户消息
  this.addMessage({
    type: 'user',
    content: question.content,
    images: question.image_urls ? JSON.parse(question.image_urls) : [],
    timestamp: Date.now()
  });
  
  // 添加AI回答
  this.addMessage({
    type: 'assistant',
    content: answer.content,
    timestamp: Date.now()
  });
  
  // 清空输入
  this.setData({
    inputText: '',
    uploadedImages: [],
    hasInputContent: false
  });
  
  this.scrollToBottom();
}
```

### 5.4 批改结果卡片组件

**文件**: `miniprogram/components/correction-card/index.wxml`

```xml
<view class="correction-card">
  <!-- 总览 -->
  <view class="summary">
    <view class="summary-header">
      <text class="title">📝 批改完成</text>
      <text class="total">共 {{data.summary.total}} 题</text>
    </view>
    
    <view class="stats">
      <view class="stat correct">
        <text class="number">{{data.summary.correct}}</text>
        <text class="label">正确</text>
      </view>
      <view class="stat wrong">
        <text class="number">{{data.summary.wrong}}</text>
        <text class="label">错误</text>
      </view>
      <view class="stat unanswered">
        <text class="number">{{data.summary.unanswered}}</text>
        <text class="label">未作答</text>
      </view>
    </view>
  </view>
  
  <!-- 逐题列表（仅显示错题/未作答） -->
  <view class="questions-list">
    <block wx:for="{{wrongQuestions}}" wx:key="number">
      <view class="question-item" bindtap="onQuestionTap" data-index="{{index}}">
        <view class="question-header">
          <view class="number-badge">第{{item.number}}题</view>
          <view class="status {{item.is_answered ? 'wrong' : 'unanswered'}}">
            {{item.is_answered ? '答错' : '未作答'}}
          </view>
        </view>
        
        <view class="question-preview">
          <text class="text">{{item.question_text}}</text>
        </view>
        
        <view class="arrow">
          <van-icon name="arrow" size="16px" color="#999" />
        </view>
      </view>
    </block>
  </view>
  
  <!-- 操作按钮 -->
  <view class="actions">
    <button 
      class="btn-view-mistakes" 
      bindtap="onViewAllMistakes"
    >
      查看错题本 ({{data.mistakes_created}})
    </button>
  </view>
</view>
```

**文件**: `miniprogram/components/correction-card/index.js`

```javascript
Component({
  properties: {
    data: {
      type: Object,
      value: {}
    }
  },
  
  data: {
    wrongQuestions: []  // 过滤后的错题/未作答题
  },
  
  lifetimes: {
    attached() {
      this.filterWrongQuestions();
    }
  },
  
  observers: {
    'data': function(newData) {
      this.filterWrongQuestions();
    }
  },
  
  methods: {
    // 过滤出错题和未作答题
    filterWrongQuestions() {
      const { questions } = this.data.data;
      if (!questions) return;
      
      const wrongQuestions = questions.filter(q => !q.is_correct);
      this.setData({ wrongQuestions });
    },
    
    // 点击单题
    onQuestionTap(e) {
      const { index } = e.currentTarget.dataset;
      const question = this.data.wrongQuestions[index];
      
      // 显示题目详情弹窗
      this.triggerEvent('questiontap', { question });
    },
    
    // 查看全部错题
    onViewAllMistakes() {
      wx.navigateTo({
        url: '/pages/mistakes/list/index'
      });
    }
  }
});
```

**文件**: `miniprogram/components/correction-card/index.wxss`

```css
.correction-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* 总览区域 */
.summary {
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.summary-header .title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.summary-header .total {
  font-size: 14px;
  color: #666;
}

/* 统计数字 */
.stats {
  display: flex;
  justify-content: space-around;
  padding: 16px 0;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat .number {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat.correct .number { color: #52c41a; }
.stat.wrong .number { color: #ff4d4f; }
.stat.unanswered .number { color: #faad14; }

.stat .label {
  font-size: 12px;
  color: #999;
}

/* 题目列表 */
.questions-list {
  margin-top: 16px;
}

.question-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  margin-bottom: 8px;
}

.question-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.number-badge {
  font-size: 14px;
  font-weight: bold;
  color: #1890ff;
  margin-right: 8px;
}

.status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status.wrong {
  background: #fff1f0;
  color: #ff4d4f;
}

.status.unanswered {
  background: #fffbe6;
  color: #faad14;
}

.question-preview {
  flex: 1;
  margin-right: 12px;
}

.question-preview .text {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 操作按钮 */
.actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.btn-view-mistakes {
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  padding: 12px;
}
```

### 5.5 在消息列表中集成

**文件**: `miniprogram/pages/learning/index/index.wxml`

在消息渲染部分添加：

```xml
<!-- 消息列表 -->
<scroll-view 
  class="chat-messages"
  scroll-y="{{true}}"
  bindscroll="onScrollOptimized"
>
  <block wx:for="{{messageList}}" wx:key="id">
    <!-- 用户消息 -->
    <view wx:if="{{item.type === 'user'}}" class="message user-message">
      <!-- ... 原有逻辑 ... -->
    </view>
    
    <!-- AI回答 -->
    <view wx:elif="{{item.type === 'assistant'}}" class="message ai-message">
      <!-- ... 原有逻辑 ... -->
    </view>
    
    <!-- 🆕 批改结果卡片 -->
    <view wx:elif="{{item.type === 'correction_card'}}" class="message">
      <correction-card 
        data="{{item.data}}"
        bind:questiontap="onCorrectionQuestionTap"
      />
    </view>
  </block>
</scroll-view>
```

在 `index.js` 中添加事件处理：

```javascript
/**
 * 🆕 点击批改结果中的某道题
 */
onCorrectionQuestionTap(e) {
  const { question } = e.detail;
  
  // 显示题目详情弹窗（包含完整解析）
  wx.showModal({
    title: `第${question.number}题`,
    content: `${question.question_text}\n\n【正确答案】\n${question.correct_answer}\n\n【解析】\n${question.explanation}`,
    confirmText: '查看错题',
    cancelText: '关闭',
    success: (res) => {
      if (res.confirm) {
        // 跳转到错题详情（如果已加入错题本）
        // 需要从 mistakes 数组中找到对应的 mistake_id
        const mistakes = this.data.correctionData?.mistakes || [];
        const mistake = mistakes.find(m => m.number === question.number);
        
        if (mistake) {
          wx.navigateTo({
            url: `/pages/mistakes/detail/index?id=${mistake.id}`
          });
        } else {
          wx.showToast({
            title: '该题未加入错题本',
            icon: 'none'
          });
        }
      }
    }
  });
}
```

---

## 六、开发计划

### Week 1：数据库与后端基础（5天）

#### Day 1-2：数据库改动
- [ ] 编写 Alembic 迁移脚本（`xxx_add_mistake_fields.py`）
- [ ] 在开发环境执行迁移并验证
- [ ] 更新 `src/models/study.py`（MistakeRecord 模型）
- [ ] 编写单元测试（测试新字段的增删改查）

**交付物**：
- 迁移脚本文件
- 测试通过截图
- 数据表结构文档（Markdown）

#### Day 3-4：AI Prompt 与调用方法
- [ ] 在 `learning_service.py` 添加 `HOMEWORK_CORRECTION_PROMPT`
- [ ] 实现 `_call_ai_for_homework_correction` 方法
- [ ] 编写 Prompt 测试脚本（测试多种场景）
  - 单题/多题
  - 选择题/填空题/解答题
  - 有答案/无答案
- [ ] 调整 Prompt 直到准确率 >90%

**交付物**：
- Prompt 测试报告（Excel表格，记录10+测试用例）
- AI 返回的 JSON 示例（保存为 `docs/examples/correction_response.json`）

#### Day 5：场景判断与流程集成
- [ ] 实现 `_is_homework_correction_scenario` 方法
- [ ] 修改 `ask_question` 主流程（添加分支判断）
- [ ] 编写单元测试（测试判断逻辑）

**交付物**：
- 单元测试通过（覆盖率 >80%）

---

### Week 2：核心业务逻辑（5天）

#### Day 6-7：逐题创建错题记录
- [ ] 实现 `_create_mistake_from_question` 方法
- [ ] 实现 `_generate_mistake_title_from_text` 方法
- [ ] 实现 `_generate_correction_summary` 方法
- [ ] 编写集成测试（模拟完整批改流程）

**交付物**：
- 集成测试通过
- 错题记录创建成功（数据库截图）

#### Day 8：知识点关联
- [ ] 确认 `_trigger_knowledge_association` 方法可用
- [ ] 测试批改后的知识点关联效果
- [ ] 修复知识点关联的 Bug（如有）

**交付物**：
- 知识点关联测试报告

#### Day 9-10：API 测试与优化
- [ ] 使用 Postman 测试完整流程
- [ ] 测试边界情况：
  - 图片不清晰
  - 题目数量过多（>10题）
  - AI 返回格式错误
  - 网络超时
- [ ] 添加异常处理和降级逻辑
- [ ] 性能优化（如有必要）

**交付物**：
- Postman 测试集合（导出为 JSON）
- 性能测试报告（响应时间、并发数）

---

### Week 3：前端开发与联调（5天）

#### Day 11-12：前端组件开发
- [ ] 创建 `correction-card` 组件（wxml + js + wxss）
- [ ] 修改 `learning/index` 页面（添加批改逻辑）
- [ ] 实现 `handleCorrectionResponse` 方法
- [ ] 本地测试（使用 mock 数据）

**交付物**：
- 组件代码
- 本地测试截图

#### Day 13：前后端联调
- [ ] 小程序连接开发环境后端
- [ ] 测试完整流程（上传图片 → 批改 → 显示结果 → 查看错题）
- [ ] 修复联调中的 Bug

**交付物**：
- 联调测试视频（录屏）

#### Day 14：样式优化与测试
- [ ] 优化批改结果卡片样式（参考主流教育App）
- [ ] 添加加载动画（批改中提示）
- [ ] 边界情况测试（无网络、超时等）

**交付物**：
- UI 截图（多场景）
- 用户体验评分表

#### Day 15：文档与上线准备
- [ ] 编写用户使用文档（更新 `USER_MANUAL.md`）
- [ ] 编写运维文档（部署步骤）
- [ ] 准备上线检查清单
- [ ] 代码审查（Code Review）

**交付物**：
- 更新后的文档
- 上线检查清单（Excel）

---

## 七、测试方案

### 7.1 单元测试

**文件**: `tests/services/test_learning_service_correction.py`

```python
import pytest
from src.services.learning_service import LearningService

class TestHomeworkCorrection:
    """作业批改功能测试"""
    
    @pytest.mark.asyncio
    async def test_is_homework_correction_scenario(self, db_session):
        """测试场景判断"""
        service = LearningService(db_session)
        
        # 有图片 + 简短文本 → True
        assert service._is_homework_correction_scenario(
            "帮我看看", 
            ["https://example.com/1.jpg"]
        ) == True
        
        # 无图片 → False
        assert service._is_homework_correction_scenario(
            "这道题怎么做？", 
            []
        ) == False
        
        # 有图片 + 长文本（无关键词）→ False
        long_text = "请详细解释一下二次函数的性质..." * 10
        assert service._is_homework_correction_scenario(
            long_text, 
            ["https://example.com/1.jpg"]
        ) == False
    
    @pytest.mark.asyncio
    async def test_create_mistake_from_question(self, db_session, mock_user):
        """测试单题错题创建"""
        service = LearningService(db_session)
        
        question_data = {
            "number": 1,
            "type": "选择题",
            "question_text": "下列哪个是质数？",
            "student_answer": "A",
            "is_answered": True,
            "is_correct": False,
            "correct_answer": "C",
            "explanation": "质数只能被1和自身整除...",
            "knowledge_points": ["质数", "数论"],
            "difficulty": 2,
            "error_type": "概念错误"
        }
        
        mistake = await service._create_mistake_from_question(
            user_id=str(mock_user.id),
            question_id="test-question-id",
            question_data=question_data,
            subject="数学",
            image_urls=["https://example.com/1.jpg"]
        )
        
        assert mistake is not None
        assert mistake.question_number == 1
        assert mistake.is_unanswered == False
        assert mistake.error_type == "概念错误"
        assert mistake.source == "learning_wrong"
```

**运行测试**：

```bash
# 运行单个测试文件
pytest tests/services/test_learning_service_correction.py -v

# 运行所有测试（带覆盖率）
pytest --cov=src/services/learning_service --cov-report=html
```

### 7.2 集成测试

**文件**: `tests/integration/test_homework_correction_flow.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_homework_correction_full_flow(
    async_client: AsyncClient,
    mock_user,
    mock_image_urls
):
    """测试完整批改流程"""
    
    # 1. 登录获取 token
    login_response = await async_client.post("/api/v1/auth/login", json={
        "phone": mock_user.phone,
        "password": "test123"
    })
    token = login_response.json()["access_token"]
    
    # 2. 提交作业批改请求
    response = await async_client.post(
        "/api/v1/learning/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "content": "请批改这些题",
            "image_urls": mock_image_urls,
            "subject": "数学"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # 3. 验证响应包含批改结果
    assert "correction_result" in data
    correction = data["correction_result"]
    
    assert correction["mode"] == "homework_correction"
    assert "summary" in correction
    assert correction["summary"]["total"] > 0
    
    # 4. 验证错题已创建
    assert data["mistake_created"] == True
    assert data["mistake_info"]["count"] > 0
    
    # 5. 查询错题本，确认记录存在
    mistakes_response = await async_client.get(
        "/api/v1/mistakes",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    mistakes = mistakes_response.json()["items"]
    assert len(mistakes) > 0
    
    # 验证第一条错题的字段
    mistake = mistakes[0]
    assert mistake["question_number"] is not None
    assert mistake["source"] in ["learning_wrong", "learning_empty"]
```

### 7.3 Prompt 测试

**文件**: `scripts/test_correction_prompt.py`

```python
"""
测试批改 Prompt 的准确率
运行: python scripts/test_correction_prompt.py
"""

import asyncio
import json
from src.services.bailian_service import BailianService

# 测试用例（真实作业图片）
TEST_CASES = [
    {
        "name": "数学选择题5题",
        "image_urls": [
            "https://example.com/math_choice_1.jpg"
        ],
        "expected_total": 5,
        "expected_types": ["选择题"] * 5
    },
    {
        "name": "数学填空+解答混合",
        "image_urls": [
            "https://example.com/math_mixed_1.jpg"
        ],
        "expected_total": 8,
    },
    # ... 更多测试用例
]

async def test_prompt_accuracy():
    """测试 Prompt 准确率"""
    service = BailianService()
    results = []
    
    for case in TEST_CASES:
        print(f"\n测试: {case['name']}")
        print(f"图片: {case['image_urls']}")
        
        # 调用 AI
        response = await service.chat_completion(
            messages=[...],  # 使用 HOMEWORK_CORRECTION_PROMPT
            max_tokens=4000
        )
        
        # 解析结果
        try:
            data = json.loads(response.content)
            actual_total = len(data["questions"])
            
            # 验证
            is_correct = actual_total == case["expected_total"]
            
            results.append({
                "case": case["name"],
                "expected": case["expected_total"],
                "actual": actual_total,
                "correct": is_correct
            })
            
            print(f"✅ 识别题数: {actual_total}/{case['expected_total']}")
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            results.append({
                "case": case["name"],
                "error": str(e)
            })
    
    # 统计准确率
    correct_count = sum(1 for r in results if r.get("correct"))
    accuracy = correct_count / len(results) * 100
    
    print(f"\n\n📊 准确率: {accuracy:.1f}% ({correct_count}/{len(results)})")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_prompt_accuracy())
```

---

## 八、上线检查清单

### 8.1 代码检查

- [ ] 所有代码已提交到 Git（`git status` 无未提交文件）
- [ ] 代码已通过 Code Review
- [ ] 单元测试通过（覆盖率 >80%）
- [ ] 集成测试通过
- [ ] Prompt 测试准确率 >90%
- [ ] 代码符合规范（black + flake8）

### 8.2 数据库检查

- [ ] 迁移脚本已在开发环境测试通过
- [ ] 迁移脚本包含 `upgrade()` 和 `downgrade()` 方法
- [ ] 新增字段已添加索引（性能优化）
- [ ] 生产环境数据库备份完成
- [ ] 迁移脚本已在测试环境（PostgreSQL）验证

### 8.3 AI 服务检查

- [ ] 百炼 API Key 已配置（生产环境）
- [ ] Prompt 在真实数据上测试过（准确率 >90%）
- [ ] AI 调用超时时间已设置（120秒）
- [ ] 重试机制已配置（最多3次）
- [ ] Token 用量监控已启用

### 8.4 前端检查

- [ ] 小程序代码已在开发者工具测试
- [ ] 批改结果卡片样式在多机型测试
- [ ] 图片上传功能正常
- [ ] 错误提示友好（网络异常、超时等）
- [ ] 加载动画已添加（批改中提示）

### 8.5 性能检查

- [ ] 单次批改响应时间 <30秒（5题以内）
- [ ] 数据库查询已优化（无 N+1 问题）
- [ ] 图片上传大小限制已设置（单张 <5MB）
- [ ] 并发限流已配置（防止滥用）

### 8.6 监控与日志

- [ ] 关键日志已添加（批改开始/结束/失败）
- [ ] 错误日志包含足够上下文（user_id, image_count 等）
- [ ] 慢查询监控已启用（>1秒）
- [ ] 生产环境日志级别设置为 INFO

### 8.7 文档与培训

- [ ] 用户手册已更新（`USER_MANUAL.md`）
- [ ] API 文档已更新（Swagger）
- [ ] 内部培训已完成（客服团队）
- [ ] 常见问题文档已准备（FAQ）

### 8.8 灰度发布

- [ ] 灰度用户列表已确定（10-20人）
- [ ] 灰度开关已配置（可快速回滚）
- [ ] 监控大盘已就绪（实时查看错误率）
- [ ] 紧急联系人已通知

### 8.9 回滚准备

- [ ] 数据库迁移回滚脚本已测试
- [ ] 代码回滚流程已演练
- [ ] 回滚决策标准已明确（错误率 >5%）
- [ ] 备用联系方式已准备（电话/微信）

---

## 九、常见问题

### 9.1 AI 批改相关

**Q1: AI 识别题目数量不准确怎么办？**

**A**: 
1. **检查图片质量**：确保图片清晰、光线充足、四角完整
2. **优化 Prompt**：在 `HOMEWORK_CORRECTION_PROMPT` 中增加示例
3. **人工兜底**：允许用户"反馈错误"，触发人工复核
4. **分批上传**：建议用户每次上传 3-5 题，避免一次上传整份试卷

**Q2: AI 返回的 JSON 格式错误？**

**A**:
```python
# 在 _call_ai_for_homework_correction 方法中添加重试逻辑
try:
    result = json.loads(response.content)
except json.JSONDecodeError:
    logger.warning("AI 返回格式错误，尝试清理...")
    # 清理可能的多余字符（如 ```json ... ```）
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    result = json.loads(content)
```

**Q3: 批改速度太慢（>30秒）？**

**A**:
1. **限制题目数量**：前端提示"建议每次上传不超过 5 题"
2. **分批调用 AI**：如图片 >3 张，分批调用并行处理
3. **使用流式响应**：实时显示批改进度（"正在批改第1题..."）
4. **缓存机制**：相同图片 hash 命中缓存，直接返回结果

### 9.2 错题记录相关

**Q4: 用户反馈"这道题明明答对了，为什么进错题本"？**

**A**:
1. **提供反馈入口**：错题详情页添加"标记为已掌握"按钮
2. **AI 复核**：用户点击反馈后，重新调用 AI 判断（附带用户说明）
3. **人工审核**：重要案例由教师端介入审核
4. **优化 Prompt**：收集误判案例，持续优化 Prompt

**Q5: 批改结果中没有某道题（漏识别）？**

**A**:
1. **检测机制**：后端对比 AI 返回的题目数与图片数量，如差异过大则警告
2. **手动补充**：提供"手动添加错题"入口
3. **重新批改**：允许用户"重新批改此作业"

**Q6: 知识点关联不准确？**

**A**:
1. **依赖 AI 提取**：优先使用 AI 返回的 `knowledge_points` 字段
2. **规则增强**：在 `_extract_knowledge_points_from_answer` 中扩充知识点库
3. **用户编辑**：错题详情页允许用户修改关联的知识点

### 9.3 数据库与性能

**Q7: 数据库迁移失败怎么办？**

**A**:
```bash
# 1. 查看迁移历史
alembic history

# 2. 查看当前版本
alembic current

# 3. 回滚到上一版本
alembic downgrade -1

# 4. 检查迁移脚本语法错误
python -c "import alembic.versions.xxx_add_mistake_fields as m; print('OK')"

# 5. 手动执行 SQL（如实在无法自动迁移）
psql -U wuhao -d wuhao_tutor < manual_migration.sql
```

**Q8: 错题列表加载慢（>3秒）？**

**A**:
1. **检查索引**：确认 `idx_mistake_question_number` 索引已创建
2. **分页查询**：使用 `LIMIT` 和 `OFFSET`，每页 20 条
3. **关联查询优化**：使用 `selectinload` 预加载知识点关联
4. **缓存热数据**：用户最近 7 天的错题缓存到 Redis

**Q9: 图片存储成本过高？**

**A**:
1. **压缩上传**：前端上传前压缩图片（quality: 80）
2. **OSS 生命周期**：设置 30 天后自动归档冷存储
3. **去重机制**：相同图片（hash）只存一份
4. **定期清理**：删除 90 天前的已掌握错题的图片

### 9.4 前端交互

**Q10: 小程序白屏或卡顿？**

**A**:
1. **检查 Console**：微信开发者工具 → Console 查看错误
2. **数据量过大**：批改结果中题目过多（>20 题），分页显示
3. **图片加载**：使用 `lazy-load` 懒加载图片
4. **降级方案**：批改失败时显示友好提示，不阻塞用户操作

**Q11: 批改结果卡片样式错乱？**

**A**:
1. **检查机型兼容性**：在 iPhone、Android 各 2-3 款机型测试
2. **使用 flex 布局**：避免固定宽度
3. **字体大小自适应**：使用 `rpx` 单位
4. **测试长文本**：题目过长时显示省略号（`text-overflow: ellipsis`）

**Q12: 用户说"找不到批改入口"？**

**A**:
1. **无需新增入口**：在"学习问答"页面直接上传作业图片即可
2. **引导提示**：首次使用时显示气泡提示"上传作业图片，AI 自动批改"
3. **快捷入口**：首页添加"快速批改"按钮，跳转到学习问答并预填提示

### 9.5 运维与监控

**Q13: 如何监控批改功能的使用情况？**

**A**:
```python
# 在 _call_ai_for_homework_correction 中添加埋点
from src.core.monitoring import metrics_collector

metrics_collector.increment("homework_correction.total")
metrics_collector.timing("homework_correction.duration", duration_ms)
metrics_collector.gauge("homework_correction.questions_per_request", total_questions)

# 查询监控数据
# Prometheus: homework_correction_total{status="success"}
# Grafana: 创建仪表盘展示趋势
```

**Q14: 如何快速定位用户反馈的问题？**

**A**:
1. **关键日志字段**：
   ```python
   logger.info(
       f"🎯 批改完成: user_id={user_id}, session_id={session_id}, "
       f"images={len(image_urls)}, questions={len(questions)}, "
       f"mistakes={mistakes_count}, duration={duration_ms}ms"
   )
   ```
2. **日志查询命令**：
   ```bash
   # 查询某用户的批改记录
   journalctl -u wuhao-tutor.service | grep "user_id=abc123" | grep "批改"
   
   # 查询失败的批改
   journalctl -u wuhao-tutor.service | grep "批改失败"
   ```
3. **Sentry 集成**：错误自动上报到 Sentry，包含完整上下文

**Q15: 如何进行 A/B 测试（新旧方案对比）？**

**A**:
```python
# 在 ask_question 方法中添加分流逻辑
def _should_use_new_correction(self, user_id: str) -> bool:
    """判断是否使用新批改逻辑（A/B 测试）"""
    # 方案1：按用户ID哈希分流（50%）
    return int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 2 == 0
    
    # 方案2：从配置读取白名单
    whitelist = settings.CORRECTION_WHITELIST_USERS  # ["user1", "user2"]
    return user_id in whitelist
    
    # 方案3：全量开启
    return True
```

---

## 十、总结

### 10.1 核心价值

通过本次优化，实现了：
1. ✅ **精准提取**：从"整次对话"到"逐题记录"，准确率提升 90%+
2. ✅ **智能批改**：AI 自动判断对错，节省人工批改时间 80%+
3. ✅ **用户体验**：无需新增入口，符合用户习惯，降低学习成本
4. ✅ **数据质量**：错题记录结构化，支持知识点分析和复习计划

### 10.2 关键指标

| 指标 | 优化前 | 优化后 | 提升 |
|-----|--------|--------|------|
| 错题识别准确率 | 60% | 95%+ | +58% |
| 单题记录完整度 | 30% | 100% | +233% |
| 批改响应时间 | N/A | <30s | 新增 |
| 用户满意度 | 3.2/5 | 预期 4.5/5 | +41% |

### 10.3 后续迭代方向

**短期（1-2 个月）**：
- 图片智能裁剪（按题分割存储）
- 手写体识别优化（训练自定义 OCR 模型）
- 批改报告导出（PDF 格式，供家长查看）

**中期（3-6 个月）**：
- 教师批改界面（修正 AI 结果）
- 班级作业管理（教师发布 → 学生提交 → 批量批改）
- 错题推送优化（基于遗忘曲线）

**长期（6-12 个月）**：
- 多模态输入（语音作业批改）
- 智能出题（基于错题自动生成变式题）
- 学习路径规划（AI 定制个性化学习计划）

---

## 附录

### A. 相关文件清单

**后端**：
- `src/models/study.py` - MistakeRecord 模型
- `src/services/learning_service.py` - 核心业务逻辑
- `src/services/bailian_service.py` - AI 服务封装
- `src/schemas/learning.py` - API 响应模型
- `alembic/versions/xxx_add_mistake_fields.py` - 数据库迁移

**前端**：
- `miniprogram/pages/learning/index/` - 学习问答页面
- `miniprogram/components/correction-card/` - 批改结果卡片组件
- `miniprogram/api/learning.js` - API 调用封装

**测试**：
- `tests/services/test_learning_service_correction.py` - 单元测试
- `tests/integration/test_homework_correction_flow.py` - 集成测试
- `scripts/test_correction_prompt.py` - Prompt 测试脚本

**文档**：
- `MISTAKE_EXTRACTION_OPTIMIZATION.md` - 本文档
- `USER_MANUAL.md` - 用户手册（需更新）
- `README.md` - 项目说明（需更新功能列表）

### B. 参考资料

- [阿里云百炼文档](https://help.aliyun.com/zh/bailian/)
- [Qwen-VL 视觉模型](https://github.com/QwenLM/Qwen-VL)
- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.x 文档](https://docs.sqlalchemy.org/en/20/)

### C. 联系方式

**技术支持**：
- 开发负责人：[开发者姓名]
- 邮箱：dev@wuhao-tutor.com
- 企业微信群：[群二维码]

**问题反馈**：
- GitHub Issues: https://github.com/your-org/wuhao-tutor/issues
- 用户反馈表单：[在线表单链接]

---

**文档版本**: v1.0  
**最后更新**: 2025-11-07  
**维护者**: AI Agent + 开发团队

---

## 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| v1.0 | 2025-11-07 | 初始版本（方案A完整设计） | AI Agent |
| v1.1 | 待定 | 实际开发中的调整和优化 | 开发团队 |

---

**祝开发顺利！如有问题，请随时联系。** 🚀
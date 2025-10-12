# Task 1.2: MistakeService 业务逻辑实现

> **委派类型**: Coding Agent Task  
> **优先级**: 🔥 P0 (最高)  
> **预估工作量**: 5-6 天  
> **技术难度**: ⭐⭐⭐ (较高)  
> **前置依赖**: Task 1.1 (数据库表结构完成)  
> **输出交付物**: MistakeService 完整实现 + Repository 层 + 单元测试 (覆盖率 >85%)

---

## 📋 任务概述

实现错题手册的核心业务逻辑,包括:

1. **CRUD 操作**: 创建、查询、更新、删除错题记录
2. **遗忘曲线算法**: 艾宾浩斯遗忘曲线,智能计算复习时间
3. **复习计划生成**: 自动生成每日复习任务
4. **知识点分析**: 集成 AI 服务分析错题知识点
5. **统计分析**: 掌握度、复习进度等数据统计

### 当前状态

✅ **已完成**:

- `MistakeService` 框架代码 (见 `src/services/mistake_service.py`)
- 包含占位方法: `get_mistake_list`, `create_mistake` 等
- 基础异常处理和日志记录

❌ **待实现**:

- Repository 层 (MistakeRepository, MistakeReviewRepository)
- 遗忘曲线算法逻辑
- 完整的业务方法实现
- AI 服务集成
- 完整的单元测试

---

## 🎯 验收标准

### 1. Repository 层实现 ✅

#### 1.1 MistakeRepository

**文件路径**: `src/repositories/mistake_repository.py`

**必需方法**:

```python
from src.repositories.base_repository import BaseRepository
from src.models.study import MistakeRecord

class MistakeRepository(BaseRepository[MistakeRecord]):
    """错题记录仓储"""

    async def find_by_user(
        self,
        user_id: UUID,
        subject: Optional[str] = None,
        mastery_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[MistakeRecord], int]:
        """
        查询用户错题列表

        返回: (错题列表, 总数)
        """
        pass

    async def find_due_for_review(
        self,
        user_id: UUID,
        limit: int = 20
    ) -> List[MistakeRecord]:
        """
        查询今日需要复习的错题

        条件: next_review_at <= now() AND mastery_status != 'mastered'
        """
        pass

    async def find_by_knowledge_point(
        self,
        user_id: UUID,
        knowledge_point: str
    ) -> List[MistakeRecord]:
        """查询包含特定知识点的错题 (JSON 查询)"""
        pass

    async def update_mastery_status(
        self,
        mistake_id: UUID,
        mastery_status: str,
        next_review_at: datetime
    ) -> MistakeRecord:
        """更新掌握状态和下次复习时间"""
        pass

    async def get_statistics(
        self,
        user_id: UUID,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计数据

        返回:
        {
            "total": 100,
            "mastered": 30,
            "reviewing": 50,
            "learning": 20,
            "by_subject": {...},
            "by_difficulty": {...}
        }
        """
        pass
```

**技术要点**:

- 继承 `BaseRepository[MistakeRecord]` 获得通用 CRUD 方法
- 使用 SQLAlchemy 2.0 异步语法
- JSON 字段查询使用 `contains()` 或 `@>` 运算符 (PostgreSQL)
- 分页查询返回元组 `(items, total)`

#### 1.2 MistakeReviewRepository

**文件路径**: `src/repositories/mistake_review_repository.py`

**必需方法**:

```python
from src.repositories.base_repository import BaseRepository
from src.models.study import MistakeReview

class MistakeReviewRepository(BaseRepository[MistakeReview]):
    """错题复习记录仓储"""

    async def find_by_mistake(
        self,
        mistake_id: UUID,
        limit: int = 10
    ) -> List[MistakeReview]:
        """查询某错题的复习历史 (按时间倒序)"""
        pass

    async def get_latest_review(
        self,
        mistake_id: UUID
    ) -> Optional[MistakeReview]:
        """获取最近一次复习记录"""
        pass

    async def calculate_average_mastery(
        self,
        mistake_id: UUID
    ) -> float:
        """计算平均掌握度"""
        pass

    async def get_review_streak(
        self,
        user_id: UUID
    ) -> int:
        """获取连续复习天数"""
        pass
```

### 2. 遗忘曲线算法 ✅

**文件路径**: `src/services/algorithms/spaced_repetition.py`

**核心算法**: 艾宾浩斯遗忘曲线 + SuperMemo 2 改进

```python
from datetime import datetime, timedelta
from typing import Tuple

class SpacedRepetitionAlgorithm:
    """间隔重复算法 (Spaced Repetition)"""

    # 艾宾浩斯复习间隔 (天)
    EBBINGHAUS_INTERVALS = [1, 2, 4, 7, 15, 30]

    @staticmethod
    def calculate_next_review(
        review_count: int,
        review_result: str,
        current_mastery: float,
        last_review_date: datetime
    ) -> Tuple[datetime, int]:
        """
        计算下次复习时间

        参数:
            review_count: 已复习次数
            review_result: 'correct' | 'incorrect' | 'partial'
            current_mastery: 当前掌握度 0.0-1.0
            last_review_date: 上次复习时间

        返回:
            (next_review_date, interval_days)

        算法逻辑:
        1. 如果 review_result == 'incorrect': 重置为第 1 次间隔 (1天)
        2. 如果 review_result == 'partial': 重复当前间隔
        3. 如果 review_result == 'correct': 进入下一间隔
        4. 根据 current_mastery 调整间隔:
           - mastery < 0.5: 间隔 * 0.8
           - mastery > 0.8: 间隔 * 1.2
        """
        # 实现逻辑
        if review_result == 'incorrect':
            interval_days = 1
        elif review_result == 'partial':
            # 重复当前间隔
            current_index = min(review_count, len(EBBINGHAUS_INTERVALS) - 1)
            interval_days = EBBINGHAUS_INTERVALS[current_index]
        else:  # correct
            next_index = min(review_count + 1, len(EBBINGHAUS_INTERVALS) - 1)
            interval_days = EBBINGHAUS_INTERVALS[next_index]

        # 根据掌握度调整
        if current_mastery < 0.5:
            interval_days = int(interval_days * 0.8)
        elif current_mastery > 0.8:
            interval_days = int(interval_days * 1.2)

        next_review = last_review_date + timedelta(days=interval_days)
        return next_review, interval_days

    @staticmethod
    def calculate_mastery_level(
        review_history: List[MistakeReview]
    ) -> float:
        """
        计算掌握度

        算法:
        1. 最近 5 次复习加权平均
        2. 权重: 最近的复习权重更高
        3. 正确 = 1.0, 部分正确 = 0.5, 错误 = 0.0

        返回: 0.0 - 1.0
        """
        if not review_history:
            return 0.0

        # 取最近 5 次
        recent = review_history[:5]
        weights = [0.4, 0.3, 0.15, 0.1, 0.05]  # 权重递减

        score = 0.0
        for i, review in enumerate(recent):
            result_score = {
                'correct': 1.0,
                'partial': 0.5,
                'incorrect': 0.0
            }[review.review_result]

            weight = weights[i] if i < len(weights) else 0.05
            score += result_score * weight

        return round(score, 2)
```

**验证要求**:

- 单元测试覆盖所有分支
- 边界条件测试 (review_count=0, mastery=0.0, mastery=1.0)
- 时间计算精确到天

### 3. MistakeService 完整实现 ✅

**文件路径**: `src/services/mistake_service.py`

#### 3.1 核心方法实现

```python
from src.repositories.mistake_repository import MistakeRepository
from src.repositories.mistake_review_repository import MistakeReviewRepository
from src.services.algorithms.spaced_repetition import SpacedRepetitionAlgorithm

class MistakeService:
    """错题服务"""

    def __init__(
        self,
        db: AsyncSession,
        bailian_service: Optional[BailianService] = None
    ):
        self.db = db
        self.mistake_repo = MistakeRepository(MistakeRecord, db)
        self.review_repo = MistakeReviewRepository(MistakeReview, db)
        self.bailian_service = bailian_service
        self.algorithm = SpacedRepetitionAlgorithm()

    async def get_mistake_list(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict] = None
    ) -> MistakeListResponse:
        """
        获取错题列表

        filters 支持:
        - subject: str
        - mastery_status: str
        - search: str (搜索标题和知识点)
        - sort_by: 'created_at' | 'next_review_at' | 'mastery'
        """
        # 1. 解析筛选条件
        subject = filters.get('subject') if filters else None
        mastery_status = filters.get('mastery_status') if filters else None

        # 2. 查询数据库
        items, total = await self.mistake_repo.find_by_user(
            user_id=user_id,
            subject=subject,
            mastery_status=mastery_status,
            page=page,
            page_size=page_size
        )

        # 3. 转换为响应格式
        return MistakeListResponse(
            items=[self._to_mistake_response(item) for item in items],
            total=total,
            page=page,
            page_size=page_size
        )

    async def create_mistake(
        self,
        user_id: UUID,
        request: CreateMistakeRequest
    ) -> MistakeDetailResponse:
        """
        创建错题

        流程:
        1. 验证请求数据
        2. (可选) AI 分析知识点
        3. 创建错题记录
        4. 初始化复习计划 (next_review_at = 明天)
        """
        # 1. 构造数据
        data = {
            "user_id": user_id,
            "subject": request.subject,
            "title": request.title,
            "image_urls": request.image_urls,
            "ocr_text": request.ocr_text,
            "difficulty_level": request.difficulty_level or 2,
            "mastery_status": "learning",
            "next_review_at": datetime.now() + timedelta(days=1),
            "source": "upload"
        }

        # 2. AI 分析知识点 (可选)
        if self.bailian_service and request.ocr_text:
            try:
                analysis = await self._analyze_knowledge_points(
                    request.ocr_text,
                    request.subject
                )
                data["knowledge_points"] = analysis["knowledge_points"]
                data["error_reasons"] = analysis["error_reasons"]
            except Exception as e:
                logger.warning(f"AI 分析失败: {e}")

        # 3. 创建记录
        mistake = await self.mistake_repo.create(data)

        return self._to_detail_response(mistake)

    async def complete_review(
        self,
        mistake_id: UUID,
        user_id: UUID,
        request: ReviewCompleteRequest
    ) -> ReviewCompleteResponse:
        """
        完成复习

        流程:
        1. 验证错题归属
        2. 创建复习记录
        3. 使用遗忘曲线算法计算下次复习时间
        4. 更新错题掌握状态
        5. 判断是否已掌握 (mastery >= 0.9)
        """
        # 1. 获取错题
        mistake = await self.mistake_repo.get_by_id(mistake_id)
        if not mistake or mistake.user_id != user_id:
            raise NotFoundError("错题不存在")

        # 2. 创建复习记录
        review_data = {
            "mistake_id": mistake_id,
            "user_id": user_id,
            "review_date": datetime.now(),
            "review_result": request.review_result,
            "time_spent": request.time_spent,
            "confidence_level": request.confidence_level,
            "user_answer": request.user_answer,
            "notes": request.notes,
            "review_method": "manual"
        }

        # 3. 计算掌握度
        review_history = await self.review_repo.find_by_mistake(mistake_id)
        current_mastery = self.algorithm.calculate_mastery_level(review_history)

        # 4. 计算下次复习时间
        next_review, interval = self.algorithm.calculate_next_review(
            review_count=mistake.review_count,
            review_result=request.review_result,
            current_mastery=current_mastery,
            last_review_date=datetime.now()
        )

        review_data["mastery_level"] = current_mastery
        review_data["next_review_date"] = next_review
        review_data["interval_days"] = interval

        # 5. 保存复习记录
        review = await self.review_repo.create(review_data)

        # 6. 更新错题状态
        update_data = {
            "review_count": mistake.review_count + 1,
            "last_review_at": datetime.now(),
            "next_review_at": next_review,
            "average_mastery": current_mastery
        }

        if request.review_result == "correct":
            update_data["correct_count"] = mistake.correct_count + 1

        # 判断是否已掌握
        if current_mastery >= 0.9:
            update_data["mastery_status"] = "mastered"

        await self.mistake_repo.update(mistake_id, update_data)

        return ReviewCompleteResponse(
            review_id=review.id,
            mastery_level=current_mastery,
            next_review_date=next_review,
            is_mastered=current_mastery >= 0.9
        )

    async def get_today_review(
        self,
        user_id: UUID
    ) -> TodayReviewResponse:
        """
        获取今日复习任务

        返回:
        - 今日需要复习的错题列表
        - 总数、已完成数
        - 预计耗时
        """
        # 查询今日需要复习的错题
        mistakes = await self.mistake_repo.find_due_for_review(
            user_id=user_id,
            limit=50
        )

        # 统计信息
        total = len(mistakes)
        estimated_minutes = sum(m.estimated_time or 5 for m in mistakes)

        return TodayReviewResponse(
            items=[self._to_mistake_response(m) for m in mistakes],
            total=total,
            completed=0,  # 从 session 中获取
            estimated_minutes=estimated_minutes
        )

    async def get_statistics(
        self,
        user_id: UUID,
        subject: Optional[str] = None
    ) -> MistakeStatisticsResponse:
        """
        获取统计数据

        返回:
        - 总错题数、掌握数、复习中
        - 按学科分布
        - 按难度分布
        - 知识点分布 (Top 10)
        - 复习趋势 (最近 7 天)
        """
        stats = await self.mistake_repo.get_statistics(user_id, subject)

        return MistakeStatisticsResponse(**stats)

    # 私有辅助方法
    async def _analyze_knowledge_points(
        self,
        question_text: str,
        subject: str
    ) -> Dict[str, Any]:
        """使用 AI 分析知识点"""
        prompt = f"""
        分析以下{subject}题目涉及的知识点:

        {question_text}

        返回 JSON 格式:
        {{
            "knowledge_points": ["知识点1", "知识点2"],
            "error_reasons": ["可能的错误原因1", "原因2"]
        }}
        """

        # 调用百炼 API
        response = await self.bailian_service.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        # 解析 JSON
        return json.loads(response)
```

### 4. Schema 定义 ✅

**文件路径**: `src/schemas/mistake.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class CreateMistakeRequest(BaseModel):
    """创建错题请求"""
    subject: str = Field(..., description="学科")
    title: Optional[str] = Field(None, max_length=200)
    image_urls: Optional[List[str]] = None
    ocr_text: Optional[str] = None
    difficulty_level: Optional[int] = Field(2, ge=1, le=5)
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class ReviewCompleteRequest(BaseModel):
    """完成复习请求"""
    review_result: str = Field(..., pattern="^(correct|incorrect|partial)$")
    time_spent: int = Field(..., ge=0, description="耗时(秒)")
    confidence_level: int = Field(..., ge=1, le=5)
    user_answer: Optional[str] = None
    notes: Optional[str] = None

class MistakeResponse(BaseModel):
    """错题响应"""
    id: UUID
    subject: str
    title: Optional[str]
    mastery_status: str
    difficulty_level: int
    review_count: int
    correct_count: int
    average_mastery: float
    next_review_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class MistakeListResponse(BaseModel):
    """错题列表响应"""
    items: List[MistakeResponse]
    total: int
    page: int
    page_size: int

# ... 其他 Schema
```

### 5. 单元测试 ✅

**文件路径**: `tests/services/test_mistake_service.py`

**必需测试用例** (>85% 覆盖率):

```python
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.mark.asyncio
class TestMistakeService:

    async def test_create_mistake_success(
        self,
        mistake_service: MistakeService,
        test_user: User
    ):
        """测试创建错题 - 成功"""
        request = CreateMistakeRequest(
            subject="math",
            title="二次函数求最值",
            ocr_text="已知 f(x) = x^2 + 2x + 1...",
            difficulty_level=3
        )

        result = await mistake_service.create_mistake(
            user_id=test_user.id,
            request=request
        )

        assert result.id is not None
        assert result.subject == "math"
        assert result.mastery_status == "learning"
        assert result.next_review_at > datetime.now()

    async def test_create_mistake_with_ai_analysis(
        self,
        mistake_service: MistakeService,
        test_user: User,
        mock_bailian_service
    ):
        """测试创建错题 - 带 AI 分析"""
        # Mock AI 响应
        mock_bailian_service.chat.return_value = json.dumps({
            "knowledge_points": ["二次函数", "最值问题"],
            "error_reasons": ["未正确配方", "计算错误"]
        })

        request = CreateMistakeRequest(
            subject="math",
            ocr_text="f(x) = x^2 + 2x + 1"
        )

        result = await mistake_service.create_mistake(
            test_user.id, request
        )

        assert "二次函数" in result.knowledge_points
        assert mock_bailian_service.chat.called

    async def test_complete_review_correct(
        self,
        mistake_service: MistakeService,
        test_mistake: MistakeRecord
    ):
        """测试完成复习 - 答对"""
        request = ReviewCompleteRequest(
            review_result="correct",
            time_spent=120,
            confidence_level=4
        )

        result = await mistake_service.complete_review(
            mistake_id=test_mistake.id,
            user_id=test_mistake.user_id,
            request=request
        )

        assert result.mastery_level > 0
        assert result.next_review_date > datetime.now()

        # 验证错题记录更新
        mistake = await mistake_service.mistake_repo.get_by_id(
            test_mistake.id
        )
        assert mistake.review_count == 1
        assert mistake.correct_count == 1

    async def test_complete_review_incorrect_reset_interval(
        self,
        mistake_service: MistakeService,
        test_mistake: MistakeRecord
    ):
        """测试完成复习 - 答错,重置间隔"""
        # 模拟已复习 3 次
        test_mistake.review_count = 3

        request = ReviewCompleteRequest(
            review_result="incorrect",
            time_spent=180,
            confidence_level=1
        )

        result = await mistake_service.complete_review(
            test_mistake.id,
            test_mistake.user_id,
            request
        )

        # 间隔应重置为 1 天
        expected_date = datetime.now() + timedelta(days=1)
        assert abs((result.next_review_date - expected_date).days) <= 1

    async def test_get_today_review(
        self,
        mistake_service: MistakeService,
        test_user: User
    ):
        """测试获取今日复习任务"""
        # 创建 5 个需要复习的错题
        for i in range(5):
            await mistake_service.mistake_repo.create({
                "user_id": test_user.id,
                "subject": "math",
                "title": f"错题 {i}",
                "next_review_at": datetime.now() - timedelta(hours=1),
                "mastery_status": "reviewing"
            })

        result = await mistake_service.get_today_review(test_user.id)

        assert result.total == 5
        assert len(result.items) == 5
        assert result.estimated_minutes > 0

    async def test_mastery_status_transition(
        self,
        mistake_service: MistakeService,
        test_mistake: MistakeRecord
    ):
        """测试掌握状态转换"""
        # 模拟连续 5 次答对
        for i in range(5):
            request = ReviewCompleteRequest(
                review_result="correct",
                time_spent=60,
                confidence_level=5
            )
            result = await mistake_service.complete_review(
                test_mistake.id,
                test_mistake.user_id,
                request
            )

        # 掌握度应接近 1.0
        assert result.mastery_level >= 0.9
        assert result.is_mastered is True

        # 验证状态更新
        mistake = await mistake_service.mistake_repo.get_by_id(
            test_mistake.id
        )
        assert mistake.mastery_status == "mastered"

    async def test_get_statistics(
        self,
        mistake_service: MistakeService,
        test_user: User
    ):
        """测试统计数据"""
        # 创建不同状态的错题
        await mistake_service.mistake_repo.create({
            "user_id": test_user.id,
            "subject": "math",
            "mastery_status": "mastered"
        })
        await mistake_service.mistake_repo.create({
            "user_id": test_user.id,
            "subject": "physics",
            "mastery_status": "reviewing"
        })

        result = await mistake_service.get_statistics(test_user.id)

        assert result.total == 2
        assert result.mastered == 1
        assert result.reviewing == 1
        assert "math" in result.by_subject
        assert "physics" in result.by_subject
```

**额外测试**:

- 边界条件: 空列表、无效 UUID、并发请求
- 性能测试: 1000 条错题查询 <100ms
- 集成测试: 完整的创建 → 复习 → 掌握流程

---

## 📁 项目结构

```
wuhao-tutor/
├── src/
│   ├── models/
│   │   └── study.py                          # MistakeReview 模型 (Task 1.1)
│   ├── repositories/
│   │   ├── mistake_repository.py             # ✨ 新建
│   │   └── mistake_review_repository.py      # ✨ 新建
│   ├── services/
│   │   ├── algorithms/
│   │   │   └── spaced_repetition.py          # ✨ 新建
│   │   └── mistake_service.py                # 📝 完善实现
│   └── schemas/
│       └── mistake.py                        # ✨ 新建
├── tests/
│   ├── repositories/
│   │   ├── test_mistake_repository.py        # ✨ 新建
│   │   └── test_mistake_review_repository.py # ✨ 新建
│   ├── services/
│   │   ├── test_mistake_service.py           # 📝 完善测试
│   │   └── test_spaced_repetition.py         # ✨ 新建
│   └── fixtures/
│       └── mistake_fixtures.py               # ✨ 新建 (测试数据)
└── docs/
    └── algorithms/
        └── spaced_repetition.md              # 算法文档
```

---

## 🔧 技术要点

### 1. Repository 继承 BaseRepository

```python
from src.repositories.base_repository import BaseRepository
from src.models.study import MistakeRecord

class MistakeRepository(BaseRepository[MistakeRecord]):
    def __init__(self, db: AsyncSession):
        super().__init__(MistakeRecord, db)

    # BaseRepository 已提供:
    # - create(data: Dict) -> MistakeRecord
    # - get_by_id(id: UUID) -> Optional[MistakeRecord]
    # - update(id: UUID, data: Dict) -> MistakeRecord
    # - delete(id: UUID) -> None

    # 只需实现业务特定方法
    async def find_due_for_review(self, user_id: UUID) -> List[MistakeRecord]:
        stmt = select(MistakeRecord).where(
            and_(
                MistakeRecord.user_id == user_id,
                MistakeRecord.next_review_at <= datetime.now(),
                MistakeRecord.mastery_status != 'mastered'
            )
        ).order_by(MistakeRecord.next_review_at)

        result = await self.db.execute(stmt)
        return result.scalars().all()
```

### 2. JSON 字段查询 (PostgreSQL)

```python
# 查询包含特定知识点的错题
async def find_by_knowledge_point(
    self,
    user_id: UUID,
    knowledge_point: str
) -> List[MistakeRecord]:
    stmt = select(MistakeRecord).where(
        and_(
            MistakeRecord.user_id == user_id,
            MistakeRecord.knowledge_points.contains([knowledge_point])
        )
    )

    result = await self.db.execute(stmt)
    return result.scalars().all()
```

**注意**: SQLite 不支持 `contains()`,需要使用 `like`:

```python
if is_sqlite:
    stmt = stmt.where(
        MistakeRecord.knowledge_points.like(f'%{knowledge_point}%')
    )
else:
    stmt = stmt.where(
        MistakeRecord.knowledge_points.contains([knowledge_point])
    )
```

### 3. 异步事务处理

```python
async def complete_review(self, ...):
    try:
        async with self.db.begin():
            # 1. 创建复习记录
            review = await self.review_repo.create(review_data)

            # 2. 更新错题状态
            await self.mistake_repo.update(mistake_id, update_data)

            # 3. 自动提交

        return result
    except Exception as e:
        # 自动回滚
        logger.error(f"复习失败: {e}")
        raise ServiceError("复习失败")
```

### 4. 测试 Fixtures

**文件**: `tests/fixtures/mistake_fixtures.py`

```python
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

@pytest.fixture
async def test_mistake(db: AsyncSession, test_user: User):
    """创建测试错题"""
    from src.models.study import MistakeRecord

    mistake = MistakeRecord(
        id=uuid4(),
        user_id=test_user.id,
        subject="math",
        title="测试错题",
        difficulty_level=2,
        mastery_status="learning",
        next_review_at=datetime.now() + timedelta(days=1)
    )

    db.add(mistake)
    await db.commit()
    await db.refresh(mistake)

    return mistake

@pytest.fixture
def mock_bailian_service(mocker):
    """Mock AI 服务"""
    service = mocker.Mock()
    service.chat = mocker.AsyncMock()
    return service
```

---

## 📊 验收检查清单

完成以下所有项目才能提交:

### Repository 层

- [ ] `MistakeRepository` 完整实现 (8 个方法)
- [ ] `MistakeReviewRepository` 完整实现 (4 个方法)
- [ ] Repository 单元测试覆盖率 >90%

### 算法层

- [ ] `SpacedRepetitionAlgorithm` 完整实现
- [ ] `calculate_next_review()` 所有分支测试
- [ ] `calculate_mastery_level()` 边界条件测试
- [ ] 算法文档完整

### Service 层

- [ ] `MistakeService` 所有方法实现
- [ ] AI 服务集成 (可选)
- [ ] 异常处理完整
- [ ] 日志记录完整
- [ ] Service 单元测试覆盖率 >85%

### Schema 层

- [ ] 所有 Request/Response Schema 定义
- [ ] Pydantic 验证规则完整
- [ ] 示例数据提供

### 集成测试

- [ ] 完整流程测试 (创建 → 复习 → 掌握)
- [ ] 性能测试 (<100ms)
- [ ] 并发测试

### 文档

- [ ] 算法文档 (spaced_repetition.md)
- [ ] API 文档更新
- [ ] 代码注释完整

---

## 🚨 常见陷阱

### 1. 时间计算错误

```python
❌ 错误: 直接相加天数
next_review = datetime.now() + interval_days  # 类型错误!

✅ 正确: 使用 timedelta
next_review = datetime.now() + timedelta(days=interval_days)
```

### 2. 掌握度计算逻辑错误

```python
❌ 错误: 只看最近一次结果
mastery = 1.0 if last_review.result == 'correct' else 0.0

✅ 正确: 加权平均历史记录
mastery = calculate_mastery_level(review_history)
```

### 3. 事务未提交

```python
❌ 错误: 忘记 commit
review = await self.review_repo.create(data)
# 没有 commit!

✅ 正确: 使用 async with 或手动 commit
async with self.db.begin():
    review = await self.review_repo.create(data)
    # 自动 commit
```

### 4. JSON 查询兼容性

```python
❌ 错误: 直接使用 PostgreSQL 语法
stmt.where(MistakeRecord.knowledge_points @> ['数学'])

✅ 正确: 使用 SQLAlchemy 抽象
stmt.where(MistakeRecord.knowledge_points.contains(['数学']))
```

---

## 📚 参考资料

- **BaseRepository**: `src/repositories/base_repository.py`
- **LearningService**: `src/services/learning_service.py` (参考实现)
- **艾宾浩斯遗忘曲线**: https://en.wikipedia.org/wiki/Forgetting_curve
- **SuperMemo 算法**: https://www.supermemo.com/en/archives1990-2015/english/ol/sm2
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

## 📝 提交清单

```bash
git add src/repositories/mistake_repository.py
git add src/repositories/mistake_review_repository.py
git add src/services/algorithms/spaced_repetition.py
git add src/services/mistake_service.py
git add src/schemas/mistake.py
git add tests/repositories/test_mistake_repository.py
git add tests/services/test_mistake_service.py
git add tests/services/test_spaced_repetition.py
git add tests/fixtures/mistake_fixtures.py
git add docs/algorithms/spaced_repetition.md

git commit -m "feat(mistake): 实现错题手册核心业务逻辑

- 新增 MistakeRepository 和 MistakeReviewRepository
- 实现艾宾浩斯遗忘曲线算法
- 完整的 CRUD 操作和复习计划生成
- 集成 AI 服务分析知识点
- 单元测试覆盖率 87%

Refs: TASK-1.2"
```

---

**预估完成时间**: 5-6 天  
**下一步任务**: Task 1.3 (错题 API 路由和中间件)  
**问题联系**: 项目维护者

---

_最后更新: 2025-10-12 | 版本: v1.0_

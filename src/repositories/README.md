# 仓储层使用指南

## 概述

本仓储层为五好伴学项目提供了灵活且强大的数据访问基础设施，采用分层设计，支持复杂的学习问答业务场景。

## 架构设计

```
Service Layer (服务层)
    ↓
Repository Layer (仓储层)
    ├── BaseRepository (基础仓储)
    └── LearningRepository (业务仓储)
    ↓
SQLAlchemy ORM (对象关系映射)
    ↓
Database (数据库)
```

## 核心组件

### 1. BaseRepository (基础仓储)

**职责**：提供通用的CRUD操作和基础查询功能

**特性**：
- 泛型设计，支持任意SQLAlchemy模型
- 完整的异步CRUD操作
- 批量操作支持
- 搜索和过滤功能
- 事务管理和错误处理

**使用场景**：
- 简单的数据创建、读取、更新、删除
- 基础的列表查询和分页
- 标准的数据验证和约束处理

### 2. LearningRepository (学习业务仓储)

**职责**：封装学习问答业务相关的复杂查询逻辑

**特性**：
- 专门的学习分析查询
- 复杂的关联查询和统计分析
- 性能优化的批量操作
- 学习模式分析和知识掌握评估

**使用场景**：
- 学习数据的深度分析
- 复杂的统计查询
- 个性化学习推荐
- 知识掌握度评估

## 快速开始

### 基础用法

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories import BaseRepository
from src.models.learning import ChatSession

class MyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.session_repo = BaseRepository(ChatSession, db)

    async def create_session(self, user_id: str, title: str):
        """创建新会话"""
        session_data = {
            'user_id': user_id,
            'title': title,
            'status': 'active'
        }
        return await self.session_repo.create(session_data)

    async def get_user_sessions(self, user_id: str, limit: int = 10):
        """获取用户会话列表"""
        return await self.session_repo.get_all(
            filters={'user_id': user_id},
            limit=limit,
            order_by='-created_at'
        )
```

### 高级用法

```python
from src.repositories import BaseRepository, LearningRepository
from src.models.learning import ChatSession, Question, Answer

class EnhancedLearningService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 基础仓储用于简单操作
        self.session_repo = BaseRepository(ChatSession, db)
        self.question_repo = BaseRepository(Question, db)

        # 业务仓储用于复杂查询
        self.learning_repo = LearningRepository(db)

    async def get_learning_insights(self, user_id: str):
        """获取学习洞察分析"""
        # 使用专门的分析方法
        stats = await self.learning_repo.get_user_learning_stats(user_id)
        mastery = await self.learning_repo.get_knowledge_mastery_analysis(user_id)
        pattern = await self.learning_repo.get_daily_activity_pattern(user_id)

        return {
            'basic_stats': stats,
            'knowledge_mastery': mastery,
            'activity_pattern': pattern
        }
```

## BaseRepository API 参考

### 核心方法

#### 创建操作
```python
# 创建单个记录
record = await repo.create(data_dict)

# 批量创建
records = await repo.bulk_create([data1, data2, data3])
```

#### 读取操作
```python
# 按ID获取
record = await repo.get_by_id("record_id")

# 按字段获取
record = await repo.get_by_field("username", "john")

# 获取列表（支持过滤、排序、分页）
records = await repo.get_all(
    filters={'status': 'active'},
    order_by='-created_at',
    limit=10,
    offset=0
)

# 搜索记录
results = await repo.search(
    search_term="python",
    search_fields=['title', 'content'],
    limit=20
)
```

#### 更新操作
```python
# 更新单个记录
updated = await repo.update("record_id", {'title': 'New Title'})

# 批量更新
count = await repo.bulk_update([
    {'id': 'id1', 'status': 'completed'},
    {'id': 'id2', 'status': 'pending'}
])
```

#### 删除操作
```python
# 删除单个记录
success = await repo.delete("record_id")

# 批量删除
count = await repo.bulk_delete(["id1", "id2", "id3"])
```

#### 统计操作
```python
# 统计总数
total = await repo.count(filters={'status': 'active'})

# 检查存在
exists = await repo.exists("record_id")
```

## LearningRepository API 参考

### 会话相关

```python
# 获取活跃会话
session = await learning_repo.get_user_active_session(
    user_id="user_123",
    subject="数学"
)

# 获取会话及统计信息
sessions = await learning_repo.get_user_sessions_with_stats(
    user_id="user_123",
    limit=10,
    status="active"
)

# 获取会话及问答历史
session_data = await learning_repo.get_session_with_qa_history(
    session_id="session_123",
    user_id="user_123",
    limit=20
)
```

### 问答查询

```python
# 搜索问题
questions = await learning_repo.search_questions_by_content(
    user_id="user_123",
    search_term="二次函数",
    subject="数学"
)

# 获取相关话题的最近问题
recent_q = await learning_repo.get_recent_questions_by_topic(
    user_id="user_123",
    topic="函数",
    days=7
)

# 获取低评分问答
low_rated = await learning_repo.get_questions_with_low_ratings(
    user_id="user_123",
    max_rating=2
)
```

### 学习分析

```python
# 学习统计数据
stats = await learning_repo.get_user_learning_stats(
    user_id="user_123",
    days=30
)

# 每日活动模式
pattern = await learning_repo.get_daily_activity_pattern(
    user_id="user_123",
    days=30
)

# 知识掌握分析
mastery = await learning_repo.get_knowledge_mastery_analysis(
    user_id="user_123",
    subject="数学"
)
```

### 批量操作

```python
# 批量更新会话统计
count = await learning_repo.bulk_update_session_stats(
    ["session1", "session2", "session3"]
)

# 清除用户缓存
await learning_repo.invalidate_user_cache("user_123")
```

## 最佳实践

### 1. 职责分离原则

```python
class LearningService:
    def __init__(self, db: AsyncSession):
        # ✅ 正确：根据操作复杂度选择合适的仓储
        self.session_repo = BaseRepository(ChatSession, db)      # 简单CRUD
        self.learning_repo = LearningRepository(db)              # 复杂查询

    async def create_session(self, data):
        # ✅ 简单创建操作使用基础仓储
        return await self.session_repo.create(data)

    async def get_learning_analytics(self, user_id):
        # ✅ 复杂分析使用业务仓储
        return await self.learning_repo.get_user_learning_stats(user_id)
```

### 2. 错误处理

```python
async def safe_create_question(self, question_data):
    try:
        return await self.question_repo.create(question_data)
    except IntegrityError as e:
        logger.error(f"Data integrity violation: {e}")
        raise ValidationError("问题数据不完整或重复")
    except Exception as e:
        logger.error(f"Unexpected error creating question: {e}")
        raise ServiceError("创建问题时发生错误")
```

### 3. 性能优化

```python
# ✅ 使用批量操作处理大量数据
questions = await self.question_repo.bulk_create(question_list)

# ✅ 使用专门的统计查询方法
stats = await self.learning_repo.get_user_learning_stats(user_id)

# ❌ 避免在循环中进行数据库查询
for question_id in question_ids:
    question = await self.question_repo.get_by_id(question_id)  # 不好
```

### 4. 事务管理

```python
async def create_question_with_answer(self, question_data, answer_data):
    # 事务在仓储层自动管理
    try:
        question = await self.question_repo.create(question_data)
        answer_data['question_id'] = question.id
        answer = await self.answer_repo.create(answer_data)
        return question, answer
    except Exception:
        # 数据库事务会自动回滚
        raise
```

### 5. 类型安全

```python
from typing import Optional, List
from src.models.learning import ChatSession

async def get_session(self, session_id: str) -> Optional[ChatSession]:
    """类型注解确保返回值类型明确"""
    return await self.session_repo.get_by_id(session_id)

async def get_sessions(self, user_id: str) -> List[ChatSession]:
    """列表查询也需要明确的类型注解"""
    return await self.session_repo.get_all(
        filters={'user_id': user_id}
    )
```

## 迁移指南

### 从直接SQLAlchemy查询迁移

```python
# ❌ 旧方式：直接在服务中写SQLAlchemy查询
class OldLearningService:
    async def get_user_sessions(self, user_id: str):
        stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

# ✅ 新方式：使用仓储抽象
class NewLearningService:
    async def get_user_sessions(self, user_id: str):
        return await self.session_repo.get_all(
            filters={'user_id': user_id}
        )
```

### 渐进式迁移策略

1. **第一阶段**：将简单的CRUD操作迁移到BaseRepository
2. **第二阶段**：识别复杂查询，迁移到LearningRepository
3. **第三阶段**：优化性能，使用批量操作和专门查询
4. **第四阶段**：完善错误处理和日志记录

## 性能考虑

### 查询优化

- 使用合适的索引策略
- 避免N+1查询问题
- 合理使用预加载（eager loading）
- 批量操作处理大数据集

### 内存管理

- 及时释放大结果集
- 使用流式查询处理大量数据
- 合理设置查询限制

### 缓存策略

- 识别热点数据
- 实现合理的缓存失效机制
- 避免缓存穿透和雪崩

## 故障排查

### 常见问题

1. **连接池耗尽**
   - 检查是否正确关闭数据库连接
   - 调整连接池大小配置

2. **查询性能差**
   - 检查是否有合适的索引
   - 使用EXPLAIN分析查询计划

3. **事务死锁**
   - 检查事务持有时间
   - 优化锁的获取顺序

### 调试技巧

```python
import logging

# 启用SQLAlchemy查询日志
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# 记录仓储操作日志
logger = get_logger(__name__)
logger.debug(f"Creating record with data: {data}")
```

## 扩展和定制

### 添加新的业务仓储

```python
from src.repositories.base_repository import BaseRepository

class CustomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.base_repo = BaseRepository(YourModel, db)

    async def your_custom_query(self, params):
        # 实现特定的业务查询逻辑
        pass
```

### 扩展BaseRepository

```python
class ExtendedBaseRepository(BaseRepository[ModelType]):
    async def soft_delete(self, record_id: str):
        """软删除实现"""
        return await self.update(record_id, {
            'deleted_at': datetime.now(),
            'is_deleted': True
        })
```

## 总结

本仓储层设计提供了：

- 🎯 **清晰的职责分离**：基础操作与业务逻辑分离
- 🚀 **高性能查询**：优化的批量操作和专门查询
- 🛡️ **类型安全**：完整的类型注解支持
- 🔧 **易于扩展**：模块化设计，便于定制
- 📊 **完善的日志**：详细的操作日志和错误追踪

通过合理使用这两个仓储类，可以构建出既高效又易维护的数据访问层，为五好伴学项目的学习问答功能提供坚实的数据基础。

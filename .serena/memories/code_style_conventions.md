# 代码风格和约定

## Python 编码规范

### 类型注解
- **强制使用类型注解** (mypy strict mode)
- 所有函数参数和返回值必须有类型注解
- 使用 `from typing import` 导入类型

```python
from typing import Optional, List, Dict
from uuid import UUID

async def get_user(user_id: UUID) -> Optional[UserModel]:
    pass
```

### 异常处理
- **禁止裸 except:** - 必须指定具体异常类型
- 使用自定义异常类 (src/core/exceptions.py)
- 记录异常日志

```python
# ✅ 正确
try:
    result = await some_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise CustomValidationError(str(e))

# ❌ 错误
try:
    result = await some_operation()
except:
    pass
```

### 异步编程
- **优先使用 async/await**
- 数据库操作必须异步
- HTTP 请求使用 httpx 异步客户端

### 函数设计
- **单一职责原则** - 函数不超过 60 行
- 复杂逻辑拆分为子函数
- 明确的函数命名

### 文档字符串
- 使用 **Google 风格** docstring
- 包含参数、返回值、异常说明

```python
async def analyze_homework(
    submission_id: UUID,
    use_ai: bool = True
) -> HomeworkAnalysis:
    """分析作业提交内容
    
    Args:
        submission_id: 作业提交ID
        use_ai: 是否使用AI分析
        
    Returns:
        HomeworkAnalysis: 分析结果
        
    Raises:
        SubmissionNotFoundError: 提交不存在
        AIServiceError: AI服务异常
    """
    pass
```

## 架构模式

### 四层架构
```
API Layer (src/api/) 
    ↓
Service Layer (src/services/)
    ↓ 
Repository Layer (src/repositories/)
    ↓
Model Layer (src/models/)
```

- **严禁跨层调用** (API 不能直接调用 Repository)
- Repository 使用泛型基类 `BaseRepository[Model]`
- Service 层处理业务逻辑

### 依赖注入
- 使用 FastAPI 的依赖注入系统
- 数据库会话通过依赖注入
- 避免全局状态

## 前端规范 (Vue 3)

### 组合式 API
- **优先使用 Composition API** (`<script setup>`)
- 明确区分 `ref` vs `reactive`
- 使用 TypeScript 严格模式

### 组件设计
- 单文件组件 (.vue)
- Props 定义类型接口
- 发射事件使用 defineEmits

### 状态管理
- 使用 **Pinia** 类型化 store
- 异步操作在 actions 中处理

## 通用约定

### 命名规范
- **变量/函数**: snake_case (Python), camelCase (TS)
- **类**: PascalCase  
- **常量**: UPPER_SNAKE_CASE
- **文件**: kebab-case 或 snake_case

### 环境管理
- **开发**: SQLite + 最小依赖
- **生产**: PostgreSQL + Redis + 完整监控
- 敏感信息存储在 `secrets/` 目录

### 性能优化
- 慢查询自动记录 (>500ms)
- 速率限制: 100 req/min per IP
- N+1 查询检测和缓存
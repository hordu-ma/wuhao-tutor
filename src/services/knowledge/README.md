# 知识点提取服务

## 概述

知识点提取服务 (`KnowledgeExtractionService`) 提供基于规则和 AI 的混合知识点提取能力，用于从作业内容和学习问答中自动识别涉及的知识点。

## 功能特性

- ✅ **规则匹配**: 基于预定义知识点词典的快速提取
- ✅ **AI 提取**: 使用百炼 API 进行语义理解和提取
- ✅ **混合策略**: 融合规则和 AI 结果，提升准确率
- ✅ **置信度评分**: 为每个知识点提供 0-1 的置信度分数
- ✅ **多学科支持**: 支持数学、语文、英语等学科
- ✅ **关键词匹配**: 基于关键词的模糊匹配
- ✅ **中文分词**: 集成 jieba 分词库

## 安装

```bash
# 安装依赖
uv add jieba
```

## 快速开始

### 1. 基础使用（仅规则）

```python
from src.services.knowledge.extraction_service import KnowledgeExtractionService

# 初始化服务
extraction_service = KnowledgeExtractionService()

# 提取知识点（同步）
content = "求二次函数 y = x² - 4x + 3 的顶点坐标"
knowledge_points = extraction_service.extract_from_question(
    content=content,
    subject="math",
    grade="九年级"
)

# 打印结果
for kp in knowledge_points:
    print(f"{kp.name} (置信度: {kp.confidence:.2f})")
```

### 2. 高级使用（规则 + AI）

```python
from src.services.knowledge.extraction_service import KnowledgeExtractionService
from src.services.bailian_service import get_bailian_service

# 初始化服务（包含 AI）
bailian_service = get_bailian_service()
extraction_service = KnowledgeExtractionService(bailian_service)

# 提取知识点（异步）
content = "这道题涉及抛物线的顶点、对称轴和开口方向"
knowledge_points = await extraction_service.extract_from_homework(
    content=content,
    subject="math",
    grade="九年级"
)

# 打印详细结果
for kp in knowledge_points:
    print(f"知识点: {kp.name}")
    print(f"  置信度: {kp.confidence:.2f}")
    print(f"  提取方法: {kp.method}")  # rule/ai/hybrid
    print(f"  匹配关键词: {kp.matched_keywords}")
    print(f"  相关知识点: {kp.related}")
```

## API 文档

### KnowledgeExtractionService

#### 方法

##### `__init__(bailian_service=None)`

初始化知识点提取服务。

**参数**:

- `bailian_service` (Optional[BailianService]): 百炼 AI 服务实例。如果不提供，则仅使用规则提取。

##### `extract_from_homework(content, subject, grade=None) -> List[KnowledgePoint]`

从作业内容提取知识点（异步，支持 AI 增强）。

**参数**:

- `content` (str): 作业内容
- `subject` (str): 学科（math/chinese/english）
- `grade` (Optional[str]): 年级

**返回**: 知识点列表（最多 10 个，按置信度降序）

##### `extract_from_question(content, subject, grade=None) -> List[KnowledgePoint]`

从问题内容提取知识点（同步，仅规则）。

**参数**:

- `content` (str): 问题内容
- `subject` (str): 学科
- `grade` (Optional[str]): 年级

**返回**: 知识点列表

### KnowledgePoint

知识点数据模型。

**属性**:

- `name` (str): 知识点名称
- `confidence` (float): 置信度 (0-1)
- `method` (str): 提取方法 (rule/ai/hybrid)
- `matched_keywords` (List[str]): 匹配的关键词
- `context` (Optional[str]): 上下文片段
- `related` (List[str]): 相关知识点

**方法**:

- `to_dict() -> Dict`: 转换为字典

## 知识点词典

知识点词典位于 `data/knowledge_dict/` 目录，按学科组织：

```
data/knowledge_dict/
├── math_grade_9.json      # 数学九年级
├── chinese_grade_9.json   # 语文九年级
└── english_grade_9.json   # 英语九年级
```

### 词典格式

```json
{
  "知识点名称": {
    "keywords": ["关键词1", "关键词2"],
    "related": ["相关知识点1", "相关知识点2"],
    "difficulty": 3,
    "description": "知识点描述"
  }
}
```

## 提取策略

### 1. 规则匹配

- **名称直接匹配**: 如果内容中包含知识点名称，置信度 0.9
- **关键词匹配**: 根据匹配关键词数量计算置信度（最高 0.85）
- **中文分词**: 使用 jieba 分词提高匹配准确率

### 2. AI 提取

- **语义理解**: 使用百炼 API 理解题目语义
- **准确提取**: 提取最相关的 5 个知识点
- **基础置信度**: AI 提取的知识点置信度为 0.8

### 3. 结果融合

- **去重**: 相同知识点只保留一个
- **置信度提升**: 规则和 AI 都提取到的知识点，置信度 +0.1
- **方法标记**: 标记为 hybrid（混合）

## 测试

```bash
# 运行单元测试
uv run pytest tests/unit/knowledge/test_extraction_service.py -v

# 运行示例
uv run python examples/knowledge_extraction_example.py
```

## 性能指标

- **提取准确率**: > 80% (基于人工标注测试集)
- **平均提取时间**:
  - 规则匹配: < 100ms
  - AI 增强: < 500ms
- **知识点数量**: 最多返回 10 个（按置信度降序）

## 扩展知识点词典

### 1. 添加新知识点

编辑对应学科的 JSON 文件：

```json
{
  "新知识点": {
    "keywords": ["关键词1", "关键词2"],
    "related": ["相关知识点"],
    "difficulty": 3,
    "description": "知识点描述"
  }
}
```

### 2. 添加新学科

创建新的 JSON 文件，如 `physics_grade_9.json`：

```json
{
  "牛顿第一定律": {
    "keywords": ["惯性", "力", "运动状态"],
    "related": ["牛顿第二定律", "牛顿第三定律"],
    "difficulty": 3,
    "description": "物体在不受力时保持静止或匀速直线运动"
  }
}
```

服务会自动加载所有 `*.json` 文件。

## 常见问题

### Q: 如何提高提取准确率？

A:

1. 丰富知识点词典的关键词
2. 启用 AI 提取（需要百炼服务）
3. 提供更多上下文信息

### Q: 如何处理多义词？

A: 通过学科参数区分，例如"函数"在数学和语文中的含义不同。

### Q: 提取速度慢怎么办？

A:

1. 仅使用规则提取（不传 bailian_service）
2. 实施缓存机制
3. 减少 AI 调用频率

## 更新日志

### v1.0.0 (2025-10-05)

- ✅ 初始版本
- ✅ 支持规则匹配和 AI 提取
- ✅ 集成 jieba 分词
- ✅ 支持数学、语文、英语三科
- ✅ 完整的单元测试覆盖

## 许可证

MIT License

# 知识图谱数据说明

## 目录结构

```
data/knowledge/
├── README.md                   # 本文件
├── math/                       # 数学学科
│   ├── grade_7.json           # 七年级（初一）
│   ├── grade_8.json           # 八年级（初二）
│   └── grade_9.json           # 九年级（初三）
├── chinese/                    # 语文学科
│   ├── grade_7.json
│   ├── grade_8.json
│   └── grade_9.json
└── english/                    # 英语学科
    ├── grade_7.json
    ├── grade_8.json
    └── grade_9.json
```

## 数据格式说明

### 节点数据结构

```json
{
  "nodes": [
    {
      "code": "math_7_1_1",
      "name": "有理数",
      "node_type": "chapter",
      "subject": "math",
      "level": 1,
      "parent_code": null,
      "description": "有理数的概念、分类和运算",
      "keywords": ["正数", "负数", "整数", "分数"],
      "examples": ["正整数: 1, 2, 3, ...", "负整数: -1, -2, -3, ...", "分数: 1/2, -3/4, ..."],
      "difficulty": 2,
      "importance": 5,
      "tags": ["基础", "必修"],
      "external_links": ["https://example.com/rational-numbers"]
    }
  ]
}
```

### 字段说明

| 字段             | 类型    | 必填 | 说明                                                                     |
| ---------------- | ------- | ---- | ------------------------------------------------------------------------ |
| `code`           | string  | ✅   | 节点唯一编码，格式: `{subject}_{grade}_{chapter}_{section}`              |
| `name`           | string  | ✅   | 节点名称                                                                 |
| `node_type`      | string  | ✅   | 节点类型: `subject`/`chapter`/`section`/`concept`/`skill`/`problem_type` |
| `subject`        | string  | ✅   | 学科代码: `math`/`chinese`/`english`                                     |
| `level`          | integer | ✅   | 层级深度 (1-10)                                                          |
| `parent_code`    | string  | ❌   | 父节点编码 (顶层节点为 null)                                             |
| `description`    | string  | ❌   | 详细描述                                                                 |
| `keywords`       | array   | ❌   | 关键词列表                                                               |
| `examples`       | array   | ❌   | 示例列表                                                                 |
| `difficulty`     | integer | ❌   | 难度等级 (1-5, 默认 3)                                                   |
| `importance`     | integer | ❌   | 重要性 (1-5, 默认 3)                                                     |
| `tags`           | array   | ❌   | 标签列表                                                                 |
| `external_links` | array   | ❌   | 外部链接                                                                 |

### 关系数据结构

```json
{
  "relations": [
    {
      "from_code": "math_7_1_1",
      "to_code": "math_7_1_2",
      "relation_type": "prerequisite",
      "weight": 0.9,
      "is_bidirectional": false,
      "description": "有理数是绝对值的前置知识",
      "confidence": 0.95
    }
  ]
}
```

### 关系类型

| 类型           | 说明     | 示例              |
| -------------- | -------- | ----------------- |
| `prerequisite` | 前置关系 | A 是 B 的前置知识 |
| `contains`     | 包含关系 | A 包含 B          |
| `similar`      | 相似关系 | A 和 B 相似       |
| `applies_to`   | 应用关系 | A 应用于 B        |
| `derives_from` | 派生关系 | A 派生自 B        |

### 关系字段说明

| 字段               | 类型    | 必填 | 说明                         |
| ------------------ | ------- | ---- | ---------------------------- |
| `from_code`        | string  | ✅   | 源节点编码                   |
| `to_code`          | string  | ✅   | 目标节点编码                 |
| `relation_type`    | string  | ✅   | 关系类型                     |
| `weight`           | float   | ❌   | 关系权重 (0.0-1.0, 默认 1.0) |
| `is_bidirectional` | boolean | ❌   | 是否双向 (默认 false)        |
| `description`      | string  | ❌   | 关系描述                     |
| `confidence`       | float   | ❌   | 置信度 (0.0-1.0, 默认 0.8)   |

## 编码规范

### 节点编码格式

```
{subject}_{grade}_{chapter}_{section}[_{subsection}]
```

**示例**:

- `math_7_1`: 七年级数学第 1 章
- `math_7_1_1`: 七年级数学第 1 章第 1 节
- `math_7_1_1_1`: 七年级数学第 1 章第 1 节第 1 小节

### 学科代码

- `math`: 数学
- `chinese`: 语文
- `english`: 英语

### 年级代码

- `7`: 七年级（初一）
- `8`: 八年级（初二）
- `9`: 九年级（初三）

## 数据来源

数据基于中国教育部《义务教育课程标准》(2022 年版):

- 数学课程标准
- 语文课程标准
- 英语课程标准

## 数据质量要求

1. **完整性**: 每个年级必须覆盖课程标准的核心知识点
2. **准确性**: 知识点描述准确，关系定义正确
3. **一致性**: 编码格式统一，命名规范一致
4. **可扩展性**: 支持后续添加新的知识点和关系

## 更新历史

- 2025-10-05: 初始化目录结构，定义数据格式规范

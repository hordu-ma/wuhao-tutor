# data/ 目录

## 📁 目录结构

```
data/
├── knowledge/         # 知识库数据（静态）
├── knowledge_dict/    # 知识词典（静态）
└── local/             # 本地运行时数据（生成）
```

## 📝 各目录说明

### knowledge/

**用途**：存储知识库的静态数据文件

- **类型**：静态数据（不在运行时修改）
- **格式**：JSON、YAML 或其他数据格式
- **来源**：初始化或导入的数据
- **Git 跟踪**：✅ 是（这些是项目必需的数据）
- **使用场景**：
  - 知识图谱的初始节点
  - 学科分类数据
  - 标准化的知识体系

### knowledge_dict/

**用途**：知识词典和术语库

- **类型**：静态数据（预定义的词典）
- **格式**：JSON 词典文件
- **来源**：项目初始化时提供
- **Git 跟踪**：✅ 是（这些是项目必需的数据）
- **使用场景**：
  - NLP 处理中的词库
  - 知识点术语对应
  - 文本标准化参考

### local/

**用途**：本地开发时生成的数据（临时）

- **类型**：动态数据（运行时生成）
- **生成时机**：
  - 程序启动时
  - 测试运行时
  - 数据处理时
- **Git 跟踪**：❌ 否（应添加到 .gitignore）
- **生命周期**：临时，可随时删除
- **常见文件**：
  - 缓存数据
  - 中间处理结果
  - 本地测试数据

## 🔄 数据流向

```
knowledge/ 和 knowledge_dict/
      ↓
  (项目提供)
      ↓
  应用程序
      ↓
local/ (生成/缓存)
```

## 🛠️ 使用示例

```python
# 加载知识库数据
from pathlib import Path
import json

# 静态知识数据
knowledge_path = Path("data/knowledge")
knowledge_data = json.load(open(knowledge_path / "nodes.json"))

# 生成本地缓存
local_path = Path("data/local")
local_path.mkdir(exist_ok=True)
cache_file = local_path / "cache.json"
```

## 📌 最佳实践

- ✅ 提交 `knowledge/` 和 `knowledge_dict/` 到 Git
- ❌ 不要提交 `local/` 目录（应在 .gitignore）
- 📝 在程序中使用相对路径访问这些目录
- 🔒 定期备份重要的静态知识数据
- 🧹 定期清理 `local/` 目录以节省空间

---

**更新**：2025-11-13

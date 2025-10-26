# 提示词快速参考

## 📋 四个核心场景

### 1️⃣ 学习问答（主功能）⭐

- **文件**: `learning_service.py:528`
- **Temperature**: 0.7
- **模型**: 自动（qwen-turbo / qwen-vl-max）
- **核心**: 五好助教，K12 学习助手

```
角色：专业K12助教，亲切友好
职责：解答问题、分析题目、学习建议、鼓励学生
要求：**粗体**标重点、举例说明、数学题写步骤
个性化：学段/学科/薄弱点
```

### 2️⃣ 错题分析

- **文件**: `mistake_service.py:628`
- **Temperature**: 0.7
- **输出**: JSON

```json
{
  "knowledge_points": ["点1", "点2", "点3"],
  "error_reason": "100字内",
  "suggestions": "150字内"
}
```

### 3️⃣ 答案质量评估

- **文件**: `answer_quality_service.py:259`
- **Temperature**: 0.3（稳定评分）
- **输出**: 5 维度 0.0-1.0

准确性/完整性/清晰度/有用性/相关性

### 4️⃣ 知识点提取

- **文件**: `extraction_service.py:215`
- **Temperature**: 0.3（准确）
- **输出**: 每行一个，最多 5 个

---

## 🎯 百炼平台优化建议

1. **系统指令**: 配置"学习问答"基础提示词（减少 token）
2. **JSON Schema**: 为错题分析/质量评估配置结构化输出
3. **参数调优**:
   - 学习问答: temp=0.7, max_tokens=1500
   - 错题分析: temp=0.7, max_tokens=1000
   - 质量评估: temp=0.3, max_tokens=800
   - 知识提取: temp=0.3, max_tokens=200

---

详见：`docs/operations/prompt-settings-summary.md`

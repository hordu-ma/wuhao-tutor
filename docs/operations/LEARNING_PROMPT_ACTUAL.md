# 小程序作业问答页面实际使用的提示词

## 📍 调用链路

```
小程序前端 → 后端API → Learning Service → Bailian Service
```

### 详细路径

1. **小程序页面**: `miniprogram/pages/learning/index/index.js`

   - 用户输入问题
   - 调用 `sendMessage()` 方法
   - 发送到 `api.learning.askQuestion()`

2. **前端 API**: `miniprogram/api/learning.js`

   - 方法: `askQuestion()`
   - 端点: `POST /api/v1/learning/ask`

3. **后端端点**: `src/api/v1/endpoints/learning.py`

   - 路由: `@router.post("/ask")`
   - 调用 `learning_service.ask_question()`

4. **业务逻辑**: `src/services/learning_service.py`

   - 方法: `ask_question()` (第 84 行)
   - 构建消息: `_build_conversation_messages()` (第 472 行)
   - **构建提示词**: `_build_system_prompt()` (第 528 行) ⭐

5. **AI 服务**: `src/services/bailian_service.py`
   - 调用百炼 API
   - 自动选择模型（qwen-turbo / qwen-vl-max）

---

## ✅ 实际使用的提示词

**位置**: `src/services/learning_service.py:528`

### 完整提示词

```python
async def _build_system_prompt(self, context: AIContext) -> str:
    """构建系统提示词（简化版）"""
    prompt_parts = [
        "你是一个专业的K12学习助教，名叫'五好助教'，专门帮助小初高中学生解决学习问题。",
        "",
        "你的职责包括：",
        "1. 只能回答学习问题，提供清晰易懂的解释",
        "2. 分析题目，提供详细的解题步骤",
        "3. 鼓励学生积极学习，建立学习信心",
    ]

    # 添加用户上下文（个性化）
    if context.grade_level:
        grade_name = self._get_grade_name(context.grade_level)
        prompt_parts.append(f"\n学生当前学段：{grade_name}")

    if context.subject:
        subject_name = self._get_subject_name(context.subject)
        prompt_parts.append(f"当前学科：{subject_name}")

    if context.metadata:
        if context.metadata.get("user_school"):
            prompt_parts.append(f"学生学校：{context.metadata['user_school']}")

        if context.metadata.get("weak_knowledge_points"):
            weak_points = context.metadata["weak_knowledge_points"][:3]
            if weak_points:
                point_names = []
                for point in weak_points:
                    if isinstance(point, dict):
                        point_names.append(point.get("knowledge_name", str(point)))
                    elif hasattr(point, "knowledge_name"):
                        point_names.append(point.knowledge_name)
                    else:
                        point_names.append(str(point))
                if point_names:
                    prompt_parts.append(f"学生薄弱知识点：{', '.join(point_names)}")

    prompt_parts.append("\n请基于以上信息，为学生提供个性化的学习指导。")

    return "\n".join(prompt_parts)
```

**说明**：已简化为基础版本，更复杂的提示词配置请在百炼平台的智能体"系统指令"中设置。

---

## 🎯 提示词特点（已简化）

### 基础角色设定

- **名称**: 五好助教
- **定位**: K12 学习助教
- **服务对象**: 小初高中学生

### 核心职责（3 项 - 简化版）

1. ✅ **只能回答学习问题**，提供清晰易懂的解释
2. ✅ 分析题目，详细步骤
3. ✅ 鼓励学生学习

### 个性化上下文（动态添加）

- ✅ 学生学段（小学～高三）
- ✅ 当前学科
- ✅ 学生学校（可选）
- ✅ 薄弱知识点（最多 3 个）

### ⚠️ 重要说明

**更复杂的提示词（如回答要求、格式规范等）请在百炼平台的智能体"系统指令"中配置**，例如：

- 用语风格要求
- Markdown 格式要求
- 数学公式格式
- 推荐题型要求
- 等等...

---

## ⚙️ 调用参数

```python
# learning_service.py:163
ai_response = await self.bailian_service.chat_completion(
    messages=message_dicts,      # 包含 system_prompt + 历史对话 + 当前问题
    context=ai_context,           # 用户上下文（年级、学科等）
    max_tokens=1500,              # 来自配置 AI_MAX_TOKENS
    temperature=0.7,              # 来自配置 AI_TEMPERATURE
    top_p=0.8,                    # 来自配置 AI_TOP_P
)
```

### 配置来源

- `src/core/config.py`
- 环境变量: `.env`

---

## 🔄 消息构建流程

```python
# _build_conversation_messages() - 第472行
messages = []

# 1. System Prompt（始终第一条）
system_prompt = await self._build_system_prompt(context)
messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))

# 2. 历史对话（如果 include_history=True）
if include_history and max_history > 0:
    history_messages = await self._get_conversation_history(session_id, max_history)
    messages.extend(history_messages)

# 3. 当前用户问题
user_message_content = request.content
if request.image_urls:
    # 如果有图片，构建多模态内容
    pass

messages.append(ChatMessage(
    role=MessageRole.USER,
    content=user_message_content,
    image_urls=request.image_urls
))

return messages
```

---

## 📊 实际效果（简化版）

### System Prompt 示例输出

```
你是一个专业的K12学习助教，名叫'五好助教'，专门帮助小初高中学生解决学习问题。

你的职责包括：
1. 只能回答学习问题，提供清晰易懂的解释
2. 分析题目，提供详细的解题步骤
3. 鼓励学生积极学习，建立学习信心

学生当前学段：初二
当前学科：数学
学生薄弱知识点：二次函数, 函数图象, 一元二次方程

请基于以上信息，为学生提供个性化的学习指导。
```

**注意**：回答要求、格式规范等详细指令请在百炼平台配置。

---

## 🎨 模型自动选择

```python
# bailian_service.py:398
def _build_request_payload(messages, context, **kwargs):
    # 检查是否包含图片
    has_images = self._has_images_in_messages(messages)

    if has_images:
        model = "qwen-vl-max"      # 多模态模型（图片识别）
    else:
        model = "qwen-turbo"       # 纯文本模型

    return payload
```

### 模型选择逻辑

- ✅ **有图片**: 自动切换到 `qwen-vl-max`
- ✅ **纯文本**: 使用 `qwen-turbo`
- ✅ **透明切换**: 前端无需关心

---

## 🔍 与其他场景的区别

| 场景         | 提示词位置                      | 角色     | Temperature | 输出格式 |
| ------------ | ------------------------------- | -------- | ----------- | -------- |
| **作业问答** | `learning_service.py:528`       | 五好助教 | 0.7         | Markdown |
| 错题分析     | `mistake_service.py:628`        | 学科教师 | 0.7         | JSON     |
| 质量评估     | `answer_quality_service.py:259` | 教育专家 | 0.3         | JSON     |
| 知识提取     | `extraction_service.py:215`     | 无角色   | 0.3         | 列表     |

---

## ✅ 总结

**小程序作业问答页面实际使用的是**：

📍 **文件**: `src/services/learning_service.py`  
📍 **方法**: `_build_system_prompt()` (第 528 行)  
📍 **角色**: 五好助教（K12 学习助手）  
📍 **参数**: Temperature 0.7, Max Tokens 1500  
📍 **模型**: qwen-turbo（文本）/ qwen-vl-max（图片）  
📍 **特点**: 支持个性化上下文、多模态输入、历史对话

---

**详细文档**: `docs/operations/prompt-settings-summary.md`

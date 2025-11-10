# 错题本优化 - 快速启动指南

> **目标**: 10 分钟快速了解错题本优化方案并开始开发
> **完整文档**: [MISTAKE_EXTRACTION_OPTIMIZATION.md](./MISTAKE_EXTRACTION_OPTIMIZATION.md)

---

## 🎯 核心问题

**当前**：用户上传作业图片后，整次对话被录入为一条错题记录  
**目标**：AI 逐题批改，只有错题/未作答的题进入错题本，每题独立记录

---

## 📋 方案概览

### 改造范围
- ✅ **数据库**：MistakeRecord 表新增 4 个字段
- ✅ **后端**：LearningService 新增批改逻辑
- ✅ **AI Prompt**：新增作业批改专用 Prompt
- ✅ **前端**：新增批改结果卡片组件

### 不改造
- ❌ 不新增页面入口（复用学习问答页面）
- ❌ 不影响现有问答功能
- ❌ 不需要改造 homework 模块

---

## 🚀 快速开始（3 步）

### Step 1: 数据库迁移（5 分钟）

```bash
# 1. 进入项目目录
cd /opt/wuhao-tutor
source .venv/bin/activate

# 2. 创建迁移文件
alembic revision -m "add_mistake_fields_for_homework_correction"

# 3. 编辑迁移文件（复制完整文档中的代码）
vim alembic/versions/xxx_add_mistake_fields.py

# 4. 执行迁移
alembic upgrade head

# 5. 验证
sqlite3 wuhao_tutor_dev.db "PRAGMA table_info(mistake_records);"
# 应该看到: question_number, is_unanswered, question_type, error_type
```

**新增字段**：
- `question_number` (Integer): 题号（从1开始）
- `is_unanswered` (Boolean): 是否未作答
- `question_type` (String): 题目类型（选择/填空/解答）
- `error_type` (String): 错误类型（未作答/计算错误等）

---

### Step 2: 后端核心逻辑（30 分钟）

**文件**: `src/services/learning_service.py`

#### 2.1 添加 Prompt 常量（复制使用）

```python
# 在文件顶部添加
HOMEWORK_CORRECTION_PROMPT = """你是一位经验丰富的K12作业批改老师，擅长{subject}学科。

**任务**：分析图片中的所有题目，逐题批改。

**输出格式**：严格按照以下JSON格式返回：
{
  "questions": [
    {
      "number": 1,
      "type": "选择题",
      "question_text": "题目原文",
      "student_answer": "A",
      "is_answered": true,
      "is_correct": false,
      "correct_answer": "B",
      "explanation": "详细解析",
      "knowledge_points": ["二次函数", "图像"],
      "difficulty": 2,
      "error_type": "概念错误"
    }
  ],
  "summary": {"total": 10, "correct": 7, "wrong": 2, "unanswered": 1}
}
"""
```

#### 2.2 添加 3 个核心方法

在 `LearningService` 类中添加：

1. **判断是否为批改场景**：
   ```python
   def _is_homework_correction_scenario(self, content: str, image_urls: List[str]) -> bool:
       """有图片 + 简短文本 → 批改模式"""
       if not image_urls or len(image_urls) == 0:
           return False
       return len(content.strip()) <= 50 or any(k in content for k in ["批改", "作业", "答案"])
   ```

2. **调用 AI 批改**：
   ```python
   async def _call_ai_for_homework_correction(
       self, image_urls: List[str], subject: str, user_hint: str = ""
   ) -> Dict[str, Any]:
       """调用百炼 API，返回 JSON 格式批改结果"""
       # 完整代码见主文档
   ```

3. **逐题创建错题**：
   ```python
   async def _create_mistake_from_question(
       self, user_id: str, question_id: str, question_data: Dict, subject: str, image_urls: List[str]
   ) -> Optional[MistakeRecord]:
       """从单题数据创建错题记录（仅错题/未作答）"""
       # 完整代码见主文档
   ```

#### 2.3 修改 `ask_question` 主流程

```python
async def ask_question(self, user_id: str, request: AskQuestionRequest) -> AskQuestionResponse:
    # ... 前置逻辑 ...
    
    # 🎯 判断批改场景
    is_homework = self._is_homework_correction_scenario(request.content, request.image_urls)
    
    if is_homework:
        # 批改模式
        correction_data = await self._call_ai_for_homework_correction(...)
        for q_data in correction_data["questions"]:
            mistake = await self._create_mistake_from_question(...)
            if mistake:
                created_mistakes.append(mistake)
        # 返回批改结果
        return AskQuestionResponse(..., correction_result=correction_data)
    else:
        # 原有问答模式（不动）
        ...
```

---

### Step 3: 前端批改结果展示（20 分钟）

**文件**: `miniprogram/components/correction-card/`

#### 3.1 创建组件目录

```bash
mkdir -p miniprogram/components/correction-card
cd miniprogram/components/correction-card
touch index.wxml index.js index.wxss index.json
```

#### 3.2 组件代码（复制使用）

**index.json**:
```json
{
  "component": true,
  "usingComponents": {
    "van-icon": "/miniprogram_npm/@vant/weapp/icon/index",
    "van-tag": "/miniprogram_npm/@vant/weapp/tag/index"
  }
}
```

**index.wxml** (核心结构):
```xml
<view class="correction-card">
  <view class="summary">
    <text class="title">📝 批改完成</text>
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
  
  <view class="questions-list">
    <block wx:for="{{wrongQuestions}}" wx:key="number">
      <view class="question-item" bindtap="onQuestionTap" data-index="{{index}}">
        <text>第{{item.number}}题: {{item.question_text}}</text>
      </view>
    </block>
  </view>
  
  <button class="btn-view-mistakes" bindtap="onViewAllMistakes">
    查看错题本 ({{data.mistakes_created}})
  </button>
</view>
```

**index.js** (过滤错题):
```javascript
Component({
  properties: {
    data: {type: Object, value: {}}
  },
  data: {
    wrongQuestions: []
  },
  observers: {
    'data': function(newData) {
      const wrongQuestions = (newData.questions || []).filter(q => !q.is_correct);
      this.setData({ wrongQuestions });
    }
  },
  methods: {
    onViewAllMistakes() {
      wx.navigateTo({url: '/pages/mistakes/list/index'});
    }
  }
});
```

#### 3.3 集成到学习问答页面

**文件**: `miniprogram/pages/learning/index/index.json`
```json
{
  "usingComponents": {
    "correction-card": "/components/correction-card/index"
  }
}
```

**文件**: `miniprogram/pages/learning/index/index.wxml`
```xml
<!-- 在消息列表中添加 -->
<view wx:elif="{{item.type === 'correction_card'}}" class="message">
  <correction-card data="{{item.data}}" />
</view>
```

**文件**: `miniprogram/pages/learning/index/index.js`
```javascript
// 处理批改响应
handleCorrectionResponse(response) {
  const { correction_result, answer } = response;
  
  // 添加批改结果卡片
  this.addMessage({
    type: 'correction_card',
    data: correction_result,
    timestamp: Date.now()
  });
  
  // 显示成功提示
  wx.showToast({
    title: `已加入${correction_result.mistakes_created}道错题`,
    icon: 'success'
  });
}
```

---

## ✅ 验证清单

### 后端验证

```bash
# 1. 运行单元测试
pytest tests/services/test_learning_service_correction.py -v

# 2. 启动开发服务器
make dev

# 3. 使用 Postman 测试
# POST /api/v1/learning/ask
# Body: {
#   "content": "请批改这些题",
#   "image_urls": ["https://..."],
#   "subject": "数学"
# }
# 
# 检查响应中是否包含:
# - correction_result (批改结果)
# - mistakes_created (错题数量)
```

### 前端验证

```bash
# 1. 微信开发者工具打开项目
# 2. 进入"学习问答"页面
# 3. 上传作业图片（建议 2-3 题）
# 4. 点击发送，观察：
#    - 是否显示批改结果卡片
#    - 统计数字是否正确
#    - 点击"查看错题本"是否跳转
```

### 数据库验证

```sql
-- 查询最新创建的错题
SELECT id, question_number, question_type, is_unanswered, error_type, title
FROM mistake_records
WHERE created_at > datetime('now', '-1 hour')
ORDER BY created_at DESC
LIMIT 10;

-- 应该看到:
-- - question_number 有值（1, 2, 3...）
-- - question_type 有值（选择题/填空题等）
-- - 每条记录对应一道题
```

---

## 🐛 常见问题速查

| 问题 | 原因 | 解决方案 |
|-----|------|---------|
| AI 返回 JSON 格式错误 | Prompt 不够明确 | 在 Prompt 中添加更多示例 |
| 题目数量识别不准 | 图片不清晰 | 提示用户"确保图片清晰、光线充足" |
| 批改速度慢 (>30s) | 题目过多 | 限制单次上传 5 题以内 |
| 错题列表显示异常 | 旧数据格式不兼容 | 只显示 `question_number IS NOT NULL` 的记录 |
| 小程序白屏 | 组件路径错误 | 检查 `index.json` 中的组件路径 |

---

## 📊 开发进度追踪

```
Week 1: 数据库与后端基础
  ✅ Day 1-2: 数据库迁移
  ⬜ Day 3-4: AI Prompt 与调用
  ⬜ Day 5: 流程集成

Week 2: 核心业务逻辑
  ⬜ Day 6-7: 逐题创建错题
  ⬜ Day 8: 知识点关联
  ⬜ Day 9-10: API 测试

Week 3: 前端与联调
  ⬜ Day 11-12: 前端组件
  ⬜ Day 13: 前后端联调
  ⬜ Day 14-15: 测试与上线
```

---

## 📖 扩展阅读

- 📘 **完整开发文档**: [MISTAKE_EXTRACTION_OPTIMIZATION.md](./MISTAKE_EXTRACTION_OPTIMIZATION.md)
- 🎯 **产品价值**: [PRODUCT_VALUE.md](./PRODUCT_VALUE.md)
- 👥 **用户手册**: [USER_MANUAL.md](./USER_MANUAL.md)
- 🔧 **Copilot 指令**: [.github/copilot-instructions.md](.github/copilot-instructions.md)

---

## 🤝 获取帮助

- **遇到技术问题**：查看完整文档的"常见问题"章节
- **需要代码示例**：完整文档包含所有可复制的代码
- **需要测试指导**：完整文档包含单元测试/集成测试示例

**祝开发顺利！** 🚀
# 错题本功能 - 小程序前端 UI 集成 Todo List

## 📋 项目概述

**功能**：在学习问答页面添加"加入错题本"按钮，允许用户将 AI 回答的题目加入错题本

**后端状态**：✅ 已完成部署

- API 端点：`POST /api/v1/learning/questions/{question_id}/add-to-mistakes`
- 小程序 API 封装：`api.learning.addQuestionToMistakes(questionId, params)`
- 数据库迁移：已完成（添加 4 个新字段）

---

## 🎯 前端集成任务清单

### 任务 1：分析消息数据结构 🔍

**目标**：确定如何从消息对象中获取 `question_id`

**文件**：`miniprogram/pages/learning/index/index.js`

**需要分析的内容**：

1. `messageList` 数组的数据结构
2. AI 回答消息的数据格式
3. `question_id` 的存储位置（可能在 `item.id` 或其他字段）

**预期结果**：

- 确定消息对象中包含 `question_id` 的字段名
- 理解用户消息和 AI 消息的配对关系

**参考代码位置**：

```javascript
// 第 674 行：用户消息创建
messageList: [...this.data.messageList, userMessage]

// 第 889-893 行：AI 回复添加
const messageList = [...this.data.messageList]
const lastMessage = messageList[messageList.length - 1]
```

---

### 任务 2：添加"加入错题本"按钮（WXML）✏️

**文件**：`miniprogram/pages/learning/index/index.wxml`

**位置**：第 123-140 行（操作按钮区域）

**修改内容**：

在现有的操作按钮（复制、点赞）后面添加新按钮：

```xml
<!-- 操作按钮 -->
<view class="bubble-actions">
  <!-- ... existing code: 复制按钮 ... -->

  <!-- ... existing code: 点赞按钮 ... -->

  <!-- 【新增】加入错题本按钮（仅AI消息显示） -->
  <view wx:if="{{item.sender === 'ai' && item.questionId}}"
        class="action-btn"
        bindtap="onAddToMistakes"
        data-question-id="{{item.questionId}}"
        data-message-id="{{item.id}}">
    <van-icon name="bookmark-o" size="14" />
    <text class="action-label">错题本</text>
  </view>

  <!-- ... existing code: 重试按钮 ... -->
</view>
```

**关键点**：

- 只在 AI 消息上显示（`item.sender === 'ai'`）
- 需要确保 `item.questionId` 存在
- 使用 `data-question-id` 传递参数
- 图标使用 vant-weapp 的 `bookmark-o`

---

### 任务 3：添加事件处理函数（JavaScript）⚙️

**文件**：`miniprogram/pages/learning/index/index.js`

**位置**：在现有方法区域添加（建议在第 1500 行左右，与其他消息操作方法一起）

**添加内容**：

```javascript
/**
 * 将题目加入错题本
 */
async onAddToMistakes(e) {
  const { questionId, messageId } = e.currentTarget.dataset;

  if (!questionId) {
    wx.showToast({
      title: '无法获取题目ID',
      icon: 'none',
    });
    return;
  }

  try {
    // 显示加载提示
    wx.showLoading({
      title: '加入错题本中...',
      mask: true,
    });

    // 调用API（使用已封装的方法）
    const result = await api.learning.addQuestionToMistakes(questionId, {
      // student_answer 可选，如果有用户输入可以传递
    });

    wx.hideLoading();

    // 成功提示
    wx.showToast({
      title: '已加入错题本',
      icon: 'success',
      duration: 2000,
    });

    // 可选：更新消息状态，标记已加入错题本
    const messageList = [...this.data.messageList];
    const message = messageList.find(msg => msg.id === messageId);
    if (message) {
      message.addedToMistakes = true;
      this.setData({ messageList });
    }

    console.log('加入错题本成功:', result);

  } catch (error) {
    wx.hideLoading();

    console.error('加入错题本失败:', error);

    // 错误处理
    let errorMsg = '加入失败，请重试';

    if (error.statusCode === 409) {
      errorMsg = '该题目已在错题本中';
    } else if (error.statusCode === 404) {
      errorMsg = '题目不存在';
    } else if (error.statusCode === 401) {
      errorMsg = '请先登录';
    }

    wx.showToast({
      title: errorMsg,
      icon: 'none',
      duration: 2000,
    });
  }
},
```

**关键点**：

- 使用 `async/await` 处理异步调用
- 完整的错误处理（409/404/401 等状态码）
- 用户友好的加载和结果提示
- 可选：更新消息状态避免重复添加

---

### 任务 4：添加按钮样式（WXSS）🎨

**文件**：`miniprogram/pages/learning/index/index.wxss`

**位置**：在 `.bubble-actions` 样式区域附近

**添加内容**：

```css
/* 操作按钮 - 文本标签 */
.action-btn .action-label {
  font-size: 10px;
  margin-left: 2px;
  color: #999;
}

/* 已加入错题本状态 */
.action-btn.added-to-mistakes {
  opacity: 0.5;
  pointer-events: none;
}

.action-btn.added-to-mistakes .action-label {
  color: #1890ff;
}
```

**可选增强**：

如果需要更明显的视觉效果：

```css
/* 错题本按钮特殊样式 */
.action-btn-mistakes {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: #fff;
}

.action-btn-mistakes .action-label {
  color: #fff;
  font-weight: 500;
}
```

---

### 任务 5：数据结构适配 🔄

**问题**：需要确保消息对象包含 `questionId` 字段

**文件**：`miniprogram/pages/learning/index/index.js`

**可能需要修改的位置**：

#### 5.1 发送消息后保存 question_id

在 API 调用成功后，将返回的 `question_id` 添加到消息对象：

```javascript
// 大约在第 700-750 行，AI 回复处理部分
async sendMessage() {

  try {
    const response = await api.learning.askQuestion({
      content: this.data.inputText,
      session_id: this.data.sessionId,
      // ... other params
    });

    // 构建AI回复消息
    const aiMessage = {
      id: this.generateMessageId(),
      sender: 'ai',
      type: 'text',
      content: response.data.answer.content,
      timestamp: new Date().toLocaleTimeString(),
      questionId: response.data.question.id,  // 【关键】保存 question_id
      confidence: response.data.answer.confidence,
    };

  }
}
```

#### 5.2 从历史消息加载 question_id

如果有历史消息加载功能，也需要确保包含 `questionId`：

```javascript
// 历史消息映射
const messages = historyData.items.map((item) => ({
  id: item.id,
  sender: item.role === 'user' ? 'user' : 'ai',
  content: item.content,
  questionId: item.question_id, // 【关键】从后端数据映射
  timestamp: item.created_at,
  // ... other fields
}))
```

---

### 任务 6：测试验证 ✅

**测试环境**：微信开发者工具

**测试步骤**：

1. **基础显示测试**

   - [ ] 打开学习问答页面
   - [ ] 发送一个问题
   - [ ] 确认 AI 回复下方显示"加入错题本"按钮
   - [ ] 确认用户消息下方不显示该按钮

2. **功能测试**

   - [ ] 点击"加入错题本"按钮
   - [ ] 确认显示"加入错题本中..."加载提示
   - [ ] 确认成功后显示"已加入错题本"提示
   - [ ] 在错题本页面验证题目已添加

3. **错误处理测试**

   - [ ] 重复点击同一题目，确认提示"已在错题本中"
   - [ ] 网络断开时点击，确认错误提示友好
   - [ ] 未登录状态点击，确认跳转登录或提示

4. **UI 测试**

   - [ ] 确认按钮样式与其他操作按钮一致
   - [ ] 确认按钮大小和间距合适
   - [ ] 确认文字和图标清晰可读

5. **性能测试**
   - [ ] 快速连续点击不会重复调用 API
   - [ ] 加载状态正确显示和隐藏
   - [ ] 页面滚动流畅，无卡顿

---

## 🔗 相关资源

### API 文档

**后端端点**：

```
POST /api/v1/learning/questions/{question_id}/add-to-mistakes
Query参数：student_answer (可选)
```

**小程序 API 封装**（已完成）：

```javascript
// miniprogram/api/learning.js
api.learning.addQuestionToMistakes(questionId, {
  student_answer: '...', // 可选
})
```

### 相关文件

**后端**：

- `/src/api/v1/endpoints/learning.py` - API 端点实现
- `/src/services/learning_service.py` - 业务逻辑
- `/src/models/study.py` - 错题记录模型

**前端**：

- `/miniprogram/pages/learning/index/index.wxml` - 页面结构
- `/miniprogram/pages/learning/index/index.js` - 页面逻辑
- `/miniprogram/pages/learning/index/index.wxss` - 页面样式
- `/miniprogram/api/learning.js` - API 封装

---

## 📌 注意事项

1. **数据结构一致性**

   - 确保消息对象包含 `questionId` 字段
   - 后端返回的 `question.id` 要正确映射到前端

2. **用户体验**

   - 添加防抖处理，避免重复点击
   - 成功后可以在按钮上显示"已添加"状态
   - 错误提示要友好明确

3. **错误处理**

   - 网络错误：提示用户检查网络
   - 409 冲突：提示已在错题本中
   - 404 错误：提示题目不存在
   - 401 未授权：引导用户登录

4. **性能优化**
   - API 调用添加超时处理
   - 考虑添加本地缓存，标记已添加的题目
   - 避免在列表渲染中进行复杂计算

---

## 🚀 下一步计划

完成前端 UI 集成后，可以考虑以下增强功能：

1. **批量添加**：选择多个题目一次性加入错题本
2. **智能推荐**：AI 自动识别错题并推荐加入
3. **学习轨迹**：记录从学习到复习的完整路径
4. **数据统计**：展示从问答到错题的转化率

---

**文档版本**：v1.0  
**创建日期**：2025-10-20  
**更新日期**：2025-10-20  
**状态**：待开发

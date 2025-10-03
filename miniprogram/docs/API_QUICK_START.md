# API 快速使用指南

> **五好伴学微信小程序 - API 快速上手文档**
>
> 5 分钟快速掌握小程序 API 的使用方法

**版本**: v1.0.0
**更新时间**: 2025-01-15

---

## 🚀 快速开始

### 1. 引入 API 模块

在页面 JS 文件顶部引入：

```javascript
// pages/xxx/index.js
const api = require('../../api/index.js');

Page({
  async onLoad() {
    // 现在可以使用 API 了
    const result = await api.learning.askQuestion({ ... });
  }
});
```

### 2. 三个主要 API 模块

```javascript
api.homework   // 作业批改模块
api.learning   // 学习问答模块
api.analysis   // 学情分析模块
```

---

## 📚 常用场景

### 场景 1: 学习问答

```javascript
// 向 AI 提问
const response = await api.learning.askQuestion({
  question: '什么是二次函数？',
  subject: 'math',
});

if (response.success) {
  console.log('AI 回答:', response.data.answer);
}
```

### 场景 2: 提交作业

```javascript
// 提交图片作业
const result = await api.homework.submitHomeworkImage({
  template_id: 'template-uuid',
  student_name: '张小明',
  filePath: 'wxfile://temp/image.jpg',
  onProgress: (progress) => {
    console.log('上传进度:', progress.progress + '%');
  },
});

// 获取批改结果
const correction = await api.homework.getCorrectionResult(
  result.data.id
);
```

### 场景 3: 查看学习报告

```javascript
// 获取学情分析数据
const analytics = await api.analysis.getAnalytics({
  days: 30, // 最近 30 天
});

if (analytics.success) {
  const data = analytics.data;
  console.log('学习会话数:', data.total_sessions);
  console.log('总提问数:', data.total_questions);
  console.log('平均评分:', data.avg_rating);
}
```

### 场景 4: 管理学习目标

```javascript
// 创建学习目标
const goal = await api.analysis.createGoal({
  title: '每天学习1小时',
  description: '坚持每天学习数学1小时',
  target_date: '2025-02-15',
  subject: 'math',
});

// 更新目标进度
await api.analysis.updateGoalProgress(goal.data.id, {
  progress: 50, // 50%
  note: '已完成15天',
});
```

---

## ⚡ 实用技巧

### 技巧 1: 统一错误处理

```javascript
async loadData() {
  try {
    const result = await api.learning.askQuestion({ ... });

    if (result.success) {
      // 成功处理
      this.setData({ data: result.data });
    } else {
      // 业务错误
      wx.showToast({
        title: result.error.message,
        icon: 'none',
      });
    }
  } catch (error) {
    // 网络错误等异常
    console.error('请求失败:', error);

    // 根据错误类型处理
    if (error.code === 'AUTH_ERROR') {
      wx.navigateTo({ url: '/pages/login/index' });
    } else {
      wx.showToast({
        title: error.message || '操作失败',
        icon: 'error',
      });
    }
  }
}
```

### 技巧 2: 加载状态管理

```javascript
Page({
  data: {
    loading: false,
  },

  async loadData() {
    this.setData({ loading: true });

    try {
      const result = await api.analysis.getAnalytics({ days: 30 });
      this.setData({ analytics: result.data });
    } finally {
      this.setData({ loading: false });
    }
  }
});
```

### 技巧 3: 自定义请求配置

```javascript
// 禁用加载提示
await api.learning.askQuestion(params, {
  showLoading: false,
});

// 自定义超时时间
await api.learning.askQuestion(params, {
  timeout: 60000, // 60 秒
});

// 增加重试次数
await api.homework.submitHomeworkImage(params, {
  retryCount: 3,
});
```

### 技巧 4: 分页加载

```javascript
Page({
  data: {
    list: [],
    page: 1,
    hasMore: true,
  },

  async loadMore() {
    if (!this.data.hasMore) return;

    const result = await api.learning.getQuestions({
      page: this.data.page,
      size: 10,
    });

    if (result.success) {
      this.setData({
        list: [...this.data.list, ...result.data],
        page: this.data.page + 1,
        hasMore: result.data.length >= 10,
      });
    }
  },

  // 触底加载
  onReachBottom() {
    this.loadMore();
  }
});
```

---

## 📖 API 速查表

### 学习问答 API

| 方法 | 功能 | 示例 |
|------|------|------|
| `askQuestion()` | AI 提问 | `api.learning.askQuestion({ question: '...' })` |
| `getSessions()` | 获取会话列表 | `api.learning.getSessions({ page: 1 })` |
| `favoriteQuestion()` | 收藏问题 | `api.learning.favoriteQuestion(questionId)` |
| `searchQuestions()` | 搜索问题 | `api.learning.searchQuestions({ q: '二次函数' })` |
| `uploadQuestionImage()` | 上传图片 | `api.learning.uploadQuestionImage(filePath)` |

### 学情分析 API

| 方法 | 功能 | 示例 |
|------|------|------|
| `getAnalytics()` | 综合分析 | `api.analysis.getAnalytics({ days: 30 })` |
| `getProgress()` | 学习进度 | `api.analysis.getProgress({ days: 7 })` |
| `getGoals()` | 学习目标 | `api.analysis.getGoals({ status: 'active' })` |
| `createGoal()` | 创建目标 | `api.analysis.createGoal({ title: '...' })` |
| `getTrends()` | 学习趋势 | `api.analysis.getTrends({ metric: 'score' })` |

### 作业批改 API

| 方法 | 功能 | 示例 |
|------|------|------|
| `getTemplates()` | 作业模板 | `api.homework.getTemplates({ page: 1 })` |
| `submitHomeworkImage()` | 提交图片 | `api.homework.submitHomeworkImage({ ... })` |
| `getSubmissions()` | 提交列表 | `api.homework.getSubmissions({ page: 1 })` |
| `getCorrectionResult()` | 批改结果 | `api.homework.getCorrectionResult(id)` |
| `pollCorrectionResult()` | 轮询结果 | `api.homework.pollCorrectionResult(id)` |

---

## ❓ 常见问题

### Q1: 如何判断 API 调用成功？

```javascript
const result = await api.learning.askQuestion({ ... });

if (result.success) {
  // 成功：result.data 包含返回数据
  console.log(result.data);
} else {
  // 失败：result.error 包含错误信息
  console.log(result.error.message);
}
```

### Q2: 如何处理网络错误？

```javascript
try {
  const result = await api.learning.askQuestion({ ... });
} catch (error) {
  // error.code 是错误代码
  // error.message 是错误描述

  if (error.code === 'NETWORK_ERROR') {
    wx.showToast({ title: '网络连接失败' });
  } else if (error.code === 'TIMEOUT_ERROR') {
    wx.showToast({ title: '请求超时' });
  }
}
```

### Q3: 如何上传多张图片？

```javascript
// 方法 1: 批量上传
const result = await api.learning.uploadQuestionImages([
  'path1.jpg',
  'path2.jpg',
  'path3.jpg',
]);

// 方法 2: 逐个上传
for (const path of imagePaths) {
  const result = await api.learning.uploadQuestionImage(path);
  console.log('上传成功:', result.data.url);
}
```

### Q4: 如何实现下拉刷新？

```javascript
Page({
  async onPullDownRefresh() {
    try {
      await this.loadData();
      wx.showToast({ title: '刷新成功', icon: 'success' });
    } finally {
      wx.stopPullDownRefresh();
    }
  },

  async loadData() {
    const result = await api.analysis.getAnalytics({ days: 30 });
    this.setData({ data: result.data });
  }
});
```

### Q5: 如何实现数据缓存？

```javascript
async loadData(forceRefresh = false) {
  // 检查缓存
  if (!forceRefresh) {
    const cached = wx.getStorageSync('data_cache');
    if (cached && Date.now() - cached.timestamp < 300000) {
      // 5 分钟内使用缓存
      this.setData({ data: cached.data });
      return;
    }
  }

  // 加载新数据
  const result = await api.analysis.getAnalytics({ days: 30 });

  // 保存缓存
  wx.setStorageSync('data_cache', {
    data: result.data,
    timestamp: Date.now(),
  });

  this.setData({ data: result.data });
}
```

---

## 🔗 更多资源

- **详细文档**: [API 集成指南](./API_INTEGRATION_GUIDE.md)
- **完整示例**: [API_INTEGRATION_GUIDE.md#使用示例](./API_INTEGRATION_GUIDE.md#使用示例)
- **后端 API**: [后端 API 文档](../../docs/api/endpoints.md)
- **项目文档**: [README.md](../../README.md)

---

## 💡 最佳实践

1. ✅ **始终使用 try-catch 包裹 API 调用**
2. ✅ **检查 result.success 判断成功或失败**
3. ✅ **使用 loading 状态提升用户体验**
4. ✅ **合理使用缓存减少网络请求**
5. ✅ **提供友好的错误提示**
6. ✅ **避免在循环中频繁调用 API**
7. ✅ **使用分页加载处理大量数据**
8. ✅ **及时释放资源和监听器**

---

**更新日志**:
- `2025-01-15`: 初始版本，包含三大 API 模块快速指南

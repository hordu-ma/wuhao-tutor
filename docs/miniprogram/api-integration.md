# 小程序 API 集成指南

> **五好伴学微信小程序 - 前后端 API 集成说明文档**
>
> 本文档说明小程序如何调用后端 API，以及网络请求的最佳实践。

**最后更新**: 2025-01-15
**版本**: v2.0.0

---

## 📋 目录

- [快速开始](#快速开始)
- [网络请求封装](#网络请求封装)
- [API 模块说明](#api-模块说明)
  - [作业批改 API](#作业批改-api)
  - [学习问答 API](#学习问答-api)
  - [学情分析 API](#学情分析-api)
- [使用示例](#使用示例)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 配置后端地址

编辑 `config/index.js` 文件，设置后端 API 地址：

```javascript
const config = {
  api: {
    // 开发环境使用本地后端
    baseUrl: 'http://localhost:8000',
    version: 'v1',
    timeout: 10000,
  },
}
```

**注意事项**：

- 开发环境使用 `http://localhost:8000`
- 生产环境使用 `https://www.horsduroot.com`
- 微信小程序要求生产环境必须使用 HTTPS

### 2. 引入 API 模块

```javascript
// 推荐：引入所有 API 模块
const api = require('../../api/index.js')

// 使用时：
api.homework.getTemplates() // 作业批改
api.learning.askQuestion() // 学习问答
api.analysis.getAnalytics() // 学情分析
```

### 3. 调用 API

```javascript
// 获取作业模板列表
const response = await api.homework.getTemplates({
  page: 1,
  size: 10,
})

if (response.success) {
  console.log('数据:', response.data)
} else {
  console.error('错误:', response.error)
}
```

---

## 🔧 网络请求封装

### Request 类

`utils/request.js` 提供了统一的网络请求封装，包含以下特性：

#### 核心功能

- ✅ **自动添加认证 Token**：无需手动处理
- ✅ **统一错误处理**：自动识别和处理各类错误
- ✅ **请求去重**：防止重复请求
- ✅ **网络状态检测**：自动检查网络连接
- ✅ **自动重试**：网络错误时自动重试
- ✅ **上传进度**：文件上传支持进度回调
- ✅ **加载提示**：可配置的加载动画

#### 配置选项

```javascript
{
  url: 'homework/submit',         // 请求路径（自动拼接 baseUrl）
  method: 'POST',                 // 请求方法
  data: { ... },                  // 请求数据
  header: { ... },                // 自定义请求头
  timeout: 10000,                 // 超时时间（毫秒）
  skipAuth: false,                // 是否跳过认证
  showLoading: true,              // 是否显示加载提示
  loadingText: '加载中...',       // 加载提示文字
  showError: true,                // 是否显示错误提示
  retryCount: 2,                  // 重试次数
  retryDelay: 1000,               // 重试延迟（毫秒）
}
```

#### 请求方法

```javascript
const { request } = require('../utils/request.js')

// GET 请求
request.get(url, params, config)

// POST 请求
request.post(url, data, config)

// PUT 请求
request.put(url, data, config)

// DELETE 请求
request.delete(url, params, config)

// 文件上传
request.upload(url, filePath, name, formData, config)
```

---

## 📦 API 模块说明

本项目包含三个主要 API 模块：

1. **作业批改 API** (`api/homework.js`) - 作业提交、批改、结果查询
2. **学习问答 API** (`api/learning.js`) - AI 问答、会话管理、问题收藏
3. **学情分析 API** (`api/analysis.js`) - 学习数据分析、进度跟踪、目标管理

---

### 作业批改 API (`api/homework.js`)

#### 1. 获取作业模板列表

```javascript
homeworkAPI.getTemplates({
  page: 1,
  size: 10,
  subject: 'math', // 可选：学科筛选
})
```

**返回数据**：

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "模板名称",
      "subject": "math",
      "description": "模板描述",
      "max_score": 100
    }
  ],
  "message": "获取成功"
}
```

#### 2. 获取作业模板详情

```javascript
homeworkAPI.getTemplateDetail(templateId)
```

#### 3. 提交作业（文本）

```javascript
homeworkAPI.submitHomeworkText({
  template_id: 'uuid',
  student_name: '张小明',
  content: '作业内容...',
  additional_info: '备注信息', // 可选
})
```

#### 4. 提交作业（图片）

```javascript
homeworkAPI.submitHomeworkImage({
  template_id: 'uuid',
  student_name: '张小明',
  filePath: 'wxfile://temp/image.jpg',
  additional_info: '备注信息', // 可选
  onProgress: (progress) => {
    console.log('上传进度:', progress.progress)
  },
})
```

#### 5. 批量提交作业图片

```javascript
homeworkAPI.submitHomeworkImages({
  template_id: 'uuid',
  student_name: '张小明',
  filePaths: ['path1.jpg', 'path2.jpg'],
  onProgress: (progress) => {
    console.log('总进度:', progress.totalProgress)
    console.log('当前:', progress.current, '/', progress.total)
  },
})
```

#### 6. 获取提交列表

```javascript
homeworkAPI.getSubmissions({
  page: 1,
  size: 10,
  template_id: 'uuid', // 可选：按模板筛选
  status: 'completed', // 可选：按状态筛选
})
```

**状态值**：

- `pending` - 等待批改
- `processing` - 批改中
- `completed` - 已完成
- `failed` - 批改失败

#### 7. 获取提交详情

```javascript
homeworkAPI.getSubmissionDetail(submissionId)
```

#### 8. 获取批改结果

```javascript
homeworkAPI.getCorrectionResult(submissionId)
```

**返回数据**：

```json
{
  "success": true,
  "data": {
    "submission_id": "uuid",
    "total_score": 85,
    "max_score": 100,
    "overall_comment": "整体评价...",
    "detailed_feedback": [
      {
        "question_number": 1,
        "score": 10,
        "max_score": 10,
        "comment": "答案正确"
      }
    ],
    "suggestions": ["建议1", "建议2"],
    "corrected_at": "2025-01-15T10:30:00Z"
  }
}
```

#### 9. 轮询批改结果

```javascript
homeworkAPI.pollCorrectionResult(submissionId, {
  interval: 3000, // 轮询间隔（毫秒）
  maxAttempts: 20, // 最大尝试次数
  onProgress: (info) => {
    console.log('轮询进度:', info.attempts, '/', info.maxAttempts)
    console.log('当前状态:', info.status)
  },
})
```

---

### 学习问答 API (`api/learning.js`)

#### 1. 向 AI 提问

```javascript
api.learning.askQuestion({
  question: '什么是二次函数？',
  session_id: 'optional-session-id', // 可选：关联到已有会话
  subject: 'math', // 可选：学科
  grade: '初中', // 可选：年级
})
```

**返回数据**：

```json
{
  "success": true,
  "data": {
    "question_id": "uuid",
    "session_id": "uuid",
    "question": "什么是二次函数？",
    "answer": "二次函数是形如 y=ax²+bx+c 的函数...",
    "confidence": 0.95,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### 2. 创建和管理会话

```javascript
// 创建会话
const session = await api.learning.createSession({
  title: '数学学习',
  subject: 'math',
  grade: '初中',
})

// 获取会话列表
const sessions = await api.learning.getSessions({
  page: 1,
  size: 10,
  status: 'active', // active/archived
})

// 获取会话详情
const detail = await api.learning.getSessionDetail(sessionId)

// 更新会话
await api.learning.updateSession(sessionId, {
  title: '新标题',
  status: 'archived',
})

// 删除会话
await api.learning.deleteSession(sessionId)
```

#### 3. 问题管理

```javascript
// 获取问题列表
const questions = await api.learning.getQuestions({
  page: 1,
  size: 10,
  session_id: 'uuid', // 可选：按会话筛选
  subject: 'math', // 可选：按学科筛选
})

// 获取问题详情
const question = await api.learning.getQuestionDetail(questionId)

// 搜索问题
const results = await api.learning.searchQuestions({
  q: '二次函数',
  subject: 'math',
  limit: 20,
})
```

#### 4. 答案评价和收藏

```javascript
// 评价答案（点赞/点踩）
await api.learning.rateAnswer(questionId, {
  helpful: true,
  feedback: '回答很清楚',
})

// 收藏问题
await api.learning.favoriteQuestion(questionId)

// 取消收藏
await api.learning.unfavoriteQuestion(questionId)

// 获取收藏列表
const favorites = await api.learning.getFavorites({
  page: 1,
  size: 10,
})
```

#### 5. 图片上传提问

```javascript
// 单张图片上传
const uploadResult = await api.learning.uploadQuestionImage('wxfile://temp/image.jpg')

// 批量上传
const batchResult = await api.learning.uploadQuestionImages(['path1.jpg', 'path2.jpg', 'path3.jpg'])

// 使用上传的图片提问
if (uploadResult.success) {
  await api.learning.askQuestion({
    question: '这道题怎么做？',
    image_urls: [uploadResult.data.url],
  })
}
```

#### 6. 推荐和热门问题

```javascript
// 获取推荐问题
const recommended = await api.learning.getRecommendedQuestions({
  subject: 'math',
  grade: '初中',
  limit: 5,
})

// 获取热门问题
const popular = await api.learning.getPopularQuestions({
  subject: 'math',
  days: 7,
  limit: 10,
})

// 获取相似问题
const similar = await api.learning.getSimilarQuestions(questionId, {
  limit: 5,
})
```

---

### 学情分析 API (`api/analysis.js`)

#### 1. 获取学情总览

```javascript
// 获取综合分析数据（用于报告页面）
const analytics = await api.analysis.getAnalytics({
  days: 30, // 最近 30 天
})
```

**返回数据**：

```json
{
  "success": true,
  "data": {
    "total_sessions": 15,
    "total_questions": 45,
    "avg_rating": 4.5,
    "positive_rate": 0.89,
    "subject_stats": [
      { "subject": "math", "count": 20, "avg_rating": 4.6 },
      { "subject": "english", "count": 15, "avg_rating": 4.3 }
    ],
    "knowledge_mastery": [
      { "name": "二次函数", "mastery": 0.85 },
      { "name": "三角函数", "mastery": 0.72 }
    ],
    "learning_patterns": {
      "most_active_hour": 19,
      "most_active_weekday": 3,
      "avg_session_duration": 1200
    }
  }
}
```

#### 2. 学习进度和历史

```javascript
// 获取学习进度
const progress = await api.analysis.getProgress({
  days: 7,
})

// 获取学习历史记录
const history = await api.analysis.getHistory({
  page: 1,
  size: 20,
  type: 'homework', // homework/question/achievement
  days: 90,
})
```

#### 3. 数据分析

```javascript
// 获取活跃度分布
const activity = await api.analysis.getActivity({
  days: 30,
  granularity: 'day', // hour/day/week/month
})

// 获取知识点掌握情况
const mastery = await api.analysis.getMastery({
  subject: 'math',
})

// 获取学习趋势
const trends = await api.analysis.getTrends({
  metric: 'score', // score/frequency/duration/mastery
  days: 30,
  subject: 'math',
})

// 获取学科统计
const subjectStats = await api.analysis.getSubjectStats({
  days: 30,
})

// 获取学习模式分析
const patterns = await api.analysis.getLearningPatterns({
  days: 30,
})
```

#### 4. 学习建议和改进

```javascript
// 获取个性化学习建议
const recommendations = await api.analysis.getRecommendations({
  subject: 'math',
  focus: 'weak', // weak/strong/balanced
})

// 获取改进建议
const improvements = await api.analysis.getImprovements({
  subject: 'math',
  priority: 'high', // high/medium/low
})

// 获取知识缺口分析
const gaps = await api.analysis.getKnowledgeGaps({
  subject: 'math',
  threshold: 0.6, // 掌握度低于 60% 视为缺口
})

// 获取 AI 生成的学习洞察
const insights = await api.analysis.getInsights({
  days: 30,
})
```

#### 5. 学习目标管理

```javascript
// 获取学习目标列表
const goals = await api.analysis.getGoals({
  status: 'active', // active/completed/overdue
})

// 创建学习目标
const newGoal = await api.analysis.createGoal({
  title: '每天学习1小时',
  description: '坚持每天学习数学1小时',
  target_date: '2025-02-15',
  subject: 'math',
  target_value: 30,
})

// 更新学习目标
await api.analysis.updateGoal(goalId, {
  title: '新标题',
  progress: 50,
  status: 'active',
})

// 更新目标进度
await api.analysis.updateGoalProgress(goalId, {
  progress: 50, // 50%
  note: '已完成15天',
})

// 删除学习目标
await api.analysis.deleteGoal(goalId)
```

#### 6. 高级功能

```javascript
// 生成学习报告
const report = await api.analysis.generateReport({
  days: 30,
  format: 'json', // json/pdf
})

// 获取学习排名
const ranking = await api.analysis.getRanking({
  scope: 'class', // class/grade/school
  metric: 'score', // score/frequency/improvement
  days: 30,
})

// 获取成就徽章
const achievements = await api.analysis.getAchievements()
```

---

## 💡 使用示例

### 示例 1: 学习问答完整流程

```javascript
Page({
  data: {
    sessionId: null,
    messages: [],
  },

  async onLoad() {
    // 1. 创建或加载会话
    await this.initSession()
  },

  async initSession() {
    try {
      // 尝试加载最近的会话
      const sessions = await api.learning.getSessions({
        page: 1,
        size: 1,
        status: 'active',
      })

      if (sessions.success && sessions.data.length > 0) {
        this.setData({ sessionId: sessions.data[0].id })
      } else {
        // 创建新会话
        const newSession = await api.learning.createSession({
          title: '数学学习',
          subject: 'math',
        })
        this.setData({ sessionId: newSession.data.id })
      }
    } catch (error) {
      console.error('会话初始化失败:', error)
    }
  },

  async askQuestion() {
    const question = this.data.inputText.trim()
    if (!question) return

    try {
      // 2. 向 AI 提问
      const response = await api.learning.askQuestion({
        question: question,
        session_id: this.data.sessionId,
        subject: 'math',
      })

      if (response.success) {
        // 3. 显示答案
        const messages = [
          ...this.data.messages,
          {
            type: 'user',
            content: question,
          },
          {
            type: 'ai',
            content: response.data.answer,
            questionId: response.data.question_id,
          },
        ]

        this.setData({ messages, inputText: '' })
      }
    } catch (error) {
      wx.showToast({
        title: error.message || '提问失败',
        icon: 'error',
      })
    }
  },

  async onLikeAnswer(e) {
    const { questionId } = e.currentTarget.dataset

    try {
      // 4. 评价答案
      await api.learning.rateAnswer(questionId, {
        helpful: true,
        feedback: '回答很有帮助',
      })

      wx.showToast({
        title: '感谢反馈',
        icon: 'success',
      })
    } catch (error) {
      console.error('评价失败:', error)
    }
  },

  async onFavorite(e) {
    const { questionId } = e.currentTarget.dataset

    try {
      // 5. 收藏问题
      await api.learning.favoriteQuestion(questionId)

      wx.showToast({
        title: '已收藏',
        icon: 'success',
      })
    } catch (error) {
      console.error('收藏失败:', error)
    }
  },
})
```

### 示例 2: 提交作业完整流程

```javascript
Page({
  data: {
    templateId: '',
    imageList: [],
  },

  // 选择图片
  async chooseImage() {
    const res = await wx.chooseMedia({
      count: 9,
      mediaType: ['image'],
    })

    this.setData({
      imageList: res.tempFiles.map((f) => f.tempFilePath),
    })
  },

  // 提交作业
  async submitHomework() {
    try {
      const { templateId, imageList } = this.data
      const userInfo = await auth.getUserInfo()

      // 提交第一张图片
      const result = await homeworkAPI.submitHomeworkImage({
        template_id: templateId,
        student_name: userInfo.name,
        filePath: imageList[0],
        onProgress: (progress) => {
          console.log('上传进度:', progress.progress + '%')
        },
      })

      if (result.success) {
        const submissionId = result.data.id

        // 跳转到详情页
        wx.navigateTo({
          url: `/pages/homework/detail/index?id=${submissionId}`,
        })

        // 后台继续上传剩余图片
        if (imageList.length > 1) {
          homeworkAPI
            .submitHomeworkImages({
              template_id: templateId,
              student_name: userInfo.name,
              filePaths: imageList.slice(1),
            })
            .catch((err) => {
              console.error('批量上传失败:', err)
            })
        }
      }
    } catch (error) {
      wx.showToast({
        title: error.message || '提交失败',
        icon: 'error',
      })
    }
  },
})
```

### 示例 3: 学情分析页面加载

```javascript
Page({
  data: {
    submissionId: '',
    correction: null,
  },

  async onLoad(options) {
    this.setData({ submissionId: options.id })
    await this.loadSubmission()
  },

  async loadSubmission() {
    try {
      // 获取提交详情
      const detail = await homeworkAPI.getSubmissionDetail(this.data.submissionId)

      if (detail.data.status === 'completed') {
        // 批改已完成，直接获取结果
        const correction = await homeworkAPI.getCorrectionResult(this.data.submissionId)
        this.setData({ correction: correction.data })
      } else if (detail.data.status === 'processing') {
        // 批改进行中，启动轮询
        this.startPolling()
      }
    } catch (error) {
      console.error('加载失败:', error)
    }
  },

  async startPolling() {
    try {
      const correction = await homeworkAPI.pollCorrectionResult(this.data.submissionId, {
        interval: 3000,
        maxAttempts: 20,
        onProgress: (info) => {
          console.log(`轮询中 ${info.attempts}/${info.maxAttempts}`)
        },
      })

      this.setData({ correction: correction.data })

      wx.showToast({
        title: '批改完成',
        icon: 'success',
      })
    } catch (error) {
      wx.showToast({
        title: '获取批改结果失败',
        icon: 'error',
      })
    }
  },
})
```

```javascript
Page({
  data: {
    loading: false,
    analytics: null,
    timeRange: 30,
  },

  async onLoad() {
    await this.loadAnalytics()
  },

  async loadAnalytics() {
    this.setData({ loading: true })

    try {
      // 1. 获取综合分析数据
      const analytics = await api.analysis.getAnalytics({
        days: this.data.timeRange,
      })

      if (analytics.success) {
        this.setData({ analytics: analytics.data })

        // 2. 渲染图表
        this.renderCharts(analytics.data)
      }
    } catch (error) {
      // 尝试使用缓存数据
      const cached = wx.getStorageSync('analytics_cache')
      if (cached) {
        this.setData({ analytics: cached })
        this.renderCharts(cached)
      } else {
        wx.showToast({
          title: '加载失败',
          icon: 'error',
        })
      }
    } finally {
      this.setData({ loading: false })
    }
  },

  renderCharts(data) {
    // 渲染学科统计图表
    this.renderSubjectChart(data.subject_stats)

    // 渲染知识掌握雷达图
    this.renderMasteryChart(data.knowledge_mastery)
  },

  async onTimeRangeChange(e) {
    const timeRange = e.detail.value
    this.setData({ timeRange })
    await this.loadAnalytics()
  },
})
```

### 示例 4: 学习目标管理

```javascript
Page({
  data: {
    goals: [],
  },

  async onLoad() {
    await this.loadGoals()
  },

  async loadGoals() {
    try {
      const response = await api.analysis.getGoals({
        status: 'active',
      })

      if (response.success) {
        this.setData({ goals: response.data })
      }
    } catch (error) {
      console.error('加载目标失败:', error)
    }
  },

  async onCreateGoal() {
    try {
      const newGoal = await api.analysis.createGoal({
        title: this.data.goalTitle,
        description: this.data.goalDesc,
        target_date: this.data.targetDate,
        subject: 'math',
        target_value: 30,
      })

      if (newGoal.success) {
        wx.showToast({
          title: '目标创建成功',
          icon: 'success',
        })

        await this.loadGoals()
      }
    } catch (error) {
      wx.showToast({
        title: error.message || '创建失败',
        icon: 'error',
      })
    }
  },

  async onUpdateProgress(e) {
    const { goalId, progress } = e.currentTarget.dataset

    try {
      await api.analysis.updateGoalProgress(goalId, {
        progress: progress,
        note: `更新进度到 ${progress}%`,
      })

      wx.showToast({
        title: '进度已更新',
        icon: 'success',
      })

      await this.loadGoals()
    } catch (error) {
      console.error('更新进度失败:', error)
    }
  },
})
```

### 示例 5: 列表加载与分页

```javascript
Page({
  data: {
    submissions: [],
    page: 1,
    hasMore: true,
    loading: false,
  },

  async loadSubmissions() {
    if (this.data.loading || !this.data.hasMore) return

    this.setData({ loading: true })

    try {
      const response = await homeworkAPI.getSubmissions({
        page: this.data.page,
        size: 10,
      })

      const newSubmissions = response.data || []
      const hasMore = newSubmissions.length >= 10

      this.setData({
        submissions: [...this.data.submissions, ...newSubmissions],
        page: this.data.page + 1,
        hasMore,
      })
    } catch (error) {
      wx.showToast({
        title: '加载失败',
        icon: 'error',
      })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 下拉刷新
  async onPullDownRefresh() {
    this.setData({
      submissions: [],
      page: 1,
      hasMore: true,
    })

    await this.loadSubmissions()
    wx.stopPullDownRefresh()
  },

  // 触底加载更多
  onReachBottom() {
    this.loadSubmissions()
  },
})
```

---

## ⚠️ 错误处理

### 错误类型

```javascript
{
  code: 'ERROR_CODE',      // 错误代码
  message: '错误描述',      // 用户友好的错误消息
  details: { ... },        // 详细错误信息（可选）
}
```

### 常见错误码

| 错误码             | 说明            | 处理建议         |
| ------------------ | --------------- | ---------------- |
| `NETWORK_ERROR`    | 网络连接失败    | 提示用户检查网络 |
| `TIMEOUT_ERROR`    | 请求超时        | 重试或提示用户   |
| `AUTH_ERROR`       | 认证失败        | 跳转到登录页     |
| `PERMISSION_ERROR` | 权限不足        | 提示用户权限不足 |
| `VALIDATION_ERROR` | 参数验证失败    | 检查请求参数     |
| `BUSINESS_ERROR`   | 业务逻辑错误    | 显示错误消息     |
| `HTTP_4XX`         | HTTP 客户端错误 | 根据状态码处理   |
| `HTTP_5XX`         | HTTP 服务器错误 | 提示稍后重试     |

### 错误处理示例

```javascript
try {
  const result = await homeworkAPI.submitHomeworkImage({ ... });

  if (result.success) {
    // 处理成功结果
  } else {
    // 业务错误
    wx.showToast({
      title: result.error.message || '操作失败',
      icon: 'error',
    });
  }
} catch (error) {
  // 网络错误或其他异常
  console.error('请求失败:', error);

  if (error.code === 'AUTH_ERROR') {
    // 认证失败，跳转登录
    wx.navigateTo({
      url: '/pages/login/index',
    });
  } else if (error.code === 'NETWORK_ERROR') {
    // 网络错误
    wx.showModal({
      title: '网络错误',
      content: '请检查网络连接后重试',
      showCancel: false,
    });
  } else {
    // 其他错误
    wx.showToast({
      title: error.message || '操作失败',
      icon: 'error',
    });
  }
}
```

---

## 🎯 最佳实践

### 1. 使用 async/await

```javascript
// ✅ 推荐
async loadData() {
  try {
    const result = await homeworkAPI.getTemplates();
    this.setData({ templates: result.data });
  } catch (error) {
    console.error(error);
  }
}

// ❌ 不推荐
loadData() {
  homeworkAPI.getTemplates().then(result => {
    this.setData({ templates: result.data });
  }).catch(error => {
    console.error(error);
  });
}
```

### 2. 统一错误处理

```javascript
// 在页面基类或工具函数中封装
handleApiError(error) {
  const errorMap = {
    'AUTH_ERROR': () => wx.navigateTo({ url: '/pages/login/index' }),
    'NETWORK_ERROR': () => wx.showToast({ title: '网络错误', icon: 'none' }),
  };

  const handler = errorMap[error.code] || (() => {
    wx.showToast({ title: error.message || '操作失败', icon: 'error' });
  });

  handler();
}
```

### 3. 请求防抖

```javascript
// 防止重复提交
data: {
  submitting: false,
},

async submitHomework() {
  if (this.data.submitting) return;

  this.setData({ submitting: true });

  try {
    await homeworkAPI.submitHomeworkImage({ ... });
  } finally {
    this.setData({ submitting: false });
  }
}
```

### 4. 加载状态管理

```javascript
data: {
  loading: false,
},

async loadData() {
  this.setData({ loading: true });

  try {
    const result = await homeworkAPI.getTemplates();
    this.setData({ templates: result.data });
  } finally {
    this.setData({ loading: false });
  }
}
```

### 5. 缓存策略

```javascript
// 使用本地缓存减少请求
async loadTemplates(forceRefresh = false) {
  if (!forceRefresh) {
    const cached = wx.getStorageSync('homework_templates');
    if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
      this.setData({ templates: cached.data });
      return;
    }
  }

  const result = await homeworkAPI.getTemplates();

  wx.setStorageSync('homework_templates', {
    data: result.data,
    timestamp: Date.now(),
  });

  this.setData({ templates: result.data });
}
```

---

## ❓ 常见问题

### Q1: 为什么请求返回 401 未授权？

**A**: 检查以下几点：

1. 用户是否已登录？调用 `auth.isAuthenticated()` 检查
2. Token 是否过期？登录超过有效期需要重新登录
3. 是否设置了 `skipAuth: true`？

### Q2: 图片上传失败怎么办？

**A**: 检查：

1. 文件大小是否超过 10MB？
2. 文件类型是否支持（JPG/PNG/WebP/PDF）？
3. 网络连接是否正常？
4. 后端上传接口是否正常？

### Q3: 批改结果一直获取不到？

**A**: 可能原因：

1. 批改还在进行中，使用 `pollCorrectionResult` 轮询
2. 批改失败，检查提交状态是否为 `failed`
3. 网络问题导致请求失败

### Q4: 如何调试网络请求？

**A**: 调试方法：

1. 开启微信开发者工具的网络面板
2. 查看 `console.log` 输出的请求信息
3. 使用 `request.getStats()` 查看请求统计
4. 后端日志查看请求详情

### Q5: 生产环境如何配置？

**A**: 修改 `config/index.js`：

```javascript
const config = {
  environment: 'production',
  api: {
    baseUrl: 'https://api.your-domain.com', // 使用 HTTPS
    version: 'v1',
    timeout: 10000,
  },
}
```

---

## 📞 支持与反馈

- **技术支持**: 查看 `miniprogram/README.md`
- **Bug 反馈**: 创建 GitHub Issue
- **功能建议**: 提交 Pull Request

---

**更新日志**:

- `2025-01-15`: 初始版本，包含作业批改 API 集成说明

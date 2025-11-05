# 首页 API 响应格式修复

## 问题诊断

### 控制台错误分析

从截图观察到的问题：

1. ⚠️ [统计数据] API 返回格式异常，使用默认值
2. ❌ [加载用户信息错误] Failed to load image (头像加载失败)
3. 三个统计数字显示为 0（累计问答、作业批改、学习时长）

### 根本原因

**API 响应格式理解错误**：

微信小程序 `wx.request()` 的响应格式：

```javascript
{
  data: {...},        // 服务器返回的实际数据
  statusCode: 200,
  header: {...}
}
```

后端 API 返回的数据结构：

```javascript
{
  success: true,
  data: {
    question_count: 0,
    homework_count: 0,
    study_hours: 0
  },
  message: "获取成功"
}
```

**错误的代码**检查了 `response.success`，但实际上后端响应在 `response.data` 中：

```javascript
// ❌ 错误：直接检查 response.success
if (response && response.success && response.data) {
  // 这里永远不会执行
}
```

**正确的访问路径**应该是 `response.data.success` 和 `response.data.data`。

### 头像问题

头像路径设置正确：

- WXML: `src="{{userInfo.avatarUrl || '/assets/images/default-avatar.png'}}"`
- auth.js: 已处理字段转换 `avatar_url -> avatarUrl`

可能原因：

1. 默认头像文件不存在：`/assets/images/default-avatar.png`
2. 服务器返回的头像 URL 格式不正确
3. 需要检查图片文件是否存在

## 修复方案

### 1. 修复 API 响应格式解析

**文件**: `miniprogram/pages/index/index.js`

**修改位置**: `loadUserStats()` 方法 (约 270-320 行)

**修改内容**:

```javascript
// 调用后端API获取真实数据
const response = await api.analysis.getUserStats()

console.log('📊 [统计数据] API响应:', response)

// ✅ 正确：微信小程序API返回格式：{ data: {...}, statusCode: 200, header: {...} }
// 后端数据在 response.data 中
if (response && response.statusCode === 200 && response.data) {
  const apiResponse = response.data

  console.log('📊 [统计数据] 后端响应:', apiResponse)

  // ✅ 后端返回格式：{ success: true, data: {...}, message: "..." }
  if (apiResponse.success && apiResponse.data) {
    const backendData = apiResponse.data

    // 映射后端字段到前端展示
    const stats = {
      questionCount: backendData.question_count || 0,
      reportCount: backendData.homework_count || 0,
      todayStudyTime: backendData.study_hours || 0,
    }

    console.log('📊 [统计数据] 设置stats:', stats)
    this.setData({ stats })
  }
}
```

### 2. 头像问题待确认

需要检查：

1. `miniprogram/assets/images/default-avatar.png` 文件是否存在
2. 如果不存在，需要添加默认头像图片
3. 或者改用微信小程序的默认图标

## 测试步骤

### 1. 重新编译测试

1. 保存修改后的文件
2. 在微信开发者工具中点击"编译"
3. 观察控制台输出

### 2. 预期结果

**控制台日志**应该显示：

```
📊 [统计数据] API响应: { data: {...}, statusCode: 200, ... }
📊 [统计数据] 后端响应: { success: true, data: {...}, ... }
📊 [统计数据] 设置stats: { questionCount: 0, reportCount: 0, todayStudyTime: 0 }
```

**页面显示**：

- 如果数据库有数据：显示实际数字
- 如果数据库无数据：显示 0 或 "待开始"
- 不应再出现"API 返回格式异常"警告

### 3. 头像测试

检查是否需要：

1. 添加默认头像文件
2. 或使用微信头像组件

## 技术说明

### 响应格式层级

```
微信小程序响应
└── data (statusCode: 200, header: {...})
    └── 后端API响应
        ├── success: true
        ├── message: "获取成功"
        └── data
            ├── question_count: 0
            ├── homework_count: 0
            └── study_hours: 0
```

### 代码访问路径

| 层级     | 访问路径                | 说明                      |
| -------- | ----------------------- | ------------------------- |
| 微信响应 | `response`              | wx.request 返回的完整响应 |
| 状态码   | `response.statusCode`   | HTTP 状态码 (200)         |
| 后端响应 | `response.data`         | 后端 API 返回的 JSON      |
| 成功标志 | `response.data.success` | 后端业务逻辑成功          |
| 实际数据 | `response.data.data`    | 统计数据对象              |

## 后续工作

1. ✅ 修复 API 响应格式解析
2. ⏸️ 检查并修复头像问题
3. ⏸️ 测试数据正常显示
4. ⏸️ 继续阶段 3：修复推荐模块

---

**创建时间**: 2025-11-05  
**状态**: 已修复 API 解析，待测试头像

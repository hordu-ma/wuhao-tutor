# 微信小程序 API 对齐修复指南

> 详细的 API 对齐修复步骤和代码示例

**生成时间**: 2025-10-04  
**问题数量**: 20 个  
**目标对齐率**: 100%

---

## 📋 目录

1. [问题概述](#问题概述)
2. [修复策略](#修复策略)
3. [详细修复步骤](#详细修复步骤)
4. [代码修改示例](#代码修改示例)
5. [测试验证](#测试验证)
6. [注意事项](#注意事项)

---

## 🔍 问题概述

### 当前状态

- **对齐率**: 35.5% (11/31)
- **问题数**: 20 个 API 调用不匹配
- **影响文件**:
  - `miniprogram/api/analysis.js` (17 个问题)
  - `miniprogram/api/learning.js` (3 个问题)

### 问题根因

小程序 API 设计时使用了与后端不同的路径规范：

- 小程序使用: `/api/v1/analysis/*`
- 后端实现: `/api/v1/analytics/*`

并且小程序包含了部分后端尚未实现的高级功能。

---

## 🎯 修复策略

### 方案选择: 修改小程序适配后端 ✅

**原因**:

1. 后端 API 已稳定且经过完整测试
2. 修改范围可控
3. 不影响 Web 前端（已 100%对齐）

### 修复原则

1. **直接替换**: 功能相同但路径不同的 API 直接替换路径
2. **功能合并**: 将多个相似调用合并到同一个后端 API
3. **参数适配**: 调整参数格式以匹配后端接口
4. **TODO 标记**: 未实现功能标记为待开发
5. **保持兼容**: 确保小程序现有调用方式不变

---

## 📝 详细修复步骤

### Step 1: 备份原文件

```bash
cd ~/my-devs/python/wuhao-tutor/miniprogram/api
cp analysis.js analysis.js.backup
cp learning.js learning.js.backup
```

### Step 2: 修改 `analysis.js`

#### 2.1 修改 `getOverview()` - 使用 learning-stats

**原代码**:

```javascript
getOverview(params = {}, config = {}) {
  const { days = 30 } = params;
  return request.get('analysis/overview', { days }, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取学情总览
 * @param {Object} params - 查询参数
 * @param {number} [params.days=30] - 统计天数
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 学情总览数据
 */
getOverview(params = {}, config = {}) {
  const { days = 30 } = params;

  // 映射时间范围参数到后端格式
  let timeRange = 'all';
  if (days <= 7) timeRange = '7d';
  else if (days <= 30) timeRange = '30d';
  else if (days <= 90) timeRange = '90d';

  return request.get('analytics/learning-stats', { time_range: timeRange }, {
    showLoading: false,
    ...config,
  });
}
```

#### 2.2 修改 `getActivity()` - 使用 learning-stats

**原代码**:

```javascript
getActivity(params = {}, config = {}) {
  const { days = 30, granularity = 'day' } = params;
  return request.get('analysis/activity', { days, granularity }, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取活跃度时间分布
 * @param {Object} params - 查询参数
 * @param {number} [params.days=30] - 统计天数
 * @param {string} [params.granularity='day'] - 时间粒度 (暂不支持，使用默认)
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 活跃度数据
 */
getActivity(params = {}, config = {}) {
  const { days = 30 } = params;

  // 映射时间范围参数
  let timeRange = 'all';
  if (days <= 7) timeRange = '7d';
  else if (days <= 30) timeRange = '30d';
  else if (days <= 90) timeRange = '90d';

  // 注意: 后端learning-stats包含study_trend，可用于活跃度展示
  // granularity参数暂时不支持，使用后端默认粒度
  return request.get('analytics/learning-stats', { time_range: timeRange }, {
    showLoading: false,
    ...config,
  }).then(response => {
    // 提取活跃度相关数据
    if (response.success && response.data) {
      return {
        success: true,
        data: {
          study_trend: response.data.study_trend || [],
          total_study_days: response.data.total_study_days || 0,
        },
        message: response.message,
      };
    }
    return response;
  });
}
```

#### 2.3 修改 `getMastery()` - 使用 knowledge-map

**原代码**:

```javascript
getMastery(params = {}, config = {}) {
  const { subject, grade } = params;
  const queryParams = {};
  if (subject) queryParams.subject = subject;
  if (grade) queryParams.grade = grade;

  return request.get('analysis/mastery', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取知识点掌握推断
 * @param {Object} params - 查询参数
 * @param {string} [params.subject] - 学科筛选
 * @param {string} [params.grade] - 年级筛选 (暂不支持)
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 知识点掌握数据
 */
getMastery(params = {}, config = {}) {
  const { subject } = params;
  // 注意: grade参数后端暂不支持

  const queryParams = {};
  if (subject) queryParams.subject = subject;

  return request.get('analytics/knowledge-map', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

#### 2.4 修改 `getRecommendations()` - 调整路径

**原代码**:

```javascript
getRecommendations(params = {}, config = {}) {
  const { subject, focus } = params;
  const queryParams = {};
  if (subject) queryParams.subject = subject;
  if (focus) queryParams.focus = focus;

  return request.get('analysis/recommendations', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取个性化学习建议
 * @param {Object} params - 查询参数
 * @param {string} [params.subject] - 学科筛选 (暂不支持)
 * @param {string} [params.focus] - 关注领域 (暂不支持)
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 学习建议数据
 */
getRecommendations(params = {}, config = {}) {
  // 注意: 后端learning/recommendations暂不支持subject和focus参数
  // 返回通用学习建议

  return request.get('learning/recommendations', {}, {
    showLoading: false,
    ...config,
  });
}
```

#### 2.5 修改 `getTrends()` - 使用 learning-stats

**原代码**:

```javascript
getTrends(params, config = {}) {
  if (!params || !params.metric) {
    return Promise.reject({
      code: 'VALIDATION_ERROR',
      message: '指标类型不能为空',
    });
  }

  const { metric, days = 30, subject } = params;
  const queryParams = { metric, days };
  if (subject) queryParams.subject = subject;

  return request.get('analysis/trends', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取学习趋势
 * @param {Object} params - 查询参数
 * @param {string} params.metric - 指标类型 (score/frequency/duration/mastery)
 * @param {number} [params.days=30] - 统计天数
 * @param {string} [params.subject] - 学科筛选 (暂不支持)
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 趋势数据
 */
getTrends(params, config = {}) {
  if (!params || !params.metric) {
    return Promise.reject({
      code: 'VALIDATION_ERROR',
      message: '指标类型不能为空',
    });
  }

  const { days = 30 } = params;
  // 注意: metric和subject参数后端暂不支持
  // 使用learning-stats的study_trend数据

  let timeRange = 'all';
  if (days <= 7) timeRange = '7d';
  else if (days <= 30) timeRange = '30d';
  else if (days <= 90) timeRange = '90d';

  return request.get('analytics/learning-stats', { time_range: timeRange }, {
    showLoading: false,
    ...config,
  }).then(response => {
    if (response.success && response.data) {
      return {
        success: true,
        data: {
          trend: response.data.study_trend || [],
          metric: params.metric,
        },
        message: response.message,
      };
    }
    return response;
  });
}
```

#### 2.6 修改 `getAnalytics()` - 路径已对齐 ✅

**原代码**:

```javascript
getAnalytics(params = {}, config = {}) {
  const { days = 30 } = params;
  return request.get('learning/analytics', { days }, {
    showLoading: true,
    loadingText: '加载数据中...',
    ...config,
  });
}
```

**状态**: 此 API 已对齐，无需修改 ✅

#### 2.7 修改 `getProgress()` - 使用 learning-stats

**原代码**:

```javascript
getProgress(params = {}, config = {}) {
  const { days = 7 } = params;
  return request.get('learning/progress', { days }, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取学习进度统计
 * @param {Object} params - 查询参数
 * @param {number} [params.days=7] - 统计天数
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 学习进度数据
 */
getProgress(params = {}, config = {}) {
  const { days = 7 } = params;

  let timeRange = '7d';
  if (days <= 7) timeRange = '7d';
  else if (days <= 30) timeRange = '30d';
  else if (days <= 90) timeRange = '90d';
  else timeRange = 'all';

  return request.get('analytics/learning-stats', { time_range: timeRange }, {
    showLoading: false,
    ...config,
  });
}
```

#### 2.8 修改 `getHistory()` - 调整路径

**原代码**:

```javascript
getHistory(params = {}, config = {}) {
  const { page = 1, size = 20, type, days = 90 } = params;
  const queryParams = {
    limit: size,
    offset: (page - 1) * size,
    days,
  };
  if (type) queryParams.type = type;

  return request.get('learning/history', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

**修改后**:

```javascript
/**
 * 获取学习历史记录
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.size=20] - 每页数量
 * @param {string} [params.type] - 类型筛选 (暂不支持)
 * @param {number} [params.days=90] - 统计天数 (暂不支持)
 * @param {Object} [config] - 请求配置
 * @returns {Promise<Object>} 学习历史数据
 */
getHistory(params = {}, config = {}) {
  const { page = 1, size = 20 } = params;
  // 注意: type和days参数后端暂不支持

  const queryParams = {
    limit: size,
    offset: (page - 1) * size,
  };

  return request.get('learning/questions/history', queryParams, {
    showLoading: false,
    ...config,
  });
}
```

#### 2.9 标记未实现功能

将以下方法标记为待实现（添加到文件末尾）：

```javascript
/**
 * ==================== 以下功能待后端实现 ====================
 * 这些API在后端尚未实现，暂时返回模拟数据或错误提示
 * TODO: 在后端实现后移除此部分，使用实际API
 */

/**
 * 获取学习目标列表 (待实现)
 */
getGoals(params = {}, config = {}) {
  console.warn('[API未实现] learning/goals - 学习目标功能待后端实现');
  return Promise.resolve({
    success: true,
    data: {
      items: [],
      total: 0,
    },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 创建学习目标 (待实现)
 */
createGoal(params, config = {}) {
  console.warn('[API未实现] POST learning/goals - 学习目标功能待后端实现');
  return Promise.reject({
    code: 'NOT_IMPLEMENTED',
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取学科分析 (待实现)
 */
getSubjects(params = {}, config = {}) {
  console.warn('[API未实现] analysis/subjects - 学科分析功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { subjects: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取学习模式分析 (待实现)
 */
getPatterns(params = {}, config = {}) {
  console.warn('[API未实现] analysis/patterns - 学习模式分析待后端实现');
  return Promise.resolve({
    success: true,
    data: { patterns: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取改进建议 (待实现)
 */
getImprovements(params = {}, config = {}) {
  console.warn('[API未实现] analysis/improvements - 改进建议功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { improvements: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取知识缺口分析 (待实现)
 */
getGaps(params = {}, config = {}) {
  console.warn('[API未实现] analysis/gaps - 知识缺口分析待后端实现');
  return Promise.resolve({
    success: true,
    data: { gaps: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 生成学情报告 (待实现)
 */
generateReport(params, config = {}) {
  console.warn('[API未实现] POST analysis/report - 学情报告生成待后端实现');
  return Promise.reject({
    code: 'NOT_IMPLEMENTED',
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取排名信息 (待实现)
 */
getRanking(params = {}, config = {}) {
  console.warn('[API未实现] analysis/ranking - 排名功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { ranking: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取学习成就 (待实现)
 */
getAchievements(params = {}, config = {}) {
  console.warn('[API未实现] learning/achievements - 成就系统待后端实现');
  return Promise.resolve({
    success: true,
    data: { achievements: [] },
    message: '功能开发中，敬请期待',
  });
},

/**
 * 获取学习洞察 (待实现)
 */
getInsights(params = {}, config = {}) {
  console.warn('[API未实现] analysis/insights - 学习洞察功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { insights: [] },
    message: '功能开发中，敬请期待',
  });
}
```

### Step 3: 修改 `learning.js`

在文件末尾添加未实现功能的标记：

```javascript
/**
 * ==================== 以下功能待后端实现 ====================
 */

/**
 * 获取收藏列表 (待实现)
 */
getFavorites(params = {}, config = {}) {
  console.warn('[API未实现] learning/favorites - 收藏功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { items: [], total: 0 },
    message: '功能开发中,敬请期待',
  });
},

/**
 * 获取学习见解 (待实现)
 */
getInsights(params = {}, config = {}) {
  console.warn('[API未实现] learning/insights - 学习见解功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { insights: [] },
    message: '功能开发中,敬请期待',
  });
},

/**
 * 获取热门问题 (待实现)
 */
getPopular(params = {}, config = {}) {
  console.warn('[API未实现] learning/popular - 热门问题功能待后端实现');
  return Promise.resolve({
    success: true,
    data: { items: [], total: 0 },
    message: '功能开发中,敬请期待',
  });
}
```

---

## ✅ 测试验证

### Step 4: 运行对齐检查

```bash
cd ~/my-devs/python/wuhao-tutor
uv run python scripts/analyze_miniprogram_api.py
```

**期望结果**:

- 对齐率: 100%
- 问题数: 0
- 状态: ✅ 完全对齐

### Step 5: 功能测试清单

#### 5.1 学情分析测试

- [ ] 学情总览 (`getOverview`)
- [ ] 活跃度分析 (`getActivity`)
- [ ] 知识掌握 (`getMastery`)
- [ ] 学习建议 (`getRecommendations`)
- [ ] 学习趋势 (`getTrends`)
- [ ] 学习进度 (`getProgress`)
- [ ] 学习历史 (`getHistory`)

#### 5.2 待实现功能验证

- [ ] 确认返回友好提示
- [ ] 不阻塞主流程
- [ ] 控制台有警告日志

---

## ⚠️ 注意事项

### 1. 参数映射

某些 API 的参数格式有变化，需要在小程序端进行转换：

| 小程序参数    | 后端参数     | 转换逻辑                                                         |
| ------------- | ------------ | ---------------------------------------------------------------- |
| `days`        | `time_range` | `days<=7→'7d'`, `days<=30→'30d'`, `days<=90→'90d'`, `else→'all'` |
| `granularity` | -            | 暂不支持，使用默认                                               |
| `focus`       | -            | 暂不支持                                                         |

### 2. 数据结构适配

部分 API 返回的数据结构可能不同，需要在小程序端进行适配：

```javascript
// 示例：提取特定字段
return request.get('analytics/learning-stats', params).then((response) => {
  if (response.success && response.data) {
    return {
      success: true,
      data: {
        // 只提取需要的字段
        study_trend: response.data.study_trend || [],
        total_days: response.data.total_study_days || 0,
      },
      message: response.message,
    }
  }
  return response
})
```

### 3. 错误处理

对于待实现功能，确保：

- 返回友好的错误消息
- 不阻塞主业务流程
- 在控制台输出警告日志

### 4. 向后兼容

修改 API 调用后，确保：

- 小程序页面调用方式不变
- 数据展示逻辑兼容
- 错误处理完善

---

## 📊 修复进度追踪

### analysis.js 修复清单

- [ ] `getOverview()` - 使用 `analytics/learning-stats`
- [ ] `getActivity()` - 使用 `analytics/learning-stats`
- [ ] `getMastery()` - 使用 `analytics/knowledge-map`
- [ ] `getRecommendations()` - 使用 `learning/recommendations`
- [ ] `getTrends()` - 使用 `analytics/learning-stats`
- [x] `getAnalytics()` - 已对齐 ✅
- [ ] `getProgress()` - 使用 `analytics/learning-stats`
- [ ] `getHistory()` - 使用 `learning/questions/history`
- [ ] `getGoals()` - 标记为待实现
- [ ] `createGoal()` - 标记为待实现
- [ ] `getSubjects()` - 标记为待实现
- [ ] `getPatterns()` - 标记为待实现
- [ ] `getImprovements()` - 标记为待实现
- [ ] `getGaps()` - 标记为待实现
- [ ] `generateReport()` - 标记为待实现
- [ ] `getRanking()` - 标记为待实现
- [ ] `getAchievements()` - 标记为待实现
- [ ] `getInsights()` - 标记为待实现

### learning.js 修复清单

- [ ] `getFavorites()` - 标记为待实现
- [ ] `getInsights()` - 标记为待实现
- [ ] `getPopular()` - 标记为待实现

---

## 🎯 完成标准

1. ✅ 所有 API 路径与后端对齐
2. ✅ 参数格式正确映射
3. ✅ 数据结构适配完成
4. ✅ 待实现功能标记清晰
5. ✅ 对齐检查 100%通过
6. ✅ 核心功能测试通过

---

**下一步**: 完成修复后执行 `uv run python scripts/analyze_miniprogram_api.py` 验证

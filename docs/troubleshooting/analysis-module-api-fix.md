# 学习报告模块 API 路径修复文档

## 问题描述

在小程序中点击"学习报告" Tab 时，出现大量 `ReferenceError` 错误，控制台显示多个 API 调用失败。

## 错误现象

```
ReferenceError: 自动分类器 is not defined
加载学情分析数据失败
```

## 根本原因

### 1. API 路径重复拼接问题

小程序 `api/analysis.js` 中的 `getActivity()` 方法使用了错误的路径格式：

```javascript
// ❌ 错误：使用 api/v1/ 前缀
return request.get('api/v1/analytics/learning-stats', ...)
```

由于 `request.js` 中的 [buildUrl()](https://link-to-request.js#L169-L185) 方法会自动添加 `/api/v1/` 前缀，导致最终请求路径变为：

```
/api/v1/api/v1/analytics/learning-stats  ❌ 404 错误
```

### 2. 响应数据格式兼容性问题

页面逻辑中直接访问 `response.data`，但没有处理 API 直接返回数据对象的情况，导致数据提取失败。

## API 路径规范

根据前端 (`frontend/src/api/analytics.ts`) 和后端的实现，正确的路径格式为：

| API 方法    | 正确路径                   | 错误路径                          |
| ----------- | -------------------------- | --------------------------------- |
| getOverview | `analytics/learning-stats` | `api/v1/analytics/learning-stats` |
| getActivity | `analytics/learning-stats` | `api/v1/analytics/learning-stats` |
| getMastery  | `analytics/knowledge-map`  | `api/v1/analytics/knowledge-map`  |
| getProgress | `analytics/learning-stats` | `api/v1/analytics/learning-stats` |

### 路径构建机制说明

`utils/request.js` 中的 `buildUrl()` 方法逻辑：

```javascript
buildUrl(url) {
  // 如果是完整 URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  // 移除开头的斜杠
  const path = url.startsWith('/') ? url.slice(1) : url;

  // 对于以 /api 开头的路径，直接拼接
  if (path.startsWith('api/')) {
    return `${this.baseUrl}/${path}`;  // 例如: http://localhost:8000/api/v1/...
  }

  // 对于传统路径，添加 /api/v1 前缀
  return `${this.baseUrl}/api/${this.version}/${path}`;  // 例如: http://localhost:8000/api/v1/analytics/learning-stats
}
```

**核心规则**：

- ✅ API 模块中的路径不应包含 `api/v1/` 前缀
- ✅ 使用相对路径，如 `analytics/learning-stats`
- ❌ 不要使用 `api/v1/analytics/learning-stats`

## 修复方案

### 1. 修复 API 路径

**文件**: `miniprogram/api/analysis.js`

修复 `getActivity()` 方法的路径：

```javascript
// 修改前 ❌
getActivity(params = {}, config = {}) {
  return request.get(
    'api/v1/analytics/learning-stats',  // 错误路径
    { time_range: timeRange },
    { showLoading: false, ...config }
  );
}

// 修改后 ✅
getActivity(params = {}, config = {}) {
  return request.get(
    'analytics/learning-stats',  // 正确路径
    { time_range: timeRange },
    { showLoading: false, ...config }
  );
}
```

### 2. 删除重复方法定义

**文件**: `miniprogram/pages/analysis/report/index.js`

#### (1) 保留正确的 `generateKnowledgePoints(subject)` 方法

```javascript
// ✅ 保留此方法 (Line 377)
generateKnowledgePoints(subject) {
  const knowledgeMap = {
    数学: [
      { name: '函数与方程', level: 'high', score: 88 },
      { name: '几何图形', level: 'medium', score: 72 },
      { name: '概率统计', level: 'low', score: 56 },
    ],
    语文: [
      { name: '阅读理解', level: 'high', score: 85 },
      { name: '作文写作', level: 'medium', score: 75 },
      { name: '古诗词', level: 'low', score: 60 },
    ],
    英语: [
      { name: '语法', level: 'high', score: 90 },
      { name: '词汇', level: 'medium', score: 78 },
      { name: '听力', level: 'low', score: 65 },
    ],
  };

  return (
    knowledgeMap[subject.subject_name] || [
      { name: '基础知识', level: 'medium', score: 75 },
      { name: '应用能力', level: 'medium', score: 70 },
    ]
  );
}

// ❌ 删除第二个无参数版本 (Line 723)
```

#### (2) 删除所有重复的图表方法

删除以下重复方法（Line 723-850）：

- `generateKnowledgePoints()` - 无参数版本
- `initKnowledgeChartComponent()` - 第二个定义
- `initKnowledgeChartCanvas()` - 第二个定义
- `initKnowledgeChart()` - 第二个定义

#### (3) 优化图表初始化逻辑

将 `initKnowledgeChartCanvas` 简化为只负责初始化 canvas，配置逻辑提取到新方法 `updateKnowledgeChartData`：

```javascript
// 简化后的 initKnowledgeChartCanvas
initKnowledgeChartCanvas(canvas, width, height, dpr) {
  knowledgeChart = echarts.init(canvas, null, {
    width: width,
    height: height,
    devicePixelRatio: dpr,
  });

  canvas.setChart(knowledgeChart);

  // 如果有数据，立即配置图表
  if (this.data.knowledgePoints && this.data.knowledgePoints.length > 0) {
    this.updateKnowledgeChartData();
  }

  return knowledgeChart;
}

// 新增: 专门负责更新图表数据
updateKnowledgeChartData() {
  if (!knowledgeChart || !this.data.knowledgePoints || this.data.knowledgePoints.length === 0) {
    console.log('知识点图表实例未初始化或无数据');
    return;
  }

  const knowledgePoints = this.data.knowledgePoints;
  const indicator = knowledgePoints.map(point => ({
    name: point.name,
    max: 100,
  }));

  const radarData = knowledgePoints.map(point => point.mastery || point.value || 0);

  const option = {
    // ... 雷达图配置
  };

  knowledgeChart.setOption(option);
}
```

### 3. 增强响应数据处理

**文件**: `miniprogram/pages/analysis/report/index.js`

优化数据提取逻辑，兼容多种响应格式：

```javascript
// 修改前 ❌
const analyticsData = {
  overview: overviewResult.status === 'fulfilled' ? overviewResult.value.data : {},
  knowledge: knowledgeResult.status === 'fulfilled' ? knowledgeResult.value.data : {},
  progress: progressResult.status === 'fulfilled' ? progressResult.value.data : {},
  timestamp: Date.now(),
}

// 修改后 ✅
// 处理结果，兼容多种响应格式
const extractData = (result) => {
  if (result.status !== 'fulfilled') return {}
  const response = result.value
  // 处理多种响应格式
  if (response.data) return response.data // { success: true, data: {...} }
  if (response.success !== false) return response // 直接返回数据
  return {} // 其他情况
}

const analyticsData = {
  overview: extractData(overviewResult),
  knowledge: extractData(knowledgeResult),
  progress: extractData(progressResult),
  timestamp: Date.now(),
}
```

## 修复后的完整路径列表

以下是 `miniprogram/api/analysis.js` 中所有正确的 API 路径：

| 方法名             | 路径                         | 说明           |
| ------------------ | ---------------------------- | -------------- |
| getOverview        | `analytics/learning-stats`   | 学情总览       |
| getActivity        | `analytics/learning-stats`   | 活跃度时间分布 |
| getMastery         | `analytics/knowledge-map`    | 知识点掌握推断 |
| getRecommendations | `learning/recommendations`   | 个性化学习建议 |
| getTrends          | `analytics/learning-stats`   | 学习趋势       |
| getAnalytics       | `learning/analytics`         | 学习统计数据   |
| getProgress        | `analytics/learning-stats`   | 学习进度统计   |
| getHistory         | `learning/questions/history` | 学习历史记录   |

## 验证步骤

1. **检查 API 路径格式**

   ```bash
   # 确认没有使用 api/v1/ 前缀
   grep -n "api/v1/" miniprogram/api/analysis.js
   # 预期输出：无匹配结果
   ```

2. **测试学习报告功能**

   - 登录小程序
   - 点击"学习报告" Tab
   - 验证数据是否正常加载
   - 检查控制台是否有错误

3. **检查网络请求**
   - 打开微信开发者工具的 Network 面板
   - 验证请求 URL 格式是否正确：
     ```
     ✅ http://localhost:8000/api/v1/analytics/learning-stats
     ❌ http://localhost:8000/api/v1/api/v1/analytics/learning-stats
     ```

## 与前端对齐

前端 (`frontend/src/api/analytics.ts`) 的实现：

```typescript
// 前端使用的正确路径
export const getLearningStats = (timeRange: string = '30d') => {
  return http.get<AnalyticsResponse<LearningStats>>('/analytics/learning-stats', {
    params: { time_range: timeRange },
  })
}

export const getKnowledgeMap = (subject?: string) => {
  return http.get<AnalyticsResponse<any>>('/analytics/knowledge-map', {
    params: { subject },
  })
}
```

小程序与前端的路径对齐表：

| 功能     | 前端路径                    | 小程序路径                 | 状态    |
| -------- | --------------------------- | -------------------------- | ------- |
| 学习统计 | `/analytics/learning-stats` | `analytics/learning-stats` | ✅ 一致 |
| 知识图谱 | `/analytics/knowledge-map`  | `analytics/knowledge-map`  | ✅ 一致 |
| 用户统计 | `/analytics/user/stats`     | 未实现                     | -       |

## 后续优化建议

1. **统一错误处理**

   - 在 API 层面捕获错误并提供友好的错误消息
   - 避免将技术错误信息直接展示给用户

2. **数据缓存策略**

   - 当前已实现本地缓存，但可以考虑添加缓存过期机制
   - 在网络错误时优先展示缓存数据

3. **加载状态优化**

   - 使用 Promise.allSettled 很好，但可以添加部分数据加载成功的提示
   - 例如："部分数据加载失败，显示已加载的内容"

4. **类型安全**
   - 考虑为 API 响应添加 JSDoc 类型注释
   - 提高代码可维护性和开发体验

## 相关文件

- `miniprogram/api/analysis.js` - 学情分析 API 模块
- `miniprogram/pages/analysis/report/index.js` - 学习报告页面逻辑
- `miniprogram/utils/request.js` - 网络请求工具
- `frontend/src/api/analytics.ts` - 前端学情分析 API（参考实现）

## 修复时间

**修复日期**: 2025-10-19  
**修复版本**: v1.0.1  
**修复人员**: AI 协作

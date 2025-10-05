# 五好伴学微信小程序 - 网络层架构文档

## 目录

- [1. 概述](#1-概述)
- [2. 架构设计](#2-架构设计)
- [3. 核心组件](#3-核心组件)
- [4. 使用指南](#4-使用指南)
- [5. 配置说明](#5-配置说明)
- [6. 错误处理](#6-错误处理)
- [7. 性能优化](#7-性能优化)
- [8. 监控与调试](#8-监控与调试)
- [9. 最佳实践](#9-最佳实践)
- [10. 故障排查](#10-故障排查)

## 1. 概述

### 1.1 设计目标

五好伴学微信小程序网络层架构旨在提供：

- **统一的API请求管理**：标准化的请求/响应处理
- **智能缓存策略**：多层缓存机制，提升用户体验
- **健壮的错误处理**：全面的错误捕获与处理机制
- **网络状态监控**：实时网络质量监测与适配
- **请求队列管理**：并发控制与优先级管理
- **性能监控**：请求性能跟踪与优化建议

### 1.2 技术特性

- 🚀 **高性能**：请求去重、并发控制、智能重试
- 🔧 **可配置**：灵活的配置系统，支持多环境切换
- 🛡️ **安全可靠**：认证管理、错误处理、数据加密
- 📊 **可观测**：完整的监控指标与日志系统
- 🎯 **用户友好**：智能的用户体验优化

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Pages/Components)               │
├─────────────────────────────────────────────────────────────┤
│                     API接口层 (api/*)                      │
├─────────────────────────────────────────────────────────────┤
│                 增强版API客户端 (EnhancedApiClient)          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ │
│  │  网络监控   │ │  缓存管理   │ │  队列管理   │ │ 错误处理│ │
│  │ NetworkMon  │ │ CacheMan    │ │ RequestQ    │ │ErrorHan │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    认证管理 (AuthManager)                   │
├─────────────────────────────────────────────────────────────┤
│                    存储管理 (StorageManager)                │
├─────────────────────────────────────────────────────────────┤
│                  微信小程序网络API (wx.request)             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流向

```
用户操作 → API调用 → 请求预处理 → 缓存检查 → 队列调度 → 网络请求 → 响应处理 → 缓存更新 → UI更新
                        ↓              ↓           ↓           ↓
                   错误处理 ←── 网络监控 ←── 性能监控 ←── 统计上报
```

## 3. 核心组件

### 3.1 增强版API客户端 (EnhancedApiClient)

**位置**: `utils/api.js`

**功能特性**:
- 统一的HTTP请求封装
- 请求/响应拦截器机制
- 自动认证头注入
- 请求去重与缓存集成
- 重试机制与错误处理

**核心方法**:

```javascript
// 基础请求方法
apiClient.request(config)
apiClient.get(url, params, options)
apiClient.post(url, data, options)
apiClient.put(url, data, options)
apiClient.delete(url, options)
apiClient.patch(url, data, options)

// 文件操作
apiClient.upload(url, filePath, options)
apiClient.download(url, options)

// 拦截器管理
apiClient.addRequestInterceptor(fulfilled, rejected)
apiClient.addResponseInterceptor(fulfilled, rejected)

// 配置与统计
apiClient.setDefaults(config)
apiClient.getStats()
apiClient.resetStats()
```

### 3.2 网络状态监控器 (NetworkMonitor)

**位置**: `utils/network-monitor.js`

**功能特性**:
- 实时网络状态监测
- 网络质量评估
- 网络切换事件监听
- 网络适配建议

**使用示例**:

```javascript
import { networkMonitor } from './utils/network-monitor.js';

// 获取当前网络状态
const status = networkMonitor.getCurrentStatus();
console.log('网络状态:', status);

// 监听网络变化
const unsubscribe = networkMonitor.addListener((current, previous) => {
  console.log('网络状态变化:', current);
});

// 检查网络质量
const quality = networkMonitor.getNetworkQuality();
console.log('网络质量:', quality.grade, quality.description);

// 检查是否适合某种操作
const suitable = networkMonitor.isNetworkSuitableFor('file_upload');
if (!suitable.suitable) {
  console.warn('当前网络不适合文件上传:', suitable.reason);
}
```

### 3.3 缓存管理器 (CacheManager)

**位置**: `utils/cache-manager.js`

**功能特性**:
- 多层缓存策略 (内存/存储)
- 自动过期与清理
- 缓存压缩与加密
- 标签化缓存管理

**缓存策略**:

```javascript
const CacheStrategy = {
  NO_CACHE: 'NO_CACHE',           // 不缓存
  MEMORY_CACHE: 'MEMORY_CACHE',   // 内存缓存
  STORAGE_CACHE: 'STORAGE_CACHE', // 存储缓存
  NETWORK_FIRST: 'NETWORK_FIRST', // 网络优先
  CACHE_FIRST: 'CACHE_FIRST',     // 缓存优先
  CACHE_ONLY: 'CACHE_ONLY',       // 仅缓存
  NETWORK_ONLY: 'NETWORK_ONLY'    // 仅网络
};
```

**使用示例**:

```javascript
import { cacheManager, CacheStrategy } from './utils/cache-manager.js';

// 设置缓存
await cacheManager.set('user_profile', userData, {
  strategy: CacheStrategy.STORAGE_CACHE,
  ttl: 24 * 60 * 60 * 1000, // 24小时
  tags: ['user', 'profile'],
  encrypt: true
});

// 获取缓存
const userData = await cacheManager.get('user_profile');

// 按标签清理缓存
await cacheManager.deleteByTags(['user']);
```

### 3.4 请求队列管理器 (RequestQueue)

**位置**: `utils/request-queue.js`

**功能特性**:
- 并发数控制
- 优先级队列
- 请求去重
- 自动重试机制

**优先级定义**:

```javascript
const Priority = {
  HIGH: 3,    // 高优先级 (用户交互、认证等)
  NORMAL: 2,  // 普通优先级 (数据获取等)
  LOW: 1      // 低优先级 (统计上报、日志等)
};
```

**使用示例**:

```javascript
import { requestQueue, Priority } from './utils/request-queue.js';

// 添加高优先级请求
const result = await requestQueue.enqueue(() => {
  return wx.request({
    url: 'https://api.example.com/urgent',
    method: 'POST',
    data: { urgent: true }
  });
}, {
  priority: Priority.HIGH,
  timeout: 5000,
  retryCount: 2
});

// 获取队列状态
const status = requestQueue.getStatus();
console.log('队列状态:', status);
```

### 3.5 错误处理器 (ErrorHandler)

**位置**: `utils/error-handler.js`

**功能特性**:
- 分类错误处理
- 自定义处理策略
- 错误上报机制
- 用户友好提示

**错误分类**:

```javascript
const ErrorCategory = {
  NETWORK: 'NETWORK',         // 网络错误
  AUTH: 'AUTH',               // 认证错误
  VALIDATION: 'VALIDATION',   // 验证错误
  BUSINESS: 'BUSINESS',       // 业务错误
  SYSTEM: 'SYSTEM',           // 系统错误
  PERMISSION: 'PERMISSION',   // 权限错误
  TIMEOUT: 'TIMEOUT',         // 超时错误
  UNKNOWN: 'UNKNOWN'          // 未知错误
};
```

**处理策略**:

```javascript
const ErrorStrategy = {
  SILENT: 'SILENT',       // 静默处理
  TOAST: 'TOAST',         // 显示Toast
  MODAL: 'MODAL',         // 显示模态框
  PAGE: 'PAGE',           // 跳转错误页
  RETRY: 'RETRY',         // 自动重试
  REPORT: 'REPORT',       // 上报错误
  FALLBACK: 'FALLBACK'    // 降级处理
};
```

## 4. 使用指南

### 4.1 基础API调用

```javascript
import { api } from '../utils/api.js';

// 获取作业列表 (自动缓存)
const homeworkList = await api.homework.getList({
  page: 1,
  size: 20,
  status: 'pending'
});

// 提交作业 (高优先级)
const submitResult = await api.homework.submit(homeworkId, {
  answers: userAnswers,
  attachments: uploadedFiles
});

// 发送AI消息 (带重试)
const chatResponse = await api.chat.sendMessage({
  sessionId: currentSessionId,
  message: userInput,
  type: 'text'
});
```

### 4.2 自定义请求配置

```javascript
import { apiClient, Priority, CacheStrategy } from '../utils/api.js';

// 自定义请求配置
const customRequest = await apiClient.post('/custom/endpoint', data, {
  // 优先级配置
  priority: Priority.HIGH,

  // 缓存配置
  enableCache: true,
  cache: {
    strategy: CacheStrategy.CACHE_FIRST,
    ttl: 10 * 60 * 1000, // 10分钟
    tags: ['custom', 'endpoint']
  },

  // 重试配置
  retry: {
    maxRetries: 2,
    baseDelay: 1000,
    strategy: 'EXPONENTIAL_BACKOFF'
  },

  // 超时配置
  timeout: 15000,

  // 其他选项
  skipAuth: false,
  enableQueue: true,
  enableDeduplication: true
});
```

### 4.3 错误处理集成

```javascript
import { errorHandler, ErrorCategory, ErrorStrategy } from '../utils/error-handler.js';

// 自定义错误处理规则
errorHandler.addRule({
  category: ErrorCategory.BUSINESS,
  condition: (error) => error.statusCode === 400 && error.data?.code === 'HOMEWORK_EXPIRED',
  strategy: ErrorStrategy.MODAL,
  message: '作业已过期，无法提交',
  action: 'goBack'
});

// 手动处理错误
try {
  const result = await api.homework.submit(id, data);
} catch (error) {
  errorHandler.handleError(error, {
    operation: 'homework_submit',
    homeworkId: id,
    timestamp: Date.now()
  });
}
```

### 4.4 网络状态适配

```javascript
import { networkMonitor } from '../utils/network-monitor.js';

// 根据网络状态调整行为
const performUpload = async (files) => {
  const networkStatus = networkMonitor.getCurrentStatus();

  if (!networkStatus.isConnected) {
    throw new Error('网络未连接，无法上传文件');
  }

  // 检查网络是否适合大文件上传
  const suitable = networkMonitor.isNetworkSuitableFor('large_download');

  if (!suitable.suitable && files.some(f => f.size > 5 * 1024 * 1024)) {
    // 网络较差时，压缩图片或提示用户
    wx.showModal({
      title: '网络提示',
      content: '当前网络状况不佳，建议在WiFi环境下上传大文件',
      showCancel: true,
      confirmText: '继续上传',
      cancelText: '稍后上传'
    });
  }

  // 执行上传
  return api.upload.file(files[0].path, {
    onProgress: (progress) => {
      console.log(`上传进度: ${progress.progress}%`);
    }
  });
};
```

## 5. 配置说明

### 5.1 环境配置

**开发环境** (`config/environments/development.js`):

```javascript
module.exports = {
  api: {
    baseUrl: 'https://dev-api.wuhao-tutor.com',
    timeout: 10000,
    retryCount: 3,
    retryDelay: 1000
  },
  cache: {
    defaultTTL: 5 * 60 * 1000,
    maxMemoryItems: 50
  },
  error: {
    showDetails: true,
    autoReport: false
  },
  performance: {
    enabled: true,
    sampleRate: 1.0
  }
};
```

**生产环境** (`config/environments/production.js`):

```javascript
module.exports = {
  api: {
    baseUrl: 'https://api.wuhao-tutor.com',
    timeout: 15000,
    retryCount: 2,
    retryDelay: 2000
  },
  cache: {
    defaultTTL: 10 * 60 * 1000,
    maxMemoryItems: 100
  },
  error: {
    showDetails: false,
    autoReport: true
  },
  performance: {
    enabled: true,
    sampleRate: 0.1
  }
};
```

### 5.2 网络层配置

```javascript
// 配置API客户端
apiClient.setDefaults({
  retry: {
    strategy: 'EXPONENTIAL_BACKOFF',
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    multiplier: 2,
    jitter: 0.1
  },
  cache: {
    strategy: CacheStrategy.MEMORY_CACHE,
    ttl: 5 * 60 * 1000,
    enableCache: false
  },
  queue: {
    enableQueue: true,
    priority: Priority.NORMAL,
    enableDeduplication: true
  }
});

// 配置错误处理器
errorHandler.setConfig({
  enabled: true,
  showDetails: __DEV__,
  autoReport: !__DEV__,
  maxErrorLogs: 1000,
  reportInterval: 60000,
  reportBatchSize: 20
});

// 配置缓存管理器
cacheManager.setConfig({
  defaultTTL: 10 * 60 * 1000,
  maxMemoryItems: 100,
  compressionThreshold: 2048,
  encryptionEnabled: true
});
```

## 6. 错误处理

### 6.1 错误分类与处理

| 错误类型 | HTTP状态码 | 处理策略 | 用户体验 |
|---------|-----------|---------|---------|
| 网络错误 | 0 | Toast + 重试 | "网络连接失败，请检查网络设置" |
| 认证过期 | 401 | Modal + 重定向 | "登录已过期，请重新登录" |
| 权限不足 | 403 | Toast | "没有权限执行此操作" |
| 参数错误 | 422 | Toast | 显示具体验证错误信息 |
| 业务错误 | 400 | Toast/Modal | 显示业务错误信息 |
| 服务器错误 | 500+ | Modal + 重试 | "服务器暂时不可用，请稍后重试" |

### 6.2 错误恢复机制

```javascript
// 网络重连恢复
networkMonitor.addListener((current, previous) => {
  if (!previous.isConnected && current.isConnected) {
    // 网络恢复，重试失败的请求
    requestQueue.resume();
    console.log('网络已恢复，开始重试失败的请求');
  }
});

// 认证过期恢复
apiClient.addResponseInterceptor(null, async (error) => {
  if (error.statusCode === 401) {
    try {
      // 自动刷新Token
      await auth.refreshToken();
      // 重试原请求
      return apiClient.request(error.config);
    } catch (refreshError) {
      // 刷新失败，跳转登录
      wx.redirectTo({ url: '/pages/login/index' });
      throw refreshError;
    }
  }
  throw error;
});
```

## 7. 性能优化

### 7.1 缓存策略优化

```javascript
// 不同数据的缓存策略
const cacheStrategies = {
  // 用户信息 - 长期缓存
  userProfile: {
    strategy: CacheStrategy.STORAGE_CACHE,
    ttl: 24 * 60 * 60 * 1000, // 24小时
    tags: ['user']
  },

  // 作业列表 - 短期缓存
  homeworkList: {
    strategy: CacheStrategy.MEMORY_CACHE,
    ttl: 5 * 60 * 1000, // 5分钟
    tags: ['homework']
  },

  // 系统配置 - 长期缓存
  systemConfig: {
    strategy: CacheStrategy.STORAGE_CACHE,
    ttl: 60 * 60 * 1000, // 1小时
    tags: ['system']
  },

  // 聊天历史 - 混合策略
  chatHistory: {
    strategy: CacheStrategy.CACHE_FIRST,
    ttl: 10 * 60 * 1000, // 10分钟
    tags: ['chat']
  }
};
```

### 7.2 请求优化

```javascript
// 请求优先级管理
const priorityMap = {
  // 用户交互 - 最高优先级
  userInteraction: Priority.HIGH,
  // 数据获取 - 普通优先级
  dataFetch: Priority.NORMAL,
  // 后台任务 - 最低优先级
  background: Priority.LOW
};

// 请求去重
const deduplicationConfig = {
  // GET请求默认去重
  enableDeduplication: true,
  // 去重时间窗口
  deduplicationWindow: 1000
};

// 并发控制
requestQueue.setConfig({
  maxConcurrency: 6,      // 最大并发数
  maxQueueSize: 100,      // 队列最大长度
  enablePriority: true,   // 启用优先级
  highPriorityRatio: 0.3  // 高优先级比例限制
});
```

### 7.3 网络适配优化

```javascript
// 根据网络状态调整策略
const adaptToNetwork = () => {
  const networkStatus = networkMonitor.getCurrentStatus();
  const quality = networkMonitor.getNetworkQuality();

  if (quality.score < 60) {
    // 网络质量较差时的优化策略
    apiClient.setDefaults({
      timeout: 20000,           // 增加超时时间
      retry: { maxRetries: 1 }, // 减少重试次数
      cache: {
        strategy: CacheStrategy.CACHE_FIRST,  // 优先使用缓存
        ttl: 30 * 60 * 1000    // 延长缓存时间
      }
    });

    // 暂停低优先级请求
    requestQueue.setConfig({ maxConcurrency: 3 });
  } else {
    // 网络质量良好时恢复默认配置
    apiClient.setDefaults(defaultApiConfig);
    requestQueue.setConfig({ maxConcurrency: 6 });
  }
};

// 监听网络变化，动态调整
networkMonitor.addListener(adaptToNetwork);
```

## 8. 监控与调试

### 8.1 性能监控

```javascript
// 获取API客户端统计
const apiStats = apiClient.getStats();
console.log('API统计:', {
  总请求数: apiStats.totalRequests,
  成功率: apiStats.successRate + '%',
  平均响应时间: apiStats.averageResponseTime + 'ms',
  缓存命中率: apiStats.cacheHitRate + '%'
});

// 获取队列状态
const queueStatus = requestQueue.getStatus();
console.log('队列状态:', {
  队列长度: queueStatus.queueLength,
  活跃请求: queueStatus.activeRequests,
  平均等待时间: queueStatus.stats.averageWaitTime + 'ms'
});

// 获取网络统计
const networkStats = networkMonitor.getStatistics();
console.log('网络统计:', {
  平均延迟: networkStats.latency.avg + 'ms',
  平均带宽: networkStats.bandwidth.avg + 'Mbps',
  信号强度: networkStats.signalStrength.avg
});
```

### 8.2 错误监控

```javascript
// 获取错误统计
const errorStats = errorHandler.getStats();
console.log('错误统计:', {
  总错误数: errorStats.totalErrors,
  网络错误: errorStats.networkErrors,
  认证错误: errorStats.authErrors,
  错误率: errorStats.errorRate + '次/分钟'
});

// 获取错误日志
const recentErrors = errorHandler.getErrorLogs(10);
console.log('最近错误:', recentErrors);
```

### 8.3 调试工具

```javascript
// 开发环境调试面板
if (__DEV__) {
  const debugPanel = {
    showStats() {
      const stats = {
        api: apiClient.getStats(),
        queue: requestQueue.getStatus(),
        cache: cacheManager.getStats(),
        network: networkMonitor.getCurrentStatus(),
        errors: errorHandler.getStats()
      };
      console.table(stats);
    },

    clearCache() {
      cacheManager.clear();
      console.log('缓存已清空');
    },

    clearQueue() {
      requestQueue.clear();
      console.log('请求队列已清空');
    },

    simulateError(type) {
      errorHandler.handleError({
        type: type,
        message: `模拟${type}错误`,
        statusCode: 500
      });
    }
  };

  // 挂载到全局，方便调试
  wx.debugPanel = debugPanel;
}
```

## 9. 最佳实践

### 9.1 API设计规范

```javascript
// ✅ 推荐：使用语义化的API调用
const homework = await api.homework.getDetail(homeworkId);
const submitResult = await api.homework.submit(homeworkId, answerData);

// ❌ 不推荐：直接使用底层请求
const homework = await apiClient.get(`/homework/${homeworkId}`);
```

### 9.2 错误处理规范

```javascript
// ✅ 推荐：使用try-catch包装可能失败的操作
const handleSubmitHomework = async (homeworkId, data) => {
  try {
    const result = await api.homework.submit(homeworkId, data);
    wx.showToast({ title: '提交成功', icon: 'success' });
    return result;
  } catch (error) {
    // 错误会被自动处理，这里只需要处理特殊逻辑
    if (error.statusCode === 400 && error.data?.code === 'HOMEWORK_EXPIRED') {
      // 特殊业务逻辑
      this.redirectToHomeworkList();
    }
    throw error;
  }
};

// ❌ 不推荐：忽略错误或不当处理
const badSubmitHomework = async (homeworkId, data) => {
  api.homework.submit(homeworkId, data); // 没有错误处理
};
```

### 9.3 缓存使用规范

```javascript
// ✅ 推荐：为不同类型的数据选择合适的缓存策略
const getCachedUserProfile = () => {
  return api.auth.getUserInfo(); // 自动使用长期缓存
};

const getLatestHomeworkList = () => {
  return api.homework.getList(params, {
    enableCache: true,
    cache: { ttl: 2 * 60 * 1000 } // 短期缓存
  });
};

// ✅ 推荐：及时清理相关缓存
const updateUserProfile = async (data) => {
  const result = await api.auth.updateUserInfo(data);
  // 清理相关缓存
  cacheManager.deleteByTags(['user']);
  return result;
};
```

### 9.4 网络适配规范

```javascript
// ✅ 推荐：在执行网络敏感操作前检查网络状态
const performLargeFileUpload = async (filePath) => {
  const suitable = networkMonitor.isNetworkSuitableFor('large_download');

  if (!suitable.suitable) {
    const confirm = await wx.showModal({
      title: '网络提示',
      content: suitable.reason + '，是否继续？'
    });

    if (!confirm.confirm) {
      return;
    }
  }

  return api.upload.file(filePath, {
    onProgress: (progress) => {
      this.setData({ uploadProgress: progress.progress });
    }
  });
};
```

## 10. 故障排查

### 10.1 常见问题

#### 问题1：请求失败，网络正常
**症状**：网络连接正常，但API请求失败
**排查步骤**：
1. 检查API地址配置是否正确
2. 检查请求头是否包含必要信息
3. 检查Token是否过期
4. 查看错误日志获取详细信息

```javascript
// 调试代码
console.log('API配置:', config.api);
console.log('当前Token:', await auth.getToken());
console.log('最近错误:', errorHandler.getErrorLogs(5));
```

#### 问题2：缓存未生效
**症状**：相同请求每次都发送网络请求
**排查步骤**：
1. 检查缓存是否启用
2. 检查缓存配置是否正确
3. 检查缓存键是否冲突

```javascript
// 调试代码
console.log('缓存统计:', cacheManager.getStats());
console.log('缓存大小:', await cacheManager.size());
```

#### 问题3：请求队列阻塞
**症状**：新请求长时间等待，无法发送
**排查步骤**：
1. 检查队列状态
2. 检查是否有请求卡死
3. 检查并发配置是否合理

```javascript
// 调试代码
console.log('队列状态:', requestQueue.getStatus());
console.log('活跃请求:', requestQueue.getActiveRequests());
console.log('排队请求:', requestQueue.getQueuedRequests());
```

### 10.2 性能问题排查

#### 问题1：请求响应缓慢
**排查步骤**：
1. 检查网络质量
2. 检查服务器响应时间
3. 检查请求大小
4. 检查并发数设置

```javascript
// 性能分析
const stats = apiClient.getStats();
console.log('平均响应时间:', stats.averageResponseTime);

const networkQuality = networkMonitor.getNetworkQuality();
console.log('网络质量:', networkQuality.grade, networkQuality.score);
```

#### 问题2：内存占用过高
**排查步骤**：
1. 检查缓存大小
2. 检查是否有内存泄漏
3. 调整缓存配置

```javascript
// 内存使用分析
const cacheStats = cacheManager.getStats();
console.log('缓存命中率:', cacheStats.hitRate);
console.log('内存缓存大小:', cacheStats.memorySize);

// 清理缓存
cacheManager.cleanup();
```

### 10.3 调试技巧

#### 启用详细日志
```javascript
// 开发环境启用详细日志
if (__DEV__) {
  errorHandler.setConfig({ showDetails: true });

  // 监听所有网络事件
  apiClient.on('request:start', (data) => {
    console.log('🚀 请求开始:', data.config.url);
  });

  apiClient.on('request:success', (data) => {
    console.log('✅ 请求成功:', data.config.url, data.duration + 'ms');
  });

  apiClient.on('request:error', (error) => {
    console.log('❌ 请求失败:', error.config?.url, error.message);
  });
}
```

#### 性能监控面板
```javascript
// 在页面中添加性能监控面板
Page({
  data: {
    showDebugPanel: __DEV__
  },

  onShow() {
    if (__DEV__) {
      this.updateDebugInfo();
      this.debugTimer = setInterval(() => {
        this.updateDebugInfo();
      }, 5000);
    }
  },

  onHide() {
    if (this.debugTimer) {
      clearInterval(this.debugTimer);
    }
  },

  updateDebugInfo() {
    const debugInfo = {
      api: apiClient.getStats(),
      network: networkMonitor.getCurrentStatus(),
      queue: requestQueue.getStatus()
    };

    this.setData({ debugInfo });
  }
});
```

---

## 总结

五好伴学微信小程序网络层架构提供了完整的网络请求解决方案，包括：

- **统一的API管理**：标准化的请求处理流程
- **智能缓存机制**：提升应用性能和用户体验
- **健壮的错误处理**：全面的错误捕获和恢复机制
- **网络状态适配**：根据网络条件智能调整策略
- **性能监控体系**：全方位的性能跟踪和优化

通过合理使用这些组件和遵循最佳实践，可以构建出高性能、高可靠性的微信小程序网络层。

如需更多技术支持，请参考项目源码或联系开发团队。

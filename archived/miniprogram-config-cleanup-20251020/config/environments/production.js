// 五好伴学小程序 - 生产环境配置
// Production Environment Configuration

module.exports = {
  // 环境标识
  environment: 'production',
  debug: false,
  version: '1.0.0',

  // API 配置
  api: {
    // 生产环境API地址
    baseUrl: 'https://api.wuhao-tutor.com',
    // API 版本
    version: 'v1',
    // 请求超时时间 (毫秒)
    timeout: 10000,
    // 重试次数
    retryCount: 3,
    // 重试间隔 (毫秒)
    retryDelay: 1000,
    // 关闭请求日志
    enableLog: false,
    // 生产环境关闭Mock
    enableMock: false,
  },

  // WebSocket 配置
  websocket: {
    url: 'wss://ws.wuhao-tutor.com',
    heartbeat: 30000,
    reconnectInterval: 5000,
    maxReconnectAttempts: 3,
  },

  // 文件上传配置
  upload: {
    // 生产环境使用CDN
    baseUrl: 'https://cdn.wuhao-tutor.com/upload',
    // 允许的文件类型
    allowedTypes: ['image/jpeg', 'image/png', 'image/webp'],
    // 单个文件最大尺寸 (字节)
    maxFileSize: 10 * 1024 * 1024, // 10MB
    // 图片压缩质量 (0-1)
    compressQuality: 0.8,
    // 图片最大宽度
    maxWidth: 1920,
    // 图片最大高度
    maxHeight: 1920,
    // 启用压缩优化性能
    enableCompress: true,
  },

  // 缓存配置
  cache: {
    // 缓存前缀
    prefix: 'wuhao_prod_',
    // 生产环境缓存时间较长
    defaultTTL: 5 * 60 * 1000, // 5分钟
    userInfoTTL: 24 * 60 * 60 * 1000, // 24小时
    staticDataTTL: 60 * 60 * 1000, // 1小时
    // 启用缓存
    enabled: true,
    // 最大缓存条目数
    maxItems: 200,
  },

  // 用户认证配置
  auth: {
    tokenKey: 'auth_token',
    userInfoKey: 'user_info',
    roleKey: 'user_role',
    // 生产环境检查间隔
    checkInterval: 5 * 60 * 1000, // 5分钟
    // 关闭自动登录
    autoLogin: false,
    // 生产环境token过期时间
    tokenExpires: 7 * 24 * 60 * 60 * 1000, // 7天
  },

  // 小程序特定配置
  miniprogram: {
    appId: 'wx2a8b340606664785',
    // 生产环境分享配置
    share: {
      title: '五好伴学 - AI智能学习助手',
      desc: '让学习更高效，让成长更快乐',
      imageUrl: '/assets/images/share-logo.png',
    },
    // 生产环境权限控制
    permissions: {
      camera: true,
      album: true,
      location: false, // 生产环境按需启用
      microphone: true,
      notification: true,
    },
  },

  // 日志配置
  log: {
    // 生产环境只记录警告和错误
    level: 'warn',
    console: false,
    remote: true, // 生产环境启用远程日志
    remoteUrl: 'https://api.wuhao-tutor.com/api/v1/logs/report',
    maxLocalLogs: 100,
    // 关闭详细日志
    enablePerformance: false,
    enableNetwork: false,
    enableUserAction: true, // 保留用户行为日志用于分析
  },

  // 错误处理配置
  error: {
    // 生产环境隐藏错误详情
    showDetails: false,
    report: true, // 生产环境启用错误上报
    reportUrl: 'https://api.wuhao-tutor.com/api/v1/errors/report',
    // 生产环境重试配置
    retry: {
      networkRetryCount: 3,
      serverRetryCount: 1,
      retryBackoffMultiplier: 2,
    },
    // 启用错误边界
    enableErrorBoundary: true,
  },

  // 性能监控配置
  performance: {
    enabled: true,
    sampleRate: 0.1, // 生产环境10%采样
    reportUrl: 'https://api.wuhao-tutor.com/api/v1/performance/report',
    // 生产环境监控关键指标
    metrics: {
      pageLoadTime: true,
      apiRequestTime: true,
      renderTime: false,
      memoryUsage: false,
      fpsMonitor: false,
    },
    // 性能阈值配置
    thresholds: {
      pageLoadTime: 2000, // 2秒
      apiRequestTime: 3000, // 3秒
      renderTime: 50, // 50ms
      memoryUsage: 50 * 1024 * 1024, // 50MB
      fps: 30,
    },
  },

  // 埋点配置
  analytics: {
    enabled: true,
    reportUrl: 'https://api.wuhao-tutor.com/api/v1/analytics/report',
    // 生产环境埋点配置
    autoTrack: {
      pageView: true,
      pageStayTime: true,
      click: false, // 生产环境关闭点击埋点减少数据量
      share: true,
      error: true,
      performance: true,
    },
    // 生产环境批量上报
    batchSize: 10,
    batchTimeout: 5000,
  },

  // 功能开关
  features: {
    // 生产环境功能配置
    voiceInput: true,
    imageUpload: true,
    offlineMode: false, // 生产环境暂时关闭离线模式
    push: true,
    share: true,
    favorite: true,
    search: true,
    darkMode: true,
    // 生产环境关闭调试功能
    debugPanel: false,
    mockData: false,
    apiTest: false,
    performanceMonitor: false,
  },

  // 第三方服务配置
  thirdParty: {
    // 地图服务
    map: {
      key: 'PROD_MAP_KEY_REPLACE_WITH_ACTUAL',
      type: 'tencent',
    },
    // 语音识别
    speech: {
      appId: 'PROD_SPEECH_APPID_REPLACE_WITH_ACTUAL',
      appKey: 'PROD_SPEECH_KEY_REPLACE_WITH_ACTUAL',
    },
    // 统计分析
    analytics: {
      appId: 'PROD_ANALYTICS_APPID_REPLACE_WITH_ACTUAL',
    },
  },

  // 安全配置
  security: {
    // 生产环境启用所有安全检查
    enableHttps: true,
    enableCsrf: true,
    enableXss: true,
    // API 签名验证
    enableSignature: true,
    // 数据加密
    enableEncryption: true,
  },

  // 数据库配置
  database: {
    name: 'wuhao_prod',
    version: 1,
    stores: ['user', 'homework', 'chat', 'cache'],
    // 生产环境数据保留策略
    retention: {
      logs: 3, // 3天
      cache: 0.5, // 12小时
      userData: 90, // 90天
    },
  },

  // 网络配置
  network: {
    // 生产环境网络超时设置
    timeout: {
      connect: 5000,
      read: 10000,
      write: 8000,
    },
    // 并发请求限制
    maxConcurrentRequests: 6,
    // 请求队列大小
    maxQueueSize: 20,
    // 启用请求去重
    enableDeduplication: true,
  },

  // UI 配置
  ui: {
    // 生产环境UI配置
    showBoundingBoxes: false,
    showFPS: false,
    showMemoryUsage: false,
    // 动画配置
    enableAnimations: true,
    animationDuration: 250, // 稍快的动画
    // 主题配置
    theme: 'auto', // 自动适应系统主题
  },

  // CDN 配置
  cdn: {
    baseUrl: 'https://cdn.wuhao-tutor.com',
    // 静态资源版本号
    version: '1.0.0',
    // 缓存策略
    cache: {
      images: 30 * 24 * 60 * 60, // 30天
      css: 7 * 24 * 60 * 60, // 7天
      js: 7 * 24 * 60 * 60, // 7天
    },
  },

  // 监控告警配置
  monitoring: {
    // 错误率阈值
    errorRateThreshold: 0.01, // 1%
    // 响应时间阈值
    responseTimeThreshold: 2000, // 2秒
    // 内存使用阈值
    memoryThreshold: 80, // 80%
    // 告警接收人
    alertReceivers: ['admin@wuhao-tutor.com'],
  },

  // 版本控制
  version: {
    // 当前版本
    current: '1.0.0',
    // 最小支持版本
    minimum: '1.0.0',
    // 强制更新版本
    forceUpdate: [],
    // 更新检查间隔
    checkInterval: 24 * 60 * 60 * 1000, // 24小时
  },
};

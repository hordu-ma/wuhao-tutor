// 五好伴学小程序 - 预发布环境配置
// Staging Environment Configuration

module.exports = {
  // 环境标识
  environment: 'staging',
  debug: false,
  version: '1.0.0-rc',

  // API 配置
  api: {
    // 预发布环境API地址
    baseUrl: 'https://staging-api.wuhao-tutor.com',
    // API 版本
    version: 'v1',
    // 请求超时时间 (毫秒)
    timeout: 12000,
    // 重试次数
    retryCount: 3,
    // 重试间隔 (毫秒)
    retryDelay: 1000,
    // 启用请求日志用于测试
    enableLog: true,
    // 预发布环境关闭Mock
    enableMock: false,
  },

  // WebSocket 配置
  websocket: {
    url: 'wss://staging-ws.wuhao-tutor.com',
    heartbeat: 30000,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
  },

  // 文件上传配置
  upload: {
    // 预发布环境使用测试CDN
    baseUrl: 'https://staging-cdn.wuhao-tutor.com/upload',
    // 允许的文件类型
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    // 单个文件最大尺寸 (字节)
    maxFileSize: 15 * 1024 * 1024, // 15MB - 比生产环境稍大便于测试
    // 图片压缩质量 (0-1)
    compressQuality: 0.85,
    // 图片最大宽度
    maxWidth: 1920,
    // 图片最大高度
    maxHeight: 1920,
    // 启用压缩
    enableCompress: true,
  },

  // 缓存配置
  cache: {
    // 缓存前缀
    prefix: 'wuhao_staging_',
    // 预发布环境缓存时间中等
    defaultTTL: 3 * 60 * 1000, // 3分钟
    userInfoTTL: 12 * 60 * 60 * 1000, // 12小时
    staticDataTTL: 30 * 60 * 1000, // 30分钟
    // 启用缓存
    enabled: true,
    // 最大缓存条目数
    maxItems: 150,
  },

  // 用户认证配置
  auth: {
    tokenKey: 'auth_token_staging',
    userInfoKey: 'user_info_staging',
    roleKey: 'user_role_staging',
    // 预发布环境检查间隔
    checkInterval: 3 * 60 * 1000, // 3分钟
    // 启用自动登录便于测试
    autoLogin: true,
    // 预发布环境token过期时间
    tokenExpires: 3 * 24 * 60 * 60 * 1000, // 3天
  },

  // 小程序特定配置
  miniprogram: {
    appId: 'wx2a8b340606664785',
    // 预发布环境分享配置
    share: {
      title: '五好伴学 - AI智能学习助手 (测试版)',
      desc: '让学习更高效，让成长更快乐 - 预发布版本',
      imageUrl: '/assets/images/share-logo-staging.png',
    },
    // 预发布环境权限配置
    permissions: {
      camera: true,
      album: true,
      location: true,
      microphone: true,
      notification: true,
    },
  },

  // 日志配置
  log: {
    // 预发布环境记录信息及以上级别
    level: 'info',
    console: false,
    remote: true, // 预发布环境启用远程日志
    remoteUrl: 'https://staging-api.wuhao-tutor.com/api/v1/logs/report',
    maxLocalLogs: 200,
    // 启用性能日志用于测试
    enablePerformance: true,
    enableNetwork: true,
    enableUserAction: true,
  },

  // 错误处理配置
  error: {
    // 预发布环境显示部分错误详情便于调试
    showDetails: true,
    report: true, // 预发布环境启用错误上报
    reportUrl: 'https://staging-api.wuhao-tutor.com/api/v1/errors/report',
    // 预发布环境重试配置
    retry: {
      networkRetryCount: 4,
      serverRetryCount: 2,
      retryBackoffMultiplier: 1.8,
    },
    // 启用错误边界
    enableErrorBoundary: true,
  },

  // 性能监控配置
  performance: {
    enabled: true,
    sampleRate: 0.5, // 预发布环境50%采样
    reportUrl: 'https://staging-api.wuhao-tutor.com/api/v1/performance/report',
    // 预发布环境监控主要指标
    metrics: {
      pageLoadTime: true,
      apiRequestTime: true,
      renderTime: true,
      memoryUsage: true,
      fpsMonitor: false,
    },
    // 性能阈值配置
    thresholds: {
      pageLoadTime: 2500, // 2.5秒
      apiRequestTime: 4000, // 4秒
      renderTime: 80, // 80ms
      memoryUsage: 80 * 1024 * 1024, // 80MB
      fps: 30,
    },
  },

  // 埋点配置
  analytics: {
    enabled: true,
    reportUrl: 'https://staging-api.wuhao-tutor.com/api/v1/analytics/report',
    // 预发布环境埋点配置
    autoTrack: {
      pageView: true,
      pageStayTime: true,
      click: true, // 预发布环境启用点击埋点用于测试
      share: true,
      error: true,
      performance: true,
    },
    // 预发布环境批量上报
    batchSize: 5,
    batchTimeout: 3000,
  },

  // 功能开关
  features: {
    // 预发布环境功能配置
    voiceInput: true,
    imageUpload: true,
    offlineMode: true, // 预发布环境测试离线模式
    push: false, // 预发布环境关闭推送避免干扰用户
    share: true,
    favorite: true,
    search: true,
    darkMode: true,
    // 预发布环境保留部分调试功能
    debugPanel: false,
    mockData: false,
    apiTest: true, // 保留API测试功能
    performanceMonitor: true,
  },

  // 开发工具配置（预发布环境保留部分调试能力）
  devtools: {
    enablePanel: false,
    enableApiDebug: true,
    enablePerformancePanel: true,
    enableNetworkPanel: true,
    enableLogPanel: false,
    hotReload: {
      enabled: false,
      port: 0,
      watchFiles: [],
    },
  },

  // 第三方服务配置
  thirdParty: {
    // 地图服务
    map: {
      key: 'STAGING_MAP_KEY_REPLACE_WITH_ACTUAL',
      type: 'tencent',
    },
    // 语音识别
    speech: {
      appId: 'STAGING_SPEECH_APPID_REPLACE_WITH_ACTUAL',
      appKey: 'STAGING_SPEECH_KEY_REPLACE_WITH_ACTUAL',
    },
    // 统计分析
    analytics: {
      appId: 'STAGING_ANALYTICS_APPID_REPLACE_WITH_ACTUAL',
    },
  },

  // 安全配置
  security: {
    // 预发布环境启用主要安全检查
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
    name: 'wuhao_staging',
    version: 1,
    stores: ['user', 'homework', 'chat', 'cache'],
    // 预发布环境数据保留策略
    retention: {
      logs: 5, // 5天
      cache: 1, // 1天
      userData: 60, // 60天
    },
  },

  // 网络配置
  network: {
    // 预发布环境网络超时设置
    timeout: {
      connect: 8000,
      read: 12000,
      write: 10000,
    },
    // 并发请求限制
    maxConcurrentRequests: 8,
    // 请求队列大小
    maxQueueSize: 30,
    // 启用请求去重
    enableDeduplication: true,
  },

  // UI 配置
  ui: {
    // 预发布环境UI配置
    showBoundingBoxes: false,
    showFPS: false,
    showMemoryUsage: false,
    // 动画配置
    enableAnimations: true,
    animationDuration: 280,
    // 主题配置
    theme: 'auto',
  },

  // CDN 配置
  cdn: {
    baseUrl: 'https://staging-cdn.wuhao-tutor.com',
    // 静态资源版本号
    version: '1.0.0-rc',
    // 缓存策略
    cache: {
      images: 7 * 24 * 60 * 60, // 7天
      css: 1 * 24 * 60 * 60, // 1天
      js: 1 * 24 * 60 * 60, // 1天
    },
  },

  // 测试配置
  testing: {
    // 预发布环境特有的测试配置
    enableTestMode: true,
    mockUserData: false,
    skipAnimations: false,
    autoLogin: {
      enabled: true,
      testUsers: [
        {
          role: 'student',
          username: 'test_student',
          password: 'test123456',
        },
        {
          role: 'parent',
          username: 'test_parent',
          password: 'test123456',
        },
        {
          role: 'teacher',
          username: 'test_teacher',
          password: 'test123456',
        },
      ],
    },
  },

  // A/B 测试配置
  abTest: {
    enabled: true,
    experiments: [
      {
        name: 'homework_submit_flow',
        variants: ['original', 'optimized'],
        traffic: 0.5, // 50% 流量
      },
      {
        name: 'chat_interface',
        variants: ['bubble', 'card'],
        traffic: 0.3, // 30% 流量
      },
    ],
  },

  // 监控告警配置
  monitoring: {
    // 错误率阈值
    errorRateThreshold: 0.05, // 5% - 预发布环境阈值较高
    // 响应时间阈值
    responseTimeThreshold: 3000, // 3秒
    // 内存使用阈值
    memoryThreshold: 85, // 85%
    // 告警接收人
    alertReceivers: ['dev@wuhao-tutor.com', 'qa@wuhao-tutor.com'],
  },

  // 版本控制
  version: {
    // 当前版本
    current: '1.0.0-rc',
    // 最小支持版本
    minimum: '1.0.0-rc',
    // 强制更新版本
    forceUpdate: [],
    // 更新检查间隔
    checkInterval: 6 * 60 * 60 * 1000, // 6小时
  },

  // 数据收集配置
  dataCollection: {
    // 预发布环境数据收集配置
    enabled: true,
    // 用户行为数据
    userBehavior: true,
    // 性能数据
    performance: true,
    // 错误数据
    errors: true,
    // 崩溃数据
    crashes: true,
    // 隐私设置
    anonymizeUserData: true,
    // 数据保留期限
    retentionPeriod: 30, // 30天
  },
};

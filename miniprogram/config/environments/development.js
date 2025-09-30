// 五好伴学小程序 - 开发环境配置
// Development Environment Configuration

module.exports = {
  // 环境标识
  environment: 'development',
  debug: true,
  version: '1.0.0-dev',

  // API 配置
  api: {
    // 本地开发服务器地址
    baseUrl: 'http://localhost:8000',
    // API 版本
    version: 'v1',
    // 请求超时时间 (毫秒)
    timeout: 15000,
    // 重试次数
    retryCount: 2,
    // 重试间隔 (毫秒)
    retryDelay: 1000,
    // 是否启用请求日志
    enableLog: true,
    // Mock 数据开关
    enableMock: false,
  },

  // WebSocket 配置
  websocket: {
    url: 'ws://localhost:8001',
    heartbeat: 30000,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
  },

  // 文件上传配置
  upload: {
    // 开发环境使用本地上传服务
    baseUrl: 'http://localhost:8000/upload',
    // 允许的文件类型
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    // 单个文件最大尺寸 (字节) - 开发环境放宽限制
    maxFileSize: 20 * 1024 * 1024, // 20MB
    // 图片压缩质量 (0-1)
    compressQuality: 0.9, // 开发环境保持高质量
    // 图片最大宽度
    maxWidth: 2048,
    // 图片最大高度
    maxHeight: 2048,
    // 是否启用压缩
    enableCompress: false, // 开发环境关闭压缩便于调试
  },

  // 缓存配置
  cache: {
    // 缓存前缀
    prefix: 'wuhao_dev_',
    // 开发环境缓存时间较短便于调试
    defaultTTL: 2 * 60 * 1000, // 2分钟
    userInfoTTL: 10 * 60 * 1000, // 10分钟
    staticDataTTL: 5 * 60 * 1000, // 5分钟
    // 是否启用缓存
    enabled: true,
    // 最大缓存条目数
    maxItems: 100,
  },

  // 用户认证配置
  auth: {
    tokenKey: 'auth_token_dev',
    userInfoKey: 'user_info_dev',
    roleKey: 'user_role_dev',
    // 开发环境检查间隔较短
    checkInterval: 2 * 60 * 1000, // 2分钟
    // 是否启用自动登录
    autoLogin: true,
    // 开发环境token过期时间
    tokenExpires: 24 * 60 * 60 * 1000, // 24小时
  },

  // 小程序特定配置
  miniprogram: {
    appId: 'wx2a8b340606664785',
    // 开发环境分享配置
    share: {
      title: '五好伴学 - AI智能学习助手 (开发版)',
      desc: '让学习更高效，让成长更快乐',
      imageUrl: '/assets/images/share-logo-dev.png',
    },
    // 开发环境启用所有权限
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
    // 开发环境启用详细日志
    level: 'debug',
    console: true,
    remote: false, // 开发环境不上报远程日志
    remoteUrl: '',
    maxLocalLogs: 500,
    // 是否启用性能日志
    enablePerformance: true,
    // 是否启用网络日志
    enableNetwork: true,
    // 是否启用用户行为日志
    enableUserAction: true,
  },

  // 错误处理配置
  error: {
    // 开发环境显示详细错误信息
    showDetails: true,
    report: false, // 开发环境不上报错误
    reportUrl: '',
    // 开发环境重试配置更宽松
    retry: {
      networkRetryCount: 5,
      serverRetryCount: 3,
      retryBackoffMultiplier: 1.5,
    },
    // 是否启用错误边界
    enableErrorBoundary: true,
  },

  // 性能监控配置
  performance: {
    enabled: true,
    sampleRate: 1.0, // 开发环境100%采样
    reportUrl: '',
    // 开发环境监控所有指标
    metrics: {
      pageLoadTime: true,
      apiRequestTime: true,
      renderTime: true,
      memoryUsage: true,
      fpsMonitor: true,
    },
    // 性能阈值配置
    thresholds: {
      pageLoadTime: 3000, // 3秒
      apiRequestTime: 5000, // 5秒
      renderTime: 100, // 100ms
      memoryUsage: 100 * 1024 * 1024, // 100MB
      fps: 30,
    },
  },

  // 埋点配置
  analytics: {
    enabled: true,
    reportUrl: '',
    // 开发环境启用所有埋点
    autoTrack: {
      pageView: true,
      pageStayTime: true,
      click: true,
      share: true,
      error: true,
      performance: true,
    },
    // 开发环境实时上报
    batchSize: 1,
    batchTimeout: 0,
  },

  // 功能开关
  features: {
    // 开发环境启用所有功能
    voiceInput: true,
    imageUpload: true,
    offlineMode: true,
    push: false, // 开发环境关闭推送避免干扰
    share: true,
    favorite: true,
    search: true,
    darkMode: true,
    // 开发环境专用功能
    debugPanel: true,
    mockData: true,
    apiTest: true,
    performanceMonitor: true,
  },

  // 开发工具配置
  devtools: {
    // 是否启用开发面板
    enablePanel: true,
    // 是否启用API调试
    enableApiDebug: true,
    // 是否启用性能监控面板
    enablePerformancePanel: true,
    // 是否启用网络面板
    enableNetworkPanel: true,
    // 是否启用日志面板
    enableLogPanel: true,
    // 热重载配置
    hotReload: {
      enabled: true,
      port: 8080,
      watchFiles: ['pages/**/*.js', 'components/**/*.js', 'utils/**/*.js'],
    },
  },

  // Mock 数据配置
  mock: {
    enabled: false, // 默认关闭，需要时手动启用
    delay: 500, // 模拟网络延迟
    // Mock API 映射
    apis: {
      '/api/v1/auth/login': '/mock/auth/login.json',
      '/api/v1/homework/list': '/mock/homework/list.json',
      '/api/v1/chat/send': '/mock/chat/send.json',
    },
  },

  // 第三方服务配置
  thirdParty: {
    // 地图服务
    map: {
      key: 'dev_map_key_placeholder',
      type: 'tencent', // tencent | baidu | amap
    },
    // 语音识别
    speech: {
      appId: 'dev_speech_appid_placeholder',
      appKey: 'dev_speech_key_placeholder',
    },
    // 统计分析
    analytics: {
      appId: 'dev_analytics_appid_placeholder',
    },
  },

  // 安全配置
  security: {
    // 开发环境安全检查相对宽松
    enableHttps: false,
    enableCsrf: false,
    enableXss: true,
    // API 签名验证
    enableSignature: false,
    // 数据加密
    enableEncryption: false,
  },

  // 数据库配置（如果使用本地存储）
  database: {
    name: 'wuhao_dev',
    version: 1,
    stores: ['user', 'homework', 'chat', 'cache'],
    // 开发环境数据保留策略
    retention: {
      logs: 7, // 7天
      cache: 1, // 1天
      userData: 30, // 30天
    },
  },

  // 网络配置
  network: {
    // 开发环境网络超时设置
    timeout: {
      connect: 10000,
      read: 15000,
      write: 10000,
    },
    // 并发请求限制
    maxConcurrentRequests: 10,
    // 请求队列大小
    maxQueueSize: 50,
    // 是否启用请求去重
    enableDeduplication: true,
  },

  // UI 配置
  ui: {
    // 开发环境UI调试配置
    showBoundingBoxes: false,
    showFPS: false,
    showMemoryUsage: false,
    // 动画配置
    enableAnimations: true,
    animationDuration: 300,
    // 主题配置
    theme: 'light', // light | dark | auto
  },
};

// 五好伴学小程序配置文件模板
// 复制此文件为 index.js 并填入正确的配置值

const config = {
  // 环境配置
  // 可选值: 'development' | 'staging' | 'production'
  // 修改为 'production' 以连接生产环境
  environment: 'production', // 默认使用生产环境进行测试
  debug: false, // 生产环境关闭调试
  version: '1.0.0',

  // API 配置
  api: {
    // 后端 API 基础地址
    // 开发环境: 'http://localhost:8000'
    // 生产环境: 'https://www.horsduroot.com'
    baseUrl: 'https://www.horsduroot.com', // 生产环境API地址 - 使用域名
    // API 版本
    version: 'v1',
    // 请求超时时间 (毫秒) - 提高到120秒以支持图片上传和AI处理
    timeout: 120000,
    // 重试次数
    retryCount: 3,
    // 重试间隔 (毫秒)
    retryDelay: 1000,
  },

  // 文件上传配置
  upload: {
    // 阿里云 OSS 或其他云存储基础地址
    ossBaseUrl: 'https://your-bucket.oss-cn-hangzhou.aliyuncs.com',
    // 允许的文件类型
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    // 单个文件最大尺寸 (字节)
    maxFileSize: 10 * 1024 * 1024, // 10MB
    // 图片压缩质量 (0-1)
    compressQuality: 0.8,
    // 图片最大宽度
    maxWidth: 1920,
    // 图片最大高度
    maxHeight: 1920,
  },

  // 缓存配置
  cache: {
    // 缓存前缀
    prefix: 'wuhao_',
    // 默认缓存时间 (毫秒)
    defaultTTL: 5 * 60 * 1000, // 5分钟
    // 用户信息缓存时间
    userInfoTTL: 24 * 60 * 60 * 1000, // 24小时
    // 静态数据缓存时间
    staticDataTTL: 60 * 60 * 1000, // 1小时
  },

  // Markdown 渲染配置
  markdown: {
    // 使用 Towxml 渲染器（AB 测试开关）
    useTowxml: false, // Towxml 3.x npm 构建问题，暂时禁用使用旧渲染器
    // 降级策略：Towxml 失败时自动降级到旧渲染器
    enableFallback: true,
    // Towxml 主题
    towxmlTheme: 'light', // light | dark
  },

  // 用户认证配置
  auth: {
    // Access Token 存储键名
    tokenKey: 'auth_token',
    // Refresh Token 存储键名
    refreshTokenKey: 'refresh_token',
    // 用户信息存储键名
    userInfoKey: 'user_info',
    // 用户角色存储键名
    roleKey: 'user_role',
    // 会话ID存储键名
    sessionIdKey: 'session_id',
    // Token 过期时间检查间隔 (毫秒)
    checkInterval: 5 * 60 * 1000, // 5分钟
    // Token 刷新提前时间 (毫秒) - 在过期前5分钟刷新
    refreshBeforeExpire: 5 * 60 * 1000,
  },

  // 小程序特定配置
  miniprogram: {
    // 小程序 AppID (需要替换)
    appId: 'wx2a8b340606664785',
    // 分享配置
    share: {
      title: '五好伴学 - AI智能学习助手',
      desc: '让学习更高效，让成长更快乐',
      imageUrl: '/assets/images/share-logo.png',
    },
    // tabBar 配置（注意：这些配置未被 app.json 实际引用）
    tabBar: {
      student: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png',
        },
        // 作业批改功能已移除，改用 learning（作业问答）模块
        // {
        //   pagePath: 'pages/homework/list/index',
        //   text: '作业',
        //   iconPath: '/assets/icons/homework.png',
        //   selectedIconPath: '/assets/icons/homework-active.png',
        // },
        {
          pagePath: 'pages/mistakes/list/index',
          text: '错题本',
          iconPath: '/assets/icons/homework.png',
          selectedIconPath: '/assets/icons/homework-active.png',
        },
        {
          pagePath: 'pages/learning/index/index',
          text: '作业问答',
          iconPath: '/assets/icons/chat.png',
          selectedIconPath: '/assets/icons/chat-active.png',
        },
        {
          pagePath: 'pages/analysis/report/index',
          text: '报告',
          iconPath: '/assets/icons/report.png',
          selectedIconPath: '/assets/icons/report-active.png',
        },
        {
          pagePath: 'pages/profile/index/index',
          text: '我的',
          iconPath: '/assets/icons/profile.png',
          selectedIconPath: '/assets/icons/profile-active.png',
        },
      ],
      parent: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png',
        },
        {
          pagePath: 'pages/analysis/progress/index',
          text: '学情',
          iconPath: '/assets/icons/progress.png',
          selectedIconPath: '/assets/icons/progress-active.png',
        },
        // 作业批改功能已移除
        // {
        //   pagePath: 'pages/homework/list/index',
        //   text: '作业',
        //   iconPath: '/assets/icons/homework.png',
        //   selectedIconPath: '/assets/icons/homework-active.png',
        // },
        {
          pagePath: 'pages/profile/index/index',
          text: '我的',
          iconPath: '/assets/icons/profile.png',
          selectedIconPath: '/assets/icons/profile-active.png',
        },
      ],
      teacher: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png',
        },
        // 作业批改功能已移除
        // {
        //   pagePath: 'pages/homework/list/index',
        //   text: '作业',
        //   iconPath: '/assets/icons/homework.png',
        //   selectedIconPath: '/assets/icons/homework-active.png',
        // },
        {
          pagePath: 'pages/analysis/report/index',
          text: '分析',
          iconPath: '/assets/icons/analysis.png',
          selectedIconPath: '/assets/icons/analysis-active.png',
        },
        {
          pagePath: 'pages/profile/index/index',
          text: '我的',
          iconPath: '/assets/icons/profile.png',
          selectedIconPath: '/assets/icons/profile-active.png',
        },
      ],
    },
  },

  // UI 主题配置
  theme: {
    // 主色调
    primaryColor: '#1890ff',
    // 成功色
    successColor: '#52c41a',
    // 警告色
    warningColor: '#faad14',
    // 错误色
    errorColor: '#f5222d',
    // 文字颜色
    textColor: '#333333',
    // 次要文字颜色
    textColorSecondary: '#666666',
    // 占位文字颜色
    textColorPlaceholder: '#999999',
    // 背景颜色
    backgroundColor: '#f5f5f5',
    // 边框颜色
    borderColor: '#d9d9d9',
    // 圆角大小
    borderRadius: '8rpx',
    // 阴影
    boxShadow: '0 2rpx 8rpx rgba(0, 0, 0, 0.1)',
  },

  // 功能开关
  features: {
    // 语音输入
    voiceInput: true,
    // 图片上传
    imageUpload: true,
    // 离线模式
    offlineMode: false,
    // 推送通知
    push: true,
    // 分享功能
    share: true,
    // 收藏功能
    favorite: true,
    // 搜索功能
    search: true,
    // 深色模式
    darkMode: false,
  },

  // 分页配置
  pagination: {
    // 默认页面大小
    defaultPageSize: 20,
    // 最大页面大小
    maxPageSize: 100,
    // 加载更多阈值
    loadMoreThreshold: 3,
  },

  // 错误处理配置
  error: {
    // 是否显示错误详情
    showDetails: true,
    // 错误上报开关（生产环境禁用以避免干扰）
    report: false,
    // 错误上报地址
    reportUrl: '/api/v1/errors/report',
    // 重试配置
    retry: {
      // 网络错误重试次数
      networkRetryCount: 3,
      // 服务器错误重试次数
      serverRetryCount: 1,
      // 重试间隔倍数
      retryBackoffMultiplier: 2,
    },
  },

  // 性能监控配置
  performance: {
    // 是否开启性能监控
    enabled: true,
    // 采样率 (0-1)
    sampleRate: 0.1,
    // 上报地址
    reportUrl: '/api/v1/performance/report',
    // 监控指标
    metrics: {
      // 页面加载时间
      pageLoadTime: true,
      // API 请求时间
      apiRequestTime: true,
      // 渲染时间
      renderTime: true,
      // 内存使用
      memoryUsage: false,
    },
  },

  // 日志配置
  log: {
    // 日志级别: 'debug' | 'info' | 'warn' | 'error'
    level: 'debug',
    // 是否打印到控制台
    console: true,
    // 是否上报服务器
    remote: false,
    // 远程日志上报地址
    remoteUrl: '/api/v1/logs/report',
    // 本地日志最大条数
    maxLocalLogs: 1000,
  },

  // 埋点配置
  analytics: {
    // 是否开启埋点
    enabled: true,
    // 埋点上报地址
    reportUrl: '/api/v1/analytics/report',
    // 自动埋点事件
    autoTrack: {
      // 页面访问
      pageView: true,
      // 页面停留时间
      pageStayTime: true,
      // 点击事件
      click: false,
      // 分享事件
      share: true,
      // 错误事件
      error: true,
    },
  },
};

// 根据环境动态调整配置
if (config.environment === 'production') {
  // 生产环境配置
  config.debug = false;
  config.log.level = 'warn';
  config.log.console = false;
  config.log.remote = true;
  config.error.showDetails = false;
  config.performance.sampleRate = 0.1; // 生产环境降低采样率

  console.log('🚀 运行于生产环境模式:', config.api.baseUrl);
} else if (config.environment === 'staging') {
  // 预发布环境配置
  config.debug = false;
  config.log.level = 'info';
  config.performance.sampleRate = 0.5;

  console.log('🧪 运行于预发布环境模式:', config.api.baseUrl);
} else {
  // 开发环境配置
  console.log('🛠️ 运行于开发环境模式:', config.api.baseUrl);
}

module.exports = config;

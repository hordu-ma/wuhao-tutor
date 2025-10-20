// 五好伴学小程序配置文件模板
// 复制此文件为 index.js 并填入正确的配置值
// Configuration Template - Copy this file to index.js and fill in actual values

// 环境配置导入
const developmentConfig = require('./environments/development.js');
const stagingConfig = require('./environments/staging.js');
const productionConfig = require('./environments/production.js');

// 当前环境 - 可通过环境变量或手动设置
// Current environment - can be set via environment variable or manually
const currentEnv = process.env.NODE_ENV || 'development'; // development | staging | production

// 环境配置映射
const envConfigs = {
  development: developmentConfig,
  staging: stagingConfig,
  production: productionConfig,
};

// 获取当前环境配置
const envConfig = envConfigs[currentEnv] || developmentConfig;

// 基础配置 - 所有环境通用
const baseConfig = {
  // 应用信息
  app: {
    name: '五好伴学',
    version: '1.0.0',
    description: 'K12 AI学情管理平台微信小程序',
    author: 'Liguo Ma <maliguo@outlook.com>',
    homepage: 'https://wuhao-tutor.com',
  },

  // 小程序基础信息
  miniprogram: {
    // ⚠️ 重要：请替换为您的小程序 AppID
    appId: 'wx2a8b340606664785', // 请替换为实际的小程序AppID
    name: '五好伴学',
    version: '1.0.0',

    // 分享默认配置
    share: {
      title: '五好伴学 - AI智能学习助手',
      desc: '让学习更高效，让成长更快乐',
      imageUrl: '/assets/images/share-logo.png',
    },

    // 不同角色的 tabBar 配置
    tabBar: {
      // 学生端 tabBar
      student: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png',
        },
        {
          pagePath: 'pages/homework/list/index',
          text: '作业',
          iconPath: '/assets/icons/homework.png',
          selectedIconPath: '/assets/icons/homework-active.png',
        },
        {
          pagePath: 'pages/chat/index/index',
          text: '问答',
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

      // 家长端 tabBar
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
        {
          pagePath: 'pages/homework/list/index',
          text: '作业',
          iconPath: '/assets/icons/homework.png',
          selectedIconPath: '/assets/icons/homework-active.png',
        },
        {
          pagePath: 'pages/profile/index/index',
          text: '我的',
          iconPath: '/assets/icons/profile.png',
          selectedIconPath: '/assets/icons/profile-active.png',
        },
      ],

      // 教师端 tabBar
      teacher: [
        {
          pagePath: 'pages/index/index',
          text: '首页',
          iconPath: '/assets/icons/home.png',
          selectedIconPath: '/assets/icons/home-active.png',
        },
        {
          pagePath: 'pages/homework/list/index',
          text: '作业',
          iconPath: '/assets/icons/homework.png',
          selectedIconPath: '/assets/icons/homework-active.png',
        },
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

  // API 配置
  api: {
    // ⚠️ 重要：请替换为您的后端 API 地址
    baseUrl: 'https://localhost:8000', // 请替换为实际的后端地址
    version: 'v1',
    timeout: 10000,
    retryCount: 3,
    retryDelay: 1000,
  },

  // 文件上传配置
  upload: {
    // ⚠️ 重要：请替换为您的文件上传服务地址
    baseUrl: 'https://your-upload-service.com', // 请替换为实际的上传地址
    allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    maxFileSize: 10 * 1024 * 1024, // 10MB
    compressQuality: 0.8,
    maxWidth: 1920,
    maxHeight: 1920,
  },

  // 缓存配置
  cache: {
    prefix: 'wuhao_',
    defaultTTL: 5 * 60 * 1000, // 5分钟
    userInfoTTL: 24 * 60 * 60 * 1000, // 24小时
    staticDataTTL: 60 * 60 * 1000, // 1小时
  },

  // 用户认证配置
  auth: {
    tokenKey: 'auth_token',
    userInfoKey: 'user_info',
    roleKey: 'user_role',
    checkInterval: 5 * 60 * 1000, // 5分钟
  },

  // UI 主题配置
  theme: {
    primaryColor: '#1890ff',
    successColor: '#52c41a',
    warningColor: '#faad14',
    errorColor: '#f5222d',
    textColor: '#333333',
    textColorSecondary: '#666666',
    textColorPlaceholder: '#999999',
    backgroundColor: '#f5f5f5',
    borderColor: '#d9d9d9',
    borderRadius: '8rpx',
    boxShadow: '0 2rpx 8rpx rgba(0, 0, 0, 0.1)',
  },

  // 功能开关
  features: {
    voiceInput: true,
    imageUpload: true,
    offlineMode: false,
    push: true,
    share: true,
    favorite: true,
    search: true,
    darkMode: false,
  },

  // 分页配置
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
    loadMoreThreshold: 3,
  },

  // 第三方服务配置
  thirdParty: {
    // ⚠️ 重要：请替换为您的实际服务密钥
    map: {
      key: 'YOUR_MAP_KEY_HERE', // 请替换为实际的地图服务密钥
      type: 'tencent', // tencent | baidu | amap
    },
    speech: {
      appId: 'YOUR_SPEECH_APPID_HERE', // 请替换为实际的语音服务AppID
      appKey: 'YOUR_SPEECH_KEY_HERE', // 请替换为实际的语音服务密钥
    },
    analytics: {
      appId: 'YOUR_ANALYTICS_APPID_HERE', // 请替换为实际的统计分析AppID
    },
  },

  // 错误处理配置
  error: {
    showDetails: true,
    report: true,
    reportUrl: '/api/v1/errors/report',
    retry: {
      networkRetryCount: 3,
      serverRetryCount: 1,
      retryBackoffMultiplier: 2,
    },
  },

  // 性能监控配置
  performance: {
    enabled: true,
    sampleRate: 0.1,
    reportUrl: '/api/v1/performance/report',
    metrics: {
      pageLoadTime: true,
      apiRequestTime: true,
      renderTime: true,
      memoryUsage: false,
    },
  },

  // 日志配置
  log: {
    level: 'debug',
    console: true,
    remote: false,
    remoteUrl: '/api/v1/logs/report',
    maxLocalLogs: 1000,
  },

  // 埋点配置
  analytics: {
    enabled: true,
    reportUrl: '/api/v1/analytics/report',
    autoTrack: {
      pageView: true,
      pageStayTime: true,
      click: false,
      share: true,
      error: true,
    },
  },
};

// 合并环境配置和基础配置
// Merge environment config with base config
const config = {
  ...baseConfig,
  ...envConfig,
  // 确保重要配置不被覆盖
  app: { ...baseConfig.app, ...envConfig.app },
  miniprogram: { ...baseConfig.miniprogram, ...envConfig.miniprogram },
  api: { ...baseConfig.api, ...envConfig.api },
  upload: { ...baseConfig.upload, ...envConfig.upload },
  theme: { ...baseConfig.theme, ...envConfig.theme },
  features: { ...baseConfig.features, ...envConfig.features },
  thirdParty: { ...baseConfig.thirdParty, ...envConfig.thirdParty },
};

// 配置验证函数
function validateConfig(config) {
  const requiredFields = [
    'miniprogram.appId',
    'api.baseUrl',
  ];

  const missingFields = requiredFields.filter(field => {
    const keys = field.split('.');
    let value = config;
    for (const key of keys) {
      value = value[key];
      if (value === undefined || value === null) {
        return true;
      }
    }
    return false;
  });

  if (missingFields.length > 0) {
    console.warn('⚠️ 配置文件缺少必要字段:', missingFields);
    console.warn('请检查 config/index.js 文件并补全配置');
  }

  // 检查是否使用了默认值
  const defaultValues = [
    'wx2a8b340606664785', // 默认AppID
    'https://localhost:8000', // 默认API地址
    'YOUR_MAP_KEY_HERE',
    'YOUR_SPEECH_APPID_HERE',
    'YOUR_ANALYTICS_APPID_HERE',
  ];

  const usedDefaults = [];
  const configStr = JSON.stringify(config);
  defaultValues.forEach(defaultValue => {
    if (configStr.includes(defaultValue)) {
      usedDefaults.push(defaultValue);
    }
  });

  if (usedDefaults.length > 0) {
    console.warn('⚠️ 检测到配置文件中仍使用默认值:');
    usedDefaults.forEach(value => {
      console.warn(`  - ${value}`);
    });
    console.warn('请替换为实际的配置值');
  }

  return missingFields.length === 0 && usedDefaults.length === 0;
}

// 开发环境下验证配置
if (config.debug) {
  validateConfig(config);
}

// 配置说明注释
config._comments = {
  setup: [
    '📝 配置说明:',
    '1. 复制 config/index.example.js 为 config/index.js',
    '2. 替换 miniprogram.appId 为您的小程序AppID',
    '3. 替换 api.baseUrl 为您的后端API地址',
    '4. 根据需要配置第三方服务密钥',
    '5. 根据环境调整相关配置项',
    '',
    '🔧 环境切换:',
    '- 开发环境: NODE_ENV=development',
    '- 预发布环境: NODE_ENV=staging',
    '- 生产环境: NODE_ENV=production',
    '',
    '⚠️ 安全提醒:',
    '- 不要在代码中硬编码敏感信息',
    '- 不要提交包含真实密钥的配置文件',
    '- 使用环境变量管理敏感配置',
  ],
};

module.exports = config;

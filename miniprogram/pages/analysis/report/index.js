// 学习报告页面逻辑
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const api = require('../../../api/index.js');
const { authManager } = require('../../../utils/auth.js');

// 难度等级映射
const DIFFICULTY_MAP = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
  expert: '专家',
};

// 星期映射
const WEEKDAY_MAP = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

// 学科映射
const SUBJECT_MAP = {
  math: '数学',
  chinese: '语文',
  english: '英语',
  physics: '物理',
  chemistry: '化学',
  biology: '生物',
  politics: '政治',
  history: '历史',
  geography: '地理',
  other: '其他',
};

const pageObject = {
  data: {
    // API状态管理
    apiStatus: 'loading', // loading | error | empty | success
    errorMessage: '',

    // 时间范围
    timeRange: '30d',
    timeRangeOptions: [
      { text: '最近7天', value: '7d' },
      { text: '最近30天', value: '30d' },
      { text: '最近90天', value: '90d' },
    ],

    // 页面状态
    loading: true,
    hasData: false,

    // 知识点数据（保留用于诊断组件）
    knowledgePoints: [],

    // 学情分析数据
    analytics: {
      user_id: '',
      total_questions: 0,
      total_sessions: 0,
      subject_stats: [],
      learning_pattern: {},
      avg_rating: 0,
      positive_feedback_rate: 0,
      improvement_suggestions: [],
      knowledge_gaps: [],
      last_analyzed_at: '',
    },

    // 学习模式格式化数据
    learningPattern: {
      most_active_hour: 0,
      most_active_day_text: '',
      avg_session_length: 0,
      preferred_difficulty_text: '',
    },

    // 格式化的更新时间
    formattedUpdateTime: '',

    // 时间范围文本
    timeRangeText: '30天',
    // 学情诊断报告数据已移除，保持简洁显示
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('学习报告页面加载');

    // 移除手动的登录检查,由 createGuardedPage 统一处理
    this.loadAnalyticsData();
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('学习报告页面显示');
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    console.log('下拉刷新学习报告');
    this.loadAnalyticsData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载学情分析数据
   */
  async loadAnalyticsData() {
    console.log('开始加载学情分析数据，时间范围:', this.data.timeRange);

    this.setData({
      loading: true,
      apiStatus: 'loading',
    });

    try {
      // 并行获取多个分析数据
      const [overviewResult, knowledgeResult, progressResult] = await Promise.allSettled([
        api.analysis.getOverview({ days: this.getTimeRangeDays() }),
        api.analysis.getMastery({ subject: 'all' }),
        api.analysis.getProgress({ days: this.getTimeRangeDays() }),
      ]);

      // 处理结果，兼容三种响应格式
      const extractData = result => {
        if (result.status !== 'fulfilled') return {};
        const response = result.value;

        console.log('📊 [extractData] response:', response);
        console.log('📊 [extractData] response.statusCode:', response?.statusCode);
        console.log('📊 [extractData] response.success:', response?.success);
        console.log('📊 [extractData] response.data:', response?.data);

        // 判断响应格式
        // Format 1: {data: {...}, statusCode: 200, header: {...}} - API客户端包装
        // Format 2: {success: true, message: "...", data: {...}} - 后端业务响应
        // Format 3: {items: [...], total: N} - 直接数据

        // Format 1: 检查 statusCode
        if (response && response.statusCode !== undefined) {
          const isSuccess = response.statusCode >= 200 && response.statusCode < 300;
          console.log('📊 [extractData] Format 1 (statusCode), isSuccess:', isSuccess);
          return isSuccess ? response.data || response : {};
        }

        // Format 2: 检查 success 字段（后端业务响应）
        if (response && response.success !== undefined) {
          console.log('📊 [extractData] Format 2 (success字段), success:', response.success);
          return response.success ? response.data || {} : {};
        }

        // Format 3: 直接数据（没有包装）
        console.log('📊 [extractData] Format 3 (直接数据)');
        return response !== null && response !== undefined ? response : {};
      };

      // 处理结果
      const analyticsData = {
        overview: extractData(overviewResult),
        knowledge: extractData(knowledgeResult),
        progress: extractData(progressResult),
        timestamp: Date.now(),
      };

      // 缓存数据
      const cacheKey = `analytics_${this.data.timeRange}`;
      wx.setStorageSync(cacheKey, analyticsData);

      this.processAnalyticsData(analyticsData);
    } catch (error) {
      console.error('加载学情分析数据失败:', error);
      this.setData({
        apiStatus: 'error',
        errorMessage: error.message || '加载失败，请重试',
        loading: false, // 关键：错误时也要结束加载状态
      });
    }
  },

  /**
   * 获取时间范围对应的天数
   */
  getTimeRangeDays() {
    const rangeMap = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
    };
    return rangeMap[this.data.timeRange] || 30;
  },

  /**
   * API重试
   */
  onApiRetry() {
    this.loadAnalyticsData();
  },

  /**
   * 处理学情分析数据
   */
  processAnalyticsData(analyticsData) {
    const { overview, knowledge, progress } = analyticsData;

    console.log('[DEBUG] processAnalyticsData 被调用');
    console.log('[DEBUG] overview:', overview);
    console.log('[DEBUG] knowledge:', knowledge);
    console.log('[DEBUG] progress:', progress);

    // 处理概览数据
    const processedOverview = {
      total_questions: overview?.total_questions || 0,
      total_sessions: overview?.total_sessions || 0,
      total_study_days: overview?.total_study_days || 0,
      avg_rating: overview?.avg_rating || 0,
      positive_feedback_rate: overview?.positive_feedback_rate || 0,
    };

    // 处理学科统计数据
    const subjectStats = overview?.subject_stats
      ? overview.subject_stats.map(item => ({
          ...item,
          subject_name: SUBJECT_MAP[item.subject] || item.subject,
        }))
      : [];

    // 处理知识点数据
    const knowledgePoints = knowledge?.knowledge_points || [];

    // 处理学习模式
    const learningPattern = this.formatLearningPattern(overview?.learning_pattern);

    // 格式化更新时间
    const formattedUpdateTime = this.formatUpdateTime(new Date().toISOString());

    const hasData = processedOverview.total_questions > 0 || processedOverview.total_sessions > 0;

    console.log('[DEBUG] hasData:', hasData);
    console.log('[DEBUG] total_questions:', processedOverview.total_questions);
    console.log('[DEBUG] total_sessions:', processedOverview.total_sessions);

    // 学情诊断报告组件已移除，不再生成 reportData

    this.setData({
      analytics: {
        ...processedOverview,
        subject_stats: subjectStats,
        learning_pattern: overview?.learning_pattern || {},
        improvement_suggestions: overview?.improvement_suggestions || [],
        knowledge_gaps: overview?.knowledge_gaps || [],
        last_analyzed_at: new Date().toISOString(),
        avg_rating: Number(processedOverview.avg_rating).toFixed(1),
      },
      knowledgePoints,
      learningPattern,
      formattedUpdateTime,
      apiStatus: hasData ? 'success' : 'empty',
      hasData,
      loading: false, // 关键：结束加载状态
    });

    console.log('[DEBUG] setData 完成，当前状态:');
    console.log('[DEBUG] - loading:', false);
    console.log('[DEBUG] - hasData:', hasData);
    console.log('[DEBUG] - apiStatus:', hasData ? 'success' : 'empty');

    // 图表和诊断组件已移除，仅保留简洁的学习概览和学习模式
  },

  /**
   * 获取友好的错误提示
   */
  getErrorMessage(error) {
    if (error && error.code) {
      switch (error.code) {
        case 401:
          return '请先登录';
        case 403:
          return '没有权限访问';
        case 404:
          return '数据不存在';
        case 500:
          return '服务器错误，请稍后重试';
        default:
          return '加载失败，请重试';
      }
    }

    if (!error || error.toString().includes('timeout')) {
      return '网络超时，请检查网络连接';
    }

    return '加载失败，请重试';
  },

  /**
   * 格式化学习模式数据
   */
  formatLearningPattern(pattern) {
    if (!pattern) {
      return {
        most_active_hour: 0,
        most_active_day_text: '未知',
        avg_session_length: 0,
        preferred_difficulty_text: '未知',
      };
    }

    return {
      most_active_hour: pattern.most_active_hour || 0,
      most_active_day_text: WEEKDAY_MAP[pattern.most_active_day] || '未知',
      avg_session_length: pattern.avg_session_length || 0,
      preferred_difficulty_text: DIFFICULTY_MAP[pattern.preferred_difficulty] || '未知',
    };
  },

  /**
   * 格式化更新时间
   */
  formatUpdateTime(timeStr) {
    if (!timeStr) return '未知';

    try {
      const date = new Date(timeStr);
      const now = new Date();
      const diff = now - date;

      // 1分钟内
      if (diff < 60000) {
        return '刚刚';
      }

      // 1小时内
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
      }

      // 24小时内
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
      }

      // 超过24小时，显示完整日期
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');

      return `${year}-${month}-${day} ${hour}:${minute}`;
    } catch (error) {
      console.error('格式化时间失败:', error);
      return timeStr;
    }
  },

  // ECharts 图表相关方法已移除，仅保留学习概览和学习模式

  /**
   * 时间范围变化
   */
  onTimeRangeChange(event) {
    const newRange = event.detail;
    console.log('时间范围变化:', newRange);

    // 更新时间范围文本
    const rangeTextMap = {
      '7d': '7天',
      '30d': '30天',
      '90d': '90天',
    };

    this.setData({
      timeRange: newRange,
      timeRangeText: rangeTextMap[newRange],
    });

    // 重新加载数据
    this.loadAnalyticsData();
  },

  /**
   * 分享报告
   */
  onShareReport() {
    console.log('分享学习报告');

    wx.showActionSheet({
      itemList: ['保存为图片', '分享给朋友'],
      success: res => {
        if (res.tapIndex === 0) {
          // 保存为图片
          this.saveReportImage();
        } else if (res.tapIndex === 1) {
          // 分享给朋友
          wx.showToast({
            title: '请点击右上角分享',
            icon: 'none',
            duration: 2000,
          });
        }
      },
    });
  },

  /**
   * 保存报告为图片
   */
  async saveReportImage() {
    wx.showLoading({
      title: '生成图片中...',
      mask: true,
    });

    try {
      // 创建 Canvas 上下文
      const query = wx.createSelectorQuery();
      query
        .select('.report-content')
        .fields({ node: true, size: true })
        .exec(res => {
          if (!res || !res[0]) {
            wx.hideLoading();
            wx.showToast({
              title: '生成失败，请重试',
              icon: 'none',
            });
            return;
          }

          // TODO: 使用 Canvas 绘制报告内容
          // 由于小程序限制，这里需要使用 Canvas 2D API 绘制
          // 简化实现：直接提示用户截图
          wx.hideLoading();
          wx.showModal({
            title: '提示',
            content: '请使用手机截图功能保存学习报告',
            showCancel: false,
          });
        });
    } catch (error) {
      console.error('保存报告图片失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '保存失败',
        icon: 'none',
      });
    }
  },

  /**
   * 导出报告
   */
  onExportReport() {
    wx.showLoading({ title: '导出中...' });

    // 模拟导出过程
    setTimeout(() => {
      wx.hideLoading();
      wx.showToast({
        title: '导出功能开发中',
        icon: 'none',
      });
    }, 1500);
  },

  /**
   * 刷新数据
   */
  onRefreshData() {
    this.loadAnalyticsData();
  },

  /**
   * 页面分享
   */
  onShareAppMessage() {
    return {
      title: '我的学习报告 - 五好伴学',
      path: '/pages/analysis/report/index',
      imageUrl: '', // TODO: 设置分享图片
    };
  },
};

// 使用守卫包装页面
Page(createGuardedPage(pageObject, 'pages/analysis/report/index'));

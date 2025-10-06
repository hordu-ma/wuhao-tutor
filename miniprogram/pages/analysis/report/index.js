// 学习报告页面逻辑
const api = require('../../../api/index.js');
import * as echarts from '../../../components/ec-canvas/echarts';

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

let subjectChart = null;
let knowledgeChart = null;

Page({
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

    // ECharts 配置
    subjectChartEc: {
      lazyLoad: true,
    },
    knowledgeChartEc: {
      lazyLoad: true,
    },

    // 知识点数据
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

    // 学情诊断报告数据
    reportData: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('学习报告页面加载');
    this.initSubjectChartComponent();
    this.initKnowledgeChartComponent();
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
      apiStatus: 'loading',
    });

    try {
      // 并行获取多个分析数据
      const [overviewResult, knowledgeResult, progressResult] = await Promise.allSettled([
        api.analysis.getOverview({ days: this.getTimeRangeDays() }),
        api.analysis.getMastery({ subject: 'all' }),
        api.analysis.getProgress({ days: this.getTimeRangeDays() }),
      ]);

      // 处理结果
      const analyticsData = {
        overview: overviewResult.status === 'fulfilled' ? overviewResult.value.data : {},
        knowledge: knowledgeResult.status === 'fulfilled' ? knowledgeResult.value.data : {},
        progress: progressResult.status === 'fulfilled' ? progressResult.value.data : {},
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
    
    // 处理概览数据
    const processedOverview = {
      total_questions: overview?.total_questions || 0,
      total_sessions: overview?.total_sessions || 0,
      total_study_days: overview?.total_study_days || 0,
      avg_rating: overview?.avg_rating || 0,
      positive_feedback_rate: overview?.positive_feedback_rate || 0,
    };

    // 处理学科统计数据
    const subjectStats = overview?.subject_stats ? overview.subject_stats.map(item => ({
      ...item,
      subject_name: SUBJECT_MAP[item.subject] || item.subject,
    })) : [];

    // 处理知识点数据
    const knowledgePoints = knowledge?.knowledge_points || [];

    // 处理学习模式
    const learningPattern = this.formatLearningPattern(overview?.learning_pattern);

    // 格式化更新时间
    const formattedUpdateTime = this.formatUpdateTime(new Date().toISOString());

    const hasData = processedOverview.total_questions > 0 || processedOverview.total_sessions > 0;

    // 生成学情诊断报告数据
    const reportData = this.generateDiagnosisReport(analyticsData);

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
      reportData, // 新增学情诊断报告数据
      apiStatus: hasData ? 'success' : 'empty',
      hasData,
    });

    // 如果有数据，初始化图表
    if (hasData && subjectStats.length > 0) {
      this.initSubjectChart();
      this.initKnowledgeChart();
    }
  },

  /**
   * 生成学情诊断报告数据
   */
  generateDiagnosisReport(analyticsData) {
    const { overview, knowledge, progress } = analyticsData;
    const currentUser = wx.getStorageSync('userInfo') || {};

    return {
      student_name: currentUser.nickname || '同学',
      time_range: this.data.timeRangeText,
      overall_score: Math.round((overview?.avg_rating || 0) * 20), // 转换为100分制
      generated_time: new Date().toLocaleString('zh-CN'),
      data_range: this.getTimeRangeDays(),

      // 学习风格分析
      learning_style: {
        analysis: [
          { type: 'visual', name: '视觉型', percentage: 65 },
          { type: 'auditory', name: '听觉型', percentage: 25 },
          { type: 'kinesthetic', name: '动觉型', percentage: 10 }
        ],
        description: '您偏向于视觉学习，建议多使用图表、思维导图等方式学习。'
      },

      // 知识点掌握情况
      knowledge_mastery: overview?.subject_stats ? overview.subject_stats.map(subject => ({
        subject: subject.subject_name,
        mastery_rate: Math.round((subject.avg_difficulty || 0.5) * 100),
        points: this.generateKnowledgePoints(subject)
      })) : [],

      // 学习行为分析
      behavior_analysis: {
        metrics: [
          {
            name: '学习积极性',
            value: `${overview?.total_sessions || 0}次`,
            icon: 'fire-o',
            trend: 15,
            trend_text: '较上周提升15%'
          },
          {
            name: '学习专注度',
            value: `${Math.round((overview?.avg_session_length || 30) / 60)}分钟`,
            icon: 'clock-o',
            trend: 0,
            trend_text: '保持稳定'
          },
          {
            name: '问题解决能力',
            value: `${Math.round((overview?.avg_rating || 0) * 20)}分`,
            icon: 'bulb-o',
            trend: 8,
            trend_text: '较上周提升8%'
          }
        ],
        patterns: ['夜间学习型', '深度思考型', '问答互动型']
      },

      // 个性化改进建议
      improvement_suggestions: [
        {
          category: '学习方法',
          icon: 'guide-o',
          priority: 'high',
          suggestions: overview?.improvement_suggestions || [
            '建议增加练习频率，巩固薄弱知识点',
            '可以尝试制作知识点思维导图',
            '定期回顾错题，避免重复犯错'
          ]
        },
        {
          category: '学习习惯',
          icon: 'clock-o',
          priority: 'medium',
          suggestions: [
            '保持规律的学习时间，建议每天固定时段学习',
            '适当休息，避免长时间连续学习导致疲劳'
          ]
        }
      ],

      // 进步跟踪
      progress_tracking: {
        overall_trend: Math.round(Math.random() * 20 - 5), // 模拟进步趋势
        consecutive_days: overview?.total_study_days || 0,
        highlights: [
          '数学成绩提升明显，继续保持',
          '问答互动积极，学习态度优秀',
          '错题复习及时，学习方法得当'
        ],
        next_goals: [
          '完成本周学习计划',
          '巩固薄弱知识点',
          '提高解题速度和准确率'
        ]
      }
    };
  },

  /**
   * 生成知识点详情
   */
  generateKnowledgePoints(subject) {
    // 根据学科生成相应的知识点
    const knowledgeMap = {
      '数学': [
        { name: '函数与方程', level: 'high', score: 88 },
        { name: '几何图形', level: 'medium', score: 72 },
        { name: '概率统计', level: 'low', score: 56 }
      ],
      '语文': [
        { name: '阅读理解', level: 'high', score: 85 },
        { name: '作文写作', level: 'medium', score: 75 },
        { name: '古诗词', level: 'low', score: 60 }
      ],
      '英语': [
        { name: '语法', level: 'high', score: 90 },
        { name: '词汇', level: 'medium', score: 78 },
        { name: '听力', level: 'low', score: 65 }
      ]
    };

    return knowledgeMap[subject.subject_name] || [
      { name: '基础知识', level: 'medium', score: 75 },
      { name: '应用能力', level: 'medium', score: 70 }
    ];
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

  /**
   * 初始化知识点掉维图（新增）
   */
  initKnowledgeChart() {
    if (!this.data.knowledgePoints || this.data.knowledgePoints.length === 0) {
      console.log('没有知识点数据，跳过图表渲染');
      return;
    }

    // 初始化知识点雷达图
    this.initKnowledgeChartComponent();
  },

  /**
   * 初始化知识点图表组件
   */
  initKnowledgeChartComponent() {
    this.setData({
      knowledgeChartEc: {
        onInit: this.initKnowledgeChartCanvas.bind(this),
      },
    });
  },

  /**
   * 知识点图表初始化回调
   */
  initKnowledgeChartCanvas(canvas, width, height, dpr) {
    knowledgeChart = echarts.init(canvas, null, {
      width: width,
      height: height,
      devicePixelRatio: dpr,
    });

    canvas.setChart(knowledgeChart);

    // 设置知识点雷达图配置
    const knowledgeData = this.data.knowledgePoints.map(point => ({
      name: point.name,
      value: point.mastery,
      max: 1,
    }));

    const option = {
      radar: {
        indicator: this.data.knowledgePoints.map(point => ({
          name: point.name,
          max: 1,
        })),
        shape: 'polygon',
        radius: '60%',
        axisLabel: {
          show: true,
          fontSize: 10,
          color: '#666',
        },
        splitLine: {
          lineStyle: {
            color: '#e0e0e0',
          },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: this.data.knowledgePoints.map(point => point.mastery),
              name: '知识点掌握度',
              areaStyle: {
                color: 'rgba(102, 126, 234, 0.3)',
              },
              lineStyle: {
                color: '#667eea',
                width: 2,
              },
              symbol: 'circle',
              symbolSize: 4,
            },
          ],
        },
      ],
      tooltip: {
        trigger: 'item',
        formatter: function (params) {
          const percent = Math.round(params.value * 100);
          return `${params.name}: ${percent}%`;
        },
      },
    };

    knowledgeChart.setOption(option);
  },

  /**
   * 初始化学科统计图表
   */
  initSubjectChart() {
    if (!this.data.analytics.subject_stats || this.data.analytics.subject_stats.length === 0) {
      console.log('没有学科统计数据，跳过图表渲染');
      return;
    }

    console.log('初始化学科统计图表');

    const subjectStats = this.data.analytics.subject_stats;
    const subjectNames = subjectStats.map(item => item.subject_name);
    const questionCounts = subjectStats.map(item => item.question_count);

    if (subjectChart) {
      // 更新图表数据
      subjectChart.setOption({
        xAxis: {
          data: subjectNames,
        },
        series: [
          {
            data: questionCounts,
          },
        ],
      });
    }
  },

  /**
   * 初始化图表组件
   */
  initSubjectChartComponent() {
    this.setData({
      subjectChartEc: {
        onInit: this.initChart.bind(this),
      },
    });
  },

  /**
   * 图表初始化回调
   */
  initChart(canvas, width, height, dpr) {
    subjectChart = echarts.init(canvas, null, {
      width: width,
      height: height,
      devicePixelRatio: dpr,
    });

    canvas.setChart(subjectChart);

    // 设置初始配置
    const option = {
      color: ['#667eea', '#764ba2', '#4ecb73', '#ffa502', '#ff6b6b'],
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
        confine: true,
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%',
        top: '10%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: [],
        axisLabel: {
          interval: 0,
          rotate: 45,
          fontSize: 10,
        },
        axisLine: {
          lineStyle: {
            color: '#cccccc',
          },
        },
      },
      yAxis: {
        type: 'value',
        name: '提问数',
        nameTextStyle: {
          fontSize: 10,
        },
        axisLabel: {
          fontSize: 10,
        },
        axisLine: {
          lineStyle: {
            color: '#cccccc',
          },
        },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: '#eeeeee',
          },
        },
      },
      series: [
        {
          name: '提问数',
          type: 'bar',
          data: [],
          barWidth: '50%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#667eea' },
              { offset: 1, color: '#764ba2' },
            ]),
          },
          label: {
            show: true,
            position: 'top',
            fontSize: 10,
          },
        },
      ],
    };

    subjectChart.setOption(option);

    return subjectChart;
  },

  /**
   * 生成知识点数据
   */
  generateKnowledgePoints() {
    // TODO: 从后端API获取真实知识点数据
    // 目前使用模拟数据
    const knowledgePoints = [
      { name: '函数与方程', mastery: 85 },
      { name: '几何图形', mastery: 72 },
      { name: '代数运算', mastery: 90 },
      { name: '概率统计', mastery: 68 },
      { name: '数列', mastery: 75 },
    ];

    this.setData({
      knowledgePoints,
    });

    // 初始化雷达图
    if (knowledgePoints.length > 0) {
      this.initKnowledgeChart();
    }
  },

  /**
   * 初始化知识点图表组件
   */
  initKnowledgeChartComponent() {
    this.setData({
      knowledgeChartEc: {
        onInit: this.initKnowledgeChartCanvas.bind(this),
      },
    });
  },

  /**
   * 知识点雷达图初始化
   */
  initKnowledgeChartCanvas(canvas, width, height, dpr) {
    knowledgeChart = echarts.init(canvas, null, {
      width: width,
      height: height,
      devicePixelRatio: dpr,
    });

    canvas.setChart(knowledgeChart);

    return knowledgeChart;
  },

  /**
   * 初始化知识点雷达图
   */
  initKnowledgeChart() {
    if (!knowledgeChart || !this.data.knowledgePoints || this.data.knowledgePoints.length === 0) {
      console.log('知识点图表实例未初始化或无数据');
      return;
    }

    console.log('初始化知识点雷达图');

    const knowledgePoints = this.data.knowledgePoints;
    const indicator = knowledgePoints.map(item => ({
      name: item.name,
      max: 100,
    }));

    const radarData = knowledgePoints.map(item => item.mastery);

    const option = {
      color: ['#667eea'],
      tooltip: {
        trigger: 'item',
        confine: true,
      },
      radar: {
        indicator: indicator,
        shape: 'polygon',
        splitNumber: 4,
        name: {
          textStyle: {
            fontSize: 10,
            color: '#666666',
          },
        },
        splitLine: {
          lineStyle: {
            color: '#eeeeee',
          },
        },
        splitArea: {
          areaStyle: {
            color: ['#ffffff', '#f5f7fa'],
          },
        },
        axisLine: {
          lineStyle: {
            color: '#cccccc',
          },
        },
      },
      series: [
        {
          name: '知识点掌握度',
          type: 'radar',
          data: [
            {
              value: radarData,
              name: '掌握度',
              areaStyle: {
                color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
                  { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
                  { offset: 1, color: 'rgba(102, 126, 234, 0.05)' },
                ]),
              },
              lineStyle: {
                width: 2,
              },
            },
          ],
        },
      ],
    };

    knowledgeChart.setOption(option);
  },

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
        icon: 'none'
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
});

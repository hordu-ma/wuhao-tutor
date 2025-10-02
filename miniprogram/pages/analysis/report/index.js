// 学习报告页面逻辑
import { request } from '../../../utils/request';
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
      loading: true,
    });

    try {
      // 先尝试从缓存读取数据
      const cacheKey = `analytics_${this.data.timeRange}`;
      const cachedData = wx.getStorageSync(cacheKey);

      if (cachedData && cachedData.timestamp) {
        const cacheAge = Date.now() - cachedData.timestamp;
        // 如果缓存在1小时内，直接使用缓存
        if (cacheAge < 3600000) {
          console.log('使用缓存数据');
          this.processAnalyticsData(cachedData.data);
          return;
        }
      }

      // 调用学情分析 API
      const response = await request({
        url: '/api/v1/learning/analytics',
        method: 'GET',
      });

      console.log('学情分析数据返回:', response);

      if (response.code === 0 && response.data) {
        const analyticsData = response.data;

        // 缓存数据
        wx.setStorageSync(cacheKey, {
          data: analyticsData,
          timestamp: Date.now(),
        });

        this.processAnalyticsData(analyticsData);
      } else {
        // 没有数据或请求失败
        console.warn('学情分析数据为空或请求失败');
        this.setData({
          hasData: false,
          loading: false,
        });
      }
    } catch (error) {
      console.error('加载学情分析数据失败:', error);

      // 错误处理：显示友好提示
      const errorMsg = this.getErrorMessage(error);
      wx.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 2000,
      });

      this.setData({
        loading: false,
        hasData: false,
      });
    }
  },

  /**
   * 处理学情分析数据
   */
  processAnalyticsData(analyticsData) {
    // 处理学科统计数据
    const subjectStats = analyticsData.subject_stats.map(item => ({
      ...item,
      subject_name: SUBJECT_MAP[item.subject] || item.subject,
    }));

    // 格式化学习模式数据
    const learningPattern = this.formatLearningPattern(analyticsData.learning_pattern);

    // 格式化更新时间
    const formattedUpdateTime = this.formatUpdateTime(analyticsData.last_analyzed_at);

    this.setData({
      analytics: {
        ...analyticsData,
        subject_stats: subjectStats,
        avg_rating: Number(analyticsData.avg_rating).toFixed(1),
      },
      learningPattern,
      formattedUpdateTime,
      hasData: analyticsData.total_questions > 0 || analyticsData.total_sessions > 0,
      loading: false,
    });

    // 如果有数据，初始化图表
    if (this.data.hasData && subjectStats.length > 0) {
      this.initSubjectChart();
    }

    // 生成模拟知识点数据（后续对接真实API）
    this.generateKnowledgePoints();
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

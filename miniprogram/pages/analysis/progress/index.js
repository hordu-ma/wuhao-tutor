// 学习进度页面逻辑
import { request } from '../../../utils/request';
import * as echarts from '../components/ec-canvas/echarts';

let trendChart = null;

Page({
  data: {
    // 页面状态
    loading: true,
    hasData: false,

    // ECharts 配置
    trendChartEc: {
      lazyLoad: true,
    },

    // 统计数据
    streakDays: 0, // 连续学习天数
    totalDays: 0, // 总学习天数
    weeklyHours: 0, // 本周学习时长
    weeklyHomework: 0, // 本周作业数

    // 图表类型
    chartType: 'time', // time: 学习时长, homework: 作业完成

    // 时间轴数据
    timelineData: [],
    currentPage: 1,
    hasMore: true,
    loadingMore: false,

    // 学习目标
    goals: [],
    showGoalDialog: false,
    goalDialogTitle: '添加目标',
    goalForm: {
      id: '',
      title: '',
      target: '',
      unit: '次',
      deadline: '',
    },

    // 日期选择器
    showCalendar: false,
    minDate: new Date().getTime(),
    maxDate: new Date(new Date().getFullYear() + 1, 11, 31).getTime(),

    // 学习洞察
    insights: [],
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    console.log('学习进度页面加载');
    this.initTrendChartComponent();
    this.loadProgressData();
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    console.log('学习进度页面显示');
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    console.log('下拉刷新学习进度');
    this.setData({
      currentPage: 1,
      timelineData: [],
      hasMore: true,
    });
    this.loadProgressData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载学习进度数据
   */
  async loadProgressData() {
    console.log('开始加载学习进度数据');

    this.setData({
      loading: true,
    });

    try {
      // 先尝试从缓存读取数据
      const cacheKey = 'progress_data';
      const cachedData = wx.getStorageSync(cacheKey);

      if (cachedData && cachedData.timestamp) {
        const cacheAge = Date.now() - cachedData.timestamp;
        // 如果缓存在30分钟内，直接使用缓存
        if (cacheAge < 1800000) {
          console.log('使用缓存数据');
          this.processProgressData(cachedData.data);
          return;
        }
      }

      // 并行加载多个接口数据
      const [statsResult, timelineResult, goalsResult] = await Promise.allSettled([
        this.loadLearningStats(),
        this.loadTimelineData(),
        this.loadGoals(),
      ]);

      const progressData = {
        stats: statsResult.status === 'fulfilled' ? statsResult.value : null,
        timeline: timelineResult.status === 'fulfilled' ? timelineResult.value : [],
        goals: goalsResult.status === 'fulfilled' ? goalsResult.value : [],
      };

      // 缓存数据
      wx.setStorageSync(cacheKey, {
        data: progressData,
        timestamp: Date.now(),
      });

      this.processProgressData(progressData);
    } catch (error) {
      console.error('加载学习进度数据失败:', error);

      // 错误处理
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
   * 处理学习进度数据
   */
  processProgressData(progressData) {
    // 处理统计数据
    if (progressData.stats) {
      this.setData({
        streakDays: progressData.stats.streak_days || 0,
        totalDays: progressData.stats.total_days || 0,
        weeklyHours: progressData.stats.weekly_hours || 0,
        weeklyHomework: progressData.stats.weekly_homework || 0,
      });
    }

    // 处理时间轴数据
    this.setData({
      timelineData: progressData.timeline || [],
    });

    // 处理学习目标
    this.setData({
      goals: progressData.goals || [],
    });

    // 生成学习洞察
    this.generateInsights();

    // 初始化图表
    this.initTrendChart();

    this.setData({
      hasData: this.data.timelineData.length > 0 || this.data.totalDays > 0,
      loading: false,
    });
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
   * 加载学习统计数据
   */
  async loadLearningStats() {
    // TODO: 调用实际的统计API
    // 目前返回模拟数据
    return {
      streak_days: 5,
      total_days: 30,
      weekly_hours: 12,
      weekly_homework: 8,
    };
  },

  /**
   * 加载时间轴数据
   */
  async loadTimelineData() {
    try {
      // TODO: 调用实际的历史记录API
      // 目前返回模拟数据
      const mockData = [
        {
          id: 1,
          type: 'homework',
          title: '完成数学作业',
          description: '完成了"二次函数"相关练习',
          time: '2小时前',
          stats: [
            { label: '得分', value: '95分' },
            { label: '用时', value: '45分钟' },
          ],
        },
        {
          id: 2,
          type: 'question',
          title: '提问互动',
          description: '向AI提问了3个问题，涉及物理和化学学科',
          time: '5小时前',
          stats: [
            { label: '提问数', value: '3个' },
            { label: '满意度', value: '5星' },
          ],
        },
        {
          id: 3,
          type: 'achievement',
          title: '获得成就',
          description: '连续学习5天，获得"坚持不懈"徽章',
          time: '1天前',
          stats: null,
        },
      ];

      return mockData;
    } catch (error) {
      console.error('加载时间轴数据失败:', error);
      return [];
    }
  },

  /**
   * 加载学习目标
   */
  async loadGoals() {
    try {
      // TODO: 调用实际的目标API
      // 目前返回模拟数据
      const mockGoals = [
        {
          id: 1,
          title: '每周完成10道数学题',
          current: 8,
          target: 10,
          unit: '道',
          progress: 80,
          deadline: '2025-10-08',
        },
        {
          id: 2,
          title: '本月学习20小时',
          current: 12,
          target: 20,
          unit: '小时',
          progress: 60,
          deadline: '2025-10-31',
        },
      ];

      return mockGoals;
    } catch (error) {
      console.error('加载学习目标失败:', error);
      return [];
    }
  },

  /**
   * 生成学习洞察
   */
  generateInsights() {
    const insights = [
      {
        icon: 'fire-o',
        color: '#ff6b6b',
        title: '学习状态极佳',
        description: '您已连续学习5天，保持这个势头！',
      },
      {
        icon: 'clock-o',
        color: '#667eea',
        title: '最佳学习时段',
        description: '您在晚上8-10点学习效率最高，建议在此时段重点攻克难题',
      },
      {
        icon: 'chart-trending-o',
        color: '#4ecb73',
        title: '进步明显',
        description: '本周作业平均分比上周提高了12分，继续加油！',
      },
    ];

    this.setData({
      insights,
    });
  },

  /**
   * 初始化趋势图表
   */
  initTrendChart() {
    console.log('初始化趋势图表, 类型:', this.data.chartType);

    if (!trendChart) {
      console.log('图表实例未初始化');
      return;
    }

    // 模拟最近30天的数据
    const dates = [];
    const timeData = [];
    const homeworkData = [];

    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      dates.push(`${date.getMonth() + 1}/${date.getDate()}`);

      // 模拟数据：学习时长在20-60分钟之间波动
      timeData.push(Math.floor(Math.random() * 40) + 20);

      // 模拟数据：作业完成数在0-3之间
      homeworkData.push(Math.floor(Math.random() * 4));
    }

    const isTimeChart = this.data.chartType === 'time';

    const option = {
      color: ['#667eea'],
      tooltip: {
        trigger: 'axis',
        confine: true,
      },
      grid: {
        left: '10%',
        right: '10%',
        bottom: '15%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLabel: {
          interval: 6,
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
        name: isTimeChart ? '分钟' : '作业数',
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
          name: isTimeChart ? '学习时长' : '作业完成',
          type: 'line',
          data: isTimeChart ? timeData : homeworkData,
          smooth: true,
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
              { offset: 1, color: 'rgba(102, 126, 234, 0.05)' },
            ]),
          },
          lineStyle: {
            width: 2,
          },
          itemStyle: {
            borderWidth: 2,
          },
        },
      ],
    };

    trendChart.setOption(option);
  },

  /**
   * 初始化图表组件
   */
  initTrendChartComponent() {
    this.setData({
      trendChartEc: {
        onInit: this.initChart.bind(this),
      },
    });
  },

  /**
   * 图表初始化回调
   */
  initChart(canvas, width, height, dpr) {
    trendChart = echarts.init(canvas, null, {
      width: width,
      height: height,
      devicePixelRatio: dpr,
    });

    canvas.setChart(trendChart);

    // 初始化空图表
    this.initTrendChart();

    return trendChart;
  },

  /**
   * 图表类型切换
   */
  onChartTypeChange(event) {
    const chartType = event.currentTarget.dataset.type;
    console.log('切换图表类型:', chartType);

    this.setData({
      chartType,
    });

    // 重新渲染图表
    this.initTrendChart();
  },

  /**
   * 加载更多时间轴数据
   */
  async onLoadMore() {
    if (this.data.loadingMore || !this.data.hasMore) {
      return;
    }

    this.setData({
      loadingMore: true,
    });

    try {
      const nextPage = this.data.currentPage + 1;
      // TODO: 调用实际API加载下一页数据
      // const newData = await this.loadTimelineData(nextPage)

      // 模拟加载
      await new Promise(resolve => setTimeout(resolve, 1000));

      this.setData({
        currentPage: nextPage,
        loadingMore: false,
        hasMore: false, // 模拟数据已加载完
      });
    } catch (error) {
      console.error('加载更多失败:', error);
      this.setData({
        loadingMore: false,
      });
    }
  },

  /**
   * 添加目标
   */
  onAddGoal() {
    console.log('添加学习目标');

    this.setData({
      showGoalDialog: true,
      goalDialogTitle: '添加目标',
      goalForm: {
        id: '',
        title: '',
        target: '',
        unit: '次',
        deadline: '',
      },
    });
  },

  /**
   * 编辑目标
   */
  onEditGoal(event) {
    const goalId = event.currentTarget.dataset.id;
    const goal = this.data.goals.find(g => g.id === goalId);

    if (goal) {
      this.setData({
        showGoalDialog: true,
        goalDialogTitle: '编辑目标',
        goalForm: {
          id: goal.id,
          title: goal.title,
          target: String(goal.target),
          unit: goal.unit,
          deadline: goal.deadline,
        },
      });
    }
  },

  /**
   * 关闭目标弹窗
   */
  onCloseGoalDialog() {
    this.setData({
      showGoalDialog: false,
    });
  },

  /**
   * 目标表单字段变化
   */
  onGoalFieldChange(event) {
    const field = event.currentTarget.dataset.field;
    const value = event.detail;

    this.setData({
      [`goalForm.${field}`]: value,
    });
  },

  /**
   * 选择截止日期
   */
  onSelectDeadline() {
    this.setData({
      showCalendar: true,
    });
  },

  /**
   * 关闭日期选择器
   */
  onCloseCalendar() {
    this.setData({
      showCalendar: false,
    });
  },

  /**
   * 确认日期
   */
  onConfirmDate(event) {
    const date = new Date(event.detail);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;

    this.setData({
      'goalForm.deadline': formattedDate,
      showCalendar: false,
    });
  },

  /**
   * 保存目标
   */
  async onSaveGoal() {
    const { goalForm } = this.data;

    // 验证表单
    if (!goalForm.title) {
      wx.showToast({
        title: '请输入目标名称',
        icon: 'none',
      });
      return;
    }

    if (!goalForm.target) {
      wx.showToast({
        title: '请输入目标数量',
        icon: 'none',
      });
      return;
    }

    if (!goalForm.deadline) {
      wx.showToast({
        title: '请选择截止日期',
        icon: 'none',
      });
      return;
    }

    try {
      // TODO: 调用实际的保存API
      console.log('保存目标:', goalForm);

      wx.showToast({
        title: goalForm.id ? '目标已更新' : '目标已添加',
        icon: 'success',
      });

      this.setData({
        showGoalDialog: false,
      });

      // 重新加载目标列表
      this.loadGoals().then(goals => {
        this.setData({ goals });
      });
    } catch (error) {
      console.error('保存目标失败:', error);
      wx.showToast({
        title: '保存失败，请重试',
        icon: 'none',
      });
    }
  },

  /**
   * 页面分享
   */
  onShareAppMessage() {
    return {
      title: '我的学习进度 - 五好伴学',
      path: '/pages/analysis/progress/index',
    };
  },
});

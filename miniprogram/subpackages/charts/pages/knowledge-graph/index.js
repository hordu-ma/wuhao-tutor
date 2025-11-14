// pages/knowledge-graph/index.js - 知识图谱页面
const { createGuardedPage } = require('../../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../../api/mistakes.js');
// 注意:官方ec-canvas组件已内置echarts,不需要单独引入

const pageObject = {
  data: {
    // 当前选择的科目
    selectedSubject: '数学',
    subjectOptions: [
      { text: '数学', value: '数学' },
      { text: '语文', value: '语文' },
      { text: '英语', value: '英语' },
      { text: '物理', value: '物理' },
      { text: '化学', value: '化学' },
      { text: '生物', value: '生物' },
      { text: '历史', value: '历史' },
      { text: '地理', value: '地理' },
      { text: '政治', value: '政治' },
    ],

    // 视图模式: 'list'(列表) | 'graph'(图谱)
    viewMode: 'list',

    // 加载状态
    loading: false,
    snapshotLoading: false,
    weakChainsLoading: false,

    // 知识图谱快照数据
    snapshot: null,

    // 薄弱知识链
    weakChains: [],

    // ECharts配置
    ec: {
      lazyLoad: true, // 延迟加载,在initGraphView中手动初始化
    },
    graphOption: null,

    // 错误状态
    error: null,
  },

  /**
   * 中文学科名称转英文枚举
   * @param {string} chineseSubject - 中文学科名（如"数学"）
   * @returns {string} 英文学科枚举（如"math"）
   */
  convertSubjectToEnglish(chineseSubject) {
    const mapping = {
      数学: 'math',
      语文: 'chinese',
      英语: 'english',
      物理: 'physics',
      化学: 'chemistry',
      生物: 'biology',
      历史: 'history',
      地理: 'geography',
      政治: 'politics',
    };
    return mapping[chineseSubject] || 'math'; // 默认返回数学
  },

  async onLoad(options) {
    console.log('知识图谱页面加载', options);

    if (options.subject) {
      this.setData({
        selectedSubject: options.subject,
      });
    }

    // 加载数据
    await this.loadData();
  },

  onShow() {
    console.log('📍 知识图谱页面显示');

    // 🆕 如果不是首次加载（已有数据），则刷新
    // 使用场景: 从错题列表删除错题后返回此页面
    if (this.data.snapshot) {
      console.log('🔄 检测到已有数据，触发增量刷新');
      this.loadData(); // 重新加载数据
    } else {
      console.log('🆕 首次加载，跳过刷新（将在onLoad中加载）');
    }
  },

  onPullDownRefresh() {
    this.loadData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载所有数据
   */
  async loadData() {
    await Promise.all([this.loadSnapshot(), this.loadWeakChains()]);
  },

  /**
   * 加载知识图谱快照
   */
  async loadSnapshot() {
    if (!this.data.selectedSubject) return;

    try {
      this.setData({ snapshotLoading: true, error: null });

      console.log('开始加载知识图谱，当前学科:', this.data.selectedSubject);

      // 🆕 转换中文学科名为英文枚举
      const subjectEn = this.convertSubjectToEnglish(this.data.selectedSubject);
      console.log('学科转换:', this.data.selectedSubject, '→', subjectEn);

      // 🆕 调用新版学科隔离API
      const response = await mistakesApi.getSubjectKnowledgeGraph({
        subject: subjectEn,
      });

      // 旧代码（注释保留，向后兼容）
      // const response = await mistakesApi.getKnowledgeGraphSnapshot({
      //   subject: this.data.selectedSubject,
      // });

      console.log('知识图谱数据加载成功:', response);

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const snapshot = isStandardFormat ? response.data || response : response;

        // 转换数据格式
        const formattedSnapshot = this.formatSnapshotData(snapshot);

        console.log('📊 格式化后的快照数据:', formattedSnapshot);
        console.log('📚 知识点数量:', formattedSnapshot?.knowledge_points?.length);

        this.setData({
          snapshot: formattedSnapshot,
          snapshotLoading: false,
        });

        // 额外验证
        if (formattedSnapshot && formattedSnapshot.knowledge_points) {
          console.log('✅ 数据设置成功，knowledge_points:', formattedSnapshot.knowledge_points);
        } else {
          console.error('❌ 格式化数据异常:', formattedSnapshot);
        }
      }
      // 如果响应异常，错误会在 catch 中处理
    } catch (error) {
      console.error('加载知识图谱快照失败', error);

      // 404 表示还没有快照数据
      if (error.statusCode === 404 || error.status === 404) {
        this.setData({
          error: '暂无数据',
          snapshotLoading: false,
          snapshot: null,
        });
        // 静默处理，不弹toast
        return;
      }

      // 其他错误
      const errorMessage = error.message || '加载失败,请稍后重试';
      this.setData({
        error: errorMessage,
        snapshotLoading: false,
        snapshot: null,
      });

      wx.showToast({
        title: errorMessage,
        icon: 'none',
        duration: 2000,
      });
    }
  },

  /**
   * 格式化快照数据（兼容新旧两种API格式）
   * @param {Object} snapshot - API响应数据
   * @returns {Object|null} 格式化后的数据，失败返回null
   */
  formatSnapshotData(snapshot) {
    if (!snapshot) {
      console.warn('快照数据为空');
      return null;
    }

    // 🆕 新版 /graphs/{subject} API 格式（优先）
    if (snapshot.nodes && Array.isArray(snapshot.nodes)) {
      console.log('✅ 检测到新版API格式，nodes数量:', snapshot.nodes.length);
      console.log('📦 原始nodes数据示例:', snapshot.nodes[0]);

      const knowledge_points = snapshot.nodes.map(node => ({
        name: node.name || '',
        mastery_level: node.mastery || 0, // 注意字段名变化: mastery
        mistake_count: node.mistake_count || 0,
        correct_count: node.correct_count || 0,
        total_attempts: node.total_attempts || 0,
        id: node.id || '', // 🆕 节点ID
      }));

      console.log('🔄 转换后knowledge_points示例:', knowledge_points[0]);

      const result = {
        subject: snapshot.subject || '',
        knowledge_points,
        total_mistakes: snapshot.total_points || 0,
        average_mastery: snapshot.avg_mastery || 0,
        // 🆕 新增字段（增强功能）
        weak_chains: snapshot.weak_chains || [],
        mastery_distribution: snapshot.mastery_distribution || {},
        recommendations: snapshot.recommendations || [],
      };

      console.log('📋 返回的result对象:', result);
      return result;
    }

    // 向后兼容：旧版 /mastery API 格式
    if (snapshot.items && Array.isArray(snapshot.items)) {
      console.log('⚠️ 检测到旧版API格式，items数量:', snapshot.items.length);

      const knowledge_points = snapshot.items.map(item => ({
        name: item.knowledge_point || '',
        mastery_level: item.mastery_level || 0, // 旧格式字段名
        mistake_count: item.mistake_count || 0,
        correct_count: item.correct_count || 0,
        total_attempts: item.total_attempts || 0,
        last_practiced: item.last_practiced_at || null,
      }));

      return {
        subject: snapshot.subject || '',
        knowledge_points,
        total_mistakes: snapshot.total_count || 0,
        average_mastery: snapshot.average_mastery || 0,
        // 旧格式无这些字段
        weak_chains: [],
        mastery_distribution: {},
        recommendations: [],
      };
    }

    // 再向后兼容：更旧版 snapshot 格式
    if (snapshot.knowledge_points) {
      console.log('⚠️ 检测到更旧版格式，直接返回');
      return snapshot;
    }

    // 兼容从 graph_data.nodes 转换
    const graphData = snapshot.graph_data || {};
    const nodes = graphData.nodes || [];

    if (nodes.length > 0) {
      console.log('⚠️ 检测到 graph_data.nodes 格式');
      const knowledge_points = nodes.map(node => ({
        name: node.name || '',
        mastery_level: node.mastery_level || node.value || 0,
        mistake_count: node.mistake_count || 0,
        last_practiced: node.last_practiced || null,
      }));

      return {
        ...snapshot,
        knowledge_points,
        total_mistakes: snapshot.total_knowledge_points || 0,
        average_mastery: this.calculateAverageMastery(knowledge_points),
        weak_chains: [],
        mastery_distribution: {},
        recommendations: [],
      };
    }

    console.error('❌ 未知的快照数据格式，无法解析:', snapshot);
    return null;
  },

  /**
   * 计算平均掌握度
   */
  calculateAverageMastery(knowledgePoints) {
    if (!knowledgePoints || knowledgePoints.length === 0) return 0;

    const sum = knowledgePoints.reduce((acc, kp) => acc + (kp.mastery_level || 0), 0);
    return sum / knowledgePoints.length;
  },

  /**
   * 加载薄弱知识链
   */
  async loadWeakChains() {
    if (!this.data.selectedSubject) return;

    try {
      this.setData({ weakChainsLoading: true });

      const response = await mistakesApi.getWeakKnowledgeChains({
        subject: this.data.selectedSubject,
        limit: 5,
      });

      // 判断响应是否成功：兼容多种响应格式
      const isStandardFormat = response && response.statusCode !== undefined;
      const isSuccess = isStandardFormat
        ? response.statusCode >= 200 && response.statusCode < 300
        : response !== null && response !== undefined;

      if (isSuccess) {
        // 兼容两种响应格式
        const responseData = isStandardFormat ? response.data || response : response;
        const weakChains = Array.isArray(responseData) ? responseData : responseData.data || [];

        this.setData({
          weakChains,
          weakChainsLoading: false,
        });
      }
      // 如果响应异常，错误会在 catch 中处理
    } catch (error) {
      console.error('加载薄弱知识链失败', error);
      this.setData({
        weakChainsLoading: false,
        weakChains: [],
      });
      // 静默处理错误,不影响主要数据展示
      if (error.status && error.status !== 404) {
        console.warn('获取薄弱知识链失败:', error.message);
      }
    }
  },

  /**
   * 切换科目
   */
  onSubjectChange(e) {
    const subject = e.detail;

    this.setData({
      selectedSubject: subject,
    });

    this.loadData();
  },

  /**
   * 查看知识点详情
   */
  onKnowledgePointTap(e) {
    const { knowledgePoint } = e.currentTarget.dataset;

    if (!knowledgePoint) return;

    // 跳转到错题列表，筛选该知识点
    wx.navigateTo({
      url: `/pages/mistakes/list/index?subject=${this.data.selectedSubject}&knowledge_point=${encodeURIComponent(knowledgePoint)}`,
    });
  },

  /**
   * 查看复习推荐
   */
  onViewRecommendations() {
    wx.navigateTo({
      url: `/pages/review-recommendations/index?subject=${this.data.selectedSubject}`,
    });
  },

  /**
   * 切换视图模式
   */
  onViewModeChange() {
    const newMode = this.data.viewMode === 'list' ? 'graph' : 'list';
    this.setData({ viewMode: newMode });

    // 如果切换到图谱视图,初始化ECharts
    if (newMode === 'graph' && this.data.snapshot) {
      this.initGraphView();
    }
  },

  /**
   * 初始化图谱视图
   */
  initGraphView() {
    if (!this.data.snapshot || !this.data.snapshot.knowledge_points) {
      console.warn('没有快照数据,无法初始化图谱');
      return;
    }

    const nodes = this.buildGraphNodes(this.data.snapshot.knowledge_points);
    const links = this.buildGraphLinks(this.data.snapshot.knowledge_points);

    console.log('✅ 构建图谱节点:', nodes.length, '个');
    console.log('✅ 构建图谱边:', links.length, '条');

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: params => {
          if (params.dataType === 'node') {
            const data = params.data;
            return `${data.name}\n掌握度: ${Math.round(data.mastery * 100)}%\n错题数: ${data.mistakes}`;
          }
          return '';
        },
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: links,
          roam: true,
          label: {
            show: true,
            position: 'bottom',
            fontSize: 10,
            formatter: '{b}',
          },
          force: {
            repulsion: 150,
            edgeLength: 100,
            layoutAnimation: true,
          },
          emphasis: {
            focus: 'adjacency',
            label: {
              fontSize: 12,
              fontWeight: 'bold',
            },
          },
        },
      ],
    };

    console.log('✅ 图表配置生成完成');

    // 获取ec-canvas组件并手动初始化
    const ecComponent = this.selectComponent('#knowledge-graph');
    if (!ecComponent) {
      console.error('❌ 未找到ec-canvas组件');
      return;
    }

    console.log('✅ 找到ec-canvas组件,开始初始化');

    // 手动调用组件的init方法
    ecComponent.init((canvas, width, height, dpr) => {
      console.log('✅ ECharts初始化回调触发');

      // 导入echarts
      const echarts = require('../../components/ec-canvas/echarts');

      // 创建图表实例
      const chart = echarts.init(canvas, null, {
        width: width,
        height: height,
        devicePixelRatio: dpr,
      });

      // 保存实例到页面对象(不是data,避免循环引用)
      this.chartInstance = chart;
      console.log('✅ chart实例已保存');

      // 设置图表配置
      chart.setOption(option);
      console.log('✅ 图表渲染完成!');

      return chart;
    });
  },

  /**
   * 构建图谱节点
   */
  buildGraphNodes(knowledgePoints) {
    return knowledgePoints.map(kp => {
      const mastery = kp.mastery_level || 0;
      let color = '#f5222d'; // 红色(待加强)
      let symbolSize = 20;

      if (mastery >= 0.7) {
        color = '#52c41a'; // 绿色(已掌握)
        symbolSize = 15;
      } else if (mastery >= 0.4) {
        color = '#faad14'; // 黄色(学习中)
        symbolSize = 18;
      } else {
        symbolSize = 25; // 薄弱点更大
      }

      return {
        name: kp.name,
        value: mastery,
        mastery: mastery,
        mistakes: kp.mistake_count || 0,
        symbolSize: symbolSize,
        itemStyle: {
          color: color,
        },
      };
    });
  },

  /**
   * 构建图谱边
   * 注意:当前快照数据可能不包含关系,这里用薄弱链作为关联
   */
  buildGraphLinks(knowledgePoints) {
    const links = [];

    // 简化实现:将薄弱知识点与其他相关知识点连接
    // 实际应用中应从后端获取 knowledge_relations 数据
    this.data.weakChains.forEach(weakChain => {
      const sourceNode = weakChain.knowledge_point;

      // 查找相关知识点(这里简化为找掌握度相近的点)
      knowledgePoints.forEach(kp => {
        if (
          kp.name !== sourceNode &&
          Math.abs(kp.mastery_level - (weakChain.avg_mastery_level || 0)) < 0.2
        ) {
          links.push({
            source: sourceNode,
            target: kp.name,
            lineStyle: {
              color: '#ccc',
              width: 1,
            },
          });
        }
      });
    });

    return links;
  },

  /**
   * 获取掌握度等级
   */
  getMasteryLevel(level) {
    if (level >= 0.7) return { text: '已掌握', type: 'success' };
    if (level >= 0.4) return { text: '学习中', type: 'warning' };
    return { text: '待加强', type: 'danger' };
  },
};

Page(createGuardedPage(pageObject, 'pages/knowledge-graph/index'));

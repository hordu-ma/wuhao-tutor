/**
 * MCP (Model Context Protocol) 服务管理工具
 * 用于管理个性化上下文和学习分析
 */

const api = require('../api/index.js');
const storage = require('./storage.js');

class MCPService {
  constructor() {
    this.contextCache = null;
    this.lastUpdateTime = 0;
    this.cacheExpiry = 10 * 60 * 1000; // 10分钟缓存
  }

  /**
   * 获取个性化学习上下文
   * @param {string} userId - 用户ID
   * @returns {Promise<Object>} 个性化上下文数据
   */
  async getPersonalizedContext(userId) {
    try {
      // 检查缓存
      if (this.contextCache && this.isCacheValid()) {
        return this.contextCache;
      }

      // 并行获取多种上下文数据
      const [preferences, weaknessAnalysis, errorHistory, progressData] = await Promise.allSettled([
        this.getlearningPreferences(userId),
        this.getWeaknessAnalysis(userId),
        this.getRecentErrors(userId),
        this.getLearningProgress(userId),
      ]);

      // 合并上下文数据
      const preferencesValue = preferences.status === 'fulfilled' ? preferences.value : {};
      const context = {
        timestamp: Date.now(),
        preferences: preferencesValue,
        weaknessPoints: weaknessAnalysis.status === 'fulfilled' ? weaknessAnalysis.value : [],
        recentErrors: errorHistory.status === 'fulfilled' ? errorHistory.value : [],
        progress: progressData.status === 'fulfilled' ? progressData.value : {},
        learningStyle: this.inferLearningStyle(preferencesValue),
      };

      // 更新缓存
      this.contextCache = context;
      this.lastUpdateTime = Date.now();

      // 本地存储备份
      await storage.set('mcp_context', context, { ttl: this.cacheExpiry });

      return context;
    } catch (error) {
      console.error('获取个性化上下文失败:', error);

      // 尝试使用本地缓存
      const localContext = await storage.get('mcp_context');
      if (localContext) {
        return localContext;
      }

      // 返回默认上下文
      return this.getDefaultContext();
    }
  }

  /**
   * 获取学习偏好
   */
  async getlearningPreferences(userId) {
    try {
      const response = await api.user.getPreferences();
      // 判断响应是否成功：检查状态码 200-299 且有数据
      const isSuccess = response && response.statusCode >= 200 && response.statusCode < 300;
      return isSuccess ? response.data : {};
    } catch (error) {
      console.warn('获取学习偏好失败:', error);
      return {};
    }
  }

  /**
   * 获取薄弱知识点分析
   */
  async getWeaknessAnalysis(userId) {
    try {
      const response = await api.analysis.getMastery({ subject: 'all' });

      // 判断响应是否成功：检查状态码 200-299 且有数据
      const isSuccess =
        response &&
        response.statusCode >= 200 &&
        response.statusCode < 300 &&
        response.data &&
        response.data.knowledge_points;

      if (isSuccess) {
        // 找出掌握度低于70%的知识点
        const weakPoints = response.data.knowledge_points
          .filter(point => point.mastery < 0.7)
          .sort((a, b) => a.mastery - b.mastery)
          .slice(0, 10); // 最多10个薄弱点

        return weakPoints.map(point => ({
          name: point.name,
          subject: point.subject,
          mastery: point.mastery,
          weight: this.calculateTimeDecay(point.last_studied),
        }));
      }

      return [];
    } catch (error) {
      console.warn('获取薄弱知识点失败:', error);
      return [];
    }
  }

  /**
   * 获取最近错题
   */
  async getRecentErrors(userId) {
    try {
      // 这里可以调用错题分析API（当后端实现后）
      // const response = await api.analysis.getErrorAnalysis({ days: 30 });

      // 暂时返回模拟数据
      return [];
    } catch (error) {
      console.warn('获取错题历史失败:', error);
      return [];
    }
  }

  /**
   * 获取学习进度
   */
  async getLearningProgress(userId) {
    try {
      const response = await api.analysis.getProgress({ days: 30 });
      // 判断响应是否成功：检查状态码 200-299 且有数据
      const isSuccess = response && response.statusCode >= 200 && response.statusCode < 300;
      return isSuccess ? response.data : {};
    } catch (error) {
      console.warn('获取学习进度失败:', error);
      return {};
    }
  }

  /**
   * 推断学习风格
   */
  inferLearningStyle(preferences) {
    if (!preferences || Object.keys(preferences).length === 0) {
      return 'balanced'; // 默认平衡型
    }

    // 基于偏好推断学习风格
    const styles = ['visual', 'auditory', 'kinesthetic', 'reading', 'balanced'];

    // 简单的推断逻辑，可以根据实际数据优化
    if (preferences.preferred_input === 'image') return 'visual';
    if (preferences.preferred_input === 'voice') return 'auditory';
    if (preferences.learning_pace === 'fast') return 'kinesthetic';
    if (preferences.preferred_subjects?.includes('chinese')) return 'reading';

    return 'balanced';
  }

  /**
   * 计算时间衰减权重
   */
  calculateTimeDecay(lastStudied) {
    if (!lastStudied) return 1.0;

    const now = Date.now();
    const studiedTime = new Date(lastStudied).getTime();
    const daysPassed = (now - studiedTime) / (1000 * 60 * 60 * 24);

    // 指数衰减函数，30天后权重降到原来的50%
    return Math.exp(-daysPassed / 30) * 0.5 + 0.5;
  }

  /**
   * 缓存是否有效
   */
  isCacheValid() {
    return Date.now() - this.lastUpdateTime < this.cacheExpiry;
  }

  /**
   * 获取默认上下文
   */
  getDefaultContext() {
    return {
      timestamp: Date.now(),
      preferences: {},
      weaknessPoints: [],
      recentErrors: [],
      progress: {},
      learningStyle: 'balanced',
    };
  }

  /**
   * 构建AI问答的上下文prompt
   */
  buildContextPrompt(context, question) {
    const prompts = [];

    // 学习风格适配
    if (context.learningStyle) {
      const stylePrompts = {
        visual: '请在回答中多使用图表、图示或结构化的展示方式',
        auditory: '请用清晰的语言表达，可以包含口诀或朗读建议',
        kinesthetic: '请提供具体的操作步骤和实践建议',
        reading: '请提供详细的文字解释和相关阅读材料',
        balanced: '请提供多样化的学习建议',
      };
      prompts.push(stylePrompts[context.learningStyle] || stylePrompts.balanced);
    }

    // 薄弱知识点关注
    if (context.weaknessPoints && context.weaknessPoints.length > 0) {
      const weakPoints = context.weaknessPoints
        .slice(0, 3)
        .map(p => p.name)
        .join('、');
      prompts.push(`用户在${weakPoints}等知识点相对薄弱，请在相关回答中给予更多关注和解释`);
    }

    // 学习进度考虑
    if (context.progress && context.progress.total_study_days > 0) {
      prompts.push(
        `用户已学习${context.progress.total_study_days}天，请根据其学习阶段给出适当难度的内容`,
      );
    }

    return prompts.length > 0 ? `\n\n个性化提示：${prompts.join('；')}` : '';
  }

  /**
   * 分析问题类型并提供相关建议
   */
  async analyzeQuestionType(question) {
    // 简单的问题类型识别
    const patterns = {
      concept: /什么是|定义|概念|解释/,
      procedure: /怎么做|如何|步骤|方法/,
      example: /举例|例子|示例/,
      practice: /练习|习题|练题/,
      comparison: /区别|比较|对比/,
    };

    for (const [type, pattern] of Object.entries(patterns)) {
      if (pattern.test(question)) {
        return type;
      }
    }

    return 'general';
  }

  /**
   * 更新用户学习行为
   */
  async updateLearningBehavior(questionId, questionType, helpful) {
    try {
      // 记录学习行为用于优化个性化推荐
      const behaviorData = {
        questionId,
        questionType,
        helpful,
        timestamp: Date.now(),
      };

      // 本地存储行为记录
      const behaviors = await storage.get('learning_behaviors', []);
      behaviors.push(behaviorData);

      // 保留最近100条记录
      if (behaviors.length > 100) {
        behaviors.splice(0, behaviors.length - 100);
      }

      await storage.set('learning_behaviors', behaviors);

      // 如果有后端接口，可以异步上报
      // api.learning.recordBehavior(behaviorData).catch(console.warn);
    } catch (error) {
      console.warn('更新学习行为失败:', error);
    }
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.contextCache = null;
    this.lastUpdateTime = 0;
    storage.remove('mcp_context');
  }

  /**
   * 强制刷新上下文
   */
  async refreshContext(userId) {
    this.clearCache();
    return await this.getPersonalizedContext(userId);
  }
}

// 创建单例实例
const mcpService = new MCPService();

module.exports = {
  mcpService,
  MCPService,
};

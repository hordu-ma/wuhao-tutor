/**
 * MCP (Model Context Protocol) 上下文工具模块
 * @description 提供个性化上下文服务,用于增强 AI 问答的准确性和个性化
 * @module utils/mcp-context
 */

const mistakesAPI = require('../api/mistakes.js');
const learningAPI = require('../api/learning.js');

/**
 * 获取用户的薄弱知识点
 * @param {Object} params - 查询参数
 * @param {string} [params.subject] - 学科筛选
 * @param {number} [params.limit=10] - 返回数量
 * @returns {Promise<Array>} 薄弱知识点列表
 */
async function getWeakKnowledgePoints(params = {}) {
  try {
    const { subject, limit = 10 } = params;

    // 获取错题统计
    const statsResponse = await mistakesAPI.getMistakeStatistics({ subject });

    if (!statsResponse.success || !statsResponse.data) {
      return [];
    }

    const { weak_knowledge_points } = statsResponse.data;

    if (!weak_knowledge_points || !Array.isArray(weak_knowledge_points)) {
      return [];
    }

    // 按错误次数排序,取前 limit 个
    return weak_knowledge_points
      .sort((a, b) => b.error_count - a.error_count)
      .slice(0, limit)
      .map(item => ({
        knowledge_point: item.knowledge_point,
        error_count: item.error_count,
        difficulty_level: item.difficulty_level,
      }));
  } catch (error) {
    console.error('获取薄弱知识点失败:', error);
    return [];
  }
}

/**
 * 获取用户的学习偏好
 * @returns {Promise<Object>} 学习偏好数据
 */
async function getLearningPreferences() {
  try {
    // 获取问答历史统计
    const questionsResponse = await learningAPI.getQuestions({
      page: 1,
      size: 100, // 获取最近100条问答记录
    });

    if (!questionsResponse.success || !questionsResponse.data) {
      return getDefaultPreferences();
    }

    const questions = questionsResponse.data.items || [];

    // 统计学科偏好
    const subjectCount = {};
    const difficultyCount = {};
    const activeHours = {};

    questions.forEach(q => {
      // 学科统计
      if (q.subject) {
        subjectCount[q.subject] = (subjectCount[q.subject] || 0) + 1;
      }

      // 难度统计
      if (q.difficulty) {
        difficultyCount[q.difficulty] = (difficultyCount[q.difficulty] || 0) + 1;
      }

      // 活跃时间统计
      if (q.created_at) {
        const hour = new Date(q.created_at).getHours();
        activeHours[hour] = (activeHours[hour] || 0) + 1;
      }
    });

    // 找出最常用的学科
    const favoriteSubject = Object.entries(subjectCount).sort((a, b) => b[1] - a[1])[0]?.[0] || '';

    // 找出常见难度
    const commonDifficulty =
      Object.entries(difficultyCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'medium';

    // 找出活跃时段
    const activeTimePeriod = getTimePeriod(
      Object.entries(activeHours).sort((a, b) => b[1] - a[1])[0]?.[0] || 14,
    );

    return {
      favoriteSubject,
      commonDifficulty,
      activeTimePeriod,
      totalQuestions: questions.length,
    };
  } catch (error) {
    console.error('获取学习偏好失败:', error);
    return getDefaultPreferences();
  }
}

/**
 * 获取默认学习偏好
 * @returns {Object} 默认偏好
 */
function getDefaultPreferences() {
  return {
    favoriteSubject: '',
    commonDifficulty: 'medium',
    activeTimePeriod: 'afternoon',
    totalQuestions: 0,
  };
}

/**
 * 根据小时数获取时段
 * @param {number} hour - 小时(0-23)
 * @returns {string} 时段名称
 */
function getTimePeriod(hour) {
  if (hour >= 6 && hour < 12) return 'morning';
  if (hour >= 12 && hour < 18) return 'afternoon';
  if (hour >= 18 && hour < 22) return 'evening';
  return 'night';
}

/**
 * 构建 MCP 上下文对象
 * @param {Object} params - 参数
 * @param {string} [params.subject] - 当前学科
 * @param {string} [params.grade] - 年级
 * @returns {Promise<Object>} MCP 上下文
 */
async function buildMCPContext(params = {}) {
  try {
    const { subject, grade } = params;

    // 并行获取数据
    const [weakPoints, preferences] = await Promise.all([
      getWeakKnowledgePoints({ subject, limit: 5 }),
      getLearningPreferences(),
    ]);

    return {
      // 薄弱知识点
      weak_knowledge_points: weakPoints.map(p => p.knowledge_point),

      // 学习偏好
      preferences: {
        favorite_subject: preferences.favoriteSubject,
        common_difficulty: preferences.commonDifficulty,
        active_time_period: preferences.activeTimePeriod,
      },

      // 当前上下文
      current_context: {
        subject: subject || preferences.favoriteSubject,
        grade: grade || '',
      },

      // 元数据
      metadata: {
        total_questions: preferences.totalQuestions,
        weak_points_count: weakPoints.length,
        generated_at: new Date().toISOString(),
      },
    };
  } catch (error) {
    console.error('构建 MCP 上下文失败:', error);
    return {
      weak_knowledge_points: [],
      preferences: getDefaultPreferences(),
      current_context: { subject: '', grade: '' },
      metadata: {
        total_questions: 0,
        weak_points_count: 0,
        generated_at: new Date().toISOString(),
      },
    };
  }
}

/**
 * 格式化 MCP 上下文为提示文本
 * @param {Object} context - MCP 上下文对象
 * @returns {string} 格式化后的文本
 */
function formatMCPContextToPrompt(context) {
  const parts = [];

  // 薄弱知识点
  if (context.weak_knowledge_points && context.weak_knowledge_points.length > 0) {
    parts.push(`学生的薄弱知识点包括: ${context.weak_knowledge_points.join('、')}`);
  }

  // 学科偏好
  if (context.preferences?.favorite_subject) {
    parts.push(`学生常学习的科目: ${context.preferences.favorite_subject}`);
  }

  // 难度偏好
  if (context.preferences?.common_difficulty) {
    const difficultyMap = {
      easy: '简单',
      medium: '中等',
      hard: '困难',
    };
    parts.push(`学生偏好的难度: ${difficultyMap[context.preferences.common_difficulty] || '中等'}`);
  }

  // 当前上下文
  if (context.current_context?.subject) {
    parts.push(`当前学科: ${context.current_context.subject}`);
  }

  return parts.length > 0 ? `【学生个性化信息】\n${parts.join('\n')}\n` : '';
}

/**
 * 缓存 MCP 上下文到本地存储
 * @param {Object} context - MCP 上下文
 * @param {number} [expireMinutes=60] - 过期时间(分钟)
 */
function cacheMCPContext(context, expireMinutes = 60) {
  try {
    const cacheData = {
      context,
      expireAt: Date.now() + expireMinutes * 60 * 1000,
    };

    wx.setStorageSync('mcp_context_cache', cacheData);
    console.log('MCP 上下文已缓存', { expireMinutes });
  } catch (error) {
    console.error('缓存 MCP 上下文失败:', error);
  }
}

/**
 * 从本地存储获取缓存的 MCP 上下文
 * @returns {Object|null} MCP 上下文或 null
 */
function getCachedMCPContext() {
  try {
    const cacheData = wx.getStorageSync('mcp_context_cache');

    if (!cacheData) {
      return null;
    }

    // 检查是否过期
    if (Date.now() > cacheData.expireAt) {
      wx.removeStorageSync('mcp_context_cache');
      console.log('MCP 上下文缓存已过期');
      return null;
    }

    console.log('使用缓存的 MCP 上下文');
    return cacheData.context;
  } catch (error) {
    console.error('获取缓存的 MCP 上下文失败:', error);
    return null;
  }
}

/**
 * 获取 MCP 上下文(优先使用缓存)
 * @param {Object} params - 参数
 * @param {boolean} [params.forceRefresh=false] - 是否强制刷新
 * @returns {Promise<Object>} MCP 上下文
 */
async function getMCPContext(params = {}) {
  const { forceRefresh = false, ...buildParams } = params;

  // 如果不强制刷新,先尝试获取缓存
  if (!forceRefresh) {
    const cached = getCachedMCPContext();
    if (cached) {
      return cached;
    }
  }

  // 构建新的上下文
  const context = await buildMCPContext(buildParams);

  // 缓存上下文
  cacheMCPContext(context);

  return context;
}

module.exports = {
  getWeakKnowledgePoints,
  getLearningPreferences,
  buildMCPContext,
  formatMCPContextToPrompt,
  cacheMCPContext,
  getCachedMCPContext,
  getMCPContext,
};

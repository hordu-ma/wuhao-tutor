// 五好伴学小程序 - 数据处理 Web Worker
// Data Processing Web Worker for Wuhao Tutor Mini Program

/**
 * 数据处理 Worker
 * 用于处理大量数据计算，避免阻塞主线程
 */

// Worker 初始化
console.log('📊 数据处理 Worker 已启动');

/**
 * 处理学习数据分析
 * @param {Array} homeworkData 作业数据
 * @param {Array} chatData 问答数据
 * @returns {Object} 分析结果
 */
function processLearningAnalysis(homeworkData, chatData) {
  const result = {
    homeworkStats: processHomeworkStats(homeworkData),
    chatStats: processChatStats(chatData),
    learningTrends: calculateLearningTrends(homeworkData, chatData),
    subjectAnalysis: analyzeSubjectPerformance(homeworkData),
    recommendations: generateRecommendations(homeworkData, chatData),
    timestamp: Date.now()
  };

  return result;
}

/**
 * 处理作业统计数据
 * @param {Array} homeworkData 作业数据
 * @returns {Object} 作业统计结果
 */
function processHomeworkStats(homeworkData) {
  if (!Array.isArray(homeworkData) || homeworkData.length === 0) {
    return {
      total: 0,
      completed: 0,
      pending: 0,
      overdue: 0,
      averageScore: 0,
      completionRate: 0
    };
  }

  const total = homeworkData.length;
  const completed = homeworkData.filter(hw => hw.status === 'completed').length;
  const pending = homeworkData.filter(hw => hw.status === 'pending').length;
  const overdue = homeworkData.filter(hw => hw.status === 'overdue').length;

  const scores = homeworkData
    .filter(hw => hw.score !== null && hw.score !== undefined)
    .map(hw => hw.score);

  const averageScore = scores.length > 0
    ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length * 100) / 100
    : 0;

  const completionRate = total > 0 ? Math.round((completed / total) * 10000) / 100 : 0;

  return {
    total,
    completed,
    pending,
    overdue,
    averageScore,
    completionRate,
    totalWithScores: scores.length
  };
}

/**
 * 处理问答统计数据
 * @param {Array} chatData 问答数据
 * @returns {Object} 问答统计结果
 */
function processChatStats(chatData) {
  if (!Array.isArray(chatData) || chatData.length === 0) {
    return {
      total: 0,
      todayCount: 0,
      weekCount: 0,
      monthCount: 0,
      subjectDistribution: {},
      avgResponseTime: 0
    };
  }

  const now = Date.now();
  const oneDayMs = 24 * 60 * 60 * 1000;
  const oneWeekMs = 7 * oneDayMs;
  const oneMonthMs = 30 * oneDayMs;

  const todayCount = chatData.filter(chat =>
    now - new Date(chat.createTime).getTime() < oneDayMs
  ).length;

  const weekCount = chatData.filter(chat =>
    now - new Date(chat.createTime).getTime() < oneWeekMs
  ).length;

  const monthCount = chatData.filter(chat =>
    now - new Date(chat.createTime).getTime() < oneMonthMs
  ).length;

  // 学科分布统计
  const subjectDistribution = {};
  chatData.forEach(chat => {
    const subject = chat.subject || '其他';
    subjectDistribution[subject] = (subjectDistribution[subject] || 0) + 1;
  });

  // 平均响应时间计算
  const responseTimes = chatData
    .filter(chat => chat.responseTime && chat.responseTime > 0)
    .map(chat => chat.responseTime);

  const avgResponseTime = responseTimes.length > 0
    ? Math.round(responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length)
    : 0;

  return {
    total: chatData.length,
    todayCount,
    weekCount,
    monthCount,
    subjectDistribution,
    avgResponseTime
  };
}

/**
 * 计算学习趋势
 * @param {Array} homeworkData 作业数据
 * @param {Array} chatData 问答数据
 * @returns {Object} 学习趋势数据
 */
function calculateLearningTrends(homeworkData, chatData) {
  const trends = {
    daily: [],
    weekly: [],
    monthly: []
  };

  // 计算最近7天的学习趋势
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const homeworkCount = homeworkData.filter(hw => {
      const hwDate = new Date(hw.createTime).toISOString().split('T')[0];
      return hwDate === dateStr;
    }).length;

    const chatCount = chatData.filter(chat => {
      const chatDate = new Date(chat.createTime).toISOString().split('T')[0];
      return chatDate === dateStr;
    }).length;

    trends.daily.push({
      date: dateStr,
      homework: homeworkCount,
      chat: chatCount,
      total: homeworkCount + chatCount
    });
  }

  // 计算最近4周的学习趋势
  for (let i = 3; i >= 0; i--) {
    const endDate = new Date(now);
    endDate.setDate(endDate.getDate() - i * 7);
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 6);

    const homeworkCount = homeworkData.filter(hw => {
      const hwTime = new Date(hw.createTime).getTime();
      return hwTime >= startDate.getTime() && hwTime <= endDate.getTime();
    }).length;

    const chatCount = chatData.filter(chat => {
      const chatTime = new Date(chat.createTime).getTime();
      return chatTime >= startDate.getTime() && chatTime <= endDate.getTime();
    }).length;

    trends.weekly.push({
      week: `${startDate.getMonth() + 1}/${startDate.getDate()}-${endDate.getMonth() + 1}/${endDate.getDate()}`,
      homework: homeworkCount,
      chat: chatCount,
      total: homeworkCount + chatCount
    });
  }

  return trends;
}

/**
 * 分析学科表现
 * @param {Array} homeworkData 作业数据
 * @returns {Object} 学科分析结果
 */
function analyzeSubjectPerformance(homeworkData) {
  const subjectStats = {};

  homeworkData.forEach(hw => {
    const subject = hw.subject || '其他';

    if (!subjectStats[subject]) {
      subjectStats[subject] = {
        total: 0,
        completed: 0,
        scores: [],
        averageScore: 0,
        completionRate: 0,
        trend: 'stable'
      };
    }

    subjectStats[subject].total++;

    if (hw.status === 'completed') {
      subjectStats[subject].completed++;
      if (hw.score !== null && hw.score !== undefined) {
        subjectStats[subject].scores.push(hw.score);
      }
    }
  });

  // 计算各学科的平均分和完成率
  Object.keys(subjectStats).forEach(subject => {
    const stats = subjectStats[subject];
    const scores = stats.scores;

    stats.averageScore = scores.length > 0
      ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length * 100) / 100
      : 0;

    stats.completionRate = stats.total > 0
      ? Math.round((stats.completed / stats.total) * 10000) / 100
      : 0;

    // 简单的趋势分析（基于最近的成绩）
    if (scores.length >= 3) {
      const recentScores = scores.slice(-3);
      const earlierScores = scores.slice(0, -3);

      if (earlierScores.length > 0) {
        const recentAvg = recentScores.reduce((sum, score) => sum + score, 0) / recentScores.length;
        const earlierAvg = earlierScores.reduce((sum, score) => sum + score, 0) / earlierScores.length;

        if (recentAvg > earlierAvg + 5) {
          stats.trend = 'improving';
        } else if (recentAvg < earlierAvg - 5) {
          stats.trend = 'declining';
        } else {
          stats.trend = 'stable';
        }
      }
    }
  });

  return subjectStats;
}

/**
 * 生成学习建议
 * @param {Array} homeworkData 作业数据
 * @param {Array} chatData 问答数据
 * @returns {Array} 建议列表
 */
function generateRecommendations(homeworkData, chatData) {
  const recommendations = [];

  // 分析作业完成情况
  const homeworkStats = processHomeworkStats(homeworkData);

  if (homeworkStats.completionRate < 70) {
    recommendations.push({
      type: 'homework',
      priority: 'high',
      title: '提高作业完成率',
      description: `当前作业完成率为 ${homeworkStats.completionRate}%，建议制定学习计划，确保按时完成作业。`,
      actionText: '查看学习计划'
    });
  }

  if (homeworkStats.averageScore < 70 && homeworkStats.totalWithScores > 0) {
    recommendations.push({
      type: 'performance',
      priority: 'high',
      title: '加强基础知识学习',
      description: `当前平均分为 ${homeworkStats.averageScore} 分，建议复习基础知识点。`,
      actionText: '开始复习'
    });
  }

  // 分析问答活跃度
  const chatStats = processChatStats(chatData);

  if (chatStats.todayCount === 0 && chatStats.weekCount < 3) {
    recommendations.push({
      type: 'engagement',
      priority: 'medium',
      title: '增加学习互动',
      description: '最近问答较少，建议多与AI助手互动，及时解决学习疑问。',
      actionText: '开始问答'
    });
  }

  // 分析学科平衡
  const subjectStats = analyzeSubjectPerformance(homeworkData);
  const subjects = Object.keys(subjectStats);

  if (subjects.length > 1) {
    const lowestSubject = subjects.reduce((lowest, current) => {
      return subjectStats[current].averageScore < subjectStats[lowest].averageScore
        ? current : lowest;
    });

    if (subjectStats[lowestSubject].averageScore < 60) {
      recommendations.push({
        type: 'subject',
        priority: 'medium',
        title: `加强${lowestSubject}学习`,
        description: `${lowestSubject}的平均分较低（${subjectStats[lowestSubject].averageScore}分），建议重点关注。`,
        actionText: `学习${lowestSubject}`
      });
    }
  }

  // 正面鼓励
  if (homeworkStats.completionRate >= 90) {
    recommendations.push({
      type: 'praise',
      priority: 'low',
      title: '学习表现优秀！',
      description: `作业完成率达到 ${homeworkStats.completionRate}%，继续保持！`,
      actionText: '查看成就'
    });
  }

  // 按优先级排序
  const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
  recommendations.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

  return recommendations.slice(0, 5); // 最多返回5条建议
}

/**
 * 处理图像数据压缩
 * @param {ArrayBuffer} imageData 图像数据
 * @param {Object} options 压缩选项
 * @returns {ArrayBuffer} 压缩后的图像数据
 */
function compressImageData(imageData, options = {}) {
  const {
    quality = 0.8,
    maxWidth = 1920,
    maxHeight = 1920,
    format = 'jpeg'
  } = options;

  // 这里是一个简化的图像处理示例
  // 实际应用中需要使用专门的图像处理库
  console.log(`🖼️ 压缩图像: 质量=${quality}, 最大尺寸=${maxWidth}x${maxHeight}, 格式=${format}`);

  // 模拟压缩处理
  return imageData;
}

/**
 * 处理大批量数据导出
 * @param {Object} data 要导出的数据
 * @param {string} format 导出格式
 * @returns {string} 导出结果
 */
function exportLearningData(data, format = 'json') {
  let result = '';

  switch (format) {
    case 'csv':
      result = convertToCSV(data);
      break;
    case 'json':
      result = JSON.stringify(data, null, 2);
      break;
    case 'txt':
      result = convertToText(data);
      break;
    default:
      result = JSON.stringify(data);
  }

  return result;
}

/**
 * 转换为CSV格式
 * @param {Object} data 数据
 * @returns {string} CSV字符串
 */
function convertToCSV(data) {
  if (!data.homework || !Array.isArray(data.homework)) {
    return '';
  }

  const headers = ['日期', '科目', '题目', '状态', '得分', '用时(分钟)'];
  const rows = [headers.join(',')];

  data.homework.forEach(hw => {
    const row = [
      hw.createTime ? new Date(hw.createTime).toLocaleDateString() : '',
      hw.subject || '',
      `"${hw.title || ''}"`, // 用引号包围标题，防止逗号问题
      hw.status || '',
      hw.score || '',
      hw.duration || ''
    ];
    rows.push(row.join(','));
  });

  return rows.join('\n');
}

/**
 * 转换为文本格式
 * @param {Object} data 数据
 * @returns {string} 文本字符串
 */
function convertToText(data) {
  let text = '=== 五好伴学 学习报告 ===\n\n';

  text += `生成时间: ${new Date().toLocaleString()}\n\n`;

  if (data.stats) {
    text += '--- 学习统计 ---\n';
    text += `总作业数: ${data.stats.homework?.total || 0}\n`;
    text += `完成率: ${data.stats.homework?.completionRate || 0}%\n`;
    text += `平均分: ${data.stats.homework?.averageScore || 0}\n`;
    text += `总问答数: ${data.stats.chat?.total || 0}\n\n`;
  }

  if (data.recommendations && data.recommendations.length > 0) {
    text += '--- 学习建议 ---\n';
    data.recommendations.forEach((rec, index) => {
      text += `${index + 1}. ${rec.title}\n`;
      text += `   ${rec.description}\n\n`;
    });
  }

  return text;
}

// 监听主线程消息
self.addEventListener('message', function (e) {
  const { type, data, id } = e.data;
  let result;

  try {
    switch (type) {
      case 'PROCESS_LEARNING_ANALYSIS':
        result = processLearningAnalysis(data.homework, data.chat);
        break;

      case 'PROCESS_HOMEWORK_STATS':
        result = processHomeworkStats(data);
        break;

      case 'PROCESS_CHAT_STATS':
        result = processChatStats(data);
        break;

      case 'CALCULATE_TRENDS':
        result = calculateLearningTrends(data.homework, data.chat);
        break;

      case 'ANALYZE_SUBJECTS':
        result = analyzeSubjectPerformance(data);
        break;

      case 'GENERATE_RECOMMENDATIONS':
        result = generateRecommendations(data.homework, data.chat);
        break;

      case 'COMPRESS_IMAGE':
        result = compressImageData(data.imageData, data.options);
        break;

      case 'EXPORT_DATA':
        result = exportLearningData(data.data, data.format);
        break;

      default:
        throw new Error(`未知的处理类型: ${type}`);
    }

    // 发送成功结果
    self.postMessage({
      id,
      type: 'SUCCESS',
      result
    });

  } catch (error) {
    console.error('Worker 处理错误:', error);

    // 发送错误结果
    self.postMessage({
      id,
      type: 'ERROR',
      error: {
        message: error.message,
        stack: error.stack
      }
    });
  }
});

// Worker 错误处理
self.addEventListener('error', function (error) {
  console.error('Worker 运行时错误:', error);

  self.postMessage({
    type: 'RUNTIME_ERROR',
    error: {
      message: error.message,
      filename: error.filename,
      lineno: error.lineno,
      colno: error.colno
    }
  });
});

// Worker 未捕获异常处理
self.addEventListener('unhandledrejection', function (event) {
  console.error('Worker 未处理的 Promise 拒绝:', event.reason);

  self.postMessage({
    type: 'UNHANDLED_REJECTION',
    error: {
      reason: event.reason?.toString() || 'Unknown error'
    }
  });
});

console.log('✅ 数据处理 Worker 初始化完成');

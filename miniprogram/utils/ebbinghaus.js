/**
 * 艾宾浩斯遗忘曲线算法模块
 * @description 基于艾宾浩斯遗忘曲线理论,计算错题复习时间
 * @module utils/ebbinghaus
 */

/**
 * 艾宾浩斯遗忘曲线复习间隔(天数)
 * 根据心理学研究,人的记忆遵循一定的遗忘规律
 */
const REVIEW_INTERVALS = [
  1,   // 第1次复习: 1天后
  2,   // 第2次复习: 2天后
  4,   // 第3次复习: 4天后
  7,   // 第4次复习: 7天后
  15,  // 第5次复习: 15天后
  30,  // 第6次复习: 30天后
  60,  // 第7次复习: 60天后
  90   // 第8次复习: 90天后
];

/**
 * 掌握状态定义
 */
const MASTERY_STATUS = {
  NOT_MASTERED: 'not_mastered',    // 未掌握
  REVIEWING: 'reviewing',          // 复习中
  MASTERED: 'mastered'             // 已掌握
};

/**
 * 复习成功阈值
 * 连续正确次数达到此值,认为已掌握
 */
const MASTERY_THRESHOLD = 3;

/**
 * 计算下次复习时间
 * @param {number} reviewCount - 已复习次数
 * @param {Date} lastReviewDate - 上次复习时间
 * @param {boolean} isCorrect - 本次是否答对
 * @returns {Date} 下次复习时间
 */
function calculateNextReviewDate(reviewCount, lastReviewDate = new Date(), isCorrect = true) {
  // 如果答错,重新开始复习周期
  if (!isCorrect) {
    reviewCount = 0;
  }

  // 获取对应的间隔天数
  const intervalIndex = Math.min(reviewCount, REVIEW_INTERVALS.length - 1);
  const intervalDays = REVIEW_INTERVALS[intervalIndex];

  // 计算下次复习时间
  const nextReviewDate = new Date(lastReviewDate);
  nextReviewDate.setDate(nextReviewDate.getDate() + intervalDays);

  return nextReviewDate;
}

/**
 * 判断掌握状态
 * @param {number} reviewCount - 已复习次数
 * @param {number} correctCount - 连续正确次数
 * @param {number} correctRate - 总体正确率(0-100)
 * @returns {string} 掌握状态
 */
function getMasteryStatus(reviewCount, correctCount, correctRate) {
  // 未开始复习
  if (reviewCount === 0) {
    return MASTERY_STATUS.NOT_MASTERED;
  }

  // 连续正确次数达到阈值,且正确率足够高
  if (correctCount >= MASTERY_THRESHOLD && correctRate >= 80) {
    return MASTERY_STATUS.MASTERED;
  }

  // 复习中
  return MASTERY_STATUS.REVIEWING;
}

/**
 * 更新复习记录
 * @param {Object} mistake - 错题对象
 * @param {boolean} isCorrect - 本次是否答对
 * @returns {Object} 更新后的错题数据
 */
function updateReviewRecord(mistake, isCorrect) {
  const now = new Date();

  // 初始化或获取现有数据
  const reviewCount = (mistake.review_count || 0) + 1;
  const correctCount = isCorrect ? (mistake.correct_count || 0) + 1 : 0;
  const totalAttempts = reviewCount;
  const correctAttempts = (mistake.correct_attempts || 0) + (isCorrect ? 1 : 0);
  const correctRate = Math.round((correctAttempts / totalAttempts) * 100);

  // 计算下次复习时间
  const nextReviewDate = calculateNextReviewDate(
    isCorrect ? reviewCount : 0,
    now,
    isCorrect
  );

  // 判断掌握状态
  const masteryStatus = getMasteryStatus(reviewCount, correctCount, correctRate);

  // 更新复习历史
  const reviewHistory = mistake.review_history || [];
  reviewHistory.push({
    review_date: now.toISOString(),
    is_correct: isCorrect,
    review_count: reviewCount
  });

  return {
    ...mistake,
    review_count: reviewCount,
    correct_count: correctCount,
    correct_attempts: correctAttempts,
    correct_rate: correctRate,
    last_review_date: now.toISOString(),
    next_review_date: masteryStatus === MASTERY_STATUS.MASTERED 
      ? null 
      : nextReviewDate.toISOString(),
    mastery_status: masteryStatus,
    review_history: reviewHistory,
    updated_at: now.toISOString()
  };
}

/**
 * 判断是否需要复习
 * @param {string} nextReviewDate - 下次复习时间(ISO字符串)
 * @returns {boolean} 是否需要复习
 */
function isNeedReview(nextReviewDate) {
  if (!nextReviewDate) {
    return false;
  }

  const now = new Date();
  const reviewDate = new Date(nextReviewDate);

  return reviewDate <= now;
}

/**
 * 获取今日复习列表
 * @param {Array<Object>} mistakes - 错题列表
 * @returns {Array<Object>} 今日需要复习的错题
 */
function getTodayReviewList(mistakes) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  return mistakes.filter(mistake => {
    // 已掌握的不需要复习
    if (mistake.mastery_status === MASTERY_STATUS.MASTERED) {
      return false;
    }

    // 没有下次复习时间,说明还未开始复习
    if (!mistake.next_review_date) {
      return true;
    }

    // 检查是否到达复习时间
    const reviewDate = new Date(mistake.next_review_date);
    return reviewDate <= now;
  });
}

/**
 * 获取复习统计信息
 * @param {Array<Object>} mistakes - 错题列表
 * @returns {Object} 统计信息
 */
function getReviewStatistics(mistakes) {
  const total = mistakes.length;
  let notMastered = 0;
  let reviewing = 0;
  let mastered = 0;
  let needReviewToday = 0;

  mistakes.forEach(mistake => {
    switch (mistake.mastery_status) {
      case MASTERY_STATUS.NOT_MASTERED:
        notMastered++;
        break;
      case MASTERY_STATUS.REVIEWING:
        reviewing++;
        break;
      case MASTERY_STATUS.MASTERED:
        mastered++;
        break;
    }

    if (isNeedReview(mistake.next_review_date)) {
      needReviewToday++;
    }
  });

  return {
    total,
    notMastered,
    reviewing,
    mastered,
    needReviewToday,
    masteryRate: total > 0 ? Math.round((mastered / total) * 100) : 0
  };
}

/**
 * 计算复习效率
 * @param {Array<Object>} reviewHistory - 复习历史
 * @param {number} days - 统计天数(默认30天)
 * @returns {Object} 复习效率数据
 */
function calculateReviewEfficiency(reviewHistory, days = 30) {
  const now = new Date();
  const startDate = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

  const recentReviews = reviewHistory.filter(record => {
    const reviewDate = new Date(record.review_date);
    return reviewDate >= startDate;
  });

  const totalReviews = recentReviews.length;
  const correctReviews = recentReviews.filter(r => r.is_correct).length;
  const correctRate = totalReviews > 0 
    ? Math.round((correctReviews / totalReviews) * 100) 
    : 0;

  return {
    totalReviews,
    correctReviews,
    correctRate,
    averagePerDay: Math.round(totalReviews / days * 10) / 10
  };
}

module.exports = {
  REVIEW_INTERVALS,
  MASTERY_STATUS,
  MASTERY_THRESHOLD,
  calculateNextReviewDate,
  getMasteryStatus,
  updateReviewRecord,
  isNeedReview,
  getTodayReviewList,
  getReviewStatistics,
  calculateReviewEfficiency
};

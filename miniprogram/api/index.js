// api/index.js
// 五好伴学小程序 - API 模块统一导出

const homeworkAPI = require('./homework.js');
const learningAPI = require('./learning.js');
const analysisAPI = require('./analysis.js');
const userAPI = require('./user.js');
const mistakesAPI = require('./mistakes.js');

/**
 * API 模块集合
 * 统一管理所有业务 API
 */
const api = {
  // 用户管理模块
  user: userAPI,

  // 作业批改模块（兼容性保留）
  homework: homeworkAPI,

  // 学习问答模块（重新定位为作业问答）
  learning: learningAPI,

  // 学情分析模块
  analysis: analysisAPI,

  // 错题手册模块（新增核心模块）
  mistakes: mistakesAPI,
};

module.exports = api;

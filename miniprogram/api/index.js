// api/index.js
// 五好伴学小程序 - API 模块统一导出

const homeworkAPI = require('./homework.js');
const learningAPI = require('./learning.js');
const analysisAPI = require('./analysis.js');

/**
 * API 模块集合
 * 统一管理所有业务 API
 */
const api = {
  // 作业批改模块
  homework: homeworkAPI,

  // 学习问答模块
  learning: learningAPI,

  // 学情分析模块
  analysis: analysisAPI,

  // TODO: 其他业务模块
  // user: require('./user.js'),
  // auth: require('./auth.js'),
};

module.exports = api;

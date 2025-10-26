// api/index.js
// 五好伴学小程序 - API 模块统一导出

// const homeworkAPI = require('./homework.js'); // 已备份至 backup/miniprogram/api/homework.js
const learningAPI = require('./learning.js');
const analysisAPI = require('./analysis.js');
const userAPI = require('./user.js');
const mistakesAPI = require('./mistakes.js');
const fileAPI = require('./file.js');
const config = require('../config/index.js');

/**
 * API 模块集合
 * 统一管理所有业务 API
 */
const api = {
  // 用户管理模块
  user: userAPI,

  // 作业批改模块（已移除，功能已由 learning 模块覆盖）
  // homework: homeworkAPI,

  // 学习问答模块（作业问答核心功能）
  learning: learningAPI,

  // chat 别名，兼容旧代码
  chat: learningAPI,

  // 学情分析模块
  analysis: analysisAPI,

  // 错题手册模块
  mistakes: mistakesAPI,

  // 文件上传模块
  file: fileAPI,

  // 基础URL，供wx.uploadFile等API使用
  baseUrl: config.api.baseUrl,
};

module.exports = api;

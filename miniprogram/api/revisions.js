/**
 * 复习计划 API 模块
 * @description 封装复习计划相关的后端 API 调用
 * @module api/revisions
 */

const { request } = require('../utils/request.js');

/**
 * 复习计划 API
 */
const revisionsAPI = {
  /**
   * 生成复习计划
   * @param {Object} data - 生成参数
   * @param {string} data.title - 计划标题
   * @param {string} [data.subject] - 学科
   * @param {string} [data.start_date] - 开始日期 (YYYY-MM-DD)
   * @param {string} [data.end_date] - 结束日期 (YYYY-MM-DD)
   * @param {Array<string>} [data.mistake_ids] - 指定错题ID列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 生成结果
   */
  generateRevisionPlan(data, config = {}) {
    return request.post('revisions/generate', data, {
      showLoading: true,
      loadingText: '生成中...',
      ...config,
    });
  },

  /**
   * 获取复习计划列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.page_size=20] - 每页数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 计划列表
   */
  getRevisionPlanList(params = {}, config = {}) {
    const queryParams = {
      page: params.page || 1,
      page_size: params.page_size || 20,
    };

    return request.get('revisions', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取复习计划详情
   * @param {string} id - 计划 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 计划详情
   */
  getRevisionPlanDetail(id, config = {}) {
    return request.get(`revisions/${id}`, {}, {
      showLoading: true,
      ...config,
    });
  },

  /**
   * 删除复习计划
   * @param {string} id - 计划 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<void>}
   */
  deleteRevisionPlan(id, config = {}) {
    return request.delete(`revisions/${id}`, {}, {
      showLoading: true,
      loadingText: '删除中...',
      ...config,
    });
  },

  /**
   * 下载复习计划
   * @param {string} id - 计划 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 下载链接信息
   */
  downloadRevisionPlan(id, config = {}) {
    return request.get(`revisions/${id}/download`, {}, {
      showLoading: true,
      ...config,
    });
  },
};

module.exports = revisionsAPI;

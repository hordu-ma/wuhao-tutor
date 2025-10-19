// api/file.js
// 五好伴学小程序 - 文件上传 API

const request = require('../utils/request.js');

/**
 * 文件上传相关的API接口
 */
const fileAPI = {
  /**
   * 上传图片供AI分析
   * @param {Object} params - 上传参数
   * @param {string} params.filePath - 本地文件路径
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 上传结果
   */
  uploadImage(params, config = {}) {
    if (!params || !params.filePath) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '文件路径不能为空',
      });
    }

    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: request.getBaseUrl() + '/files/upload-image-for-learning',
        filePath: params.filePath,
        name: 'file',
        header: {
          Authorization: wx.getStorageSync('token') ? `Bearer ${wx.getStorageSync('token')}` : '',
        },
        success(res) {
          try {
            let data = res.data;
            if (typeof data === 'string') {
              data = JSON.parse(data);
            }
            if (data.success) {
              resolve(data);
            } else {
              reject(data);
            }
          } catch (error) {
            reject({
              code: 'PARSE_ERROR',
              message: '解析上传结果失败',
              details: error.message,
            });
          }
        },
        fail(error) {
          reject({
            code: 'UPLOAD_ERROR',
            message: '文件上传失败',
            details: error,
          });
        },
        ...config,
      });
    });
  },

  /**
   * 上传学习问答图片（别名方法）
   * @param {Object} params - 上传参数
   * @param {string} params.filePath - 本地文件路径
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 上传结果
   */
  uploadLearningImage(params, config = {}) {
    return this.uploadImage(params, config);
  },
};

module.exports = fileAPI;

// api/homework.js
// 作业批改 API 接口模块

const { request } = require('../utils/request.js');

/**
 * 作业批改 API
 */
const homeworkAPI = {
  /**
   * 获取作业模板列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.subject] - 学科筛选
   * @returns {Promise<{success: boolean, data: Array, message: string}>}
   */
  getTemplates(params = {}) {
    return request.get('api/v1/homework/templates', params, {
      showLoading: false,
    });
  },

  /**
   * 获取作业模板详情
   * @param {string} templateId - 模板ID
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  getTemplateDetail(templateId) {
    return request.get(`api/v1/homework/templates/${templateId}`, {}, {
      showLoading: true,
      loadingText: '加载中...',
    });
  },

  /**
   * 创建作业模板
   * @param {Object} data - 模板数据
   * @param {string} data.name - 模板名称
   * @param {string} data.subject - 学科
   * @param {string} data.description - 模板描述
   * @param {number} [data.max_score=100] - 最高分数
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  createTemplate(data) {
    return request.post('api/v1/homework/templates', data, {
      showLoading: true,
      loadingText: '创建中...',
      showError: true,
    });
  },

  /**
   * 提交作业（文本形式）
   * @param {Object} data - 提交数据
   * @param {string} data.template_id - 作业模板ID
   * @param {string} data.student_name - 学生姓名
   * @param {string} data.content - 作业内容
   * @param {string} [data.additional_info] - 附加信息
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  submitHomeworkText(data) {
    return request.post('api/v1/homework/submissions', data, {
      showLoading: true,
      loadingText: '提交中...',
      showError: true,
    });
  },

  /**
   * 提交作业（图片形式）
   * @param {Object} params - 提交参数
   * @param {string} params.template_id - 作业模板ID
   * @param {string} params.student_name - 学生姓名
   * @param {string} params.filePath - 本地图片路径
   * @param {string} [params.additional_info] - 附加信息
   * @param {Function} [params.onProgress] - 上传进度回调
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  submitHomeworkImage({ template_id, student_name, filePath, additional_info, onProgress }) {
    const formData = {
      template_id,
      student_name,
    };

    if (additional_info) {
      formData.additional_info = additional_info;
    }

    return request.upload(
      'api/v1/homework/submissions',
      filePath,
      'homework_file',
      formData,
      {
        showLoading: true,
        loadingText: '上传中...',
        showError: true,
        onProgress,
      }
    );
  },

  /**
   * 批量提交作业图片
   * @param {Object} params - 提交参数
   * @param {string} params.template_id - 作业模板ID
   * @param {string} params.student_name - 学生姓名
   * @param {Array<string>} params.filePaths - 本地图片路径数组
   * @param {string} [params.additional_info] - 附加信息
   * @param {Function} [params.onProgress] - 上传进度回调
   * @returns {Promise<Array<{success: boolean, data: Object, message: string}>>}
   */
  async submitHomeworkImages({ template_id, student_name, filePaths, additional_info, onProgress }) {
    const results = [];

    for (let i = 0; i < filePaths.length; i++) {
      const filePath = filePaths[i];

      try {
        const result = await this.submitHomeworkImage({
          template_id,
          student_name,
          filePath,
          additional_info: additional_info ? `${additional_info} (${i + 1}/${filePaths.length})` : undefined,
          onProgress: onProgress ? (progress) => {
            // 计算总体进度
            const totalProgress = Math.floor(
              ((i + progress.progress / 100) / filePaths.length) * 100
            );
            onProgress({
              ...progress,
              current: i + 1,
              total: filePaths.length,
              totalProgress,
            });
          } : undefined,
        });

        results.push(result);
      } catch (error) {
        console.error(`上传第 ${i + 1} 张图片失败:`, error);
        results.push({
          success: false,
          error: error.message || '上传失败',
          filePath,
        });
      }
    }

    return results;
  },

  /**
   * 获取作业提交列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.template_id] - 模板ID筛选
   * @param {string} [params.status] - 状态筛选：pending/processing/completed/failed
   * @returns {Promise<{success: boolean, data: Array, message: string}>}
   */
  getSubmissions(params = {}) {
    return request.get('api/v1/homework/submissions', params, {
      showLoading: false,
    });
  },

  /**
   * 获取作业提交详情
   * @param {string} submissionId - 提交记录ID
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  getSubmissionDetail(submissionId) {
    return request.get(`api/v1/homework/submissions/${submissionId}`, {}, {
      showLoading: true,
      loadingText: '加载中...',
    });
  },

  /**
   * 获取作业批改结果
   * @param {string} submissionId - 提交记录ID
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  getCorrectionResult(submissionId) {
    return request.get(`api/v1/homework/submissions/${submissionId}/correction`, {}, {
      showLoading: true,
      loadingText: '获取批改结果...',
      showError: true,
    });
  },

  /**
   * 轮询批改结果
   * @param {string} submissionId - 提交记录ID
   * @param {Object} options - 配置选项
   * @param {number} [options.interval=3000] - 轮询间隔（毫秒）
   * @param {number} [options.maxAttempts=20] - 最大尝试次数
   * @param {Function} [options.onProgress] - 进度回调
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  async pollCorrectionResult(submissionId, options = {}) {
    const {
      interval = 3000,
      maxAttempts = 20,
      onProgress,
    } = options;

    let attempts = 0;

    const poll = async () => {
      attempts++;

      try {
        const result = await this.getSubmissionDetail(submissionId);

        if (onProgress) {
          onProgress({
            attempts,
            maxAttempts,
            status: result.data.status,
          });
        }

        // 检查状态
        if (result.data.status === 'completed') {
          // 批改完成，获取批改结果
          return await this.getCorrectionResult(submissionId);
        } else if (result.data.status === 'failed') {
          // 批改失败
          throw new Error(result.data.error_message || '批改失败');
        } else if (attempts >= maxAttempts) {
          // 超过最大尝试次数
          throw new Error('批改超时，请稍后查看');
        } else {
          // 继续轮询
          await new Promise(resolve => setTimeout(resolve, interval));
          return await poll();
        }
      } catch (error) {
        if (attempts >= maxAttempts) {
          throw error;
        }
        // 继续尝试
        await new Promise(resolve => setTimeout(resolve, interval));
        return await poll();
      }
    };

    return poll();
  },

  /**
   * 删除作业提交
   * @param {string} submissionId - 提交记录ID
   * @returns {Promise<{success: boolean, message: string}>}
   */
  deleteSubmission(submissionId) {
    return request.delete(`api/v1/homework/submissions/${submissionId}`, {}, {
      showLoading: true,
      loadingText: '删除中...',
      showError: true,
    });
  },

  // ========== 兼容性方法 ==========
  // 为了保持与旧版本小程序的兼容性，提供一些别名方法

  /**
   * 获取作业列表（兼容性方法）
   * @param {Object} params - 查询参数
   * @returns {Promise<{success: boolean, data: Array, message: string}>}
   */
  getHomeworkList(params = {}) {
    return request.get('api/v1/homework/list', params, {
      showLoading: false,
    });
  },

  /**
   * 获取作业详情（兼容性方法）
   * @param {string} homeworkId - 作业ID
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  getHomeworkDetail(homeworkId) {
    return request.get(`api/v1/homework/${homeworkId}`, {}, {
      showLoading: true,
      loadingText: '加载中...',
    });
  },

  /**
   * 开始批改作业（兼容性方法）
   * @param {string} homeworkId - 作业ID
   * @returns {Promise<{success: boolean, data: Object, message: string}>}
   */
  correctHomework(homeworkId) {
    return request.post(`api/v1/homework/${homeworkId}/correct`, {}, {
      showLoading: true,
      loadingText: '批改中...',
      showError: true,
    });
  },
};

module.exports = homeworkAPI;

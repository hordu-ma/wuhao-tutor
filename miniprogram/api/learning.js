/**
 * 学习问答 API 模块
 * @description 封装学习问答相关的后端 API 调用
 * @module api/learning
 */

const { request } = require('../utils/request.js');

/**
 * 学习问答 API
 */
const learningAPI = {
  /**
   * 创建学习会话
   * @param {Object} params - 会话参数
   * @param {string} [params.title] - 会话标题
   * @param {string} [params.subject] - 学科
   * @param {string} [params.grade] - 年级
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话信息
   */
  createSession(params = {}, config = {}) {
    return request.post('api/v1/learning/sessions', params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取会话列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.status_filter] - 会话状态筛选 (active/archived)
   * @param {string} [params.subject_filter] - 学科筛选
   * @param {string} [params.search] - 搜索关键词
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话列表响应 {total, page, size, pages, items}
   */
  getSessions(params = {}, config = {}) {
    const { page = 1, size = 10, status_filter, subject_filter, search } = params;

    const queryParams = {
      page,
      size,
    };

    if (status_filter) queryParams.status_filter = status_filter;
    if (subject_filter) queryParams.subject_filter = subject_filter;
    if (search) queryParams.search = search;

    return request.get('api/v1/learning/sessions', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取会话详情
   * @param {string} sessionId - 会话 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 会话详情
   */
  getSessionDetail(sessionId, config = {}) {
    return request.get(
      `api/v1/learning/sessions/${sessionId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 更新会话
   * @param {string} sessionId - 会话 ID
   * @param {Object} params - 更新参数
   * @param {string} [params.title] - 会话标题
   * @param {string} [params.status] - 会话状态
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 更新后的会话信息
   */
  updateSession(sessionId, params, config = {}) {
    return request.put(`api/v1/learning/sessions/${sessionId}`, params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 删除会话
   * @param {string} sessionId - 会话 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 删除结果
   */
  deleteSession(sessionId, config = {}) {
    return request.delete(
      `api/v1/learning/sessions/${sessionId}`,
      {},
      {
        showLoading: true,
        loadingText: '删除中...',
        ...config,
      },
    );
  },

  /**
   * 向 AI 提问 - 对齐网页端实现
   * @param {Object} params - 提问参数
   * @param {string} params.content - 问题内容（对齐网页端字段名）
   * @param {string} [params.session_id] - 会话 ID
   * @param {string} [params.subject] - 学科
   * @param {string} [params.question_type] - 问题类型
   * @param {Array<string>} [params.image_urls] - 图片 URL 列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} AI 回答
   */
  askQuestion(params, config = {}) {
    if (!params || !params.content) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题内容不能为空',
      });
    }

    return request.post('api/v1/learning/ask', params, {
      timeout: 120000, // 120秒超时 - 支持图片OCR和AI处理
      showLoading: true,
      loadingText: 'AI 思考中...',
      showError: true,
      ...config,
    });
  },

  /**
   * 向 AI 提问（流式响应）- SSE 实时返回
   * @param {Object} params - 提问参数
   * @param {string} params.content - 问题内容
   * @param {string} [params.session_id] - 会话 ID
   * @param {string} [params.subject] - 学科
   * @param {string} [params.question_type] - 问题类型
   * @param {Array<string>} [params.image_urls] - 图片 URL 列表
   * @param {Function} onChunk - 接收流式数据的回调函数 (chunk) => void
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 最终完整的 AI 回答
   */
  askQuestionStreamWS(params, onChunk, config = {}) {
    if (!params || !params.content) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题内容不能为空',
      });
    }

    if (typeof onChunk !== 'function') {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: 'onChunk 回调函数不能为空',
      });
    }

    return new Promise((resolve, reject) => {
      const app = getApp();
      const token = app.globalData.token;

      // 验证 token
      if (!token) {
        reject({
          code: 'AUTH_ERROR',
          message: '用户未登录，请先登录',
        });
        return;
      }

      const apiConfig = require('../config/index.js').api;
      const baseUrl = apiConfig.baseUrl;

      // 构建 WebSocket URL
      const wsUrl =
        baseUrl.replace('https://', 'wss://').replace('http://', 'ws://') +
        '/api/v1/learning/ws/ask';

      console.log('[WebSocket] 正在连接:', wsUrl);

      let fullContent = '';
      let finalData = null;
      let hasError = false;

      // 创建 WebSocket 连接
      const socketTask = wx.connectSocket({
        url: wsUrl,
        success: () => {
          console.log('[WebSocket] 连接请求已发送');
        },
        fail: error => {
          console.error('[WebSocket] 连接失败:', error);
          hasError = true;
          reject({
            code: 'WS_CONNECT_ERROR',
            message: '连接失败，请检查网络',
            details: error,
          });
        },
      });

      // 监听连接打开
      socketTask.onOpen(() => {
        console.log('[WebSocket] 连接已建立，发送请求...');

        // 发送请求数据
        socketTask.send({
          data: JSON.stringify({
            token: token,
            params: params,
          }),
          success: () => {
            console.log('[WebSocket] 请求数据已发送');
          },
          fail: error => {
            console.error('[WebSocket] 发送请求失败:', error);
            hasError = true;
            reject({
              code: 'WS_SEND_ERROR',
              message: '发送请求失败',
              details: error,
            });
          },
        });
      });

      // 监听接收消息
      socketTask.onMessage(res => {
        try {
          const chunk = JSON.parse(res.data);
          console.log('[WebSocket] 收到消息:', {
            type: chunk.type,
            contentLength: chunk.content ? chunk.content.length : 0,
            hasFullContent: !!chunk.full_content,
          });

          // 处理错误
          if (chunk.type === 'error') {
            console.error('[WebSocket] 服务器错误:', chunk.message);
            hasError = true;
            reject({
              code: 'SERVER_ERROR',
              message: chunk.message || 'AI 服务错误',
            });
            socketTask.close();
            return;
          }

          // 累积内容
          if (chunk.content) {
            fullContent += chunk.content;
          } else if (chunk.full_content) {
            fullContent = chunk.full_content;
          }

          // 调用回调函数，传递流式数据
          onChunk({
            type: chunk.type || 'content',
            content: chunk.content || '',
            full_content: chunk.full_content || fullContent,
            finish_reason: chunk.finish_reason,
            question_id: chunk.question_id,
            answer_id: chunk.answer_id,
            session_id: chunk.session_id,
            usage: chunk.usage,
          });

          // 保存最终数据
          if (chunk.type === 'done' || chunk.finish_reason === 'stop') {
            finalData = {
              type: 'done',
              full_content: chunk.full_content || fullContent,
              content: chunk.full_content || fullContent,
              question_id: chunk.question_id,
              answer_id: chunk.answer_id,
              session_id: chunk.session_id,
              usage: chunk.usage,
            };
            console.log('[WebSocket] 流式响应完成');
          }
        } catch (error) {
          console.error('[WebSocket] 解析消息失败:', error, res.data);
        }
      });

      // 监听连接关闭
      socketTask.onClose(res => {
        console.log('[WebSocket] 连接已关闭:', res);

        if (hasError) {
          // 已经在错误处理中 reject，不再重复处理
          return;
        }

        // 正常关闭，返回最终结果
        if (finalData) {
          resolve(finalData);
        } else {
          // 没有收到 done 事件，使用累积的内容
          resolve({
            type: 'done',
            full_content: fullContent,
            content: fullContent,
          });
        }
      });

      // 监听连接错误
      socketTask.onError(error => {
        console.error('[WebSocket] 连接错误:', error);
        if (!hasError) {
          hasError = true;
          reject({
            code: 'WS_ERROR',
            message: 'WebSocket 连接错误',
            details: error,
          });
        }
      });
    });
  },

  /**
   * 向 AI 提问（流式响应）- SSE 实时返回（备用方案）
   * @deprecated 使用 askQuestionStreamWS 代替
   * @param {Object} params - 提问参数
   * @param {string} params.content - 问题内容
   * @param {string} [params.session_id] - 会话 ID
   * @param {string} [params.subject] - 学科
   * @param {string} [params.question_type] - 问题类型
   * @param {Array<string>} [params.image_urls] - 图片 URL 列表
   * @param {Function} onChunk - 接收流式数据的回调函数 (chunk) => void
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 最终完整的 AI 回答
   */
  askQuestionStream(params, onChunk, config = {}) {
    if (!params || !params.content) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题内容不能为空',
      });
    }

    if (typeof onChunk !== 'function') {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: 'onChunk 回调函数不能为空',
      });
    }

    return new Promise((resolve, reject) => {
      const app = getApp();
      const token = app.globalData.token;
      const apiConfig = require('../config/index.js').api;
      const baseUrl = apiConfig.baseUrl;

      // 验证 token
      if (!token) {
        console.error('[SSE Stream] Token 未找到，用户可能未登录');
        reject({
          code: 'AUTH_ERROR',
          message: '用户未登录，请先登录',
        });
        return;
      }

      // 获取完整 URL
      const fullUrl = `${baseUrl}/api/v1/learning/ask-stream`;

      console.log('[SSE Stream] 开始流式请求:', {
        url: fullUrl,
        hasToken: !!token,
        tokenPrefix: token ? token.substring(0, 20) + '...' : 'none',
        params: params,
      });

      let buffer = ''; // SSE 数据缓冲区
      let fullContent = ''; // 累积的完整内容
      let finalData = null; // 最终返回数据
      let chunkCount = 0; // 统计接收到的块数

      console.log('[SSE Stream] 创建请求任务');

      // 🔧 尝试方案：不使用 enableChunked，直接获取完整响应
      const requestTask = wx.request({
        url: fullUrl,
        method: 'POST',
        data: params,
        header: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        timeout: 120000,
        // enableChunked: true, // ❌ 暂时禁用，看是否能获取完整响应
        // responseType: 'text', // ❌ 暂时不设置

        // 接收到数据块时的回调（仅在 enableChunked: true 时有效）
        onChunkReceived(res) {
          chunkCount++;
          console.log(`[SSE Stream] onChunkReceived 被调用 (第 ${chunkCount} 次):`, {
            hasData: !!res.data,
            dataType: typeof res.data,
            dataLength: res.data?.length,
            dataPreview: res.data?.substring(0, 100),
          });

          if (res.data) {
            buffer += res.data;

            // 解析 SSE 格式：data: {json}\n\n
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后一个不完整的行

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const jsonStr = line.substring(6); // 去掉 "data: " 前缀
                  const chunk = JSON.parse(jsonStr);

                  console.log('[SSE Chunk]', chunk);

                  // 累积内容
                  if (chunk.content) {
                    fullContent += chunk.content;
                  }

                  // 调用回调函数，传递增量数据
                  onChunk({
                    type: chunk.type || 'content',
                    content: chunk.content || '',
                    full_content: chunk.full_content || fullContent,
                    finish_reason: chunk.finish_reason,
                  });

                  // 保存最终数据（type="done" 或 finish_reason="stop"）
                  if (chunk.type === 'done' || chunk.finish_reason === 'stop') {
                    finalData = chunk;
                    console.log('[SSE Stream] 保存最终数据:', finalData);
                  }
                } catch (error) {
                  console.error('[SSE Parse Error]', error, line);
                }
              }
            }
          }
        },

        success(res) {
          console.log('[SSE Stream] 请求完成:', {
            statusCode: res.statusCode,
            header: res.header,
            dataLength: res.data?.length,
            chunkCount: chunkCount, // 统计接收了多少次 onChunkReceived
            hasFinalData: !!finalData,
            finalData: finalData,
            fullContent: fullContent,
            fullContentLength: fullContent.length,
          });

          if (chunkCount === 0) {
            console.error('[SSE Stream] ❌ onChunkReceived 从未被调用！');
            console.error('[SSE Stream] 响应详情:', {
              statusCode: res.statusCode,
              hasData: !!res.data,
              dataType: typeof res.data,
              dataLength: res.data?.length || 0,
              dataIsString: typeof res.data === 'string',
              dataIsEmpty: !res.data || res.data.length === 0,
              headers: res.header,
            });
            console.error('[SSE Stream] 这可能是因为：');
            console.error('  1. 微信基础库不支持 enableChunked (需要 >= 2.20.1)');
            console.error('  2. 后端没有正确发送 SSE 流（响应为空）');
            console.error('  3. responseType 设置不正确');
            console.error('[SSE Stream] 完整响应数据:', res);

            // 🔧 回退方案：尝试从 res.data 中解析 SSE 格式
            if (res.data && typeof res.data === 'string' && res.data.length > 0) {
              console.log('[SSE Stream] 🔄 尝试从完整响应中解析 SSE 数据');
              console.log('[SSE Stream] 响应前 200 个字符:', res.data.substring(0, 200));

              const lines = res.data.split('\n');
              let parsedContent = '';

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const jsonStr = line.substring(6);
                    const chunk = JSON.parse(jsonStr);
                    console.log('[SSE Fallback] 解析到块:', chunk);

                    if (chunk.content) {
                      parsedContent += chunk.content;
                    } else if (chunk.full_content) {
                      parsedContent = chunk.full_content;
                    }

                    if (chunk.type === 'done') {
                      finalData = chunk;
                    }
                  } catch (err) {
                    console.warn('[SSE Fallback] 解析失败:', line, err);
                  }
                }
              }

              fullContent = parsedContent;
              console.log('[SSE Fallback] 解析完成:', {
                contentLength: fullContent.length,
                hasFinalData: !!finalData,
              });
            } else {
              console.error('[SSE Stream] ❌ 响应数据为空或不是字符串，无法使用回退方案');
              console.error('[SSE Stream] ⚠️ 这表明后端可能没有正确返回 SSE 流');
            }
          }

          if (res.statusCode === 200) {
            // 检查是否有最终数据
            if (!finalData) {
              console.warn('[SSE Stream] ⚠️ finalData 为空，使用备用数据结构');
              console.warn('[SSE Stream] 这可能是因为 done 事件在 success 之后到达');
            }

            // 等待一小段时间，确保所有 SSE 事件都被处理
            setTimeout(() => {
              console.log('[SSE Stream] 延迟检查 finalData:', {
                hasFinalData: !!finalData,
                finalData: finalData,
              });

              // 返回最终数据或累积内容
              resolve(
                finalData || {
                  type: 'done',
                  success: true,
                  full_content: fullContent,
                  content: fullContent,
                  data: {
                    answer: fullContent,
                    content: fullContent,
                  },
                },
              );
            }, 100); // 等待 100ms
          } else if (res.statusCode === 401) {
            console.error('[SSE Stream] 认证失败 (401):', res.data);
            reject({
              code: 'AUTH_ERROR',
              message: '登录已过期，请重新登录',
            });
          } else {
            console.error('[SSE Stream] 请求失败:', {
              statusCode: res.statusCode,
              data: res.data,
            });
            reject({
              code: `HTTP_${res.statusCode}`,
              message: res.data || `请求失败 (${res.statusCode})`,
            });
          }
        },

        fail(error) {
          console.error('[SSE Stream] 网络请求失败:', {
            errMsg: error.errMsg,
            errno: error.errno,
          });
          reject({
            code: 'NETWORK_ERROR',
            message: error.errMsg || '网络请求失败',
          });
        },
      });

      // 支持取消请求（可选）
      if (config.onRequestCreated) {
        config.onRequestCreated(requestTask);
      }
    });
  },

  /**
   * 获取问题列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {string} [params.session_id] - 会话 ID 筛选
   * @param {string} [params.subject] - 学科筛选
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 问题列表
   */
  getQuestions(params = {}, config = {}) {
    const { page = 1, size = 10, session_id, subject } = params;

    const queryParams = {
      limit: size,
      offset: (page - 1) * size,
    };

    if (session_id) queryParams.session_id = session_id;
    if (subject) queryParams.subject = subject;

    return request.get('api/v1/learning/questions', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取单个问题和回答
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 问题详情
   */
  getQuestionDetail(questionId, config = {}) {
    return request.get(
      `api/v1/learning/questions/${questionId}`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 搜索问题
   * @param {Object} params - 搜索参数
   * @param {string} params.q - 搜索关键词
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.limit=20] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 搜索结果
   */
  searchQuestions(params, config = {}) {
    if (!params || !params.q) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '搜索关键词不能为空',
      });
    }

    const { q, subject, limit = 20 } = params;

    const queryParams = { q, limit };
    if (subject) queryParams.subject = subject;

    return request.get('api/v1/learning/questions/search', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 对答案评价（点赞/点踩）
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 评价参数
   * @param {boolean} params.helpful - 是否有帮助
   * @param {string} [params.feedback] - 反馈内容
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 评价结果
   */
  rateAnswer(questionId, params, config = {}) {
    return request.post(`api/v1/learning/questions/${questionId}/rate`, params, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 收藏问题
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 收藏结果
   */
  favoriteQuestion(questionId, config = {}) {
    return request.post(
      `api/v1/learning/questions/${questionId}/favorite`,
      {},
      {
        showLoading: false,
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 取消收藏问题
   * @param {string} questionId - 问题 ID
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 取消收藏结果
   */
  unfavoriteQuestion(questionId, config = {}) {
    return request.delete(
      `api/v1/learning/questions/${questionId}/favorite`,
      {},
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取收藏的问题列表
   * @param {Object} params - 查询参数
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=10] - 每页数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 收藏列表
   * @deprecated 后端未实现，功能开发中
   */
  getFavorites(params = {}, config = {}) {
    console.warn('[API未实现] learning/favorites - 收藏功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { items: [], total: 0 },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取学习洞察（频次等统计）
   * @param {Object} params - 查询参数
   * @param {number} [params.days=30] - 统计天数
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 学习洞察数据
   * @deprecated 后端未实现，功能开发中
   */
  getInsights(params = {}, config = {}) {
    console.warn('[API未实现] learning/insights - 学习见解功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { insights: [] },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 上传图片用于提问
   * @param {string} filePath - 本地文件路径
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 上传结果（包含图片 URL）
   */
  uploadQuestionImage(filePath, config = {}) {
    return request.upload(
      'api/v1/files/upload',
      filePath,
      'file',
      { category: 'question' },
      {
        showLoading: true,
        loadingText: '上传图片中...',
        ...config,
      },
    );
  },

  /**
   * 批量上传图片用于提问
   * @param {Array<string>} filePaths - 本地文件路径列表
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Array<Object>>} 上传结果列表
   */
  async uploadQuestionImages(filePaths, config = {}) {
    if (!Array.isArray(filePaths) || filePaths.length === 0) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '文件路径列表不能为空',
      });
    }

    const results = [];
    const errors = [];

    for (let i = 0; i < filePaths.length; i++) {
      try {
        const result = await this.uploadQuestionImage(filePaths[i], {
          ...config,
          loadingText: `上传图片 ${i + 1}/${filePaths.length}`,
        });

        if (result.success && result.data) {
          results.push(result.data);
        } else {
          errors.push({
            index: i,
            path: filePaths[i],
            error: result.error || '上传失败',
          });
        }
      } catch (error) {
        errors.push({
          index: i,
          path: filePaths[i],
          error: error.message || '上传失败',
        });
      }
    }

    if (errors.length > 0) {
      console.warn('部分图片上传失败:', errors);
    }

    return {
      success: true,
      data: results,
      errors: errors.length > 0 ? errors : undefined,
    };
  },

  /**
   * 获取推荐问题
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科
   * @param {string} [params.grade] - 年级
   * @param {number} [params.limit=5] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 推荐问题列表
   */
  getRecommendedQuestions(params = {}, config = {}) {
    const { subject, grade, limit = 5 } = params;

    const queryParams = { limit };
    if (subject) queryParams.subject = subject;
    if (grade) queryParams.grade = grade;

    return request.get('api/v1/learning/recommendations', queryParams, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 获取热门问题
   * @param {Object} params - 查询参数
   * @param {string} [params.subject] - 学科筛选
   * @param {number} [params.days=7] - 统计天数
   * @param {number} [params.limit=10] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 热门问题列表
   * @deprecated 后端未实现，功能开发中
   */
  getPopularQuestions(params = {}, config = {}) {
    console.warn('[API未实现] learning/popular - 热门问题功能待后端实现');
    return Promise.resolve({
      success: true,
      data: { items: [], total: 0 },
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取相似问题
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 查询参数
   * @param {number} [params.limit=5] - 返回数量
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 相似问题列表
   */
  getSimilarQuestions(questionId, params = {}, config = {}) {
    const { limit = 5 } = params;

    return request.get(
      `api/v1/learning/questions/${questionId}/similar`,
      { limit },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  // ========== 聊天会话相关方法 (向后兼容) ==========

  /**
   * 获取 AI 服务状态
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} AI 服务状态
   */
  async getAIStatus(config = {}) {
    try {
      const response = await request.get(
        'api/v1/learning/health',
        {},
        {
          showLoading: false,
          ...config,
        },
      );

      // 适配后端返回格式 -> 前端期望格式
      // 后端返回: { status: "ok", module: "learning", ... }
      // 前端期望: { success: true, data: { online: true, capabilities: [...] } }
      return {
        success: response.status === 'ok',
        data: {
          online: response.status === 'ok',
          capabilities: [
            'text_qa', // 文本问答
            'image_upload', // 图片上传
            'context_aware', // 上下文感知
            'multi_subject', // 多学科支持
          ],
          module: response.module,
          timestamp: response.timestamp,
        },
      };
    } catch (error) {
      console.error('[getAIStatus] 获取AI状态失败:', error);
      // 返回离线状态
      return {
        success: false,
        data: {
          online: false,
          capabilities: [],
        },
      };
    }
  },

  /**
   * 获取会话消息列表
   * @param {Object} params - 查询参数
   * @param {string} params.sessionId - 会话 ID (也支持 session_id)
   * @param {number} [params.page=1] - 页码
   * @param {number} [params.size=20] - 每页大小
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 消息列表
   */
  getMessages(params = {}, config = {}) {
    // 兼容两种参数命名：sessionId (驼峰) 和 session_id (下划线)
    const sessionId = params.sessionId || params.session_id;
    const { page = 1, size = 20 } = params;

    if (!sessionId) {
      console.error('[API错误] getMessages 缺少必需参数 sessionId');
      return Promise.reject(new Error('缺少会话ID'));
    }

    // 调试：验证sessionId在API调用前的状态
    console.log('调试 - getMessages API调用:');
    console.log('  接收到的sessionId:', sessionId);
    console.log('  sessionId长度:', sessionId.length);
    console.log('  sessionId类型:', typeof sessionId);

    const url = `api/v1/learning/sessions/${sessionId}/history`;
    console.log('  构建的URL:', url);
    console.log('  URL长度:', url.length);

    return request.get(
      url,
      { page, size },
      {
        showLoading: false,
        ...config,
      },
    );
  },

  /**
   * 获取用户统计信息
   * @param {Object} params - 查询参数
   * @param {string} [params.date] - 日期 (YYYY-MM-DD)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 用户统计
   */
  getUserStats(params = {}, config = {}) {
    const { date } = params;

    return request.get('api/v1/learning/stats/daily', date ? { date } : {}, {
      showLoading: false,
      ...config,
    });
  },

  /**
   * 清除会话消息
   * @param {Object} params - 参数
   * @param {string} params.sessionId - 会话 ID (也支持 session_id)
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 操作结果
   * @deprecated 后端未实现删除会话功能，返回模拟成功
   */
  clearMessages(params = {}, config = {}) {
    // 兼容两种参数命名：sessionId (驼峰) 和 session_id (下划线)
    const sessionId = params.sessionId || params.session_id;

    if (!sessionId) {
      console.error('[API错误] clearMessages 缺少必需参数 sessionId');
      return Promise.reject(new Error('缺少会话ID'));
    }

    // 注意：后端暂无删除会话接口，这里返回模拟成功
    console.warn('[API未实现] 清除消息功能待后端实现');
    return Promise.resolve({
      success: true,
      message: '功能开发中，敬请期待',
    });
  },

  /**
   * 获取推荐问题
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 推荐问题列表
   */
  getRecommendations(config = {}) {
    return request.get('api/v1/learning/recommendations', {}, config);
  },

  /**
   * 将学习问答中的题目加入错题本
   * @param {string} questionId - 问题 ID
   * @param {Object} params - 参数
   * @param {string} [params.student_answer] - 学生答案（可选，用于标记答错）
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 创建的错题详情
   */
  addQuestionToMistakes(questionId, params = {}, config = {}) {
    if (!questionId) {
      return Promise.reject({
        code: 'VALIDATION_ERROR',
        message: '问题ID不能为空',
      });
    }

    const { student_answer } = params;
    const queryParams = student_answer ? { student_answer } : {};

    return request.post(
      `api/v1/learning/questions/${questionId}/add-to-mistakes`,
      {},
      {
        params: queryParams, // query 参数
        showLoading: true,
        loadingText: '加入错题本中...',
        showError: true,
        ...config,
      },
    );
  },

  /**
   * 获取系统统计 - 使用日统计接口
   * @param {Object} [config] - 请求配置
   * @returns {Promise<Object>} 系统统计信息
   */
  getSystemStats(config = {}) {
    return request.get('api/v1/learning/stats/daily', {}, config);
  },
};

module.exports = learningAPI;

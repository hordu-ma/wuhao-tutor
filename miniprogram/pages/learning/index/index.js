// pages/chat/index/index.js - AI问答对话页面

const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');
const { mcpService } = require('../../../utils/mcp-service.js');
const api = require('../../../api/index.js');
const config = require('../../../config/index.js');
const utils = require('../../../utils/utils.js');
const { parseMarkdown } = require('../../../utils/markdown-formatter.js');

const pageObject = {
  data: {
    // API状态管理
    apiStatus: 'success', // loading | error | empty | success
    errorMessage: '',

    // MCP上下文增强 - 暂时禁用
    mcpEnabled: false,
    personalizedContext: {
      learningStyle: '', // 学习风格
      weaknessPoints: [], // 薄弱知识点
      recentErrors: [], // 最近错题
      preferences: {}, // 学习偏好
    },

    // 用户信息
    userInfo: null,
    userRole: '',

    // 对话消息列表
    messageList: [],

    // 输入相关
    inputText: '', // 当前输入内容
    inputFocus: false, // 输入框焦点状态
    inputBottom: 0, // 输入框底部距离
    maxInputLength: 500, // 最大输入长度
    inputMode: 'text', // 输入模式: text | voice
    showImageActionSheet: false, // 显示图片操作选择（旧变量，保留兼容）
    showImageActions: false, // 显示图片上传选择菜单

    // AI回复状态
    isAITyping: false, // AI正在回复
    isConnected: true, // AI连接状态

    // 页面状态
    loading: false,
    sending: false,
    refreshing: false,
    scrollTop: 0, // 滚动位置

    // 功能状态
    recordStatus: 'idle', // 录音状态: idle, recording, uploading
    recordDuration: 0, // 录音时长（秒）
    cancelVoice: false, // 是否取消录音
    touchStartY: 0, // 触摸起始Y坐标
    showQuickReply: true, // 显示快捷回复
    showSubjectTabs: true, // 显示学科标签
    showTools: false, // 显示工具栏
    showActionSheet: false, // 显示功能菜单

    // 快捷回复选项
    quickReplies: [
      '这道题怎么做？',
      '解释一下这个概念',
      '给我出几道练习题',
      '总结一下重点',
      '有什么学习建议吗？',
    ],

    // 快速问题
    quickQuestions: ['今天的作业有疑问吗？', '需要复习什么知识点？', '想了解什么新内容？'],

    // 学科分类
    subjects: [
      { id: 'all', name: '全部', icon: 'apps-o', active: true },
      { id: 'math', name: '数学', icon: 'balance-o', active: false },
      { id: 'chinese', name: '语文', icon: 'edit', active: false },
      { id: 'english', name: '英语', icon: 'chat-o', active: false },
      { id: 'physics', name: '物理', icon: 'fire-o', active: false },
      { id: 'chemistry', name: '化学', icon: 'diamond-o', active: false },
    ],

    // 问题统计
    questionStats: {
      total: 0,
      bySubject: {},
      recentTopics: [],
    },

    // 当前选中学科
    currentSubject: 'all',

    // 页面配置
    showScrollToBottom: false, // 显示滚动到底部按钮
    hasMore: false, // 是否有更多历史消息
    loadingHistory: false, // 加载历史消息状态

    // 权限状态
    canAsk: true,
    canView: true,
    canModerate: false,

    // 会话管理
    sessionId: '', // 当前会话ID
    isNewSession: false, // 是否为新创建的会话
    conversationContext: [], // 对话上下文

    // 网络状态
    networkStatus: 'online', // online, offline, slow
    retryCount: 0, // 重试次数
    maxRetryCount: 3, // 最大重试次数

    // 错误状态
    error: null,

    // 图片上传
    uploadedImages: [], // 待发送的图片列表 [{tempFilePath, aiUrl}]
    uploadingCount: 0, // 正在上传的图片数量
    maxImageCount: 5, // 最大图片数量（与 Web 前端保持一致）

    // 计算属性：是否有输入内容（用于条件渲染）
    hasInputContent: false, // inputText.trim() 是否有内容

    // 历史会话
    showHistoryPopup: false, // 显示历史会话弹窗
    recentSessions: [], // 最近的会话列表
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('AI问答页面加载', options);

    try {
      await this.initUserInfo();
      await this.initPermissions();
      await this.initSession();
      // await this.initMCPContext(); // 暂时禁用MCP功能
      await this.initChat();
      this.initNetworkMonitor();
      await this.loadRecommendedQuestions();

      // 从其他页面传入的初始问题
      if (options.question) {
        const question = decodeURIComponent(options.question);
        this.setData({ inputText: question });
        setTimeout(() => this.sendMessage(), 500);
      }

      // 特定学科模式
      if (options.subject) {
        this.switchSubject(options.subject);
      }
    } catch (error) {
      console.error('页面初始化失败:', error);
      this.showError('页面加载失败');
    }
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 恢复输入焦点
    if (this.data.canAsk) {
      this.setData({ inputFocus: true });
    }

    // 重新连接WebSocket
    this.reconnectIfNeeded();

    // 刷新在线状态
    this.updateOnlineStatus();
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    // 停止AI回复动画
    this.stopAITyping();

    // 保存当前输入内容
    if (this.data.inputText.trim()) {
      wx.setStorageSync('chat_draft', this.data.inputText);
    }
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    this.refreshData().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    if (this.data.hasMore && !this.data.loadingHistory) {
      this.loadMoreMessages();
    }
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '五好AI助手 - 智能学习问答',
      path: '/pages/chat/index/index',
      imageUrl: '/assets/images/share-chat.png',
    };
  },

  /**
   * 用户点击右上角分享到朋友圈
   */
  onShareTimeline() {
    return {
      title: '五好AI助手 - 智能学习问答',
      imageUrl: '/assets/images/share-chat.png',
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();

      // 使用本地默认头像，避免服务器图片加载失败导致500错误
      if (userInfo) {
        userInfo.avatar_url = '/assets/images/default-avatar.png';
      }

      this.setData({ userInfo });

      // 获取用户角色信息
      const userRole = await authManager.getUserRole();
      this.setData({ userRole: userRole });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 初始化权限设置 - 简化版本
   */
  async initPermissions() {
    try {
      // 暂时简化权限检查，直接允许所有操作
      this.setData({
        canAsk: true,
        canView: true,
        canModerate: false,
      });
      console.log('权限设置结果:', {
        canAsk: this.data.canAsk,
        canView: this.data.canView,
        canModerate: this.data.canModerate,
      });
    } catch (error) {
      console.error('获取权限失败:', error);
      // 设置默认权限
      this.setData({
        canAsk: true,
        canView: true,
        canModerate: false,
      });
    }
  },

  /**
   * 初始化MCP个性化上下文
   */
  async initMCPContext() {
    try {
      if (!this.data.mcpEnabled) return;

      const { userInfo } = this.data;
      if (!userInfo || !userInfo.id) return;

      // 获取个性化学习上下文
      const context = await mcpService.getPersonalizedContext(userInfo.id);

      this.setData({
        personalizedContext: {
          learningStyle: context.learningStyle,
          weaknessPoints: context.weaknessPoints,
          recentErrors: context.recentErrors,
          preferences: context.preferences,
        },
      });

      console.log('MCP上下文初始化成功:', context);
    } catch (error) {
      console.error('MCP上下文初始化失败:', error);
      // MCP失败不影响正常功能
      this.setData({ mcpEnabled: false });
    }
  },

  /**
   * 初始化会话 - 对齐网页端实现
   */
  async initSession() {
    try {
      // 强制清除旧的session，创建新的
      // TODO: 这是临时解决方案，生产环境应该保留有效session
      console.log('强制清除旧session，创建新的会话...');
      wx.removeStorageSync('chat_session_id');

      // 创建新会话
      const sessionResponse = await api.learning.createSession({
        title: '新对话',
        context_enabled: true,
      });

      let sessionId;
      let isNewSession = false;
      if (sessionResponse.success) {
        sessionId = sessionResponse.data.id;
        wx.setStorageSync('chat_session_id', sessionId);
        isNewSession = true;
        console.log('新会话创建成功:', sessionId);
      } else {
        // 如果创建会话失败，回退到本地生成
        sessionId = this.generateSessionId();
        wx.setStorageSync('chat_session_id', sessionId);
        isNewSession = true;
        console.log('使用本地生成的sessionId:', sessionId);
      }

      this.setData({
        sessionId,
        isNewSession, // 标记是否为新会话
      });

      // 恢复草稿
      const draft = wx.getStorageSync('chat_draft');
      if (draft) {
        this.setData({ inputText: draft });
        wx.removeStorageSync('chat_draft');
      }
    } catch (error) {
      console.error('初始化会话失败:', error);
      // 发生错误时使用本地生成的会话ID
      const sessionId = this.generateSessionId();
      this.setData({
        sessionId,
        isNewSession: true,
      });
      wx.setStorageSync('chat_session_id', sessionId);
    }
  },

  /**
   * 初始化聊天功能
   */
  async initChat() {
    try {
      this.setData({ loading: true });

      // 只有非新会话才加载历史消息
      // 新会话没有历史，跳过加载避免404错误
      if (!this.data.isNewSession) {
        await this.loadHistoryMessages();
      } else {
        console.log('新会话跳过历史消息加载');
        this.setData({ messageList: [] });
      }

      // 初始化AI连接状态
      await this.checkAIStatus();

      // 加载用户统计
      await this.loadUserStats();
    } catch (error) {
      console.error('初始化聊天功能失败:', error);
      this.showError('聊天功能初始化失败');
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 初始化网络监控
   */
  initNetworkMonitor() {
    // 监听网络状态变化
    wx.onNetworkStatusChange(res => {
      this.setData({
        networkStatus: res.isConnected ? 'online' : 'offline',
      });

      if (res.isConnected) {
        this.reconnectIfNeeded();
      }
    });

    // 获取当前网络状态
    wx.getNetworkType({
      success: res => {
        this.setData({
          networkStatus: res.networkType === 'none' ? 'offline' : 'online',
        });
      },
    });
  },

  /**
   * 加载推荐问题
   */
  async loadRecommendedQuestions() {
    try {
      // 根据用户角色和学科获取推荐问题
      const recommendations = await api.learning.getRecommendations();

      if (recommendations.success) {
        this.setData({
          quickReplies: recommendations.data.slice(0, 5),
          quickQuestions: recommendations.data.slice(0, 3),
        });
      }
    } catch (error) {
      console.error('加载推荐问题失败:', error);
      // 使用默认推荐问题
    }
  },

  /**
   * 生成会话ID
   */
  generateSessionId() {
    return utils.string.uuid();
  },

  /**
   * 检查AI状态
   */
  async checkAIStatus() {
    try {
      // 暂时简化AI状态检查：直接设置为在线
      // TODO: 后续可以调用专门的健康检查接口
      console.log('AI状态检查：默认设置为在线');
      this.setData({
        isConnected: true,
        aiCapabilities: [],
      });

      // 可选：后台静默检查系统状态（不影响用户使用）
      api.learning.getSystemStats().catch(err => {
        console.warn('后台系统状态检查失败:', err);
        // 不改变isConnected状态，避免影响用户体验
      });
    } catch (error) {
      console.error('检查AI状态失败:', error);
      // 即使发生错误，也默认设置为在线（乐观策略）
      this.setData({ isConnected: true });
    }
  },

  /**
   * 加载历史消息 - 对齐网页端实现
   */
  async loadHistoryMessages() {
    try {
      if (!this.data.sessionId) {
        console.log('没有会话ID，跳过历史消息加载');
        return;
      }

      // 调试：在调用API前验证sessionId
      console.log('调试 - loadHistoryMessages开始:');
      console.log('  this.data.sessionId:', this.data.sessionId);
      console.log('  长度:', this.data.sessionId.length);
      console.log('  类型:', typeof this.data.sessionId);

      // 使用learning API而不是chat API
      const response = await api.learning.getMessages({
        sessionId: this.data.sessionId,
        page: 1,
        size: 20,
      });

      if (response.success && response.data) {
        const messages = response.data.map(item => ({
          id: item.question?.id || utils.generateId(),
          content: item.question?.content || '',
          type: 'user',
          sender: 'user',
          timestamp: item.question?.created_at || Date.now(),
          status: 'sent',
        }));

        // 添加AI回复
        response.data.forEach(item => {
          if (item.answer) {
            messages.push({
              id: item.answer.id || utils.generateId(),
              content: item.answer.content || '',
              richContent: parseMarkdown(item.answer.content || ''), // 🎯 解析Markdown格式
              type: 'ai',
              sender: 'ai',
              timestamp: item.answer.created_at || Date.now(),
              status: 'received',
            });
          }
        });

        // 按时间排序
        messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        this.setData({
          messageList: messages,
          hasMore: false, // 简化分页逻辑
        });

        // 滚动到底部
        this.scrollToBottom();
      }
    } catch (error) {
      console.error('加载历史消息失败:', error);
    }
  },

  /**
   * 加载更多消息
   */
  async loadMoreMessages() {
    if (this.data.loadingHistory) return;

    try {
      this.setData({ loadingHistory: true });

      const page = Math.ceil(this.data.messageList.length / 20) + 1;
      const response = await api.learning.getMessages({
        session_id: this.data.sessionId,
        page,
        size: 20,
      });

      if (response.success && response.data.length > 0) {
        const newMessages = response.data.map(msg => ({
          id: msg.id,
          content: msg.content,
          type: msg.type,
          sender: msg.sender,
          timestamp: msg.created_at,
          status: msg.status || 'sent',
        }));

        this.setData({
          messageList: [...newMessages, ...this.data.messageList],
          hasMore: response.pagination?.has_more || false,
        });
      } else {
        this.setData({ hasMore: false });
      }
    } catch (error) {
      console.error('加载更多消息失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'error',
      });
    } finally {
      this.setData({ loadingHistory: false });
    }
  },

  /**
   * 加载用户统计
   */
  async loadUserStats() {
    try {
      const stats = await api.learning.getSystemStats();
      if (stats.success) {
        this.setData({ questionStats: stats.data });
      }
    } catch (error) {
      console.error('加载用户统计失败:', error);
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    try {
      this.setData({ refreshing: true });

      await Promise.all([
        this.loadHistoryMessages(),
        this.checkAIStatus(),
        this.loadUserStats(),
        this.loadRecommendedQuestions(),
      ]);
    } catch (error) {
      console.error('刷新数据失败:', error);
    } finally {
      this.setData({ refreshing: false });
    }
  },

  /**
   * 发送消息
   */
  async sendMessage() {
    const inputText = this.data.inputText.trim();

    // 调试信息
    console.log('发送消息调试:', {
      原始输入: this.data.inputText,
      去空格后: inputText,
      长度: inputText.length,
      字符码: inputText.split('').map(c => c.charCodeAt(0)),
      图片数量: this.data.uploadedImages.length,
    });

    // 检查是否有输入或图片
    if (!inputText && this.data.uploadedImages.length === 0) {
      wx.showToast({
        title: '请输入问题或选择图片',
        icon: 'none',
      });
      return;
    }

    if (!this.data.canAsk) {
      wx.showToast({
        title: '您暂无提问权限',
        icon: 'none',
      });
      return;
    }

    if (!this.data.isConnected) {
      wx.showToast({
        title: 'AI助手暂时离线',
        icon: 'none',
      });
      return;
    }

    try {
      // 1. 先上传所有图片（如果有的话）
      let imageUrls = [];
      if (this.data.uploadedImages.length > 0) {
        try {
          imageUrls = await this.uploadAllImages();
          console.log('图片上传完成，AI URLs:', imageUrls);
        } catch (uploadError) {
          console.error('图片上传失败:', uploadError);
          wx.showToast({
            title: '图片上传失败，请重试',
            icon: 'error',
          });
          return; // 上传失败则不发送消息
        }
      }

      // 2. 创建用户消息（包含文本和图片引用）
      const userMessage = {
        id: this.generateMessageId(),
        content: inputText || '[图片]', // 如果没有文本，显示 [图片]
        type: 'text',
        sender: 'user',
        timestamp: new Date().toISOString(),
        status: 'sending',
        images: this.data.uploadedImages.map(img => ({
          tempFilePath: img.tempFilePath,
          aiUrl: img.aiUrl,
        })), // 保存图片信息用于显示
      };

      // 3. 清空输入和图片列表
      this.setData({
        messageList: [...this.data.messageList, userMessage],
        inputText: '',
        uploadedImages: [], // 清空已上传的图片
        sending: true,
        isAITyping: true,
      });

      // 滚动到底部
      this.scrollToBottom();

      // 4. 调用API - 包含图片 URLs（与 Web 前端对齐）
      const requestParams = {
        content: inputText || '请分析这张图片中的内容，如果是学习相关的题目，请详细解答。',
        session_id: this.data.sessionId,
        subject: this.data.currentSubject !== 'all' ? this.data.currentSubject : undefined,
        use_context: true,
        include_history: true,
        max_history: 10,
      };

      // 只有在有图片时才添加 image_urls 参数
      if (imageUrls.length > 0) {
        requestParams.image_urls = imageUrls;
      }

      console.log('发送请求参数:', requestParams);

      const response = await api.learning.askQuestion(requestParams);

      // 后端返回格式: { question: {...}, answer: {...}, session: {...} }
      console.log('API响应:', response);

      if (response && response.answer && response.answer.content) {
        // 更新用户消息状态
        const updatedUserMessage = {
          ...userMessage,
          status: 'sent',
          id: response.question.id,
        };

        // 创建AI回复消息
        const aiMessage = {
          id: response.answer.id,
          content: response.answer.content,
          richContent: parseMarkdown(response.answer.content), // 🎯 解析Markdown格式
          type: 'text',
          sender: 'ai',
          timestamp: response.answer.created_at,
          status: 'received',
          confidence: response.answer.confidence_score || 0,
          sources: response.answer.sources || [],
        };

        // 更新消息列表
        const newMessageList = [...this.data.messageList];
        newMessageList[newMessageList.length - 1] = updatedUserMessage;
        newMessageList.push(aiMessage);

        this.setData({
          messageList: newMessageList,
          isAITyping: false,
        });

        // 打字机效果显示AI回复
        this.showAIReplyWithTyping(aiMessage);

        // 更新对话上下文
        this.updateConversationContext(userMessage, aiMessage);

        // 更新统计
        this.updateQuestionStats();
      } else {
        console.error('AI回复格式错误，响应数据:', response);
        throw new Error('AI回复格式错误');
      }
    } catch (error) {
      console.error('发送消息失败:', error);

      // 更新用户消息状态为失败
      const newMessageList = [...this.data.messageList];
      const lastMessage = newMessageList[newMessageList.length - 1];
      lastMessage.status = 'failed';
      lastMessage.error = error.message;

      this.setData({
        messageList: newMessageList,
        isAITyping: false,
      });

      // 显示重试选项
      this.showRetryOption(error.message);
    } finally {
      this.setData({ sending: false });
    }
  },

  /**
   * 带MCP增强的发送消息
   */
  async sendMessageWithMCP(messageData) {
    try {
      let enhancedMessage = { ...messageData };

      // 如果MCP启用，添加个性化上下文
      if (this.data.mcpEnabled && this.data.personalizedContext) {
        const { userInfo, personalizedContext } = this.data;

        // 分析问题类型
        const questionType = await mcpService.analyzeQuestionType(messageData.content);

        // 构建个性化上下文
        const contextPrompt = mcpService.buildContextPrompt(
          personalizedContext,
          messageData.content,
        );

        // 增强消息内容
        if (contextPrompt) {
          enhancedMessage.enhanced_prompt = contextPrompt;
          enhancedMessage.question_type = questionType;
          enhancedMessage.user_context = {
            learning_style: personalizedContext.learningStyle,
            weakness_points: personalizedContext.weaknessPoints.slice(0, 3),
            recent_subjects: personalizedContext.preferences.preferred_subjects || [],
          };
        }

        console.log('MCP增强上下文:', enhancedMessage.user_context);
      }

      // 调用API - 确保参数名称正确
      const apiParams = {
        ...enhancedMessage,
        question: enhancedMessage.content, // API期望question参数
      };
      delete apiParams.content; // 移除content参数避免混淆

      const response = await api.learning.askQuestion(apiParams);

      // 记录学习行为
      if (response.success && this.data.mcpEnabled) {
        setTimeout(() => {
          mcpService.updateLearningBehavior(
            response.data.ai_message_id,
            enhancedMessage.question_type || 'general',
            true, // 默认有帮助，后续可根据用户评价更新
          );
        }, 1000);
      }

      return response;
    } catch (error) {
      console.error('MCP增强发送失败:', error);
      // 回退到普通发送 - 确保参数名称正确
      const fallbackParams = {
        ...messageData,
        question: messageData.content,
      };
      delete fallbackParams.content;
      return await api.learning.askQuestion(fallbackParams);
    }
  },

  /**
   * 生成消息ID
   */
  generateMessageId() {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * 获取对话上下文
   */
  getConversationContext() {
    // 获取最近5轮对话作为上下文
    const recentMessages = this.data.messageList
      .filter(msg => msg.status === 'sent' || msg.status === 'received')
      .slice(-10);

    return recentMessages.map(msg => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.content,
    }));
  },

  /**
   * 更新对话上下文
   */
  updateConversationContext(userMessage, aiMessage) {
    const context = this.data.conversationContext;
    context.push(
      { role: 'user', content: userMessage.content },
      { role: 'assistant', content: aiMessage.content },
    );

    // 保持上下文长度不超过20条
    if (context.length > 20) {
      context.splice(0, context.length - 20);
    }

    this.setData({ conversationContext: context });
  },

  /**
   * 打字机效果显示AI回复
   */
  showAIReplyWithTyping(message) {
    const content = message.content;
    let currentText = '';
    let index = 0;

    const typeInterval = setInterval(() => {
      if (index < content.length) {
        currentText += content[index];

        // 更新消息内容
        const messageList = [...this.data.messageList];
        const lastMessage = messageList[messageList.length - 1];
        lastMessage.content = currentText;
        // 实时解析当前已显示的内容
        lastMessage.richContent = parseMarkdown(currentText);

        this.setData({ messageList });
        this.scrollToBottom();

        index++;
      } else {
        clearInterval(typeInterval);
        this.setData({ isAITyping: false });
      }
    }, 50);

    // 保存定时器引用以便清理
    this.typingTimer = typeInterval;
  },

  /**
   * 停止AI打字动画
   */
  stopAITyping() {
    if (this.typingTimer) {
      clearInterval(this.typingTimer);
      this.typingTimer = null;
    }
    this.setData({ isAITyping: false });
  },

  /**
   * 更新问题统计
   */
  updateQuestionStats() {
    const stats = { ...this.data.questionStats };
    stats.total += 1;

    if (stats.bySubject[this.data.currentSubject]) {
      stats.bySubject[this.data.currentSubject] += 1;
    } else {
      stats.bySubject[this.data.currentSubject] = 1;
    }

    this.setData({ questionStats: stats });
  },

  /**
   * 滚动到底部
   */
  scrollToBottom() {
    setTimeout(() => {
      this.setData({
        scrollTop: 999999,
      });
    }, 100);
  },

  /**
   * 显示重试选项
   */
  showRetryOption(errorMessage) {
    wx.showModal({
      title: '发送失败',
      content: errorMessage || '网络异常，是否重试？',
      confirmText: '重试',
      cancelText: '取消',
      success: res => {
        if (res.confirm) {
          this.retryLastMessage();
        }
      },
    });
  },

  /**
   * 重试最后一条消息
   */
  async retryLastMessage() {
    const messageList = [...this.data.messageList];
    const lastMessage = messageList[messageList.length - 1];

    if (lastMessage && lastMessage.status === 'failed') {
      // 重新设置输入内容并发送
      this.setData({ inputText: lastMessage.content });

      // 移除失败的消息
      messageList.pop();
      this.setData({ messageList });

      // 重新发送
      await this.sendMessage();
    }
  },

  /**
   * 输入内容变化
   */
  onInputChange(e) {
    const newValue = e.detail.value;
    const hasContent = newValue.trim().length > 0;
    console.log('输入变化调试:', {
      新值: newValue,
      长度: newValue.length,
      是否有内容: hasContent,
      事件对象: e.detail,
    });
    this.setData({
      inputText: newValue,
      hasInputContent: hasContent,
    });
  },

  /**
   * 输入框获得焦点
   */
  onInputFocus(e) {
    this.setData({
      inputFocus: true,
      inputBottom: e.detail.height || 0,
    });

    // 延迟滚动到底部
    setTimeout(() => {
      this.scrollToBottom();
    }, 300);
  },

  /**
   * 输入框失去焦点
   */
  onInputBlur() {
    this.setData({
      inputFocus: false,
      inputBottom: 0,
    });
  },

  /**
   * 快捷回复
   */
  onQuickReply(e) {
    const { question } = e.currentTarget.dataset;
    this.setData({ inputText: question });
    this.sendMessage();
  },

  /**
   * 快速问题
   */
  onQuickQuestion(e) {
    const { question } = e.currentTarget.dataset;
    this.setData({ inputText: question });
  },

  /**
   * 切换输入模式（文本/语音）
   */
  onSwitchInputMode() {
    const newMode = this.data.inputMode === 'text' ? 'voice' : 'text';
    this.setData({ inputMode: newMode });

    if (newMode === 'voice') {
      // 检查录音权限
      this.checkRecordPermission();
    }
  },

  /**
   * 检查录音权限
   */
  checkRecordPermission() {
    wx.getSetting({
      success: res => {
        if (!res.authSetting['scope.record']) {
          wx.authorize({
            scope: 'scope.record',
            success: () => {
              console.log('录音权限获取成功');
            },
            fail: () => {
              wx.showModal({
                title: '需要录音权限',
                content: '请在设置中开启录音权限以使用语音功能',
                confirmText: '去设置',
                success: res => {
                  if (res.confirm) {
                    wx.openSetting();
                  }
                },
              });
            },
          });
        }
      },
    });
  },

  /**
   * 开始录音
   */
  startVoiceRecord() {
    if (this.data.recordStatus !== 'idle') return;

    this.setData({
      recordStatus: 'recording',
      recordDuration: 0,
    });

    const recorderManager = wx.getRecorderManager();
    this.recorderManager = recorderManager;

    // 录音开始
    recorderManager.onStart(() => {
      console.log('开始录音');

      // 开始计时
      this.recordTimer = setInterval(() => {
        const duration = this.data.recordDuration + 1;
        this.setData({ recordDuration: duration });

        // 超过60秒自动停止
        if (duration >= 60) {
          this.stopVoiceRecord();
        }
      }, 1000);
    });

    // 录音结束
    recorderManager.onStop(res => {
      console.log('===== 录音结束回调触发 =====');
      console.log('录音结果:', res);
      console.log('当前录音时长:', this.data.recordDuration, '秒');
      console.log('当前状态:', this.data.recordStatus);

      // 清除计时器
      if (this.recordTimer) {
        clearInterval(this.recordTimer);
        this.recordTimer = null;
        console.log('计时器已清除');
      }

      // 录音时长不足1秒，提示
      if (this.data.recordDuration < 1) {
        console.log('录音时间太短，不上传');
        this.setData({ recordStatus: 'idle' });
        wx.showToast({
          title: '录音时间太短',
          icon: 'none',
        });
        return;
      }

      // 上传语音文件
      console.log('开始上传语音文件...');
      this.setData({ recordStatus: 'uploading' });
      this.uploadVoiceFile(res.tempFilePath);
    });

    // 录音错误
    recorderManager.onError(err => {
      console.error('===== 录音错误 =====');
      console.error('错误对象:', err);
      console.error('错误码:', err.errCode);
      console.error('错误信息:', err.errMsg);

      if (this.recordTimer) {
        clearInterval(this.recordTimer);
        this.recordTimer = null;
      }

      this.setData({ recordStatus: 'idle' });

      // 根据错误码显示不同提示
      let errorMsg = '录音失败，请重试';
      if (err.errMsg) {
        const msg = err.errMsg.toLowerCase();
        if (msg.includes('系统') || msg.includes('system') || msg.includes('busy')) {
          errorMsg = '系统繁忙，请稍后再试';
        } else if (msg.includes('权限') || msg.includes('auth') || msg.includes('permission')) {
          errorMsg = '没有录音权限，请在设置中开启';
        } else if (msg.includes('fail')) {
          errorMsg = '录音启动失败，请再试一次';
        }
      }

      wx.showModal({
        title: '录音失败',
        content: errorMsg + '\n\n错误码: ' + (err.errCode || '未知'),
        showCancel: true,
        cancelText: '取消',
        confirmText: '再试',
        success: res => {
          if (res.confirm) {
            // 用户点击再试，提示重新长按
            wx.showToast({
              title: '请再次长按语音按钮',
              icon: 'none',
            });
          }
        },
      });
    });

    // 开始录音（使用简化的配置，提高兼容性）
    recorderManager.start({
      duration: 60000, // 最长录音60秒
      sampleRate: 16000, // 采样率 16kHz
      numberOfChannels: 1, // 单声道
      encodeBitRate: 96000, // 码率 96kbps（降低以提高兼容性）
      format: 'mp3', // MP3格式
    });
  },

  /**
   * 停止录音
   */
  stopVoiceRecord() {
    if (this.data.recordStatus === 'recording' && this.recorderManager) {
      this.recorderManager.stop();
    }
  },

  /**
   * 取消录音
   */
  cancelVoiceRecord() {
    console.log('取消录音');

    if (this.recorderManager) {
      this.recorderManager.stop();
    }

    if (this.recordTimer) {
      clearInterval(this.recordTimer);
      this.recordTimer = null;
    }

    this.setData({
      recordStatus: 'idle',
      recordDuration: 0,
      cancelVoice: false,
    });

    wx.showToast({
      title: '已取消',
      icon: 'none',
    });
  },

  /**
   * 上传语音文件并转换为文字
   */
  async uploadVoiceFile(filePath) {
    try {
      console.log('===== 开始上传语音文件 =====');
      console.log('filePath:', filePath);
      console.log('api.baseUrl:', api.baseUrl);

      const uploadUrl = `${api.baseUrl}/api/v1/learning/voice-to-text`;
      console.log('完整上传URL:', uploadUrl);

      const token = await authManager.getToken();
      console.log('Token获取成功:', token ? '✅' : '❌');

      // 显示加载提示
      wx.showLoading({
        title: '识别中...',
        mask: true,
      });

      // 上传语音文件到语音识别API
      const uploadResult = await new Promise((resolve, reject) => {
        console.log('开始调用 wx.uploadFile...');
        wx.uploadFile({
          url: uploadUrl,
          filePath: filePath,
          name: 'voice',
          header: {
            Authorization: `Bearer ${token}`,
          },
          timeout: 30000, // 30秒超时
          success: res => {
            console.log('uploadFile success:', res);
            console.log('服务器返回的原始data:', res.data);
            console.log('响应statusCode:', res.statusCode);
            wx.hideLoading();

            try {
              const data = JSON.parse(res.data);
              console.log('解析后的data:', data);
              console.log('data.success:', data.success);
              console.log('data.data:', data.data);

              if (data.success) {
                resolve(data.data);
              } else {
                console.error('服务器返回失败:', data.message);
                reject(new Error(data.message || '语音转换失败'));
              }
            } catch (error) {
              console.error('响应解析失败:', error);
              console.error('原始响应:', res.data);
              reject(new Error('响应解析失败'));
            }
          },
          fail: err => {
            console.error('uploadFile fail:', err);
            wx.hideLoading();
            reject(err);
          },
        });
      });

      // 将转换的文字设置到输入框
      if (uploadResult.text) {
        this.setData({
          inputText: uploadResult.text,
          recordStatus: 'idle',
        });

        // 显示识别成功提示
        wx.showToast({
          title: '识别成功，正在发送...',
          icon: 'loading',
          duration: 1000,
        });

        console.log('语音识别结果:', uploadResult);

        // 自动发送消息给AI
        // 等待短暂时间让用户看到识别结果
        setTimeout(() => {
          // 检查是否有内容需要发送
          if (this.data.inputText && this.data.inputText.trim()) {
            console.log('自动发送语音识别结果:', this.data.inputText);
            this.sendMessage();
          }
        }, 500);
      } else {
        throw new Error('语音转换结果为空');
      }
    } catch (error) {
      console.error('语音上传失败:', error);

      this.setData({ recordStatus: 'idle' });

      // 错误提示 - 修复 includes 错误
      let errorMessage = '语音识别失败';
      const errMsg = error.message || error.errMsg || '';

      if (errMsg.includes('timeout')) {
        errorMessage = '识别超时，请重试';
      } else if (errMsg.includes('配置')) {
        errorMessage = '语音识别服务暂不可用';
      } else if (errMsg.includes('domain')) {
        errorMessage = '请在微信开发者工具中配置服务器域名';
      } else if (errMsg) {
        errorMessage = errMsg;
      }

      wx.showModal({
        title: '识别失败',
        content: errorMessage,
        showCancel: false,
      });
    }
  },

  /**
   * 语音按钮长按开始录音
   */
  onVoiceTouchStart(e) {
    console.log('开始长按录音');

    // 记录触摸起始位置
    this.setData({
      touchStartY: e.touches[0].pageY,
      cancelVoice: false,
    });

    // 检查录音权限
    wx.getSetting({
      success: res => {
        if (res.authSetting['scope.record']) {
          // 已授权，直接开始录音
          this.startVoiceRecord();
        } else if (res.authSetting['scope.record'] === false) {
          // 用户曾拒绝授权
          wx.showModal({
            title: '需要录音权限',
            content: '请在设置中开启录音权限以使用语音功能',
            confirmText: '去设置',
            success: modalRes => {
              if (modalRes.confirm) {
                wx.openSetting({
                  success: settingRes => {
                    // 用户从设置页面返回后，检查是否授权
                    if (settingRes.authSetting['scope.record']) {
                      wx.showToast({
                        title: '权限已开启，请再次点击语音按钮',
                        icon: 'success',
                      });
                    }
                  },
                });
              }
            },
          });
        } else {
          // 首次请求权限 - 关键修改：授权后提示用户再次点击
          wx.authorize({
            scope: 'scope.record',
            success: () => {
              // 授权成功后提示用户
              wx.showToast({
                title: '权限已开启，请再次长按录音',
                icon: 'success',
                duration: 2000,
              });
            },
            fail: () => {
              wx.showToast({
                title: '需要录音权限',
                icon: 'none',
              });
            },
          });
        }
      },
    });
  },

  /**
   * 语音按钮触摸移动（检测上滑取消）
   */
  onVoiceTouchMove(e) {
    if (this.data.recordStatus !== 'recording') return;

    const currentY = e.touches[0].pageY;
    const moveDistance = this.data.touchStartY - currentY;

    // 上滑超过100px，显示"松开取消"
    const shouldCancel = moveDistance > 100;
    if (shouldCancel !== this.data.cancelVoice) {
      this.setData({ cancelVoice: shouldCancel });

      // 震动反馈
      if (shouldCancel) {
        wx.vibrateShort({ type: 'medium' });
      }
    }
  },

  /**
   * 语音按钮松开停止录音
   */
  onVoiceTouchEnd() {
    console.log('===== 松开按钮 =====');
    console.log('当前状态:', this.data.recordStatus);
    console.log('是否取消:', this.data.cancelVoice);

    if (this.data.recordStatus === 'recording') {
      if (this.data.cancelVoice) {
        // 取消录音
        console.log('用户上滑取消录音');
        this.cancelVoiceRecord();
      } else {
        // 发送录音
        console.log('正常结束录音，调用 stopVoiceRecord');
        this.stopVoiceRecord();
      }
    } else {
      console.log('状态不是 recording，不处理');
    }
  },

  /**
   * 显示图片上传选择菜单
   */
  onShowImageActions() {
    console.log('===== 点击加号按钮 =====');
    console.log('当前 uploadedImages:', this.data.uploadedImages);
    console.log('showImageActions 设置为 true');
    this.setData({ showImageActions: true });
    console.log('showImageActions 当前值:', this.data.showImageActions);
  },

  /**
   * 关闭图片选择菜单
   */
  onCloseImageActions() {
    this.setData({ showImageActions: false });
  },

  /**
   * 拍照
   */
  onTakePhoto() {
    console.log('===== 点击"拍照" =====');
    this.setData({ showImageActions: false });
    console.log('即将调用 chooseImage("camera")');
    this.chooseImage('camera');
  },

  /**
   * 从相册选择图片
   */
  onChooseImage() {
    console.log('===== 点击"从相册选择" =====');
    this.setData({ showImageActions: false });
    console.log('即将调用 chooseImage("album")');
    this.chooseImage('album');
  },

  /**
   * 显示图片上传选择
   */
  onImageUpload() {
    this.setData({ showImageActionSheet: true });
  },

  /**
   * 关闭图片选择弹窗
   */
  onCloseImageActionSheet() {
    this.setData({ showImageActionSheet: false });
  },

  /**
   * 从相机拍照
   */
  onChooseFromCamera() {
    this.setData({ showImageActionSheet: false });
    this.chooseImage('camera');
  },

  /**
   * 从相册选择
   */
  onChooseFromAlbum() {
    this.setData({ showImageActionSheet: false });
    this.chooseImage('album');
  },

  /**
   * 选择图片
   */
  chooseImage(sourceType) {
    console.log('===== chooseImage 开始 =====');
    console.log('sourceType:', sourceType);
    console.log('当前已选图片数量:', this.data.uploadedImages.length);
    console.log('maxImageCount:', this.data.maxImageCount);

    // 检查图片数量限制
    if (this.data.uploadedImages.length >= this.data.maxImageCount) {
      console.log('已达到图片数量上限');
      wx.showToast({
        title: `最多只能上传${this.data.maxImageCount}张图片`,
        icon: 'none',
      });
      return;
    }

    console.log('调用 wx.chooseMedia...');
    wx.chooseMedia({
      count: this.data.maxImageCount - this.data.uploadedImages.length, // 剩余可选数量
      mediaType: ['image'],
      sourceType: [sourceType],
      camera: 'back',
      success: res => {
        console.log('===== wx.chooseMedia SUCCESS =====');
        console.log('选择的文件数量:', res.tempFiles.length);
        console.log('文件信息:', res.tempFiles);

        // 关闭图片选择菜单
        this.setData({ showImageActions: false });

        // 添加选中的图片到列表
        const newImages = res.tempFiles.map(file => ({
          tempFilePath: file.tempFilePath,
          size: file.size,
          aiUrl: null, // 上传后填充
        }));

        console.log('准备添加的图片:', newImages);

        // 文件大小预检：检查总大小和单个文件大小
        const existingImages = this.data.uploadedImages;
        const allImages = [...existingImages, ...newImages];

        // 计算总大小
        const totalSize = allImages.reduce((sum, img) => sum + (img.size || 0), 0);
        const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(1);

        // 检查是否有超大单个文件（>10MB）
        const oversizedImages = newImages.filter(img => img.size > 10 * 1024 * 1024);

        // 检查总大小是否超过20MB
        const isTotalOversized = totalSize > 20 * 1024 * 1024;

        // 如果有超大文件，警告用户
        if (oversizedImages.length > 0) {
          const oversizedInfo = oversizedImages
            .map(img => `${(img.size / (1024 * 1024)).toFixed(1)}MB`)
            .join('、');

          wx.showModal({
            title: '图片过大提示',
            content: `检测到 ${oversizedImages.length} 张图片超过10MB（${oversizedInfo}），上传时将自动压缩优化。建议使用较小的图片以获得更快的上传速度。`,
            showCancel: false,
            confirmText: '知道了',
          });
        } else if (isTotalOversized) {
          // 总大小超过20MB，提示将自动压缩
          wx.showModal({
            title: '自动压缩提示',
            content: `当前图片总大小为 ${totalSizeMB}MB，上传时将自动压缩优化，以确保上传速度和AI处理效率。`,
            showCancel: false,
            confirmText: '好的',
          });
        }

        this.setData(
          {
            uploadedImages: allImages,
          },
          () => {
            // setData 完成后的回调
            console.log('setData 完成，当前图片数量:', this.data.uploadedImages.length);
            console.log('当前图片总大小:', totalSizeMB + 'MB');

            // 给用户明确的反馈
            if (!oversizedImages.length && !isTotalOversized) {
              wx.showToast({
                title: `已选择 ${this.data.uploadedImages.length} 张图片`,
                icon: 'success',
                duration: 1500,
              });
            }
          },
        );

        console.log('已选择图片总数:', this.data.uploadedImages.length);
        console.log('===== chooseImage 完成 =====');
      },
      fail: error => {
        console.error('===== wx.chooseMedia FAIL =====');
        console.error('选择图片失败:', error);
        if (error.errMsg.includes('cancel')) {
          console.log('用户取消选择');
          return;
        }

        wx.showToast({
          title: '选择图片失败',
          icon: 'error',
        });
      },
    });
  },

  /**
   * 移除已选图片
   */
  removeImage(e) {
    const { index } = e.currentTarget.dataset;
    console.log('===== 删除图片 =====');
    console.log('删除索引:', index);

    const images = [...this.data.uploadedImages];
    images.splice(index, 1);

    this.setData({ uploadedImages: images });
    console.log('删除后剩余图片数量:', this.data.uploadedImages.length);
  },

  /**
   * 图片加载成功回调
   */
  onImageLoad(e) {
    console.log('图片加载成功:', e.detail);
  },

  /**
   * 图片加载失败回调
   */
  onImageLoadError(e) {
    console.error('图片加载失败:', e.detail);
    wx.showToast({
      title: '图片加载失败',
      icon: 'none',
    });
  },

  /**
   * 图片压缩处理
   * 策略：超过2MB或需要优化时才压缩
   * @param {string} filePath - 原始图片路径
   * @param {number} originalSize - 原始文件大小（字节）
   * @returns {Promise<{path: string, size: number, compressed: boolean}>} 压缩后的文件信息
   */
  async compressImageIfNeeded(filePath, originalSize) {
    const COMPRESS_THRESHOLD = 2 * 1024 * 1024; // 2MB阈值
    const TARGET_WIDTH = 1920; // AI识别最佳分辨率
    const QUALITY = 80; // 压缩质量80%

    // 判断是否需要压缩
    const needCompress = originalSize > COMPRESS_THRESHOLD;

    if (!needCompress) {
      console.log(
        `图片无需压缩: ${(originalSize / 1024).toFixed(0)}KB < ${COMPRESS_THRESHOLD / 1024}KB`,
      );
      return {
        path: filePath,
        size: originalSize,
        compressed: false,
      };
    }

    try {
      console.log(`开始压缩图片: ${(originalSize / 1024).toFixed(0)}KB`);

      const res = await wx.compressImage({
        src: filePath,
        quality: QUALITY,
        compressedWidth: TARGET_WIDTH,
        compressedHeight: TARGET_WIDTH,
      });

      // 获取压缩后的文件信息
      const fileInfo = await new Promise((resolve, reject) => {
        wx.getFileInfo({
          filePath: res.tempFilePath,
          success: resolve,
          fail: reject,
        });
      });

      const compressedSize = fileInfo.size;
      const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(1);

      console.log(
        `图片压缩成功: ${(originalSize / 1024).toFixed(0)}KB → ${(compressedSize / 1024).toFixed(0)}KB (减少${compressionRatio}%)`,
      );

      return {
        path: res.tempFilePath,
        size: compressedSize,
        compressed: true,
      };
    } catch (error) {
      console.warn('图片压缩失败，使用原图:', error);
      wx.showToast({
        title: '图片压缩失败，使用原图上传',
        icon: 'none',
        duration: 2000,
      });

      return {
        path: filePath,
        size: originalSize,
        compressed: false,
      };
    }
  },

  /**
   * 上传单张图片到 AI 服务
   * 返回 AI 可访问的公开 URL
   * @param {string} filePath - 图片文件路径
   * @param {number} originalSize - 原始文件大小
   */
  async uploadImageToAI(filePath, originalSize = 0) {
    try {
      // 1. 先压缩图片（如果需要）
      const compressedImage = await this.compressImageIfNeeded(filePath, originalSize);

      const token = await authManager.getToken();

      console.log('===== 开始上传图片 =====');
      console.log('文件路径:', compressedImage.path);
      console.log('文件大小:', (compressedImage.size / 1024).toFixed(0) + 'KB');
      console.log('已压缩:', compressedImage.compressed ? '是' : '否');
      console.log('上传 URL:', `${config.api.baseUrl}/api/v1/files/upload-for-ai`);
      console.log('Token:', token ? '已获取' : '未获取');

      const uploadResult = await new Promise((resolve, reject) => {
        const uploadTask = wx.uploadFile({
          url: `${config.api.baseUrl}/api/v1/files/upload-for-ai`,
          filePath: compressedImage.path, // 使用压缩后的路径
          name: 'file',
          timeout: 120000, // 设置 120 秒超时，与API超时一致
          header: {
            Authorization: `Bearer ${token}`,
          },
          success: res => {
            console.log('===== 上传成功响应 =====');
            console.log('HTTP 状态码:', res.statusCode);
            console.log('响应数据:', res.data);

            try {
              const result = JSON.parse(res.data);
              if (result.success && result.data) {
                console.log('AI URL:', result.data.ai_accessible_url);
                resolve(result.data.ai_accessible_url);
              } else {
                console.error('上传失败:', result.message);
                reject(new Error(result.message || '图片上传失败'));
              }
            } catch (error) {
              console.error('响应解析失败:', error);
              console.error('原始响应:', res.data);
              reject(new Error('响应解析失败'));
            }
          },
          fail: error => {
            console.error('===== 上传失败 =====');
            console.error('错误类型:', error.errMsg);
            console.error('完整错误:', error);

            // 根据错误类型给出更友好的提示
            let errorMessage = '图片上传失败';
            let errorType = 'unknown';

            if (error.errMsg.includes('timeout')) {
              errorMessage = '上传超时';
              errorType = 'timeout';
            } else if (error.errMsg.includes('fail uploadFile')) {
              errorMessage = '网络连接失败';
              errorType = 'network';
            } else if (error.errMsg.includes('abort')) {
              errorMessage = '上传已取消';
              errorType = 'abort';
            }

            const detailedError = new Error(errorMessage);
            detailedError.type = errorType;
            detailedError.originalError = error;

            reject(detailedError);
          },
        });

        // 监听上传进度
        uploadTask.onProgressUpdate(res => {
          console.log('上传进度:', res.progress + '%');
          console.log('已上传:', res.totalBytesSent);
          console.log('总大小:', res.totalBytesExpectedToSend);
        });
      });

      console.log('===== 上传完成 =====');
      return uploadResult;
    } catch (error) {
      console.error('图片上传失败:', error);
      throw error;
    }
  },

  /**
   * 批量上传所有待发送的图片
   */
  async uploadAllImages() {
    const imagesToUpload = this.data.uploadedImages.filter(img => !img.aiUrl);
    if (imagesToUpload.length === 0) {
      return []; // 没有需要上传的图片
    }

    console.log(`开始上传 ${imagesToUpload.length} 张图片...`);

    // 显示上传进度
    wx.showLoading({
      title: `上传图片 0/${imagesToUpload.length}`,
      mask: true,
    });

    this.setData({ uploadingCount: imagesToUpload.length });

    try {
      const aiUrls = [];

      // 顺序上传图片（避免并发导致的问题）
      for (let i = 0; i < imagesToUpload.length; i++) {
        const img = imagesToUpload[i];

        // 更新上传进度
        wx.showLoading({
          title: `上传图片 ${i + 1}/${imagesToUpload.length}`,
          mask: true,
        });

        try {
          const aiUrl = await this.uploadImageToAI(img.tempFilePath, img.size);

          // 更新图片列表中的 aiUrl
          const allImages = [...this.data.uploadedImages];
          const imgIndex = allImages.findIndex(item => item.tempFilePath === img.tempFilePath);
          if (imgIndex !== -1) {
            allImages[imgIndex].aiUrl = aiUrl;
          }

          this.setData({ uploadedImages: allImages });

          aiUrls.push(aiUrl);
        } catch (error) {
          console.error(`图片 ${i + 1} 上传失败:`, error);

          // 隐藏加载提示，准备显示详细错误
          wx.hideLoading();
          this.setData({ uploadingCount: 0 });

          // 根据错误类型提供具体的解决建议
          let errorTitle = '图片上传失败';
          let errorContent = '请重试或选择其他图片';

          if (error.type === 'timeout') {
            errorTitle = '上传超时';
            errorContent =
              '网络连接较慢，建议：\n1. 切换到WiFi环境\n2. 选择较小的图片\n3. 稍后重试';
          } else if (error.type === 'network') {
            errorTitle = '网络连接失败';
            errorContent =
              '无法连接到服务器，请检查：\n1. 网络是否正常\n2. 是否开启了飞行模式\n3. 稍后重试';
          } else if (error.message && error.message.includes('过大')) {
            errorTitle = '图片文件过大';
            errorContent =
              '即使压缩后仍超出限制，建议：\n1. 选择分辨率较低的图片\n2. 使用相机拍照而非从相册选择\n3. 分批上传图片';
          } else if (error.message && error.message.includes('格式')) {
            errorTitle = '图片格式不支持';
            errorContent = '请使用 JPG、PNG 或 WebP 格式的图片';
          }

          wx.showModal({
            title: errorTitle,
            content: errorContent,
            showCancel: true,
            confirmText: '知道了',
            cancelText: '重试',
            success: res => {
              if (res.cancel) {
                // 用户选择重试，递归调用上传
                this.uploadAllImages().catch(retryError => {
                  console.error('重试上传失败:', retryError);
                });
              }
            },
          });

          throw error;
        }
      }

      wx.hideLoading();
      this.setData({ uploadingCount: 0 });

      console.log('所有图片上传成功:', aiUrls);
      return aiUrls;
    } catch (error) {
      // 错误已在上面处理，这里只需要抛出
      console.error('批量上传中断:', error);
      throw error;
    }
  },

  /**
   * 切换学科
   */
  switchSubject(subject) {
    this.setData({ currentSubject: subject });
    this.loadRecommendedQuestions();
  },

  /**
   * 消息重试
   */
  onRetryMessage(e) {
    const { messageId } = e.detail;
    const messageList = [...this.data.messageList];
    const message = messageList.find(msg => msg.id === messageId);

    if (message) {
      this.setData({ inputText: message.content });
      this.sendMessage();
    }
  },

  /**
   * 复制消息
   */
  onCopyMessage(e) {
    const { content } = e.detail;
    wx.setClipboardData({
      data: content,
      success: () => {
        wx.showToast({
          title: '已复制',
          icon: 'success',
        });
      },
    });
  },

  /**
   * 点赞消息
   */
  onLikeMessage(e) {
    const { messageId, liked } = e.detail;

    // 调用API记录点赞
    api.chat
      .likeMessage({
        message_id: messageId,
        liked: !liked,
      })
      .then(response => {
        if (response.success) {
          wx.showToast({
            title: liked ? '已取消点赞' : '已点赞',
            icon: 'success',
          });
        }
      })
      .catch(error => {
        console.error('点赞失败:', error);
      });
  },

  /**
   * 重新连接
   */
  reconnectIfNeeded() {
    if (this.data.networkStatus === 'online' && !this.data.isConnected) {
      this.checkAIStatus();
    }
  },

  /**
   * 更新在线状态
   */
  updateOnlineStatus() {
    this.checkAIStatus();
  },

  /**
   * 切换工具栏显示
   */
  onToggleTools() {
    this.setData({ showTools: !this.data.showTools });
  },

  /**
   * 显示功能菜单
   */
  onShowActionSheet() {
    this.setData({ showActionSheet: true });
  },

  /**
   * 关闭功能菜单
   */
  onCloseActionSheet() {
    this.setData({ showActionSheet: false });
  },

  /**
   * 显示历史会话弹窗
   */
  /**
   * 新建对话
   */
  async onNewChat() {
    try {
      // 如果当前已经是新会话且没有消息，直接返回
      if (this.data.isNewSession && this.data.messageList.length === 0) {
        wx.showToast({
          title: '当前已是新对话',
          icon: 'none',
          duration: 1500,
        });
        return;
      }

      // 如果有未保存的内容，提示用户
      if (this.data.inputText.trim() || this.data.uploadedImages.length > 0) {
        const confirm = await new Promise(resolve => {
          wx.showModal({
            title: '提示',
            content: '当前有未发送的内容，是否要新建对话？',
            confirmText: '新建',
            cancelText: '取消',
            success: res => resolve(res.confirm),
            fail: () => resolve(false),
          });
        });

        if (!confirm) return;
      }

      wx.showLoading({ title: '创建中...' });

      // 生成新的会话 ID
      const newSessionId = this.generateSessionId();

      // 保存新会话 ID
      wx.setStorageSync('chat_session_id', newSessionId);

      // 重置页面状态
      this.setData({
        sessionId: newSessionId,
        isNewSession: true,
        messageList: [],
        inputText: '',
        uploadedImages: [],
        conversationContext: [],
      });

      wx.hideLoading();

      wx.showToast({
        title: '已创建新对话',
        icon: 'success',
        duration: 1500,
      });

      // 滚动到顶部
      this.setData({ scrollTop: 0 });

      console.log('新建对话成功:', newSessionId);
    } catch (error) {
      console.error('新建对话失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '创建失败',
        icon: 'error',
      });
    }
  },

  async onShowHistory() {
    try {
      // 加载最近的会话列表
      await this.loadRecentSessions();
      this.setData({ showHistoryPopup: true });
    } catch (error) {
      console.error('加载历史会话失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'none',
      });
    }
  },

  /**
   * 关闭历史会话弹窗
   */
  onCloseHistory() {
    this.setData({ showHistoryPopup: false });
  },

  /**
   * 加载最近的会话列表
   */
  async loadRecentSessions() {
    try {
      // 调用后端API获取历史会话
      const response = await api.learning.getSessions({
        page: 1,
        size: 6,
        status_filter: 'active', // 只获取活跃会话
      });

      console.log('加载会话列表响应:', response);

      // 兼容两种响应格式
      const sessionList = response.data || response.items || [];

      // 转换为前端需要的格式
      const sessions = sessionList.map(session => ({
        id: session.id,
        title: session.title || '未命名会话',
        messageCount: session.message_count || 0,
        lastMessageTime: new Date(session.last_active_at || session.updated_at).getTime(),
        timeText: this.formatSessionTime(new Date(session.last_active_at || session.updated_at)),
      }));

      console.log(`加载了 ${sessions.length} 个会话`);

      this.setData({
        recentSessions: sessions,
      });
    } catch (error) {
      console.error('加载最近会话失败:', error);
      // 失败时使用模拟数据作为降级方案
      const mockSessions = this.generateMockSessions();
      this.setData({
        recentSessions: mockSessions,
      });
      throw error;
    }
  },

  /**
   * 生成模拟会话数据（临时使用）
   */
  generateMockSessions() {
    const now = new Date();
    const sessions = [];

    // 当前会话
    if (this.data.sessionId && this.data.messageList.length > 0) {
      const firstMessage = this.data.messageList[0];
      sessions.push({
        id: this.data.sessionId,
        title: firstMessage?.content?.substring(0, 20) || '当前会话',
        messageCount: this.data.messageList.length,
        lastMessageTime: now.getTime(),
        timeText: '刚刚',
      });
    }

    // 模拟历史会话
    const mockTitles = [
      '今天的作业有疑问吗？',
      '需要复习什么知识点？',
      '数学函数概念讲解',
      '英语语法点总结',
      '物理实验分析讨论',
    ];

    mockTitles.forEach((title, index) => {
      const hoursAgo = (index + 1) * 3;
      const time = new Date(now.getTime() - hoursAgo * 60 * 60 * 1000);
      sessions.push({
        id: `session_${index + 1}`,
        title: title,
        messageCount: Math.floor(Math.random() * 10) + 3,
        lastMessageTime: time.getTime(),
        timeText: this.formatSessionTime(time),
      });
    });

    return sessions.slice(0, 6); // 最多显示6条
  },

  /**
   * 格式化时间戳为可读时间
   */
  formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (hours < 1) {
      return '刚刚';
    } else if (hours < 24) {
      const hour = date.getHours();
      const minute = date.getMinutes();
      return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
    } else if (
      date.toDateString() === new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString()
    ) {
      return '昨天';
    } else {
      return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
  },

  /**
   * 格式化会话时间
   */
  formatSessionTime(time) {
    const now = new Date();
    const diff = now.getTime() - time.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) {
      return '刚刚';
    } else if (hours < 24) {
      return `${hours}小时前`;
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return `${time.getMonth() + 1}月${time.getDate()}日`;
    }
  },

  /**
   * 选择历史会话
   */
  async onSelectSession(e) {
    const { sessionId } = e.currentTarget.dataset;

    if (sessionId === this.data.sessionId) {
      // 已经是当前会话，直接关闭弹窗
      this.onCloseHistory();
      return;
    }

    try {
      wx.showLoading({ title: '加载会话中...' });

      // 1. 获取会话详情
      const session = await api.learning.getSessionDetail(sessionId);

      // 2. 加载会话的历史消息
      const historyResponse = await api.learning.getMessages({
        sessionId: sessionId,
        page: 1,
        size: 50,
      });

      console.log('加载历史消息响应:', historyResponse);

      // 3. 转换为聊天消息格式
      const messages = [];
      // 兼容两种响应格式: historyResponse.data 或 historyResponse.items
      const dataList = historyResponse.data || historyResponse.items || [];

      if (dataList.length > 0) {
        dataList.forEach(pair => {
          // 添加用户问题
          if (pair.question) {
            messages.push({
              id: pair.question.id,
              sender: 'user',
              type: 'text',
              content: pair.question.content,
              timestamp: this.formatTime(pair.question.created_at),
              images: pair.question.image_urls || [],
              status: 'sent',
            });
          }

          // 添加AI回答
          if (pair.answer) {
            messages.push({
              id: pair.answer.id,
              sender: 'ai',
              type: 'text',
              content: pair.answer.content,
              richContent: parseMarkdown(pair.answer.content || ''), // 🎯 解析Markdown格式
              timestamp: this.formatTime(pair.answer.created_at),
              confidence: pair.answer.confidence,
              sources: pair.answer.sources || [],
              status: 'received',
            });
          }
        });
      }

      console.log(`解析到 ${messages.length} 条消息`);

      // 4. 更新当前会话状态
      this.setData({
        sessionId: sessionId,
        isNewSession: false, // 已存在的会话
        messageList: messages,
        conversationContext: messages.map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.content,
        })),
      });

      // 5. 保存到本地存储
      wx.setStorageSync('chat_session_id', sessionId);

      // 5. 关闭弹窗
      this.onCloseHistory();

      // 6. 滚动到底部
      setTimeout(() => {
        this.scrollToBottom();
      }, 300);

      wx.hideLoading();
      wx.showToast({
        title: '会话已切换',
        icon: 'success',
        duration: 1500,
      });

      console.log(`切换到会话: ${sessionId}, 加载了 ${messages.length} 条消息`);
    } catch (error) {
      wx.hideLoading();
      console.error('切换会话失败:', error);
      wx.showToast({
        title: error.message || '切换失败',
        icon: 'none',
        duration: 2000,
      });
    }
  },

  /**
   * 切换学科
   */
  onSwitchSubject(e) {
    const { subject } = e.currentTarget.dataset;

    // 更新学科选择状态
    const subjects = this.data.subjects.map(s => ({
      ...s,
      active: s.id === subject,
    }));

    this.setData({
      subjects,
      currentSubject: subject,
    });

    this.switchSubject(subject);
  },

  /**
   * 选择学科
   */
  onSelectSubject() {
    const subjects = this.data.subjects.map(s => s.name);

    wx.showActionSheet({
      itemList: subjects,
      success: res => {
        const selectedSubject = this.data.subjects[res.tapIndex];
        this.switchSubject(selectedSubject.id);

        wx.showToast({
          title: `已切换到${selectedSubject.name}`,
          icon: 'success',
        });
      },
    });
  },

  /**
   * 上传图片
   */
  onUploadImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: res => {
        this.handleImageUpload(res.tempFiles[0]);
      },
    });
  },

  /**
   * 处理图片上传
   */
  async handleImageUpload(file) {
    try {
      wx.showLoading({ title: '上传中...' });

      const uploadResult = await api.file.uploadImage({
        filePath: file.tempFilePath,
        session_id: this.data.sessionId,
      });

      if (uploadResult.success) {
        // 创建图片消息
        const imageMessage = {
          id: this.generateMessageId(),
          content: uploadResult.data.url,
          type: 'image',
          sender: 'user',
          timestamp: new Date().toISOString(),
          status: 'sent',
        };

        this.setData({
          messageList: [...this.data.messageList, imageMessage],
        });

        this.scrollToBottom();

        wx.hideLoading();
        wx.showToast({
          title: '上传成功',
          icon: 'success',
        });
      }
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '上传失败',
        icon: 'error',
      });
    }
  },

  /**
   * 语音输入
   */
  onVoiceInput() {
    wx.showModal({
      title: '提示',
      content: '语音输入功能开发中，敬请期待',
      showCancel: false,
    });
  },

  /**
   * 设置页面
   */
  onSettings() {
    wx.navigateTo({
      url: '/pages/chat/settings/index',
    });
  },

  /**
   * 历史记录
   */
  onHistory() {
    wx.navigateTo({
      url: '/pages/chat/history/index',
    });
  },

  /**
   * 清空聊天记录
   */
  onClearChat() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有聊天记录吗？此操作不可恢复。',
      success: res => {
        if (res.confirm) {
          this.clearAllMessages();
        }
      },
    });
  },

  /**
   * 清空所有消息
   */
  async clearAllMessages() {
    try {
      const response = await api.learning.deleteSession(this.data.sessionId);

      if (response.success) {
        this.setData({
          messageList: [],
          conversationContext: [],
        });

        wx.showToast({
          title: '已清空',
          icon: 'success',
        });
      }
    } catch (error) {
      wx.showToast({
        title: '清空失败',
        icon: 'error',
      });
    }
  },

  /**
   * 预览图片
   */
  previewImage(e) {
    const { url } = e.currentTarget.dataset;
    const imageUrls = this.data.messageList
      .filter(msg => msg.type === 'image')
      .map(msg => msg.content);

    wx.previewImage({
      current: url,
      urls: imageUrls,
    });
  },

  /**
   * 加载历史记录 - 占位方法
   */
  onLoadMore() {
    console.log('加载更多历史消息');
    // 这个方法在 loadMoreMessages 中已实现
  },

  /**
   * 头像加载失败处理
   */
  onAvatarError(e) {
    console.warn('头像加载失败，使用默认头像');
    // 图片加载失败时，WXML中已经设置了默认头像作为fallback
  },

  /**
   * 显示错误信息
   */
  showError(message) {
    wx.showToast({
      title: message,
      icon: 'error',
      duration: 2000,
    });
  },
};

// 使用守卫包装页面
Page(createGuardedPage(pageObject, 'pages/learning/index/index'));

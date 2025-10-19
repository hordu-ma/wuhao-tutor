// pages/chat/index/index.js - AI问答对话页面

const { routeGuard } = require('../../../utils/route-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');
const { mcpService } = require('../../../utils/mcp-service.js');
const api = require('../../../api/index.js');
const utils = require('../../../utils/utils.js');

Page({
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
    });

    if (!inputText) {
      wx.showToast({
        title: '输入不能为空，请输入问题',
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
      // 创建用户消息
      const userMessage = {
        id: this.generateMessageId(),
        content: inputText,
        type: 'text',
        sender: 'user',
        timestamp: new Date().toISOString(),
        status: 'sending',
      };

      // 添加到消息列表
      this.setData({
        messageList: [...this.data.messageList, userMessage],
        inputText: '',
        sending: true,
        isAITyping: true,
      });

      // 滚动到底部
      this.scrollToBottom();

      // 直接调用API - 简化版本，对齐网页端
      const response = await api.learning.askQuestion({
        content: inputText,
        session_id: this.data.sessionId,
        subject: this.data.currentSubject !== 'all' ? this.data.currentSubject : undefined,
        use_context: true,
        include_history: true,
        max_history: 10,
      });

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
    console.log('输入变化调试:', {
      新值: newValue,
      长度: newValue.length,
      事件对象: e.detail,
    });
    this.setData({ inputText: newValue });
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

    this.setData({ recordStatus: 'recording' });

    const recorderManager = wx.getRecorderManager();
    this.recorderManager = recorderManager;

    recorderManager.onStart(() => {
      console.log('开始录音');
      wx.showToast({
        title: '正在录音...',
        icon: 'loading',
        duration: 60000,
      });
    });

    recorderManager.onStop(res => {
      console.log('录音结束', res);
      wx.hideToast();
      this.setData({ recordStatus: 'uploading' });
      this.uploadVoiceFile(res.tempFilePath);
    });

    recorderManager.onError(err => {
      console.error('录音错误', err);
      wx.hideToast();
      this.setData({ recordStatus: 'idle' });
      wx.showToast({
        title: '录音失败',
        icon: 'error',
      });
    });

    recorderManager.start({
      duration: 60000, // 最长录音60秒
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 96000,
      format: 'mp3',
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
   * 上传语音文件并转换为文字
   */
  async uploadVoiceFile(filePath) {
    try {
      const token = await authManager.getToken();

      // 上传语音文件到新的API接口
      const uploadResult = await new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${api.baseUrl}/learning/voice-to-text`,
          filePath: filePath,
          name: 'voice', // 后端期望的字段名
          header: {
            Authorization: `Bearer ${token}`,
          },
          success: res => {
            try {
              const data = JSON.parse(res.data);
              if (data.success) {
                resolve(data.data);
              } else {
                reject(new Error(data.message || '语音转换失败'));
              }
            } catch (error) {
              reject(new Error('响应解析失败'));
            }
          },
          fail: reject,
        });
      });

      // 将转换的文字设置到输入框
      if (uploadResult.text) {
        this.setData({
          inputText: uploadResult.text,
          recordStatus: 'idle',
        });
        wx.showToast({
          title: '语音转换成功',
          icon: 'success',
        });
      } else {
        throw new Error('语音转换结果为空');
      }
    } catch (error) {
      console.error('语音上传失败:', error);
      this.setData({ recordStatus: 'idle' });

      // 更详细的错误处理
      let errorMessage = '语音转换失败';
      if (error.message.includes('配置')) {
        errorMessage = '语音识别服务暂不可用';
      } else if (error.message.includes('格式')) {
        errorMessage = '不支持的音频格式';
      } else if (error.message.includes('大小') || error.message.includes('时长')) {
        errorMessage = '音频文件过大或过长';
      }

      wx.showToast({
        title: errorMessage,
        icon: 'error',
      });
    }
  },

  /**
   * 语音按钮长按开始录音
   */
  onVoiceTouchStart() {
    if (this.data.inputMode === 'voice') {
      this.startVoiceRecord();
    }
  },

  /**
   * 语音按钮松开停止录音
   */
  onVoiceTouchEnd() {
    if (this.data.inputMode === 'voice') {
      this.stopVoiceRecord();
    }
  },

  /**
   * 显示图片上传选择菜单
   */
  onShowImageActions() {
    this.setData({ showImageActions: true });
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
    this.setData({ showImageActions: false });
    this.chooseImage('camera');
  },

  /**
   * 从相册选择图片
   */
  onChooseImage() {
    this.setData({ showImageActions: false });
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
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: [sourceType],
      camera: 'back',
      success: res => {
        const tempFilePath = res.tempFiles[0].tempFilePath;
        this.uploadImage(tempFilePath);
      },
      fail: error => {
        console.error('选择图片失败:', error);
        if (error.errMsg.includes('cancel')) return;

        wx.showToast({
          title: '选择图片失败',
          icon: 'error',
        });
      },
    });
  },

  /**
   * 上传图片
   */
  async uploadImage(filePath) {
    try {
      wx.showLoading({
        title: '上传中...',
        mask: true,
      });

      const token = await authManager.getToken();

      const uploadResult = await new Promise((resolve, reject) => {
        wx.uploadFile({
          url: `${api.baseUrl}/files/upload-image-for-learning`,
          filePath: filePath,
          name: 'file', // 注意：后端期望的字段名是 'file'
          header: {
            Authorization: `Bearer ${token}`,
          },
          success: res => {
            try {
              const data = JSON.parse(res.data);
              if (data.success) {
                resolve(data.data);
              } else {
                reject(new Error(data.message || '图片上传失败'));
              }
            } catch (error) {
              reject(new Error('响应解析失败'));
            }
          },
          fail: reject,
        });
      });

      wx.hideLoading();

      // 创建包含图片的消息
      const message = {
        id: utils.generateId(),
        type: 'user',
        content: '[图片]',
        imageUrl: uploadResult.url,
        timestamp: Date.now(),
        status: 'success',
      };

      // 添加到消息列表
      this.addMessage(message);

      // 发送图片分析请求
      this.sendImageAnalysis(uploadResult.url);
    } catch (error) {
      wx.hideLoading();
      console.error('图片上传失败:', error);
      wx.showToast({
        title: error.message || '图片上传失败',
        icon: 'error',
      });
    }
  },

  /**
   * 发送图片分析请求
   * 使用Qwen VL多模态模型进行图片理解
   */
  async sendImageAnalysis(imageUrl) {
    try {
      this.setData({ isAITyping: true });

      // 构建包含图片的消息，通过现有的askQuestion接口发送
      const response = await api.learning.askQuestion({
        content: '请分析这张图片中的内容，如果是学习相关的题目，请详细解答。',
        session_id: this.data.sessionId,
        image_urls: [imageUrl], // 传递图片URL给Qwen VL模型
        subject: this.data.currentSubject !== 'all' ? this.data.currentSubject : undefined,
      });

      if (response.success) {
        const aiMessage = {
          id: utils.generateId(),
          type: 'ai',
          content: response.data.answer || response.data.analysis || '图片分析完成',
          timestamp: Date.now(),
          status: 'success',
        };

        this.addMessage(aiMessage);
      } else {
        throw new Error(response.message || '图片分析失败');
      }
    } catch (error) {
      console.error('图片分析失败:', error);
      const errorMessage = {
        id: utils.generateId(),
        type: 'ai',
        content: '抱歉，图片分析失败，请稍后重试',
        timestamp: Date.now(),
        status: 'error',
      };
      this.addMessage(errorMessage);
    } finally {
      this.setData({ isAITyping: false });
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
});

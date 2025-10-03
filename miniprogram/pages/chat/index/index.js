// pages/chat/index/index.js - AI问答对话页面

const { routeGuard } = require('../../../utils/route-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');
const api = require('../../../api/index.js');
const utils = require('../../../utils/utils.js');

Page({
  data: {
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
    quickQuestions: [
      '今天的作业有疑问吗？',
      '需要复习什么知识点？',
      '想了解什么新内容？',
    ],

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
      imageUrl: '/assets/images/share-chat.png'
    };
  },

  /**
   * 用户点击右上角分享到朋友圈
   */
  onShareTimeline() {
    return {
      title: '五好AI助手 - 智能学习问答',
      imageUrl: '/assets/images/share-chat.png'
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();
      this.setData({ userInfo });

      // 获取用户角色信息
      const userRole = await roleManager.getUserRole();
      this.setData({ userRole: userRole.role });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 初始化权限设置
   */
  async initPermissions() {
    try {
      const permissions = await permissionManager.getUserPermissions();
      this.setData({
        canAsk: permissions.includes('chat:ask'),
        canView: permissions.includes('chat:view'),
        canModerate: permissions.includes('chat:moderate')
      });
    } catch (error) {
      console.error('获取权限失败:', error);
      // 设置默认权限
      this.setData({
        canAsk: true,
        canView: true,
        canModerate: false
      });
    }
  },

  /**
   * 初始化会话
   */
  async initSession() {
    try {
      // 生成或获取会话ID
      let sessionId = wx.getStorageSync('chat_session_id');
      if (!sessionId) {
        sessionId = this.generateSessionId();
        wx.setStorageSync('chat_session_id', sessionId);
      }

      this.setData({ sessionId });

      // 恢复草稿
      const draft = wx.getStorageSync('chat_draft');
      if (draft) {
        this.setData({ inputText: draft });
        wx.removeStorageSync('chat_draft');
      }
    } catch (error) {
      console.error('初始化会话失败:', error);
    }
  },

  /**
   * 初始化聊天功能
   */
  async initChat() {
    try {
      this.setData({ loading: true });

      // 加载历史消息
      await this.loadHistoryMessages();

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
    wx.onNetworkStatusChange((res) => {
      this.setData({
        networkStatus: res.isConnected ? 'online' : 'offline'
      });

      if (res.isConnected) {
        this.reconnectIfNeeded();
      }
    });

    // 获取当前网络状态
    wx.getNetworkType({
      success: (res) => {
        this.setData({
          networkStatus: res.networkType === 'none' ? 'offline' : 'online'
        });
      }
    });
  },

  /**
   * 加载推荐问题
   */
  async loadRecommendedQuestions() {
    try {
      // 根据用户角色和学科获取推荐问题
      const recommendations = await api.chat.getRecommendedQuestions({
        role: this.data.userRole,
        subject: this.data.currentSubject
      });

      if (recommendations.success) {
        this.setData({
          quickReplies: recommendations.data.slice(0, 5),
          quickQuestions: recommendations.data.slice(0, 3)
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
    return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * 检查AI状态
   */
  async checkAIStatus() {
    try {
      const status = await api.chat.getAIStatus();
      this.setData({
        isConnected: status.success && status.data.online,
        aiCapabilities: status.data.capabilities || []
      });
    } catch (error) {
      console.error('检查AI状态失败:', error);
      this.setData({ isConnected: false });
    }
  },

  /**
   * 加载历史消息
   */
  async loadHistoryMessages() {
    try {
      const response = await api.chat.getMessages({
        session_id: this.data.sessionId,
        page: 1,
        size: 20
      });

      if (response.success) {
        const messages = response.data.map(msg => ({
          id: msg.id,
          content: msg.content,
          type: msg.type,
          sender: msg.sender,
          timestamp: msg.created_at,
          status: msg.status || 'sent'
        }));

        this.setData({
          messageList: messages,
          hasMore: response.pagination?.has_more || false
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
      const response = await api.chat.getMessages({
        session_id: this.data.sessionId,
        page,
        size: 20
      });

      if (response.success && response.data.length > 0) {
        const newMessages = response.data.map(msg => ({
          id: msg.id,
          content: msg.content,
          type: msg.type,
          sender: msg.sender,
          timestamp: msg.created_at,
          status: msg.status || 'sent'
        }));

        this.setData({
          messageList: [...newMessages, ...this.data.messageList],
          hasMore: response.pagination?.has_more || false
        });
      } else {
        this.setData({ hasMore: false });
      }
    } catch (error) {
      console.error('加载更多消息失败:', error);
      wx.showToast({
        title: '加载失败',
        icon: 'error'
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
      const stats = await api.chat.getUserStats();
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
        this.loadRecommendedQuestions()
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

    if (!inputText) {
      wx.showToast({
        title: '请输入问题',
        icon: 'none'
      });
      return;
    }

    if (!this.data.canAsk) {
      wx.showToast({
        title: '您暂无提问权限',
        icon: 'none'
      });
      return;
    }

    if (!this.data.isConnected) {
      wx.showToast({
        title: 'AI助手暂时离线',
        icon: 'none'
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
        status: 'sending'
      };

      // 添加到消息列表
      this.setData({
        messageList: [...this.data.messageList, userMessage],
        inputText: '',
        sending: true,
        isAITyping: true
      });

      // 滚动到底部
      this.scrollToBottom();

      // 发送到服务器
      const response = await api.chat.sendMessage({
        session_id: this.data.sessionId,
        content: inputText,
        type: 'text',
        subject: this.data.currentSubject,
        context: this.getConversationContext()
      });

      if (response.success) {
        // 更新用户消息状态
        const updatedUserMessage = {
          ...userMessage,
          status: 'sent',
          id: response.data.user_message_id
        };

        // 创建AI回复消息
        const aiMessage = {
          id: response.data.ai_message_id,
          content: response.data.reply,
          type: 'text',
          sender: 'ai',
          timestamp: response.data.created_at,
          status: 'received',
          confidence: response.data.confidence,
          sources: response.data.sources || []
        };

        // 更新消息列表
        const newMessageList = [...this.data.messageList];
        newMessageList[newMessageList.length - 1] = updatedUserMessage;
        newMessageList.push(aiMessage);

        this.setData({
          messageList: newMessageList,
          isAITyping: false
        });

        // 打字机效果显示AI回复
        this.showAIReplyWithTyping(aiMessage);

        // 更新对话上下文
        this.updateConversationContext(userMessage, aiMessage);

        // 更新统计
        this.updateQuestionStats();

      } else {
        throw new Error(response.message || '发送失败');
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
        isAITyping: false
      });

      // 显示重试选项
      this.showRetryOption(error.message);

    } finally {
      this.setData({ sending: false });
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
      content: msg.content
    }));
  },

  /**
   * 更新对话上下文
   */
  updateConversationContext(userMessage, aiMessage) {
    const context = this.data.conversationContext;
    context.push(
      { role: 'user', content: userMessage.content },
      { role: 'assistant', content: aiMessage.content }
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
        scrollTop: 999999
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
      success: (res) => {
        if (res.confirm) {
          this.retryLastMessage();
        }
      }
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
    this.setData({ inputText: e.detail.value });
  },

  /**
   * 输入框获得焦点
   */
  onInputFocus(e) {
    this.setData({
      inputFocus: true,
      inputBottom: e.detail.height || 0
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
      inputBottom: 0
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
          icon: 'success'
        });
      }
    });
  },

  /**
   * 点赞消息
   */
  onLikeMessage(e) {
    const { messageId, liked } = e.detail;

    // 调用API记录点赞
    api.chat.likeMessage({
      message_id: messageId,
      liked: !liked
    }).then(response => {
      if (response.success) {
        wx.showToast({
          title: liked ? '已取消点赞' : '已点赞',
          icon: 'success'
        });
      }
    }).catch(error => {
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
      active: s.id === subject
    }));

    this.setData({
      subjects,
      currentSubject: subject
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
      success: (res) => {
        const selectedSubject = this.data.subjects[res.tapIndex];
        this.switchSubject(selectedSubject.id);

        wx.showToast({
          title: `已切换到${selectedSubject.name}`,
          icon: 'success'
        });
      }
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
      success: (res) => {
        this.handleImageUpload(res.tempFiles[0]);
      }
    });
  },

  /**
   * 处理图片上传
   */
  async handleImageUpload(file) {
    try {
      wx.showLoading({ title: '上传中...' });

      const uploadResult = await api.chat.uploadImage({
        filePath: file.tempFilePath,
        session_id: this.data.sessionId
      });

      if (uploadResult.success) {
        // 创建图片消息
        const imageMessage = {
          id: this.generateMessageId(),
          content: uploadResult.data.url,
          type: 'image',
          sender: 'user',
          timestamp: new Date().toISOString(),
          status: 'sent'
        };

        this.setData({
          messageList: [...this.data.messageList, imageMessage]
        });

        this.scrollToBottom();

        wx.hideLoading();
        wx.showToast({
          title: '上传成功',
          icon: 'success'
        });
      }
    } catch (error) {
      wx.hideLoading();
      wx.showToast({
        title: '上传失败',
        icon: 'error'
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
      showCancel: false
    });
  },

  /**
   * 设置页面
   */
  onSettings() {
    wx.navigateTo({
      url: '/pages/chat/settings/index'
    });
  },

  /**
   * 历史记录
   */
  onHistory() {
    wx.navigateTo({
      url: '/pages/chat/history/index'
    });
  },

  /**
   * 清空聊天记录
   */
  onClearChat() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空所有聊天记录吗？此操作不可恢复。',
      success: (res) => {
        if (res.confirm) {
          this.clearAllMessages();
        }
      }
    });
  },

  /**
   * 清空所有消息
   */
  async clearAllMessages() {
    try {
      const response = await api.chat.clearMessages({
        session_id: this.data.sessionId
      });

      if (response.success) {
        this.setData({
          messageList: [],
          conversationContext: []
        });

        wx.showToast({
          title: '已清空',
          icon: 'success'
        });
      }
    } catch (error) {
      wx.showToast({
        title: '清空失败',
        icon: 'error'
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
      urls: imageUrls
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
   * 显示错误信息
   */
  showError(message) {
    wx.showToast({
      title: message,
      icon: 'error',
      duration: 2000
    });
  }
});

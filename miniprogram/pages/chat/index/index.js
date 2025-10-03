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

    // AI回复状态
    isAITyping: false, // AI正在回复
    typingMessage: '', // 正在显示的回复内容

    // 页面状态
    loading: false,
    sending: false,
    scrollToView: '', // 滚动到指定消息

    // 功能状态
    recordStatus: 'idle', // 录音状态: idle, recording, uploading
    showQuickReply: true, // 显示快捷回复
    showSubjectTabs: true, // 显示学科标签

    // 快捷回复选项
    quickReplies: [
      '这道题怎么做？',
      '解释一下这个概念',
      '给我出几道练习题',
      '总结一下重点',
      '有什么学习建议吗？',
    ],

    // 学科分类
    subjects: [
      { id: 'all', name: '全部', icon: 'apps-o', active: true },
      { id: 'math', name: '数学', icon: 'balance-o', active: false },
      { id: 'chinese', name: '语文', icon: 'bookmark-o', active: false },
      { id: 'english', name: '英语', icon: 'chat-o', active: false },
      { id: 'physics', name: '物理', icon: 'fire-o', active: false },
      { id: 'chemistry', name: '化学', icon: 'fire-o', active: false },
    ],

    // 学科专业问题模板
    subjectTemplates: {
      math: [
        '这道数学题的解题步骤是什么？',
        '请解释这个数学概念',
        '帮我出几道同类型的练习题',
        '这个公式如何推导？',
        '请检查我的计算过程',
      ],
      chinese: [
        '这篇文章的主题思想是什么？',
        '请分析这个句子的语法结构',
        '帮我改写这段文字',
        '这个字词的含义是什么？',
        '请点评我的作文',
      ],
      english: [
        'Please translate this sentence',
        'How to use this grammar correctly?',
        'What does this phrase mean?',
        'Help me practice conversation',
        'Check my pronunciation',
      ],
      physics: [
        '这个物理现象的原理是什么？',
        '请解释这个物理定律',
        '帮我分析这道物理题',
        '这个公式如何应用？',
        '实验结果如何分析？',
      ],
      chemistry: [
        '这个化学反应的机理是什么？',
        '请解释这个化学概念',
        '帮我配平这个化学方程式',
        '这个实验的操作步骤是什么？',
        '如何分析化学实验结果？',
      ],
    },

    // 智能推荐问题
    recommendedQuestions: [],

    // 问题分类统计
    questionStats: {
      total: 0,
      bySubject: {},
      recentTopics: [],
    },

    // 当前选中学科
    currentSubject: 'all',

    // 页面配置
    showScrollToBottom: false, // 显示滚动到底部按钮

    // 权限状态
    canAsk: false,
    canView: false,
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
      // 执行路由守卫检查
      const guardResult = await routeGuard.checkPageAuth();
      if (!guardResult.success) {
        return;
      }

      // 检查页面访问权限
      const canAccess = await permissionManager.checkPageAccess('pages/chat/index/index');
      if (!canAccess) {
        wx.showModal({
          title: '访问受限',
          content: '您当前的角色无权访问AI问答功能',
          showCancel: false,
          success: () => {
            wx.switchTab({
              url: '/pages/index/index',
            });
          },
        });
        return;
      }

      await this.initUserInfo();
      await this.initPermissions();
      await this.initSession();
      await this.initChat();
      await this.initNetworkMonitor();
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
  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {
    // 停止AI回复动画
    this.stopAITyping();
  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    this.loadChatHistory().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - AI智能问答',
      path: '/pages/chat/index/index',
      imageUrl: '/assets/images/share-chat.png',
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();
      this.setData({ userInfo, userRole });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 初始化权限
   */
  async initPermissions() {
    try {
      const userRole = this.data.userRole;

      // 根据用户角色设置权限
      const permissions = await permissionManager.getPagePermissions(
        'pages/chat/index/index',
        userRole,
      );

      this.setData({
        canAsk: permissions.canAsk || userRole === 'student',
        canView: permissions.canView || true,
        canModerate: permissions.canModerate || userRole === 'teacher',
      });
    } catch (error) {
      console.error('初始化权限失败:', error);
    }
  },

  /**
   * 初始化会话
   */
  async initSession() {
    try {
      // 生成唯一会话ID
      const sessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

      this.setData({
        sessionId,
        conversationContext: [],
        retryCount: 0,
      });

      console.log('会话初始化完成:', sessionId);
    } catch (error) {
      console.error('初始化会话失败:', error);
      throw error;
    }
  },

  /**
   * 初始化网络监控
   */
  async initNetworkMonitor() {
    try {
      // 获取当前网络状态
      const networkInfo = await wx.getNetworkType();
      this.updateNetworkStatus(networkInfo.networkType);

      // 监听网络状态变化
      wx.onNetworkStatusChange(res => {
        this.updateNetworkStatus(res.networkType);

        if (res.isConnected) {
          console.log('网络已连接:', res.networkType);
          this.setData({ retryCount: 0 }); // 重置重试计数
        } else {
          console.log('网络断开连接');
          this.setData({ networkStatus: 'offline' });
        }
      });
    } catch (error) {
      console.error('初始化网络监控失败:', error);
    }
  },

  /**
   * 更新网络状态
   */
  updateNetworkStatus(networkType) {
    let status = 'online';

    if (networkType === 'none') {
      status = 'offline';
    } else if (networkType === '2g' || networkType === '3g') {
      status = 'slow';
    }

    this.setData({ networkStatus: status });
  },

  /**
   * 初始化聊天
   */
  async initChat() {
    try {
      this.setData({ loading: true });

      // 显示欢迎消息
      const welcomeMessage = {
        id: 'welcome_' + Date.now(),
        type: 'ai',
        content: '你好！我是你的AI学习助手，有什么问题可以随时问我哦～',
        timestamp: Date.now(),
        status: 'sent',
      };

      this.setData({
        messageList: [welcomeMessage],
        loading: false,
      });

      // 滚动到底部
      this.scrollToBottom();
    } catch (error) {
      console.error('初始化聊天失败:', error);
      this.setData({ loading: false });
    }
  },

  /**
   * 加载聊天历史
   */
  async loadChatHistory() {
    try {
      this.setData({ loading: true });

      // TODO: 调用API获取聊天历史
      // const response = await api.getChatHistory();

      // 模拟历史消息
      const historyMessages = [];

      this.setData({
        messageList: [...historyMessages, ...this.data.messageList],
      });
    } catch (error) {
      console.error('加载聊天历史失败:', error);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 输入框内容变化
   */
  onInputChange(e) {
    const { value } = e.detail;
    this.setData({ inputText: value });

    // 隐藏快捷回复
    if (value.trim() && this.data.showQuickReply) {
      this.setData({ showQuickReply: false });
    } else if (!value.trim() && !this.data.showQuickReply) {
      this.setData({ showQuickReply: true });
    }
  },

  /**
   * 输入框获得焦点
   */
  onInputFocus(e) {
    const { height } = e.detail;
    this.setData({
      inputFocus: true,
      inputBottom: height,
      showQuickReply: false,
      showSubjectTabs: false,
    });

    // 延迟滚动到底部
    setTimeout(() => {
      this.scrollToBottom();
    }, 100);
  },

  /**
   * 输入框失去焦点
   */
  onInputBlur() {
    this.setData({
      inputFocus: false,
      inputBottom: 0,
      showQuickReply: true,
      showSubjectTabs: true,
    });
  },

  /**
   * 发送消息
   */
  async sendMessage(customText = '') {
    const content = customText || this.data.inputText.trim();

    if (!content) {
      wx.showToast({
        title: '请输入问题',
        icon: 'none',
      });
      return;
    }

    if (!this.data.canAsk) {
      wx.showToast({
        title: '您没有提问权限',
        icon: 'none',
      });
      return;
    }

    // 检查网络状态
    if (this.data.networkStatus === 'offline') {
      wx.showModal({
        title: '网络异常',
        content: '当前网络不可用，请检查网络连接后重试',
        showCancel: false,
      });
      return;
    }

    try {
      this.setData({ sending: true, retryCount: 0 });

      // 创建用户消息
      const questionType = this.identifyQuestionType(content);
      const userMessage = {
        id: 'user_' + Date.now(),
        type: 'user',
        content: content,
        timestamp: Date.now(),
        status: 'sending',
        questionType: questionType,
        subject: this.data.currentSubject,
      };

      // 更新问题统计和推荐
      this.updateQuestionStats(questionType, this.data.currentSubject);

      // 添加到消息列表
      const messageList = [...this.data.messageList, userMessage];
      this.setData({
        messageList,
        inputText: '',
        showQuickReply: false,
      });

      // 滚动到底部
      this.scrollToBottom();

      // 标记消息为已发送
      userMessage.status = 'sent';
      this.setData({ messageList: [...messageList] });

      // 开始AI回复
      await this.getAIResponse(content);
    } catch (error) {
      console.error('发送消息失败:', error);
      this.showError('发送失败，请重试');
    } finally {
      this.setData({ sending: false });
    }
  },

  /**
   * 获取AI回复
   */
  async getAIResponse(question) {
    try {
      // 显示AI正在输入
      this.setData({ isAITyping: true });

      // 创建AI消息占位符
      const aiMessage = {
        id: 'ai_' + Date.now(),
        type: 'ai',
        content: '',
        timestamp: Date.now(),
        status: 'typing',
      };

      const messageList = [...this.data.messageList, aiMessage];
      this.setData({ messageList });
      this.scrollToBottom();

      // 调用真实的学习问答 API
      try {
        const response = await api.learning.askQuestion({
          question: question,
          session_id: this.data.sessionId,
          subject: this.data.currentSubject !== 'all' ? this.data.currentSubject : undefined,
        });

        if (response.success && response.data) {
          const answerData = response.data;

          // 模拟打字效果显示答案
          await this.typeAIMessage(aiMessage.id, answerData.answer, answerData.question_id);

          // 重置重试计数
          this.setData({ retryCount: 0 });
        } else {
          throw new Error(response.error?.message || 'AI 回复失败');
        }
      } catch (apiError) {
        console.error('AI API调用失败:', apiError);

        // 根据错误类型处理
        if (apiError.code === 'TIMEOUT_ERROR') {
          // 超时错误，提供重试选项
          this.showTimeoutError(aiMessage.id, question);
        } else if (apiError.code === 'NETWORK_ERROR') {
          // 网络错误，根据重试次数决定处理方式
          if (this.data.retryCount < this.data.maxRetryCount) {
            this.showRetryOption(aiMessage.id, question);
          } else {
            throw apiError;
          }
        } else {
          // 其他API错误，显示错误信息
          throw apiError;
        }
      }
    } catch (error) {
      console.error('获取AI回复失败:', error);

      // 显示错误消息
      const errorMessage = {
        id: 'error_' + Date.now(),
        type: 'ai',
        content: this.getErrorMessage(error),
        timestamp: Date.now(),
        status: 'error',
        retryQuestion: question,
      };

      const messageList = this.data.messageList;
      messageList[messageList.length - 1] = errorMessage;
      this.setData({ messageList });
    } finally {
      this.setData({ isAITyping: false });
    }
  },

  /**
   * 处理流式响应
   */
  async handleStreamResponse(messageId, response) {
    let fullContent = '';

    try {
      // 模拟流式数据处理
      for await (const chunk of response.stream) {
        if (!this.data.isAITyping) break;

        const chunkText = chunk.content || chunk.text || '';
        fullContent += chunkText;

        // 实时更新消息内容
        const messageList = this.data.messageList.map(msg => {
          if (msg.id === messageId) {
            return { ...msg, content: fullContent, status: 'typing' };
          }
          return msg;
        });

        this.setData({ messageList });
        this.scrollToBottom();

        // 控制更新频率
        await this.sleep(50);
      }

      // 标记完成
      const messageList = this.data.messageList.map(msg => {
        if (msg.id === messageId) {
          return { ...msg, status: 'sent' };
        }
        return msg;
      });
      this.setData({ messageList });
    } catch (streamError) {
      console.error('流式处理失败:', streamError);
      // 回退到普通处理
      await this.typeAIMessage(messageId, fullContent || '处理中出现错误，请重试');
    }
  },

  /**
   * 获取错误提示信息
   */
  getErrorMessage(error) {
    if (error.code === 'NETWORK_ERROR') {
      return '网络连接失败，请检查网络后重试';
    } else if (error.code === 'TIMEOUT') {
      return '请求超时，请稍后重试';
    } else if (error.code === 'RATE_LIMIT') {
      return '提问太频繁，请稍后再试';
    } else if (error.code === 'AUTH_ERROR') {
      return '认证失败，请重新登录';
    } else {
      return '抱歉，我暂时无法回答，请稍后重试';
    }
  },

  /**
   * 保存对话历史
   */
  async saveChatHistory(question, answer) {
    try {
      await api.saveChatHistory({
        userId: this.data.userInfo?.id,
        sessionId: this.data.sessionId,
        question: question,
        answer: answer,
        subject: this.data.currentSubject,
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('保存对话历史失败:', error);
      // 非关键功能，失败不影响主流程
    }
  },

  /**
   * 获取最近消息历史（用于上下文）
   */
  getRecentMessages() {
    const recentCount = 10; // 只取最近10条消息作为上下文
    const messages = this.data.messageList
      .filter(msg => msg.status === 'sent' && msg.type !== 'system')
      .slice(-recentCount)
      .map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
      }));

    return messages;
  },

  /**
   * 生成模拟AI回复
   */
  generateMockAIResponse(question) {
    const responses = [
      '这是一个很好的问题！让我来为你详细解答：\n\n首先，我们需要理解题目的关键信息...',
      '根据你提出的问题，我建议从以下几个方面来理解：\n\n1. 基本概念\n2. 解题思路\n3. 注意事项',
      '这道题考查的是重要知识点，让我一步步为你分析：\n\n第一步：明确已知条件\n第二步：确定求解目标\n第三步：选择合适方法',
      '很棒的思考！这个概念可以这样理解：\n\n简单来说，就是...\n\n具体应用时需要注意...',
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  },

  /**
   * AI打字效果
   */
  async typeAIMessage(messageId, fullContent) {
    const chars = fullContent.split('');
    let currentContent = '';

    for (let i = 0; i < chars.length; i++) {
      if (!this.data.isAITyping) break; // 如果页面隐藏则停止

      currentContent += chars[i];

      // 更新消息内容
      const messageList = this.data.messageList.map(msg => {
        if (msg.id === messageId) {
          return { ...msg, content: currentContent, status: 'typing' };
        }
        return msg;
      });

      this.setData({ messageList });

      // 控制打字速度
      if (chars[i] === '\n') {
        await this.sleep(200); // 换行稍微慢一点
      } else {
        await this.sleep(30); // 正常字符
      }

      // 定期滚动到底部
      if (i % 10 === 0) {
        this.scrollToBottom();
      }
    }

    // 标记为完成
    const messageList = this.data.messageList.map(msg => {
      if (msg.id === messageId) {
        return { ...msg, content: fullContent, status: 'sent' };
      }
      return msg;
    });

    this.setData({ messageList });
    this.scrollToBottom();
  },

  /**
   * 停止AI输入效果
   */
  stopAITyping() {
    this.setData({ isAITyping: false });
  },

  /**
   * 重试发送消息
   */
  async retryMessage(messageId) {
    const message = this.data.messageList.find(msg => msg.id === messageId);
    if (!message || message.type !== 'user') return;

    // 检查重试次数
    if (this.data.retryCount >= this.data.maxRetryCount) {
      wx.showModal({
        title: '发送失败',
        content: '重试次数过多，请稍后再试',
        showCancel: false,
      });
      return;
    }

    this.setData({ retryCount: this.data.retryCount + 1 });

    // 重新发送
    await this.getAIResponse(message.content);
  },

  /**
   * 删除消息
   */
  deleteMessage(messageId) {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条消息吗？',
      success: res => {
        if (res.confirm) {
          const messageList = this.data.messageList.filter(msg => msg.id !== messageId);
          this.setData({ messageList });
        }
      },
    });
  },

  /**
   * 复制消息内容
   */
  copyMessage(content) {
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
   * 检查消息长度限制
   */
  checkMessageLength(content) {
    const maxLength = 2000; // 最大字符数限制

    if (content.length > maxLength) {
      wx.showModal({
        title: '内容过长',
        content: `消息长度不能超过${maxLength}个字符，当前${content.length}个字符`,
        showCancel: false,
      });
      return false;
    }

    return true;
  },

  /**
   * 处理网络超时
   */
  async handleNetworkTimeout(retryCallback) {
    const timeoutDuration = this.data.networkStatus === 'slow' ? 30000 : 15000; // 慢网络延长超时时间

    return Promise.race([
      retryCallback(),
      new Promise((_, reject) => {
        setTimeout(() => {
          reject(new Error('TIMEOUT'));
        }, timeoutDuration);
      }),
    ]);
  },

  /**
   * 延迟函数
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * 快捷回复点击
   */
  onQuickReplyTap(e) {
    const { text } = e.currentTarget.dataset;
    this.setData({ inputText: text });
    this.sendMessage(text);
  },

  /**
   * 学科切换
   */
  onSubjectTap(e) {
    const { subject } = e.currentTarget.dataset;
    this.switchSubject(subject);
  },

  /**
   * 切换学科
   */
  switchSubject(subjectId) {
    const subjects = this.data.subjects.map(item => ({
      ...item,
      active: item.id === subjectId,
    }));

    this.setData({
      subjects,
      currentSubject: subjectId,
    });

    // 更新快捷回复为学科专业模板
    this.updateQuickRepliesForSubject(subjectId);

    // 加载学科相关推荐问题
    this.loadSubjectRecommendations(subjectId);

    // 发送学科切换消息
    const subjectName = subjects.find(s => s.id === subjectId)?.name || '全部';
    wx.showToast({
      title: `切换到${subjectName}模式`,
      icon: 'none',
      duration: 1500,
    });

    // 统计学科使用情况
    this.updateSubjectStats(subjectId);
  },

  /**
   * 更新快捷回复为学科专业模板
   */
  updateQuickRepliesForSubject(subjectId) {
    let quickReplies = [];

    if (subjectId === 'all' || !this.data.subjectTemplates[subjectId]) {
      // 使用通用模板
      quickReplies = [
        '这道题怎么做？',
        '解释一下这个概念',
        '给我出几道练习题',
        '总结一下重点',
        '有什么学习建议吗？',
      ];
    } else {
      // 使用学科专业模板
      quickReplies = this.data.subjectTemplates[subjectId];
    }

    this.setData({ quickReplies });
  },

  /**
   * 加载学科相关推荐问题
   */
  async loadSubjectRecommendations(subjectId) {
    try {
      // TODO: 调用API获取学科推荐问题
      // const recommendations = await api.getSubjectRecommendations(subjectId);

      // 模拟智能推荐
      const mockRecommendations = this.generateSubjectRecommendations(subjectId);

      this.setData({ recommendedQuestions: mockRecommendations });
    } catch (error) {
      console.error('加载学科推荐失败:', error);
    }
  },

  /**
   * 生成学科推荐问题
   */
  generateSubjectRecommendations(subjectId) {
    const allRecommendations = {
      math: [
        { question: '二次函数的图像性质', type: 'concept', difficulty: 'medium' },
        { question: '如何解一元二次方程？', type: 'method', difficulty: 'easy' },
        { question: '三角函数的应用场景', type: 'application', difficulty: 'hard' },
      ],
      chinese: [
        { question: '古诗词鉴赏技巧', type: 'skill', difficulty: 'medium' },
        { question: '议论文写作方法', type: 'writing', difficulty: 'medium' },
        { question: '文言文翻译技巧', type: 'translation', difficulty: 'hard' },
      ],
      english: [
        { question: 'Common English grammar mistakes', type: 'grammar', difficulty: 'medium' },
        { question: 'How to improve vocabulary?', type: 'vocabulary', difficulty: 'easy' },
        { question: 'English writing techniques', type: 'writing', difficulty: 'hard' },
      ],
      physics: [
        { question: '牛顿运动定律的应用', type: 'law', difficulty: 'medium' },
        { question: '电路分析方法', type: 'analysis', difficulty: 'hard' },
        { question: '能量守恒定律实例', type: 'example', difficulty: 'easy' },
      ],
      chemistry: [
        { question: '化学平衡原理', type: 'principle', difficulty: 'hard' },
        { question: '有机化学反应类型', type: 'reaction', difficulty: 'medium' },
        { question: '元素周期表规律', type: 'pattern', difficulty: 'easy' },
      ],
    };

    if (subjectId === 'all') {
      // 混合推荐
      const mixed = [];
      Object.values(allRecommendations).forEach(subjects => {
        mixed.push(...subjects.slice(0, 1));
      });
      return mixed;
    }

    return allRecommendations[subjectId] || [];
  },

  /**
   * 更新学科统计
   */
  updateSubjectStats(subjectId) {
    const stats = { ...this.data.questionStats };

    if (!stats.bySubject[subjectId]) {
      stats.bySubject[subjectId] = 0;
    }
    stats.bySubject[subjectId]++;

    this.setData({ questionStats: stats });
  },

  /**
   * 加载推荐问题
   */
  async loadRecommendedQuestions() {
    try {
      // TODO: 调用API获取个性化推荐
      // const recommendations = await api.getPersonalizedRecommendations({
      //   userId: this.data.userInfo?.id,
      //   userRole: this.data.userRole,
      //   recentTopics: this.data.questionStats.recentTopics
      // });

      // 模拟个性化推荐
      const mockRecommendations = [
        { question: '今天的数学作业有疑问吗？', type: 'homework', priority: 'high' },
        { question: '需要复习昨天学的知识点吗？', type: 'review', priority: 'medium' },
        { question: '想了解一些有趣的科学知识吗？', type: 'explore', priority: 'low' },
      ];

      this.setData({ recommendedQuestions: mockRecommendations });
    } catch (error) {
      console.error('加载推荐问题失败:', error);
    }
  },

  /**
   * 问题类型智能识别
   */
  identifyQuestionType(question) {
    const patterns = {
      homework: /作业|练习|题目|解题/,
      concept: /概念|定义|原理|什么是/,
      method: /怎么|如何|方法|步骤/,
      example: /例子|举例|案例|实例/,
      review: /复习|总结|回顾|梳理/,
      explore: /拓展|延伸|更多|深入/,
    };

    for (const [type, pattern] of Object.entries(patterns)) {
      if (pattern.test(question)) {
        return type;
      }
    }

    return 'general';
  },

  /**
   * 更新问题统计
   */
  updateQuestionStats(questionType, subject) {
    const stats = { ...this.data.questionStats };

    // 更新总数
    stats.total++;

    // 更新学科统计
    if (!stats.bySubject[subject]) {
      stats.bySubject[subject] = 0;
    }
    stats.bySubject[subject]++;

    // 更新最近话题
    stats.recentTopics.unshift({
      type: questionType,
      subject: subject,
      timestamp: Date.now(),
    });

    // 只保留最近10个话题
    if (stats.recentTopics.length > 10) {
      stats.recentTopics = stats.recentTopics.slice(0, 10);
    }

    this.setData({ questionStats: stats });

    // 根据统计更新推荐
    this.updateRecommendationsBasedOnStats();
  },

  /**
   * 基于统计更新推荐
   */
  async updateRecommendationsBasedOnStats() {
    const stats = this.data.questionStats;
    const recentTypes = stats.recentTopics.map(t => t.type);
    const currentSubject = this.data.currentSubject;

    // 生成智能推荐
    const recommendations = [];

    // 基于最近提问类型推荐
    if (recentTypes.includes('homework')) {
      recommendations.push({
        question: '需要更多练习题吗？',
        type: 'practice',
        priority: 'high',
        reason: '基于您最近的作业问题',
      });
    }

    if (recentTypes.includes('concept')) {
      recommendations.push({
        question: '想了解相关的实际应用吗？',
        type: 'application',
        priority: 'medium',
        reason: '基于您对概念的兴趣',
      });
    }

    // 基于学科推荐深度学习内容
    if (currentSubject !== 'all') {
      const subjectName = this.data.subjects.find(s => s.id === currentSubject)?.name;
      recommendations.push({
        question: `${subjectName}还有哪些有趣的知识点？`,
        type: 'explore',
        priority: 'low',
        reason: `基于您对${subjectName}的关注`,
      });
    }

    this.setData({ recommendedQuestions: recommendations });
  },

  /**
   * 获取推荐问题点击处理
   */
  onRecommendedQuestionTap(e) {
    const { question } = e.currentTarget.dataset;
    this.setData({ inputText: question });
    this.sendMessage(question);
  },

  /**
   * 显示问题分类帮助
   */
  showQuestionTypeHelp() {
    wx.showModal({
      title: '问题分类帮助',
      content:
        '我可以帮您回答：\n• 作业和练习题解答\n• 概念和原理解释\n• 学习方法指导\n• 知识点总结复习\n• 拓展知识探索',
      showCancel: false,
    });
  },

  /**
   * 开始录音
   */
  startRecord() {
    if (!this.data.canAsk) {
      wx.showToast({
        title: '您没有语音提问权限',
        icon: 'none',
      });
      return;
    }

    this.setData({ recordStatus: 'recording' });

    wx.startRecord({
      success: res => {
        this.setData({ recordStatus: 'uploading' });
        this.uploadAudio(res.tempFilePath);
      },
      fail: error => {
        console.error('录音失败:', error);
        this.setData({ recordStatus: 'idle' });
        this.showError('录音失败');
      },
    });
  },

  /**
   * 停止录音
   */
  stopRecord() {
    wx.stopRecord();
    this.setData({ recordStatus: 'idle' });
  },

  /**
   * 上传音频
   */
  async uploadAudio(audioPath) {
    try {
      // TODO: 实现音频上传和语音识别
      // const result = await api.speechToText(audioPath);

      // 模拟语音识别结果
      await this.sleep(1000);
      const mockText = '这道数学题怎么解？';

      this.setData({
        inputText: mockText,
        recordStatus: 'idle',
      });

      wx.showToast({
        title: '语音识别完成',
        icon: 'success',
      });
    } catch (error) {
      console.error('音频上传失败:', error);
      this.setData({ recordStatus: 'idle' });
      this.showError('语音识别失败');
    }
  },

  /**
   * 显示超时错误
   */
  showTimeoutError(messageId, question) {
    const errorMessage = {
      id: messageId,
      type: 'ai',
      content: '请求超时，网络可能较慢',
      timestamp: Date.now(),
      status: 'timeout',
      retryData: { question },
    };

    const messageList = this.data.messageList.map(msg =>
      msg.id === messageId ? errorMessage : msg,
    );

    this.setData({ messageList });
  },

  /**
   * 显示重试选项
   */
  showRetryOption(messageId, question) {
    const retryMessage = {
      id: messageId,
      type: 'ai',
      content: '网络请求失败，请点击重试',
      timestamp: Date.now(),
      status: 'retry',
      retryData: { question },
    };

    const messageList = this.data.messageList.map(msg =>
      msg.id === messageId ? retryMessage : msg,
    );

    this.setData({ messageList });
  },

  /**
   * 处理消息重试
   */
  async onMessageRetry(e) {
    const { messageId } = e.currentTarget.dataset;
    const message = this.data.messageList.find(msg => msg.id === messageId);

    if (message && message.retryData) {
      // 更新消息状态为重试中
      const messageList = this.data.messageList.map(msg => {
        if (msg.id === messageId) {
          return { ...msg, content: '正在重试...', status: 'typing' };
        }
        return msg;
      });

      this.setData({ messageList });

      // 重新发送请求
      await this.getAIResponse(message.retryData.question);
    }
  },

  /**
   * 滚动到底部
   */
  scrollToBottom() {
    const query = wx.createSelectorQuery();
    query.select('#message-list').boundingClientRect();
    query.selectViewport().scrollOffset();
    query.exec(res => {
      if (res[0] && res[1]) {
        const { height } = res[0];
        const { scrollHeight } = res[1];

        wx.pageScrollTo({
          scrollTop: scrollHeight + height,
          duration: 300,
        });
      }
    });
  },

  /**
   * 消息长按
   */
  onMessageLongPress(e) {
    const { message } = e.currentTarget.dataset;

    const options = ['复制'];
    if (message.type === 'ai') {
      options.push('收藏', '分享');
    }

    wx.showActionSheet({
      itemList: options,
      success: res => {
        switch (res.tapIndex) {
          case 0: // 复制
            wx.setClipboardData({
              data: message.content,
              success: () => {
                wx.showToast({
                  title: '复制成功',
                  icon: 'success',
                });
              },
            });
            break;
          case 1: // 收藏
            this.collectMessage(message);
            break;
          case 2: // 分享
            this.shareMessage(message);
            break;
        }
      },
    });
  },

  /**
   * 收藏消息
   */
  async collectMessage(message) {
    try {
      // TODO: 调用收藏API
      // await api.collectMessage(message);

      wx.showToast({
        title: '收藏成功',
        icon: 'success',
      });
    } catch (error) {
      console.error('收藏失败:', error);
      this.showError('收藏失败');
    }
  },

  /**
   * 分享消息
   */
  shareMessage(message) {
    wx.showShareMenu({
      withShareTicket: true,
    });
  },

  /**
   * 跳转到历史记录
   */
  async onGoToHistory() {
    try {
      // 加载会话列表
      const response = await api.learning.getSessions({
        page: 1,
        size: 20,
        status: 'active',
      });

      if (response.success && response.data) {
        // 导航到历史记录页面
        wx.navigateTo({
          url: '/pages/chat/history/index',
        });
      } else {
        wx.navigateTo({
          url: '/pages/chat/history/index',
        });
      }
    } catch (error) {
      console.error('加载历史记录失败:', error);
      wx.navigateTo({
        url: '/pages/chat/history/index',
      });
    }
  },

  /**
   * 跳转到收藏夹
   */
  onGoToCollection() {
    wx.navigateTo({
      url: '/pages/chat/collection/index',
    });
  },

  /**
   * 清空对话
   */
  onClearChat() {
    wx.showModal({
      title: '确认清空',
      content: '确定要清空当前对话吗？',
      success: res => {
        if (res.confirm) {
          this.setData({
            messageList: [],
          });
          this.initChat();
        }
      },
    });
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

  /**
   * 获取最近消息（用于AI上下文）
   */
  getRecentMessages() {
    return this.data.messageList
      .slice(-10) // 最近10条消息
      .map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content,
      }));
  },

  /**
   * 格式化时间
   */
  formatTime(timestamp) {
    return utils.formatTime(new Date(timestamp));
  },
});

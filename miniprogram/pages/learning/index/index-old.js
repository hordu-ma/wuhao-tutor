// pages/chat/index/index.js - AI问答对话页面

const { routeGuard } = require('../../../utils/route-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');
const api = require('../../../utils/api.js');
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
      '有什么学习建议吗？'
    ],
    
    // 学科分类
    subjects: [
      { id: 'all', name: '全部', icon: 'apps-o', active: true },
      { id: 'math', name: '数学', icon: 'balance-o', active: false },
      { id: 'chinese', name: '语文', icon: 'bookmark-o', active: false },
      { id: 'english', name: '英语', icon: 'chat-o', active: false },
      { id: 'physics', name: '物理', icon: 'fire-o', active: false },
      { id: 'chemistry', name: '化学', icon: 'fire-o', active: false }
    ],
    
    // 当前选中学科
    currentSubject: 'all',
    
    // 页面配置
    showScrollToBottom: false, // 显示滚动到底部按钮
    
    // 权限状态
    canAsk: false,
    canView: false,
    canModerate: false,
    
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
              url: '/pages/index/index'
            });
          }
        });
        return;
      }

      await this.initUserInfo();
      await this.initPermissions();
      await this.initChat();
      
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
      imageUrl: '/assets/images/share-chat.png'
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
      const permissions = await permissionManager.getPagePermissions('pages/chat/index/index', userRole);
      
      this.setData({
        canAsk: permissions.canAsk || userRole === 'student',
        canView: permissions.canView || true,
        canModerate: permissions.canModerate || userRole === 'teacher'
      });
    } catch (error) {
      console.error('初始化权限失败:', error);
    }
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
        status: 'sent'
      };
      
      this.setData({
        messageList: [welcomeMessage],
        loading: false
      });
      
      // 滚动到底部
      this.scrollToBottom();
      
    } catch (error) {
      console.error('初始化聊天失败:', error);
      this.setData({ loading: false });
    }
  },

    await this.initPage();
  },

  /**
   * 生命周期函数--监听页面显示
   */
  async onShow() {
    console.log('问答页面显示');
    
    // 再次检查登录状态
    const isLoggedIn = await authManager.isLoggedIn();
    if (!isLoggedIn) {
      routeGuard.redirectToLogin();
      return;
    }
  },

  /**
   * 初始化页面
   */
  async initPage() {
    try {
      this.setData({ loading: true });

      // 获取用户信息
      const [userInfo, userRole] = await Promise.all([
        authManager.getUserInfo(),
        authManager.getUserRole()
      ]);

      this.setData({
        userInfo,
        userRole
      });

      // 检查用户权限
      await this.checkUserPermissions();

      // 加载聊天记录
      await this.loadChatHistory();

    } catch (error) {
      console.error('初始化页面失败:', error);
      wx.showToast({
        title: '页面加载失败',
        icon: 'error'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 检查用户权限
   */
  async checkUserPermissions() {
    try {
      const canAsk = await permissionManager.hasPermission('chat.ask');
      const canView = await permissionManager.hasPermission('chat.view');
      const canModerate = await permissionManager.hasPermission('chat.moderate');

      this.setData({
        canAsk,
        canView,
        canModerate
      });

      console.log('聊天权限检查结果', {
        canAsk, canView, canModerate
      });

      // 如果连查看权限都没有，禁止访问
      if (!canView) {
        wx.showModal({
          title: '权限不足',
          content: '您没有查看对话的权限',
          showCancel: false,
          success: () => {
            wx.switchTab({
              url: '/pages/index/index'
            });
          }
        });
        return false;
      }

      return true;
    } catch (error) {
      console.error('检查用户权限失败', error);
      return false;
    }
  },

  /**
   * 加载聊天记录
   */
  async loadChatHistory() {
    try {
      // TODO: 实现聊天记录加载
      console.log('加载聊天记录');
      
      // 模拟数据
      this.setData({
        chatList: [
          {
            id: 1,
            type: 'user',
            content: '你好，我想问一道数学题',
            time: '10:30'
          },
          {
            id: 2,
            type: 'ai',
            content: '你好！我是你的AI学习助手，很高兴为你解答数学问题。请把题目发给我吧！',
            time: '10:30'
          }
        ]
      });
    } catch (error) {
      console.error('加载聊天记录失败:', error);
    }
  },

  /**
   * 发送消息
   */
  async onSendMessage() {
    const content = this.data.messageContent.trim();
    if (!content) {
      wx.showToast({
        title: '请输入消息内容',
        icon: 'none'
      });
      return;
    }

    // 检查发送权限
    const canAsk = await permissionManager.hasPermission('chat.ask');
    if (!canAsk) {
      wx.showToast({
        title: '您没有发送消息的权限',
        icon: 'none'
      });
      return;
    }

    // 检查时间限制
    const timeValid = permissionManager.checkTimeRestriction('06:00-23:00');
    if (!timeValid) {
      wx.showToast({
        title: 'AI问答时间限制：06:00-23:00',
        icon: 'none'
      });
      return;
    }

    if (this.data.sending) {
      return;
    }

    try {
      this.setData({ sending: true });

      // 添加用户消息到聊天列表
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: content,
        time: new Date().toLocaleTimeString().slice(0, 5)
      };

      this.setData({
        chatList: [...this.data.chatList, userMessage],
        messageContent: ''
      });

      // TODO: 调用AI接口获取回复
      setTimeout(() => {
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: '这是AI的回复示例，实际需要调用后端API。',
          time: new Date().toLocaleTimeString().slice(0, 5)
        };

        this.setData({
          chatList: [...this.data.chatList, aiMessage]
        });
      }, 1000);

    } catch (error) {
      console.error('发送消息失败:', error);
      wx.showToast({
        title: '发送失败，请重试',
        icon: 'error'
      });
    } finally {
      this.setData({ sending: false });
    }
  },

  /**
   * 输入框内容变化
   */
  onInputChange(e) {
    this.setData({
      messageContent: e.detail.value
    });
  },

  /**
   * 页面下拉刷新
   */
  async onPullDownRefresh() {
    await this.loadChatHistory();
    wx.stopPullDownRefresh();
  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    return {
      title: '五好伴学 - AI问答助手',
      path: '/pages/chat/index/index'
    };
  }
});
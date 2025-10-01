// pages/chat/index/index.js - 问答页面

const { routeGuard } = require('../../../utils/route-guard.js');
const { authManager } = require('../../../utils/auth.js');
const { permissionManager } = require('../../../utils/permission-manager.js');
const { roleManager } = require('../../../utils/role-manager.js');

Page({
  data: {
    userInfo: null,
    userRole: '',
    chatList: [],
    loading: true,
    messageContent: '',
    sending: false,
    
    // 权限状态
    canAsk: false,
    canView: false,
    canModerate: false
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('问答页面加载', options);

    // 执行路由守卫检查
    const guardResult = await routeGuard.checkPageAuth();
    if (!guardResult.success) {
      // 路由守卫失败，页面不应该继续加载
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
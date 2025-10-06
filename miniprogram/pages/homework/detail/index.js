// pages/homework/detail/index.js - 作业详情页面

const { authManager } = require('../../../utils/auth.js');
const api = require('../../../api/index.js');
const utils = require('../../../utils/utils.js');

Page({
  /**
   * 页面的初始数据
   */
  data: {
    // 作业详情
    homework: null,

    // 用户信息
    userInfo: null,
    userRole: '',

    // 加载状态
    loading: true,

    // 提交详情（包含批改状态）
    submission: null,
    hasSubmission: false,

    // 批改结果
    correction: null,
    hasCorrection: false,

    // 批改状态轮询
    isPolling: false,
    pollingTimer: null,

    // 权限控制
    canSubmit: false,
    canCorrect: false,
    canEdit: false,

    // 附件列表
    attachments: [],

    // 错误状态
    error: null,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('作业详情页面加载', options);

    if (!options.id) {
      this.showError('作业ID不能为空');
      return;
    }

    try {
      await this.initUserInfo();
      await this.loadHomeworkDetail(options.id);
    } catch (error) {
      console.error('页面初始化失败:', error);
      this.showError('页面加载失败');
    }
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 检查是否需要刷新数据
    const pages = getCurrentPages();
    const currentPage = pages[pages.length - 1];

    if (currentPage.data.needRefresh) {
      this.refreshData();
      this.setData({ needRefresh: false });
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
   * 用户点击右上角分享
   */
  onShareAppMessage() {
    const { homework } = this.data;
    return {
      title: `作业：${homework?.title || '详情'}`,
      path: `/pages/homework/detail/index?id=${homework?.id}`,
      imageUrl: '/assets/images/share-homework.png',
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();
      const userRole = await authManager.getUserRole();

      this.setData({
        userInfo,
        userRole,
        canSubmit: userRole === 'student',
        canCorrect: userRole === 'teacher',
        canEdit: userRole === 'teacher',
      });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 加载作业详情
   */
  async loadHomeworkDetail(homeworkId) {
    try {
      this.setData({ loading: true, error: null });

      // 调用API获取作业提交详情
      const response = await api.homework.getSubmissionDetail(homeworkId);

      if (response.success && response.data) {
        const submission = response.data;

        this.setData({
          submission,
          hasSubmission: true,
        });

        // 如果批改正在进行中，启动轮询
        if (submission.status === 'processing' || submission.status === 'pending') {
          this.startPolling(homeworkId);
        } else if (submission.status === 'completed') {
          // 批改已完成，加载批改结果
          await this.loadCorrection(homeworkId);
        }
      } else {
        throw new Error(response.message || '加载作业详情失败');
      }
    } catch (error) {
      console.error('加载作业详情失败:', error);
      this.setData({ error: error.message || '加载失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 开始轮询批改状态
   */
  startPolling(submissionId) {
    if (this.data.isPolling) return;

    console.log('开始轮询批改状态:', submissionId);
    this.setData({ isPolling: true });

    const poll = async () => {
      try {
        const response = await api.homework.getSubmissionDetail(submissionId);

        if (response.success && response.data) {
          const submission = response.data;
          this.setData({ submission });

          if (submission.status === 'completed') {
            // 批改完成，加载批改结果
            console.log('批改完成，加载批改结果');
            await this.loadCorrection(submissionId);
            this.stopPolling();

            wx.showToast({
              title: '批改完成',
              icon: 'success',
            });
          } else if (submission.status === 'failed') {
            // 批改失败
            console.log('批改失败');
            this.stopPolling();

            wx.showToast({
              title: '批改失败，请重试',
              icon: 'error',
            });
          } else {
            // 继续轮询
            this.data.pollingTimer = setTimeout(poll, 3000);
          }
        }
      } catch (error) {
        console.error('轮询批改状态失败:', error);
        // 继续轮询
        this.data.pollingTimer = setTimeout(poll, 3000);
      }
    };

    // 开始轮询
    poll();
  },

  /**
   * 停止轮询
   */
  stopPolling() {
    console.log('停止轮询批改状态');

    if (this.data.pollingTimer) {
      clearTimeout(this.data.pollingTimer);
      this.setData({
        pollingTimer: null,
        isPolling: false,
      });
    }
  },

  /**
   * 加载批改结果
   */
  async loadCorrection(submissionId) {
    try {
      const response = await homeworkAPI.getCorrectionResult(submissionId);

      if (response.success && response.data) {
        this.setData({
          correction: response.data,
          hasCorrection: true,
        });
      } else {
        console.log('暂无批改结果:', response.message);
      }
    } catch (error) {
      console.error('加载批改结果失败:', error);
      // 批改结果可能还未生成，不显示错误
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    const { submission } = this.data;
    if (submission?.id) {
      await this.loadHomeworkDetail(submission.id);
    }
  },

  /**
   * 页面卸载时清理轮询
   */
  onUnload() {
    this.stopPolling();
  },

  /**
   * 页面隐藏时停止轮询
   */
  onHide() {
    this.stopPolling();
  },

  /**
   * 重新提交作业
   */
  onResubmitHomework() {
    const { submission } = this.data;

    wx.showModal({
      title: '重新提交',
      content: '确定要重新提交作业吗？',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: `/pages/homework/submit/index?homeworkId=${submission.template_id || submission.homework_id}`,
          });
        }
      },
    });
  },

  /**
   * 查看原始图片
   */
  onViewOriginalImage() {
    const { submission } = this.data;
    if (!submission || !submission.file_url) return;

    wx.previewImage({
      current: submission.file_url,
      urls: [submission.file_url],
    });
  },

  /**
   * 手动刷新批改结果
   */
  async onRefreshCorrection() {
    const { submission } = this.data;

    if (submission.status === 'processing' || submission.status === 'pending') {
      wx.showToast({
        title: '批改进行中，请稍候...',
        icon: 'loading',
        duration: 2000,
      });

      // 重新启动轮询
      this.stopPolling();
      this.startPolling(submission.id);
    } else if (submission.status === 'completed') {
      // 重新加载批改结果
      await this.loadCorrection(submission.id);

      wx.showToast({
        title: '刷新成功',
        icon: 'success',
      });
    }
  },

  /**
   * 返回作业列表
   */
  onBackToList() {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        wx.switchTab({
          url: '/pages/homework/list/index',
        });
      },
    });
  },

  /**
   * 分享批改结果
   */
  onShareResult() {
    const { correction } = this.data;

    if (!correction) {
      wx.showToast({
        title: '暂无批改结果',
        icon: 'none',
      });
      return;
    }

    // 生成分享图片或跳转到分享页面
    wx.showToast({
      title: '分享功能开发中',
      icon: 'none',
    });
  },

  /**
   * 获取批改状态文本
   */
  getStatusText(status) {
    const statusMap = {
      pending: '等待批改',
      processing: '批改中',
      completed: '已完成',
      failed: '批改失败',
    };
    return statusMap[status] || '未知状态';
  },

  /**
   * 获取批改状态颜色
   */
  getStatusColor(status) {
    const colorMap = {
      pending: '#faad14',
      processing: '#1890ff',
      completed: '#52c41a',
      failed: '#f5222d',
    };
    return colorMap[status] || '#999999';
  },

  /**
   * 格式化分数显示
   */
  formatScore(score, maxScore) {
    if (score === undefined || score === null) return '-';
    return `${score}/${maxScore || 100}`;
  },

  /**
   * 获取等级
   */
  getGrade(score, maxScore = 100) {
    const percentage = (score / maxScore) * 100;

    if (percentage >= 90) return 'A';
    if (percentage >= 80) return 'B';
    if (percentage >= 70) return 'C';
    if (percentage >= 60) return 'D';
    return 'E';
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
   * 格式化时间
   */
  formatTime(timeString) {
    return utils.formatTime(new Date(timeString));
  },

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
});

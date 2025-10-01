// pages/homework/detail/index.js - 作业详情页面

const { authManager } = require('../../../utils/auth.js');
const api = require('../../../utils/api.js');
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

    // 提交状态
    submission: null,
    hasSubmission: false,

    // 批改结果
    correction: null,
    hasCorrection: false,

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

      // TODO: 调用API获取作业详情
      // const response = await api.getHomeworkDetail(homeworkId);

      // 模拟数据
      const homework = {
        id: homeworkId,
        title: '数学第三章函数练习',
        subject: '数学',
        description: '完成课本第45-50页的练习题，重点掌握二次函数的图像和性质。',
        requirements: [
          '独立完成所有题目',
          '写出详细的解题步骤',
          '对于错题要标注原因',
          '字迹工整，格式规范',
        ],
        difficulty: 'medium',
        totalScore: 100,
        deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        teacherName: '李老师',
        teacherId: 'teacher_001',
        attachments: [
          {
            id: 'att_001',
            name: '练习题参考答案.pdf',
            url: '/files/answer_reference.pdf',
            size: '2.5MB',
            type: 'pdf',
          },
        ],
        status: 'pending', // pending, submitted, corrected, overdue
        submissionCount: 0,
        totalStudents: 30,
      };

      this.setData({ homework });

      // 加载提交记录和批改结果
      await Promise.all([this.loadSubmission(homeworkId), this.loadCorrection(homeworkId)]);
    } catch (error) {
      console.error('加载作业详情失败:', error);
      this.setData({ error: '加载失败，请重试' });
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载提交记录
   */
  async loadSubmission(homeworkId) {
    try {
      if (this.data.userRole !== 'student') return;

      // TODO: 调用API获取提交记录
      // const response = await api.getHomeworkSubmission(homeworkId);

      // 模拟数据
      const submission = {
        id: 'sub_001',
        homeworkId: homeworkId,
        studentId: this.data.userInfo?.id,
        content: '我的作业答案...',
        attachments: [
          {
            id: 'img_001',
            name: '作业答案1.jpg',
            url: '/images/homework_1.jpg',
            type: 'image',
          },
        ],
        submittedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'submitted', // submitted, corrected
      };

      this.setData({
        submission,
        hasSubmission: true,
      });
    } catch (error) {
      console.error('加载提交记录失败:', error);
    }
  },

  /**
   * 加载批改结果
   */
  async loadCorrection(homeworkId) {
    try {
      // TODO: 调用API获取批改结果
      // const response = await api.getHomeworkCorrection(homeworkId);

      // 模拟数据
      const correction = {
        id: 'cor_001',
        homeworkId: homeworkId,
        teacherId: 'teacher_001',
        score: 85,
        totalScore: 100,
        grade: 'B',
        comment: '整体完成得不错，解题思路清晰。第3题的计算有小错误，需要注意细心。继续保持！',
        corrections: [
          {
            questionNo: 3,
            isCorrect: false,
            comment: '计算错误：应该是x²+2x-3，你写成了x²+2x-2',
            score: 8,
            totalScore: 10,
          },
        ],
        correctedAt: new Date(Date.now() - 0.5 * 24 * 60 * 60 * 1000).toISOString(),
      };

      this.setData({
        correction,
        hasCorrection: true,
      });
    } catch (error) {
      console.error('加载批改结果失败:', error);
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    const { homework } = this.data;
    if (homework?.id) {
      await this.loadHomeworkDetail(homework.id);
    }
  },

  /**
   * 提交作业
   */
  onSubmitHomework() {
    const { homework } = this.data;
    wx.navigateTo({
      url: `/pages/homework/submit/index?homeworkId=${homework.id}`,
    });
  },

  /**
   * 查看提交详情
   */
  onViewSubmission() {
    const { submission } = this.data;
    if (!submission) return;

    // 显示提交详情
    wx.navigateTo({
      url: `/pages/homework/submission/detail?id=${submission.id}`,
    });
  },

  /**
   * 编辑作业
   */
  onEditHomework() {
    const { homework } = this.data;
    wx.navigateTo({
      url: `/pages/homework/edit/index?id=${homework.id}`,
    });
  },

  /**
   * 批改作业
   */
  onCorrectHomework() {
    const { homework } = this.data;
    wx.navigateTo({
      url: `/pages/homework/correct/index?id=${homework.id}`,
    });
  },

  /**
   * 下载附件
   */
  onDownloadAttachment(e) {
    const { attachment } = e.currentTarget.dataset;

    wx.showLoading({ title: '下载中...' });

    wx.downloadFile({
      url: attachment.url,
      success: res => {
        wx.hideLoading();
        if (res.statusCode === 200) {
          wx.openDocument({
            filePath: res.tempFilePath,
            showMenu: true,
          });
        }
      },
      fail: error => {
        wx.hideLoading();
        console.error('下载失败:', error);
        wx.showToast({
          title: '下载失败',
          icon: 'error',
        });
      },
    });
  },

  /**
   * 预览图片
   */
  onPreviewImage(e) {
    const { url, urls } = e.currentTarget.dataset;

    wx.previewImage({
      current: url,
      urls: urls || [url],
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

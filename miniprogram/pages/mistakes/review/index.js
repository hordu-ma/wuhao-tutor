// pages/mistakes/review/index.js - 三阶段递进式复习页面
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../api/mistakes.js');

const pageObject = {
  /**
   * 页面的初始数据
   */
  data: {
    // 会话信息
    sessionId: '',
    mistakeId: '',

    // 复习状态
    currentStage: 1,
    stageName: '原题复习',
    status: 'in_progress', // in_progress | completed_success | completed_fail

    // 题目信息
    questionContent: '',
    correctAnswer: '',
    knowledgePoints: [],
    // 🎯 [Phase 1] 新增：原题图片
    imageUrls: [],
    hasImages: false,

    // 用户答案
    userAnswer: '',

    // 加载状态
    loading: true,
    submitting: false,

    // 阶段进度
    stageSteps: [
      { text: '原题复习', desc: '验证基础掌握' },
      { text: '变体题挑战', desc: '测试知识迁移' },
      { text: '知识点巩固', desc: '深化理解' },
    ],

    // 结果展示
    showResult: false,
    resultData: null,

    // 结果弹窗
    showResultDialog: false,
    resultDialogBtn: '',
    resultDialogCancelBtn: '',
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('复习页面加载', options);

    const { session_id, mistake_id } = options;

    if (!session_id || !mistake_id) {
      wx.showToast({
        title: '参数错误',
        icon: 'none',
        duration: 2000,
      });
      setTimeout(() => {
        wx.navigateBack();
      }, 2000);
      return;
    }

    this.setData({
      sessionId: session_id,
      mistakeId: mistake_id,
    });

    // 加载复习会话信息
    await this.loadReviewSession();
  },

  /**
   * 加载复习会话信息
   */
  async loadReviewSession() {
    try {
      this.setData({ loading: true });

      const sessionData = await mistakesApi.getReviewSession(this.data.sessionId);

      console.log('📚 [复习页面] 会话数据完整内容:', sessionData);
      console.log('📚 [复习页面] question_content:', sessionData.question_content);
      console.log('📚 [复习页面] question_content类型:', typeof sessionData.question_content);
      console.log('📚 [复习页面] question_content长度:', sessionData.question_content?.length);

      this.setData({
        currentStage: sessionData.stage || 1,
        stageName: sessionData.stage_name || '原题复习',
        status: sessionData.status || 'in_progress',
        questionContent: sessionData.question_content || '',
        correctAnswer: sessionData.correct_answer || '',
        knowledgePoints: sessionData.knowledge_points || [],
        // 🎯 [Phase 1] 新增：接收图片数据
        imageUrls: sessionData.image_urls || [],
        hasImages: sessionData.has_images || false,
        loading: false,
      });

      console.log('📚 [复习页面] 设置后的questionContent:', this.data.questionContent);
      console.log('📚 [复习页面] 设置后的loading:', this.data.loading);

      // 如果会话已完成，显示结果
      if (sessionData.status !== 'in_progress') {
        this.showCompletionResult(sessionData);
      }
    } catch (error) {
      console.error('加载复习会话失败', error);
      this.setData({ loading: false });

      wx.showModal({
        title: '加载失败',
        content: error.message || '无法加载复习会话',
        showCancel: false,
        success: res => {
          if (res.confirm) {
            wx.navigateBack();
          }
        },
      });
    }
  },

  /**
   * 答案输入
   */
  onAnswerInput(e) {
    this.setData({
      userAnswer: e.detail.value || '',
    });
  },

  /**
   * 提交答案（AI判断）
   */
  async onSubmitAnswer() {
    const { userAnswer, sessionId, submitting } = this.data;

    if (submitting) return;

    if (!userAnswer || !userAnswer.trim()) {
      wx.showToast({
        title: '请先输入答案',
        icon: 'none',
        duration: 2000,
      });
      return;
    }

    try {
      this.setData({ submitting: true });

      const result = await mistakesApi.submitReviewAnswer(sessionId, {
        answer: userAnswer,
        skip: false,
      });

      console.log('AI判题结果', result);

      this.setData({ submitting: false });

      // 处理结果
      await this.handleSubmitResult(result);
    } catch (error) {
      console.error('提交答案失败', error);
      this.setData({ submitting: false });

      wx.showToast({
        title: error.message || '提交失败',
        icon: 'none',
        duration: 2000,
      });
    }
  },

  /**
   * 跳过题目（不会做）
   */
  async onSkipQuestion() {
    const { sessionId, submitting } = this.data;

    if (submitting) return;

    try {
      this.setData({ submitting: true });

      const result = await mistakesApi.submitReviewAnswer(sessionId, {
        answer: '',
        skip: true,
      });

      console.log('跳过结果', result);

      this.setData({ submitting: false });

      // 显示答案和反馈
      this.showResultDialog({
        ...result,
        skip: true,
      });
    } catch (error) {
      console.error('跳过失败', error);
      this.setData({ submitting: false });

      wx.showToast({
        title: error.message || '操作失败',
        icon: 'none',
        duration: 2000,
      });
    }
  },

  /**
   * 处理提交结果
   */
  async handleSubmitResult(result) {
    if (!result.correct) {
      // 答案错误，显示反馈弹窗
      this.showResultDialog(result);
      return;
    }

    // 答案正确
    if (result.status === 'completed_success') {
      // 第三阶段完成，显示成功弹窗
      this.showResultDialog({
        ...result,
        is_final: true,
      });
      return;
    }

    // 进入下一阶段，显示鼓励弹窗
    this.showResultDialog({
      ...result,
      is_next_stage: true,
    });
  },

  /**
   * 显示结果弹窗
   */
  showResultDialog(result) {
    console.log('显示结果弹窗', result);

    let dialogBtn = '确定'; // 默认按钮
    let dialogCancelBtn = '';

    if (result.skip || !result.correct) {
      // 答错或跳过：只能返回
      dialogBtn = '返回错题详情';
      dialogCancelBtn = '';
    } else if (result.is_final) {
      // 第三阶段完成：返回
      dialogBtn = '返回错题列表';
      dialogCancelBtn = '';
    } else if (result.is_next_stage) {
      // 进入下一阶段：下一阶段
      dialogBtn = '进入下一阶段';
      dialogCancelBtn = '';
    }

    console.log('弹窗按钮配置', { dialogBtn, dialogCancelBtn });

    this.setData({
      showResultDialog: true,
      resultData: result,
      resultDialogBtn: dialogBtn,
      resultDialogCancelBtn: dialogCancelBtn,
    });
  },

  /**
   * 结果弹窗确认
   */
  onResultDialogConfirm() {
    const { resultData } = this.data;

    this.setData({ showResultDialog: false });

    if (resultData.skip || !resultData.correct) {
      // 答错或跳过：返回
      wx.navigateBack();
    } else if (resultData.is_final) {
      // 第三阶段完成：返回
      wx.navigateBack();
    } else if (resultData.is_next_stage) {
      // 进入下一阶段：更新页面
      this.setData({
        currentStage: resultData.next_stage,
        stageName: resultData.stage_name || `阶段 ${resultData.next_stage}`,
        questionContent: resultData.next_question?.question_content || '',
        knowledgePoints: resultData.next_question?.knowledge_points || [],
        // 🎯 [Phase 1] 新增：下一阶段也可能有图片
        imageUrls: resultData.next_question?.image_urls || [],
        hasImages: resultData.next_question?.has_images || false,
        userAnswer: '', // 清空答案
      });
    }
  },

  /**
   * 结果弹窗取消
   */
  onResultDialogCancel() {
    this.setData({ showResultDialog: false });
  },

  /**
   * 显示完成结果
   */
  showCompletionResult(data) {
    const isSuccess = data.status === 'completed_success';

    this.setData({
      showResult: true,
      status: data.status,
      resultData: {
        success: isSuccess,
        title: isSuccess ? '🎉 复习完成' : '😔 复习失败',
        message: data.message || '',
        icon: isSuccess ? 'success' : 'fail',
      },
    });

    // 3秒后自动返回
    setTimeout(() => {
      wx.navigateBack();
    }, 3000);
  },

  /**
   * 返回列表
   */
  onBackToList() {
    wx.navigateBack();
  },

  /**
   * 🎯 [Phase 1] 新增：图片预览
   */
  onPreviewImage(e) {
    const { url, urls } = e.currentTarget.dataset;

    if (!url || !urls || urls.length === 0) {
      console.warn('图片数据无效');
      return;
    }

    wx.previewImage({
      current: url,
      urls: urls,
      fail: error => {
        console.error('预览图片失败', error);
        wx.showToast({
          title: '预览失败',
          icon: 'none',
        });
      },
    });
  },

  /**
   * 查看答案
   */
  onViewAnswer() {
    wx.showModal({
      title: '参考答案',
      content: this.data.correctAnswer || '暂无参考答案',
      showCancel: false,
    });
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {},

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {},

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {},

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {},

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    this.loadReviewSession();
    wx.stopPullDownRefresh();
  },
};

// ✅ 使用增强页面守卫包装
const wrappedPage = createGuardedPage(pageObject, {
  requireAuth: true,
  allowedRoles: ['student', 'teacher'],
});

Page(wrappedPage);

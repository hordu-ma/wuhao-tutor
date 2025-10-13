// pages/mistakes/add/index.js
const { createGuardedPage } = require('../../../utils/enhanced-page-guard.js');
const mistakesApi = require('../../../api/mistakes.js');

const pageObject = {
  data: {
    formData: {
      subject: '',
      difficulty_level: 2,
      question_content: '',
      student_answer: '',
      correct_answer: '',
      explanation: ''
    },
    submitting: false,
    showSubjectPicker: false,
    showDifficultyPicker: false,
    subjectActions: [
      { name: '语文' },
      { name: '数学' },
      { name: '英语' },
      { name: '物理' },
      { name: '化学' },
      { name: '生物' },
      { name: '历史' },
      { name: '地理' },
      { name: '政治' }
    ],
    difficultyActions: [
      { name: '简单', value: 1 },
      { name: '中等', value: 2 },
      { name: '困难', value: 3 }
    ]
  },

  onLoad(options) {
    // 从问答页面跳转时携带的参数
    if (options.questionId) {
      this.loadQuestionData(options.questionId);
    }
  },

  getDifficultyText(level) {
    const map = { 1: '简单', 2: '中等', 3: '困难' };
    return map[level] || '';
  },

  onSelectSubject() {
    this.setData({ showSubjectPicker: true });
  },

  onSubjectSelected(e) {
    this.setData({
      'formData.subject': e.detail.name,
      showSubjectPicker: false
    });
  },

  onCloseSubjectPicker() {
    this.setData({ showSubjectPicker: false });
  },

  onSelectDifficulty() {
    this.setData({ showDifficultyPicker: true });
  },

  onDifficultySelected(e) {
    this.setData({
      'formData.difficulty_level': e.detail.value,
      showDifficultyPicker: false
    });
  },

  onCloseDifficultyPicker() {
    this.setData({ showDifficultyPicker: false });
  },

  onQuestionChange(e) {
    this.setData({ 'formData.question_content': e.detail });
  },

  onStudentAnswerChange(e) {
    this.setData({ 'formData.student_answer': e.detail });
  },

  onCorrectAnswerChange(e) {
    this.setData({ 'formData.correct_answer': e.detail });
  },

  onExplanationChange(e) {
    this.setData({ 'formData.explanation': e.detail });
  },

  async onSubmit() {
    const { formData } = this.data;

    // 验证表单
    if (!formData.subject) {
      wx.showToast({ title: '请选择科目', icon: 'none' });
      return;
    }

    if (!formData.question_content.trim()) {
      wx.showToast({ title: '请输入题目内容', icon: 'none' });
      return;
    }

    if (!formData.correct_answer.trim()) {
      wx.showToast({ title: '请输入正确答案', icon: 'none' });
      return;
    }

    try {
      this.setData({ submitting: true });

      const response = await mistakesApi.createMistake(formData);

      if (response.success) {
        wx.showToast({
          title: '添加成功',
          icon: 'success'
        });

        setTimeout(() => {
          wx.navigateBack();
        }, 1500);
      } else {
        throw new Error(response.message || '添加失败');
      }
    } catch (error) {
      console.error('添加错题失败', error);
      wx.showToast({
        title: error.message || '添加失败',
        icon: 'error'
      });
    } finally {
      this.setData({ submitting: false });
    }
  }
};

Page(createGuardedPage(pageObject, 'pages/mistakes/add/index'));

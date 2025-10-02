// 帮助中心页面
const request = require('../../../utils/request');

Page({
  data: {
    searchValue: '',
    filteredFaqs: [],
    expandedIndex: -1,

    // 常见问题数据
    faqs: [
      {
        id: 1,
        question: '如何提交作业？',
        answer:
          '进入"作业"页面，点击待提交作业，选择拍照或从相册选择作业照片，系统会自动识别并批改。支持批量上传，每次最多9张图片。',
        category: '作业批改',
        helpful: 0,
      },
      {
        id: 2,
        question: '批改结果多久出来？',
        answer:
          'AI批改通常在10秒内完成。复杂题目或批量作业可能需要20-30秒。您可以在"我的作业"中查看批改进度和历史记录。',
        category: '作业批改',
        helpful: 0,
      },
      {
        id: 3,
        question: '如何查看错题本？',
        answer:
          '进入"学情分析"→"错题本"，可按学科、知识点筛选错题。点击错题查看详细解析和相似题推荐。支持收藏重点错题和打印功能。',
        category: '学习分析',
        helpful: 0,
      },
      {
        id: 4,
        question: '学习报告如何生成？',
        answer:
          '系统每周自动生成学习报告。您也可以在"学情分析"→"学习报告"中选择时间范围手动生成。报告包含学习趋势、知识点掌握度等数据。',
        category: '学习分析',
        helpful: 0,
      },
      {
        id: 5,
        question: '如何向AI提问？',
        answer:
          '进入"学习问答"页面，点击底部输入框。支持文字、语音、图片三种方式提问。AI会根据您的年级和学科提供针对性解答。',
        category: '学习问答',
        helpful: 0,
      },
      {
        id: 6,
        question: 'AI答案不准确怎么办？',
        answer:
          '点击答案下方的"不满意"按钮，选择问题类型（如理解偏差、知识点错误等）。我们会人工复核并优化AI模型。您也可以联系在线客服获取人工解答。',
        category: '学习问答',
        helpful: 0,
      },
      {
        id: 7,
        question: '如何修改个人信息？',
        answer:
          '进入"个人中心"，点击顶部头像区域进入编辑页面。可修改昵称、头像、年级、学科等信息。年级信息会影响题目推荐难度。',
        category: '账号设置',
        helpful: 0,
      },
      {
        id: 8,
        question: '如何切换学习难度？',
        answer:
          '进入"设置"→"学习偏好"→"难度设置"，选择基础巩固、同步提高或拓展挑战。系统会根据难度调整题目推荐和解析详细程度。',
        category: '账号设置',
        helpful: 0,
      },
      {
        id: 9,
        question: '数据会同步到云端吗？',
        answer:
          '是的，所有学习数据（作业记录、错题、问答历史等）自动同步到云端。更换设备登录后可查看完整历史数据。本地缓存会定期清理。',
        category: '数据隐私',
        helpful: 0,
      },
      {
        id: 10,
        question: '如何保护隐私？',
        answer:
          '我们采用端到端加密传输学习数据，不会向第三方共享您的个人信息。作业照片仅用于批改和学习分析。详见《隐私政策》。',
        category: '数据隐私',
        helpful: 0,
      },
    ],

    // 功能教程数据
    tutorials: [
      {
        id: 1,
        title: '新手入门指南',
        duration: '5分钟',
        cover: '',
        tags: ['新手必看'],
      },
      {
        id: 2,
        title: '作业批改完整流程',
        duration: '3分钟',
        cover: '',
        tags: ['作业批改'],
      },
      {
        id: 3,
        title: '如何使用错题本',
        duration: '4分钟',
        cover: '',
        tags: ['学习分析'],
      },
      {
        id: 4,
        title: 'AI问答技巧',
        duration: '6分钟',
        cover: '',
        tags: ['学习问答'],
      },
      {
        id: 5,
        title: '学习报告解读',
        duration: '5分钟',
        cover: '',
        tags: ['学习分析'],
      },
    ],
  },

  onLoad() {
    this.setData({
      filteredFaqs: this.data.faqs,
    });
  },

  // 搜索FAQ
  onSearchChange(event) {
    const value = event.detail.trim().toLowerCase();
    this.setData({ searchValue: value });

    if (!value) {
      this.setData({ filteredFaqs: this.data.faqs });
      return;
    }

    const filtered = this.data.faqs.filter(
      faq =>
        faq.question.toLowerCase().includes(value) ||
        faq.answer.toLowerCase().includes(value) ||
        faq.category.toLowerCase().includes(value),
    );

    this.setData({ filteredFaqs: filtered });
  },

  // 清空搜索
  onSearchClear() {
    this.setData({
      searchValue: '',
      filteredFaqs: this.data.faqs,
    });
  },

  // 展开/折叠FAQ
  toggleFaq(event) {
    const index = event.currentTarget.dataset.index;
    this.setData({
      expandedIndex: this.data.expandedIndex === index ? -1 : index,
    });
  },

  // 标记有帮助
  markHelpful(event) {
    const index = event.currentTarget.dataset.index;
    const faqs = [...this.data.faqs];
    faqs[index].helpful += 1;

    this.setData({ faqs });

    wx.showToast({
      title: '感谢反馈！',
      icon: 'success',
      duration: 1500,
    });

    // TODO: 发送反馈到后端
    this.submitFeedback(faqs[index].id, true);
  },

  // 标记无帮助
  markNotHelpful(event) {
    const index = event.currentTarget.dataset.index;
    const faq = this.data.faqs[index];

    wx.showModal({
      title: '问题反馈',
      content: '请告诉我们如何改进这个答案',
      editable: true,
      placeholderText: '请输入您的建议...',
      success: res => {
        if (res.confirm) {
          wx.showToast({
            title: '感谢反馈！',
            icon: 'success',
            duration: 1500,
          });
          // TODO: 发送反馈到后端
          this.submitFeedback(faq.id, false, res.content);
        }
      },
    });
  },

  // 提交反馈
  submitFeedback(faqId, helpful, comment) {
    request
      .post('/api/v1/help/feedback', {
        faq_id: faqId,
        helpful,
        comment: comment || '',
      })
      .catch(err => {
        console.error('提交反馈失败:', err);
      });
  },

  // 快捷入口
  handleQuickAccess(event) {
    const type = event.currentTarget.dataset.type;

    switch (type) {
      case 'guide':
        this.openTutorial({ currentTarget: { dataset: { id: 1 } } });
        break;
      case 'video':
        wx.showToast({
          title: '视频教程开发中',
          icon: 'none',
          duration: 2000,
        });
        break;
      case 'service':
        this.contactService('wechat');
        break;
      case 'faq':
        // 滚动到FAQ区域
        wx.pageScrollTo({
          selector: '.faq-section',
          duration: 300,
        });
        break;
    }
  },

  // 打开教程
  openTutorial(event) {
    const id = event.currentTarget.dataset.id;
    // TODO: 跳转到教程详情页
    wx.showToast({
      title: '教程详情开发中',
      icon: 'none',
      duration: 2000,
    });
  },

  // 联系客服
  contactService(type) {
    switch (type) {
      case 'wechat':
        wx.setClipboardData({
          data: 'wuhao_tutor_service',
          success: () => {
            wx.showModal({
              title: '微信客服',
              content: '客服微信号已复制，请在微信中添加好友',
              showCancel: false,
              confirmText: '知道了',
            });
          },
        });
        break;
      case 'phone':
        wx.makePhoneCall({
          phoneNumber: '400-123-4567',
        });
        break;
      case 'email':
        wx.setClipboardData({
          data: 'support@wuhaotutor.com',
          success: () => {
            wx.showToast({
              title: '邮箱地址已复制',
              icon: 'success',
              duration: 2000,
            });
          },
        });
        break;
    }
  },

  // 意见反馈
  handleFeedback() {
    wx.navigateTo({
      url: '/pages/profile/feedback/index',
    });
  },

  // 分享
  onShareAppMessage() {
    return {
      title: '五好伴学 - 专业的K12学习辅导助手',
      path: '/pages/index/index',
      imageUrl: '/assets/images/share-help.png',
    };
  },

  onShareTimeline() {
    return {
      title: '五好伴学 - 专业的K12学习辅导助手',
      query: 'from=timeline',
      imageUrl: '/assets/images/share-help.png',
    };
  },
});

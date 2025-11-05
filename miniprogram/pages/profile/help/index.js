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
      },
      {
        id: 2,
        question: '批改结果多久出来？',
        answer:
          'AI批改通常在10秒内完成。复杂题目或批量作业可能需要20-30秒。您可以在"我的作业"中查看批改进度和历史记录。',
        category: '作业批改',
      },
      {
        id: 3,
        question: '如何查看错题本？',
        answer:
          '进入"学情分析"→"错题本"，可按学科、知识点筛选错题。点击错题查看详细解析和相似题推荐。支持收藏重点错题和打印功能。',
        category: '学习分析',
      },
      {
        id: 4,
        question: '学习报告如何生成？',
        answer:
          '系统每周自动生成学习报告。您也可以在"学情分析"→"学习报告"中选择时间范围手动生成。报告包含学习趋势、知识点掌握度等数据。',
        category: '学习分析',
      },
      {
        id: 5,
        question: '如何向AI提问？',
        answer:
          '进入"学习问答"页面，点击底部输入框。支持文字、语音、图片三种方式提问。AI会根据您的年级和学科提供针对性解答。',
        category: '学习问答',
      },
      {
        id: 6,
        question: 'AI答案不准确怎么办？',
        answer:
          '点击答案下方的"不满意"按钮，选择问题类型（如理解偏差、知识点错误等）。我们会人工复核并优化AI模型。您也可以联系在线客服获取人工解答。',
        category: '学习问答',
      },
      {
        id: 7,
        question: '如何修改个人信息？',
        answer:
          '进入"个人中心"，点击顶部头像区域进入编辑页面。可修改昵称、头像、年级、学科等信息。年级信息会影响题目推荐难度。',
        category: '账号设置',
      },
      {
        id: 8,
        question: '数据会同步到云端吗？',
        answer:
          '是的，所有学习数据（作业记录、错题、问答历史等）自动同步到云端。更换设备登录后可查看完整历史数据。本地缓存会定期清理。',
        category: '数据隐私',
      },
      {
        id: 9,
        question: '如何保护隐私？',
        answer:
          '我们采用端到端加密传输学习数据，不会向第三方共享您的个人信息。作业照片仅用于批改和学习分析。详见《隐私政策》。',
        category: '数据隐私',
      },
      {
        id: 10,
        question: '遇到问题如何联系客服？',
        answer:
          '可以通过以下方式联系我们：\n1. 添加客服微信：wuhao_service\n2. 发送邮件：support@wuhaotutor.com\n工作时间：周一至周五 9:00-18:00',
        category: '其他',
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

  // 快捷入口
  handleQuickAccess(event) {
    const type = event.currentTarget.dataset.type;

    switch (type) {
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

  // 联系客服
  contactService(type) {
    switch (type) {
      case 'wechat':
        wx.setClipboardData({
          data: 'wuhao_service',
          success: () => {
            wx.showModal({
              title: '客服微信',
              content: '客服微信号已复制\nwuhao_service\n\n请在微信中添加好友',
              showCancel: false,
              confirmText: '知道了',
            });
          },
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

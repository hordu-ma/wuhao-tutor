// pages/homework/submit/index.js - 作业提交页面

const { authManager } = require('../../../utils/auth.js');
const api = require('../../../utils/api.js');
const utils = require('../../../utils/utils.js');

Page({
  /**
   * 页面的初始数据
   */
  data: {
    // 作业信息
    homework: null,
    homeworkId: '',

    // 用户信息
    userInfo: null,

    // 提交类型
    submitType: 'text', // text, image, mixed

    // 文字提交内容
    textContent: '',

    // 图片列表
    imageList: [],
    maxImageCount: 9,

    // 文件列表
    fileList: [],

    // 提交状态
    isSubmitting: false,

    // 表单验证
    errors: {},

    // 加载状态
    loading: true,

    // 预览模式
    previewMode: false,

    // 字数统计
    wordCount: 0,
    minWordCount: 50,
    maxWordCount: 2000,
  },

  /**
   * 生命周期函数--监听页面加载
   */
  async onLoad(options) {
    console.log('作业提交页面加载', options);

    if (!options.homeworkId) {
      this.showError('作业ID不能为空');
      return;
    }

    this.setData({ homeworkId: options.homeworkId });

    // 处理从首页快捷提交传入的参数
    if (options.type) {
      this.setData({ submitType: options.type });
    }

    if (options.images) {
      try {
        const images = JSON.parse(options.images);
        this.setData({ imageList: images });
      } catch (error) {
        console.error('解析图片参数失败:', error);
      }
    }

    try {
      await this.initUserInfo();
      await this.loadHomeworkInfo(options.homeworkId);
      await this.loadExistingSubmission(options.homeworkId);
    } catch (error) {
      console.error('页面初始化失败:', error);
      this.showError('页面加载失败');
    }
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    // 检查字数
    this.updateWordCount();
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
    return {
      title: '作业提交',
      path: `/pages/homework/submit/index?homeworkId=${this.data.homeworkId}`,
    };
  },

  /**
   * 初始化用户信息
   */
  async initUserInfo() {
    try {
      const userInfo = await authManager.getUserInfo();
      this.setData({ userInfo });
    } catch (error) {
      console.error('获取用户信息失败:', error);
      throw error;
    }
  },

  /**
   * 加载作业信息
   */
  async loadHomeworkInfo(homeworkId) {
    try {
      this.setData({ loading: true });

      // TODO: 调用API获取作业信息
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
        deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        allowedTypes: ['text', 'image'], // 允许的提交类型
        minWords: 50,
        maxWords: 2000,
      };

      this.setData({
        homework,
        minWordCount: homework.minWords || 50,
        maxWordCount: homework.maxWords || 2000,
      });
    } catch (error) {
      console.error('加载作业信息失败:', error);
      throw error;
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载已有提交记录
   */
  async loadExistingSubmission(homeworkId) {
    try {
      // TODO: 调用API获取已有提交记录
      // const response = await api.getHomeworkSubmission(homeworkId);

      // 模拟数据 - 如果有已提交的作业，可以编辑
      const existingSubmission = null;

      if (existingSubmission) {
        this.setData({
          textContent: existingSubmission.content || '',
          imageList: existingSubmission.images || [],
          fileList: existingSubmission.files || [],
        });
        this.updateWordCount();
      }
    } catch (error) {
      console.error('加载提交记录失败:', error);
    }
  },

  /**
   * 刷新数据
   */
  async refreshData() {
    const { homeworkId } = this.data;
    if (homeworkId) {
      await this.loadHomeworkInfo(homeworkId);
    }
  },

  /**
   * 切换提交类型
   */
  onSubmitTypeChange(e) {
    const { type } = e.currentTarget.dataset;
    this.setData({ submitType: type });
  },

  /**
   * 文字内容输入
   */
  onTextInput(e) {
    const content = e.detail.value;
    this.setData({ textContent: content });
    this.updateWordCount();
    this.validateText();
  },

  /**
   * 更新字数统计
   */
  updateWordCount() {
    const { textContent } = this.data;
    const wordCount = textContent.trim().length;
    this.setData({ wordCount });
  },

  /**
   * 验证文字内容
   */
  validateText() {
    const { textContent, minWordCount, maxWordCount } = this.data;
    const wordCount = textContent.trim().length;
    const errors = { ...this.data.errors };

    if (wordCount < minWordCount) {
      errors.text = `至少需要${minWordCount}个字符`;
    } else if (wordCount > maxWordCount) {
      errors.text = `不能超过${maxWordCount}个字符`;
    } else {
      delete errors.text;
    }

    this.setData({ errors });
  },

  /**
   * 选择图片
   */
  onChooseImage() {
    const { imageList, maxImageCount } = this.data;
    const remainCount = maxImageCount - imageList.length;

    if (remainCount <= 0) {
      wx.showToast({
        title: `最多只能选择${maxImageCount}张图片`,
        icon: 'none',
      });
      return;
    }

    wx.chooseMedia({
      count: remainCount,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: res => {
        const newImages = res.tempFiles.map(file => ({
          url: file.tempFilePath,
          size: file.size,
        }));

        this.setData({
          imageList: [...imageList, ...newImages],
        });
      },
      fail: error => {
        console.error('选择图片失败:', error);
        wx.showToast({
          title: '选择图片失败',
          icon: 'error',
        });
      },
    });
  },

  /**
   * 预览图片
   */
  onPreviewImage(e) {
    const { index } = e.currentTarget.dataset;
    const { imageList } = this.data;

    wx.previewImage({
      current: imageList[index].url,
      urls: imageList.map(img => img.url),
    });
  },

  /**
   * 删除图片
   */
  onDeleteImage(e) {
    const { index } = e.currentTarget.dataset;
    const { imageList } = this.data;

    imageList.splice(index, 1);
    this.setData({ imageList });
  },

  /**
   * 拍照
   */
  onTakePhoto() {
    const { imageList, maxImageCount } = this.data;

    if (imageList.length >= maxImageCount) {
      wx.showToast({
        title: `最多只能拍摄${maxImageCount}张图片`,
        icon: 'none',
      });
      return;
    }

    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      success: res => {
        const newImage = {
          url: res.tempFiles[0].tempFilePath,
          size: res.tempFiles[0].size,
        };

        this.setData({
          imageList: [...imageList, newImage],
        });
      },
      fail: error => {
        console.error('拍照失败:', error);
        wx.showToast({
          title: '拍照失败',
          icon: 'error',
        });
      },
    });
  },

  /**
   * 选择文件
   */
  onChooseFile() {
    // 微信小程序目前不支持直接选择文件，这里可以提示用户使用图片代替
    wx.showModal({
      title: '提示',
      content: '小程序暂不支持文件上传，请使用图片方式提交',
      showCancel: false,
    });
  },

  /**
   * 切换预览模式
   */
  onTogglePreview() {
    this.setData({ previewMode: !this.data.previewMode });
  },

  /**
   * 提交作业
   */
  async onSubmitHomework() {
    if (!this.validateSubmission()) {
      return;
    }

    try {
      this.setData({ isSubmitting: true });

      const { homework, textContent, imageList, userInfo } = this.data;

      // 构建提交数据
      const submissionData = {
        homeworkId: homework.id,
        studentId: userInfo.id,
        content: textContent.trim(),
        images: imageList,
        submittedAt: new Date().toISOString(),
      };

      // TODO: 上传图片和提交数据
      // await this.uploadImages();
      // const response = await api.submitHomework(submissionData);

      // 模拟提交成功
      await new Promise(resolve => setTimeout(resolve, 2000));

      wx.showToast({
        title: '提交成功',
        icon: 'success',
      });

      // 返回上一页并刷新
      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          const prevPage = pages[pages.length - 2];
          prevPage.setData({ needRefresh: true });
        }
        wx.navigateBack();
      }, 1500);
    } catch (error) {
      console.error('提交作业失败:', error);
      wx.showToast({
        title: '提交失败，请重试',
        icon: 'error',
      });
    } finally {
      this.setData({ isSubmitting: false });
    }
  },

  /**
   * 验证提交内容
   */
  validateSubmission() {
    const { submitType, textContent, imageList, minWordCount } = this.data;

    if (submitType === 'text' || submitType === 'mixed') {
      if (textContent.trim().length < minWordCount) {
        wx.showToast({
          title: `文字内容至少需要${minWordCount}个字符`,
          icon: 'none',
        });
        return false;
      }
    }

    if (submitType === 'image' || submitType === 'mixed') {
      if (imageList.length === 0) {
        wx.showToast({
          title: '请至少上传一张图片',
          icon: 'none',
        });
        return false;
      }
    }

    if (submitType === 'text' && textContent.trim().length === 0) {
      wx.showToast({
        title: '请输入作业内容',
        icon: 'none',
      });
      return false;
    }

    return true;
  },

  /**
   * 上传图片
   */
  async uploadImages() {
    // TODO: 实现图片上传逻辑
    const { imageList } = this.data;
    const uploadedUrls = [];

    for (let i = 0; i < imageList.length; i++) {
      const image = imageList[i];
      if (image.url.startsWith('http')) {
        uploadedUrls.push(image.url);
        continue;
      }

      // 上传本地图片
      const uploadResult = await this.uploadSingleImage(image.url);
      uploadedUrls.push(uploadResult.url);
    }

    return uploadedUrls;
  },

  /**
   * 上传单张图片
   */
  uploadSingleImage(filePath) {
    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${api.baseURL}/upload/image`,
        filePath: filePath,
        name: 'file',
        header: {
          Authorization: `Bearer ${authManager.getToken()}`,
        },
        success: res => {
          try {
            const result = JSON.parse(res.data);
            if (result.success) {
              resolve({ url: result.data.url });
            } else {
              reject(new Error(result.message));
            }
          } catch (error) {
            reject(error);
          }
        },
        fail: reject,
      });
    });
  },

  /**
   * 保存草稿
   */
  async onSaveDraft() {
    try {
      const { homework, textContent, imageList } = this.data;

      const draftData = {
        homeworkId: homework.id,
        content: textContent,
        images: imageList,
        savedAt: new Date().toISOString(),
      };

      // TODO: 保存草稿到本地或服务器
      wx.setStorageSync(`homework_draft_${homework.id}`, draftData);

      wx.showToast({
        title: '草稿已保存',
        icon: 'success',
      });
    } catch (error) {
      console.error('保存草稿失败:', error);
      wx.showToast({
        title: '保存失败',
        icon: 'error',
      });
    }
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
});

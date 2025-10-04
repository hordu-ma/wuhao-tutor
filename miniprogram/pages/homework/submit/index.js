// pages/homework/submit/index.js - 作业提交页面

const { authManager } = require('../../../utils/auth.js');
const homeworkAPI = require('../../../api/homework.js');
const utils = require('../../../utils/utils.js');
const imageProcessor = require('../../../utils/image-processor.js');

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

    // 图片处理状态
    imageProcessing: false,
    compressionProgress: 0,
    showCompressionDialog: false,

    // 新增: 图片裁剪相关
    showImageCropper: false,
    currentCropImage: null,
    currentCropIndex: -1,

    // 新增: 质量选择器
    showQualitySelector: false,
    selectedQuality: 'standard', // high, standard, low
    qualityConfig: {
      quality: 0.8,
      maxSizeKB: 500,
      maxWidth: 1080,
      maxHeight: 1920
    },

    // 新增: OCR进度
    showOCRProgress: false,
    ocrImages: [], // {id, path, status, ocrText, confidence, error}
    ocrProgress: 0
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

      // 调用API获取作业模板详情
      const response = await homeworkAPI.getTemplateDetail(homeworkId);

      if (response.success && response.data) {
        const homework = {
          id: response.data.id,
          title: response.data.name,
          subject: response.data.subject,
          description: response.data.description,
          requirements: response.data.requirements || [],
          deadline: response.data.deadline,
          allowedTypes: ['text', 'image'],
          minWords: response.data.min_words || 50,
          maxWords: response.data.max_words || 2000,
          maxScore: response.data.max_score || 100,
        };

        this.setData({
          homework,
          minWordCount: homework.minWords,
          maxWordCount: homework.maxWords,
        });
      } else {
        throw new Error(response.message || '加载作业信息失败');
      }
    } catch (error) {
      console.error('加载作业信息失败:', error);
      wx.showToast({
        title: error.message || '加载失败',
        icon: 'error',
      });
      // 等待提示显示后返回上一页
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 加载已有提交记录
   */
  async loadExistingSubmission(homeworkId) {
    try {
      // 获取该作业的提交记录
      const response = await homeworkAPI.getSubmissions({
        template_id: homeworkId,
        page: 1,
        size: 1,
      });

      if (response.success && response.data && response.data.length > 0) {
        const existingSubmission = response.data[0];

        // 如果状态是pending或failed，允许重新编辑
        if (existingSubmission.status === 'pending' || existingSubmission.status === 'failed') {
          this.setData({
            textContent: existingSubmission.content || '',
            imageList: existingSubmission.images || [],
          });
          this.updateWordCount();

          wx.showToast({
            title: '已加载上次提交内容',
            icon: 'success',
          });
        }
      }
    } catch (error) {
      console.error('加载提交记录失败:', error);
      // 不影响主流程，静默失败
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
  async onChooseImage() {
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
      success: async (res) => {
        await this.processSelectedImages(res.tempFiles);
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
  async onTakePhoto() {
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
      success: async (res) => {
        await this.processSelectedImages(res.tempFiles);
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
   * 处理选中的图片
   */
  async processSelectedImages(tempFiles) {
    try {
      this.setData({
        imageProcessing: true,
        showCompressionDialog: true,
        compressionProgress: 0
      });

      const { imageList } = this.data;
      const processedImages = [];

      for (let i = 0; i < tempFiles.length; i++) {
        const file = tempFiles[i];

        // 更新进度
        const progress = Math.round(((i + 1) / tempFiles.length) * 100);
        this.setData({ compressionProgress: progress });

        try {
          // 检查是否需要压缩
          const shouldCompressResult = await imageProcessor.shouldCompress(file.tempFilePath, {
            maxWidth: 1080,
            maxHeight: 1920,
            maxSizeKB: 500
          });

          let finalPath = file.tempFilePath;
          let finalSize = file.size;

          if (shouldCompressResult.shouldCompress) {
            // 压缩图片
            const compressResult = await imageProcessor.compressImage(file.tempFilePath, {
              maxWidth: 1080,
              maxHeight: 1920,
              quality: 0.8,
              maxSizeKB: 500
            });

            if (compressResult.success) {
              finalPath = compressResult.compressedPath;
              finalSize = compressResult.compressedSize;

              console.log(`图片压缩成功: ${imageProcessor.formatFileSize(compressResult.originalSize)} -> ${imageProcessor.formatFileSize(compressResult.compressedSize)} (压缩率: ${compressResult.compressionRatio}%)`);
            } else {
              console.warn('图片压缩失败，使用原图:', compressResult.error);
            }
          }

          // 矫正图片方向
          const correctedPath = await imageProcessor.correctImageOrientation(finalPath);

          // 生成预览信息
          const previewInfo = await imageProcessor.generatePreviewInfo(correctedPath);

          processedImages.push({
            url: correctedPath,
            size: finalSize,
            originalSize: file.size,
            width: previewInfo.width,
            height: previewInfo.height,
            formattedSize: previewInfo.formattedSize,
            compressed: shouldCompressResult.shouldCompress,
          });

        } catch (error) {
          console.error('处理图片失败:', error);
          // 处理失败时使用原图
          processedImages.push({
            url: file.tempFilePath,
            size: file.size,
            originalSize: file.size,
            compressed: false,
            error: error.message,
          });
        }
      }

      // 更新图片列表
      this.setData({
        imageList: [...imageList, ...processedImages],
        imageProcessing: false,
        showCompressionDialog: false,
        compressionProgress: 0,
      });

      // 显示处理结果
      const compressedCount = processedImages.filter(img => img.compressed).length;
      if (compressedCount > 0) {
        wx.showToast({
          title: `已优化${compressedCount}张图片`,
          icon: 'success',
        });
      }

    } catch (error) {
      console.error('批量处理图片失败:', error);
      this.setData({
        imageProcessing: false,
        showCompressionDialog: false,
        compressionProgress: 0,
      });

      wx.showToast({
        title: '图片处理失败',
        icon: 'error',
      });
    }
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

      const { homework, textContent, imageList, userInfo, submitType } = this.data;

      let submissionResult = null;

      // 根据提交类型调用不同的API
      if (submitType === 'image' || (submitType === 'mixed' && imageList.length > 0)) {
        // 图片提交
        submissionResult = await this.submitWithImages();
      } else {
        // 纯文本提交
        submissionResult = await this.submitWithText();
      }

      if (submissionResult && submissionResult.success) {
        // 提交成功，显示成功提示
        wx.showToast({
          title: '提交成功',
          icon: 'success',
          duration: 2000,
        });

        // 跳转到批改结果页面或返回列表
        setTimeout(() => {
          const submissionId = submissionResult.data.id;
          if (submissionId) {
            // 跳转到详情页查看批改结果
            wx.redirectTo({
              url: `/pages/homework/detail/index?id=${submissionId}`,
            });
          } else {
            // 返回上一页
            const pages = getCurrentPages();
            if (pages.length > 1) {
              const prevPage = pages[pages.length - 2];
              if (prevPage.refreshData) {
                prevPage.refreshData();
              }
            }
            wx.navigateBack();
          }
        }, 1500);
      } else {
        throw new Error(submissionResult?.message || '提交失败');
      }
    } catch (error) {
      console.error('提交作业失败:', error);
      wx.showModal({
        title: '提交失败',
        content: error.message || '网络错误，请重试',
        showCancel: false,
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
   * 文本提交
   */
  async submitWithText() {
    const { homework, textContent, userInfo } = this.data;

    const submitData = {
      template_id: homework.id,
      student_name: userInfo.name || userInfo.username || '学生',
      content: textContent.trim(),
    };

    return await homeworkAPI.submitHomeworkText(submitData);
  },

  /**
   * 图片提交
   */
  async submitWithImages() {
    const { homework, imageList, textContent, userInfo } = this.data;

    // 获取第一张图片作为主提交
    const firstImage = imageList[0];

    if (!firstImage || !firstImage.url) {
      throw new Error('请至少上传一张图片');
    }

    const additionalInfo = textContent.trim() || undefined;

    // 提交第一张图片
    const result = await homeworkAPI.submitHomeworkImage({
      template_id: homework.id,
      student_name: userInfo.name || userInfo.username || '学生',
      filePath: firstImage.url,
      additional_info: additionalInfo,
      onProgress: (progress) => {
        console.log('上传进度:', progress);
        // 可以在这里更新UI显示上传进度
      },
    });

    // 如果有多张图片，继续提交剩余图片
    if (imageList.length > 1) {
      const remainingImages = imageList.slice(1);
      const filePaths = remainingImages.map(img => img.url);

      // 后台继续上传剩余图片（不阻塞返回）
      homeworkAPI.submitHomeworkImages({
        template_id: homework.id,
        student_name: userInfo.name || userInfo.username || '学生',
        filePaths,
        additional_info: `附加图片 (${remainingImages.length}张)`,
        onProgress: (progress) => {
          console.log('批量上传进度:', progress);
        },
      }).catch(error => {
        console.error('批量上传失败:', error);
      });
    }

    return result;
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

      // 保存草稿到本地存储
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
   * 加载草稿
   */
  loadDraft() {
    try {
      const { homework } = this.data;
      const draftData = wx.getStorageSync(`homework_draft_${homework.id}`);

      if (draftData) {
        wx.showModal({
          title: '发现草稿',
          content: '是否加载上次保存的草稿？',
          success: (res) => {
            if (res.confirm) {
              this.setData({
                textContent: draftData.content || '',
                imageList: draftData.images || [],
              });
              this.updateWordCount();

              wx.showToast({
                title: '草稿已加载',
                icon: 'success',
              });
            }
          },
        });
      }
    } catch (error) {
      console.error('加载草稿失败:', error);
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

  /**
   * 重新压缩单张图片
   */
  async onRecompressImage(e) {
    const { index } = e.currentTarget.dataset;
    const { imageList } = this.data;

    if (!imageList[index]) return;

    const image = imageList[index];

    try {
      wx.showLoading({ title: '重新优化中...' });

      const compressResult = await imageProcessor.compressImage(image.url, {
        maxWidth: 800,
        maxHeight: 1200,
        quality: 0.6,
        maxSizeKB: 300
      });

      if (compressResult.success) {
        // 更新图片信息
        const updatedImage = {
          ...image,
          url: compressResult.compressedPath,
          size: compressResult.compressedSize,
          compressed: true,
          formattedSize: imageProcessor.formatFileSize(compressResult.compressedSize),
        };

        const newImageList = [...imageList];
        newImageList[index] = updatedImage;

        this.setData({ imageList: newImageList });

        wx.hideLoading();
        wx.showToast({
          title: '优化成功',
          icon: 'success',
        });
      }
    } catch (error) {
      console.error('重新压缩失败:', error);
      wx.hideLoading();
      wx.showToast({
        title: '优化失败',
        icon: 'error',
      });
    }
  },

  /**
   * 查看图片详情
   */
  onViewImageInfo(e) {
    const { index } = e.currentTarget.dataset;
    const { imageList } = this.data;
    const image = imageList[index];

    if (!image) return;

    const info = [
      `尺寸: ${image.width || '未知'} × ${image.height || '未知'}`,
      `大小: ${image.formattedSize || imageProcessor.formatFileSize(image.size)}`,
      `状态: ${image.compressed ? '已优化' : '原图'}`,
    ];

    if (image.originalSize && image.originalSize !== image.size) {
      const ratio = Math.round(((image.originalSize - image.size) / image.originalSize) * 100);
      info.push(`压缩率: ${ratio}%`);
    }

    wx.showModal({
      title: '图片信息',
      content: info.join('\n'),
      showCancel: false,
    });
  },
});

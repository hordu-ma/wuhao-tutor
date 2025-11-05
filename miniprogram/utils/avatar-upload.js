// utils/avatar-upload.js - 头像上传工具

const { apiClient } = require('./api.js'); // 使用 apiClient 而不是 api
const { authManager } = require('./auth.js');
const { errorToast } = require('./error-toast.js');
const { profileErrorHandler } = require('./profile-error-handler.js');

/**
 * 头像上传管理器
 */
class AvatarUploadManager {
  constructor() {
    this.uploadInProgress = false;
    this.maxFileSize = 5 * 1024 * 1024; // 5MB
    this.allowedTypes = ['jpg', 'jpeg', 'png', 'webp'];
    this.compressQuality = 0.8;
    this.maxWidth = 800;
    this.maxHeight = 800;
  }

  /**
   * 选择并上传头像
   */
  async selectAndUploadAvatar(options = {}) {
    console.log('🚀 [Avatar Debug] selectAndUploadAvatar 被调用');

    if (this.uploadInProgress) {
      wx.showToast({
        title: '正在上传中...',
        icon: 'none',
      });
      return;
    }

    try {
      // 选择图片
      const imageResult = await this.chooseAvatar(options);
      if (!imageResult) {
        return null;
      }

      console.log('🚀 [Avatar Debug] 图片选择成功，准备上传');

      // 上传图片
      const uploadResult = await this.uploadAvatarImage(imageResult.tempFilePath);
      return uploadResult;
    } catch (error) {
      console.error('头像上传失败:', error);
      this.handleUploadError(error);
      throw error;
    }
  }

  /**
   * 选择头像图片
   */
  async chooseAvatar(options = {}) {
    return new Promise((resolve, reject) => {
      wx.showActionSheet({
        itemList: ['从相册选择', '拍照'],
        success: res => {
          if (res.tapIndex === 0) {
            // 从相册选择
            this.chooseImageFromAlbum(options).then(resolve).catch(reject);
          } else if (res.tapIndex === 1) {
            // 拍照
            this.chooseImageFromCamera(options).then(resolve).catch(reject);
          }
        },
        fail: () => {
          resolve(null); // 用户取消选择
        },
      });
    });
  }

  /**
   * 从相册选择图片
   */
  async chooseImageFromAlbum(options = {}) {
    return new Promise((resolve, reject) => {
      wx.chooseImage({
        count: 1,
        sizeType: ['compressed', 'original'],
        sourceType: ['album'],
        ...options,
        success: async res => {
          try {
            const filePath = res.tempFilePaths[0];
            const validationResult = await this.validateImage(filePath);

            if (validationResult.valid) {
              resolve({
                tempFilePath: filePath,
                size: validationResult.size,
              });
            } else {
              wx.showToast({
                title: validationResult.message,
                icon: 'error',
              });
              resolve(null);
            }
          } catch (error) {
            reject(error);
          }
        },
        fail: error => {
          if (error.errMsg !== 'chooseImage:fail cancel') {
            reject(error);
          } else {
            resolve(null);
          }
        },
      });
    });
  }

  /**
   * 拍照选择图片
   */
  async chooseImageFromCamera(options = {}) {
    return new Promise((resolve, reject) => {
      wx.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['camera'],
        ...options,
        success: async res => {
          try {
            const filePath = res.tempFilePaths[0];
            const validationResult = await this.validateImage(filePath);

            if (validationResult.valid) {
              resolve({
                tempFilePath: filePath,
                size: validationResult.size,
              });
            } else {
              wx.showToast({
                title: validationResult.message,
                icon: 'error',
              });
              resolve(null);
            }
          } catch (error) {
            reject(error);
          }
        },
        fail: error => {
          if (error.errMsg !== 'chooseImage:fail cancel') {
            reject(error);
          } else {
            resolve(null);
          }
        },
      });
    });
  }

  /**
   * 验证图片
   */
  async validateImage(filePath) {
    try {
      // 获取图片信息
      const imageInfo = await this.getImageInfo(filePath);

      // 检查文件大小
      if (imageInfo.size > this.maxFileSize) {
        return {
          valid: false,
          message: `图片大小不能超过${this.formatFileSize(this.maxFileSize)}`,
        };
      }

      // 检查图片格式
      const extension = this.getFileExtension(filePath);
      if (!this.allowedTypes.includes(extension.toLowerCase())) {
        return {
          valid: false,
          message: `不支持的图片格式，请选择${this.allowedTypes.join('、')}格式的图片`,
        };
      }

      // 检查图片尺寸（建议）
      if (imageInfo.width < 100 || imageInfo.height < 100) {
        return {
          valid: false,
          message: '图片尺寸太小，建议选择至少100x100像素的图片',
        };
      }

      return {
        valid: true,
        size: imageInfo.size,
        width: imageInfo.width,
        height: imageInfo.height,
      };
    } catch (error) {
      console.error('验证图片失败:', error);
      return {
        valid: false,
        message: '图片格式不正确',
      };
    }
  }

  /**
   * 获取图片信息
   */
  async getImageInfo(filePath) {
    return new Promise((resolve, reject) => {
      wx.getImageInfo({
        src: filePath,
        success: res => {
          // 获取文件大小
          wx.getFileInfo({
            filePath,
            success: fileRes => {
              resolve({
                width: res.width,
                height: res.height,
                size: fileRes.size,
                type: res.type,
              });
            },
            fail: () => {
              resolve({
                width: res.width,
                height: res.height,
                size: 0,
                type: res.type,
              });
            },
          });
        },
        fail: reject,
      });
    });
  }

  /**
   * 上传头像图片
   */
  async uploadAvatarImage(filePath) {
    console.log('🚀 [Avatar Debug] uploadAvatarImage 开始，文件路径:', filePath);

    try {
      this.uploadInProgress = true;

      // 显示上传进度
      wx.showLoading({
        title: '上传中...',
        mask: true,
      });

      // 调用后端头像上传接口
      console.log('🔧 [Avatar Upload Debug] 开始上传头像');
      console.log('🔧 [Avatar Upload Debug] 文件路径:', filePath);
      console.log('🔧 [Avatar Upload Debug] 上传URL路径: /auth/avatar');

      const response = await apiClient.upload('/auth/avatar', filePath, {
        name: 'file',
        formData: {
          category: 'avatar',
          compress: 'true',
        },
      });

      console.log('🔧 [Avatar Upload Debug] 上传响应:', response);

      wx.hideLoading();

      // 修复：检查实际的响应结构
      if (
        response.statusCode >= 200 &&
        response.statusCode < 300 &&
        response.data &&
        response.data.success
      ) {
        const avatarUrl = response.data.data.avatar_url;

        // 确保头像URL是完整的HTTPS URL
        const fullAvatarUrl = avatarUrl.startsWith('http')
          ? avatarUrl
          : `https://www.horsduroot.com${avatarUrl}`;

        // 更新本地用户信息
        await this.updateLocalUserAvatar(fullAvatarUrl);

        // 重要：同步头像URL到后端数据库
        await this.syncAvatarToBackend(fullAvatarUrl);

        console.log('🔧 [Avatar Upload Debug] 完整头像URL:', fullAvatarUrl);

        wx.showToast({
          title: '头像上传成功',
          icon: 'success',
        });

        return {
          success: true,
          avatarUrl: fullAvatarUrl,
          data: response.data.data,
        };
      } else {
        throw new Error(response.data?.message || response.data?.detail || '上传失败');
      }
    } catch (error) {
      console.error('头像上传失败:', error);

      // 使用专业的错误处理器
      const errorResult = await profileErrorHandler.handleAvatarUploadError(error, {
        retryFunction: async () => {
          const response = await apiClient.upload('/auth/avatar', filePath, {
            name: 'file',
            formData: {
              category: 'avatar',
              compress: 'true',
            },
          });

          if (
            response.statusCode >= 200 &&
            response.statusCode < 300 &&
            response.data &&
            response.data.success
          ) {
            const avatarUrl = response.data.data.avatar_url;

            // 确保头像URL是完整的HTTPS URL
            const fullAvatarUrl = avatarUrl.startsWith('http')
              ? avatarUrl
              : `https://www.horsduroot.com${avatarUrl}`;

            await this.updateLocalUserAvatar(fullAvatarUrl);
            return {
              success: true,
              avatarUrl: fullAvatarUrl,
              data: response.data.data,
            };
          } else {
            throw new Error(response.data?.message || response.data?.detail || '上传失败');
          }
        },
      });

      if (errorResult.success) {
        wx.showToast({
          title: '头像上传成功',
          icon: 'success',
        });
        return errorResult.data;
      }

      throw error;
    } finally {
      this.uploadInProgress = false;
    }
  }

  /**
   * 同步头像到后端数据库
   */
  async syncAvatarToBackend(avatarUrl) {
    try {
      console.log('🔧 [Avatar Sync Debug] 开始同步头像到后端:', avatarUrl);

      // 获取用户API模块
      const userAPI = require('../api/user.js');

      // 调用后端更新接口，只更新头像字段
      const updateData = {
        avatar_url: avatarUrl,
      };

      console.log('🔧 [Avatar Sync Debug] 发送更新数据:', updateData);

      const response = await userAPI.updateProfile(updateData);

      console.log('🔧 [Avatar Sync Debug] 后端响应:', response);

      // 判断响应是否成功：检查状态码 200-299
      const isSuccess = response.statusCode >= 200 && response.statusCode < 300;

      if (isSuccess) {
        console.log('🔧 [Avatar Sync Debug] 头像同步到后端成功');

        // 强制刷新用户信息以确保数据一致性
        try {
          console.log('🔧 [Avatar Sync Debug] 准备触发用户信息同步...');

          // 使用同步管理器触发手动同步
          const { syncManager } = require('./sync-manager.js');
          await syncManager.manualSyncUserInfo();

          console.log('🔧 [Avatar Sync Debug] 用户信息同步完成');
        } catch (refreshError) {
          console.warn('🔧 [Avatar Sync Debug] 用户信息同步失败:', refreshError);
        }
      } else {
        console.error('🔧 [Avatar Sync Debug] 头像同步到后端失败:', response.message);
      }
    } catch (error) {
      console.error('🔧 [Avatar Sync Debug] 头像同步到后端异常:', error);
      // 不抛出错误，避免影响用户体验
    }
  }

  /**
   * 更新本地用户头像
   */
  async updateLocalUserAvatar(avatarUrl) {
    try {
      const currentUserInfo = await authManager.getUserInfo();
      const updatedUserInfo = {
        ...currentUserInfo,
        avatarUrl: avatarUrl,
        avatar_url: avatarUrl, // 兼容后端字段名
        lastUpdated: Date.now(),
      };

      await authManager.updateUserInfo(updatedUserInfo);
      console.log('本地用户头像已更新:', avatarUrl);
    } catch (error) {
      console.error('更新本地用户头像失败:', error);
    }
  }

  /**
   * 获取文件扩展名
   */
  getFileExtension(filePath) {
    const lastDotIndex = filePath.lastIndexOf('.');
    return lastDotIndex > -1 ? filePath.substring(lastDotIndex + 1) : '';
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + sizes[i];
  }

  /**
   * 处理上传错误
   */
  handleUploadError(error) {
    let message = '头像上传失败';

    if (error.statusCode) {
      switch (error.statusCode) {
        case 400:
          message = '图片格式不正确';
          break;
        case 401:
          message = '登录已过期，请重新登录';
          break;
        case 413:
          message = '图片文件过大';
          break;
        case 429:
          message = '上传过于频繁，请稍后再试';
          break;
        case 500:
          message = '服务器错误，请稍后重试';
          break;
        default:
          if (error.message) {
            message = error.message;
          }
      }
    } else if (error.errMsg) {
      if (error.errMsg.includes('fail')) {
        message = '上传失败，请检查网络连接';
      }
    }

    errorToast.show(message);
  }

  /**
   * 预览头像
   */
  previewAvatar(avatarUrl) {
    if (!avatarUrl || avatarUrl.includes('default-avatar')) {
      wx.showToast({
        title: '暂无头像',
        icon: 'none',
      });
      return;
    }

    wx.previewImage({
      urls: [avatarUrl],
      current: avatarUrl,
      fail: () => {
        wx.showToast({
          title: '预览失败',
          icon: 'error',
        });
      },
    });
  }

  /**
   * 删除头像（恢复默认）
   */
  async deleteAvatar() {
    try {
      wx.showLoading({
        title: '删除中...',
        mask: true,
      });

      // 调用后端删除头像接口
      const response = await api.delete('/auth/avatar');

      // 判断响应是否成功：检查状态码 200-299
      const isSuccess = response.statusCode >= 200 && response.statusCode < 300;

      if (isSuccess) {
        // 更新本地用户信息
        await this.updateLocalUserAvatar('/assets/images/default-avatar.png');

        wx.showToast({
          title: '头像已删除',
          icon: 'success',
        });

        return true;
      } else {
        throw new Error(response.data?.message || response.message || '删除失败');
      }
    } catch (error) {
      console.error('删除头像失败:', error);
      errorToast.show('删除失败，请稍后重试');
      return false;
    } finally {
      wx.hideLoading();
    }
  }
}

// 创建单例实例
const avatarUploadManager = new AvatarUploadManager();

module.exports = {
  avatarUploadManager,
  AvatarUploadManager,
};

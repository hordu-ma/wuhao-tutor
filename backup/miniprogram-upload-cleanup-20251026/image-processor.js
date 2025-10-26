// utils/image-processor.js - 图片处理工具

/**
 * 图片压缩和优化工具类
 */
class ImageProcessor {
  constructor() {
    // 默认配置
    this.defaultConfig = {
      maxWidth: 1080,      // 最大宽度
      maxHeight: 1920,     // 最大高度
      quality: 0.8,        // 压缩质量 (0.1-1.0)
      maxSizeKB: 500,      // 最大文件大小(KB)
      format: 'jpg',       // 输出格式
    };
  }

  /**
   * 压缩图片
   * @param {string} filePath - 原始图片路径
   * @param {Object} options - 压缩选项
   * @returns {Promise<Object>} 压缩结果
   */
  async compressImage(filePath, options = {}) {
    const config = { ...this.defaultConfig, ...options };

    try {
      // 获取图片信息
      const imageInfo = await this.getImageInfo(filePath);

      // 计算目标尺寸
      const targetSize = this.calculateTargetSize(
        imageInfo.width,
        imageInfo.height,
        config.maxWidth,
        config.maxHeight
      );

      // 压缩图片
      const compressedPath = await this.performCompress(filePath, {
        ...config,
        width: targetSize.width,
        height: targetSize.height,
      });

      // 获取压缩后的文件信息
      const compressedInfo = await this.getFileInfo(compressedPath);

      return {
        success: true,
        originalPath: filePath,
        compressedPath,
        originalSize: imageInfo.fileSize || 0,
        compressedSize: compressedInfo.size,
        compressionRatio: this.calculateCompressionRatio(
          imageInfo.fileSize || 0,
          compressedInfo.size
        ),
        dimensions: {
          original: { width: imageInfo.width, height: imageInfo.height },
          compressed: targetSize,
        },
      };
    } catch (error) {
      console.error('图片压缩失败:', error);
      return {
        success: false,
        error: error.message,
        originalPath: filePath,
      };
    }
  }

  /**
   * 批量压缩图片
   * @param {Array<string>} filePaths - 图片路径数组
   * @param {Object} options - 压缩选项
   * @returns {Promise<Array>} 批量压缩结果
   */
  async batchCompressImages(filePaths, options = {}) {
    const results = [];

    for (let i = 0; i < filePaths.length; i++) {
      const filePath = filePaths[i];

      try {
        // 显示压缩进度
        if (options.onProgress) {
          options.onProgress({
            current: i + 1,
            total: filePaths.length,
            percentage: Math.round(((i + 1) / filePaths.length) * 100),
            currentFile: filePath,
          });
        }

        const result = await this.compressImage(filePath, options);
        results.push(result);

        // 添加延迟避免过快处理
        if (i < filePaths.length - 1) {
          await this.delay(100);
        }
      } catch (error) {
        console.error(`压缩图片 ${filePath} 失败:`, error);
        results.push({
          success: false,
          error: error.message,
          originalPath: filePath,
        });
      }
    }

    return results;
  }

  /**
   * 获取图片信息
   * @param {string} filePath - 图片路径
   * @returns {Promise<Object>} 图片信息
   */
  getImageInfo(filePath) {
    return new Promise((resolve, reject) => {
      wx.getImageInfo({
        src: filePath,
        success: (res) => {
          resolve({
            width: res.width,
            height: res.height,
            path: res.path,
            orientation: res.orientation || 'up',
            type: res.type || 'unknown',
            fileSize: res.fileSize,
          });
        },
        fail: (error) => {
          reject(new Error(`获取图片信息失败: ${error.errMsg}`));
        },
      });
    });
  }

  /**
   * 获取文件信息
   * @param {string} filePath - 文件路径
   * @returns {Promise<Object>} 文件信息
   */
  getFileInfo(filePath) {
    return new Promise((resolve, reject) => {
      wx.getFileInfo({
        filePath,
        success: (res) => {
          resolve({
            size: res.size,
            createTime: res.createTime,
          });
        },
        fail: (error) => {
          reject(new Error(`获取文件信息失败: ${error.errMsg}`));
        },
      });
    });
  }

  /**
   * 执行图片压缩
   * @param {string} src - 源图片路径
   * @param {Object} config - 压缩配置
   * @returns {Promise<string>} 压缩后的图片路径
   */
  performCompress(src, config) {
    return new Promise((resolve, reject) => {
      wx.compressImage({
        src,
        quality: Math.round(config.quality * 100),
        compressedWidth: config.width,
        compressedHeight: config.height,
        success: (res) => {
          resolve(res.tempFilePath);
        },
        fail: (error) => {
          reject(new Error(`图片压缩失败: ${error.errMsg}`));
        },
      });
    });
  }

  /**
   * 计算目标尺寸
   * @param {number} originalWidth - 原始宽度
   * @param {number} originalHeight - 原始高度
   * @param {number} maxWidth - 最大宽度
   * @param {number} maxHeight - 最大高度
   * @returns {Object} 目标尺寸
   */
  calculateTargetSize(originalWidth, originalHeight, maxWidth, maxHeight) {
    let targetWidth = originalWidth;
    let targetHeight = originalHeight;

    // 如果原始尺寸已经符合要求，直接返回
    if (targetWidth <= maxWidth && targetHeight <= maxHeight) {
      return { width: targetWidth, height: targetHeight };
    }

    // 计算缩放比例
    const widthRatio = maxWidth / originalWidth;
    const heightRatio = maxHeight / originalHeight;
    const ratio = Math.min(widthRatio, heightRatio);

    targetWidth = Math.round(originalWidth * ratio);
    targetHeight = Math.round(originalHeight * ratio);

    return { width: targetWidth, height: targetHeight };
  }

  /**
   * 计算压缩比例
   * @param {number} originalSize - 原始大小
   * @param {number} compressedSize - 压缩后大小
   * @returns {number} 压缩比例(百分比)
   */
  calculateCompressionRatio(originalSize, compressedSize) {
    if (originalSize === 0) return 0;
    return Math.round(((originalSize - compressedSize) / originalSize) * 100);
  }

  /**
   * 格式化文件大小
   * @param {number} bytes - 字节数
   * @returns {string} 格式化后的大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 检查图片是否需要压缩
   * @param {string} filePath - 图片路径
   * @param {Object} options - 检查选项
   * @returns {Promise<Object>} 检查结果
   */
  async shouldCompress(filePath, options = {}) {
    try {
      const imageInfo = await this.getImageInfo(filePath);
      const fileInfo = await this.getFileInfo(filePath);

      const config = { ...this.defaultConfig, ...options };

      const needsResize = imageInfo.width > config.maxWidth ||
        imageInfo.height > config.maxHeight;

      const needsSizeReduction = (fileInfo.size / 1024) > config.maxSizeKB;

      return {
        shouldCompress: needsResize || needsSizeReduction,
        reasons: {
          oversized: needsResize,
          tooLarge: needsSizeReduction,
        },
        currentSize: fileInfo.size,
        currentDimensions: {
          width: imageInfo.width,
          height: imageInfo.height,
        },
        limits: {
          maxSizeKB: config.maxSizeKB,
          maxWidth: config.maxWidth,
          maxHeight: config.maxHeight,
        },
      };
    } catch (error) {
      console.error('检查图片失败:', error);
      return {
        shouldCompress: true, // 默认建议压缩
        error: error.message,
      };
    }
  }

  /**
   * 优化图片方向
   * @param {string} filePath - 图片路径
   * @returns {Promise<string>} 处理后的图片路径
   */
  async correctImageOrientation(filePath) {
    try {
      const imageInfo = await this.getImageInfo(filePath);

      // 如果方向正常，直接返回原路径
      if (!imageInfo.orientation || imageInfo.orientation === 'up') {
        return filePath;
      }

      // 根据方向进行旋转矫正
      return await this.rotateImage(filePath, imageInfo.orientation);
    } catch (error) {
      console.error('矫正图片方向失败:', error);
      return filePath; // 失败时返回原路径
    }
  }

  /**
   * 旋转图片
   * @param {string} filePath - 图片路径
   * @param {string} orientation - 图片方向
   * @returns {Promise<string>} 旋转后的图片路径
   */
  rotateImage(filePath, orientation) {
    return new Promise((resolve, reject) => {
      const canvas = wx.createCanvasContext('image-processor-canvas');

      wx.getImageInfo({
        src: filePath,
        success: (imageInfo) => {
          let { width, height } = imageInfo;
          let rotation = 0;

          // 根据orientation确定旋转角度
          switch (orientation) {
            case 'down':
              rotation = 180;
              break;
            case 'left':
              rotation = 90;
              [width, height] = [height, width];
              break;
            case 'right':
              rotation = -90;
              [width, height] = [height, width];
              break;
            default:
              resolve(filePath);
              return;
          }

          // 设置画布大小
          canvas.drawImage(filePath, 0, 0, width, height);

          wx.canvasToTempFilePath({
            canvasId: 'image-processor-canvas',
            success: (res) => {
              resolve(res.tempFilePath);
            },
            fail: (error) => {
              reject(new Error(`图片旋转失败: ${error.errMsg}`));
            },
          });
        },
        fail: (error) => {
          reject(new Error(`获取图片信息失败: ${error.errMsg}`));
        },
      });
    });
  }

  /**
   * 生成图片预览信息
   * @param {string} filePath - 图片路径
   * @returns {Promise<Object>} 预览信息
   */
  async generatePreviewInfo(filePath) {
    try {
      const [imageInfo, fileInfo] = await Promise.all([
        this.getImageInfo(filePath),
        this.getFileInfo(filePath),
      ]);

      return {
        path: filePath,
        width: imageInfo.width,
        height: imageInfo.height,
        size: fileInfo.size,
        formattedSize: this.formatFileSize(fileInfo.size),
        aspectRatio: (imageInfo.width / imageInfo.height).toFixed(2),
        orientation: imageInfo.orientation || 'up',
        type: imageInfo.type || 'unknown',
        isLandscape: imageInfo.width > imageInfo.height,
        isPortrait: imageInfo.height > imageInfo.width,
        isSquare: imageInfo.width === imageInfo.height,
      };
    } catch (error) {
      console.error('生成预览信息失败:', error);
      return {
        path: filePath,
        error: error.message,
      };
    }
  }

  /**
   * 延迟工具函数
   * @param {number} ms - 延迟毫秒数
   * @returns {Promise} Promise对象
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 清理临时文件
   * @param {Array<string>} filePaths - 文件路径数组
   */
  async cleanupTempFiles(filePaths) {
    if (!Array.isArray(filePaths)) {
      filePaths = [filePaths];
    }

    for (const filePath of filePaths) {
      try {
        if (filePath && filePath.includes('tmp_')) {
          await wx.removeSavedFile({ filePath });
        }
      } catch (error) {
        console.warn('清理临时文件失败:', filePath, error);
      }
    }
  }
}

// 创建单例实例
const imageProcessor = new ImageProcessor();

module.exports = imageProcessor;

// components/image-cropper/index.js - 图片裁剪组件

Component({
  /**
   * 组件的属性列表
   */
  properties: {
    // 原始图片路径
    imagePath: {
      type: String,
      value: '',
    },
    // 显示裁剪器
    show: {
      type: Boolean,
      value: false,
    },
    // 裁剪比例 (可选: free, 1:1, 4:3, 16:9)
    aspectRatio: {
      type: String,
      value: 'free',
    },
    // 最大宽度
    maxWidth: {
      type: Number,
      value: 1080,
    },
    // 最大高度
    maxHeight: {
      type: Number,
      value: 1920,
    },
    // 输出质量 (0-1)
    quality: {
      type: Number,
      value: 0.9,
    },
  },

  /**
   * 组件的初始数据
   */
  data: {
    // Canvas上下文
    ctx: null,
    // 图片信息
    imageInfo: null,
    // 裁剪区域
    cropArea: {
      x: 0,
      y: 0,
      width: 300,
      height: 300,
    },
    // 画布尺寸
    canvasWidth: 0,
    canvasHeight: 0,
    // 图片在画布中的位置和尺寸
    displayImage: {
      x: 0,
      y: 0,
      width: 0,
      height: 0,
    },
    // 缩放比例
    scale: 1,
    // 旋转角度
    rotation: 0,
    // 触摸状态
    touching: false,
    touchStartX: 0,
    touchStartY: 0,
    // 操作模式: move(移动), resize(调整大小), rotate(旋转)
    mode: 'move',
    // 工具栏选项
    tools: [
      { id: 'rotate-left', icon: '↺', label: '左转' },
      { id: 'rotate-right', icon: '↻', label: '右转' },
      { id: 'flip-h', icon: '⇄', label: '水平翻转' },
      { id: 'flip-v', icon: '⇅', label: '垂直翻转' },
      { id: 'reset', icon: '⟲', label: '重置' },
    ],
    // 比例选项
    ratioOptions: [
      { value: 'free', label: '自由' },
      { value: '1:1', label: '1:1' },
      { value: '4:3', label: '4:3' },
      { value: '16:9', label: '16:9' },
    ],
    // 处理状态
    processing: false,
  },

  lifetimes: {
    attached() {
      this.initCanvas();
    },
  },

  observers: {
    'imagePath, show': function (imagePath, show) {
      if (show && imagePath) {
        this.loadImage();
      }
    },
  },

  /**
   * 组件的方法列表
   */
  methods: {
    /**
     * 初始化Canvas
     */
    initCanvas() {
      const query = this.createSelectorQuery();
      query
        .select('#cropperCanvas')
        .fields({ node: true, size: true })
        .exec(res => {
          if (res[0]) {
            const canvas = res[0].node;
            const ctx = canvas.getContext('2d');

            const dpr = wx.getSystemInfoSync().pixelRatio;
            canvas.width = res[0].width * dpr;
            canvas.height = res[0].height * dpr;
            ctx.scale(dpr, dpr);

            this.setData({
              ctx,
              canvasWidth: res[0].width,
              canvasHeight: res[0].height,
            });

            this.canvas = canvas;
          }
        });
    },

    /**
     * 加载图片
     */
    async loadImage() {
      try {
        const imageInfo = await this.getImageInfo(this.data.imagePath);

        // 计算图片在画布中的显示尺寸
        const displayImage = this.calculateImageSize(
          imageInfo.width,
          imageInfo.height,
          this.data.canvasWidth,
          this.data.canvasHeight,
        );

        // 初始化裁剪区域（居中，60%大小）
        const cropSize = Math.min(displayImage.width, displayImage.height) * 0.6;
        const cropArea = {
          x: displayImage.x + (displayImage.width - cropSize) / 2,
          y: displayImage.y + (displayImage.height - cropSize) / 2,
          width: cropSize,
          height: cropSize,
        };

        this.setData({
          imageInfo,
          displayImage,
          cropArea,
          scale: 1,
          rotation: 0,
        });

        this.drawCanvas();
      } catch (error) {
        console.error('加载图片失败:', error);
        wx.showToast({
          title: '加载图片失败',
          icon: 'none',
        });
      }
    },

    /**
     * 获取图片信息
     */
    getImageInfo(path) {
      return new Promise((resolve, reject) => {
        wx.getImageInfo({
          src: path,
          success: resolve,
          fail: reject,
        });
      });
    },

    /**
     * 计算图片显示尺寸
     */
    calculateImageSize(imgWidth, imgHeight, canvasWidth, canvasHeight) {
      const padding = 40;
      const maxWidth = canvasWidth - padding * 2;
      const maxHeight = canvasHeight - padding * 2;

      let width = imgWidth;
      let height = imgHeight;
      const ratio = imgWidth / imgHeight;

      if (width > maxWidth) {
        width = maxWidth;
        height = width / ratio;
      }

      if (height > maxHeight) {
        height = maxHeight;
        width = height * ratio;
      }

      const x = (canvasWidth - width) / 2;
      const y = (canvasHeight - height) / 2;

      return { x, y, width, height };
    },

    /**
     * 绘制画布
     */
    async drawCanvas() {
      const { ctx, imageInfo, displayImage, cropArea, rotation, scale } = this.data;
      if (!ctx || !imageInfo) return;

      // 清空画布
      ctx.clearRect(0, 0, this.data.canvasWidth, this.data.canvasHeight);

      // 保存上下文状态
      ctx.save();

      // 绘制背景遮罩
      ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
      ctx.fillRect(0, 0, this.data.canvasWidth, this.data.canvasHeight);

      // 绘制裁剪区域（透明）
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillRect(cropArea.x, cropArea.y, cropArea.width, cropArea.height);
      ctx.globalCompositeOperation = 'source-over';

      // 绘制图片
      const img = this.canvas.createImage();
      img.src = imageInfo.path;

      await new Promise(resolve => {
        img.onload = resolve;
      });

      // 应用变换
      ctx.save();
      const centerX = displayImage.x + displayImage.width / 2;
      const centerY = displayImage.y + displayImage.height / 2;

      ctx.translate(centerX, centerY);
      ctx.rotate((rotation * Math.PI) / 180);
      ctx.scale(scale, scale);
      ctx.translate(-centerX, -centerY);

      ctx.drawImage(img, displayImage.x, displayImage.y, displayImage.width, displayImage.height);

      ctx.restore();

      // 绘制裁剪框
      this.drawCropFrame(ctx, cropArea);

      ctx.restore();
    },

    /**
     * 绘制裁剪框
     */
    drawCropFrame(ctx, area) {
      // 边框
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.strokeRect(area.x, area.y, area.width, area.height);

      // 九宫格辅助线
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
      ctx.lineWidth = 1;

      // 水平线
      ctx.beginPath();
      ctx.moveTo(area.x, area.y + area.height / 3);
      ctx.lineTo(area.x + area.width, area.y + area.height / 3);
      ctx.moveTo(area.x, area.y + (area.height * 2) / 3);
      ctx.lineTo(area.x + area.width, area.y + (area.height * 2) / 3);
      ctx.stroke();

      // 垂直线
      ctx.beginPath();
      ctx.moveTo(area.x + area.width / 3, area.y);
      ctx.lineTo(area.x + area.width / 3, area.y + area.height);
      ctx.moveTo(area.x + (area.width * 2) / 3, area.y);
      ctx.lineTo(area.x + (area.width * 2) / 3, area.y + area.height);
      ctx.stroke();

      // 角点
      const cornerSize = 20;
      ctx.strokeStyle = '#409eff';
      ctx.lineWidth = 3;

      // 左上
      ctx.beginPath();
      ctx.moveTo(area.x, area.y + cornerSize);
      ctx.lineTo(area.x, area.y);
      ctx.lineTo(area.x + cornerSize, area.y);
      ctx.stroke();

      // 右上
      ctx.beginPath();
      ctx.moveTo(area.x + area.width - cornerSize, area.y);
      ctx.lineTo(area.x + area.width, area.y);
      ctx.lineTo(area.x + area.width, area.y + cornerSize);
      ctx.stroke();

      // 左下
      ctx.beginPath();
      ctx.moveTo(area.x, area.y + area.height - cornerSize);
      ctx.lineTo(area.x, area.y + area.height);
      ctx.lineTo(area.x + cornerSize, area.y + area.height);
      ctx.stroke();

      // 右下
      ctx.beginPath();
      ctx.moveTo(area.x + area.width - cornerSize, area.y + area.height);
      ctx.lineTo(area.x + area.width, area.y + area.height);
      ctx.lineTo(area.x + area.width, area.y + area.height - cornerSize);
      ctx.stroke();
    },

    /**
     * 触摸开始
     */
    onTouchStart(e) {
      const touch = e.touches[0];
      this.setData({
        touching: true,
        touchStartX: touch.x,
        touchStartY: touch.y,
      });
    },

    /**
     * 触摸移动
     */
    onTouchMove(e) {
      if (!this.data.touching) return;

      const touch = e.touches[0];
      const deltaX = touch.x - this.data.touchStartX;
      const deltaY = touch.y - this.data.touchStartY;

      // 移动裁剪框
      const cropArea = { ...this.data.cropArea };
      cropArea.x += deltaX;
      cropArea.y += deltaY;

      // 限制在图片范围内
      const { displayImage } = this.data;
      cropArea.x = Math.max(
        displayImage.x,
        Math.min(cropArea.x, displayImage.x + displayImage.width - cropArea.width),
      );
      cropArea.y = Math.max(
        displayImage.y,
        Math.min(cropArea.y, displayImage.y + displayImage.height - cropArea.height),
      );

      this.setData({
        cropArea,
        touchStartX: touch.x,
        touchStartY: touch.y,
      });

      this.drawCanvas();
    },

    /**
     * 触摸结束
     */
    onTouchEnd() {
      this.setData({ touching: false });
    },

    /**
     * 工具操作
     */
    onToolClick(e) {
      const { tool } = e.currentTarget.dataset;

      switch (tool) {
        case 'rotate-left':
          this.rotate(-90);
          break;
        case 'rotate-right':
          this.rotate(90);
          break;
        case 'flip-h':
          this.flipHorizontal();
          break;
        case 'flip-v':
          this.flipVertical();
          break;
        case 'reset':
          this.reset();
          break;
      }
    },

    /**
     * 旋转图片
     */
    rotate(degree) {
      const rotation = (this.data.rotation + degree) % 360;
      this.setData({ rotation });
      this.drawCanvas();
    },

    /**
     * 水平翻转
     */
    flipHorizontal() {
      // 实现水平翻转逻辑
      wx.showToast({ title: '水平翻转', icon: 'none' });
    },

    /**
     * 垂直翻转
     */
    flipVertical() {
      // 实现垂直翻转逻辑
      wx.showToast({ title: '垂直翻转', icon: 'none' });
    },

    /**
     * 重置
     */
    reset() {
      this.loadImage();
    },

    /**
     * 改变裁剪比例
     */
    onRatioChange(e) {
      const ratio = e.currentTarget.dataset.ratio;
      this.setData({ aspectRatio: ratio });
      this.adjustCropArea(ratio);
    },

    /**
     * 调整裁剪区域比例
     */
    adjustCropArea(ratio) {
      const { cropArea, displayImage } = this.data;
      const newArea = { ...cropArea };

      if (ratio === 'free') {
        // 自由比例，不调整
      } else {
        const [w, h] = ratio.split(':').map(Number);
        const aspectRatio = w / h;

        if (cropArea.width / cropArea.height > aspectRatio) {
          // 宽度过大，调整宽度
          newArea.width = cropArea.height * aspectRatio;
        } else {
          // 高度过大，调整高度
          newArea.height = cropArea.width / aspectRatio;
        }

        // 居中
        newArea.x = cropArea.x + (cropArea.width - newArea.width) / 2;
        newArea.y = cropArea.y + (cropArea.height - newArea.height) / 2;
      }

      this.setData({ cropArea: newArea });
      this.drawCanvas();
    },

    /**
     * 取消裁剪
     */
    onCancel() {
      this.triggerEvent('cancel');
    },

    /**
     * 确认裁剪
     */
    async onConfirm() {
      try {
        this.setData({ processing: true });

        // 裁剪图片
        const croppedImage = await this.cropImage();

        this.triggerEvent('confirm', {
          originalPath: this.data.imagePath,
          croppedPath: croppedImage.path,
          width: croppedImage.width,
          height: croppedImage.height,
        });
      } catch (error) {
        console.error('裁剪失败:', error);
        wx.showToast({
          title: '裁剪失败',
          icon: 'none',
        });
      } finally {
        this.setData({ processing: false });
      }
    },

    /**
     * 执行图片裁剪
     */
    cropImage() {
      return new Promise((resolve, reject) => {
        const { imageInfo, cropArea, displayImage, scale, rotation } = this.data;

        // 计算实际裁剪区域（相对于原图）
        const scaleX = imageInfo.width / displayImage.width;
        const scaleY = imageInfo.height / displayImage.height;

        const realCropArea = {
          x: (cropArea.x - displayImage.x) * scaleX,
          y: (cropArea.y - displayImage.y) * scaleY,
          width: cropArea.width * scaleX,
          height: cropArea.height * scaleY,
        };

        // 使用Canvas API裁剪
        const canvas = this.canvas;
        canvas.width = realCropArea.width;
        canvas.height = realCropArea.height;

        const ctx = canvas.getContext('2d');
        const img = canvas.createImage();
        img.src = imageInfo.path;

        img.onload = () => {
          ctx.drawImage(
            img,
            realCropArea.x,
            realCropArea.y,
            realCropArea.width,
            realCropArea.height,
            0,
            0,
            realCropArea.width,
            realCropArea.height,
          );

          wx.canvasToTempFilePath(
            {
              canvas: canvas,
              quality: this.data.quality,
              success: res => {
                resolve({
                  path: res.tempFilePath,
                  width: realCropArea.width,
                  height: realCropArea.height,
                });
              },
              fail: reject,
            },
            this,
          );
        };

        img.onerror = reject;
      });
    },
  },
});

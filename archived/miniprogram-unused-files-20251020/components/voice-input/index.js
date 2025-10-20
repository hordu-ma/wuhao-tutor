Component({
  /**
   * 语音输入组件
   * 支持录音、识别、播放等功能
   */
  properties: {
    // 最大录音时长（秒）
    maxDuration: {
      type: Number,
      value: 60,
    },
    // 是否启用音频播放
    enablePlayback: {
      type: Boolean,
      value: true,
    },
    // 录音质量
    quality: {
      type: String,
      value: 'high', // high | standard | low
    },
    // 是否自动开始识别
    autoRecognize: {
      type: Boolean,
      value: true,
    },
  },

  data: {
    // 录音状态
    recordStatus: 'idle', // idle | recording | processing | completed | error
    // 录音时长
    recordDuration: 0,
    // 录音文件路径
    recordPath: '',
    // 识别结果
    recognizeText: '',
    // 错误信息
    errorMessage: '',
    // 音量大小
    volume: 0,
    // 定时器
    timer: null,
    // 录音管理器
    recorderManager: null,
    // 播放管理器
    audioContext: null,
  },

  lifetimes: {
    attached() {
      this.initRecorder();
      this.initAudio();
    },

    detached() {
      this.cleanup();
    },
  },

  methods: {
    /**
     * 初始化录音管理器
     */
    initRecorder() {
      const recorderManager = wx.getRecorderManager();
      
      recorderManager.onStart(() => {
        console.log('录音开始');
        this.setData({ recordStatus: 'recording' });
        this.startTimer();
      });

      recorderManager.onPause(() => {
        console.log('录音暂停');
      });

      recorderManager.onStop((res) => {
        console.log('录音结束', res);
        this.setData({
          recordStatus: 'processing',
          recordPath: res.tempFilePath,
          recordDuration: res.duration / 1000,
        });
        this.stopTimer();
        
        if (this.properties.autoRecognize) {
          this.startRecognize();
        } else {
          this.setData({ recordStatus: 'completed' });
          this.triggerRecordComplete();
        }
      });

      recorderManager.onFrameRecorded((res) => {
        // 获取音量大小
        const volume = this.calculateVolume(res.frameBuffer);
        this.setData({ volume });
      });

      recorderManager.onError((res) => {
        console.error('录音错误', res);
        this.setData({
          recordStatus: 'error',
          errorMessage: '录音失败，请重试',
        });
        this.stopTimer();
      });

      this.setData({ recorderManager });
    },

    /**
     * 初始化音频播放
     */
    initAudio() {
      const audioContext = wx.createInnerAudioContext();
      
      audioContext.onPlay(() => {
        console.log('开始播放');
      });

      audioContext.onEnded(() => {
        console.log('播放结束');
      });

      audioContext.onError((res) => {
        console.error('播放错误', res);
        wx.showToast({
          title: '播放失败',
          icon: 'error',
        });
      });

      this.setData({ audioContext });
    },

    /**
     * 开始录音
     */
    startRecord() {
      // 检查录音权限
      wx.getSetting({
        success: (res) => {
          if (res.authSetting['scope.record'] !== false) {
            this.doStartRecord();
          } else {
            this.requestRecordPermission();
          }
        },
      });
    },

    /**
     * 请求录音权限
     */
    requestRecordPermission() {
      wx.authorize({
        scope: 'scope.record',
        success: () => {
          this.doStartRecord();
        },
        fail: () => {
          wx.showModal({
            title: '需要录音权限',
            content: '请在设置中开启录音权限后重试',
            showCancel: false,
          });
        },
      });
    },

    /**
     * 执行录音
     */
    doStartRecord() {
      const { maxDuration, quality } = this.properties;
      
      const options = {
        duration: maxDuration * 1000,
        sampleRate: quality === 'high' ? 44100 : quality === 'standard' ? 16000 : 8000,
        numberOfChannels: 1,
        encodeBitRate: quality === 'high' ? 192000 : quality === 'standard' ? 96000 : 48000,
        format: 'mp3',
        frameSize: 50,
      };

      this.data.recorderManager.start(options);
      this.setData({
        recordDuration: 0,
        volume: 0,
        recognizeText: '',
        errorMessage: '',
      });
    },

    /**
     * 停止录音
     */
    stopRecord() {
      this.data.recorderManager.stop();
    },

    /**
     * 取消录音
     */
    cancelRecord() {
      this.data.recorderManager.stop();
      this.setData({
        recordStatus: 'idle',
        recordDuration: 0,
        recordPath: '',
        recognizeText: '',
        errorMessage: '',
      });
      this.stopTimer();
    },

    /**
     * 重新录音
     */
    retryRecord() {
      this.setData({
        recordStatus: 'idle',
        recordDuration: 0,
        recordPath: '',
        recognizeText: '',
        errorMessage: '',
      });
    },

    /**
     * 播放录音
     */
    playRecord() {
      if (!this.data.recordPath) return;
      
      this.data.audioContext.src = this.data.recordPath;
      this.data.audioContext.play();
    },

    /**
     * 开始语音识别
     */
    async startRecognize() {
      if (!this.data.recordPath) return;

      try {
        this.setData({ recordStatus: 'processing' });

        // 调用语音识别API
        const result = await this.callRecognizeAPI(this.data.recordPath);
        
        if (result.success) {
          this.setData({
            recordStatus: 'completed',
            recognizeText: result.text,
          });
          this.triggerRecognizeComplete(result.text);
        } else {
          throw new Error(result.message || '识别失败');
        }
      } catch (error) {
        console.error('语音识别失败:', error);
        this.setData({
          recordStatus: 'error',
          errorMessage: error.message || '识别失败，请重试',
        });
      }
    },

    /**
     * 调用语音识别API
     */
    async callRecognizeAPI(audioPath) {
      // 这里应该调用实际的语音识别API
      // 暂时返回模拟结果
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            text: '这是语音识别的结果文本',
            confidence: 0.95,
          });
        }, 2000);
      });
    },

    /**
     * 开始计时
     */
    startTimer() {
      this.data.timer = setInterval(() => {
        const duration = this.data.recordDuration + 0.1;
        this.setData({ recordDuration: duration });
        
        if (duration >= this.properties.maxDuration) {
          this.stopRecord();
        }
      }, 100);
    },

    /**
     * 停止计时
     */
    stopTimer() {
      if (this.data.timer) {
        clearInterval(this.data.timer);
        this.setData({ timer: null });
      }
    },

    /**
     * 计算音量
     */
    calculateVolume(buffer) {
      if (!buffer) return 0;
      
      const data = new Int16Array(buffer);
      let sum = 0;
      
      for (let i = 0; i < data.length; i++) {
        sum += Math.abs(data[i]);
      }
      
      return Math.min(sum / data.length / 1000, 1);
    },

    /**
     * 格式化时间
     */
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },

    /**
     * 清理资源
     */
    cleanup() {
      this.stopTimer();
      
      if (this.data.audioContext) {
        this.data.audioContext.destroy();
      }
    },

    /**
     * 触发录音完成事件
     */
    triggerRecordComplete() {
      this.triggerEvent('recordcomplete', {
        path: this.data.recordPath,
        duration: this.data.recordDuration,
      });
    },

    /**
     * 触发识别完成事件
     */
    triggerRecognizeComplete(text) {
      this.triggerEvent('recognizecomplete', {
        text,
        path: this.data.recordPath,
        duration: this.data.recordDuration,
      });
    },

    /**
     * 触发取消事件
     */
    triggerCancel() {
      this.triggerEvent('cancel');
    },

    /**
     * 触发确认事件
     */
    triggerConfirm() {
      this.triggerEvent('confirm', {
        text: this.data.recognizeText,
        path: this.data.recordPath,
        duration: this.data.recordDuration,
      });
    },

    // 按钮事件处理
    onRecordTap() {
      if (this.data.recordStatus === 'idle') {
        this.startRecord();
      } else if (this.data.recordStatus === 'recording') {
        this.stopRecord();
      }
    },

    onCancelTap() {
      this.cancelRecord();
      this.triggerCancel();
    },

    onRetryTap() {
      this.retryRecord();
    },

    onPlayTap() {
      this.playRecord();
    },

    onConfirmTap() {
      this.triggerConfirm();
    },
  },
});
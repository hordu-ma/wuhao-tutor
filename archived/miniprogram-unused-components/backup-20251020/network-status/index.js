const { networkMonitor } = require('../../utils/network-monitor.js');

Component({
  /**
   * 网络状态显示组件
   * 监控网络状态并给用户友好的提示
   */
  properties: {
    // 是否自动监听网络状态
    autoMonitor: {
      type: Boolean,
      value: true,
    },
    // 显示位置: top | bottom | inline
    position: {
      type: String,
      value: 'top',
    },
    // 是否可关闭
    closable: {
      type: Boolean,
      value: true,
    },
  },

  data: {
    networkType: 'unknown',
    isConnected: true,
    showNotice: false,
    noticeText: '',
    noticeType: 'info', // info | warning | error
  },

  lifetimes: {
    attached() {
      if (this.properties.autoMonitor) {
        this.startMonitoring();
      }
    },

    detached() {
      this.stopMonitoring();
    },
  },

  methods: {
    /**
     * 开始监控网络状态
     */
    startMonitoring() {
      // 获取初始网络状态
      this.checkNetworkStatus();

      // 监听网络状态变化
      wx.onNetworkStatusChange(this.onNetworkChange.bind(this));
    },

    /**
     * 停止监控网络状态
     */
    stopMonitoring() {
      wx.offNetworkStatusChange(this.onNetworkChange);
    },

    /**
     * 检查当前网络状态
     */
    checkNetworkStatus() {
      wx.getNetworkType({
        success: (res) => {
          this.updateNetworkStatus(res.networkType, res.networkType !== 'none');
        },
        fail: () => {
          this.updateNetworkStatus('unknown', false);
        },
      });
    },

    /**
     * 网络状态变化处理
     */
    onNetworkChange(res) {
      this.updateNetworkStatus(res.networkType, res.isConnected);
    },

    /**
     * 更新网络状态显示
     */
    updateNetworkStatus(networkType, isConnected) {
      const oldConnected = this.data.isConnected;
      
      this.setData({
        networkType,
        isConnected,
      });

      // 网络状态变化时的处理
      if (!isConnected) {
        this.showNetworkNotice('网络连接已断开，请检查网络设置', 'error');
      } else if (!oldConnected && isConnected) {
        this.showNetworkNotice('网络连接已恢复', 'info');
        setTimeout(() => {
          this.hideNotice();
        }, 3000);
      } else if (networkType === '2g') {
        this.showNetworkNotice('当前网络较慢，建议切换到WiFi', 'warning');
      } else {
        this.hideNotice();
      }

      // 触发网络状态变化事件
      this.triggerEvent('networkchange', {
        networkType,
        isConnected,
      });
    },

    /**
     * 显示网络提示
     */
    showNetworkNotice(text, type = 'info') {
      this.setData({
        showNotice: true,
        noticeText: text,
        noticeType: type,
      });
    },

    /**
     * 隐藏网络提示
     */
    hideNotice() {
      this.setData({
        showNotice: false,
      });
    },

    /**
     * 关闭提示
     */
    onClose() {
      this.hideNotice();
    },

    /**
     * 点击提示
     */
    onNoticeClick() {
      if (!this.data.isConnected) {
        // 尝试重新连接
        this.checkNetworkStatus();
      }
    },

    /**
     * 获取网络类型描述
     */
    getNetworkTypeDesc(networkType) {
      const typeMap = {
        'wifi': 'WiFi',
        '2g': '2G',
        '3g': '3G',
        '4g': '4G',
        '5g': '5G',
        'none': '无网络',
        'unknown': '未知网络',
      };
      return typeMap[networkType] || '未知网络';
    },

    /**
     * 获取网络状态图标
     */
    getNetworkIcon(networkType, isConnected) {
      if (!isConnected) return '📵';
      
      const iconMap = {
        'wifi': '📶',
        '5g': '📶',
        '4g': '📶',
        '3g': '📶',
        '2g': '📴',
        'unknown': '❓',
      };
      return iconMap[networkType] || '❓';
    },
  },

  observers: {
    'networkType, isConnected'(networkType, isConnected) {
      // 通知网络监控工具
      if (networkMonitor) {
        networkMonitor.updateStatus(networkType, isConnected);
      }
    },
  },
});
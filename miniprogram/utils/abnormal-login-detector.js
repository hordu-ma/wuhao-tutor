/**
 * 异常登录检测系统
 * 监控设备变化、登录频率、地理位置等，检测可疑登录活动
 */

const storage = require('./storage.js');
const { authManager } = require('./auth.js');

/**
 * 异常登录检测器
 */
class AbnormalLoginDetector {
  constructor() {
    this.loginHistoryKey = 'login_history';
    this.deviceInfoKey = 'trusted_devices';
    this.securityEventsKey = 'security_events';
    this.alertConfigKey = 'security_alert_config';
    
    // 默认安全配置
    this.defaultConfig = {
      maxLoginAttemptsPerHour: 10,
      maxDevicesAllowed: 5,
      suspiciousLoginCooldown: 30 * 60 * 1000, // 30分钟
      deviceTrustPeriod: 30 * 24 * 60 * 60 * 1000, // 30天
      enableLocationCheck: false, // 小程序中地理位置检查较为复杂
      enableFrequencyCheck: true,
      enableDeviceCheck: true,
      enableTimePatternCheck: true
    };

    this.init();
  }

  /**
   * 初始化检测器
   */
  async init() {
    try {
      // 加载安全配置
      const config = await storage.get(this.alertConfigKey);
      this.config = { ...this.defaultConfig, ...config };

      console.log('[AbnormalLogin] 异常登录检测器初始化完成');
    } catch (error) {
      console.error('[AbnormalLogin] 初始化失败:', error);
      this.config = this.defaultConfig;
    }
  }

  /**
   * 检测登录是否异常
   * @param {Object} loginInfo - 登录信息
   * @returns {Promise<Object>} 检测结果
   */
  async detectAbnormalLogin(loginInfo) {
    try {
      console.log('[AbnormalLogin] 开始异常登录检测');

      const detectionResults = [];

      // 1. 设备检测
      if (this.config.enableDeviceCheck) {
        const deviceResult = await this.checkDeviceAnomaly(loginInfo);
        if (deviceResult.isAbnormal) {
          detectionResults.push(deviceResult);
        }
      }

      // 2. 频率检测
      if (this.config.enableFrequencyCheck) {
        const frequencyResult = await this.checkLoginFrequency(loginInfo);
        if (frequencyResult.isAbnormal) {
          detectionResults.push(frequencyResult);
        }
      }

      // 3. 时间模式检测
      if (this.config.enableTimePatternCheck) {
        const timePatternResult = await this.checkTimePattern(loginInfo);
        if (timePatternResult.isAbnormal) {
          detectionResults.push(timePatternResult);
        }
      }

      // 4. 综合风险评估
      const riskAssessment = this.assessOverallRisk(detectionResults);

      // 5. 记录检测结果
      await this.recordSecurityEvent(loginInfo, detectionResults, riskAssessment);

      return {
        isAbnormal: detectionResults.length > 0,
        riskLevel: riskAssessment.level,
        riskScore: riskAssessment.score,
        detections: detectionResults,
        recommendations: riskAssessment.recommendations,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error('[AbnormalLogin] 异常登录检测失败:', error);
      return {
        isAbnormal: false,
        riskLevel: 'unknown',
        riskScore: 0,
        detections: [],
        error: error.message
      };
    }
  }

  /**
   * 检测设备异常
   * @param {Object} loginInfo - 登录信息
   * @returns {Promise<Object>} 设备检测结果
   */
  async checkDeviceAnomaly(loginInfo) {
    try {
      const currentDevice = loginInfo.deviceInfo || await this.getCurrentDeviceInfo();
      const trustedDevices = await this.getTrustedDevices();
      const loginHistory = await this.getLoginHistory();

      // 检查是否为新设备
      const isNewDevice = !trustedDevices.some(device => 
        this.isSameDevice(device, currentDevice)
      );

      // 检查设备数量是否超限
      const uniqueDevices = this.getUniqueDevicesFromHistory(loginHistory);
      const deviceCountExceeded = uniqueDevices.length > this.config.maxDevicesAllowed;

      // 检查设备信息变化
      const recentLogins = loginHistory.slice(-5); // 最近5次登录
      const deviceChanges = this.analyzeDeviceChanges(recentLogins, currentDevice);

      const anomalies = [];

      if (isNewDevice) {
        anomalies.push({
          type: 'new_device',
          description: '检测到新设备登录',
          severity: 'medium',
          details: {
            currentDevice: this.sanitizeDeviceInfo(currentDevice),
            isFirstTime: trustedDevices.length === 0
          }
        });
      }

      if (deviceCountExceeded) {
        anomalies.push({
          type: 'too_many_devices',
          description: '登录设备数量过多',
          severity: 'high',
          details: {
            deviceCount: uniqueDevices.length,
            maxAllowed: this.config.maxDevicesAllowed
          }
        });
      }

      if (deviceChanges.hasSignificantChange) {
        anomalies.push({
          type: 'device_change',
          description: '设备信息发生显著变化',
          severity: 'medium',
          details: deviceChanges.changes
        });
      }

      return {
        isAbnormal: anomalies.length > 0,
        type: 'device_anomaly',
        anomalies,
        deviceInfo: this.sanitizeDeviceInfo(currentDevice),
        trustedDeviceCount: trustedDevices.length
      };

    } catch (error) {
      console.error('[AbnormalLogin] 设备异常检测失败:', error);
      return {
        isAbnormal: false,
        type: 'device_anomaly',
        error: error.message
      };
    }
  }

  /**
   * 检测登录频率异常
   * @param {Object} loginInfo - 登录信息
   * @returns {Promise<Object>} 频率检测结果
   */
  async checkLoginFrequency(loginInfo) {
    try {
      const loginHistory = await this.getLoginHistory();
      const now = Date.now();
      const oneHour = 60 * 60 * 1000;

      // 最近一小时的登录次数
      const recentLogins = loginHistory.filter(login => 
        (now - login.timestamp) < oneHour
      );

      const loginCount = recentLogins.length;
      const isFrequencyAbnormal = loginCount > this.config.maxLoginAttemptsPerHour;

      // 分析登录间隔
      const intervals = this.calculateLoginIntervals(loginHistory.slice(-10));
      const avgInterval = intervals.length > 0 ? 
        intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length : 0;

      // 检测短时间内大量登录
      const shortIntervals = intervals.filter(interval => interval < 60 * 1000); // 1分钟内
      const hasBurstActivity = shortIntervals.length > 3;

      const anomalies = [];

      if (isFrequencyAbnormal) {
        anomalies.push({
          type: 'high_frequency',
          description: '登录频率过高',
          severity: 'high',
          details: {
            loginCount,
            timeWindow: '1小时',
            maxAllowed: this.config.maxLoginAttemptsPerHour
          }
        });
      }

      if (hasBurstActivity) {
        anomalies.push({
          type: 'burst_activity',
          description: '检测到短时间内频繁登录',
          severity: 'medium',
          details: {
            shortIntervalCount: shortIntervals.length,
            avgInterval: Math.round(avgInterval / 1000) + '秒'
          }
        });
      }

      return {
        isAbnormal: anomalies.length > 0,
        type: 'frequency_anomaly',
        anomalies,
        stats: {
          recentLoginCount: loginCount,
          averageInterval: avgInterval,
          shortIntervalCount: shortIntervals.length
        }
      };

    } catch (error) {
      console.error('[AbnormalLogin] 登录频率检测失败:', error);
      return {
        isAbnormal: false,
        type: 'frequency_anomaly',
        error: error.message
      };
    }
  }

  /**
   * 检测时间模式异常
   * @param {Object} loginInfo - 登录信息
   * @returns {Promise<Object>} 时间模式检测结果
   */
  async checkTimePattern(loginInfo) {
    try {
      const loginHistory = await this.getLoginHistory();
      const currentHour = new Date().getHours();

      // 分析历史登录时间模式
      const hourlyStats = this.analyzeHourlyLoginPattern(loginHistory);
      const dailyStats = this.analyzeDailyLoginPattern(loginHistory);

      // 检测异常登录时间
      const isUnusualHour = this.isUnusualLoginTime(currentHour, hourlyStats);
      const isUnusualDay = this.isUnusualLoginDay(new Date().getDay(), dailyStats);

      // 检测夜间登录（23:00 - 06:00）
      const isNightTime = currentHour >= 23 || currentHour <= 6;
      const hasNightTimeActivity = isNightTime && hourlyStats[currentHour] < 2;

      const anomalies = [];

      if (isUnusualHour) {
        anomalies.push({
          type: 'unusual_time',
          description: '非常规时间登录',
          severity: 'low',
          details: {
            currentHour,
            usualHours: Object.keys(hourlyStats)
              .filter(hour => hourlyStats[hour] > 2)
              .join(', ')
          }
        });
      }

      if (hasNightTimeActivity && loginHistory.length > 10) {
        anomalies.push({
          type: 'night_activity',
          description: '检测到夜间登录活动',
          severity: 'low',
          details: {
            loginTime: currentHour + ':00',
            normalPattern: '通常在白天活动'
          }
        });
      }

      return {
        isAbnormal: anomalies.length > 0,
        type: 'time_pattern_anomaly',
        anomalies,
        patterns: {
          hourlyStats: this.getTopLoginHours(hourlyStats),
          currentHour,
          isNightTime
        }
      };

    } catch (error) {
      console.error('[AbnormalLogin] 时间模式检测失败:', error);
      return {
        isAbnormal: false,
        type: 'time_pattern_anomaly',
        error: error.message
      };
    }
  }

  /**
   * 综合风险评估
   * @param {Array} detectionResults - 检测结果数组
   * @returns {Object} 风险评估结果
   */
  assessOverallRisk(detectionResults) {
    let totalScore = 0;
    const recommendations = [];

    detectionResults.forEach(result => {
      result.anomalies?.forEach(anomaly => {
        switch (anomaly.severity) {
          case 'high':
            totalScore += 30;
            recommendations.push('建议立即验证身份');
            break;
          case 'medium':
            totalScore += 15;
            recommendations.push('建议进行额外验证');
            break;
          case 'low':
            totalScore += 5;
            recommendations.push('注意监控账号活动');
            break;
        }
      });
    });

    let level;
    if (totalScore >= 50) {
      level = 'high';
      recommendations.push('建议强制重新认证');
    } else if (totalScore >= 20) {
      level = 'medium';
      recommendations.push('建议启用额外安全措施');
    } else if (totalScore > 0) {
      level = 'low';
      recommendations.push('继续监控');
    } else {
      level = 'normal';
    }

    return {
      score: totalScore,
      level,
      recommendations: [...new Set(recommendations)] // 去重
    };
  }

  /**
   * 记录登录历史
   * @param {Object} loginInfo - 登录信息
   */
  async recordLoginHistory(loginInfo) {
    try {
      const history = await this.getLoginHistory();
      const deviceInfo = loginInfo.deviceInfo || await this.getCurrentDeviceInfo();

      const record = {
        id: Date.now().toString(),
        timestamp: Date.now(),
        deviceInfo: this.sanitizeDeviceInfo(deviceInfo),
        userAgent: loginInfo.userAgent,
        success: loginInfo.success !== false,
        ip: loginInfo.ip || 'unknown',
        location: loginInfo.location,
        sessionId: loginInfo.sessionId
      };

      history.push(record);

      // 只保留最近100条记录
      if (history.length > 100) {
        history.splice(0, history.length - 100);
      }

      await storage.set(this.loginHistoryKey, history);

      // 如果是成功登录，更新受信任设备
      if (record.success) {
        await this.updateTrustedDevices(deviceInfo);
      }

      console.log('[AbnormalLogin] 登录历史已记录');

    } catch (error) {
      console.error('[AbnormalLogin] 记录登录历史失败:', error);
    }
  }

  /**
   * 记录安全事件
   * @param {Object} loginInfo - 登录信息
   * @param {Array} detectionResults - 检测结果
   * @param {Object} riskAssessment - 风险评估
   */
  async recordSecurityEvent(loginInfo, detectionResults, riskAssessment) {
    try {
      if (detectionResults.length === 0) return;

      const events = await storage.get(this.securityEventsKey) || [];

      const event = {
        id: Date.now().toString(),
        timestamp: Date.now(),
        type: 'abnormal_login_detected',
        riskLevel: riskAssessment.level,
        riskScore: riskAssessment.score,
        detections: detectionResults,
        deviceInfo: this.sanitizeDeviceInfo(loginInfo.deviceInfo || await this.getCurrentDeviceInfo()),
        handled: false
      };

      events.push(event);

      // 只保留最近50个安全事件
      if (events.length > 50) {
        events.splice(0, events.length - 50);
      }

      await storage.set(this.securityEventsKey, events);
      console.log('[AbnormalLogin] 安全事件已记录');

    } catch (error) {
      console.error('[AbnormalLogin] 记录安全事件失败:', error);
    }
  }

  /**
   * 获取当前设备信息
   * @returns {Promise<Object>} 设备信息
   */
  async getCurrentDeviceInfo() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      return {
        brand: systemInfo.brand,
        model: systemInfo.model,
        system: systemInfo.system,
        version: systemInfo.version,
        platform: systemInfo.platform,
        screenWidth: systemInfo.screenWidth,
        screenHeight: systemInfo.screenHeight,
        pixelRatio: systemInfo.pixelRatio,
        language: systemInfo.language,
        wechatVersion: systemInfo.version,
        deviceId: this.generateDeviceId(systemInfo)
      };
    } catch (error) {
      console.error('[AbnormalLogin] 获取设备信息失败:', error);
      return {};
    }
  }

  /**
   * 生成设备ID
   * @param {Object} systemInfo - 系统信息
   * @returns {string} 设备ID
   */
  generateDeviceId(systemInfo) {
    const deviceString = [
      systemInfo.brand,
      systemInfo.model,
      systemInfo.system,
      systemInfo.screenWidth,
      systemInfo.screenHeight
    ].join('-');

    // 简单哈希生成设备ID
    let hash = 0;
    for (let i = 0; i < deviceString.length; i++) {
      const char = deviceString.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    
    return Math.abs(hash).toString(36);
  }

  /**
   * 清理设备信息（移除敏感数据）
   * @param {Object} deviceInfo - 原始设备信息
   * @returns {Object} 清理后的设备信息
   */
  sanitizeDeviceInfo(deviceInfo) {
    if (!deviceInfo) return {};

    return {
      brand: deviceInfo.brand,
      model: deviceInfo.model,
      system: deviceInfo.system,
      platform: deviceInfo.platform,
      deviceId: deviceInfo.deviceId
    };
  }

  /**
   * 判断是否为同一设备
   * @param {Object} device1 - 设备1
   * @param {Object} device2 - 设备2
   * @returns {boolean} 是否为同一设备
   */
  isSameDevice(device1, device2) {
    if (!device1 || !device2) return false;
    
    return device1.deviceId === device2.deviceId ||
           (device1.brand === device2.brand &&
            device1.model === device2.model &&
            device1.system === device2.system);
  }

  /**
   * 获取登录历史
   * @returns {Promise<Array>} 登录历史
   */
  async getLoginHistory() {
    try {
      return await storage.get(this.loginHistoryKey) || [];
    } catch (error) {
      console.error('[AbnormalLogin] 获取登录历史失败:', error);
      return [];
    }
  }

  /**
   * 获取受信任设备列表
   * @returns {Promise<Array>} 受信任设备列表
   */
  async getTrustedDevices() {
    try {
      return await storage.get(this.deviceInfoKey) || [];
    } catch (error) {
      console.error('[AbnormalLogin] 获取受信任设备失败:', error);
      return [];
    }
  }

  /**
   * 更新受信任设备
   * @param {Object} deviceInfo - 设备信息
   */
  async updateTrustedDevices(deviceInfo) {
    try {
      const trustedDevices = await this.getTrustedDevices();
      const sanitizedDevice = this.sanitizeDeviceInfo(deviceInfo);

      // 检查设备是否已存在
      const existingIndex = trustedDevices.findIndex(device => 
        this.isSameDevice(device, sanitizedDevice)
      );

      if (existingIndex >= 0) {
        // 更新最后使用时间
        trustedDevices[existingIndex].lastUsed = Date.now();
      } else {
        // 添加新设备
        trustedDevices.push({
          ...sanitizedDevice,
          firstUsed: Date.now(),
          lastUsed: Date.now(),
          trusted: false // 新设备默认不受信任
        });
      }

      // 清理过期设备
      const now = Date.now();
      const validDevices = trustedDevices.filter(device => 
        (now - device.lastUsed) < this.config.deviceTrustPeriod
      );

      await storage.set(this.deviceInfoKey, validDevices);

    } catch (error) {
      console.error('[AbnormalLogin] 更新受信任设备失败:', error);
    }
  }

  /**
   * 从历史记录中获取唯一设备
   * @param {Array} loginHistory - 登录历史
   * @returns {Array} 唯一设备列表
   */
  getUniqueDevicesFromHistory(loginHistory) {
    const devices = new Map();
    
    loginHistory.forEach(login => {
      if (login.deviceInfo && login.deviceInfo.deviceId) {
        devices.set(login.deviceInfo.deviceId, login.deviceInfo);
      }
    });

    return Array.from(devices.values());
  }

  /**
   * 分析设备变化
   * @param {Array} recentLogins - 最近登录记录
   * @param {Object} currentDevice - 当前设备
   * @returns {Object} 设备变化分析
   */
  analyzeDeviceChanges(recentLogins, currentDevice) {
    const changes = [];
    
    if (recentLogins.length > 0) {
      const lastLogin = recentLogins[recentLogins.length - 1];
      const lastDevice = lastLogin.deviceInfo;

      if (lastDevice) {
        if (lastDevice.system !== currentDevice.system) {
          changes.push({ field: 'system', from: lastDevice.system, to: currentDevice.system });
        }
        if (lastDevice.version !== currentDevice.version) {
          changes.push({ field: 'version', from: lastDevice.version, to: currentDevice.version });
        }
        if (lastDevice.brand !== currentDevice.brand) {
          changes.push({ field: 'brand', from: lastDevice.brand, to: currentDevice.brand });
        }
      }
    }

    return {
      hasSignificantChange: changes.length > 0,
      changes
    };
  }

  /**
   * 计算登录间隔
   * @param {Array} loginHistory - 登录历史
   * @returns {Array} 间隔时间数组
   */
  calculateLoginIntervals(loginHistory) {
    const intervals = [];
    
    for (let i = 1; i < loginHistory.length; i++) {
      const interval = loginHistory[i].timestamp - loginHistory[i - 1].timestamp;
      intervals.push(interval);
    }

    return intervals;
  }

  /**
   * 分析每小时登录模式
   * @param {Array} loginHistory - 登录历史
   * @returns {Object} 每小时统计
   */
  analyzeHourlyLoginPattern(loginHistory) {
    const hourlyStats = {};

    loginHistory.forEach(login => {
      const hour = new Date(login.timestamp).getHours();
      hourlyStats[hour] = (hourlyStats[hour] || 0) + 1;
    });

    return hourlyStats;
  }

  /**
   * 分析每日登录模式
   * @param {Array} loginHistory - 登录历史
   * @returns {Object} 每日统计
   */
  analyzeDailyLoginPattern(loginHistory) {
    const dailyStats = {};

    loginHistory.forEach(login => {
      const day = new Date(login.timestamp).getDay();
      dailyStats[day] = (dailyStats[day] || 0) + 1;
    });

    return dailyStats;
  }

  /**
   * 检测是否为异常登录时间
   * @param {number} currentHour - 当前小时
   * @param {Object} hourlyStats - 每小时统计
   * @returns {boolean} 是否异常
   */
  isUnusualLoginTime(currentHour, hourlyStats) {
    const currentHourCount = hourlyStats[currentHour] || 0;
    const totalLogins = Object.values(hourlyStats).reduce((sum, count) => sum + count, 0);
    
    if (totalLogins < 10) return false; // 数据不足，不判断异常

    const averagePerHour = totalLogins / 24;
    return currentHourCount < averagePerHour * 0.3; // 低于平均值30%视为异常
  }

  /**
   * 检测是否为异常登录日期
   * @param {number} currentDay - 当前星期
   * @param {Object} dailyStats - 每日统计
   * @returns {boolean} 是否异常
   */
  isUnusualLoginDay(currentDay, dailyStats) {
    const currentDayCount = dailyStats[currentDay] || 0;
    const totalLogins = Object.values(dailyStats).reduce((sum, count) => sum + count, 0);
    
    if (totalLogins < 20) return false; // 数据不足，不判断异常

    const averagePerDay = totalLogins / 7;
    return currentDayCount < averagePerDay * 0.2; // 低于平均值20%视为异常
  }

  /**
   * 获取最常用的登录时间
   * @param {Object} hourlyStats - 每小时统计
   * @returns {Array} 最常用时间段
   */
  getTopLoginHours(hourlyStats) {
    return Object.entries(hourlyStats)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([hour, count]) => ({ hour: parseInt(hour), count }));
  }

  /**
   * 获取安全事件
   * @returns {Promise<Array>} 安全事件列表
   */
  async getSecurityEvents() {
    try {
      return await storage.get(this.securityEventsKey) || [];
    } catch (error) {
      console.error('[AbnormalLogin] 获取安全事件失败:', error);
      return [];
    }
  }

  /**
   * 清理历史数据
   */
  async clearHistoryData() {
    try {
      await Promise.all([
        storage.remove(this.loginHistoryKey),
        storage.remove(this.deviceInfoKey),
        storage.remove(this.securityEventsKey)
      ]);
      console.log('[AbnormalLogin] 历史数据已清理');
    } catch (error) {
      console.error('[AbnormalLogin] 清理历史数据失败:', error);
    }
  }
}

// 创建单例实例
const abnormalLoginDetector = new AbnormalLoginDetector();

module.exports = {
  abnormalLoginDetector,
  AbnormalLoginDetector
};
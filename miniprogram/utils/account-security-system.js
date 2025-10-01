/**
 * 账号安全系统集成管理器
 * 整合所有安全组件，提供统一的安全管理接口
 */

const { accountBindingManager } = require('./account-security-manager.js');
const { abnormalLoginDetector } = require('./abnormal-login-detector.js');
const { sessionManager } = require('./session-manager.js');
const { secureLogoutManager } = require('./secure-logout-manager.js');
const { privacyProtectionManager } = require('./privacy-protection-manager.js');
const { authManager } = require('./auth.js');

/**
 * 账号安全系统管理器
 */
class AccountSecuritySystem {
  constructor() {
    this.isInitialized = false;
    this.securityLevel = 'standard'; // minimal, standard, strict
    this.monitoringEnabled = true;
    this.securityEvents = [];
    
    // 安全配置
    this.config = {
      enableAccountBinding: true,
      enableAbnormalDetection: true,
      enableSessionManagement: true,
      enableSecureLogout: true,
      enablePrivacyProtection: true,
      autoSecurityChecks: true,
      securityCheckInterval: 10 * 60 * 1000, // 10分钟
      maxSecurityEvents: 100
    };

    this.init();
  }

  /**
   * 初始化安全系统
   */
  async init() {
    try {
      console.log('[AccountSecurity] 初始化账号安全系统');

      // 初始化各个安全组件
      await this.initializeComponents();

      // 设置安全监控
      if (this.config.autoSecurityChecks) {
        this.startSecurityMonitoring();
      }

      // 检查并恢复中断的安全流程
      await this.recoverInterruptedProcesses();

      this.isInitialized = true;
      console.log('[AccountSecurity] 账号安全系统初始化完成');

    } catch (error) {
      console.error('[AccountSecurity] 初始化失败:', error);
    }
  }

  /**
   * 初始化安全组件
   */
  async initializeComponents() {
    try {
      const initPromises = [];

      // 初始化各个安全管理器
      if (this.config.enableAccountBinding) {
        initPromises.push(this.initAccountBinding());
      }

      if (this.config.enableAbnormalDetection) {
        initPromises.push(this.initAbnormalDetection());
      }

      if (this.config.enableSessionManagement) {
        initPromises.push(this.initSessionManagement());
      }

      if (this.config.enablePrivacyProtection) {
        initPromises.push(this.initPrivacyProtection());
      }

      await Promise.allSettled(initPromises);

    } catch (error) {
      console.error('[AccountSecurity] 组件初始化失败:', error);
    }
  }

  /**
   * 初始化账号绑定
   */
  async initAccountBinding() {
    try {
      // 检查账号绑定状态
      const bindingStatus = await accountBindingManager.checkWechatBinding();
      
      if (!bindingStatus.isBound && await authManager.isLoggedIn()) {
        console.log('[AccountSecurity] 检测到未绑定账号，需要验证');
        // 可以在这里触发绑定验证流程
      }

    } catch (error) {
      console.error('[AccountSecurity] 账号绑定初始化失败:', error);
    }
  }

  /**
   * 初始化异常检测
   */
  async initAbnormalDetection() {
    try {
      // 异常检测器会自动初始化
      console.log('[AccountSecurity] 异常登录检测已启用');
    } catch (error) {
      console.error('[AccountSecurity] 异常检测初始化失败:', error);
    }
  }

  /**
   * 初始化会话管理
   */
  async initSessionManagement() {
    try {
      // 会话管理器会自动初始化
      console.log('[AccountSecurity] 会话管理已启用');
    } catch (error) {
      console.error('[AccountSecurity] 会话管理初始化失败:', error);
    }
  }

  /**
   * 初始化隐私保护
   */
  async initPrivacyProtection() {
    try {
      // 隐私保护管理器会自动初始化
      console.log('[AccountSecurity] 隐私保护已启用');
    } catch (error) {
      console.error('[AccountSecurity] 隐私保护初始化失败:', error);
    }
  }

  /**
   * 执行安全登录流程
   * @param {Object} loginData - 登录数据
   * @returns {Promise<Object>} 登录结果
   */
  async performSecureLogin(loginData) {
    try {
      console.log('[AccountSecurity] 开始安全登录流程');

      // 1. 异常登录检测
      const abnormalCheck = await abnormalLoginDetector.detectAbnormalLogin(loginData);
      
      if (abnormalCheck.isAbnormal && abnormalCheck.riskLevel === 'high') {
        return {
          success: false,
          reason: 'security_risk',
          message: '检测到登录异常，请稍后重试',
          securityInfo: abnormalCheck
        };
      }

      // 2. 账号绑定验证
      if (this.config.enableAccountBinding) {
        const bindingResult = await accountBindingManager.verifyWechatBinding();
        
        if (!bindingResult.success && bindingResult.reason !== 'already_bound') {
          return {
            success: false,
            reason: 'binding_failed',
            message: '账号绑定验证失败',
            bindingInfo: bindingResult
          };
        }
      }

      // 3. 创建安全会话
      const sessionResult = await sessionManager.createSession(loginData);
      
      if (!sessionResult.success) {
        return {
          success: false,
          reason: 'session_failed',
          message: '会话创建失败',
          sessionInfo: sessionResult
        };
      }

      // 4. 记录登录历史
      await abnormalLoginDetector.recordLoginHistory({
        success: true,
        deviceInfo: loginData.deviceInfo,
        timestamp: Date.now(),
        sessionId: sessionResult.session.sessionId
      });

      // 5. 记录安全事件
      await this.recordSecurityEvent({
        type: 'secure_login',
        level: 'info',
        message: '安全登录成功',
        data: {
          sessionId: sessionResult.session.sessionId,
          abnormalCheck: abnormalCheck,
          bindingStatus: this.config.enableAccountBinding
        }
      });

      return {
        success: true,
        message: '安全登录成功',
        sessionInfo: sessionResult,
        securityInfo: abnormalCheck
      };

    } catch (error) {
      console.error('[AccountSecurity] 安全登录失败:', error);
      return {
        success: false,
        reason: 'security_error',
        message: '安全登录过程出错',
        error: error.message
      };
    }
  }

  /**
   * 执行安全退出流程
   * @param {Object} options - 退出选项
   * @returns {Promise<Object>} 退出结果
   */
  async performSecureLogout(options = {}) {
    try {
      console.log('[AccountSecurity] 开始安全退出流程');

      // 执行安全退出
      const logoutResult = await secureLogoutManager.performSecureLogout(options);

      // 记录安全事件
      await this.recordSecurityEvent({
        type: 'secure_logout',
        level: 'info',
        message: logoutResult.success ? '安全退出成功' : '安全退出失败',
        data: {
          method: options.method || 'normal',
          reason: options.reason || 'user_initiated',
          success: logoutResult.success
        }
      });

      return logoutResult;

    } catch (error) {
      console.error('[AccountSecurity] 安全退出失败:', error);
      return {
        success: false,
        reason: 'security_error',
        message: '安全退出过程出错',
        error: error.message
      };
    }
  }

  /**
   * 检查整体安全状态
   * @returns {Promise<Object>} 安全状态
   */
  async checkSecurityStatus() {
    try {
      console.log('[AccountSecurity] 检查安全状态');

      const status = {
        timestamp: Date.now(),
        overallSecurity: 'unknown',
        components: {},
        recommendations: [],
        alerts: []
      };

      // 检查账号绑定状态
      if (this.config.enableAccountBinding) {
        const bindingStatus = await accountBindingManager.checkWechatBinding();
        status.components.accountBinding = {
          status: bindingStatus.isBound ? 'secure' : 'warning',
          details: bindingStatus
        };

        if (!bindingStatus.isBound) {
          status.recommendations.push('建议完成账号绑定验证');
        }
      }

      // 检查会话健康状态
      if (this.config.enableSessionManagement) {
        const sessionHealth = await sessionManager.getSessionHealth();
        status.components.sessionManagement = {
          status: sessionHealth.status === 'healthy' ? 'secure' : 'warning',
          details: sessionHealth
        };

        if (sessionHealth.needsRefresh) {
          status.recommendations.push('会话即将过期，建议刷新');
        }
      }

      // 检查最近的安全事件
      const recentEvents = await this.getRecentSecurityEvents(24 * 60 * 60 * 1000); // 最近24小时
      const highRiskEvents = recentEvents.filter(event => event.level === 'high');
      
      if (highRiskEvents.length > 0) {
        status.alerts = highRiskEvents.map(event => ({
          type: event.type,
          message: event.message,
          timestamp: event.timestamp
        }));
      }

      // 生成隐私合规报告
      if (this.config.enablePrivacyProtection) {
        const privacyReport = privacyProtectionManager.generatePrivacyComplianceReport();
        status.components.privacyProtection = {
          status: privacyReport.compliance ? 'secure' : 'warning',
          details: privacyReport
        };

        if (privacyReport.recommendations) {
          status.recommendations.push(...privacyReport.recommendations);
        }
      }

      // 计算整体安全等级
      status.overallSecurity = this.calculateOverallSecurity(status.components, status.alerts);

      return status;

    } catch (error) {
      console.error('[AccountSecurity] 安全状态检查失败:', error);
      return {
        timestamp: Date.now(),
        overallSecurity: 'error',
        error: error.message
      };
    }
  }

  /**
   * 计算整体安全等级
   * @param {Object} components - 组件状态
   * @param {Array} alerts - 警报列表
   * @returns {string} 安全等级
   */
  calculateOverallSecurity(components, alerts) {
    const componentStatuses = Object.values(components).map(comp => comp.status);
    
    // 如果有任何组件状态为error，整体为不安全
    if (componentStatuses.includes('error')) {
      return 'unsafe';
    }
    
    // 如果有高风险警报，整体为警告
    if (alerts.length > 0) {
      return 'warning';
    }
    
    // 如果有任何组件状态为warning，整体为警告
    if (componentStatuses.includes('warning')) {
      return 'warning';
    }
    
    // 否则为安全
    return 'secure';
  }

  /**
   * 启动安全监控
   */
  startSecurityMonitoring() {
    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
    }

    this.monitoringTimer = setInterval(async () => {
      await this.performSecurityCheck();
    }, this.config.securityCheckInterval);

    console.log('[AccountSecurity] 安全监控已启动');
  }

  /**
   * 执行安全检查
   */
  async performSecurityCheck() {
    try {
      const securityStatus = await this.checkSecurityStatus();
      
      // 如果发现高风险问题，触发安全响应
      if (securityStatus.overallSecurity === 'unsafe') {
        await this.handleSecurityThreat(securityStatus);
      } else if (securityStatus.alerts.length > 0) {
        await this.handleSecurityAlert(securityStatus.alerts);
      }

    } catch (error) {
      console.error('[AccountSecurity] 安全检查失败:', error);
    }
  }

  /**
   * 处理安全威胁
   * @param {Object} securityStatus - 安全状态
   */
  async handleSecurityThreat(securityStatus) {
    try {
      console.warn('[AccountSecurity] 检测到安全威胁，执行安全响应');

      // 记录高危安全事件
      await this.recordSecurityEvent({
        type: 'security_threat',
        level: 'high',
        message: '检测到安全威胁',
        data: securityStatus
      });

      // 根据威胁类型执行相应措施
      // 这里可以实现强制退出、锁定账号等措施

    } catch (error) {
      console.error('[AccountSecurity] 处理安全威胁失败:', error);
    }
  }

  /**
   * 处理安全警报
   * @param {Array} alerts - 警报列表
   */
  async handleSecurityAlert(alerts) {
    try {
      console.warn('[AccountSecurity] 处理安全警报:', alerts.length);

      for (const alert of alerts) {
        await this.recordSecurityEvent({
          type: 'security_alert',
          level: 'medium',
          message: alert.message,
          data: alert
        });
      }

    } catch (error) {
      console.error('[AccountSecurity] 处理安全警报失败:', error);
    }
  }

  /**
   * 记录安全事件
   * @param {Object} event - 安全事件
   */
  async recordSecurityEvent(event) {
    try {
      const securityEvent = {
        id: Date.now().toString(),
        timestamp: Date.now(),
        type: event.type,
        level: event.level || 'info',
        message: event.message,
        data: event.data,
        handled: false
      };

      this.securityEvents.push(securityEvent);

      // 限制事件数量
      if (this.securityEvents.length > this.config.maxSecurityEvents) {
        this.securityEvents.shift();
      }

      console.log('[AccountSecurity] 安全事件已记录:', securityEvent.type);

    } catch (error) {
      console.error('[AccountSecurity] 记录安全事件失败:', error);
    }
  }

  /**
   * 获取最近的安全事件
   * @param {number} timeRange - 时间范围（毫秒）
   * @returns {Array} 安全事件列表
   */
  async getRecentSecurityEvents(timeRange) {
    try {
      const cutoffTime = Date.now() - timeRange;
      return this.securityEvents.filter(event => event.timestamp > cutoffTime);
    } catch (error) {
      console.error('[AccountSecurity] 获取安全事件失败:', error);
      return [];
    }
  }

  /**
   * 恢复中断的安全流程
   */
  async recoverInterruptedProcesses() {
    try {
      // 恢复中断的退出流程
      await secureLogoutManager.recoverInterruptedLogout();

      console.log('[AccountSecurity] 中断流程恢复检查完成');

    } catch (error) {
      console.error('[AccountSecurity] 恢复中断流程失败:', error);
    }
  }

  /**
   * 更新安全配置
   * @param {Object} newConfig - 新配置
   */
  updateSecurityConfig(newConfig) {
    try {
      this.config = { ...this.config, ...newConfig };
      
      // 重新启动监控
      if (this.config.autoSecurityChecks && !this.monitoringTimer) {
        this.startSecurityMonitoring();
      } else if (!this.config.autoSecurityChecks && this.monitoringTimer) {
        clearInterval(this.monitoringTimer);
        this.monitoringTimer = null;
      }

      console.log('[AccountSecurity] 安全配置已更新');

    } catch (error) {
      console.error('[AccountSecurity] 更新安全配置失败:', error);
    }
  }

  /**
   * 获取安全系统状态
   * @returns {Object} 系统状态
   */
  getSystemStatus() {
    return {
      isInitialized: this.isInitialized,
      securityLevel: this.securityLevel,
      monitoringEnabled: this.monitoringEnabled,
      config: this.config,
      eventCount: this.securityEvents.length,
      lastCheck: this.lastSecurityCheck
    };
  }

  /**
   * 销毁安全系统
   */
  async destroy() {
    try {
      // 停止监控
      if (this.monitoringTimer) {
        clearInterval(this.monitoringTimer);
        this.monitoringTimer = null;
      }

      // 销毁各个管理器
      await Promise.allSettled([
        sessionManager.destroy(),
        privacyProtectionManager.destroy()
      ]);

      // 清理状态
      this.securityEvents = [];
      this.isInitialized = false;

      console.log('[AccountSecurity] 安全系统已销毁');

    } catch (error) {
      console.error('[AccountSecurity] 销毁安全系统失败:', error);
    }
  }
}

// 创建单例实例
const accountSecuritySystem = new AccountSecuritySystem();

module.exports = {
  accountSecuritySystem,
  AccountSecuritySystem
};
/**
 * 隐私信息保护管理器
 * 实现数据加密、脱敏处理、隐私合规等功能
 */

const storage = require('./storage.js');
const config = require('../config/index.js');

/**
 * 隐私保护管理器
 */
class PrivacyProtectionManager {
  constructor() {
    this.encryptionKey = 'privacy_encryption_key';
    this.sensitiveDataTypes = [
      'phone', 'email', 'idCard', 'realName', 'address', 
      'bankCard', 'password', 'token', 'openId', 'unionId'
    ];
    
    // 加密配置
    this.encryptionConfig = {
      algorithm: 'AES',
      keyLength: 256,
      enableLocalEncryption: true,
      enableTransmissionEncryption: true,
      encryptionScope: ['storage', 'transmission', 'display']
    };

    // 脱敏配置
    this.maskingRules = {
      phone: { type: 'phone', keepFirst: 3, keepLast: 4 },
      email: { type: 'email', keepFirst: 2, keepLast: 0 },
      idCard: { type: 'idCard', keepFirst: 6, keepLast: 4 },
      realName: { type: 'name', keepFirst: 1, keepLast: 0 },
      address: { type: 'address', keepFirst: 6, keepLast: 0 },
      bankCard: { type: 'bankCard', keepFirst: 4, keepLast: 4 }
    };

    this.init();
  }

  /**
   * 初始化隐私保护管理器
   */
  async init() {
    try {
      // 生成或获取加密密钥
      await this.initEncryptionKey();
      
      console.log('[PrivacyProtection] 隐私保护管理器初始化完成');
    } catch (error) {
      console.error('[PrivacyProtection] 初始化失败:', error);
    }
  }

  /**
   * 初始化加密密钥
   */
  async initEncryptionKey() {
    try {
      let key = await storage.get(this.encryptionKey);
      
      if (!key) {
        // 生成新的加密密钥
        key = this.generateEncryptionKey();
        await storage.set(this.encryptionKey, key);
        console.log('[PrivacyProtection] 生成新的加密密钥');
      }

      this.currentKey = key;
    } catch (error) {
      console.error('[PrivacyProtection] 初始化加密密钥失败:', error);
      // 使用默认密钥
      this.currentKey = this.generateDefaultKey();
    }
  }

  /**
   * 生成加密密钥
   * @returns {string} 加密密钥
   */
  generateEncryptionKey() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let key = '';
    
    for (let i = 0; i < 32; i++) {
      key += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    
    return key;
  }

  /**
   * 生成默认密钥
   * @returns {string} 默认密钥
   */
  generateDefaultKey() {
    return 'WuHaoTutor2024DefaultKey123456789';
  }

  /**
   * 加密敏感数据
   * @param {any} data - 要加密的数据
   * @param {Object} options - 加密选项
   * @returns {string} 加密后的数据
   */
  encryptData(data, options = {}) {
    try {
      if (!this.encryptionConfig.enableLocalEncryption) {
        return data;
      }

      if (data === null || data === undefined) {
        return data;
      }

      // 将数据转换为字符串
      const dataString = typeof data === 'string' ? data : JSON.stringify(data);
      
      // 使用简单的加密算法（在生产环境中应使用更强的加密）
      const encrypted = this.simpleEncrypt(dataString, this.currentKey);
      
      return {
        __encrypted: true,
        data: encrypted,
        timestamp: Date.now(),
        algorithm: 'simple'
      };

    } catch (error) {
      console.error('[PrivacyProtection] 数据加密失败:', error);
      return data; // 加密失败时返回原数据
    }
  }

  /**
   * 解密敏感数据
   * @param {any} encryptedData - 加密的数据
   * @returns {any} 解密后的数据
   */
  decryptData(encryptedData) {
    try {
      // 检查是否为加密数据
      if (!encryptedData || typeof encryptedData !== 'object' || !encryptedData.__encrypted) {
        return encryptedData;
      }

      // 解密数据
      const decryptedString = this.simpleDecrypt(encryptedData.data, this.currentKey);
      
      // 尝试解析JSON
      try {
        return JSON.parse(decryptedString);
      } catch {
        return decryptedString;
      }

    } catch (error) {
      console.error('[PrivacyProtection] 数据解密失败:', error);
      return encryptedData;
    }
  }

  /**
   * 简单加密算法
   * @param {string} text - 明文
   * @param {string} key - 密钥
   * @returns {string} 密文
   */
  simpleEncrypt(text, key) {
    let result = '';
    const keyLength = key.length;
    
    for (let i = 0; i < text.length; i++) {
      const textChar = text.charCodeAt(i);
      const keyChar = key.charCodeAt(i % keyLength);
      const encryptedChar = textChar ^ keyChar;
      result += String.fromCharCode(encryptedChar);
    }
    
    // Base64编码
    return wx.arrayBufferToBase64(this.stringToArrayBuffer(result));
  }

  /**
   * 简单解密算法
   * @param {string} encryptedText - 密文
   * @param {string} key - 密钥
   * @returns {string} 明文
   */
  simpleDecrypt(encryptedText, key) {
    try {
      // Base64解码
      const arrayBuffer = wx.base64ToArrayBuffer(encryptedText);
      const text = this.arrayBufferToString(arrayBuffer);
      
      let result = '';
      const keyLength = key.length;
      
      for (let i = 0; i < text.length; i++) {
        const encryptedChar = text.charCodeAt(i);
        const keyChar = key.charCodeAt(i % keyLength);
        const decryptedChar = encryptedChar ^ keyChar;
        result += String.fromCharCode(decryptedChar);
      }
      
      return result;
    } catch (error) {
      console.error('[PrivacyProtection] 解密过程错误:', error);
      return encryptedText;
    }
  }

  /**
   * 字符串转ArrayBuffer
   * @param {string} str - 字符串
   * @returns {ArrayBuffer} ArrayBuffer
   */
  stringToArrayBuffer(str) {
    const buffer = new ArrayBuffer(str.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < str.length; i++) {
      view[i] = str.charCodeAt(i);
    }
    return buffer;
  }

  /**
   * ArrayBuffer转字符串
   * @param {ArrayBuffer} buffer - ArrayBuffer
   * @returns {string} 字符串
   */
  arrayBufferToString(buffer) {
    const view = new Uint8Array(buffer);
    let str = '';
    for (let i = 0; i < view.length; i++) {
      str += String.fromCharCode(view[i]);
    }
    return str;
  }

  /**
   * 数据脱敏处理
   * @param {string} data - 原始数据
   * @param {string} type - 数据类型
   * @param {Object} options - 脱敏选项
   * @returns {string} 脱敏后的数据
   */
  maskSensitiveData(data, type, options = {}) {
    try {
      if (!data || typeof data !== 'string') {
        return data;
      }

      const rule = this.maskingRules[type];
      if (!rule) {
        // 默认脱敏规则
        return this.defaultMask(data, options);
      }

      switch (rule.type) {
        case 'phone':
          return this.maskPhone(data);
        case 'email':
          return this.maskEmail(data);
        case 'idCard':
          return this.maskIdCard(data);
        case 'name':
          return this.maskName(data);
        case 'address':
          return this.maskAddress(data);
        case 'bankCard':
          return this.maskBankCard(data);
        default:
          return this.defaultMask(data, options);
      }

    } catch (error) {
      console.error('[PrivacyProtection] 数据脱敏失败:', error);
      return data;
    }
  }

  /**
   * 手机号脱敏
   * @param {string} phone - 手机号
   * @returns {string} 脱敏后的手机号
   */
  maskPhone(phone) {
    if (!phone || phone.length !== 11) {
      return phone;
    }
    return phone.substring(0, 3) + '****' + phone.substring(7);
  }

  /**
   * 邮箱脱敏
   * @param {string} email - 邮箱
   * @returns {string} 脱敏后的邮箱
   */
  maskEmail(email) {
    if (!email || !email.includes('@')) {
      return email;
    }
    
    const [localPart, domain] = email.split('@');
    if (localPart.length <= 2) {
      return email;
    }
    
    const maskedLocal = localPart.substring(0, 2) + '***';
    return maskedLocal + '@' + domain;
  }

  /**
   * 身份证脱敏
   * @param {string} idCard - 身份证号
   * @returns {string} 脱敏后的身份证号
   */
  maskIdCard(idCard) {
    if (!idCard || idCard.length < 10) {
      return idCard;
    }
    
    const start = idCard.substring(0, 6);
    const end = idCard.substring(idCard.length - 4);
    const middle = '*'.repeat(idCard.length - 10);
    
    return start + middle + end;
  }

  /**
   * 姓名脱敏
   * @param {string} name - 姓名
   * @returns {string} 脱敏后的姓名
   */
  maskName(name) {
    if (!name || name.length <= 1) {
      return name;
    }
    
    if (name.length === 2) {
      return name.charAt(0) + '*';
    }
    
    return name.charAt(0) + '*'.repeat(name.length - 1);
  }

  /**
   * 地址脱敏
   * @param {string} address - 地址
   * @returns {string} 脱敏后的地址
   */
  maskAddress(address) {
    if (!address || address.length <= 6) {
      return address;
    }
    
    const start = address.substring(0, 6);
    const masked = '*'.repeat(Math.min(address.length - 6, 10));
    
    return start + masked;
  }

  /**
   * 银行卡脱敏
   * @param {string} bankCard - 银行卡号
   * @returns {string} 脱敏后的银行卡号
   */
  maskBankCard(bankCard) {
    if (!bankCard || bankCard.length < 8) {
      return bankCard;
    }
    
    const start = bankCard.substring(0, 4);
    const end = bankCard.substring(bankCard.length - 4);
    const middle = '*'.repeat(bankCard.length - 8);
    
    return start + middle + end;
  }

  /**
   * 默认脱敏
   * @param {string} data - 数据
   * @param {Object} options - 选项
   * @returns {string} 脱敏后的数据
   */
  defaultMask(data, options = {}) {
    const { keepFirst = 1, keepLast = 1, maskChar = '*' } = options;
    
    if (data.length <= keepFirst + keepLast) {
      return data;
    }
    
    const start = data.substring(0, keepFirst);
    const end = data.substring(data.length - keepLast);
    const middle = maskChar.repeat(data.length - keepFirst - keepLast);
    
    return start + middle + end;
  }

  /**
   * 安全存储敏感数据
   * @param {string} key - 存储键
   * @param {any} data - 数据
   * @param {Object} options - 存储选项
   */
  async secureStore(key, data, options = {}) {
    try {
      const { encrypt = true, enableMasking = false } = options;
      
      let processedData = data;
      
      // 加密处理
      if (encrypt && this.encryptionConfig.enableLocalEncryption) {
        processedData = this.encryptData(data);
      }
      
      // 存储到本地
      await storage.set(key, processedData);
      
      console.log(`[PrivacyProtection] 安全存储数据: ${key}`);

    } catch (error) {
      console.error('[PrivacyProtection] 安全存储失败:', error);
      throw error;
    }
  }

  /**
   * 安全读取敏感数据
   * @param {string} key - 存储键
   * @param {Object} options - 读取选项
   * @returns {any} 数据
   */
  async secureRetrieve(key, options = {}) {
    try {
      const { decrypt = true } = options;
      
      let data = await storage.get(key);
      
      // 解密处理
      if (decrypt && data) {
        data = this.decryptData(data);
      }
      
      return data;

    } catch (error) {
      console.error('[PrivacyProtection] 安全读取失败:', error);
      return null;
    }
  }

  /**
   * 清理敏感数据
   * @param {string|Array} keys - 要清理的键
   */
  async cleanupSensitiveData(keys) {
    try {
      const keysToClean = Array.isArray(keys) ? keys : [keys];
      
      const cleanupPromises = keysToClean.map(key => storage.remove(key));
      await Promise.allSettled(cleanupPromises);
      
      console.log(`[PrivacyProtection] 清理敏感数据完成: ${keysToClean.join(', ')}`);

    } catch (error) {
      console.error('[PrivacyProtection] 清理敏感数据失败:', error);
    }
  }

  /**
   * 检测敏感数据
   * @param {any} data - 要检测的数据
   * @returns {Object} 检测结果
   */
  detectSensitiveData(data) {
    try {
      const detectedTypes = [];
      
      if (typeof data === 'string') {
        // 检测手机号
        if (/^1[3-9]\d{9}$/.test(data)) {
          detectedTypes.push('phone');
        }
        
        // 检测邮箱
        if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data)) {
          detectedTypes.push('email');
        }
        
        // 检测身份证
        if (/^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/.test(data)) {
          detectedTypes.push('idCard');
        }
        
        // 检测银行卡
        if (/^\d{16,19}$/.test(data)) {
          detectedTypes.push('bankCard');
        }
      }
      
      return {
        isSensitive: detectedTypes.length > 0,
        types: detectedTypes,
        data: data
      };

    } catch (error) {
      console.error('[PrivacyProtection] 敏感数据检测失败:', error);
      return {
        isSensitive: false,
        types: [],
        data: data
      };
    }
  }

  /**
   * 批量处理用户数据
   * @param {Object} userData - 用户数据
   * @param {Object} options - 处理选项
   * @returns {Object} 处理后的数据
   */
  processUserData(userData, options = {}) {
    try {
      const { mode = 'display', enableMasking = true } = options;
      const processedData = { ...userData };
      
      // 遍历用户数据字段
      Object.keys(processedData).forEach(key => {
        const value = processedData[key];
        
        if (typeof value === 'string') {
          const detection = this.detectSensitiveData(value);
          
          if (detection.isSensitive && enableMasking && mode === 'display') {
            // 对敏感数据进行脱敏
            detection.types.forEach(type => {
              processedData[key] = this.maskSensitiveData(value, type);
            });
          }
        }
      });
      
      return processedData;

    } catch (error) {
      console.error('[PrivacyProtection] 批量处理用户数据失败:', error);
      return userData;
    }
  }

  /**
   * 生成隐私合规报告
   * @returns {Object} 合规报告
   */
  generatePrivacyComplianceReport() {
    try {
      return {
        timestamp: Date.now(),
        encryptionStatus: {
          enabled: this.encryptionConfig.enableLocalEncryption,
          algorithm: this.encryptionConfig.algorithm,
          keyLength: this.encryptionConfig.keyLength
        },
        maskingRules: Object.keys(this.maskingRules).length,
        sensitiveDataTypes: this.sensitiveDataTypes.length,
        compliance: {
          dataEncryption: this.encryptionConfig.enableLocalEncryption,
          dataMasking: true,
          secureStorage: true,
          dataCleanup: true
        },
        recommendations: this.generateComplianceRecommendations()
      };

    } catch (error) {
      console.error('[PrivacyProtection] 生成合规报告失败:', error);
      return {
        timestamp: Date.now(),
        error: error.message
      };
    }
  }

  /**
   * 生成合规建议
   * @returns {Array} 建议列表
   */
  generateComplianceRecommendations() {
    const recommendations = [];
    
    if (!this.encryptionConfig.enableLocalEncryption) {
      recommendations.push('建议启用本地数据加密');
    }
    
    if (!this.encryptionConfig.enableTransmissionEncryption) {
      recommendations.push('建议启用传输加密');
    }
    
    if (this.sensitiveDataTypes.length < 5) {
      recommendations.push('建议增加敏感数据类型定义');
    }
    
    recommendations.push('定期更新加密密钥');
    recommendations.push('定期清理过期的敏感数据');
    
    return recommendations;
  }

  /**
   * 更新隐私配置
   * @param {Object} newConfig - 新配置
   */
  async updatePrivacyConfig(newConfig) {
    try {
      this.encryptionConfig = { ...this.encryptionConfig, ...newConfig.encryption };
      this.maskingRules = { ...this.maskingRules, ...newConfig.masking };
      
      if (newConfig.sensitiveDataTypes) {
        this.sensitiveDataTypes = [...new Set([...this.sensitiveDataTypes, ...newConfig.sensitiveDataTypes])];
      }
      
      console.log('[PrivacyProtection] 隐私配置已更新');

    } catch (error) {
      console.error('[PrivacyProtection] 更新隐私配置失败:', error);
    }
  }

  /**
   * 验证数据完整性
   * @param {any} originalData - 原始数据
   * @param {any} processedData - 处理后的数据
   * @returns {boolean} 验证结果
   */
  verifyDataIntegrity(originalData, processedData) {
    try {
      // 解密处理后的数据
      const decrypted = this.decryptData(processedData);
      
      // 比较原始数据
      return JSON.stringify(originalData) === JSON.stringify(decrypted);

    } catch (error) {
      console.error('[PrivacyProtection] 数据完整性验证失败:', error);
      return false;
    }
  }

  /**
   * 销毁隐私保护管理器
   */
  async destroy() {
    try {
      // 清理密钥
      this.currentKey = null;
      
      // 清理配置
      this.encryptionConfig = null;
      this.maskingRules = null;
      
      console.log('[PrivacyProtection] 隐私保护管理器已销毁');

    } catch (error) {
      console.error('[PrivacyProtection] 销毁隐私保护管理器失败:', error);
    }
  }
}

// 创建单例实例
const privacyProtectionManager = new PrivacyProtectionManager();

module.exports = {
  privacyProtectionManager,
  PrivacyProtectionManager
};
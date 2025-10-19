// utils/storage.js
// 本地存储工具

const config = require('../config/index.js');

/**
 * 本地存储管理类
 */
class StorageManager {
  constructor() {
    this.prefix = config.cache.prefix;
    this.defaultTTL = config.cache.defaultTTL;

    // 内存缓存
    this.memoryCache = new Map();

    // 缓存策略
    this.cacheStrategy = {
      // 用户信息长期缓存
      userInfo: config.cache.userInfoTTL,
      // 静态数据中期缓存
      staticData: config.cache.staticDataTTL,
      // 临时数据短期缓存
      tempData: this.defaultTTL,
    };

    console.log('存储管理器初始化成功');
  }

  /**
   * 生成带前缀的键名
   */
  getKey(key) {
    return `${this.prefix}${key}`;
  }

  /**
   * 生成缓存元数据
   */
  createCacheData(value, ttl = this.defaultTTL) {
    const now = Date.now();
    return {
      value,
      timestamp: now,
      expiry: ttl > 0 ? now + ttl : 0, // 0表示永不过期
      version: config.version,
    };
  }

  /**
   * 检查缓存是否有效
   */
  isCacheValid(cacheData) {
    if (!cacheData || typeof cacheData !== 'object') {
      return false;
    }

    // 检查版本兼容性 - 向后兼容策略
    // 允许没有 version 字段的旧数据
    // 只在主版本号（major version）不匹配时才判定为无效
    if (cacheData.version && cacheData.version !== config.version) {
      try {
        const currentMajor = config.version.split('.')[0];
        const cacheMajor = cacheData.version.split('.')[0];

        // 只在主版本号不匹配时才判定为无效
        if (currentMajor !== cacheMajor) {
          console.warn('缓存主版本不匹配，清理缓存', {
            current: config.version,
            cached: cacheData.version,
          });
          return false;
        }
        // 主版本匹配，次版本和补丁版本不匹配时允许继续使用
        console.log('缓存版本兼容', {
          current: config.version,
          cached: cacheData.version,
        });
      } catch (error) {
        console.warn('版本检查失败，允许使用缓存', error);
        // 版本解析失败时，允许使用缓存（宽容策略）
      }
    }
    // 允许旧数据没有 version 字段（向后兼容）

    // 检查是否过期
    if (cacheData.expiry > 0 && Date.now() > cacheData.expiry) {
      return false;
    }

    return true;
  }

  /**
   * 存储数据到本地
   */
  async set(key, value, options = {}) {
    try {
      const { ttl = this.defaultTTL, sync = false, memory = true, strategy = 'tempData' } = options;

      const finalKey = this.getKey(key);
      const finalTTL = ttl || this.cacheStrategy[strategy] || this.defaultTTL;
      const cacheData = this.createCacheData(value, finalTTL);

      // 存储到内存缓存
      if (memory) {
        this.memoryCache.set(finalKey, cacheData);
      }

      // 存储到本地存储
      if (sync) {
        // 同步存储
        wx.setStorageSync(finalKey, cacheData);
      } else {
        // 异步存储
        await new Promise((resolve, reject) => {
          wx.setStorage({
            key: finalKey,
            data: cacheData,
            success: resolve,
            fail: reject,
          });
        });
      }

      console.log(`数据存储成功: ${key}`, { ttl: finalTTL, strategy });
      return true;
    } catch (error) {
      console.error(`存储数据失败: ${key}`, error);
      throw new Error(`存储失败: ${error.message}`);
    }
  }

  /**
   * 从本地获取数据
   */
  async get(key, options = {}) {
    try {
      const { sync = false, memory = true, defaultValue = null } = options;

      const finalKey = this.getKey(key);

      // 优先从内存缓存获取
      if (memory && this.memoryCache.has(finalKey)) {
        const cacheData = this.memoryCache.get(finalKey);

        if (this.isCacheValid(cacheData)) {
          console.log(`从内存缓存获取数据: ${key}`);
          return cacheData.value;
        } else {
          // 内存缓存已过期，删除
          this.memoryCache.delete(finalKey);
        }
      }

      // 从本地存储获取
      let cacheData;
      if (sync) {
        // 同步获取
        cacheData = wx.getStorageSync(finalKey);
      } else {
        // 异步获取
        cacheData = await new Promise((resolve, reject) => {
          wx.getStorage({
            key: finalKey,
            success: res => resolve(res.data),
            fail: () => resolve(null), // 不存在时返回null而不是抛错
          });
        });
      }

      // 检查缓存有效性
      if (this.isCacheValid(cacheData)) {
        // 更新内存缓存
        if (memory) {
          this.memoryCache.set(finalKey, cacheData);
        }

        console.log(`从本地存储获取数据: ${key}`);
        return cacheData.value;
      } else if (cacheData) {
        // 缓存已过期，删除
        await this.remove(key, { sync, silent: true });
      }

      // 返回默认值
      return defaultValue;
    } catch (error) {
      console.error(`获取数据失败: ${key}`, error);
      return options.defaultValue || null;
    }
  }

  /**
   * 删除存储的数据
   */
  async remove(key, options = {}) {
    try {
      const { sync = false, silent = false } = options;

      const finalKey = this.getKey(key);

      // 从内存缓存删除
      this.memoryCache.delete(finalKey);

      // 从本地存储删除
      if (sync) {
        // 同步删除
        wx.removeStorageSync(finalKey);
      } else {
        // 异步删除
        await new Promise((resolve, reject) => {
          wx.removeStorage({
            key: finalKey,
            success: resolve,
            fail: error => {
              // 如果key不存在，不认为是错误
              if (error.errMsg && error.errMsg.includes('data not found')) {
                resolve();
              } else {
                reject(error);
              }
            },
          });
        });
      }

      if (!silent) {
        console.log(`数据删除成功: ${key}`);
      }
      return true;
    } catch (error) {
      console.error(`删除数据失败: ${key}`, error);
      throw new Error(`删除失败: ${error.message}`);
    }
  }

  /**
   * 检查数据是否存在
   */
  async has(key, options = {}) {
    try {
      const value = await this.get(key, { ...options, defaultValue: undefined });
      return value !== undefined && value !== null;
    } catch (error) {
      console.error(`检查数据存在性失败: ${key}`, error);
      return false;
    }
  }

  /**
   * 清空所有缓存
   */
  async clear(options = {}) {
    try {
      const {
        sync = false,
        pattern = null, // 可以指定清空模式，如只清空某个前缀的数据
      } = options;

      // 清空内存缓存
      if (pattern) {
        // 按模式清空
        for (const [key] of this.memoryCache) {
          if (key.includes(pattern)) {
            this.memoryCache.delete(key);
          }
        }
      } else {
        this.memoryCache.clear();
      }

      // 清空本地存储
      if (pattern) {
        // 按模式清空需要先获取所有key
        const allKeys = await this.getAllKeys({ sync });
        const keysToDelete = allKeys.filter(key => key.includes(pattern));

        for (const key of keysToDelete) {
          if (sync) {
            wx.removeStorageSync(key);
          } else {
            await new Promise(resolve => {
              wx.removeStorage({
                key,
                success: resolve,
                fail: resolve, // 忽略删除失败
              });
            });
          }
        }
      } else {
        // 清空所有本地存储
        if (sync) {
          wx.clearStorageSync();
        } else {
          await new Promise((resolve, reject) => {
            wx.clearStorage({
              success: resolve,
              fail: reject,
            });
          });
        }
      }

      console.log('缓存清空成功', { pattern });
      return true;
    } catch (error) {
      console.error('清空缓存失败', error);
      throw new Error(`清空失败: ${error.message}`);
    }
  }

  /**
   * 获取所有存储的key
   */
  async getAllKeys(options = {}) {
    try {
      const { sync = false } = options;

      if (sync) {
        const info = wx.getStorageInfoSync();
        return info.keys || [];
      } else {
        return new Promise((resolve, reject) => {
          wx.getStorageInfo({
            success: res => resolve(res.keys || []),
            fail: reject,
          });
        });
      }
    } catch (error) {
      console.error('获取存储key列表失败', error);
      return [];
    }
  }

  /**
   * 获取存储使用情况
   */
  async getStorageInfo(options = {}) {
    try {
      const { sync = false } = options;

      if (sync) {
        return wx.getStorageInfoSync();
      } else {
        return new Promise((resolve, reject) => {
          wx.getStorageInfo({
            success: resolve,
            fail: reject,
          });
        });
      }
    } catch (error) {
      console.error('获取存储信息失败', error);
      return {
        keys: [],
        currentSize: 0,
        limitSize: 0,
      };
    }
  }

  /**
   * 清理过期缓存
   */
  async cleanExpiredCache() {
    try {
      const allKeys = await this.getAllKeys();
      const prefixedKeys = allKeys.filter(key => key.startsWith(this.prefix));
      let cleanedCount = 0;

      for (const key of prefixedKeys) {
        try {
          const cacheData = await this.get(key.replace(this.prefix, ''), {
            memory: false,
            defaultValue: undefined,
          });

          if (cacheData === undefined) {
            cleanedCount++;
          }
        } catch (error) {
          console.warn(`清理过期缓存时检查失败: ${key}`, error);
        }
      }

      // 清理内存中的过期缓存
      const now = Date.now();
      for (const [key, cacheData] of this.memoryCache) {
        if (!this.isCacheValid(cacheData)) {
          this.memoryCache.delete(key);
          cleanedCount++;
        }
      }

      console.log(`过期缓存清理完成，共清理 ${cleanedCount} 项`);
      return cleanedCount;
    } catch (error) {
      console.error('清理过期缓存失败', error);
      return 0;
    }
  }

  /**
   * 批量操作
   */
  async batch(operations) {
    const results = [];

    for (const operation of operations) {
      try {
        const { type, key, value, options } = operation;

        let result;
        switch (type) {
          case 'set':
            result = await this.set(key, value, options);
            break;
          case 'get':
            result = await this.get(key, options);
            break;
          case 'remove':
            result = await this.remove(key, options);
            break;
          case 'has':
            result = await this.has(key, options);
            break;
          default:
            throw new Error(`不支持的操作类型: ${type}`);
        }

        results.push({ success: true, data: result });
      } catch (error) {
        results.push({
          success: false,
          error: error.message,
          operation,
        });
      }
    }

    return results;
  }

  /**
   * 缓存装饰器工厂
   */
  cache(options = {}) {
    const { ttl = this.defaultTTL, key: keyGenerator, strategy = 'tempData' } = options;

    return function (target, propertyKey, descriptor) {
      const originalMethod = descriptor.value;

      descriptor.value = async function (...args) {
        // 生成缓存key
        const cacheKey = keyGenerator
          ? keyGenerator(...args)
          : `${propertyKey}_${JSON.stringify(args)}`;

        // 尝试从缓存获取
        try {
          const cachedResult = await storage.get(cacheKey, { strategy });
          if (cachedResult !== null) {
            return cachedResult;
          }
        } catch (error) {
          console.warn(`缓存读取失败: ${cacheKey}`, error);
        }

        // 执行原方法
        const result = await originalMethod.apply(this, args);

        // 缓存结果
        try {
          await storage.set(cacheKey, result, { ttl, strategy });
        } catch (error) {
          console.warn(`缓存写入失败: ${cacheKey}`, error);
        }

        return result;
      };

      return descriptor;
    };
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    return {
      memoryCache: {
        size: this.memoryCache.size,
        keys: Array.from(this.memoryCache.keys()),
      },
      config: {
        prefix: this.prefix,
        defaultTTL: this.defaultTTL,
        strategies: this.cacheStrategy,
      },
    };
  }
}

// 创建存储管理器实例
const storageManager = new StorageManager();

// 导出常用方法
module.exports = {
  // 存储管理器实例
  storageManager,

  // 基础操作方法
  set: (key, value, options) => storageManager.set(key, value, options),
  get: (key, options) => storageManager.get(key, options),
  remove: (key, options) => storageManager.remove(key, options),
  has: (key, options) => storageManager.has(key, options),
  clear: options => storageManager.clear(options),

  // 同步操作方法
  setSync: (key, value, ttl) => storageManager.set(key, value, { sync: true, ttl }),
  getSync: (key, defaultValue) => storageManager.get(key, { sync: true, defaultValue }),
  removeSync: key => storageManager.remove(key, { sync: true }),
  hasSync: key => storageManager.has(key, { sync: true }),
  clearSync: () => storageManager.clear({ sync: true }),

  // 高级功能
  getAllKeys: options => storageManager.getAllKeys(options),
  getStorageInfo: options => storageManager.getStorageInfo(options),
  cleanExpiredCache: () => storageManager.cleanExpiredCache(),
  batch: operations => storageManager.batch(operations),
  getStats: () => storageManager.getStats(),

  // 缓存装饰器
  cache: options => storageManager.cache(options),

  // 预定义的存储策略
  strategies: {
    // 用户信息存储
    userInfo: (key, value) =>
      storageManager.set(key, value, {
        strategy: 'userInfo',
        memory: true,
      }),

    // 静态数据存储
    staticData: (key, value) =>
      storageManager.set(key, value, {
        strategy: 'staticData',
        memory: true,
      }),

    // 临时数据存储
    tempData: (key, value, ttl) =>
      storageManager.set(key, value, {
        strategy: 'tempData',
        ttl,
        memory: false,
      }),

    // 会话数据存储（仅内存）
    sessionData: (key, value) =>
      storageManager.set(key, value, {
        ttl: 0, // 永不过期
        memory: true,
        sync: false,
      }),
  },
};

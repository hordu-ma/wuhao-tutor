// utils/cache-manager.js
// 缓存管理器 - 五好伴学微信小程序

const storage = require('./storage.js');
const { btoa, atob } = require('./base64.js');

/**
 * 缓存管理器类
 */
class CacheManager {
  constructor() {
    // 内存缓存
    this.memoryCache = new Map();

    // 缓存配置
    this.config = {
      // 默认缓存时间(毫秒)
      defaultTTL: 5 * 60 * 1000, // 5分钟
      // 内存缓存最大数量
      maxMemoryItems: 100,
      // 存储缓存前缀
      storagePrefix: 'cache_',
      // 缓存统计前缀
      statsPrefix: 'cache_stats_',
      // 自动清理间隔(毫秒)
      cleanupInterval: 60 * 1000, // 1分钟
      // 压缩阈值(字节)
      compressionThreshold: 1024, // 1KB
      // 加密密钥
      encryptionKey: 'wuhao_cache_key_2024',
    };

    // 缓存统计
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      evictions: 0,
      startTime: Date.now(),
    };

    // 清理定时器
    this.cleanupTimer = null;

    // 缓存策略
    this.strategies = {
      NO_CACHE: 'NO_CACHE',
      MEMORY_CACHE: 'MEMORY_CACHE',
      STORAGE_CACHE: 'STORAGE_CACHE',
      NETWORK_FIRST: 'NETWORK_FIRST',
      CACHE_FIRST: 'CACHE_FIRST',
      CACHE_ONLY: 'CACHE_ONLY',
      NETWORK_ONLY: 'NETWORK_ONLY',
    };

    // 初始化
    this.init();
  }

  /**
   * 初始化缓存管理器
   */
  async init() {
    try {
      // 恢复统计信息
      await this.loadStats();

      // 启动自动清理
      this.startCleanup();

      console.log('缓存管理器初始化成功');
    } catch (error) {
      console.error('缓存管理器初始化失败', error);
    }
  }

  /**
   * 设置缓存
   */
  async set(key, value, options = {}) {
    try {
      const {
        ttl = this.config.defaultTTL,
        strategy = this.strategies.MEMORY_CACHE,
        tags = [],
        encrypt = false,
        compress = false,
      } = options;

      const cacheItem = {
        key,
        value,
        expireTime: Date.now() + ttl,
        createTime: Date.now(),
        accessCount: 0,
        lastAccessTime: Date.now(),
        tags,
        size: this.calculateSize(value),
        encrypted: encrypt,
        compressed: compress,
      };

      // 处理数据
      let processedValue = value;

      // 压缩数据
      if (compress && cacheItem.size > this.config.compressionThreshold) {
        processedValue = this.compress(processedValue);
        cacheItem.compressed = true;
      }

      // 加密数据
      if (encrypt) {
        processedValue = this.encrypt(processedValue);
        cacheItem.encrypted = true;
      }

      cacheItem.value = processedValue;

      // 根据策略存储
      switch (strategy) {
        case this.strategies.MEMORY_CACHE:
          await this.setMemoryCache(key, cacheItem);
          break;
        case this.strategies.STORAGE_CACHE:
          await this.setStorageCache(key, cacheItem);
          break;
        default:
          await this.setMemoryCache(key, cacheItem);
      }

      // 更新统计
      this.stats.sets++;
      await this.saveStats();

      return true;
    } catch (error) {
      console.error('设置缓存失败', error);
      return false;
    }
  }

  /**
   * 获取缓存
   */
  async get(key, options = {}) {
    try {
      const { strategy = this.strategies.MEMORY_CACHE, updateAccessTime = true } = options;

      let cacheItem = null;

      // 根据策略获取
      switch (strategy) {
        case this.strategies.MEMORY_CACHE:
          cacheItem = await this.getMemoryCache(key);
          break;
        case this.strategies.STORAGE_CACHE:
          cacheItem = await this.getStorageCache(key);
          break;
        case this.strategies.CACHE_FIRST:
          // 先从内存缓存获取，再从存储缓存获取
          cacheItem = await this.getMemoryCache(key);
          if (!cacheItem) {
            cacheItem = await this.getStorageCache(key);
            if (cacheItem) {
              // 将存储缓存提升到内存缓存
              await this.setMemoryCache(key, cacheItem);
            }
          }
          break;
        default:
          cacheItem = await this.getMemoryCache(key);
      }

      if (!cacheItem) {
        this.stats.misses++;
        await this.saveStats();
        return null;
      }

      // 检查是否过期
      if (cacheItem.expireTime < Date.now()) {
        await this.delete(key);
        this.stats.misses++;
        await this.saveStats();
        return null;
      }

      // 更新访问信息
      if (updateAccessTime) {
        cacheItem.accessCount++;
        cacheItem.lastAccessTime = Date.now();
      }

      // 处理数据
      let value = cacheItem.value;

      // 解密数据
      if (cacheItem.encrypted) {
        value = this.decrypt(value);
      }

      // 解压数据
      if (cacheItem.compressed) {
        value = this.decompress(value);
      }

      // 更新统计
      this.stats.hits++;
      await this.saveStats();

      return value;
    } catch (error) {
      console.error('获取缓存失败', error);
      this.stats.misses++;
      await this.saveStats();
      return null;
    }
  }

  /**
   * 删除缓存
   */
  async delete(key) {
    try {
      let deleted = false;

      // 从内存缓存删除
      if (this.memoryCache.has(key)) {
        this.memoryCache.delete(key);
        deleted = true;
      }

      // 从存储缓存删除
      try {
        await storage.remove(this.config.storagePrefix + key);
        deleted = true;
      } catch (error) {
        // 忽略删除不存在项的错误
      }

      if (deleted) {
        this.stats.deletes++;
        await this.saveStats();
      }

      return deleted;
    } catch (error) {
      console.error('删除缓存失败', error);
      return false;
    }
  }

  /**
   * 清空所有缓存
   */
  async clear() {
    try {
      // 清空内存缓存
      this.memoryCache.clear();

      // 清空存储缓存
      const keys = await this.getStorageCacheKeys();
      for (const key of keys) {
        await storage.remove(key);
      }

      console.log('所有缓存已清空');
      return true;
    } catch (error) {
      console.error('清空缓存失败', error);
      return false;
    }
  }

  /**
   * 根据标签删除缓存
   */
  async deleteByTags(tags) {
    try {
      const tagsArray = Array.isArray(tags) ? tags : [tags];
      let deletedCount = 0;

      // 删除内存缓存中匹配的项
      for (const [key, item] of this.memoryCache.entries()) {
        if (item.tags && tagsArray.some(tag => item.tags.includes(tag))) {
          this.memoryCache.delete(key);
          deletedCount++;
        }
      }

      // 删除存储缓存中匹配的项
      const storageKeys = await this.getStorageCacheKeys();
      for (const storageKey of storageKeys) {
        try {
          const item = await storage.get(storageKey);
          if (item && item.tags && tagsArray.some(tag => item.tags.includes(tag))) {
            await storage.remove(storageKey);
            deletedCount++;
          }
        } catch (error) {
          // 忽略读取失败的项
        }
      }

      console.log(`根据标签删除了 ${deletedCount} 个缓存项`);
      return deletedCount;
    } catch (error) {
      console.error('根据标签删除缓存失败', error);
      return 0;
    }
  }

  /**
   * 检查缓存是否存在
   */
  async has(key) {
    try {
      const value = await this.get(key, { updateAccessTime: false });
      return value !== null;
    } catch (error) {
      return false;
    }
  }

  /**
   * 获取缓存大小
   */
  async size() {
    try {
      const memorySize = this.memoryCache.size;
      const storageKeys = await this.getStorageCacheKeys();
      return memorySize + storageKeys.length;
    } catch (error) {
      console.error('获取缓存大小失败', error);
      return 0;
    }
  }

  /**
   * 设置内存缓存
   */
  async setMemoryCache(key, cacheItem) {
    // 检查内存缓存大小限制
    if (this.memoryCache.size >= this.config.maxMemoryItems) {
      // 使用LRU策略清理最久未使用的项
      this.evictLRU();
    }

    this.memoryCache.set(key, cacheItem);
  }

  /**
   * 获取内存缓存
   */
  async getMemoryCache(key) {
    return this.memoryCache.get(key) || null;
  }

  /**
   * 设置存储缓存
   */
  async setStorageCache(key, cacheItem) {
    const storageKey = this.config.storagePrefix + key;
    await storage.set(storageKey, cacheItem);
  }

  /**
   * 获取存储缓存
   */
  async getStorageCache(key) {
    try {
      const storageKey = this.config.storagePrefix + key;
      const cacheItem = await storage.get(storageKey);
      return cacheItem || null;
    } catch (error) {
      return null;
    }
  }

  /**
   * LRU淘汰策略
   */
  evictLRU() {
    let oldestKey = null;
    let oldestTime = Date.now();

    for (const [key, item] of this.memoryCache.entries()) {
      if (item.lastAccessTime < oldestTime) {
        oldestTime = item.lastAccessTime;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.memoryCache.delete(oldestKey);
      this.stats.evictions++;
    }
  }

  /**
   * 启动自动清理
   */
  startCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
    }

    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);

    console.log('缓存自动清理已启动');
  }

  /**
   * 停止自动清理
   */
  stopCleanup() {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
      console.log('缓存自动清理已停止');
    }
  }

  /**
   * 清理过期缓存
   */
  async cleanup() {
    try {
      const now = Date.now();
      let cleanedCount = 0;

      // 清理内存缓存中的过期项
      for (const [key, item] of this.memoryCache.entries()) {
        if (item.expireTime < now) {
          this.memoryCache.delete(key);
          cleanedCount++;
        }
      }

      // 清理存储缓存中的过期项
      const storageKeys = await this.getStorageCacheKeys();
      for (const storageKey of storageKeys) {
        try {
          const item = await storage.get(storageKey);
          if (item && item.expireTime < now) {
            await storage.remove(storageKey);
            cleanedCount++;
          }
        } catch (error) {
          // 忽略读取失败的项，可能已被删除
        }
      }

      if (cleanedCount > 0) {
        console.log(`清理了 ${cleanedCount} 个过期缓存项`);
      }
    } catch (error) {
      console.error('清理缓存失败', error);
    }
  }

  /**
   * 获取存储缓存键列表
   */
  async getStorageCacheKeys() {
    try {
      // 这里需要根据实际的storage实现来获取所有键
      // 由于小程序存储API限制，这里使用一个简化的实现
      const allKeys = (await storage.getKeys?.()) || [];
      return allKeys.filter(key => key.startsWith(this.config.storagePrefix));
    } catch (error) {
      console.error('获取存储缓存键失败', error);
      return [];
    }
  }

  /**
   * 计算数据大小
   */
  calculateSize(data) {
    try {
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      return new Blob([str]).size;
    } catch (error) {
      // 降级估算
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      return str.length * 2; // UTF-16字符大概2字节
    }
  }

  /**
   * 压缩数据
   */
  compress(data) {
    try {
      // 简单的压缩实现，实际项目中可以使用更好的压缩算法
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      return this.lzCompress(str);
    } catch (error) {
      console.error('压缩数据失败', error);
      return data;
    }
  }

  /**
   * 解压数据
   */
  decompress(data) {
    try {
      return this.lzDecompress(data);
    } catch (error) {
      console.error('解压数据失败', error);
      return data;
    }
  }

  /**
   * LZ压缩算法简化实现
   */
  lzCompress(str) {
    const dict = {};
    const data = str.split('');
    const result = [];
    let currChar;
    let phrase = data[0];
    let code = 256;

    for (let i = 1; i < data.length; i++) {
      currChar = data[i];
      if (dict[phrase + currChar] != null) {
        phrase += currChar;
      } else {
        result.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
        dict[phrase + currChar] = code;
        code++;
        phrase = currChar;
      }
    }
    result.push(phrase.length > 1 ? dict[phrase] : phrase.charCodeAt(0));
    return result;
  }

  /**
   * LZ解压算法简化实现
   */
  lzDecompress(data) {
    const dict = {};
    let currChar = String.fromCharCode(data[0]);
    let oldPhrase = currChar;
    const result = [currChar];
    let code = 256;
    let phrase;

    for (let i = 1; i < data.length; i++) {
      const currCode = data[i];
      if (currCode < 256) {
        phrase = String.fromCharCode(currCode);
      } else {
        phrase = dict[currCode] ? dict[currCode] : oldPhrase + currChar;
      }
      result.push(phrase);
      currChar = phrase.charAt(0);
      dict[code] = oldPhrase + currChar;
      code++;
      oldPhrase = phrase;
    }
    return result.join('');
  }

  /**
   * 加密数据
   */
  encrypt(data) {
    try {
      // 简单的XOR加密，实际项目中应使用更安全的加密算法
      const str = typeof data === 'string' ? data : JSON.stringify(data);
      const key = this.config.encryptionKey;
      let result = '';

      for (let i = 0; i < str.length; i++) {
        result += String.fromCharCode(str.charCodeAt(i) ^ key.charCodeAt(i % key.length));
      }

      // 使用微信小程序兼容的 btoa 替代浏览器 API
      return btoa(result); // Base64编码
    } catch (error) {
      console.error('加密数据失败', error);
      return data;
    }
  }

  /**
   * 解密数据
   */
  decrypt(data) {
    try {
      // 使用微信小程序兼容的 atob 替代浏览器 API
      const encryptedData = atob(data); // Base64解码
      const key = this.config.encryptionKey;
      let result = '';

      for (let i = 0; i < encryptedData.length; i++) {
        result += String.fromCharCode(encryptedData.charCodeAt(i) ^ key.charCodeAt(i % key.length));
      }

      try {
        return JSON.parse(result);
      } catch {
        return result;
      }
    } catch (error) {
      console.error('解密数据失败', error);
      return data;
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats() {
    const runTime = Date.now() - this.stats.startTime;
    const hitRate =
      this.stats.hits + this.stats.misses > 0
        ? ((this.stats.hits / (this.stats.hits + this.stats.misses)) * 100).toFixed(2)
        : '0.00';

    return {
      ...this.stats,
      hitRate: parseFloat(hitRate),
      runTime,
      memorySize: this.memoryCache.size,
    };
  }

  /**
   * 重置统计信息
   */
  resetStats() {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      evictions: 0,
      startTime: Date.now(),
    };
    this.saveStats();
  }

  /**
   * 保存统计信息
   */
  async saveStats() {
    try {
      const statsKey = this.config.statsPrefix + 'main';
      await storage.set(statsKey, this.stats);
    } catch (error) {
      console.error('保存缓存统计失败', error);
    }
  }

  /**
   * 加载统计信息
   */
  async loadStats() {
    try {
      const statsKey = this.config.statsPrefix + 'main';
      const savedStats = await storage.get(statsKey);
      if (savedStats) {
        this.stats = { ...this.stats, ...savedStats };
      }
    } catch (error) {
      console.error('加载缓存统计失败', error);
    }
  }

  /**
   * 销毁缓存管理器
   */
  destroy() {
    this.stopCleanup();
    this.clear();
    console.log('缓存管理器已销毁');
  }

  /**
   * 导出缓存数据
   */
  async export() {
    try {
      const memoryData = {};
      for (const [key, item] of this.memoryCache.entries()) {
        memoryData[key] = item;
      }

      const storageData = {};
      const storageKeys = await this.getStorageCacheKeys();
      for (const storageKey of storageKeys) {
        try {
          const item = await storage.get(storageKey);
          if (item) {
            const originalKey = storageKey.replace(this.config.storagePrefix, '');
            storageData[originalKey] = item;
          }
        } catch (error) {
          console.warn('导出存储缓存项失败', storageKey, error);
        }
      }

      return {
        memory: memoryData,
        storage: storageData,
        stats: this.stats,
        exportTime: Date.now(),
      };
    } catch (error) {
      console.error('导出缓存数据失败', error);
      return null;
    }
  }

  /**
   * 导入缓存数据
   */
  async import(cacheData) {
    try {
      if (!cacheData || typeof cacheData !== 'object') {
        throw new Error('无效的缓存数据');
      }

      // 导入内存缓存
      if (cacheData.memory) {
        for (const [key, item] of Object.entries(cacheData.memory)) {
          if (item.expireTime > Date.now()) {
            this.memoryCache.set(key, item);
          }
        }
      }

      // 导入存储缓存
      if (cacheData.storage) {
        for (const [key, item] of Object.entries(cacheData.storage)) {
          if (item.expireTime > Date.now()) {
            await this.setStorageCache(key, item);
          }
        }
      }

      console.log('缓存数据导入成功');
      return true;
    } catch (error) {
      console.error('导入缓存数据失败', error);
      return false;
    }
  }
}

// 创建单例实例
const cacheManager = new CacheManager();

module.exports = {
  cacheManager,

  // 缓存策略常量
  CacheStrategy: cacheManager.strategies,

  // 导出常用方法
  set: (key, value, options) => cacheManager.set(key, value, options),
  get: (key, options) => cacheManager.get(key, options),
  delete: key => cacheManager.delete(key),
  clear: () => cacheManager.clear(),
  has: key => cacheManager.has(key),
  size: () => cacheManager.size(),
  getStats: () => cacheManager.getStats(),
  resetStats: () => cacheManager.resetStats(),
  deleteByTags: tags => cacheManager.deleteByTags(tags),
  cleanup: () => cacheManager.cleanup(),

  // 高级功能
  export: () => cacheManager.export(),
  import: data => cacheManager.import(data),

  // 便捷方法
  setWithTTL: (key, value, ttl) => cacheManager.set(key, value, { ttl }),
  setMemory: (key, value, ttl) =>
    cacheManager.set(key, value, {
      strategy: cacheManager.strategies.MEMORY_CACHE,
      ttl,
    }),
  setStorage: (key, value, ttl) =>
    cacheManager.set(key, value, {
      strategy: cacheManager.strategies.STORAGE_CACHE,
      ttl,
    }),

  // 缓存装饰器
  cached: (key, ttl = 5 * 60 * 1000) => {
    return function (target, propertyKey, descriptor) {
      const originalMethod = descriptor.value;

      descriptor.value = async function (...args) {
        const cacheKey = `${key}_${JSON.stringify(args)}`;

        // 尝试从缓存获取
        let result = await cacheManager.get(cacheKey);
        if (result !== null) {
          return result;
        }

        // 执行原方法
        result = await originalMethod.apply(this, args);

        // 缓存结果
        await cacheManager.set(cacheKey, result, { ttl });

        return result;
      };

      return descriptor;
    };
  },
};

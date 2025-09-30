// utils/utils.js
// 通用工具函数库

const config = require('../config/index.js');

/**
 * 工具函数库
 */
const utils = {
  /**
   * 格式化时间
   */
  formatTime: {
    /**
     * 格式化为相对时间
     */
    relative(timestamp) {
      if (!timestamp) return '';

      try {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) {
          return '刚刚';
        } else if (minutes < 60) {
          return `${minutes}分钟前`;
        } else if (hours < 24) {
          return `${hours}小时前`;
        } else if (days < 7) {
          return `${days}天前`;
        } else {
          return this.format(timestamp, 'MM-dd');
        }
      } catch (error) {
        console.error('相对时间格式化失败', error);
        return '';
      }
    },

    /**
     * 格式化为指定格式
     */
    format(timestamp, format = 'YYYY-MM-dd HH:mm:ss') {
      if (!timestamp) return '';

      try {
        const date = new Date(timestamp);
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hour = date.getHours().toString().padStart(2, '0');
        const minute = date.getMinutes().toString().padStart(2, '0');
        const second = date.getSeconds().toString().padStart(2, '0');

        return format
          .replace('YYYY', year)
          .replace('MM', month)
          .replace('dd', day)
          .replace('HH', hour)
          .replace('mm', minute)
          .replace('ss', second);
      } catch (error) {
        console.error('时间格式化失败', error);
        return '';
      }
    },

    /**
     * 格式化为友好时间
     */
    friendly(timestamp) {
      if (!timestamp) return '';

      try {
        const date = new Date(timestamp);
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);

        const timeStr = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

        if (date >= today && date < tomorrow) {
          return `今天 ${timeStr}`;
        } else if (date >= yesterday && date < today) {
          return `昨天 ${timeStr}`;
        } else if (date >= tomorrow && date < new Date(tomorrow.getTime() + 24 * 60 * 60 * 1000)) {
          return `明天 ${timeStr}`;
        } else {
          return this.format(timestamp, 'MM-dd HH:mm');
        }
      } catch (error) {
        console.error('友好时间格式化失败', error);
        return '';
      }
    },

    /**
     * 获取时间差
     */
    diff(startTime, endTime = Date.now()) {
      const diff = endTime - startTime;
      const seconds = Math.floor(diff / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      return { diff, seconds, minutes, hours, days };
    },

    /**
     * 检查是否为今天
     */
    isToday(timestamp) {
      if (!timestamp) return false;

      const date = new Date(timestamp);
      const today = new Date();

      return date.getDate() === today.getDate() &&
        date.getMonth() === today.getMonth() &&
        date.getFullYear() === today.getFullYear();
    }
  },

  /**
   * 字符串处理
   */
  string: {
    /**
     * 生成随机字符串
     */
    random(length = 8, chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') {
      let result = '';
      for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      return result;
    },

    /**
     * 生成UUID
     */
    uuid() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    },

    /**
     * 截断字符串
     */
    truncate(str, length = 50, suffix = '...') {
      if (!str || str.length <= length) return str;
      return str.substring(0, length) + suffix;
    },

    /**
     * 首字母大写
     */
    capitalize(str) {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    },

    /**
     * 驼峰转下划线
     */
    camelToSnake(str) {
      return str.replace(/([A-Z])/g, '_$1').toLowerCase();
    },

    /**
     * 下划线转驼峰
     */
    snakeToCamel(str) {
      return str.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
    },

    /**
     * 移除HTML标签
     */
    stripHtml(str) {
      return str.replace(/<[^>]*>/g, '');
    },

    /**
     * 转义HTML字符
     */
    escapeHtml(str) {
      const htmlEscapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
      };
      return str.replace(/[&<>"']/g, (match) => htmlEscapes[match]);
    }
  },

  /**
   * 数字处理
   */
  number: {
    /**
     * 格式化数字（添加千分位分隔符）
     */
    format(num, separator = ',') {
      if (num == null) return '';
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, separator);
    },

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
      if (bytes === 0) return '0 B';

      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));

      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * 生成指定范围的随机数
     */
    random(min = 0, max = 100) {
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    /**
     * 保留指定小数位
     */
    toFixed(num, digits = 2) {
      return Number(parseFloat(num).toFixed(digits));
    },

    /**
     * 转换为百分比
     */
    toPercent(num, digits = 1) {
      return (num * 100).toFixed(digits) + '%';
    },

    /**
     * 安全除法
     */
    safeDivide(dividend, divisor, defaultValue = 0) {
      return divisor === 0 ? defaultValue : dividend / divisor;
    }
  },

  /**
   * 数组处理
   */
  array: {
    /**
     * 数组去重
     */
    unique(arr, key) {
      if (!Array.isArray(arr)) return [];

      if (key) {
        const seen = new Set();
        return arr.filter(item => {
          const keyValue = item[key];
          if (seen.has(keyValue)) {
            return false;
          }
          seen.add(keyValue);
          return true;
        });
      }

      return [...new Set(arr)];
    },

    /**
     * 数组分组
     */
    groupBy(arr, key) {
      if (!Array.isArray(arr)) return {};

      return arr.reduce((groups, item) => {
        const group = typeof key === 'function' ? key(item) : item[key];
        groups[group] = groups[group] || [];
        groups[group].push(item);
        return groups;
      }, {});
    },

    /**
     * 数组分页
     */
    paginate(arr, page = 1, pageSize = 10) {
      if (!Array.isArray(arr)) return { items: [], total: 0, page: 1, pageSize };

      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      const items = arr.slice(start, end);

      return {
        items,
        total: arr.length,
        page,
        pageSize,
        totalPages: Math.ceil(arr.length / pageSize),
        hasMore: end < arr.length
      };
    },

    /**
     * 随机打乱数组
     */
    shuffle(arr) {
      const newArr = [...arr];
      for (let i = newArr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArr[i], newArr[j]] = [newArr[j], newArr[i]];
      }
      return newArr;
    },

    /**
     * 数组求和
     */
    sum(arr, key) {
      if (!Array.isArray(arr)) return 0;

      return arr.reduce((sum, item) => {
        const value = key ? item[key] : item;
        return sum + (Number(value) || 0);
      }, 0);
    },

    /**
     * 数组求平均值
     */
    average(arr, key) {
      if (!Array.isArray(arr) || arr.length === 0) return 0;

      const total = this.sum(arr, key);
      return total / arr.length;
    },

    /**
     * 查找最大值
     */
    max(arr, key) {
      if (!Array.isArray(arr) || arr.length === 0) return null;

      return arr.reduce((max, item) => {
        const value = key ? item[key] : item;
        const maxValue = key ? max[key] : max;
        return value > maxValue ? item : max;
      });
    },

    /**
     * 查找最小值
     */
    min(arr, key) {
      if (!Array.isArray(arr) || arr.length === 0) return null;

      return arr.reduce((min, item) => {
        const value = key ? item[key] : item;
        const minValue = key ? min[key] : min;
        return value < minValue ? item : min;
      });
    }
  },

  /**
   * 对象处理
   */
  object: {
    /**
     * 深拷贝
     */
    deepClone(obj) {
      if (obj === null || typeof obj !== 'object') return obj;
      if (obj instanceof Date) return new Date(obj.getTime());
      if (obj instanceof Array) return obj.map(item => this.deepClone(item));
      if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
          if (obj.hasOwnProperty(key)) {
            clonedObj[key] = this.deepClone(obj[key]);
          }
        }
        return clonedObj;
      }
    },

    /**
     * 深度合并对象
     */
    deepMerge(target, ...sources) {
      if (!sources.length) return target;
      const source = sources.shift();

      if (this.isObject(target) && this.isObject(source)) {
        for (const key in source) {
          if (this.isObject(source[key])) {
            if (!target[key]) Object.assign(target, { [key]: {} });
            this.deepMerge(target[key], source[key]);
          } else {
            Object.assign(target, { [key]: source[key] });
          }
        }
      }

      return this.deepMerge(target, ...sources);
    },

    /**
     * 检查是否为对象
     */
    isObject(item) {
      return item && typeof item === 'object' && !Array.isArray(item);
    },

    /**
     * 获取嵌套对象属性
     */
    get(obj, path, defaultValue) {
      const keys = path.split('.');
      let result = obj;

      for (const key of keys) {
        if (result == null || typeof result !== 'object') {
          return defaultValue;
        }
        result = result[key];
      }

      return result !== undefined ? result : defaultValue;
    },

    /**
     * 设置嵌套对象属性
     */
    set(obj, path, value) {
      const keys = path.split('.');
      let current = obj;

      for (let i = 0; i < keys.length - 1; i++) {
        const key = keys[i];
        if (!(key in current) || typeof current[key] !== 'object') {
          current[key] = {};
        }
        current = current[key];
      }

      current[keys[keys.length - 1]] = value;
      return obj;
    },

    /**
     * 移除对象中的空值
     */
    removeEmpty(obj) {
      const newObj = {};
      for (const key in obj) {
        const value = obj[key];
        if (value != null && value !== '' && (!Array.isArray(value) || value.length > 0)) {
          newObj[key] = typeof value === 'object' ? this.removeEmpty(value) : value;
        }
      }
      return newObj;
    },

    /**
     * 对象转查询字符串
     */
    toQueryString(obj) {
      const params = [];
      for (const key in obj) {
        if (obj[key] != null) {
          params.push(`${encodeURIComponent(key)}=${encodeURIComponent(obj[key])}`);
        }
      }
      return params.join('&');
    }
  },

  /**
   * 验证工具
   */
  validate: {
    /**
     * 验证邮箱
     */
    email(email) {
      const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return regex.test(email);
    },

    /**
     * 验证手机号
     */
    phone(phone) {
      const regex = /^1[3-9]\d{9}$/;
      return regex.test(phone);
    },

    /**
     * 验证身份证号
     */
    idCard(idCard) {
      const regex = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/;
      return regex.test(idCard);
    },

    /**
     * 验证URL
     */
    url(url) {
      const regex = /^https?:\/\/.+/;
      return regex.test(url);
    },

    /**
     * 验证密码强度
     */
    password(password, minLength = 6) {
      if (!password || password.length < minLength) return false;

      // 至少包含数字和字母
      const hasNumber = /\d/.test(password);
      const hasLetter = /[a-zA-Z]/.test(password);

      return hasNumber && hasLetter;
    },

    /**
     * 验证是否为空
     */
    isEmpty(value) {
      if (value == null) return true;
      if (typeof value === 'string') return value.trim() === '';
      if (Array.isArray(value)) return value.length === 0;
      if (typeof value === 'object') return Object.keys(value).length === 0;
      return false;
    },

    /**
     * 验证年龄
     */
    age(age) {
      return Number.isInteger(age) && age >= 0 && age <= 150;
    }
  },

  /**
   * 设备信息
   */
  device: {
    /**
     * 获取系统信息
     */
    getSystemInfo() {
      try {
        return wx.getSystemInfoSync();
      } catch (error) {
        console.error('获取系统信息失败', error);
        return {};
      }
    },

    /**
     * 检查是否为iOS
     */
    isIOS() {
      const systemInfo = this.getSystemInfo();
      return systemInfo.platform === 'ios';
    },

    /**
     * 检查是否为Android
     */
    isAndroid() {
      const systemInfo = this.getSystemInfo();
      return systemInfo.platform === 'android';
    },

    /**
     * 获取屏幕尺寸
     */
    getScreenSize() {
      const systemInfo = this.getSystemInfo();
      return {
        width: systemInfo.screenWidth,
        height: systemInfo.screenHeight,
        pixelRatio: systemInfo.pixelRatio
      };
    },

    /**
     * rpx转px
     */
    rpxToPx(rpx) {
      const systemInfo = this.getSystemInfo();
      return (rpx * systemInfo.screenWidth) / 750;
    },

    /**
     * px转rpx
     */
    pxToRpx(px) {
      const systemInfo = this.getSystemInfo();
      return (px * 750) / systemInfo.screenWidth;
    }
  },

  /**
   * 颜色处理
   */
  color: {
    /**
     * 十六进制转RGB
     */
    hexToRgb(hex) {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null;
    },

    /**
     * RGB转十六进制
     */
    rgbToHex(r, g, b) {
      return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    },

    /**
     * 生成随机颜色
     */
    random() {
      return '#' + Math.floor(Math.random() * 16777215).toString(16);
    },

    /**
     * 调整颜色亮度
     */
    adjustBrightness(hex, percent) {
      const rgb = this.hexToRgb(hex);
      if (!rgb) return hex;

      const adjust = (color) => {
        const adjusted = Math.round(color * (100 + percent) / 100);
        return Math.max(0, Math.min(255, adjusted));
      };

      return this.rgbToHex(
        adjust(rgb.r),
        adjust(rgb.g),
        adjust(rgb.b)
      );
    }
  },

  /**
   * 防抖和节流
   */
  throttle: {
    /**
     * 防抖函数
     */
    debounce(func, wait = 300) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    /**
     * 节流函数
     */
    throttle(func, limit = 300) {
      let inThrottle;
      return function executedFunction(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    }
  },

  /**
   * 错误处理
   */
  error: {
    /**
     * 安全执行函数
     */
    async safeExecute(fn, defaultValue = null) {
      try {
        return await fn();
      } catch (error) {
        console.error('函数执行失败', error);
        return defaultValue;
      }
    },

    /**
     * 重试执行
     */
    async retry(fn, maxRetries = 3, delay = 1000) {
      let lastError;

      for (let i = 0; i <= maxRetries; i++) {
        try {
          return await fn();
        } catch (error) {
          lastError = error;
          if (i < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }

      throw lastError;
    }
  },

  /**
   * 缓存管理
   */
  cache: {
    /**
     * 简单内存缓存
     */
    memory: new Map(),

    /**
     * 设置缓存
     */
    set(key, value, ttl = 0) {
      const expiry = ttl > 0 ? Date.now() + ttl : 0;
      this.memory.set(key, { value, expiry });
    },

    /**
     * 获取缓存
     */
    get(key) {
      const item = this.memory.get(key);
      if (!item) return null;

      if (item.expiry > 0 && Date.now() > item.expiry) {
        this.memory.delete(key);
        return null;
      }

      return item.value;
    },

    /**
     * 删除缓存
     */
    delete(key) {
      return this.memory.delete(key);
    },

    /**
     * 清空缓存
     */
    clear() {
      this.memory.clear();
    }
  },

  /**
   * URL处理
   */
  url: {
    /**
     * 解析URL参数
     */
    parseQuery(url) {
      const queryString = url.includes('?') ? url.split('?')[1] : '';
      const params = {};

      if (queryString) {
        queryString.split('&').forEach(param => {
          const [key, value] = param.split('=');
          if (key) {
            params[decodeURIComponent(key)] = decodeURIComponent(value || '');
          }
        });
      }

      return params;
    },

    /**
     * 构建URL
     */
    build(base, params = {}) {
      const queryString = utils.object.toQueryString(params);
      return queryString ? `${base}?${queryString}` : base;
    },

    /**
     * 合并URL参数
     */
    mergeParams(url, newParams = {}) {
      const [base, queryString] = url.split('?');
      const existingParams = queryString ? this.parseQuery('?' + queryString) : {};
      const mergedParams = { ...existingParams, ...newParams };
      return this.build(base, mergedParams);
    }
  },

  /**
   * 图像处理
   */
  image: {
    /**
     * 压缩图片
     */
    async compress(src, quality = 0.8, maxWidth = 1080) {
      return new Promise((resolve, reject) => {
        wx.getImageInfo({
          src,
          success: (res) => {
            const canvas = wx.createCanvasContext('imageCanvas');
            const { width, height } = res;

            // 计算新尺寸
            let newWidth = width;
            let newHeight = height;

            if (width > maxWidth) {
              newWidth = maxWidth;
              newHeight = (height * maxWidth) / width;
            }

            // 绘制并导出
            canvas.drawImage(src, 0, 0, newWidth, newHeight);
            canvas.draw(false, () => {
              wx.canvasToTempFilePath({
                canvasId: 'imageCanvas',
                width: newWidth,
                height: newHeight,
                fileType: 'jpg',
                quality,
                success: resolve,
                fail: reject
              });
            });
          },
          fail: reject
        });
      });
    },

    /**
     * 获取图片信息
     */
    async getInfo(src) {
      return new Promise((resolve, reject) => {
        wx.getImageInfo({
          src,
          success: resolve,
          fail: reject
        });
      });
    }
  }
};

module.exports = utils;

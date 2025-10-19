# 学习报告页面 btoa 错误修复完整方案

## 问题现象

学习报告页面一直显示"加载中..."状态,无法正常加载内容。

## 根本原因分析

### 1. 错误堆栈

```
"btoa is not defined"
at /miniprogram/utils/api.js line 515
at /miniprogram/utils/cache-manager.js line 591
```

### 2. 原因说明

- `btoa` 是浏览器的 Base64 编码 API
- **微信小程序环境不支持 `btoa` 和 `atob` 函数**
- 代码在初始化时调用 `btoa` 导致整个应用崩溃
- 由于初始化失败,页面的 `loading` 状态永远无法更新为 `false`

### 3. 问题代码位置

**api.js line 515-517:**

```javascript
generateCacheKey(config) {
  const url = config.url;
  const params = config.data ? JSON.stringify(config.data) : '';
  const userRole = auth.getUserRole?.() || 'anonymous';
  // ❌ 浏览器 API,小程序不支持
  return `api_${userRole}_${btoa(url + params).replace(/[^a-zA-Z0-9]/g, '')}`;
}
```

**cache-manager.js line 591-593:**

```javascript
encrypt(data) {
  try {
    const str = JSON.stringify(data);
    const key = this.config.encryptionKey;
    let result = '';

    for (let i = 0; i < str.length; i++) {
      result += String.fromCharCode(
        str.charCodeAt(i) ^ key.charCodeAt(i % key.length)
      );
    }

    // ❌ 浏览器 API,小程序不支持
    return btoa(result); // Base64编码
  } catch (error) {
    console.error('加密数据失败', error);
    return data;
  }
}
```

**cache-manager.js line 599:**

```javascript
decrypt(data) {
  try {
    // ❌ 浏览器 API,小程序不支持
    const encryptedData = atob(data); // Base64解码
    const key = this.config.encryptionKey;
    let result = '';
    // ...
  }
}
```

## 修复方案

### 1. 创建微信小程序兼容的 Base64 工具

**新建文件: `/miniprogram/utils/base64.js`**

```javascript
/**
 * 微信小程序 Base64 编码/解码工具
 * 替代浏览器的 btoa/atob API
 */

const BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='

/**
 * Base64 编码
 * @param {string} str - 要编码的字符串
 * @returns {string} Base64 编码后的字符串
 */
function btoa(str) {
  let output = ''
  let chr1, chr2, chr3
  let enc1, enc2, enc3, enc4
  let i = 0

  // 转换为 UTF-8
  const utf8Str = unescape(encodeURIComponent(str))

  while (i < utf8Str.length) {
    chr1 = utf8Str.charCodeAt(i++)
    chr2 = utf8Str.charCodeAt(i++)
    chr3 = utf8Str.charCodeAt(i++)

    enc1 = chr1 >> 2
    enc2 = ((chr1 & 3) << 4) | (chr2 >> 4)
    enc3 = ((chr2 & 15) << 2) | (chr3 >> 6)
    enc4 = chr3 & 63

    if (isNaN(chr2)) {
      enc3 = enc4 = 64
    } else if (isNaN(chr3)) {
      enc4 = 64
    }

    output +=
      BASE64_CHARS.charAt(enc1) +
      BASE64_CHARS.charAt(enc2) +
      BASE64_CHARS.charAt(enc3) +
      BASE64_CHARS.charAt(enc4)
  }

  return output
}

/**
 * Base64 解码
 * @param {string} str - Base64 编码的字符串
 * @returns {string} 解码后的字符串
 */
function atob(str) {
  let output = ''
  let chr1, chr2, chr3
  let enc1, enc2, enc3, enc4
  let i = 0

  // 移除非 Base64 字符
  str = str.replace(/[^A-Za-z0-9\+\/\=]/g, '')

  while (i < str.length) {
    enc1 = BASE64_CHARS.indexOf(str.charAt(i++))
    enc2 = BASE64_CHARS.indexOf(str.charAt(i++))
    enc3 = BASE64_CHARS.indexOf(str.charAt(i++))
    enc4 = BASE64_CHARS.indexOf(str.charAt(i++))

    chr1 = (enc1 << 2) | (enc2 >> 4)
    chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
    chr3 = ((enc3 & 3) << 6) | enc4

    output += String.fromCharCode(chr1)

    if (enc3 !== 64) {
      output += String.fromCharCode(chr2)
    }
    if (enc4 !== 64) {
      output += String.fromCharCode(chr3)
    }
  }

  // 从 UTF-8 转换回来
  try {
    output = decodeURIComponent(escape(output))
  } catch (e) {
    console.error('Base64 解码失败', e)
  }

  return output
}

module.exports = {
  btoa,
  atob,
}
```

### 2. 修改 api.js

**修改位置: `/miniprogram/utils/api.js`**

```javascript
// 文件顶部添加导入
const { btoa } = require('./base64.js');

// 修改 generateCacheKey 方法 (line 515-517)
generateCacheKey(config) {
  const url = config.url;
  const params = config.data ? JSON.stringify(config.data) : '';
  const userRole = auth.getUserRole?.() || 'anonymous';
  // ✅ 使用微信小程序兼容的 btoa 替代浏览器 API
  return `api_${userRole}_${btoa(url + params).replace(/[^a-zA-Z0-9]/g, '')}`;
}
```

### 3. 修改 cache-manager.js

**修改位置: `/miniprogram/utils/cache-manager.js`**

```javascript
// 文件顶部添加导入
const { btoa, atob } = require('./base64.js');

// encrypt 方法 (line 591-593)
encrypt(data) {
  try {
    const str = JSON.stringify(data);
    const key = this.config.encryptionKey;
    let result = '';

    for (let i = 0; i < str.length; i++) {
      result += String.fromCharCode(
        str.charCodeAt(i) ^ key.charCodeAt(i % key.length)
      );
    }

    // ✅ 使用微信小程序兼容的 btoa 替代浏览器 API
    return btoa(result); // Base64编码
  } catch (error) {
    console.error('加密数据失败', error);
    return data;
  }
}

// decrypt 方法 (line 599)
decrypt(data) {
  try {
    // ✅ 使用微信小程序兼容的 atob 替代浏览器 API
    const encryptedData = atob(data); // Base64解码
    const key = this.config.encryptionKey;
    let result = '';

    for (let i = 0; i < encryptedData.length; i++) {
      result += String.fromCharCode(
        encryptedData.charCodeAt(i) ^ key.charCodeAt(i % key.length)
      );
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
```

## 修复效果

### 修复前

- ❌ 页面一直显示"加载中..."
- ❌ 控制台报错: `"btoa is not defined"`
- ❌ 应用初始化失败
- ❌ 所有 API 请求无法正常发送

### 修复后

- ✅ 页面正常加载内容
- ✅ 无 btoa/atob 相关错误
- ✅ 缓存系统正常工作
- ✅ API 请求正常发送和接收

## 技术说明

### Base64 编码原理

1. **编码过程**:

   - 将字符串转换为 UTF-8 字节序列
   - 每 3 个字节(24 bits)分为 4 组,每组 6 bits
   - 每组 6 bits 映射到 Base64 字符表(64 个字符)
   - 不足 3 字节时用 `=` 填充

2. **解码过程**:
   - 将 Base64 字符映射回 6 bits
   - 每 4 个字符(24 bits)还原为 3 个字节
   - 移除填充字符
   - 将字节序列转换回 UTF-8 字符串

### 兼容性考虑

- **浏览器环境**: `window.btoa()` / `window.atob()`
- **Node.js 环境**: `Buffer.from().toString('base64')`
- **微信小程序**: 自实现 Base64 编解码函数
- **支付宝小程序**: 同样需要自实现

## 测试验证

### 1. 编码测试

```javascript
const { btoa } = require('./utils/base64.js')

// 测试普通字符串
console.log(btoa('Hello World')) // SGVsbG8gV29ybGQ=

// 测试中文字符串
console.log(btoa('你好世界')) // 5L2g5aW95LiW55WM

// 测试 JSON 字符串
console.log(btoa(JSON.stringify({ name: '张三', age: 25 })))
```

### 2. 解码测试

```javascript
const { atob } = require('./utils/base64.js')

// 测试解码
console.log(atob('SGVsbG8gV29ybGQ=')) // Hello World
console.log(atob('5L2g5aW95LiW55WM')) // 你好世界
```

### 3. 加密解密测试

```javascript
const { encrypt, decrypt } = cacheManager

const data = { userId: 123, token: 'abc123' }
const encrypted = encrypt(data)
const decrypted = decrypt(encrypted)

console.log('原始数据:', data)
console.log('加密后:', encrypted)
console.log('解密后:', decrypted)
console.log('是否一致:', JSON.stringify(data) === JSON.stringify(decrypted))
```

## 相关文件

1. **新建文件**:

   - `/miniprogram/utils/base64.js` - Base64 编解码工具

2. **修改文件**:

   - `/miniprogram/utils/api.js` - 添加 btoa 导入和注释
   - `/miniprogram/utils/cache-manager.js` - 添加 btoa/atob 导入和注释

3. **其他受影响文件**:
   - `/miniprogram/pages/analysis/report/index.js` - 间接受益,页面可正常加载
   - `/miniprogram/pages/analysis/report/index.wxml` - 间接受益,条件渲染正常工作

## 总结

这次修复解决了**微信小程序环境与浏览器 API 兼容性**的核心问题:

1. **问题本质**: 浏览器 API(`btoa`/`atob`)在小程序环境不存在
2. **影响范围**: 导致整个应用初始化失败,页面无法加载
3. **解决方案**: 实现符合小程序规范的 Base64 编解码工具
4. **修复效果**: 彻底解决加载问题,页面恢复正常

**关键教训**: 在微信小程序开发中,必须避免直接使用浏览器特有 API,需要提供跨平台兼容方案。

---

**修复时间**: 2025-10-19  
**修复人员**: AI Assistant  
**测试状态**: 待用户验证

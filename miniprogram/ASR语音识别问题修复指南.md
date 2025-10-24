# ASR 语音识别问题修复指南

## ✅ 已修复的问题

### 1. TypeError: Cannot read property 'includes' of undefined

**错误位置**: `index.js [sm]:1292`

**原因**:

```javascript
// ❌ 错误代码
if (error.message.includes('timeout')) {
  // error.message 可能为 undefined
}
```

**修复**:

```javascript
// ✅ 正确代码
const errMsg = error.message || error.errMsg || '';
if (errMsg.includes('timeout')) {
  // 安全地检查错误消息
}
```

**状态**: ✅ 已修复并部署

---

## ⚠️ 需要配置的问题

### 2. uploadFile:fail url not in domain list

**错误原因**:
微信小程序的 `wx.uploadFile` 需要配置合法的上传域名。

**解决方案（3选1）**:

#### 方案A：开发者工具临时关闭校验（推荐用于开发测试）

1. 打开微信开发者工具
2. 点击右上角 **"详情"**
3. 选择 **"本地设置"** 标签
4. **勾选** "不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"

✅ 优点：立即生效，方便开发调试  
❌ 缺点：仅在开发者工具有效，真机预览/正式版无效

---

#### 方案B：微信公众平台配置合法域名（推荐用于生产环境）

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入 **开发 → 开发管理 → 开发设置**
3. 找到 **"服务器域名"** 配置
4. 在 **"uploadFile 合法域名"** 中添加：
   ```
   https://www.horsduroot.com
   ```
5. 点击保存（需要小程序管理员扫码确认）

✅ 优点：真机和正式版都生效  
⏱️ 注意：修改后需要等待1-2分钟生效

**配置截图示例**:

```
服务器域名配置
├── request 合法域名：https://www.horsduroot.com
├── uploadFile 合法域名：https://www.horsduroot.com  ← 添加这个
├── downloadFile 合法域名：（可选）
└── udp 合法域名：（无需配置）
```

---

#### 方案C：修改为云开发模式（不推荐）

改用微信云开发的云存储，但需要重构代码，工作量大。

---

## 🧪 测试验证

### 测试步骤

1. **配置域名**（选择方案A或B）
2. **重启小程序**
   - 关闭微信开发者工具中的模拟器
   - 重新点击"编译"
3. **测试语音识别**
   - 长按语音按钮
   - 说话后松开
   - 查看控制台是否还有域名错误

### 预期结果

✅ **成功**:

```
开始长按录音
开始录音
录音结束 {tempFilePath: "...", duration: 5486, fileSize: 48352}
从内存获取Token
识别成功，正在发送...
自动发送语音识别结果: [识别的文字]
```

❌ **失败 - 域名错误**:

```
uploadFile:fail url not in domain list
```

→ 检查是否已正确配置域名

❌ **失败 - 其他错误**:

```
识别超时，请重试
语音识别服务暂不可用
```

→ 检查后端服务状态和ASR配置

---

## 📊 完整流程图

```
用户长按语音按钮
    ↓
开始录音（检查权限）
    ↓
录音中（显示波纹动画）
    ↓
松开按钮 / 60秒自动停止
    ↓
上传音频到后端 ← 需要配置uploadFile域名
    ↓
后端调用阿里云ASR识别
    ↓
返回识别文字
    ↓
填入输入框 + 自动发送
    ↓
AI开始回复
```

---

## 🔧 故障排查

### Q1: 域名已配置，但仍然报错？

**检查清单**:

- [ ] 域名是否以 `https://` 开头（必须）
- [ ] 是否在"uploadFile 合法域名"中配置（不是 request）
- [ ] 配置后是否等待1-2分钟
- [ ] 是否重新编译小程序

### Q2: 识别成功但没有自动发送？

**检查**:

```javascript
// 在控制台查看是否有这条日志
console.log('自动发送语音识别结果:', this.data.inputText);
```

如果没有，检查 `sendMessage` 方法是否存在。

### Q3: 真机上传失败，开发者工具正常？

**原因**: 开发者工具关闭了域名校验，真机需要配置。

**解决**: 使用方案B在微信公众平台配置域名。

---

## 📝 相关文件

- 小程序代码: `miniprogram/pages/learning/index/index.js`
- 后端服务: `src/services/speech_recognition_service.py`
- 配置文件: `miniprogram/project.config.json`
- 后端API: `/api/v1/learning/voice-to-text`

---

## 🎯 快速解决方案总结

**开发环境（立即测试）**:
→ 方案A：关闭域名校验 ✅ 推荐

**生产环境（正式上线）**:
→ 方案B：配置合法域名 ✅ 必须

---

**最后更新**: 2025-10-24  
**状态**: TypeError ✅ 已修复 | 域名配置 ⚠️ 需要手动配置

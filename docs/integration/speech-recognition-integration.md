# 语音识别服务集成指南

## 概述

本项目已集成阿里云语音识别服务，为微信小程序的作业问答模块提供语音转文字功能。

## 功能特性

- **多格式支持**: MP3, WAV, M4A, AAC, FLAC, OGG
- **智能断句**: 自动添加标点符号
- **文本规范化**: 支持数字、时间等的智能转换
- **错误处理**: 完善的错误提示和重试机制
- **权限管理**: 用户认证和访问控制

## 架构设计

### 前端（微信小程序）

```
用户录音 → 权限检查 → 录音管理器 → 文件上传 → API调用 → 结果展示
```

### 后端（FastAPI）

```
API接口 → 文件验证 → 语音识别服务 → 阿里云ASR → 结果处理 → 响应返回
```

## 配置要求

### 1. 阿里云语音识别服务配置

在 `.env` 文件中添加以下配置：

```bash
# 语音识别服务配置
ASR_ENABLED=true
ASR_APP_KEY=your_asr_app_key_here
ASR_ACCESS_TOKEN=your_asr_access_token_here
ASR_ENDPOINT=https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr
ASR_FORMAT=mp3
ASR_SAMPLE_RATE=16000
ASR_ENABLE_INTERMEDIATE_RESULT=false
ASR_ENABLE_PUNCTUATION_PREDICTION=true
ASR_ENABLE_INVERSE_TEXT_NORMALIZATION=true
ASR_MAX_AUDIO_DURATION=60
```

### 2. 阿里云智能语音服务开通

1. 登录阿里云控制台
2. 开通智能语音交互服务
3. 创建项目并获取 AppKey
4. 生成访问令牌 (Access Token)
5. 配置服务地域（推荐：华东 2-上海）

### 3. 微信小程序域名配置

在微信小程序管理后台配置请求域名：

```
https://your-domain.com
https://nls-gateway-cn-shanghai.aliyuncs.com
```

## 接口说明

### 语音转文字 API

**接口地址**: `POST /api/v1/learning/voice-to-text`

**请求参数**:

- `voice`: 音频文件 (form-data)
- `language`: 识别语言，默认 zh-CN (可选)

**响应格式**:

```json
{
  \"success\": true,
  \"data\": {
    \"text\": \"识别出的文字内容\",
    \"confidence\": 0.95,
    \"duration\": 3.2,
    \"audio_size\": 51200,
    \"language\": \"zh-CN\"
  },
  \"message\": \"语音识别成功\"
}
```

## 使用方式

### 前端调用示例

```javascript
// 1. 检查录音权限
this.checkRecordPermission();

// 2. 开始录音
this.startVoiceRecord();

// 3. 停止录音并上传
this.stopVoiceRecord();

// 4. 语音文件上传和识别
async uploadVoiceFile(filePath) {
  const token = await authManager.getToken();

  const uploadResult = await new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${api.baseUrl}/learning/voice-to-text`,
      filePath: filePath,
      name: 'voice',
      header: {
        Authorization: `Bearer ${token}`,
      },
      success: res => {
        const data = JSON.parse(res.data);
        if (data.success) {
          resolve(data.data);
        } else {
          reject(new Error(data.message));
        }
      },
      fail: reject,
    });
  });

  // 设置识别结果到输入框
  this.setData({ inputText: uploadResult.text });
}
```

## 部署配置

### 开发环境

1. 复制配置模板：

   ```bash
   cp config/templates/env.dev.template .env
   ```

2. 配置语音识别服务参数（可选，用于测试）

3. 启动服务：
   ```bash
   ./scripts/start-dev.sh
   ```

### 生产环境

1. 配置生产环境变量：

   ```bash
   # 必须配置真实的阿里云ASR服务参数
   ASR_APP_KEY=your_production_app_key
   ASR_ACCESS_TOKEN=your_production_access_token
   ```

2. 使用生产部署脚本：
   ```bash
   ./scripts/deploy_to_production.sh
   ```

## 错误处理

### 常见错误及解决方案

1. **配置不完整错误**

   - 错误信息：\"语音识别服务配置不完整\"
   - 解决方案：检查 ASR_APP_KEY 和 ASR_ACCESS_TOKEN 配置

2. **不支持的音频格式**

   - 错误信息：\"不支持的音频格式\"
   - 解决方案：确保音频文件为支持的格式（MP3、WAV 等）

3. **文件过大错误**

   - 错误信息：\"音频文件过大或过长\"
   - 解决方案：控制录音时长在 60 秒内

4. **网络连接失败**
   - 错误信息：\"语音识别网络请求失败\"
   - 解决方案：检查网络连接和防火墙设置

### 调试方法

1. **查看日志**：

   ```bash
   tail -f logs/app.log | grep speech_recognition
   ```

2. **健康检查**：

   ```bash
   curl http://localhost:8000/api/v1/learning/health
   ```

3. **测试语音识别**：
   ```bash
   curl -X POST \\
     -H \"Authorization: Bearer your_token\" \\
     -F \"voice=@test_audio.mp3\" \\
     http://localhost:8000/api/v1/learning/voice-to-text
   ```

## 性能优化

### 建议配置

- **音频格式**: MP3（压缩率高，传输快）
- **采样率**: 16kHz（平衡质量和大小）
- **录音时长**: ≤ 60 秒（提高识别准确性）
- **网络优化**: 启用 GZIP 压缩

### 监控指标

- 语音识别成功率
- 平均响应时间
- 错误率分布
- API 调用频次

## 安全考虑

1. **用户认证**: 所有 API 调用需要有效的 JWT 令牌
2. **文件验证**: 严格检查上传文件的格式和大小
3. **访问控制**: 限制请求频率和文件大小
4. **数据隐私**: 语音文件不长期存储，及时清理

## 更新日志

### v1.0.0 (2025-10-14)

- 🎉 首次集成阿里云语音识别服务
- ✨ 支持微信小程序语音转文字功能
- 🔧 完善的配置管理和错误处理
- 📝 WeChat 风格的用户界面设计
- 🎯 多模态问答支持（文字 + 语音 + 图片）

## 技术支持

如有问题，请查看：

- [阿里云智能语音服务文档](https://help.aliyun.com/product/30413.html)
- [微信小程序录音 API 文档](https://developers.weixin.qq.com/miniprogram/dev/api/media/recorder/RecorderManager.html)
- 项目 Issue 跟踪

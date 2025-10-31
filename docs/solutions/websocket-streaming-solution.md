# 微信小程序 WebSocket 流式方案

## 方案概述

由于微信小程序的 `enableChunked` 支持不稳定，推荐使用 **WebSocket** 实现真正的流式响应。

## 架构设计

```
微信小程序 ←→ WebSocket ←→ FastAPI WebSocket 端点 ←→ 阿里云百炼 SSE
```

---

## 后端实现

### 1. 新增 WebSocket 端点

```python
# src/api/v1/endpoints/learning.py

from fastapi import WebSocket, WebSocketDisconnect
import json

@router.websocket("/ws/ask")
async def websocket_ask(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket 流式问答"""
    await websocket.accept()

    try:
        # 接收请求数据
        request_data = await websocket.receive_json()

        # 验证 token
        token = request_data.get("token")
        user_id = await verify_websocket_token(token)

        # 构建请求
        request = AskQuestionRequest(**request_data["params"])

        # 流式调用
        learning_service = get_learning_service(db)
        async for chunk in learning_service.ask_question_stream(user_id, request):
            # 发送数据块
            await websocket.send_json(chunk)

    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await websocket.close()
```

---

## 前端实现

### 1. WebSocket 客户端

```javascript
// miniprogram/api/learning.js

/**
 * WebSocket 流式问答
 */
askQuestionStreamWS(params, onChunk, config = {}) {
  return new Promise((resolve, reject) => {
    const app = getApp();
    const token = app.globalData.token;

    if (!token) {
      reject({ code: 'AUTH_ERROR', message: '用户未登录' });
      return;
    }

    const apiConfig = require('../config/index.js').api;
    // WebSocket URL (wss:// for HTTPS)
    const wsUrl = apiConfig.baseUrl
      .replace('https://', 'wss://')
      .replace('http://', 'ws://') + '/api/v1/learning/ws/ask';

    console.log('[WebSocket Stream] 连接:', wsUrl);

    let fullContent = '';
    let finalData = null;

    // 创建 WebSocket 连接
    const socketTask = wx.connectSocket({
      url: wsUrl,
      success: () => {
        console.log('[WebSocket] 连接成功');
      },
      fail: (error) => {
        console.error('[WebSocket] 连接失败:', error);
        reject({ code: 'WS_CONNECT_ERROR', message: '连接失败' });
      }
    });

    // 监听连接打开
    socketTask.onOpen(() => {
      console.log('[WebSocket] 连接已建立');

      // 发送请求数据
      socketTask.send({
        data: JSON.stringify({
          token: token,
          params: params
        }),
        success: () => {
          console.log('[WebSocket] 请求已发送');
        },
        fail: (error) => {
          console.error('[WebSocket] 发送失败:', error);
          reject({ code: 'WS_SEND_ERROR', message: '发送失败' });
        }
      });
    });

    // 监听消息
    socketTask.onMessage((res) => {
      try {
        const chunk = JSON.parse(res.data);
        console.log('[WebSocket Chunk]', chunk);

        // 累积内容
        if (chunk.content) {
          fullContent += chunk.content;
        } else if (chunk.full_content) {
          fullContent = chunk.full_content;
        }

        // 回调前端
        onChunk({
          type: chunk.type || 'content',
          content: chunk.content || '',
          full_content: chunk.full_content || fullContent,
          finish_reason: chunk.finish_reason,
        });

        // 保存最终数据
        if (chunk.type === 'done' || chunk.finish_reason === 'stop') {
          finalData = chunk;
        }

      } catch (error) {
        console.error('[WebSocket] 解析消息失败:', error);
      }
    });

    // 监听关闭
    socketTask.onClose(() => {
      console.log('[WebSocket] 连接已关闭');

      // 返回结果
      resolve(finalData || {
        type: 'done',
        full_content: fullContent,
        content: fullContent,
      });
    });

    // 监听错误
    socketTask.onError((error) => {
      console.error('[WebSocket] 错误:', error);
      reject({ code: 'WS_ERROR', message: '连接错误' });
    });
  });
}
```

### 2. 使用 WebSocket 方法

```javascript
// miniprogram/pages/learning/index/index.js

// 调用 WebSocket 流式 API
const response = await api.learning.askQuestionStreamWS(
  requestParams,
  (chunk) => {
    // 实时更新 UI（完全一样的代码）
    fullContent += chunk.content;
    aiMessage.content = fullContent;
    this.setData({ messageList: [...] });
    this.scrollToBottom();
  }
);
```

---

## 配置要求

### 1. 微信小程序域名配置

登录微信公众平台 → 开发 → 开发设置 → 服务器域名：

- **socket 合法域名**：`wss://horsduroot.com`

### 2. Nginx 配置（WebSocket 支持）

```nginx
# /etc/nginx/sites-available/wuhao-tutor

location /api/v1/learning/ws/ {
    proxy_pass http://127.0.0.1:8000;

    # WebSocket 支持
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # 其他配置
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # 超时配置
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

---

## 优势

| 特性           | SSE + enableChunked | WebSocket   |
| -------------- | ------------------- | ----------- |
| **实时性**     | ❓ 不稳定           | ✅ 极好     |
| **兼容性**     | ❌ 基础库 >= 2.20.1 | ✅ 所有版本 |
| **双向通信**   | ❌ 单向             | ✅ 双向     |
| **稳定性**     | ❌ 容易断连         | ✅ 自动重连 |
| **开发复杂度** | ✅ 简单             | ⚠️ 中等     |

---

## 实施步骤

1. ✅ **后端添加 WebSocket 端点**（1 小时）
2. ✅ **前端实现 WebSocket 客户端**（30 分钟）
3. ✅ **配置 Nginx WebSocket 支持**（15 分钟）
4. ✅ **微信后台添加 socket 域名**（5 分钟）
5. ✅ **测试验证**（30 分钟）

**总计：约 2.5 小时**

---

## 回退策略

如果 WebSocket 不可用，自动降级到普通 HTTP 请求：

```javascript
async function askWithFallback(params, onChunk) {
  try {
    // 优先使用 WebSocket
    return await api.learning.askQuestionStreamWS(params, onChunk)
  } catch (error) {
    if (error.code === 'WS_CONNECT_ERROR') {
      console.warn('WebSocket 不可用，降级到普通请求')
      // 降级到普通请求（无流式）
      return await api.learning.askQuestion(params)
    }
    throw error
  }
}
```

---

**推荐指数**: ⭐⭐⭐⭐⭐

**最佳选择**: WebSocket 是微信小程序中实现真正流式响应的最佳方案。

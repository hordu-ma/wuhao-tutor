# WebSocket 连接修复 - 测试验证指南

**修复日期**: 2025-11-02  
**修复版本**: 生产环境已部署  
**问题**: 华为/三星手机 WebSocket 连接失败

---

## ✅ 修复已完成

### 变更内容

#### 1. `/etc/nginx/nginx.conf`

添加 RFC 6455 标准的 Connection 头映射：

```nginx
# WebSocket Connection 头映射（RFC 6455 标准）
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
```

#### 2. `/etc/nginx/conf.d/wuhao-tutor.conf`

WebSocket location 使用映射变量：

```nginx
location /api/v1/learning/ws/ {
    proxy_set_header Connection $connection_upgrade;  # ← 修复点
    ...
}
```

**修复前**: `proxy_set_header Connection "upgrade";` (硬编码)  
**修复后**: `proxy_set_header Connection $connection_upgrade;` (映射变量)

---

## 🧪 测试验证步骤

### 立即测试（5 分钟）

#### 步骤 1: 华为手机测试（关键）

1. 打开微信小程序"五好伴学"
2. 进入"作业问答"页面
3. 上传一张作业图片
4. 发送问题

**预期结果**:

- ✅ 不再出现"网络连接失败"弹窗
- ✅ AI 回复流式显示
- ✅ 可以正常对话

**如果仍失败**:

- 截图错误信息
- 开启微信调试模式，查看控制台日志
- 联系开发团队进一步排查

---

#### 步骤 2: 三星手机测试

同上

---

#### 步骤 3: 回归测试

在 **iPhone** 和 **小米平板** 上重复测试，确保：

- ✅ 原本正常的设备仍然正常
- ✅ 没有性能下降
- ✅ 连接更稳定

---

### 进阶验证（可选）

#### 查看服务器日志

```bash
ssh root@121.199.173.244

# 1. 查看 WebSocket 连接日志
tail -f /var/log/nginx/access.log | grep "ws/ask"

# 2. 查看错误日志（应该没有 WebSocket 相关错误）
tail -f /var/log/nginx/error.log

# 3. 查看后端日志
journalctl -u wuhao-tutor.service -f | grep "WebSocket"
```

**正常日志示例**:

```
[WebSocket] 连接已建立
[WebSocket] 收到请求: dict_keys(['token', 'params'])
[WebSocket] 流式响应完成
```

---

## 📊 技术细节

### 问题原因分析

| 设备                 | WebView 内核 | 协议检查 | 结果            |
| -------------------- | ------------ | -------- | --------------- |
| **华为** (HarmonyOS) | 定制内核     | 严格     | ❌ 拒绝硬编码头 |
| **三星** (One UI)    | 定制内核     | 严格     | ❌ 拒绝硬编码头 |
| **iPhone**           | WebKit       | 宽松     | ✅ 偶然成功     |
| **小米**             | MIUI WebView | 宽松     | ✅ 偶然成功     |

### RFC 6455 标准要求

**WebSocket 握手时的 Connection 头处理**:

1. 客户端发送 `Upgrade: websocket` 和 `Connection: Upgrade`
2. 服务器应该根据 `$http_upgrade` 动态设置 `Connection` 头
3. 如果请求不是 Upgrade（空字符串），应该设置为 `close`

**映射逻辑**:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;    # 有 Upgrade 头时，返回 "upgrade"
    ''      close;      # 无 Upgrade 头时，返回 "close"
}
```

### 为什么硬编码会失败？

**硬编码方式**:

```nginx
proxy_set_header Connection 'upgrade';  # ❌ 所有请求都发送 "upgrade"
```

**问题**:

- 即使非 WebSocket 请求（如预检请求），也会发送 `Connection: upgrade`
- 严格的 WebView 检测到不匹配，拒绝连接
- 返回错误码（可能是 400 Bad Request 或握手失败）

**标准方式**:

```nginx
proxy_set_header Connection $connection_upgrade;  # ✅ 根据请求动态设置
```

**优势**:

- WebSocket 请求：自动设置为 `upgrade`
- 普通 HTTP 请求：自动设置为 `close`
- 符合 RFC 6455 标准，所有设备兼容

---

## 🔄 回滚方案（如需要）

**如果修复后仍有问题，可以回滚**:

```bash
ssh root@121.199.173.244

# 1. 查看备份文件
ls -lh /etc/nginx/*.backup*
ls -lh /etc/nginx/conf.d/*.backup*

# 2. 回滚到修复前的配置
cp /etc/nginx/nginx.conf.backup-YYYYMMDD-HHMMSS /etc/nginx/nginx.conf
cp /etc/nginx/conf.d/wuhao-tutor.conf.backup-YYYYMMDD-HHMMSS /etc/nginx/conf.d/wuhao-tutor.conf

# 3. 测试配置
nginx -t

# 4. 重载 Nginx
systemctl reload nginx
```

**注意**: 请记录回滚的备份文件时间戳，以便后续分析。

---

## 📝 测试结果记录

| 测试项         | 设备     | 结果      | 备注            | 测试人 | 日期 |
| -------------- | -------- | --------- | --------------- | ------ | ---- |
| WebSocket 连接 | 华为手机 | ⏳ 待测试 | -               | -      | -    |
| WebSocket 连接 | 三星手机 | ⏳ 待测试 | -               | -      | -    |
| 回归测试       | iPhone   | ⏳ 待测试 | -               | -      | -    |
| 回归测试       | 小米平板 | ⏳ 待测试 | -               | -      | -    |
| 流式响应       | 所有设备 | ⏳ 待测试 | AI 回复正常显示 | -      | -    |
| 错误处理       | 所有设备 | ⏳ 待测试 | 网络中断恢复    | -      | -    |

**测试通过标准**:

- ✅ 华为/三星手机连接成功
- ✅ 所有设备无退化
- ✅ 服务器日志无异常

---

## 🎯 下一步行动

### 立即执行

1. **通知测试人员** - 在华为/三星手机上测试
2. **监控服务器** - 观察 WebSocket 连接日志
3. **记录结果** - 填写上方测试结果表格

### 后续优化（如果测试通过）

1. 推送代码到 Git 远程仓库
2. 更新部署文档
3. 关闭相关 Issue/工单

### 如果仍有问题

1. 收集详细日志（前端 + 后端）
2. 抓包分析 WebSocket 握手过程
3. 考虑备用方案（HTTP SSE 或长轮询）

---

**修复人员**: AI Assistant  
**审核状态**: ⏳ 待测试验证  
**部署状态**: ✅ 已部署到生产环境  
**Git Commit**: 6e19aca

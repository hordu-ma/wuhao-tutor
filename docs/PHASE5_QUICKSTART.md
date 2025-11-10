# Phase 5.1 快速启动指南

**目标**: 5 分钟内开始前后端联调测试  
**阶段**: Phase 5.1 - 前后端联调  
**预计时间**: 30-60 分钟

---

## 🚀 快速开始（3 步）

### Step 1: 运行自动化检查（1 分钟）

```bash
# 在项目根目录执行
cd /Users/liguoma/my-devs/python/wuhao-tutor
./scripts/test-phase5-integration.sh
```

**预期输出**:
```
✅ 主服务健康检查通过
✅ 学习模块健康检查通过
✅ API 地址配置正确 (生产环境)
✅ 组件文件存在: index.js
...
📋 完整测试报告: ./test-results/phase5/integration-test-*.md
```

**如果出现错误**: 查看生成的测试报告，修复问题后重试。

---

### Step 2: 打开微信开发者工具（1 分钟）

1. 打开**微信开发者工具**
2. 导入项目: `miniprogram/` 目录
3. 点击**编译**，确保无错误
4. 确认右上角显示"生产环境"

**验证配置**:
```javascript
// 在控制台执行
const config = require('./config/index.js');
console.log({
  env: config.environment,      // 应该是 'production'
  url: config.api.baseUrl,      // 应该是 'https://www.horsduroot.com'
  timeout: config.api.timeout   // 应该是 120000
});
```

---

### Step 3: 开始手动测试（1 分钟准备）

1. 准备测试图片（3 张）:
   - **图片 A**: 有错误的作业（2-3 个错题）
   - **图片 B**: 全部正确的作业
   - **图片 C**: 含未作答题目的作业

2. 打开测试检查清单:
   ```bash
   open docs/PHASE5_MANUAL_TEST_CHECKLIST.md
   ```

3. 登录测试账号，开始测试 ✅

---

## 📋 核心测试流程（30 分钟）

### 测试 1: 基本批改流程（10 分钟）

```
1. 打开"作业问答"页面
2. 点击相机图标 📷
3. 上传图片 A（有错误的作业）
4. 等待 AI 批改完成（约 20-30 秒）
5. 检查批改结果卡片:
   ✓ 统计数字正确
   ✓ 错题列表完整
   ✓ 解析清晰
6. 点击"查看错题本"
7. 验证错题已创建
```

**关键验证点**:
- [ ] 批改时间 < 40 秒
- [ ] 错题数量正确
- [ ] 跳转错题本成功
- [ ] 错题信息完整

---

### 测试 2: 全对场景（5 分钟）

```
1. 上传图片 B（全部正确）
2. 等待批改完成
3. 检查全对提示和鼓励信息
4. 验证不显示错题列表
5. 点击"继续练习"
```

**关键验证点**:
- [ ] 显示"恭喜你全对了！"
- [ ] 错误数 = 0
- [ ] 只显示"继续练习"按钮

---

### 测试 3: 未作答场景（5 分钟）

```
1. 上传图片 C（有未作答题目）
2. 等待批改完成
3. 检查未作答标记
4. 验证未作答题目创建为错题
```

**关键验证点**:
- [ ] 未作答题目有特殊标识
- [ ] 未作答题目也被记录到错题本

---

### 测试 4: 网络异常（5 分钟）

```
1. 关闭网络
2. 尝试上传图片
3. 观察错误提示
4. 恢复网络
5. 验证重试机制
```

**关键验证点**:
- [ ] 错误提示友好
- [ ] 不会崩溃
- [ ] 可以重试

---

### 测试 5: 数据验证（5 分钟）

```
1. SSH 到生产服务器
2. 查询数据库验证错题创建
3. 查看后端日志
```

**数据库查询**:
```sql
-- 连接数据库
psql -U wuhao_user -d wuhao_db

-- 查询最新错题
SELECT 
  id, 
  question_number, 
  error_type, 
  is_unanswered,
  created_at
FROM mistakes
ORDER BY created_at DESC
LIMIT 10;
```

**后端日志查看**:
```bash
# 查看实时日志
journalctl -u wuhao-tutor.service -f | grep "批改"

# 查看最近日志
journalctl -u wuhao-tutor.service -n 100 | grep "错题创建"
```

---

## 🔍 监控要点

### 前端日志（微信开发者工具 Console）

**关键日志**:
```javascript
// 1. 批改结果检测
📋 检测到批改结果: [{...}]
📋 批改统计: { totalQuestions: 5, mistakesCreated: 2 }

// 2. 组件加载
[correction-card] 组件已挂载
[correction-card] 数据更新: { total: 5, correct: 3, errors: 2, ... }

// 3. 跳转
[correction-card] 跳转到错题本
```

---

### 网络请求（微信开发者工具 Network）

**关键请求**:
```
POST /api/v1/learning/ask-stream
Request:
  - Content-Type: application/json
  - Authorization: Bearer <token>
  - Body: { content, question_type: "homework_review", image_urls: [...] }

Response (SSE):
  - event: message (多次)
  - event: done
    - correction_result: [...]
    - mistakes_created: 2
```

**验证点**:
- [ ] 请求头正确
- [ ] 响应格式正确
- [ ] correction_result 存在
- [ ] mistakes_created 为数字

---

### 后端日志（生产服务器）

**关键日志**:
```
📝 检测到作业批改场景，启动专用逻辑
✅ [批改完成] total_questions=5, errors=2, ...
📝 [错题创建] 开始处理批改结果
  [1/5] 🔴 处理错题: Q1
  [2/5] 跳过正确题目: Q2
✅ [错题创建] 成功创建 2 个错题
```

---

## ❌ 常见问题快速修复

### 问题 1: 批改结果不显示

**症状**: AI 回复完成，但没有批改卡片

**快速排查**:
```javascript
// 在控制台执行
console.log('检查最后一条消息:', this.data.messageList[this.data.messageList.length - 1]);
```

**可能原因**:
1. 后端未返回 `correction_result` → 检查后端日志
2. 组件未注册 → 检查 `pages/learning/index/index.json`
3. 条件渲染错误 → 检查 `index.wxml` 中的 `wx:if`

**解决方案**:
```bash
# 重启后端服务
ssh root@121.199.173.244
systemctl restart wuhao-tutor.service

# 重新编译小程序
# 在微信开发者工具中点击"编译"
```

---

### 问题 2: 错题未创建到数据库

**症状**: 批改完成，但错题本中没有记录

**快速排查**:
```bash
# SSH 到服务器
ssh root@121.199.173.244

# 查看错题创建日志
journalctl -u wuhao-tutor.service -n 200 | grep "错题创建"
```

**可能原因**:
1. 所有题目都正确（预期行为）
2. 批改逻辑未识别错题
3. 数据库写入失败

**解决方案**:
```bash
# 检查数据库连接
psql -U wuhao_user -d wuhao_db -c "SELECT COUNT(*) FROM mistakes;"

# 查看数据库错误日志
tail -f /var/log/postgresql/postgresql-*.log
```

---

### 问题 3: 图片上传失败

**症状**: 选择图片后上传失败

**快速排查**:
```javascript
// 检查图片大小和格式
console.log('图片信息:', {
  size: file.size,
  type: file.type
});
```

**可能原因**:
1. 图片过大（> 10MB）
2. 网络不稳定
3. Token 过期

**解决方案**:
- 压缩图片或选择较小的图片
- 检查网络连接
- 重新登录获取新 Token

---

### 问题 4: API 请求 401 未授权

**症状**: 请求返回 401 错误

**快速排查**:
```javascript
// 检查 Token
const auth = require('./utils/auth.js');
auth.getToken().then(token => {
  console.log('当前 Token:', token ? 'exists' : 'null');
});
```

**解决方案**:
```javascript
// 清除旧 Token 重新登录
wx.removeStorageSync('auth_token');
wx.removeStorageSync('refresh_token');
// 然后重新登录
```

---

## 📊 性能基准

### 目标响应时间
- 图片上传: < 5 秒
- AI 批改（5 题）: < 30 秒
- 错题创建: < 2 秒
- 页面跳转: < 1 秒
- **总流程**: < 40 秒

### 目标成功率
- API 调用: > 99%
- 图片上传: > 95%
- AI 批改: > 95%
- 错题创建: > 99%

---

## ✅ 完成标准

### Phase 5.1 通过条件

- [ ] ✅ 所有自动化测试通过
- [ ] ✅ 核心功能手动测试通过
- [ ] ✅ 批改结果卡片正确显示
- [ ] ✅ 错题本关联功能正常
- [ ] ✅ 数据流完整（前端 → 后端 → 数据库 → 前端）
- [ ] ✅ 边界情况处理得当
- [ ] ✅ 性能指标达标
- [ ] ✅ 无阻塞性问题

### 输出物

- [ ] 自动化测试报告: `test-results/phase5/integration-test-*.md`
- [ ] 手动测试检查清单（已填写）: `docs/PHASE5_MANUAL_TEST_CHECKLIST.md`
- [ ] 问题列表（如有）
- [ ] 性能数据记录
- [ ] 测试截图（可选）

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| `docs/PHASE5_INTEGRATION_TEST.md` | 详细测试指南和用例 |
| `docs/PHASE5_MANUAL_TEST_CHECKLIST.md` | 手动测试检查清单 |
| `DEVELOPMENT_CONTEXT.md` | 开发进度和任务列表 |
| `scripts/test-phase5-integration.sh` | 自动化测试脚本 |

---

## 🎯 下一步

Phase 5.1 完成后，继续进行:

1. **Phase 5.2**: 场景测试
   - 多学科测试（数学、语文、英语等）
   - 多题型测试（选择题、填空题、应用题等）
   - 更多边界条件

2. **Phase 5.3**: 性能与稳定性测试
   - 压力测试
   - 并发测试
   - 长时间运行测试

3. **Phase 5.4**: UI/UX 测试
   - 不同机型适配
   - 交互体验优化
   - 无障碍性测试

---

## 💡 提示

- **保存进度**: 每完成一个测试场景，记得在检查清单中打勾
- **记录问题**: 发现问题立即记录，包含复现步骤和截图
- **性能监控**: 记录每次测试的响应时间，计算平均值
- **寻求帮助**: 遇到阻塞问题，查看 `docs/PHASE5_INTEGRATION_TEST.md` 的排查指南

---

**准备好了吗？开始测试吧！** 🚀

```bash
# 运行自动化检查
./scripts/test-phase5-integration.sh

# 打开手动测试清单
open docs/PHASE5_MANUAL_TEST_CHECKLIST.md
```

**祝测试顺利！**
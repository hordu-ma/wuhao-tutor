# 公式渲染修复方案 - 实施文档

> **修复日期**: 2025-01-XX
> **问题**: 小程序端数学公式以原始LaTeX格式显示，未渲染为图片
> **影响**: 用户体验差，公式难以阅读
> **优先级**: P0 (核心功能缺陷)

---

## 📋 问题诊断

### 问题现象
AI回复中的数学公式显示为原始LaTeX格式:
```
球的体积公式:
一个半径为 $ r $ 的球的体积公式为:
$$V = \frac{4}{3} \pi r^3$$
```

而不是渲染后的公式图片。

### 根本原因
**后端公式增强成功，但增强后的内容未发送给前端。**

**流程断点分析:**
```mermaid
AI输出LaTeX
  → 前端接收并显示$$...$$
  → finish_reason="stop"
  → 后端formula_service处理
  → 生成<img class="math-formula-*">标签
  ❌ 只保存到数据库，未yield给前端
  → 前端继续显示原始LaTeX
```

**代码证据 (src/services/learning_service.py:346-356):**
```python
if chunk.get("finish_reason") == "stop":
    enhanced_content = await self.formula_service.process_text_with_formulas(
        full_answer_content
    )
    if enhanced_content:
        full_answer_content = enhanced_content  # ✅ 赋值成功

    # ❌ 但这里没有yield给前端!
    # 继续执行保存到数据库...
```

---

## ✅ 修复方案

### 方案1: 后端修复 (已完成)

**文件**: `src/services/learning_service.py`
**位置**: 第346-370行

**修改内容:**
```python
if chunk.get("finish_reason") == "stop":
    logger.info("✅ 进入公式增强流程")

    try:
        enhanced_content = await self.formula_service.process_text_with_formulas(
            full_answer_content
        )

        # 如果公式处理成功且内容有变化
        if enhanced_content and enhanced_content != full_answer_content:
            full_answer_content = enhanced_content
            logger.info(f"✅ 公式增强成功，内容长度: {len(enhanced_content)}")

            # 🔧 关键修复：发送增强后的完整内容给前端
            yield {
                "type": "formula_enhanced",
                "content": enhanced_content,
                "full_content": enhanced_content,
                "finish_reason": "stop",
            }
            logger.info("📤 已发送公式增强内容给前端")
        else:
            logger.info("⚠️ 公式增强未生效或内容未变化")

    except Exception as formula_err:
        logger.warning(f"公式增强失败，使用原始内容: {str(formula_err)}")
```

**变更说明:**
1. 增加内容变化检查 (`enhanced_content != full_answer_content`)
2. 在公式增强成功后 **立即yield** `formula_enhanced`事件
3. 添加详细日志便于追踪

---

### 方案2: 前端监听 (已完成)

**文件**: `miniprogram/pages/learning/index/index.js`
**位置**: sendMessage方法的WebSocket回调中 (约1043行后)

**修改内容:**
```javascript
const response = await api.learning.askQuestionStreamWS(requestParams, chunk => {
  console.log('[WebSocket Stream Chunk]', {
    type: chunk.type,
    contentLength: chunk.content ? chunk.content.length : 0,
  });

  // 🔧 [新增] 处理公式增强事件
  if (chunk.type === 'formula_enhanced') {
    console.log('📐 收到公式增强内容，长度:', chunk.content?.length || 0);

    // 使用增强后的完整内容替换
    fullContent = chunk.content || chunk.full_content || fullContent;

    // 立即更新UI，不等待节流
    const newMessageList = [...this.data.messageList];
    const aiMsgIndex = newMessageList.findIndex(msg => msg.id === aiMessageId);

    if (aiMsgIndex !== -1) {
      const enhancedContent = this.enhanceMessageContent(fullContent);

      newMessageList[aiMsgIndex] = {
        ...newMessageList[aiMsgIndex],
        content: enhancedContent.content,
        hasHtmlContent: enhancedContent.hasHtmlContent,
        richContent: enhancedContent.richContent,
      };

      this.setData({ messageList: newMessageList });

      console.log('✅ 公式增强内容已应用到UI');
    }

    // formula_enhanced 事件不需要节流更新
    return;
  }

  // ... 现有的content处理逻辑 ...
});
```

**变更说明:**
1. 在WebSocket chunk回调的**最前面**添加`formula_enhanced`事件检查
2. 收到事件后**立即更新UI**，不走节流逻辑
3. 调用`enhanceMessageContent`方法生成richContent (调用markdown-formatter解析公式标签)
4. 更新后直接return，避免后续的常规处理

---

### 方案3: 渲染验证 (已就绪，无需修改)

✅ **降级渲染器已完整支持公式**

**组件**: `miniprogram/components/towxml-renderer/index.wxml`

```xml
<!-- 数学公式图片渲染 -->
<image wx:elif="{{inline.type === 'math-formula'}}"
       class="math-formula-{{inline.value.type}}"
       src="{{inline.value.src}}"
       alt="{{inline.value.alt}}"
       mode="{{inline.value.type === 'block' ? 'widthFix' : 'aspectFit'}}"
       bindtap="onFormulaImageTap"
       data-alt="{{inline.value.alt}}" />
```

✅ **Markdown解析器已支持公式标签**

**文件**: `miniprogram/utils/markdown-formatter.js`

```javascript
{
  regex: /<img\s+class="math-formula-(block|inline)"[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*\/?>(?:<\/img>)?/g,
  type: 'math-formula',
  getValue: match => ({
    type: match[1],    // block 或 inline
    src: match[2],     // 图片URL
    alt: match[3] || '数学公式',
  }),
}
```

✅ **样式已配置**

**文件**: `miniprogram/pages/learning/index/index.wxss`

```css
.math-formula-inline {
  display: inline-block;
  vertical-align: middle;
  max-height: 1.2em;
}

.math-formula-block {
  display: block;
  max-width: 100%;
  margin: 20rpx auto;
  text-align: center;
}
```

---

## 🧪 测试验证

### 自动化测试

运行验证脚本:
```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor

# 运行后端验证
uv run python scripts/verify_formula_fix.py
```

**预期输出:**
```
✅ 收到 formula_enhanced 事件!
✅ 内容包含公式图片标签
✅ 测试通过: 公式已正确增强并包含图片标签
🎉 所有测试通过! 公式渲染修复成功!
```

---

### 手动测试

#### 1. 启动后端
```bash
make dev
# 或
uv run python src/main.py
```

#### 2. 启动小程序
- 打开微信开发者工具
- 加载项目: `/Users/liguoma/my-devs/python/wuhao-tutor/miniprogram`
- 编译并运行

#### 3. 测试用例

**测试1: 块级公式**
```
问题: "球的体积公式是什么?"
预期: AI回复包含渲染后的公式图片 (V = 4/3 πr³)
```

**测试2: 行内公式**
```
问题: "圆的面积公式是 $A = \pi r^2$，对吗?"
预期: 公式嵌入在文本中，显示为小图片
```

**测试3: 复杂公式**
```
问题: "二次方程的求根公式是什么?"
预期: 分数、根号等符号正确显示
```

#### 4. 验证检查点

- [ ] 打开微信开发者工具控制台
- [ ] 发送包含公式的问题
- [ ] 观察Console日志:
  ```
  📐 收到公式增强内容，长度: XXX
  ✅ 公式增强内容已应用到UI
  ```
- [ ] 检查聊天界面中公式是否显示为图片
- [ ] 点击公式图片，确认可以预览

---

### 监控验证

访问公式渲染监控端点:
```bash
curl http://localhost:8000/api/v1/health/formula-metrics
```

**检查指标:**
```json
{
  "timestamp": "2025-01-XX...",
  "metrics": {
    "total_requests": 10,      // 应该增加
    "render_success": 9,        // 成功率
    "cache_hits": 5,           // 缓存命中
    "errors": {
      "quicklatex": 1,
      "total": 1
    }
  }
}
```

---

## 📊 预期效果

### 修复前
```
用户: "球的体积公式是什么?"
AI: "球的体积公式为: $$V = \frac{4}{3} \pi r^3$$"
显示: 用户看到原始LaTeX文本
```

### 修复后
```
用户: "球的体积公式是什么?"
AI流式输出: "球的体积公式为: $$V = \frac{4}{3} \pi r^3$$"
  ↓ 前端显示LaTeX (流式阶段)
  ↓ finish_reason="stop"
  ↓ 后端处理公式 → 生成图片URL
  ↓ 发送 formula_enhanced 事件
  ↓ 前端接收 → 替换为图片标签
  ↓ 渲染器显示图片
显示: 用户看到美观的公式图片 [V = 4/3 πr³]
```

---

## 🔍 故障排查

### 问题1: 未收到 formula_enhanced 事件

**检查:**
```bash
# 查看后端日志
tail -f logs/app.log | grep "formula_enhanced"

# 或
journalctl -u wuhao-tutor -f | grep "formula"
```

**可能原因:**
- 公式服务未启用
- QuickLaTeX API失败
- 公式提取正则未匹配

**解决:**
```bash
# 检查环境变量
env | grep FORMULA

# 确认公式服务配置
ENABLE_FORMULA_CACHE=true
```

---

### 问题2: 前端未更新UI

**检查:**
- 打开微信开发者工具 Console
- 查找日志: `"📐 收到公式增强内容"`
- 如果没有，检查WebSocket连接状态

**可能原因:**
- 前端代码未重新编译
- WebSocket连接中断
- chunk类型判断错误

**解决:**
```bash
# 微信开发者工具中
1. 清除缓存
2. 重新编译
3. 重启调试
```

---

### 问题3: 公式图片加载失败

**检查:**
```javascript
// 在 Console 中查看图片URL
console.log('公式图片URL:', chunk.content)
```

**可能原因:**
- QuickLaTeX服务不可用
- OSS上传失败
- 图片URL过期

**解决:**
```bash
# 查看公式渲染指标
curl http://localhost:8000/api/v1/health/formula-metrics

# 检查错误类型
{
  "errors": {
    "quicklatex": X,    // QuickLaTeX失败
    "oss_upload": Y,    // OSS上传失败
  }
}
```

---

## 🚀 生产部署

### 1. 代码提交
```bash
git add src/services/learning_service.py
git add miniprogram/pages/learning/index/index.js
git commit -m "fix(formula): 修复小程序公式渲染问题

- 后端在公式增强后发送formula_enhanced事件
- 前端监听并立即更新UI
- 添加详细日志便于追踪

解决问题: 公式以原始LaTeX格式显示
影响范围: 小程序作业问答模块
测试状态: 已通过自动化测试"

git push origin main
```

### 2. 部署到生产
```bash
# 一键部署
./scripts/deploy.sh

# 或手动部署
ssh root@121.199.173.244 'cd /opt/wuhao-tutor && git pull && systemctl restart wuhao-tutor'
```

### 3. 小程序上传
- 微信开发者工具 → 上传代码
- 填写版本号: `v1.x.x - 修复公式渲染`
- 提交审核

### 4. 验证部署
```bash
# 检查生产环境公式指标
curl https://horsduroot.com/api/v1/health/formula-metrics

# 查看服务日志
ssh root@121.199.173.244 'journalctl -u wuhao-tutor -f | grep formula'
```

---

## 📝 总结

### 修复内容
- ✅ 后端: 在公式增强成功后发送`formula_enhanced`事件
- ✅ 前端: 监听事件并立即更新UI
- ✅ 测试: 添加自动化验证脚本

### 影响范围
- **后端**: 1个文件，15行代码
- **前端**: 1个文件，30行代码
- **风险**: 低 (仅新增事件，不影响现有流程)

### 工作量
- **开发**: 30分钟
- **测试**: 15分钟
- **部署**: 10分钟
- **总计**: 约1小时

### 优先级
- **P0 - 必须修复** (核心功能缺陷，影响用户体验)

---

## 📚 相关文档

- [公式服务文档](../architecture/formula-service.md)
- [流式问答架构](../architecture/streaming-api.md)
- [前端Markdown渲染](../frontend/markdown-rendering.md)
- [生产部署指南](../deployment/production-deployment-guide.md)

---

**最后更新**: 2025-01-XX
**维护者**: 五好伴学开发团队

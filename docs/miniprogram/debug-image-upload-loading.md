# 图片上传转圈问题调试指南

## 问题现象

用户报告：点击加号 → 选择"从相册选择" → 选择图片后 → 页面一直转圈

## 调试步骤

### 1. 清除缓存并重新编译

在微信开发者工具中：

1. 点击菜单 "工具" → "清除缓存" → "清除全部缓存"
2. 关闭小程序
3. 重新点击"编译"按钮

### 2. 打开控制台

在微信开发者工具中：

1. 点击底部的 "Console" 标签
2. 确保选择了 "Console" 而不是 "Wxml" 或 "Sources"
3. 清空之前的日志（点击 🚫 图标）

### 3. 执行测试操作

**操作步骤**：

1. 在小程序中，进入"作业问答"页面
2. 点击输入框左边的 **"+" 按钮**
3. 观察控制台，应该看到：

   ```
   ===== 点击加号按钮 =====
   当前 uploadedImages: []
   showImageActions 设置为 true
   showImageActions 当前值: true
   ```

4. 在弹出的菜单中，点击 **"从相册选择"**
5. 观察控制台，应该看到：

   ```
   ===== 点击"从相册选择" =====
   即将调用 chooseImage("album")
   ===== chooseImage 开始 =====
   sourceType: album
   当前已选图片数量: 0
   maxImageCount: 5
   调用 wx.chooseMedia...
   ```

6. 在相册中 **选择一张图片**
7. 观察控制台，应该看到：

   ```
   ===== wx.chooseMedia SUCCESS =====
   选择的文件数量: 1
   文件信息: [{tempFilePath: "...", size: ...}]
   准备添加的图片: [...]
   已选择图片总数: 1
   ===== chooseImage 完成 =====
   ```

8. 此时应该 **在输入框上方看到图片预览**
9. **不要点击发送**，只是观察图片是否显示

### 4. 检查关键日志

**如果看到以下日志**，说明图片选择成功：

- ✅ `===== wx.chooseMedia SUCCESS =====`
- ✅ `已选择图片总数: 1`
- ✅ `===== chooseImage 完成 =====`

**如果看到以下日志**，说明图片选择失败：

- ❌ `===== wx.chooseMedia FAIL =====`
- ❌ `选择图片失败: ...`

**如果没有看到任何日志**：

- ❌ 可能是代码没有正确编译
- ❌ 可能是页面没有正确加载
- ❌ 建议重新清除缓存并编译

### 5. 检查界面状态

**正常情况下**：

- ✅ 输入框上方应该出现**图片预览区域**（灰色背景）
- ✅ 图片预览区域应该显示**选中的图片缩略图**
- ✅ 图片右上角应该有一个 **× 删除按钮**
- ✅ **不应该有任何 loading 转圈**

**异常情况下**：

- ❌ 如果图片预览区域没有出现 → WXML 渲染问题
- ❌ 如果图片缩略图一直转圈 → 图片加载问题
- ❌ 如果整个页面卡住 → 可能是 `setData` 卡住

## 可能的问题场景

### 场景 1: `wx.chooseMedia` 没有返回

**症状**：

- 控制台显示 `调用 wx.chooseMedia...`
- 但没有显示 `SUCCESS` 或 `FAIL`

**原因**：

- 微信 API 调用被阻塞
- 权限问题（相册权限）
- 微信版本不支持 `wx.chooseMedia`

**解决**：

1. 检查微信开发者工具版本（建议 ≥ 1.06.0）
2. 检查基础库版本（在右上角查看）
3. 尝试在真机上测试
4. 检查 `app.json` 中的权限配置

### 场景 2: `setData` 导致卡顿

**症状**：

- 控制台显示 `===== chooseImage 完成 =====`
- 但界面没有更新，一直转圈

**原因**：

- `uploadedImages` 数据过大
- `setData` 执行缓慢
- 渲染层卡住

**解决**：

1. 检查 `uploadedImages` 的数据结构
2. 检查是否有其他 `setData` 同时执行
3. 尝试简化图片预览 UI

### 场景 3: 图片加载失败

**症状**：

- 图片预览区域出现
- 但图片缩略图一直转圈

**原因**：

- `tempFilePath` 无效
- 图片文件损坏
- 微信无法访问临时文件

**解决**：

1. 在控制台检查 `tempFilePath` 的值
2. 尝试选择其他图片
3. 检查图片文件大小（是否超过 10MB）

## 测试结果收集

### 请截图以下信息

1. **控制台完整日志**（从点击 "+" 到图片选择完成）
2. **小程序界面状态**（图片预览区域是否出现）
3. **开发者工具右上角信息**（基础库版本、微信版本）
4. **Network 面板**（是否有网络请求）

### 日志模板

请将控制台日志复制粘贴，格式如下：

```
===== 点击加号按钮 =====
当前 uploadedImages: []
showImageActions 设置为 true

===== 点击"从相册选择" =====
即将调用 chooseImage("album")

===== chooseImage 开始 =====
sourceType: album
当前已选图片数量: 0
maxImageCount: 5
调用 wx.chooseMedia...

[这里应该看到 SUCCESS 或 FAIL]
```

## 下一步诊断

根据控制台日志的不同，采取不同的措施：

### 如果日志停在 "调用 wx.chooseMedia..."

→ 说明 `wx.chooseMedia` API 没有响应
→ 检查微信版本和权限
→ 尝试降级使用 `wx.chooseImage`（旧 API）

### 如果日志显示 "SUCCESS" 但界面没反应

→ 说明数据更新成功，但 UI 没有渲染
→ 检查 WXML 中的 `wx:if="{{uploadedImages.length > 0}}"`
→ 检查 WXSS 样式是否正确

### 如果日志显示 "FAIL"

→ 说明图片选择失败
→ 查看错误信息 `error.errMsg`
→ 根据错误信息采取对应措施

## 紧急回退方案

如果调试困难，可以暂时使用简化版本：

### 方案 A: 立即上传（不预览）

修改 `chooseImage` 的 success 回调：

```javascript
success: async (res) => {
  this.setData({ showImageActions: false })

  // 立即上传第一张图片
  const filePath = res.tempFiles[0].tempFilePath

  wx.showLoading({ title: '上传中...', mask: true })

  try {
    const aiUrl = await this.uploadImageToAI(filePath)

    // 直接发送到 AI
    const response = await api.learning.askQuestion({
      content: '请分析这张图片',
      session_id: this.data.sessionId,
      image_urls: [aiUrl],
    })

    wx.hideLoading()
    // 显示 AI 回复...
  } catch (error) {
    wx.hideLoading()
    wx.showToast({ title: '上传失败', icon: 'error' })
  }
}
```

### 方案 B: 使用旧版 API

如果 `wx.chooseMedia` 有兼容性问题，降级使用 `wx.chooseImage`:

```javascript
wx.chooseImage({
  count: 1,
  sourceType: [sourceType],
  success: (res) => {
    const tempFilePath = res.tempFilePaths[0]
    // ... 后续处理
  },
})
```

---

**请按照上述步骤执行测试，并将控制台日志截图发给我！** 🔍

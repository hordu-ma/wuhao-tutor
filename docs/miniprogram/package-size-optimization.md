# 微信小程序代码包体积优化方案

> 问题：主包大小 2190KB 超过限制 2048KB（超出 142KB）
> 目标：减小到 2048KB 以下

---

## 📊 当前问题分析

### 大文件占用情况

1. **echarts.min.js**: 1.0 MB（主要占用）
2. **其他组件和页面**: ~1.2 MB
3. **总计**: 2190KB

### 优化目标

- ✅ 减小 echarts 体积（从 1MB 减到 200KB）
- ✅ 移除不必要的打包文件
- ✅ 使用分包加载

---

## ✅ 解决方案（3 个方法，选其一）

### **方案 1：使用 ECharts 精简版**（推荐，立即生效）

ECharts 完整版 1MB 太大，使用按需加载的精简版。

#### 步骤 1：安装 ECharts 精简版

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram
npm install echarts-for-weixin
```

#### 步骤 2：替换 echarts.min.js

替换 `components/ec-canvas/echarts.min.js` 为精简版：

```bash
# 备份原文件
mv components/ec-canvas/echarts.min.js components/ec-canvas/echarts.min.js.backup

# 使用精简版（从 node_modules 复制）
cp node_modules/echarts-for-weixin/echarts.min.js components/ec-canvas/
```

**预期效果**：从 1.0MB 减到约 **200-300KB**

---

### **方案 2：按需引入 ECharts 模块**（最优，但需要修改代码）

只引入需要的图表类型（柱状图、折线图等），进一步减小体积。

#### 步骤 1：创建自定义 echarts 构建

```javascript
// components/ec-canvas/echarts-custom.js
// 按需引入 ECharts 模块

import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必需的组件
echarts.use([
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
])

export default echarts
```

#### 步骤 2：修改引用

在使用 echarts 的页面中，将：

```javascript
import * as echarts from './components/ec-canvas/echarts.min.js'
```

改为：

```javascript
import echarts from './components/ec-canvas/echarts-custom.js'
```

**预期效果**：减小到约 **100-200KB**

---

### **方案 3：使用分包加载**（推荐，配合方案 1 使用）

将图表相关页面移到分包，主包只保留核心功能。

#### 步骤 1：在 app.json 中配置分包

```json
{
  "pages": [
    "pages/index/index",
    "pages/login/index",
    "pages/mistakes/list/index",
    "pages/learning/index/index",
    "pages/profile/index/index"
  ],

  "subpackages": [
    {
      "root": "subpackages/analysis",
      "name": "analysis",
      "pages": ["pages/report/index", "pages/progress/index"]
    }
  ],

  "preloadRule": {
    "pages/index/index": {
      "network": "all",
      "packages": ["analysis"]
    }
  }
}
```

#### 步骤 2：移动文件

```bash
# 创建分包目录
mkdir -p subpackages/analysis/pages

# 移动学习报告页面
mv pages/analysis/report subpackages/analysis/pages/
mv pages/analysis/progress subpackages/analysis/pages/
```

**预期效果**：主包减小约 **500KB**

---

## 🚀 快速修复（立即执行）

### 执行方案 1：替换为精简版 ECharts

```bash
cd /Users/liguoma/my-devs/python/wuhao-tutor/miniprogram

# 1. 安装精简版
npm install echarts-for-weixin

# 2. 备份原文件
mv components/ec-canvas/echarts.min.js components/ec-canvas/echarts.min.js.backup

# 3. 复制精简版
cp node_modules/echarts-for-weixin/echarts.min.js components/ec-canvas/

# 4. 检查文件大小
ls -lh components/ec-canvas/echarts.min.js
```

### 执行方案：优化打包配置（已完成）

已在 `project.config.json` 中添加更多忽略规则：

- ✅ 忽略 docs/ 目录
- ✅ 忽略 examples/ 目录
- ✅ 忽略 tests/ 目录
- ✅ 忽略 .sh 和 .py 文件
- ✅ 忽略 README.md 等文档

---

## 📋 优化后检查清单

### 在微信开发者工具中：

1. **重新编译**

   - 点击"编译"按钮
   - 等待编译完成

2. **检查代码包大小**

   - 查看右上角"详情" → "基本信息" → "代码包信息"
   - 确认主包 < 2048KB

3. **测试功能**

   - 测试图表是否正常显示
   - 测试学习报告页面
   - 确认无报错

4. **上传**
   - 代码包符合要求后，点击"上传"

---

## 📊 预期优化效果

| 项目           | 优化前 | 优化后     | 减少      |
| -------------- | ------ | ---------- | --------- |
| echarts.min.js | 1000KB | 200KB      | 800KB     |
| 打包配置优化   | -      | -          | 50KB      |
| **总计**       | 2190KB | **1340KB** | **850KB** |

**结果**：主包从 2190KB 减少到约 **1340KB**，符合 2048KB 限制 ✅

---

## 🔧 额外优化建议（可选）

### 1. 图片优化

```bash
# 压缩 PNG 图片（使用 TinyPNG 或其他工具）
# 将 PNG 转为 WebP 格式（体积减少 30-50%）
```

### 2. 代码压缩

```json
// project.config.json
{
  "setting": {
    "minified": true, // 代码压缩
    "minifyWXML": true, // WXML 压缩
    "minifyWXSS": true // WXSS 压缩
  }
}
```

### 3. 使用 CDN

对于大文件（如字体、图片），可以使用 CDN：

```javascript
// 不要打包到小程序，使用线上地址
const iconUrl = 'https://cdn.example.com/icons/icon.png'
```

---

## ❓ 常见问题

### Q1：使用精简版 ECharts 后图表不显示？

**检查**：

- 确认引入路径正确
- 检查 console 是否有报错
- 确认图表配置正确

### Q2：分包后页面跳转失败？

**解决**：
更新跳转路径：

```javascript
// 原路径
wx.navigateTo({ url: '/pages/analysis/report/index' })

// 分包后路径
wx.navigateTo({ url: '/subpackages/analysis/pages/report/index' })
```

### Q3：优化后还是超限？

**进一步优化**：

1. 使用分包（方案 3）
2. 图片使用外链（CDN）
3. 移除不必要的组件库
4. 代码按需引入

---

## 📞 获取帮助

**相关文档**：

- [微信小程序分包文档](https://developers.weixin.qq.com/miniprogram/dev/framework/subpackages.html)
- [ECharts 小程序版](https://github.com/ecomfe/echarts-for-weixin)
- [代码包大小优化指南](https://developers.weixin.qq.com/miniprogram/dev/framework/performance/tips/start_optimizeA.html)

---

_最后更新：2025-10-19_
